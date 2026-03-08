"""Unit tests for the upload cleanup service."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tahalilai.services.cleanup import (
    _PROTECTED,
    delete_old_uploads,
    run_cleanup_loop,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_file(directory: Path, name: str, age_hours: float) -> Path:
    """Create a file and back-date its mtime by *age_hours*."""
    path = directory / name
    path.write_bytes(b"data")
    past = time.time() - age_hours * 3600
    import os
    os.utime(path, (past, past))
    return path


# ---------------------------------------------------------------------------
# delete_old_uploads
# ---------------------------------------------------------------------------


class TestDeleteOldUploads:
    """Tests for the synchronous sweep function."""

    def test_returns_zero_on_missing_directory(self, tmp_path: Path) -> None:
        """Non-existent directory should return 0 without raising."""
        assert delete_old_uploads(tmp_path / "nonexistent", max_age_hours=24) == 0

    def test_deletes_old_file(self, tmp_path: Path) -> None:
        """Files older than max_age_hours must be deleted."""
        _make_file(tmp_path, "old.png", age_hours=25)
        n = delete_old_uploads(tmp_path, max_age_hours=24)
        assert n == 1
        assert not (tmp_path / "old.png").exists()

    def test_keeps_recent_file(self, tmp_path: Path) -> None:
        """Files younger than max_age_hours must be preserved."""
        _make_file(tmp_path, "new.png", age_hours=1)
        n = delete_old_uploads(tmp_path, max_age_hours=24)
        assert n == 0
        assert (tmp_path / "new.png").exists()

    def test_deletes_only_stale_files(self, tmp_path: Path) -> None:
        """Mixed directory: only the old file is removed."""
        _make_file(tmp_path, "old.pdf", age_hours=48)
        _make_file(tmp_path, "new.pdf", age_hours=2)
        n = delete_old_uploads(tmp_path, max_age_hours=24)
        assert n == 1
        assert not (tmp_path / "old.pdf").exists()
        assert (tmp_path / "new.pdf").exists()

    def test_skips_gitkeep(self, tmp_path: Path) -> None:
        """.gitkeep must never be deleted regardless of age."""
        _make_file(tmp_path, ".gitkeep", age_hours=9999)
        n = delete_old_uploads(tmp_path, max_age_hours=0)
        assert n == 0
        assert (tmp_path / ".gitkeep").exists()

    def test_skips_all_protected_names(self, tmp_path: Path) -> None:
        """All names in _PROTECTED are skipped."""
        for name in _PROTECTED:
            _make_file(tmp_path, name, age_hours=9999)
        n = delete_old_uploads(tmp_path, max_age_hours=0)
        assert n == 0

    def test_skips_subdirectories(self, tmp_path: Path) -> None:
        """Sub-directories are never removed."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        n = delete_old_uploads(tmp_path, max_age_hours=0)
        assert n == 0
        assert subdir.exists()

    def test_tolerates_oserror_on_single_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """An OSError on one file should be logged and skipped; others processed."""
        _make_file(tmp_path, "locked.png", age_hours=48)
        _make_file(tmp_path, "unlocked.png", age_hours=48)

        original_unlink = Path.unlink

        def _flaky_unlink(self, missing_ok: bool = False) -> None:
            if self.name == "locked.png":
                raise OSError("File locked")
            original_unlink(self, missing_ok=missing_ok)

        monkeypatch.setattr(Path, "unlink", _flaky_unlink)
        n = delete_old_uploads(tmp_path, max_age_hours=24)
        # Only the unlocked file should be counted as deleted
        assert n == 1
        assert (tmp_path / "locked.png").exists()

    def test_multiple_file_types(self, tmp_path: Path) -> None:
        """PNG, PDF, and MP3 files are all eligible for deletion."""
        for name in ("report.pdf", "image.png", "audio.mp3"):
            _make_file(tmp_path, name, age_hours=48)
        n = delete_old_uploads(tmp_path, max_age_hours=24)
        assert n == 3

    def test_zero_max_age_deletes_everything(self, tmp_path: Path) -> None:
        """max_age_hours=0 should delete all files (except protected).

        Files are back-dated by 0.1 h (6 min) so their mtime is
        definitively earlier than the cutoff = time.time() - 0.
        """
        for name in ("a.png", "b.pdf"):
            _make_file(tmp_path, name, age_hours=0.1)
        n = delete_old_uploads(tmp_path, max_age_hours=0)
        assert n == 2

    def test_returns_correct_count(self, tmp_path: Path) -> None:
        """Return value must equal the number of files deleted."""
        for i in range(5):
            _make_file(tmp_path, f"file{i}.png", age_hours=48)
        n = delete_old_uploads(tmp_path, max_age_hours=24)
        assert n == 5


# ---------------------------------------------------------------------------
# run_cleanup_loop
# ---------------------------------------------------------------------------


class TestRunCleanupLoop:
    """Tests for the async background loop."""

    @pytest.mark.asyncio
    async def test_loop_calls_delete_after_interval(self, tmp_path: Path) -> None:
        """The loop must invoke delete_old_uploads after sleeping interval_seconds."""
        call_count = 0

        async def _fake_sleep(_seconds: float) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError

        with patch("tahalilai.services.cleanup.asyncio.sleep", side_effect=_fake_sleep), \
             patch("tahalilai.services.cleanup.delete_old_uploads", return_value=0) as mock_delete:
            with pytest.raises(asyncio.CancelledError):
                await run_cleanup_loop(tmp_path, max_age_hours=24, interval_seconds=3600)

        # delete_old_uploads should have been called at least once
        assert mock_delete.call_count >= 1
        mock_delete.assert_called_with(tmp_path, 24)

    @pytest.mark.asyncio
    async def test_loop_logs_deleted_count(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Loop should print a summary when files are deleted."""
        call_count = 0

        async def _fake_sleep(_seconds: float) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError

        with patch("tahalilai.services.cleanup.asyncio.sleep", side_effect=_fake_sleep), \
             patch("tahalilai.services.cleanup.delete_old_uploads", return_value=3):
            with pytest.raises(asyncio.CancelledError):
                await run_cleanup_loop(tmp_path, max_age_hours=24, interval_seconds=3600)

        captured = capsys.readouterr()
        assert "3" in captured.out

    @pytest.mark.asyncio
    async def test_loop_survives_delete_exception(self, tmp_path: Path) -> None:
        """An exception inside delete_old_uploads must not kill the loop."""
        call_count = 0

        async def _fake_sleep(_seconds: float) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                raise asyncio.CancelledError

        with patch("tahalilai.services.cleanup.asyncio.sleep", side_effect=_fake_sleep), \
             patch("tahalilai.services.cleanup.delete_old_uploads", side_effect=RuntimeError("boom")):
            with pytest.raises(asyncio.CancelledError):
                await run_cleanup_loop(tmp_path, max_age_hours=24, interval_seconds=3600)

        # If we reach here, the loop survived the exception on the first tick
        assert call_count >= 2
