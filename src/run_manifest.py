"""Persistent metadata for one local pipeline run."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from loguru import logger


def utc_now() -> str:
    """Return an ISO-8601 timestamp with an explicit UTC offset."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def file_sha256(path: Path) -> Optional[str]:
    """Return a file digest, or ``None`` when the file is unavailable."""
    if not path.is_file():
        return None

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_files(paths: Iterable[Path], root: Path) -> Dict[str, Optional[str]]:
    """Create a stable relative-path to SHA-256 mapping for input files."""
    result: Dict[str, Optional[str]] = {}
    for path in sorted(paths):
        try:
            relative = str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            relative = str(path.resolve())
        result[relative] = file_sha256(path)
    return result


def _atomic_json_write(path: Path, data: Dict[str, Any]) -> None:
    """Write JSON without exposing a partially written manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        try:
            directory_fd = os.open(path.parent, os.O_DIRECTORY)
        except (AttributeError, OSError):
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


class RunManifest:
    """Create and update the metadata file for a single pipeline run."""

    def __init__(self, path: Path, initial_data: Dict[str, Any]):
        self.path = Path(path)
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"Invalid run manifest: {self.path}") from exc
            if not isinstance(loaded, dict):
                raise ValueError(f"Run manifest must contain an object: {self.path}")
            self.data: Dict[str, Any] = loaded
            logger.info(f"Loaded run manifest: {self.path}")
        else:
            self.data = dict(initial_data)
            self.data.setdefault("created_at", utc_now())
            self.data.setdefault("updated_at", self.data["created_at"])
            self._save()
            logger.info(f"Created run manifest: {self.path}")

    @property
    def run_seed(self) -> Optional[int]:
        value = self.data.get("run_seed")
        return int(value) if value is not None else None

    def update(self, **values: Any) -> None:
        """Update fields and persist the manifest atomically."""
        self.data.update(values)
        self.data["updated_at"] = utc_now()
        self._save()

    def set_status(self, status: str, error: Optional[str] = None) -> None:
        """Set the top-level lifecycle state of a run."""
        values: Dict[str, Any] = {"status": status}
        if status == "running" and not self.data.get("started_at"):
            values["started_at"] = utc_now()
        if status == "running":
            values["pid"] = os.getpid()
        if status in {"completed", "failed", "cancelled"}:
            values["finished_at"] = utc_now()
        if error:
            values["error"] = error
        elif status != "failed":
            self.data.pop("error", None)
        self.update(**values)

    def set_phase_status(
        self,
        phase_name: str,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        """Record a phase lifecycle state without changing phase data."""
        phases = self.data.setdefault("phases", {})
        phase = dict(phases.get(phase_name, {}))
        phase["status"] = status
        if status == "running" and not phase.get("started_at"):
            phase["started_at"] = utc_now()
        if status in {"completed", "failed", "cancelled"}:
            phase["finished_at"] = utc_now()
        if error:
            phase["error"] = error
        elif status != "failed":
            phase.pop("error", None)
        phases[phase_name] = phase
        self.update(phases=phases)

    def reconcile_interrupted(self) -> bool:
        """Reconcile a run left in ``running`` state by a dead process.

        Returns ``True`` when a stale run was marked failed. A live process
        belonging to another PID raises so a resume cannot overwrite it.
        """
        if self.data.get("status") != "running":
            return False

        pid = self.data.get("pid")
        if pid is not None:
            try:
                pid = int(pid)
            except (TypeError, ValueError):
                pid = None
        if pid and pid != os.getpid() and self._process_is_alive(pid):
            raise RuntimeError(
                f"Run manifest is already active in another process (pid={pid}): {self.path}"
            )
        if pid == os.getpid():
            return False

        message = "Previous process ended while the run was active; resume is required"
        self.set_status("failed", error=message)
        phases = self.data.get("phases", {})
        for phase_name, phase in phases.items():
            if isinstance(phase, dict) and phase.get("status") == "running":
                phase["status"] = "failed"
                phase["error"] = message
                phase["finished_at"] = utc_now()
        self.update(phases=phases)
        logger.warning(f"Reconciled interrupted run manifest: {self.path}")
        return True

    @staticmethod
    def _process_is_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _save(self) -> None:
        _atomic_json_write(self.path, self.data)
