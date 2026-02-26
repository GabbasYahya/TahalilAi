"""FastAPI application for TahalilAI medical report analysis.

Provides endpoints for:
* ``POST /analyze`` — upload a medical report for OCR + AI analysis.
* ``GET  /status/{job_id}`` — poll for analysis progress / results.
* ``POST /generate-audio`` — on-demand TTS for completed analyses.
* ``GET  /audio-status/{job_id}`` — poll for audio readiness.
* ``POST /translate`` — translate an analysis to Arabic via Gemini.
* ``GET  /`` — health-check.
"""

from __future__ import annotations

import os
import shutil
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from tahalilai.config import get_settings
from tahalilai.schemas import AudioRequest, TranslationRequest
from tahalilai.services.analyzer import analyze_text
from tahalilai.services.ocr import perform_ocr
from tahalilai.services.report import generate_arabic_pdf_report, generate_pdf_report
from tahalilai.services.translator import translate_medical_report
from tahalilai.services.tts import generate_audio
from tahalilai.utils.security import sanitize_filename, validate_file

# In-memory job store — replace with Redis / a database for production
_jobs: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _lifespan(_app: FastAPI):  # type: ignore[no-untyped-def]
    """Lightweight startup — TTS model is lazy-loaded on first audio request."""
    print("TahalilAI server ready (TTS deferred to first request).")
    yield
    print("TahalilAI server shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    settings = get_settings()
    uploads = settings.uploads_dir

    application = FastAPI(
        title="TahalilAI",
        description="Privacy-first medical lab report analysis API",
        version="1.0.0",
        lifespan=_lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    application.mount("/uploads", StaticFiles(directory=str(uploads)), name="uploads")

    # ── Health-check ───────────────────────────────────────────────────

    @application.get("/")
    def health_check() -> dict[str, str]:
        """Return server status."""
        return {"status": "online", "message": "TahalilAI Backend is running"}

    # ── Job status ─────────────────────────────────────────────────────

    @application.get("/status/{job_id}")
    def get_status(job_id: str) -> dict[str, Any]:
        """Return current status of an analysis job."""
        job = _jobs.get(job_id)
        if not job:
            return {"status": "not_found"}
        return job

    # ── Analysis ───────────────────────────────────────────────────────

    _FILE_FIELD = File(...)
    _AGE_FIELD = Form(None)
    _GENDER_FIELD = Form(None)
    _WAIT_FIELD = Form(False)

    @application.post("/analyze")
    async def analyze(
        background_tasks: BackgroundTasks,
        file: UploadFile = _FILE_FIELD,
        age: str = _AGE_FIELD,
        gender: str = _GENDER_FIELD,
        wait_for_result: bool = _WAIT_FIELD,
    ) -> JSONResponse:
        """Upload a medical report and start the analysis pipeline."""
        try:
            safe_name = sanitize_filename(file.filename or "upload")
            ext = os.path.splitext(safe_name)[1].lower() or ".unknown"
            file_uuid = str(uuid.uuid4())
            file_path = uploads / f"{file_uuid}{ext}"

            with open(file_path, "wb") as buf:
                shutil.copyfileobj(file.file, buf)

            try:
                validate_file(file_path)
            except ValueError as ve:
                file_path.unlink(missing_ok=True)
                return JSONResponse({"status": "error", "message": str(ve)}, status_code=400)

            job_id = file_uuid

            if wait_for_result:
                # Run the long pipeline in a thread-pool so that asyncio
                # cancellation (browser timeout, Ctrl+C) does NOT abort
                # the subprocess mid-inference.
                _jobs[job_id] = {"status": "processing", "submitted_at": time.time()}
                loop = __import__("asyncio").get_running_loop()
                with ThreadPoolExecutor(max_workers=1) as pool:
                    await loop.run_in_executor(
                        pool, _run_pipeline, job_id, str(file_path), age, gender
                    )
                job_data = _jobs[job_id]
                elapsed = round(time.time() - job_data.get("submitted_at", 0), 1)
                if job_data["status"] == "completed":
                    return JSONResponse(
                        {
                            "status": "completed",
                            "job_id": job_id,
                            "elapsed_seconds": elapsed,
                            "result": job_data["result"],
                        }
                    )
                return JSONResponse(
                    {
                        "status": job_data["status"],
                        "job_id": job_id,
                        "error": job_data.get("error", "Unknown"),
                    },
                    status_code=500,
                )

            # Async mode (default)
            _jobs[job_id] = {"status": "queued", "submitted_at": time.time(), "age": age, "gender": gender}
            background_tasks.add_task(_run_pipeline, job_id, str(file_path), age, gender)
            return JSONResponse(
                {
                    "status": "queued",
                    "job_id": job_id,
                    "message": "Processing started. Poll /status/<job_id> for results.",
                }
            )
        except Exception as exc:
            return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)

    # ── On-demand audio ────────────────────────────────────────────────

    @application.post("/generate-audio", response_model=None)
    async def generate_audio_endpoint(
        request: AudioRequest,
        background_tasks: BackgroundTasks,
    ) -> JSONResponse | dict[str, str]:
        """Trigger TTS generation for a completed analysis."""
        job = _jobs.get(request.job_id)
        if not job or job.get("status") != "completed":
            return JSONResponse(
                {"status": "error", "message": "Job not found or not completed"},
                status_code=404,
            )

        audio_name = f"{request.job_id}.mp3"
        audio_path = uploads / audio_name

        if audio_path.exists():
            return {"status": "completed", "audio_url": f"/uploads/{audio_name}"}

        if job.get("audio_status") == "generating":
            return {"status": "generating", "message": "Audio is being generated..."}

        analysis_text: str = job.get("result", {}).get("analysis", "")
        if not analysis_text:
            return JSONResponse(
                {"status": "error", "message": "No analysis text to convert"},
                status_code=400,
            )

        _jobs[request.job_id]["audio_status"] = "generating"
        tts_lang = request.language  # capture before closure

        def _audio_task() -> None:
            t0 = time.time()
            try:
                generate_audio(analysis_text, audio_path, lang=tts_lang)
                elapsed = round(time.time() - t0, 2)
                print(f"[{request.job_id[:8]}] Audio generated in {elapsed}s")
                _jobs[request.job_id]["audio_status"] = "completed"
                if "result" in _jobs[request.job_id]:
                    _jobs[request.job_id]["result"]["audio_url"] = f"/uploads/{audio_name}"
            except Exception as exc:
                print(f"[{request.job_id[:8]}] Audio failed: {exc}")
                _jobs[request.job_id]["audio_status"] = "failed"

        background_tasks.add_task(_audio_task)
        return {"status": "generating", "message": "Audio generation started."}

    @application.get("/audio-status/{job_id}")
    def audio_status(job_id: str) -> dict[str, str]:
        """Check whether on-demand audio is ready."""
        job = _jobs.get(job_id)
        if not job:
            return {"status": "not_found"}

        audio_name = f"{job_id}.mp3"
        if (uploads / audio_name).exists():
            return {"status": "completed", "audio_url": f"/uploads/{audio_name}"}

        return {"status": job.get("audio_status", "not_started")}

    # ── Translation ────────────────────────────────────────────────────

    @application.post("/translate", response_model=None)
    async def translate(request: TranslationRequest) -> JSONResponse | dict[str, str]:
        """Translate a completed analysis to Arabic via Gemini."""
        if request.job_id not in _jobs:
            return JSONResponse({"status": "error", "message": "Job not found"}, status_code=404)

        try:
            arabic = translate_medical_report(request.text)
            if arabic.startswith("Error"):
                return JSONResponse({"status": "error", "message": arabic}, status_code=502)

            # Generate Arabic PDF in background
            arabic_pdf_url: str | None = None
            try:
                ar_pdf_name = f"{request.job_id}_report_ar.pdf"
                ar_pdf_path = settings.uploads_dir / ar_pdf_name
                generate_arabic_pdf_report(arabic, ar_pdf_path)
                arabic_pdf_url = f"/uploads/{ar_pdf_name}" if ar_pdf_path.exists() else None
            except Exception as pdf_exc:
                print(f"[{request.job_id[:8]}] Arabic PDF failed: {pdf_exc}")

            if "result" in _jobs[request.job_id]:
                _jobs[request.job_id]["result"]["arabic_analysis"] = arabic
                _jobs[request.job_id]["result"]["arabic_pdf_url"] = arabic_pdf_url
            return {"status": "success", "arabic_text": arabic, "arabic_pdf_url": arabic_pdf_url}
        except Exception as exc:
            return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)

    return application


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _run_pipeline(
    job_id: str,
    file_path: str,
    age: str | None,
    gender: str | None,
) -> None:
    """Execute the analysis pipeline: OCR → AI → PDF."""
    settings = get_settings()
    tag = job_id[:8]

    try:
        t_start = time.time()
        _jobs[job_id]["status"] = "processing"
        _jobs[job_id]["message"] = "Extracting text from document (OCR)..."

        # Step 1: OCR
        t0 = time.time()
        ocr_text = perform_ocr(file_path, lang=settings.ocr_languages)
        ocr_s = round(time.time() - t0, 2)

        if not ocr_text or len(ocr_text) < 10:
            msg = (
                ocr_text
                if (ocr_text and "Error" in ocr_text)
                else "Could not read text from file. Check image quality."
            )
            raise RuntimeError(msg)

        print(f"[{tag}] OCR: {len(ocr_text)} chars in {ocr_s}s")

        # Step 2: AI analysis
        _jobs[job_id]["message"] = "AI Doctor is analyzing your results..."
        t0 = time.time()
        analysis = analyze_text(ocr_text, age, gender)
        ai_s = round(time.time() - t0, 2)

        if analysis.startswith("Error"):
            _jobs[job_id].update(status="failed", error=analysis)
            return

        print(f"[{tag}] AI analysis completed in {ai_s}s")

        # Step 3: PDF report
        _jobs[job_id]["message"] = "Generating PDF Report..."
        t0 = time.time()
        pdf_name = f"{job_id}_report.pdf"
        pdf_path = settings.uploads_dir / pdf_name
        generate_pdf_report(analysis, pdf_path)
        pdf_s = round(time.time() - t0, 2)

        total = round(time.time() - t_start, 2)
        print(f"[{tag}] Pipeline: {total}s (OCR:{ocr_s} AI:{ai_s} PDF:{pdf_s})")

        _jobs[job_id].update(
            status="completed",
            message="Analysis complete!",
            result={
                "job_id": job_id,
                "analysis": analysis,
                "pdf_url": f"/uploads/{pdf_name}" if pdf_path.exists() else None,
                "audio_url": None,
                "timing": {
                    "ocr_seconds": ocr_s,
                    "ai_seconds": ai_s,
                    "pdf_seconds": pdf_s,
                    "total_seconds": total,
                },
            },
        )

    except Exception as exc:
        print(f"[{tag}] Pipeline error: {exc}")
        _jobs[job_id].update(status="failed", error=str(exc), message="An error occurred.")


# Module-level app instance — used by ``uvicorn tahalilai.app:app``
app = create_app()
