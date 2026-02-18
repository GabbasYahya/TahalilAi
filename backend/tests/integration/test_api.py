"""Integration tests for the FastAPI endpoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


class TestHealthCheck:
    """Tests for ``GET /``."""

    def test_returns_online(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "online"
        assert "TahalilAI" in data["message"]


class TestStatusEndpoint:
    """Tests for ``GET /status/{job_id}``."""

    def test_nonexistent_job(self, client: TestClient) -> None:
        resp = client.get("/status/nonexistent-id")
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_found"


class TestAnalyzeEndpoint:
    """Tests for ``POST /analyze``."""

    @patch("tahalilai.app.generate_pdf_report")
    @patch("tahalilai.app.analyze_text")
    @patch("tahalilai.app.perform_ocr")
    def test_sync_analysis(
        self,
        mock_ocr: MagicMock,
        mock_analyze: MagicMock,
        mock_pdf: MagicMock,
        client: TestClient,
        tmp_image: Path,
    ) -> None:
        mock_ocr.return_value = "Hemoglobin: 14.5 g/dL - Normal range"
        mock_analyze.return_value = "**Summary**: Normal blood work."
        mock_pdf.return_value = Path("/dummy/report.pdf")

        with open(tmp_image, "rb") as f:
            resp = client.post(
                "/analyze",
                files={"file": ("test.png", f, "image/png")},
                data={"age": "30", "gender": "male", "wait_for_result": "true"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert "Summary" in data["result"]["analysis"]

    @patch("tahalilai.app.generate_pdf_report")
    @patch("tahalilai.app.analyze_text")
    @patch("tahalilai.app.perform_ocr")
    def test_async_analysis(
        self,
        mock_ocr: MagicMock,
        mock_analyze: MagicMock,
        mock_pdf: MagicMock,
        client: TestClient,
        tmp_image: Path,
    ) -> None:
        mock_ocr.return_value = "Glucose: 95 mg/dL"
        mock_analyze.return_value = "**Summary**: Normal glucose levels."
        mock_pdf.return_value = Path("/dummy/report.pdf")

        with open(tmp_image, "rb") as f:
            resp = client.post(
                "/analyze",
                files={"file": ("test.png", f, "image/png")},
                data={"age": "25", "gender": "female"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert "job_id" in data

        # Background task should have completed in TestClient
        status = client.get(f"/status/{data['job_id']}").json()
        assert status["status"] == "completed"

    def test_rejects_invalid_file(self, client: TestClient, tmp_path: Path) -> None:
        txt = tmp_path / "test.txt"
        txt.write_text("not an image", encoding="utf-8")

        with open(txt, "rb") as f:
            resp = client.post(
                "/analyze",
                files={"file": ("test.txt", f, "text/plain")},
            )

        assert resp.status_code == 400
        assert "Security" in resp.json()["message"] or "Invalid" in resp.json()["message"]


class TestTranslateEndpoint:
    """Tests for ``POST /translate``."""

    def test_job_not_found(self, client: TestClient) -> None:
        resp = client.post(
            "/translate",
            json={"text": "Hello", "job_id": "nonexistent"},
        )
        assert resp.status_code == 404


class TestAudioEndpoints:
    """Tests for audio generation endpoints."""

    def test_audio_status_not_found(self, client: TestClient) -> None:
        resp = client.get("/audio-status/nonexistent")
        assert resp.json()["status"] == "not_found"

    def test_generate_audio_no_job(self, client: TestClient) -> None:
        resp = client.post("/generate-audio", json={"job_id": "nonexistent"})
        assert resp.status_code == 404
