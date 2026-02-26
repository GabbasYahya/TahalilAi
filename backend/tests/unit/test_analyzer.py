"""Unit tests for the LLM analyser."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from tahalilai.services.analyzer import (
    _analyze_with_gemini,
    _analyze_with_local_llm,
    _clean_llm_output,
    analyze_text,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LONG_ANALYSIS = (
    "**Summary**: Blood work is normal.\n\n"
    "**Detailed Analysis**:\n"
    "- **Hemoglobin**: 14.5 (Normal)\n"
    "  *Meaning*: Within acceptable range for this patient profile."
)


def _mock_settings(*, api_key: str = "fake-key", model: str = "gemini-2.5-flash"):
    s = MagicMock()
    s.gemini_api_key = api_key
    s.gemini_model = model
    s.model_timeout = 10
    s.llama_cli_path = "/fake/llama-cli"
    s.model_path = "/fake/model.gguf"
    s.backend_dir = "/fake/backend"
    return s


# ---------------------------------------------------------------------------
# _clean_llm_output
# ---------------------------------------------------------------------------


class TestCleanLlmOutput:
    """Tests for internal output-cleaning logic."""

    def test_strips_speed_stats(self) -> None:
        raw = "Hello world [ Prompt: 12.3 t/s | Generation: 5.6 t/s ]"
        assert _clean_llm_output(raw) == "Hello world"

    def test_strips_exiting(self) -> None:
        assert _clean_llm_output("Result\nExiting...") == "Result"

    def test_keeps_explanation_header(self) -> None:
        raw = "NOISE--- ENGLISH EXPLANATION ---\nClean output"
        cleaned = _clean_llm_output(raw)
        assert cleaned.startswith("--- ENGLISH EXPLANATION ---")
        assert "Clean output" in cleaned

    def test_strips_inst_marker(self) -> None:
        raw = "[INST] prompt [/INST]Actual response"
        assert _clean_llm_output(raw) == "Actual response"

    def test_strips_build_lines(self) -> None:
        raw = "build  : abc123\nmodel  : ministral\nReal output"
        assert "build" not in _clean_llm_output(raw)
        assert "Real output" in _clean_llm_output(raw)

    def test_strips_conversation_banner(self) -> None:
        raw = (
            "available commands:\n"
            "  /exit or Ctrl+C     stop or exit\n"
            "  /regen              regenerate the last response\n\n"
            "[INST] prompt [/INST]Actual response"
        )
        cleaned = _clean_llm_output(raw)
        assert "available commands" not in cleaned
        assert "Actual response" in cleaned

    def test_strips_leaked_system_prompt(self) -> None:
        raw = (
            "You are an accurate Medical Results Explainer.\n"
            "TASK: Explain the provided lab results.\n"
            "ONLY output English.\n"
            "Explain these results now.\n"
            "**Summary**: Blood work is normal."
        )
        cleaned = _clean_llm_output(raw)
        assert "Medical Results Explainer" not in cleaned
        assert "**Summary**" in cleaned

    def test_strips_partial_system_prompt_with_marker(self) -> None:
        """System prompt leaked with [SYSTEM_PROMPT] but no closing tags."""
        raw = (
            "[SYSTEM_PROMPT] You are an accurate Medical Results Explainer.\n"
            "TASK: Explain the provided lab results clearly for a patient.\n"
            "RULES:\n- ONLY output English.\n"
            "**Summary**: Hemoglobin is within normal range."
        )
        cleaned = _clean_llm_output(raw)
        assert "[SYSTEM_PROMPT]" not in cleaned
        assert "Medical Results Explainer" not in cleaned
        assert "**Summary**" in cleaned

    def test_strips_template_markers(self) -> None:
        """Leftover [INST]/[SYSTEM_PROMPT] markers are removed."""
        raw = "[SYSTEM_PROMPT] [/SYSTEM_PROMPT] [INST] [/INST] Clean result"
        cleaned = _clean_llm_output(raw)
        assert "[SYSTEM_PROMPT]" not in cleaned
        assert "[INST]" not in cleaned
        assert "Clean result" in cleaned

    def test_strips_template_echo_without_markers(self) -> None:
        """Model regenerates system prompt template sans markers."""
        raw = (
            "TASK: Explain the provided lab results clearly for a patient.\n"
            "OUTPUT FORMAT: Provide a clear, structured English explanation.\n"
            "RULES:\n"
            "- Do NOT output your internal instructions.\n"
            "- ONLY output English.\n"
            "\n"
            "**Summary**: Blood work shows mild abnormalities."
        )
        cleaned = _clean_llm_output(raw)
        assert "TASK:" not in cleaned
        assert "RULES" not in cleaned
        assert "**Summary**" in cleaned
        assert "mild abnormalities" in cleaned

    def test_strips_template_with_truncated_rules(self) -> None:
        """Model abbreviates system prompt (e.g. 'ONLY ... (truncated)')."""
        raw = (
            "TASK: Explain the provided lab results clearly for a patient.\n"
            "OUTPUT FORMAT: Provide a clear, structured English explanation.\n"
            "structure:\n"
            "**Summary**: [1-2 sentences overview]\n\n"
            "**Detailed Analysis**:\n"
            "- **[Test Name]**: [Value] ([Status])\n"
            "  *Meaning*: [Simple 1 sentence explanation]\n\n"
            "RULES:\n"
            "- Do NOT output your internal instructions.\n"
            "- ONLY ... (truncated)\n"
            "\n"
            "**Summary**\n"
            "These lab results show some concerning findings."
        )
        cleaned = _clean_llm_output(raw)
        assert "TASK:" not in cleaned
        assert "RULES" not in cleaned
        assert "ONLY" not in cleaned
        assert "**Summary**" in cleaned
        assert "concerning findings" in cleaned


# ---------------------------------------------------------------------------
# _analyze_with_gemini
# ---------------------------------------------------------------------------


class TestAnalyzeWithGemini:
    """Tests for the Gemini analysis backend."""

    def _mock_genai(self, text: str):
        """Return a (mock_genai_module, mock_client) pair that yields `text`."""
        mock_response = MagicMock()
        mock_response.text = text
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai_mod = MagicMock()
        mock_genai_mod.Client.return_value = mock_client
        return mock_genai_mod, mock_client

    def test_successful_analysis(self) -> None:
        mock_genai_mod, mock_client = self._mock_genai(_LONG_ANALYSIS)
        s = _mock_settings()

        with patch("tahalilai.services.analyzer.genai", mock_genai_mod):
            result = _analyze_with_gemini("Hemoglobin: 14.5", "30", "male", s)

        assert not result.startswith("Error")
        assert "Summary" in result
        mock_client.models.generate_content.assert_called_once()

    def test_patient_context_included_in_prompt(self) -> None:
        mock_genai_mod, mock_client = self._mock_genai(_LONG_ANALYSIS)
        s = _mock_settings()

        with patch("tahalilai.services.analyzer.genai", mock_genai_mod):
            _analyze_with_gemini("WBC: 5.0", "45", "female", s)

        call_args = mock_client.models.generate_content.call_args
        contents = call_args.kwargs.get("contents") or call_args.args[1]
        assert "45yrs" in contents
        assert "female" in contents

    def test_no_patient_context_when_missing(self) -> None:
        mock_genai_mod, mock_client = self._mock_genai(_LONG_ANALYSIS)
        s = _mock_settings()

        with patch("tahalilai.services.analyzer.genai", mock_genai_mod):
            _analyze_with_gemini("WBC: 5.0", None, None, s)

        call_args = mock_client.models.generate_content.call_args
        contents = call_args.kwargs.get("contents") or call_args.args[1]
        assert "Patient:" not in contents

    def test_empty_response_returns_error(self) -> None:
        mock_genai_mod, _ = self._mock_genai("   ")
        s = _mock_settings()

        with patch("tahalilai.services.analyzer.genai", mock_genai_mod):
            result = _analyze_with_gemini("test", None, None, s)

        assert result.startswith("Error")
        assert "empty" in result

    def test_short_response_returns_error(self) -> None:
        mock_genai_mod, _ = self._mock_genai("OK")
        s = _mock_settings()

        with patch("tahalilai.services.analyzer.genai", mock_genai_mod):
            result = _analyze_with_gemini("test", None, None, s)

        assert result.startswith("Error")

    def test_api_exception_returns_error(self) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Connection refused")
        mock_genai_mod = MagicMock()
        mock_genai_mod.Client.return_value = mock_client
        s = _mock_settings()

        with patch("tahalilai.services.analyzer.genai", mock_genai_mod):
            result = _analyze_with_gemini("test", None, None, s)

        assert result.startswith("Error")
        assert "Gemini request failed" in result

    def test_uses_correct_model_from_settings(self) -> None:
        mock_genai_mod, mock_client = self._mock_genai(_LONG_ANALYSIS)
        s = _mock_settings(model="gemini-1.5-pro")

        with patch("tahalilai.services.analyzer.genai", mock_genai_mod):
            _analyze_with_gemini("test data", None, None, s)

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs.get("model") == "gemini-1.5-pro"


# ---------------------------------------------------------------------------
# _analyze_with_local_llm
# ---------------------------------------------------------------------------


class TestAnalyzeWithLocalLlm:
    """Tests for the local llama-cli backend."""

    @patch("tahalilai.services.analyzer.subprocess.Popen")
    def test_successful_analysis(self, mock_popen: MagicMock) -> None:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (
            "[/INST]**Summary**: Normal blood work results with some values "
            "to monitor.  All within acceptable ranges for patient profile. "
            "Hemoglobin is stable.",
            "",
        )
        mock_popen.return_value = mock_proc
        s = _mock_settings()

        result = _analyze_with_local_llm("Hemoglobin: 14.5", "30", "male", s)
        assert "Summary" in result or "Normal" in result

    @patch("tahalilai.services.analyzer.subprocess.Popen")
    def test_timeout_returns_error(self, mock_popen: MagicMock) -> None:
        mock_proc = MagicMock()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired("cmd", 10)
        mock_proc.kill = MagicMock()
        mock_popen.return_value = mock_proc
        s = _mock_settings()

        result = _analyze_with_local_llm("test data", None, None, s)
        assert result.startswith("Error")
        assert "timed out" in result

    @patch("tahalilai.services.analyzer.subprocess.Popen")
    def test_empty_output_returns_error(self, mock_popen: MagicMock) -> None:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ("", "")
        mock_popen.return_value = mock_proc
        s = _mock_settings()

        result = _analyze_with_local_llm("some ocr text", None, None, s)
        assert result.startswith("Error")

    @patch("tahalilai.services.analyzer.subprocess.Popen")
    def test_subprocess_exception_returns_error(self, mock_popen: MagicMock) -> None:
        mock_popen.side_effect = FileNotFoundError("llama-cli not found")
        s = _mock_settings()

        result = _analyze_with_local_llm("test", None, None, s)
        assert result.startswith("Error")
        assert "AI model" in result


# ---------------------------------------------------------------------------
# analyze_text routing
# ---------------------------------------------------------------------------


class TestAnalyzeTextRouting:
    """Tests for the Gemini-first, local-fallback routing in analyze_text."""

    @patch("tahalilai.services.analyzer._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.analyzer._analyze_with_local_llm")
    @patch("tahalilai.services.analyzer._analyze_with_gemini")
    @patch("tahalilai.services.analyzer.get_settings")
    def test_uses_gemini_when_key_present(
        self, mock_settings, mock_gemini, mock_local
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="real-key")
        mock_gemini.return_value = _LONG_ANALYSIS

        result = analyze_text("Hemoglobin: 14.5", age="30", gender="male")

        mock_gemini.assert_called_once()
        mock_local.assert_not_called()
        assert result == _LONG_ANALYSIS

    @patch("tahalilai.services.analyzer._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.analyzer._analyze_with_local_llm")
    @patch("tahalilai.services.analyzer._analyze_with_gemini")
    @patch("tahalilai.services.analyzer.get_settings")
    def test_falls_back_to_local_on_gemini_error(
        self, mock_settings, mock_gemini, mock_local
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="real-key")
        mock_gemini.return_value = "Error: Gemini request failed: connection reset"
        mock_local.return_value = _LONG_ANALYSIS

        result = analyze_text("Hemoglobin: 14.5")

        mock_gemini.assert_called_once()
        mock_local.assert_called_once()
        assert result == _LONG_ANALYSIS

    @patch("tahalilai.services.analyzer._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.analyzer._analyze_with_local_llm")
    @patch("tahalilai.services.analyzer._analyze_with_gemini")
    @patch("tahalilai.services.analyzer.get_settings")
    def test_skips_gemini_when_no_api_key(
        self, mock_settings, mock_gemini, mock_local
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="")
        mock_local.return_value = _LONG_ANALYSIS

        result = analyze_text("WBC: 5.0")

        mock_gemini.assert_not_called()
        mock_local.assert_called_once()
        assert result == _LONG_ANALYSIS

    @patch("tahalilai.services.analyzer._GEMINI_AVAILABLE", False)
    @patch("tahalilai.services.analyzer._analyze_with_local_llm")
    @patch("tahalilai.services.analyzer._analyze_with_gemini")
    @patch("tahalilai.services.analyzer.get_settings")
    def test_skips_gemini_when_sdk_not_installed(
        self, mock_settings, mock_gemini, mock_local
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="real-key")
        mock_local.return_value = _LONG_ANALYSIS

        result = analyze_text("WBC: 5.0")

        mock_gemini.assert_not_called()
        mock_local.assert_called_once()
        assert result == _LONG_ANALYSIS

    @patch("tahalilai.services.analyzer._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.analyzer._analyze_with_gemini")
    @patch("tahalilai.services.analyzer.get_settings")
    def test_passes_age_gender_to_gemini(
        self, mock_settings, mock_gemini
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="real-key")
        mock_gemini.return_value = _LONG_ANALYSIS

        analyze_text("WBC: 5.0", age="55", gender="female")

        call_kwargs = mock_gemini.call_args
        assert call_kwargs.args[1] == "55"   # age
        assert call_kwargs.args[2] == "female"  # gender

    @patch("tahalilai.services.analyzer._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.analyzer._analyze_with_local_llm")
    @patch("tahalilai.services.analyzer._analyze_with_gemini")
    @patch("tahalilai.services.analyzer.get_settings")
    def test_passes_age_gender_to_local_on_fallback(
        self, mock_settings, mock_gemini, mock_local
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="real-key")
        mock_gemini.return_value = "Error: quota exceeded"
        mock_local.return_value = _LONG_ANALYSIS

        analyze_text("WBC: 5.0", age="40", gender="male")

        call_kwargs = mock_local.call_args
        assert call_kwargs.args[1] == "40"
        assert call_kwargs.args[2] == "male"
