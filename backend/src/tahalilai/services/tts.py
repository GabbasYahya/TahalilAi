"""Text-to-speech service.

Supports two back-ends:

* **Qwen3-TTS** — high-quality neural TTS (optional, requires GPU or patience).
* **gTTS** — lightweight Google TTS fallback (always available).

Qwen3-TTS is lazy-loaded on the first call so the server starts instantly.
"""

from __future__ import annotations

import re
import traceback
from pathlib import Path

from gtts import gTTS

from tahalilai.config import get_settings

# Optional heavy imports for Qwen TTS
_QWEN_AVAILABLE = False
try:
    import soundfile as sf  # noqa: F401  (checked at import-time)
    import torch
    from qwen_tts import Qwen3TTSModel  # type: ignore[import-untyped]

    _QWEN_AVAILABLE = True
except ImportError:
    pass

_qwen_model: object | None = None  # lazy singleton


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_audio(text: str, output_path: str | Path, lang: str = "en") -> bool:
    """Generate an audio file from *text*.

    Tries Qwen3-TTS first (if available), then falls back to gTTS.

    Args:
        text: Plain or markdown text to speak.
        output_path: Destination file path (typically ``.mp3``).
        lang: BCP-47 language code (``en``, ``fr``, ``ar``, etc.).

    Returns:
        ``True`` on success, ``False`` if all engines failed.
    """
    clean = _strip_markdown(text)
    out = Path(output_path)

    if _QWEN_AVAILABLE:
        model = _get_qwen_model()
        if model is not None and _try_qwen(model, clean, out, lang):
            return True

    return _fallback_gtts(clean, out, lang)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_markdown(text: str) -> str:
    """Remove markdown artefacts that shouldn't be spoken aloud."""
    text = text.replace("*", "").replace("#", "")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def _get_qwen_model() -> object | None:
    """Lazily initialise the Qwen3-TTS model (singleton)."""
    global _qwen_model
    if not _QWEN_AVAILABLE:
        return None
    if _qwen_model is not None:
        return _qwen_model
    try:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        print(f"Loading Qwen3-TTS on {device} ({dtype})...")
        _qwen_model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            device_map=device,
            dtype=dtype,
        )
        print("Qwen3-TTS loaded successfully.")
        return _qwen_model
    except Exception as exc:
        print(f"Failed to load Qwen3-TTS: {exc}")
        traceback.print_exc()
        return None


_LANG_MAP: dict[str, str] = {
    "en": "English",
    "fr": "French",
    "ar": "Arabic",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
}


def _try_qwen(model: object, text: str, output_path: Path, lang: str) -> bool:
    """Attempt TTS with the Qwen3-TTS model."""
    try:
        import numpy as np
        import soundfile as sf

        qwen_lang = _LANG_MAP.get(lang.lower(), "English")
        settings = get_settings()
        ref_audio = settings.assets_dir / "ref_audio.wav"

        if not ref_audio.exists():
            ref_audio.parent.mkdir(parents=True, exist_ok=True)
            silence = np.zeros(16_000 * 3)
            sf.write(str(ref_audio), silence, 16_000)

        print(f"Generating audio with Qwen3-TTS ({qwen_lang})...")
        wavs, sr = model.generate_voice_clone(  # type: ignore[union-attr]
            text=text,
            language=qwen_lang,
            ref_audio=str(ref_audio),
            ref_text="Reference audio for voice style.",
        )
        sf.write(str(output_path), wavs[0], sr)
        print(f"Qwen TTS → {output_path}")
        return True
    except Exception as exc:
        print(f"Qwen3-TTS failed: {exc}")
        return False


def _fallback_gtts(text: str, output_path: Path, lang: str) -> bool:
    """Fallback TTS via Google gTTS."""
    print("Using gTTS fallback...")
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(output_path))
        print(f"gTTS → {output_path}")
        return True
    except Exception as exc:
        print(f"gTTS failed: {exc}")
        return False
