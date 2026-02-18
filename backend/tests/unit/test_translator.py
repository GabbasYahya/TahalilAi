"""Unit tests for the Gemini translator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestTranslateMedicalReport:
    """Tests for ``translate_medical_report``."""

    def test_missing_api_key(self) -> None:
        with patch("tahalilai.services.translator.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(gemini_api_key="")
            from tahalilai.services.translator import translate_medical_report

            result = translate_medical_report("Hello")
            assert result.startswith("Error")
            assert "API" in result or "not set" in result

    @patch("tahalilai.services.translator._GEMINI_AVAILABLE", False)
    def test_sdk_not_installed(self) -> None:
        from tahalilai.services.translator import translate_medical_report

        result = translate_medical_report("Hello")
        assert result.startswith("Error")
        assert "SDK" in result or "installed" in result

    @patch("tahalilai.services.translator._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.translator.genai")
    def test_successful_translation(self, mock_genai: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = "الملخص: نتائج فحص الدم طبيعية"
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        with patch("tahalilai.services.translator.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                gemini_api_key="test-key", gemini_model="gemini-2.5-flash"
            )
            from tahalilai.services.translator import translate_medical_report

            result = translate_medical_report("Summary: Normal blood work.")

        assert "الملخص" in result
        assert not result.startswith("Error")

    @patch("tahalilai.services.translator._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.translator.genai")
    def test_api_exception(self, mock_genai: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("API quota exceeded")
        mock_genai.Client.return_value = mock_client

        with patch("tahalilai.services.translator.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                gemini_api_key="test-key", gemini_model="gemini-2.5-flash"
            )
            from tahalilai.services.translator import translate_medical_report

            result = translate_medical_report("Test")

        assert result.startswith("Error")
        assert "quota" in result
