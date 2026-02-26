"""Unit tests for TTS service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from tahalilai.services.tts import _strip_markdown, generate_audio


class TestStripMarkdown:
    """Tests for the markdown-stripping helper."""

    def test_removes_bold_markers(self) -> None:
        assert _strip_markdown("**bold text**") == "bold text"

    def test_removes_header_markers(self) -> None:
        assert _strip_markdown("## Header") == " Header"

    def test_strips_links(self) -> None:
        assert _strip_markdown("[click here](https://example.com)") == "click here"

    def test_preserves_plain_text(self) -> None:
        assert _strip_markdown("Normal text") == "Normal text"


class TestGenerateAudio:
    """Tests for ``generate_audio`` with mocked gTTS."""

    @patch("tahalilai.services.tts.gTTS")
    def test_gtts_fallback(self, mock_gtts_cls: MagicMock, tmp_path: Path) -> None:
        mock_tts = MagicMock()
        mock_gtts_cls.return_value = mock_tts

        output = tmp_path / "test.mp3"
        result = generate_audio("Hello world", output, lang="en")

        assert result is True
        mock_gtts_cls.assert_called_once()
        mock_tts.save.assert_called_once_with(str(output))

    @patch("tahalilai.services.tts.gTTS")
    def test_gtts_failure(self, mock_gtts_cls: MagicMock, tmp_path: Path) -> None:
        mock_gtts_cls.side_effect = Exception("Network error")

        output = tmp_path / "fail.mp3"
        result = generate_audio("Hello", output)

        assert result is False
