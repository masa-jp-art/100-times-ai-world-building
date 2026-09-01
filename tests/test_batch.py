"""Tests for repeated experiment execution."""

from types import SimpleNamespace

import src.batch as batch_module
from src.batch import BatchRunner


def test_batch_runner_creates_independent_seeded_records(monkeypatch, tmp_path):
    created = []

    class FakePipeline:
        def __init__(self, **kwargs):
            created.append(kwargs)
            self.run_id = f"run_{kwargs['seed']}"
            self.base_dir = str(tmp_path / self.run_id)
            self.manifest = SimpleNamespace(
                data={"status": "completed"},
                path=tmp_path / self.run_id / "run_manifest.json",
            )

        def run_full_pipeline(self, *args, **kwargs):
            return {"ok": True}

    monkeypatch.setattr(batch_module, "Pipeline", FakePipeline)
    monkeypatch.setattr(
        batch_module,
        "load_config",
        lambda _path: {"output": {"base_dir": str(tmp_path)}},
    )

    summary = BatchRunner({"config_path": "unused.yaml", "model": "local"}).run(
        user_context="context",
        runs=3,
        seed=123,
    )

    assert summary["status"] == "completed"
    assert summary["completed_runs"] == 3
    assert summary["failed_runs"] == 0
    assert len(summary["runs"]) == 3
    assert len({kwargs["seed"] for kwargs in created}) == 3
    assert summary["summary_path"]
    assert summary["summary_path"].endswith("/batch_manifest.json")
    assert all("/worlds" in kwargs["output_dir"] for kwargs in created)


def test_batch_runner_continues_after_one_failure(monkeypatch, tmp_path):
    call_count = 0

    class FakePipeline:
        def __init__(self, **kwargs):
            self.run_id = f"run_{kwargs['seed']}"
            self.base_dir = str(tmp_path / self.run_id)
            self.manifest = SimpleNamespace(
                data={"status": "failed"},
                path=tmp_path / self.run_id / "run_manifest.json",
            )

        def run_full_pipeline(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("intentional failure")
            self.manifest.data["status"] = "completed"
            return {"ok": True}

    monkeypatch.setattr(batch_module, "Pipeline", FakePipeline)
    monkeypatch.setattr(
        batch_module,
        "load_config",
        lambda _path: {"output": {"base_dir": str(tmp_path)}},
    )

    summary = BatchRunner({"config_path": "unused.yaml"}).run(
        user_context="context",
        runs=3,
        seed=456,
    )

    assert summary["status"] == "completed_with_errors"
    assert summary["completed_runs"] == 2
    assert summary["failed_runs"] == 1
    assert len(summary["runs"]) == 3
