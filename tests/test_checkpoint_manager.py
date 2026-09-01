"""Tests for durable checkpoint storage."""

import json

from src.checkpoint_manager import CheckpointManager
from src.run_manifest import RunManifest


def test_checkpoint_load_falls_back_from_corrupt_latest(tmp_path):
    manager = CheckpointManager(str(tmp_path), max_checkpoints_per_phase=10)
    older = manager.save_checkpoint("phase", {"value": 1}, timestamp="20260101_000000_000000")
    latest = manager.save_checkpoint("phase", {"value": 2}, timestamp="20260101_000001_000000")

    with open(latest, "w", encoding="utf-8") as handle:
        handle.write("{broken")

    assert manager.load_checkpoint("phase") == {"value": 1}
    assert older != latest


def test_compressed_checkpoint_round_trip_and_retention(tmp_path):
    manager = CheckpointManager(
        str(tmp_path), compression=True, max_checkpoints_per_phase=2
    )
    manager.save_checkpoint("phase", {"value": 1}, timestamp="20260101_000000_000000")
    manager.save_checkpoint("phase", {"value": 2}, timestamp="20260101_000001_000000")
    manager.save_checkpoint("phase", {"value": 3}, timestamp="20260101_000002_000000")

    assert manager.load_checkpoint("phase") == {"value": 3}
    assert len(manager.list_checkpoints("phase")) == 2
    assert all(path.endswith(".json.gz") for path in manager.list_checkpoints("phase"))


def test_phase_status_is_persisted(tmp_path):
    manager = CheckpointManager(str(tmp_path))
    manager.mark_phase("phase1", "failed", error="invalid output")

    reloaded = CheckpointManager(str(tmp_path))
    assert reloaded.get_phase_status("phase1")["status"] == "failed"
    assert reloaded.get_phase_status("phase1")["error"] == "invalid output"


def test_interrupted_manifest_is_reconciled_as_failed(tmp_path):
    path = tmp_path / "run_manifest.json"
    manifest = RunManifest(
        path,
        {
            "schema_version": 1,
            "run_id": "interrupted",
            "run_seed": 1,
            "status": "initialized",
            "phases": {},
        },
    )
    manifest.set_status("running")
    manifest.set_phase_status("phase1", "running")
    manifest.data.pop("pid", None)
    manifest.update()

    reloaded = RunManifest(path, {})
    assert reloaded.reconcile_interrupted() is True
    assert reloaded.data["status"] == "failed"
    assert reloaded.data["phases"]["phase1"]["status"] == "failed"
