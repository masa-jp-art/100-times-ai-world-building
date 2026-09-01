"""Filesystem layout for generated world outputs."""

from pathlib import Path
from typing import Tuple


def world_package_name(run_id: str) -> str:
    """Return the directory name for one generated world package."""
    return f"world_{run_id}"


def resolve_world_package(root: Path, run_id: str) -> Tuple[Path, bool]:
    """Resolve a run ID to its package directory.

    New executions use ``world_<run_id>``. Existing ``run_<run_id>``
    directories are still accepted so older local runs can be resumed without
    first being moved or renamed.

    Returns:
        ``(path, is_legacy_layout)``
    """
    root = Path(root)
    current = root / world_package_name(run_id)
    legacy = root / f"run_{run_id}"
    if current.exists():
        return current, False
    if legacy.exists():
        return legacy, True
    return current, False
