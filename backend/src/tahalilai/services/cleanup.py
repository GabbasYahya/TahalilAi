"""Periodic upload-directory cleanup service.

Automatically removes files from ``backend/uploads/`` that are older than a
configurable age limit, preventing unbounded disk growth and reducing the
risk of retaining sensitive patient data beyond its useful lifetime.

How it works
------------
* :func:`delete_old_uploads` is a plain synchronous function that scans the
  directory, compares each file's last-modification time against the cutoff,
  and deletes stale files.  It is intentionally synchronous so it can also be
  called from tests or maintenance scripts without an asyncio event loop.

* :func:`run_cleanup_loop` is an ``async`` task that calls
  :func:`delete_old_uploads` on a fixed interval (default: every hour).
  It is launched via ``asyncio.create_task`` inside the FastAPI lifespan, so
  it runs indefinitely in the background alongside the server and is
  automatically cancelled when the server shuts down.

Files that are never deleted
----------------------------
* ``.gitkeep`` — the VCS placeholder that keeps the directory tracked.
* Any sub-directories that may be created in the future.

Error handling
--------------
Neither function ever propagates an exception to the caller.  Individual
file-deletion errors (e.g. a file locked by another process) are logged and
skipped; the rest of the sweep continues normally.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

# Files that must never be deleted by the cleanup sweep.
_PROTECTED = frozenset({".gitkeep"})


# ---------------------------------------------------------------------------
# Core logic  (synchronous — safe to call from tests / scripts)
# ---------------------------------------------------------------------------


def delete_old_uploads(uploads_dir: Path, max_age_hours: float) -> int:
    """Delete files in *uploads_dir* that are older than *max_age_hours*.

    Args:
        uploads_dir: The directory to sweep (typically ``backend/uploads/``).
        max_age_hours: Files whose ``mtime`` is older than this many hours
            are deleted.  Use ``0`` to delete everything (useful in tests).

    Returns:
        The number of files successfully deleted in this sweep.
    """
    cutoff = time.time() - max_age_hours * 3600
    deleted = 0

    if not uploads_dir.exists():
        return 0

    for path in uploads_dir.iterdir():
        # Skip protected names and sub-directories
        if path.name in _PROTECTED or not path.is_file():
            continue

        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                deleted += 1
                print(f"[cleanup] Deleted expired file: {path.name}")
        except OSError as exc:
            # File may have been deleted concurrently or be locked — skip it.
            print(f"[cleanup] Could not delete {path.name}: {exc}")

    return deleted


# ---------------------------------------------------------------------------
# Async background loop  (started by the FastAPI lifespan)
# ---------------------------------------------------------------------------


async def run_cleanup_loop(
    uploads_dir: Path,
    max_age_hours: float,
    interval_seconds: int = 3600,
) -> None:
    """Asyncio background task: sweep uploads on a fixed interval.

    Runs forever until the enclosing task is cancelled (e.g. on server
    shutdown via the FastAPI lifespan context manager).

    Args:
        uploads_dir: Directory to sweep on each tick.
        max_age_hours: Maximum file age in hours before deletion.
        interval_seconds: Seconds to sleep between sweeps. Default: 3600 (1 h).
    """
    print(
        f"[cleanup] Background task started — "
        f"max_age={max_age_hours}h, interval={interval_seconds}s."
    )

    while True:
        # Wait first so the very first sweep happens after *interval_seconds*,
        # not immediately at startup (files just uploaded should not vanish).
        await asyncio.sleep(interval_seconds)

        try:
            n = delete_old_uploads(uploads_dir, max_age_hours)
            if n:
                print(f"[cleanup] Swept uploads/: {n} expired file(s) removed.")
            else:
                print("[cleanup] Swept uploads/: nothing to delete.")
        except Exception as exc:  # pragma: no cover — safety net
            print(f"[cleanup] Unexpected error during sweep: {exc}")
