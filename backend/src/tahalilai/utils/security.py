"""File validation and filename sanitisation utilities.

Enforces an allow-list of file types (PDF, JPEG, PNG) by inspecting
magic bytes, with a fallback to raw header checks when ``python-magic``
is unavailable.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
    }
)


def validate_file(file_path: str | Path) -> bool:
    """Validate an uploaded file by checking its magic bytes.

    Args:
        file_path: Path to the file to validate.

    Returns:
        ``True`` if the file is a valid PDF, JPEG, or PNG.

    Raises:
        ValueError: If the file type is not in the allow-list.
    """
    file_path = Path(file_path)

    try:
        import magic

        mime_checker = magic.Magic(mime=True)
        detected = mime_checker.from_file(str(file_path))

        if detected in _ALLOWED_MIME_TYPES:
            return True

        # python-magic sometimes returns generic type for valid files
        if detected == "application/octet-stream":
            return _check_header(file_path)

        raise ValueError(
            f"Security: Invalid file type ({detected}). Only PDF, JPG, and PNG are allowed."
        )
    except ImportError:
        return _check_header(file_path)
    except ValueError:
        raise
    except Exception:
        return _check_header(file_path)


def _check_header(file_path: Path) -> bool:
    """Validate the file by inspecting its raw header bytes.

    Raises:
        ValueError: If the header does not match any allowed type.
    """
    with open(file_path, "rb") as fh:
        header = fh.read(4)

    if header.startswith(b"%PDF"):
        return True
    if header.startswith(b"\xff\xd8\xff"):
        return True
    if header.startswith(b"\x89PNG"):
        return True

    raise ValueError("Security: File header mismatch. Invalid format.")


def sanitize_filename(filename: str) -> str:
    """Return a filesystem-safe version of *filename*.

    Strips path components and restricts characters to alphanumeric,
    dot, dash, and underscore.
    """
    filename = os.path.basename(filename)
    return re.sub(r"[^a-zA-Z0-9_.\-]", "_", filename)
