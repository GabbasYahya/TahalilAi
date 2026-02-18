"""Benchmark script for the analysis pipeline.

Usage (requires a running server):
    python -m scripts.benchmark

Or directly:
    python scripts/benchmark.py
"""

from __future__ import annotations

import os
import sys
import time

import httpx

API = os.getenv("TAHALILAI_API", "http://127.0.0.1:8000")

# Resolve test image relative to the repo root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)  # backend/
TEST_FILE = os.path.join(
    _REPO_ROOT, "..", "images",
    "Resultats-de-laboratoire-pathologiques-a-ladmission.png",
)


def main() -> None:
    if not os.path.exists(TEST_FILE):
        print(f"Test image not found: {TEST_FILE}")
        sys.exit(1)

    print("=== ANALYSIS PIPELINE BENCHMARK ===")
    print(f"Image: {os.path.basename(TEST_FILE)}")
    t_start = time.time()

    with open(TEST_FILE, "rb") as f:
        resp = httpx.post(
            f"{API}/analyze",
            files={"file": ("test_lab.png", f, "image/png")},
            data={"age": "30", "gender": "male"},
            timeout=None,
        )

    data = resp.json()
    if data.get("status") == "error":
        print(f"ERROR: {data.get('message')}")
        sys.exit(1)

    job_id = data["job_id"]
    print(f"Job {job_id} queued ({time.time() - t_start:.1f}s)")

    # Poll for completion
    while True:
        time.sleep(2)
        status = httpx.get(f"{API}/status/{job_id}", timeout=10).json()
        elapsed = round(time.time() - t_start, 1)
        print(f"  [{elapsed}s] {status['status']} — {status.get('message', '')}")
        if status["status"] in ("completed", "failed"):
            break

    total = round(time.time() - t_start, 2)
    print(f"\n=== TOTAL: {total}s ===")

    if "result" in status:
        timing = status["result"].get("timing", {})
        print(f"  OCR:  {timing.get('ocr_seconds', '?')}s")
        print(f"  AI:   {timing.get('ai_seconds', '?')}s")
        print(f"  PDF:  {timing.get('pdf_seconds', '?')}s")
        print(f"\nFirst 200 chars:\n{status['result']['analysis'][:200]}")
    else:
        print(f"Pipeline failed: {status.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
