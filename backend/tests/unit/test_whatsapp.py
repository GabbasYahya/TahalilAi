"""Unit tests for the WhatsApp messaging service."""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

from tahalilai.services.whatsapp import (
    _extract_message_id,
    _parse_api_error,
    _truncate_message,
    send_whatsapp_document,
    send_whatsapp_message,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_settings(*, token: str = "fake-token", phone_id: str = "123456"):
    """Build a fake Settings object with WhatsApp fields."""
    s = MagicMock()
    s.whatsapp_access_token = token
    s.whatsapp_phone_number_id = phone_id
    s.whatsapp_api_version = "v19.0"
    return s


def _mock_urlopen_response(body: dict) -> MagicMock:
    """Create a mock context-manager response for ``urllib.request.urlopen``.

    ``urlopen`` is used as a context manager (``with urlopen(...) as resp``),
    so we need to mock both ``__enter__`` and ``__exit__``.
    """
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(body).encode("utf-8")
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# _truncate_message
# ---------------------------------------------------------------------------


class TestTruncateMessage:
    """Tests for the message truncation helper."""

    def test_short_message_unchanged(self) -> None:
        assert _truncate_message("Hello") == "Hello"

    def test_exact_limit_unchanged(self) -> None:
        text = "a" * 4096
        assert _truncate_message(text) == text
        assert len(_truncate_message(text)) == 4096

    def test_long_message_truncated_with_ellipsis(self) -> None:
        text = "a" * 5000
        result = _truncate_message(text)
        assert len(result) == 4096
        assert result.endswith("...")


# ---------------------------------------------------------------------------
# _extract_message_id
# ---------------------------------------------------------------------------


class TestExtractMessageId:
    """Tests for message ID extraction from the API response."""

    def test_valid_response(self) -> None:
        body = {"messages": [{"id": "wamid.abc123"}]}
        assert _extract_message_id(body) == "wamid.abc123"

    def test_missing_messages_key(self) -> None:
        assert _extract_message_id({}) == "unknown"

    def test_empty_messages_list(self) -> None:
        assert _extract_message_id({"messages": []}) == "unknown"


# ---------------------------------------------------------------------------
# _parse_api_error
# ---------------------------------------------------------------------------


class TestParseApiError:
    """Tests for Meta API error response parsing."""

    def test_valid_error_json(self) -> None:
        raw = json.dumps({"error": {"message": "Invalid token"}})
        assert _parse_api_error(raw) == "Invalid token"

    def test_invalid_json_returns_raw(self) -> None:
        assert _parse_api_error("not json at all") == "not json at all"


# ---------------------------------------------------------------------------
# send_whatsapp_message
# ---------------------------------------------------------------------------


class TestSendWhatsappMessage:
    """Tests for ``send_whatsapp_message``."""

    def test_missing_credentials_returns_error(self) -> None:
        with patch("tahalilai.services.whatsapp.get_settings") as mock:
            mock.return_value = _mock_settings(token="", phone_id="")
            result = send_whatsapp_message("213555000000", "Hello")
        assert result["status"] == "error"
        assert "WHATSAPP" in result["message"]

    @patch("tahalilai.services.whatsapp.urllib.request.urlopen")
    def test_successful_send(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _mock_urlopen_response(
            {"messages": [{"id": "wamid.test123"}]}
        )
        with patch("tahalilai.services.whatsapp.get_settings") as mock_settings:
            mock_settings.return_value = _mock_settings()
            result = send_whatsapp_message("213555000000", "Your report is ready")

        assert result["status"] == "sent"
        assert result["message_id"] == "wamid.test123"

    @patch("tahalilai.services.whatsapp.urllib.request.urlopen")
    def test_api_http_error(self, mock_urlopen: MagicMock) -> None:
        """Meta API returns 401 → parse error body and return error dict."""
        error_body = json.dumps({"error": {"message": "Invalid token"}}).encode()
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://graph.facebook.com/...",
            code=401,
            msg="Unauthorized",
            hdrs=None,  # type: ignore[arg-type]
            fp=MagicMock(read=MagicMock(return_value=error_body)),
        )
        with patch("tahalilai.services.whatsapp.get_settings") as mock_settings:
            mock_settings.return_value = _mock_settings()
            result = send_whatsapp_message("213555000000", "Hello")

        assert result["status"] == "error"
        assert "Invalid token" in result["message"]

    @patch("tahalilai.services.whatsapp.urllib.request.urlopen")
    def test_network_error(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = ConnectionError("Network unreachable")
        with patch("tahalilai.services.whatsapp.get_settings") as mock_settings:
            mock_settings.return_value = _mock_settings()
            result = send_whatsapp_message("213555000000", "Hello")

        assert result["status"] == "error"
        assert "Failed to send" in result["message"]


# ---------------------------------------------------------------------------
# send_whatsapp_document
# ---------------------------------------------------------------------------


class TestSendWhatsappDocument:
    """Tests for ``send_whatsapp_document``."""

    def test_missing_credentials_returns_error(self) -> None:
        with patch("tahalilai.services.whatsapp.get_settings") as mock:
            mock.return_value = _mock_settings(token="", phone_id="")
            result = send_whatsapp_document(
                "213555000000", "https://example.com/report.pdf"
            )
        assert result["status"] == "error"

    @patch("tahalilai.services.whatsapp.urllib.request.urlopen")
    def test_successful_document_send(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _mock_urlopen_response(
            {"messages": [{"id": "wamid.doc456"}]}
        )
        with patch("tahalilai.services.whatsapp.get_settings") as mock_settings:
            mock_settings.return_value = _mock_settings()
            result = send_whatsapp_document(
                "213555000000",
                "https://example.com/report.pdf",
                filename="lab_report.pdf",
                caption="Your lab results",
            )

        assert result["status"] == "sent"
        assert result["message_id"] == "wamid.doc456"
