"""Unit and integration tests for FileRunRecorder (U01).

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from pfp.domain.ports.run_recorder import (
    RunId,
    RunStream,
    RunTrigger,
)
from pfp.infrastructure.persistence.file_run_recorder import (
    FileRunRecorder,
    compute_file_sha256,
)


def test_invalid_ic_activation_is_typed_without_writes_and_recovery_seals(tmp_path: Path) -> None:
    marker = tmp_path / "_ic/odni/migration/activation.json"
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b"{}")
    recorder = FileRunRecorder(root=tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    refused = recorder.open_run(RunTrigger.CLI, "custody-control")
    assert refused.is_err
    assert refused.unwrap_err().code == "ACTIVATION_INVALID"
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
    marker.unlink()
    opened = recorder.open_run(RunTrigger.CLI, "custody-control", budget_micro_usd=50_000)
    assert opened.is_ok
    run_id = opened.unwrap()
    assert recorder.append(run_id, RunStream.PACKETS, {"task": "custody-control"}).is_ok
    closed = recorder.close(run_id, summary={"status": "BOUNDED"}, report_md="custody control")
    assert closed.is_ok
    final_dir = Path(closed.unwrap())
    assert final_dir.parent == tmp_path / "_ic/darpa/symbol_game/runs"
    assert json.loads((final_dir / "packets.jsonl").read_bytes()) == {"task": "custody-control"}
    assert json.loads((final_dir / "receipt.json").read_bytes())["status"] == "SEALED"
    assert not (tmp_path / "_intelligence").exists()


def test_run_recorder_obstructed_root_returns_typed_io_refusal(tmp_path: Path) -> None:
    root = tmp_path / "not-a-directory"
    root.write_bytes(b"retain obstruction")
    result = FileRunRecorder(root=root).open_run(RunTrigger.CLI, "obstructed-root")
    assert result.is_err
    assert result.unwrap_err().code == "RUN_DIRECTORY_CREATION_FAILED"
    assert root.read_bytes() == b"retain obstruction"


def _snapshot(root: Path) -> dict[str, bytes | None]:
    return {
        path.relative_to(root).as_posix(): None if path.is_dir() else path.read_bytes()
        for path in root.rglob("*")
    }


def _mutate(recorder: FileRunRecorder, run_id: RunId, operation: str):
    if operation == "append":
        return recorder.append(run_id, RunStream.PACKETS, {"turn": 2})
    if operation == "close":
        return recorder.close(run_id, {"status": "done"}, "retained report")
    if operation == "abort":
        return recorder.abort(run_id, "bounded abort")
    return recorder._seal_and_rename(recorder._open_runs[run_id.value], status="SEALED")


def _assert_recovered(recorder: FileRunRecorder, run_id: RunId, operation: str) -> None:
    recovered = _mutate(recorder, run_id, operation)
    assert recovered.is_ok
    if operation == "append":
        recovered = recorder.close(run_id, {}, "after recovery")
        assert recovered.is_ok
    final = Path(recovered.unwrap())
    packet_rows = [json.loads(line) for line in (final / "packets.jsonl").read_text().splitlines()]
    assert packet_rows == ([{"turn": 1}, {"turn": 2}] if operation == "append" else [{"turn": 1}])
    receipt = json.loads((final / "receipt.json").read_bytes())
    assert receipt["status"] == ("ABORTED" if operation == "abort" else "SEALED")
    assert compute_file_sha256(final / "packets.jsonl") == receipt["files"]["packets.jsonl"]


@pytest.mark.parametrize("operation", ["append", "close", "abort", "seal"])
def test_midrun_invalid_activation_refuses_without_writes_then_recovers(
    tmp_path: Path, operation: str,
) -> None:
    recorder = FileRunRecorder(root=tmp_path)
    opened = recorder.open_run(RunTrigger.TEST, "midrun-activation")
    assert opened.is_ok
    run_id = opened.unwrap()
    assert recorder.append(run_id, RunStream.PACKETS, {"turn": 1}).is_ok
    marker = tmp_path / "_ic/odni/migration/activation.json"
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b"{}")
    before = _snapshot(tmp_path)
    refused = _mutate(recorder, run_id, operation)
    assert refused.is_err
    assert refused.unwrap_err().code == "ACTIVATION_INVALID"
    assert _snapshot(tmp_path) == before
    marker.unlink()  # Restore the original absence of an activation record.
    _assert_recovered(recorder, run_id, operation)


@pytest.mark.parametrize("operation", ["append", "close", "abort", "seal"])
@pytest.mark.parametrize("alias_name", ["packets.jsonl", "report.md", "receipt.json", "extra.txt"])
def test_midrun_hard_link_refuses_without_outside_writes_then_exact_restore_recovers(
    tmp_path: Path, operation: str, alias_name: str,
) -> None:
    recorder = FileRunRecorder(root=tmp_path)
    opened = recorder.open_run(RunTrigger.TEST, "midrun-hard-link")
    assert opened.is_ok
    run_id = opened.unwrap()
    assert recorder.append(run_id, RunStream.PACKETS, {"turn": 1}).is_ok
    info = recorder._open_runs[run_id.value]
    staged = info.staged_dir
    alias = staged / alias_name
    original = alias.read_bytes() if alias.exists() else None
    outside = tmp_path / "outside"
    outside.mkdir()
    external_file = outside / "retain.txt"
    external_file.write_bytes(original if original is not None else b"retain external bytes")
    alias.unlink(missing_ok=True)
    os.link(external_file, alias)
    assert alias.stat().st_nlink == 2
    before = _snapshot(tmp_path)
    try:
        refused = _mutate(recorder, run_id, operation)
        assert refused.is_err
        assert refused.unwrap_err().code == "HARD_LINK_REFUSED"
        assert _snapshot(tmp_path) == before
    finally:
        # Unlink only the alias and restore the original ordinary-file state.
        actual_alias = alias if staged.exists() else info.final_dir / alias_name
        actual_alias.unlink(missing_ok=True)
        if original is not None:
            actual_alias.write_bytes(original)
    _assert_recovered(recorder, run_id, operation)
    assert external_file.read_bytes() == (original if original is not None else b"retain external bytes")


@pytest.mark.skipif(os.name != "nt", reason="Windows junction control")
@pytest.mark.parametrize("operation", ["append", "close", "abort", "seal"])
@pytest.mark.parametrize("junction_target", ["staged", "final", "report"])
def test_midrun_junction_refuses_before_writes_then_exact_restore_recovers(
    tmp_path: Path, operation: str, junction_target: str,
) -> None:
    recorder = FileRunRecorder(root=tmp_path)
    opened = recorder.open_run(RunTrigger.TEST, "midrun-junction")
    assert opened.is_ok
    run_id = opened.unwrap()
    assert recorder.append(run_id, RunStream.PACKETS, {"turn": 1}).is_ok
    info = recorder._open_runs[run_id.value]
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel.txt").write_bytes(b"outside must remain unchanged")
    staged = info.staged_dir
    parked = staged.with_name(staged.name + ".parked")
    assert staged.absolute().is_relative_to(tmp_path.absolute())
    assert parked.absolute().is_relative_to(tmp_path.absolute())
    if junction_target == "staged":
        staged.rename(parked)
        junction = staged
    elif junction_target == "final":
        junction = info.final_dir
    else:
        junction = staged / "report.md"
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
        check=True, capture_output=True,
    )
    assert junction.is_junction()
    try:
        before_outside = _snapshot(outside)
        retained = parked if junction_target == "staged" else staged
        before_files = {
            p.name: p.read_bytes() for p in retained.iterdir() if p.is_file()
        }
        refused = _mutate(recorder, run_id, operation)
        assert refused.is_err
        assert refused.unwrap_err().code == "REPARSE_REFUSED"
        assert _snapshot(outside) == before_outside
        assert {p.name: p.read_bytes() for p in retained.iterdir() if p.is_file()} == before_files
    finally:
        # Removing a junction removes the link itself, never its target tree.
        if junction.is_junction():
            junction.rmdir()
        elif junction_target == "staged" and info.final_dir.is_junction():
            info.final_dir.rmdir()
        elif junction_target == "report" and (info.final_dir / "report.md").is_junction():
            (info.final_dir / "report.md").rmdir()
        if parked.exists():
            parked.rename(staged)
    _assert_recovered(recorder, run_id, operation)


def test_file_run_recorder_open_append_close_and_verify(tmp_path: Path) -> None:
    recorder = FileRunRecorder(root=tmp_path)

    open_res = recorder.open_run(
        trigger=RunTrigger.CLI,
        task_slug="test_cli_task",
        parent_run_ids=["parent_123"],
        run_mode="fixture",
        budget_micro_usd=50_000,
        model_registry_entries=["toy_model_v1"],
    )
    assert open_res.is_ok
    run_id = open_res.unwrap()
    assert isinstance(run_id, RunId)
    assert "test_cli_task" in run_id.value

    # Append to packets stream
    app_res = recorder.append(
        run_id,
        RunStream.PACKETS,
        {"prompt": "Calculate Phi1", "response": "Phi1 is 0"},
    )
    assert app_res.is_ok

    # Append to DDC stream
    app_ddc = recorder.append(
        run_id,
        RunStream.DDC_TRACE,
        {"letter": "C", "phi1": "0", "gamma2": "0"},
    )
    assert app_ddc.is_ok

    # Close the run
    summary = {"status": "SUCCESS", "turns": 1}
    report = "# Test Run Report\nSuccessful execution."
    close_res = recorder.close(run_id, summary=summary, report_md=report)
    assert close_res.is_ok
    final_dir = Path(close_res.unwrap())

    assert final_dir.is_dir()
    assert (final_dir / "manifest.json").exists()
    assert (final_dir / "packets.jsonl").exists()
    assert (final_dir / "ddc_trace.jsonl").exists()
    assert (final_dir / "summary.json").exists()
    assert (final_dir / "report.md").exists()
    assert (final_dir / "receipt.json").exists()

    receipt_data = json.loads((final_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt_data["status"] == "SEALED"
    assert receipt_data["authority_effect"] == "None"
    assert "packets.jsonl" in receipt_data["files"]
    assert "ddc_trace.jsonl" in receipt_data["files"]

    # Verify bound digests match actual files
    for fname, expected_hash in receipt_data["files"].items():
        actual_hash = compute_file_sha256(final_dir / fname)
        assert actual_hash == expected_hash

    # Appending after close must return RUN_NOT_OPEN
    post_close = recorder.append(run_id, RunStream.PACKETS, {"error": "late"})
    assert post_close.is_err
    assert post_close.unwrap_err().code == "RUN_NOT_OPEN"


def test_file_run_recorder_abort_preserves_partial_data(tmp_path: Path) -> None:
    recorder = FileRunRecorder(root=tmp_path)

    open_res = recorder.open_run(
        trigger=RunTrigger.TRIAL,
        task_slug="crash_task",
    )
    assert open_res.is_ok
    run_id = open_res.unwrap()

    recorder.append(run_id, RunStream.PACKETS, {"turn": 1, "status": "partial"})

    abort_res = recorder.abort(run_id, reason="Simulated process timeout")
    assert abort_res.is_ok
    final_dir = Path(abort_res.unwrap())

    assert final_dir.is_dir()
    assert (final_dir / "packets.jsonl").exists()
    receipt_data = json.loads((final_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt_data["status"] == "ABORTED"
    assert receipt_data["reason"] == "Simulated process timeout"

    summary_data = json.loads((final_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary_data["status"] == "ABORTED"
    assert summary_data["abort_reason"] == "Simulated process timeout"


def test_file_run_recorder_run_folder_exists_refusal(tmp_path: Path) -> None:
    recorder = FileRunRecorder(root=tmp_path)

    open_res = recorder.open_run(
        trigger=RunTrigger.TEST,
        task_slug="duplicate_task",
    )
    assert open_res.is_ok
    run_id = open_res.unwrap()
    recorder.close(run_id, summary={}, report_md="first")

    # Manually recreate folder with same name
    runs_dir = tmp_path / "_ic" / "darpa" / "symbol_game" / "runs"
    assert (runs_dir / run_id.value).exists()
