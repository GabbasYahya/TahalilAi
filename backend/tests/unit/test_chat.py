"""Unit tests for the follow-up chat service."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from tahalilai.services.chat import (
    _build_context_prompt,
    _chat_with_gemini,
    _chat_with_local_llm,
    answer_question,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LONG_ANSWER = (
    "Your hemoglobin level of 14.5 g/dL is within the normal range for adults. "
    "This means your red blood cells are carrying oxygen effectively throughout "
    "your body. There is no cause for concern based on this value alone."
)

_OCR = "Hemoglobin: 14.5 g/dL\nWBC: 5.2 x10^3/uL\nPlatelets: 220 x10^3/uL"
_ANALYSIS = "**Summary**: Blood work is normal.\n\n**Detailed Analysis**:\n- Hemoglobin: 14.5 (Normal)"
_HISTORY: list[dict[str, str]] = []


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
# _build_context_prompt
# ---------------------------------------------------------------------------


class TestBuildContextPrompt:
    def test_contains_ocr_text(self) -> None:
        prompt = _build_context_prompt(_OCR, _ANALYSIS, [], "What is my hemoglobin?")
        assert "Hemoglobin: 14.5" in prompt

    def test_contains_initial_analysis(self) -> None:
        prompt = _build_context_prompt(_OCR, _ANALYSIS, [], "Should I worry?")
        assert "Blood work is normal" in prompt

    def test_contains_question(self) -> None:
        prompt = _build_context_prompt(_OCR, _ANALYSIS, [], "Is my WBC normal?")
        assert "Is my WBC normal?" in prompt

    def test_includes_history(self) -> None:
        history = [
            {"role": "user", "content": "What is hemoglobin?"},
            {"role": "assistant", "content": "It carries oxygen in your blood."},
        ]
        prompt = _build_context_prompt(_OCR, _ANALYSIS, history, "And WBC?")
        assert "What is hemoglobin?" in prompt
        assert "It carries oxygen" in prompt

    def test_history_labels(self) -> None:
        history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
        prompt = _build_context_prompt(_OCR, _ANALYSIS, history, "Any concerns?")
        assert "Patient: Hello" in prompt
        assert "Assistant: Hi" in prompt

    def test_new_question_appears_in_conversation(self) -> None:
        prompt = _build_context_prompt(_OCR, _ANALYSIS, [], "My final question")
        assert "Patient: My final question" in prompt


# ---------------------------------------------------------------------------
# _chat_with_gemini
# ---------------------------------------------------------------------------


class TestChatWithGemini:
    def _mock_genai(self, text: str):
        mock_response = MagicMock()
        mock_response.text = text
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai_mod = MagicMock()
        mock_genai_mod.Client.return_value = mock_client
        return mock_genai_mod, mock_client

    def test_successful_response(self) -> None:
        mock_genai_mod, mock_client = self._mock_genai(_LONG_ANSWER)
        s = _mock_settings()

        with patch("tahalilai.services.chat.genai", mock_genai_mod):
            result = _chat_with_gemini(_OCR, _ANALYSIS, _HISTORY, "What is hemoglobin?", s)

        assert not result.startswith("Error")
        assert "hemoglobin" in result.lower()
        mock_client.models.generate_content.assert_called_once()

    def test_context_sent_to_api(self) -> None:
        mock_genai_mod, mock_client = self._mock_genai(_LONG_ANSWER)
        s = _mock_settings()

        with patch("tahalilai.services.chat.genai", mock_genai_mod):
            _chat_with_gemini(_OCR, _ANALYSIS, _HISTORY, "What is WBC?", s)

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        contents = call_kwargs.get("contents", "")
        assert "Hemoglobin: 14.5" in contents
        assert "Blood work is normal" in contents
        assert "What is WBC?" in contents

    def test_empty_response_returns_error(self) -> None:
        mock_genai_mod, _ = self._mock_genai("  ")
        s = _mock_settings()

        with patch("tahalilai.services.chat.genai", mock_genai_mod):
            result = _chat_with_gemini(_OCR, _ANALYSIS, _HISTORY, "?", s)

        assert result.startswith("Error")

    def test_api_exception_returns_error(self) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Network error")
        mock_genai_mod = MagicMock()
        mock_genai_mod.Client.return_value = mock_client
        s = _mock_settings()

        with patch("tahalilai.services.chat.genai", mock_genai_mod):
            result = _chat_with_gemini(_OCR, _ANALYSIS, _HISTORY, "?", s)

        assert result.startswith("Error")
        assert "Gemini chat failed" in result

    def test_uses_correct_model(self) -> None:
        mock_genai_mod, mock_client = self._mock_genai(_LONG_ANSWER)
        s = _mock_settings(model="gemini-1.5-pro")

        with patch("tahalilai.services.chat.genai", mock_genai_mod):
            _chat_with_gemini(_OCR, _ANALYSIS, _HISTORY, "test", s)

        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs.get("model") == "gemini-1.5-pro"


# ---------------------------------------------------------------------------
# _chat_with_local_llm
# ---------------------------------------------------------------------------


class TestChatWithLocalLlm:
    @patch("tahalilai.services.chat.subprocess.Popen")
    def test_successful_response(self, mock_popen: MagicMock) -> None:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (
            "[/INST]Your hemoglobin level is within the normal range.", ""
        )
        mock_popen.return_value = mock_proc
        s = _mock_settings()

        result = _chat_with_local_llm(_OCR, _ANALYSIS, _HISTORY, "What is hemoglobin?", s)
        assert not result.startswith("Error")
        assert "hemoglobin" in result.lower()

    @patch("tahalilai.services.chat.subprocess.Popen")
    def test_timeout_returns_error(self, mock_popen: MagicMock) -> None:
        mock_proc = MagicMock()
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired("cmd", 10)
        mock_proc.kill = MagicMock()
        mock_popen.return_value = mock_proc
        s = _mock_settings()

        result = _chat_with_local_llm(_OCR, _ANALYSIS, _HISTORY, "test?", s)
        assert result.startswith("Error")
        assert "timed out" in result

    @patch("tahalilai.services.chat.subprocess.Popen")
    def test_empty_output_returns_error(self, mock_popen: MagicMock) -> None:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ("", "")
        mock_popen.return_value = mock_proc
        s = _mock_settings()

        result = _chat_with_local_llm(_OCR, _ANALYSIS, _HISTORY, "test?", s)
        assert result.startswith("Error")

    @patch("tahalilai.services.chat.subprocess.Popen")
    def test_strips_inst_echo(self, mock_popen: MagicMock) -> None:
        """Response after [/INST] marker is extracted correctly."""
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = (
            "[INST] some prompt [/INST]Your WBC is normal.", ""
        )
        mock_popen.return_value = mock_proc
        s = _mock_settings()

        result = _chat_with_local_llm(_OCR, _ANALYSIS, _HISTORY, "WBC?", s)
        assert result == "Your WBC is normal."

    @patch("tahalilai.services.chat.subprocess.Popen")
    def test_subprocess_exception_returns_error(self, mock_popen: MagicMock) -> None:
        mock_popen.side_effect = FileNotFoundError("llama-cli not found")
        s = _mock_settings()

        result = _chat_with_local_llm(_OCR, _ANALYSIS, _HISTORY, "test?", s)
        assert result.startswith("Error")
        assert "Local model failed" in result


# ---------------------------------------------------------------------------
# answer_question routing
# ---------------------------------------------------------------------------


class TestAnswerQuestionRouting:
    @patch("tahalilai.services.chat._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.chat._chat_with_local_llm")
    @patch("tahalilai.services.chat._chat_with_gemini")
    @patch("tahalilai.services.chat.get_settings")
    def test_uses_gemini_when_key_present(
        self, mock_settings, mock_gemini, mock_local
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="real-key")
        mock_gemini.return_value = _LONG_ANSWER

        result = answer_question(_OCR, _ANALYSIS, _HISTORY, "What is hemoglobin?")

        mock_gemini.assert_called_once()
        mock_local.assert_not_called()
        assert result == _LONG_ANSWER

    @patch("tahalilai.services.chat._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.chat._chat_with_local_llm")
    @patch("tahalilai.services.chat._chat_with_gemini")
    @patch("tahalilai.services.chat.get_settings")
    def test_falls_back_to_local_on_gemini_error(
        self, mock_settings, mock_gemini, mock_local
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="real-key")
        mock_gemini.return_value = "Error: Gemini chat failed: connection reset"
        mock_local.return_value = _LONG_ANSWER

        result = answer_question(_OCR, _ANALYSIS, _HISTORY, "Any concerns?")

        mock_gemini.assert_called_once()
        mock_local.assert_called_once()
        assert result == _LONG_ANSWER

    @patch("tahalilai.services.chat._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.chat._chat_with_local_llm")
    @patch("tahalilai.services.chat._chat_with_gemini")
    @patch("tahalilai.services.chat.get_settings")
    def test_skips_gemini_when_no_api_key(
        self, mock_settings, mock_gemini, mock_local
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="")
        mock_local.return_value = _LONG_ANSWER

        answer_question(_OCR, _ANALYSIS, _HISTORY, "test?")

        mock_gemini.assert_not_called()
        mock_local.assert_called_once()

    @patch("tahalilai.services.chat._GEMINI_AVAILABLE", False)
    @patch("tahalilai.services.chat._chat_with_local_llm")
    @patch("tahalilai.services.chat._chat_with_gemini")
    @patch("tahalilai.services.chat.get_settings")
    def test_skips_gemini_when_sdk_missing(
        self, mock_settings, mock_gemini, mock_local
    ) -> None:
        mock_settings.return_value = _mock_settings(api_key="real-key")
        mock_local.return_value = _LONG_ANSWER

        answer_question(_OCR, _ANALYSIS, _HISTORY, "test?")

        mock_gemini.assert_not_called()
        mock_local.assert_called_once()

    @patch("tahalilai.services.chat._GEMINI_AVAILABLE", True)
    @patch("tahalilai.services.chat._chat_with_gemini")
    @patch("tahalilai.services.chat.get_settings")
    def test_history_trimmed_to_max(self, mock_settings, mock_gemini) -> None:
        """History longer than _MAX_HISTORY is trimmed before passing to backends."""
        mock_settings.return_value = _mock_settings(api_key="real-key")
        mock_gemini.return_value = _LONG_ANSWER

        long_history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
            for i in range(30)  # 30 messages > _MAX_HISTORY (20)
        ]

        answer_question(_OCR, _ANALYSIS, long_history, "final question")

        passed_history = mock_gemini.call_args.args[2]
        assert len(passed_history) <= 20
