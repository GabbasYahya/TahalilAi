"""FastAPI application for TahalilAI medical report analysis.

Provides endpoints for:
* ``POST /analyze`` — upload a medical report for OCR + AI analysis.
* ``GET  /status/{job_id}`` — poll for analysis progress / results.
* ``POST /generate-audio`` — on-demand TTS for completed analyses.
* ``GET  /audio-status/{job_id}`` — poll for audio readiness.
* ``POST /chat`` — follow-up Q&A about analysis results.
* ``POST /translate`` — translate an analysis to Arabic via Gemini.
* ``POST /send-email`` — send report via Gmail SMTP.
* ``POST /send-whatsapp`` — send report summary via WhatsApp.
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
from tahalilai.services.cleanup import run_cleanup_loop
from tahalilai.schemas import (
    AudioRequest,
    ChatRequest,
    EmailRequest,
    StructuredAnalysis,
    TranslationRequest,
    WhatsAppRequest,
)
from tahalilai.services.analyzer import analyze_text
from tahalilai.services.renderer import render_markdown
from tahalilai.services.chat import answer_question
from tahalilai.services.email_sender import send_report_email
from tahalilai.services.ocr import perform_ocr
from tahalilai.services.report import generate_arabic_pdf_report, generate_pdf_report
from tahalilai.services.translator import translate_medical_report
from tahalilai.services.tts import generate_audio
from tahalilai.services.whatsapp import send_whatsapp_message
from tahalilai.utils.security import sanitize_filename, validate_file

# In-memory job store — replace with Redis / a database for production
_jobs: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _lifespan(_app: FastAPI):  # type: ignore[no-untyped-def]
    """Startup / shutdown lifecycle handler.

    * Launches a background cleanup task that periodically removes expired
      files from ``uploads/`` (age limit and interval from config).
    * TTS model is still lazy-loaded on the first audio request.
    """
    import asyncio

    from tahalilai.database import Base, engine
    from tahalilai.models import Doctor, HealthFacility  # noqa: F401 — register models

    Base.metadata.create_all(bind=engine)

    cfg = get_settings()
    cleanup_task = asyncio.create_task(
        run_cleanup_loop(
            uploads_dir=cfg.uploads_dir,
            max_age_hours=cfg.uploads_max_age_hours,
            interval_seconds=cfg.uploads_cleanup_interval_seconds,
        )
    )
    print(
        f"TahalilAI server ready — upload cleanup every "
        f"{cfg.uploads_cleanup_interval_seconds}s, "
        f"max age {cfg.uploads_max_age_hours}h."
    )

    yield

    # Cancel the cleanup loop gracefully on shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
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

    # ── Routers ─────────────────────────────────────────────────────
    from tahalilai.routers.doctors import router as doctors_router
    from tahalilai.routers.hospitals import router as hospitals_router

    application.include_router(doctors_router)
    application.include_router(hospitals_router)

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
    _CITY_FIELD = Form(None)
    _WAIT_FIELD = Form(False)

    @application.post("/analyze")
    async def analyze(
        background_tasks: BackgroundTasks,
        file: UploadFile = _FILE_FIELD,
        age: str = _AGE_FIELD,
        gender: str = _GENDER_FIELD,
        city: str = _CITY_FIELD,
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
                        pool, _run_pipeline, job_id, str(file_path), age, gender, city
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
            _jobs[job_id] = {"status": "queued", "submitted_at": time.time(), "age": age, "gender": gender, "city": city}
            background_tasks.add_task(_run_pipeline, job_id, str(file_path), age, gender, city)
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

    # ── Follow-up chat ─────────────────────────────────────────────────

    @application.post("/chat", response_model=None)
    async def chat(request: ChatRequest) -> JSONResponse | dict[str, str]:
        """Answer a follow-up question about a completed analysis."""
        job = _jobs.get(request.job_id)
        if not job:
            return JSONResponse(
                {"status": "error", "message": "Job not found"}, status_code=404
            )
        if job.get("status") != "completed":
            return JSONResponse(
                {"status": "error", "message": "Analysis not yet completed"},
                status_code=400,
            )

        ocr_text: str = job.get("ocr_text", "")
        analysis: str = job.get("result", {}).get("analysis", "")
        history: list[dict[str, str]] = job.get("conversation", [])

        if not analysis:
            return JSONResponse(
                {"status": "error", "message": "No analysis found for this job"},
                status_code=400,
            )

        answer = answer_question(ocr_text, analysis, history, request.message)

        if answer.startswith("Error"):
            return JSONResponse({"status": "error", "message": answer}, status_code=502)

        # Persist conversation history in the job store
        history.append({"role": "user", "content": request.message})
        history.append({"role": "assistant", "content": answer})
        _jobs[request.job_id]["conversation"] = history

        return {"status": "success", "answer": answer}

    # ── Translation ────────────────────────────────────────────────────

    @application.post("/translate", response_model=None)
    async def translate(request: TranslationRequest) -> JSONResponse | dict[str, str]:
        """Translate a completed analysis to Arabic via Gemini."""
        # Job may no longer be in memory (e.g. after a server restart).
        # We still translate the text — we just skip writing the result back.
        job_in_memory = request.job_id in _jobs

        try:
            arabic = translate_medical_report(request.text)
            if arabic.startswith("Error"):
                return JSONResponse({"status": "error", "message": arabic}, status_code=502)

            # Generate Arabic PDF
            arabic_pdf_url: str | None = None
            try:
                ar_pdf_name = f"{request.job_id}_report_ar.pdf"
                ar_pdf_path = settings.uploads_dir / ar_pdf_name
                job_result = _jobs[request.job_id].get("result", {}) if job_in_memory else {}
                generate_arabic_pdf_report(
                    arabic,
                    ar_pdf_path,
                    recommended_doctors=job_result.get("recommended_doctors"),
                    urgency=job_result.get("urgency", "routine"),
                )
                arabic_pdf_url = f"/uploads/{ar_pdf_name}" if ar_pdf_path.exists() else None
            except Exception as pdf_exc:
                print(f"[{request.job_id[:8]}] Arabic PDF failed: {pdf_exc}")

            if job_in_memory and "result" in _jobs[request.job_id]:
                _jobs[request.job_id]["result"]["arabic_analysis"] = arabic
                _jobs[request.job_id]["result"]["arabic_pdf_url"] = arabic_pdf_url
            return {"status": "success", "arabic_text": arabic, "arabic_pdf_url": arabic_pdf_url}
        except Exception as exc:
            return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)

    # ── Email delivery ─────────────────────────────────────────────────

    @application.post("/send-email", response_model=None)
    async def send_email_endpoint(
        request: EmailRequest,
        background_tasks: BackgroundTasks,
    ) -> JSONResponse | dict[str, str]:
        """Send the analysis report to the patient via Gmail SMTP.

        Why BackgroundTasks?
          Sending an email takes 2-5 seconds (network round-trip to Gmail).
          We don't want the user's browser to hang waiting. So we:
          1. Return {"status": "sending"} immediately (fast response).
          2. Actually send the email in the background.
        """
        job = _jobs.get(request.job_id)
        if not job or job.get("status") != "completed":
            return JSONResponse(
                {"status": "error", "message": "Job not found or not completed"},
                status_code=404,
            )

        analysis: str = job.get("result", {}).get("analysis", "")
        if not analysis:
            return JSONResponse(
                {"status": "error", "message": "No analysis text available"},
                status_code=400,
            )

        # Build the PDF path from the job result (may not exist)
        pdf_url: str | None = job.get("result", {}).get("pdf_url")
        pdf_path = settings.uploads_dir / f"{request.job_id}_report.pdf" if pdf_url else None

        subject = "Your TahalilAI Lab Report"
        body = (
            "Hello,\n\n"
            "Your medical lab report analysis is complete. "
            "Here is a summary:\n\n"
            f"{analysis[:2000]}\n\n"
            "Please find the full PDF report attached.\n\n"
            "Best regards,\nTahalilAI"
        )

        # This closure runs AFTER the HTTP response is sent back
        def _email_task() -> None:
            result = send_report_email(
                recipient_email=request.recipient_email,
                subject=subject,
                body_text=body,
                pdf_path=pdf_path,
            )
            print(f"[{request.job_id[:8]}] Email: {result}")

        background_tasks.add_task(_email_task)
        return {"status": "sending", "message": "Email is being sent."}

    # ── WhatsApp delivery ──────────────────────────────────────────────

    @application.post("/send-whatsapp", response_model=None)
    async def send_whatsapp_endpoint(
        request: WhatsAppRequest,
        background_tasks: BackgroundTasks,
    ) -> JSONResponse | dict[str, str]:
        """Send the analysis summary to the patient via WhatsApp."""
        job = _jobs.get(request.job_id)
        if not job or job.get("status") != "completed":
            return JSONResponse(
                {"status": "error", "message": "Job not found or not completed"},
                status_code=404,
            )

        analysis: str = job.get("result", {}).get("analysis", "")
        if not analysis:
            return JSONResponse(
                {"status": "error", "message": "No analysis text available"},
                status_code=400,
            )

        message = (
            "TahalilAI Lab Report\n"
            "====================\n\n"
            f"{analysis}"
        )

        def _whatsapp_task() -> None:
            result = send_whatsapp_message(
                to_phone=request.to_phone,
                message_text=message,
            )
            print(f"[{request.job_id[:8]}] WhatsApp: {result}")

        background_tasks.add_task(_whatsapp_task)
        return {"status": "sending", "message": "WhatsApp message is being sent."}

    return application


# ---------------------------------------------------------------------------
# EN → FR specialty mapping (structured analysis returns English names)
# ---------------------------------------------------------------------------

_EN_TO_FR_SPECIALITY: dict[str, str] = {
    "general practitioner": "Médecin généraliste",
    "cardiologist": "Cardiologue",
    "dermatologist": "Dermatologue",
    "endocrinologist": "Endocrinologue",
    "gastroenterologist": "Gastro-entérologue",
    "gynecologist": "Gynécologue",
    "obstetrician": "Gynécologue obstétricien",
    "nephrologist": "Néphrologue",
    "neurologist": "Neurologue",
    "ophthalmologist": "Ophtalmologue",
    "ent specialist": "Oto-rhino-laryngologue",
    "otolaryngologist": "Oto-rhino-laryngologue",
    "pediatrician": "Pédiatre",
    "pulmonologist": "Pneumologue",
    "psychiatrist": "Psychiatre",
    "radiologist": "Radiologue",
    "rheumatologist": "Rhumatologue",
    "urologist": "Urologue",
    "diabetologist": "Diabétologue",
    "allergist": "Allergologue",
    "internist": "Médecin interniste",
    "internal medicine": "Médecin interniste",
    "dentist": "Dentiste",
    "oncologist": "Oncologue",
    "hematologist": "Hématologue",
    "nutritionist": "Nutritionniste",
    "physiotherapist": "Kinésithérapeute",
    "psychologist": "Psychologue",
    "anesthesiologist": "Anesthésiste-réanimateur",
    "neurosurgeon": "Neurochirurgien",
    "general surgeon": "Chirurgien général",
    "orthopedic surgeon": "Traumatologue-orthopédiste",
    "hepatologist": "Gastro-entérologue",
}


def _map_specialties_to_french(english_specs: list[str]) -> list[str]:
    """Map English specialty names to French canonical names for DB lookup."""
    result: list[str] = []
    for spec in english_specs:
        key = spec.lower().strip()
        if key in _EN_TO_FR_SPECIALITY:
            result.append(_EN_TO_FR_SPECIALITY[key])
        else:
            # Try partial matching
            for en, fr in _EN_TO_FR_SPECIALITY.items():
                if en in key or key in en:
                    result.append(fr)
                    break
            else:
                # Pass through as-is (may already be French)
                result.append(spec)
    return result


def _lookup_region_for_city(city: str, db_session) -> str | None:  # type: ignore[type-arg]
    """Look up the region name for a given city/delegation from the hospital DB."""
    try:
        from tahalilai.models import HealthFacility
        from sqlalchemy import func

        row = (
            db_session.query(HealthFacility.region)
            .filter(HealthFacility.delegation.ilike(f"%{city}%"))
            .first()
        )
        return row[0] if row else None
    except Exception:
        return None


def _urgency_from_status(status_value: str) -> str:
    """Derive urgency level from overall_status enum value."""
    if status_value in ("normal", "mostly_normal"):
        return "routine"
    if status_value == "abnormal":
        return "soon"
    return "urgent"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _run_pipeline(
    job_id: str,
    file_path: str,
    age: str | None,
    gender: str | None,
    city: str | None = None,
) -> None:
    """Execute the analysis pipeline: OCR -> AI -> Recommend -> PDF."""
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
        _jobs[job_id]["ocr_text"] = ocr_text

        # Step 2: AI analysis
        _jobs[job_id]["message"] = "AI Doctor is analyzing your results..."
        t0 = time.time()
        analysis_result = analyze_text(ocr_text, age, gender)
        ai_s = round(time.time() - t0, 2)

        # Handle structured vs error/string result
        structured: StructuredAnalysis | None = None
        structured_dict: dict | None = None
        if isinstance(analysis_result, StructuredAnalysis):
            structured = analysis_result
            analysis_markdown = render_markdown(structured)
            structured_dict = structured.model_dump(mode="json")
        elif isinstance(analysis_result, str) and analysis_result.startswith("Error"):
            _jobs[job_id].update(status="failed", error=analysis_result)
            return
        else:
            # Safety net: plain string (shouldn't happen with new code)
            analysis_markdown = str(analysis_result)

        print(f"[{tag}] AI analysis completed in {ai_s}s")

        # Step 2.5: Doctor + hospital recommendation
        _jobs[job_id]["message"] = "Finding recommended doctors and hospitals..."
        recommendation = {"specialities": ["Médecin généraliste"], "urgency": "routine"}
        recommended_doctors: list[dict] = []
        recommended_hospitals: list[dict] = []
        try:
            from tahalilai.services.recommender import (
                extract_recommended_specialities,
                find_recommended_doctors,
                find_recommended_hospitals,
            )
            from tahalilai.database import SessionLocal

            # Extract specialties from structured data (skip 2nd Gemini call)
            if structured and structured.recommended_specialties:
                en_specs = [s.specialty for s in structured.recommended_specialties[:2]]
                fr_specs = _map_specialties_to_french(en_specs)
                urgency = _urgency_from_status(
                    structured.report_summary.overall_status.value
                )
                recommendation = {"specialities": fr_specs, "urgency": urgency}
            else:
                recommendation = extract_recommended_specialities(analysis_markdown)

            db = SessionLocal()
            try:
                # Resolve region from city for better hospital filtering
                region = _lookup_region_for_city(city, db) if city else None

                recommended_doctors = find_recommended_doctors(
                    specialities=recommendation.get("specialities", []),
                    city=city,
                    db=db,
                )
                hospital_objects = find_recommended_hospitals(
                    specialities=recommendation.get("specialities", []),
                    delegation=city,
                    region=region,
                    db=db,
                    limit_per_speciality=2,
                )
                recommended_hospitals = [
                    {
                        "id": h.id,
                        "name": h.name,
                        "category_code": h.category_code,
                        "category_name": h.category_name,
                        "facility_type": h.facility_type,
                        "region": h.region,
                        "delegation": h.delegation,
                        "commune": h.commune or "",
                        "departments": h.departments or "",
                        "phone": h.phone or "",
                        "address": h.address or "",
                    }
                    for h in hospital_objects
                ]
            finally:
                db.close()
            print(
                f"[{tag}] Recommended: {recommendation.get('specialities', [])} "
                f"({len(recommended_doctors)} doctors, {len(recommended_hospitals)} hospitals)"
            )
        except Exception as exc:
            print(f"[{tag}] Recommendation failed: {exc}")

        # Step 3: PDF report
        _jobs[job_id]["message"] = "Generating PDF Report..."
        t0 = time.time()
        pdf_name = f"{job_id}_report.pdf"
        pdf_path = settings.uploads_dir / pdf_name
        generate_pdf_report(
            analysis_markdown,
            pdf_path,
            recommended_doctors=recommended_doctors,
            urgency=recommendation.get("urgency", "routine"),
            structured=structured,
        )
        pdf_s = round(time.time() - t0, 2)

        total = round(time.time() - t_start, 2)
        print(f"[{tag}] Pipeline: {total}s (OCR:{ocr_s} AI:{ai_s} PDF:{pdf_s})")

        _jobs[job_id].update(
            status="completed",
            message="Analysis complete!",
            result={
                "job_id": job_id,
                "analysis": analysis_markdown,
                "structured_analysis": structured_dict,
                "pdf_url": f"/uploads/{pdf_name}" if pdf_path.exists() else None,
                "audio_url": None,
                "recommended_specialities": recommendation.get("specialities", []),
                "urgency": recommendation.get("urgency", "routine"),
                "recommended_doctors": recommended_doctors,
                "recommended_hospitals": recommended_hospitals,
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
