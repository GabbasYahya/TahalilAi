"""Unit tests for the email sender service."""

from __future__ import annotations

import smtplib
from pathlib import Path
from unittest.mock import MagicMock, patch

from tahalilai.services.email_sender import (
    _build_message,
    _make_pdf_attachment,
    send_report_email,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_settings(*, sender: str = "test@gmail.com", password: str = "fake-pass"):
    """Build a fake Settings object with SMTP fields."""
    s = MagicMock()
    s.smtp_host = "smtp.gmail.com"
    s.smtp_port = 465
    s.smtp_sender_email = sender
    s.smtp_app_password = password
    return s


# ---------------------------------------------------------------------------
# send_report_email
# ---------------------------------------------------------------------------


class TestSendReportEmail:
    """Tests for the main ``send_report_email`` function."""

    def test_missing_credentials_returns_error(self) -> None:
        """If SMTP creds are empty, return an error immediately (don't try to connect)."""
        with patch("tahalilai.services.email_sender.get_settings") as mock:
            mock.return_value = _mock_settings(sender="", password="")
            result = send_report_email("patient@example.com", "Subject", "Body")
        assert result["status"] == "error"
        assert "SMTP" in result["message"]

    def test_pdf_not_found_returns_error(self, tmp_path: Path) -> None:
        """If a PDF path is given but the file doesn't exist, return an error."""
        with patch("tahalilai.services.email_sender.get_settings") as mock:
            mock.return_value = _mock_settings()
            result = send_report_email(
                "patient@example.com",
                "Subject",
                "Body",
                pdf_path=tmp_path / "nonexistent.pdf",
            )
        assert result["status"] == "error"
        assert "not found" in result["message"]

    @patch("tahalilai.services.email_sender.smtplib")
    def test_successful_send_without_pdf(self, mock_smtplib: MagicMock) -> None:
        """Happy path: credentials set, no PDF, email sends successfully."""
        mock_server = MagicMock()
        mock_smtplib.SMTP_SSL.return_value.__enter__ = MagicMock(
            return_value=mock_server
        )
        mock_smtplib.SMTP_SSL.return_value.__exit__ = MagicMock(return_value=False)

        with patch("tahalilai.services.email_sender.get_settings") as mock_settings:
            mock_settings.return_value = _mock_settings()
            result = send_report_email("patient@example.com", "Report", "Your results")

        assert result["status"] == "sent"
        mock_server.login.assert_called_once_with("test@gmail.com", "fake-pass")
        mock_server.sendmail.assert_called_once()

    @patch("tahalilai.services.email_sender.smtplib")
    def test_successful_send_with_pdf(
        self, mock_smtplib: MagicMock, tmp_path: Path
    ) -> None:
        """Happy path with a PDF attachment."""
        pdf = tmp_path / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake content")

        mock_server = MagicMock()
        mock_smtplib.SMTP_SSL.return_value.__enter__ = MagicMock(
            return_value=mock_server
        )
        mock_smtplib.SMTP_SSL.return_value.__exit__ = MagicMock(return_value=False)

        with patch("tahalilai.services.email_sender.get_settings") as mock_settings:
            mock_settings.return_value = _mock_settings()
            result = send_report_email(
                "patient@example.com", "Report", "Your results", pdf_path=pdf
            )

        assert result["status"] == "sent"

    @patch("tahalilai.services.email_sender._send_via_smtp")
    def test_authentication_error(self, mock_send: MagicMock) -> None:
        """SMTPAuthenticationError → return a clear error message."""
        mock_send.side_effect = smtplib.SMTPAuthenticationError(
            535, b"Bad credentials"
        )

        with patch("tahalilai.services.email_sender.get_settings") as mock_settings:
            mock_settings.return_value = _mock_settings()
            result = send_report_email("patient@example.com", "Subject", "Body")

        assert result["status"] == "error"
        assert "authentication" in result["message"].lower()

    @patch("tahalilai.services.email_sender._send_via_smtp")
    def test_generic_error(self, mock_send: MagicMock) -> None:
        """Any other exception → catch it and return an error dict."""
        mock_send.side_effect = ConnectionRefusedError("Connection refused")

        with patch("tahalilai.services.email_sender.get_settings") as mock_settings:
            mock_settings.return_value = _mock_settings()
            result = send_report_email("patient@example.com", "Subject", "Body")

        assert result["status"] == "error"
        assert "Failed to send" in result["message"]


# ---------------------------------------------------------------------------
# _build_message
# ---------------------------------------------------------------------------


class TestBuildMessage:
    """Tests for the MIME message builder."""

    def test_headers_are_correct(self) -> None:
        msg = _build_message("a@b.com", "c@d.com", "Test Subject", "Body text", None)
        assert msg["From"] == "a@b.com"
        assert msg["To"] == "c@d.com"
        assert msg["Subject"] == "Test Subject"

    def test_without_attachment_has_one_part(self) -> None:
        """Text-only email should have exactly one MIME part (the body)."""
        msg = _build_message("a@b.com", "c@d.com", "Subj", "Body", None)
        parts = msg.get_payload()
        assert len(parts) == 1

    def test_with_attachment_has_two_parts(self, tmp_path: Path) -> None:
        """Email with PDF should have two MIME parts (body + attachment)."""
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 test")
        msg = _build_message("a@b.com", "c@d.com", "Subj", "Body", pdf)
        parts = msg.get_payload()
        assert len(parts) == 2


# ---------------------------------------------------------------------------
# _make_pdf_attachment
# ---------------------------------------------------------------------------


class TestMakePdfAttachment:
    """Tests for the PDF attachment builder."""

    def test_attachment_has_correct_filename(self, tmp_path: Path) -> None:
        pdf = tmp_path / "my_report.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        part = _make_pdf_attachment(pdf)
        assert "my_report.pdf" in part["Content-Disposition"]

    def test_attachment_is_base64_encoded(self, tmp_path: Path) -> None:
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        part = _make_pdf_attachment(pdf)
        assert part["Content-Transfer-Encoding"] == "base64"
