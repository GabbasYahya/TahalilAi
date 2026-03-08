"""Text-to-speech service using gTTS.

Converts text to MP3 audio via Google TTS (gTTS).  Qwen3-TTS (local neural TTS)
is omitted because it requires a CUDA GPU; add it back when one is available.
"""

from __future__ import annotations

import re
from pathlib import Path

from gtts import gTTS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_audio(text: str, output_path: str | Path, lang: str = "en") -> bool:
    """Generate an MP3 audio file from *text* using gTTS.

    Args:
        text: Plain or markdown text to speak.
        output_path: Destination ``.mp3`` file path.
        lang: BCP-47 language code (``en``, ``fr``, ``ar``, etc.).

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    clean = _strip_markdown(text)
    return _gtts(clean, Path(output_path), lang)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_markdown(text: str) -> str:
    """Remove markdown artefacts that shouldn't be spoken aloud."""
    text = text.replace("*", "").replace("#", "")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def _gtts(text: str, output_path: Path, lang: str) -> bool:
    """Generate audio via Google TTS.

    gTTS handles long text internally by splitting at sentence boundaries and
    making multiple API requests, then writing all audio sequentially to one
    stream. This produces a valid single MP3 that browsers can play in full.

    We write to a temp file first and rename atomically so that the polling
    endpoint never serves a partially-written file.
    """
    tmp_path = output_path.with_suffix(".tmp")
    try:
        print(f"gTTS: generating audio for {len(text)} chars")
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(tmp_path))
        tmp_path.rename(output_path)
        print(f"gTTS → {output_path}")
        return True
    except Exception as exc:
        print(f"gTTS failed: {exc}")
        tmp_path.unlink(missing_ok=True)
        return False
