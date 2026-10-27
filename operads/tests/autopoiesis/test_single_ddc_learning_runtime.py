"""Completion learns from the actual new reports and retained historical names."""
import json

import pytest

from operads.infrastructure.autopoiesis.learning_runtime import LearningCompletion


@pytest.mark.parametrize("reports", [("uns.md", "uts.jsonl", "ddc.jsonl"),
                                     ("novella.md", "dda_actions.jsonl", "ddc.jsonl")])
def test_learning_completion_imports_present_report_files(tmp_path, reports):
    (tmp_path / "receipt.json").write_text(json.dumps({"task_key": "actual-source"}), encoding="utf-8")
    (tmp_path / "summary.json").write_text("{}\n", encoding="utf-8")
    for name in reports:
        (tmp_path / name).write_bytes(b"retained observation\n")
    runtime = LearningCompletion(tmp_path, service=None)
    calls = []
    runtime.import_paths = lambda paths, **kwargs: calls.append((paths, kwargs))
    runtime.completed(str(tmp_path), outcome="OPEN_RESIDUAL")
    assert len(calls) == 1
    assert {path.name for path in calls[0][0]} == {"receipt.json", "summary.json", *reports}
    assert calls[0][1]["host"] == "adversary"
