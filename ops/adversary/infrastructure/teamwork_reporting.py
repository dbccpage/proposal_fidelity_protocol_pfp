"""Thin file I/O for native UNS/UTS projections of an existing Adversary state.

Reporting has its own status and cannot change the task's checked outcome.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from ..infrastructure.native import value as native_value


def _atomic_write(path: Path, raw: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _report_directory(state_path: Path) -> Path:
    directory = state_path.with_suffix(".reports")
    upgraded = state_path.with_suffix(".reports-v2")
    if upgraded.is_dir():
        return upgraded
    marker = directory / "reporting.json"
    if marker.is_file() and json.loads(marker.read_bytes()).get("schema_version") == "core.adversary.reporting-status.v1":
        return upgraded
    return directory


def _context(run) -> dict:
    if isinstance(run, dict):
        return {"work_status": run.get("work_status", run.get("terminal_status", "INCOMPLETE")),
                "evidence_verdict": run.get("evidence_verdict", run.get("terminal_verdict"))}
    context = {"work_status": run.work_status, "evidence_verdict": run.evidence_verdict}
    skipped = run.panel_coverage.get("skipped_by_schedule")
    if skipped:  # The native report lists these as schedule skips, not as missing seats.
        context["skipped_by_schedule"] = list(skipped)
    return context


def _execution_records(history: dict) -> list[dict]:
    """Retain observed actions and the latest actual procedure, without reissuing it.

    The ordered action projection is evidence, not an executable C/R/I/T program.
    The last sealed program already retains its prefix; copying every earlier
    program would count the same procedure repeatedly.
    """
    observations = history.get("observations", [])
    records = [{"record_kind": "observed_action", "action_id": item.get("action_id"),
                "worker": item.get("worker"), "summary": item.get("summary"),
                "blocked": item.get("blocked", False), "check": item.get("check"),
                "source_pointer": f"/source_history/observations/{index}"}
               for index, item in enumerate(observations)]
    programs = [(index, item["ddc_program"]) for index, item in enumerate(observations)
                if item.get("ddc_program")]
    if programs:
        index, program = programs[-1]
        records.extend({"record_kind": "retained_ddc_step", "step": step,
                        "source_pointer": f"/source_history/observations/{index}/ddc_program/steps/{offset}",
                        "program_binding": program["binding"], "run_path": program["run_path"]}
                       for offset, step in enumerate(program.get("steps", [])))
    return records


def checkpoint_reports(state_path: Path | str, run, *, finalize: bool = False,
                       output_dir: Path | str | None = None, context: dict | None = None) -> dict:
    """Project one saved checkpoint; exact repeated terminal publication reuses it.

    The caller saves state first and exposes the returned status. A report failure
    leaves the state intact. A resumed terminal snapshot gets a distinct immutable
    folder, while checkpoint views are replaceable projections.
    """
    state_path = Path(state_path).absolute()
    report_dir = state_path.with_suffix(".reports")
    status = {"schema_version": "core.adversary.reporting-status.v2", "authority_effect": "None",
              "state_path": str(state_path), "report_directory": str(report_dir)}
    try:
        report_dir = _report_directory(state_path)
        status["report_directory"] = str(report_dir)
        history = run.model_dump(mode="json") if hasattr(run, "model_dump") else dict(run)
        raw = state_path.read_bytes()
        if json.loads(raw) != history:
            raise ValueError("REPORT_SOURCE_CHANGED: saved state differs from supplied history")
        supplied_context = dict(context) if context is not None else _context(run)
        supplied_context["checkpoint_finalized"] = finalize
        projection = native_value("project_run_reports", history_json=json.dumps(history, ensure_ascii=False),
                                  context_json=json.dumps(supplied_context, ensure_ascii=False),
                                  source_reference="../" + state_path.name)
        if state_path.read_bytes() != raw:
            raise ValueError("REPORT_SOURCE_CHANGED: state changed during native projection")
        report_dir.mkdir(parents=True, exist_ok=True)
        steps = _execution_records(history)
        tape = native_value("tape", steps_json=json.dumps(steps, ensure_ascii=False))
        reports = {"uns.md": projection["novella_md"].encode("utf-8"),
                   "uts.jsonl": projection["uts_jsonl"].encode("utf-8"),
                   "ddc.jsonl": bytes.fromhex(tape["bytes_hex"])}
        for name, content in reports.items():
            _atomic_write(report_dir / name, content)
        status.update(status="MATERIALIZED", source_sha256=projection["source_sha256"],
                      source_file_sha256=hashlib.sha256(raw).hexdigest(),
                      files={name: hashlib.sha256(content).hexdigest() for name, content in reports.items()})
        if finalize:
            from operating_system.adapters.intelligence_custody.ic_routing import (
                intelligence_path,
            )
            from operating_system.adapters.intelligence_custody.intelligence_root import (
                resolve_intelligence_repo_root,
            )

            canonical = intelligence_path(resolve_intelligence_repo_root(), "_intelligence/_adversary")
            destination = Path(output_dir).absolute() if output_dir is not None else canonical
            if destination.resolve() != canonical.resolve():
                raise ValueError("ADVERSARY_OUTPUT_CUSTODY_INVALID: final reporting uses canonical _ic/adversary")
            final = native_value("project_run_reports", history_json=json.dumps(history, ensure_ascii=False),
                                 context_json=json.dumps(supplied_context, ensure_ascii=False),
                                 source_reference="summary.json#/source_history")
            run_id = history.get("run_id") or history.get("task_key")
            if not isinstance(run_id, str) or not run_id:
                raise ValueError("REPORT_RUN_ID_REQUIRED")
            run_key = run_id + "-" + final["source_sha256"][:12]
            summary = {"schema_version": "core.adversary.teamwork-report-summary.v1", "task_key": run_id,
                       "source_history": history, "report_context": supplied_context, "authority_effect": "None"}
            programs = [{"source_pointer": f"/source_history/observations/{index}/ddc_program",
                         "run_path": item["ddc_program"]["run_path"], "binding": item["ddc_program"]["binding"]}
                        for index, item in enumerate(history.get("observations", [])) if item.get("ddc_program")]
            summary.update(ddc_source_references=programs,
                           ddc_storage_status="EXISTING_PROGRAM_STEPS_RETAINED" if programs else
                           "ACTION_HISTORY_ONLY" if steps else "NOT_CAPTURED")
            receipt_id = native_value("receipt_id_v3", novella_md=final["novella_md"],
                                      steps_json=json.dumps(steps, ensure_ascii=False),
                                      summary_json=json.dumps(summary, ensure_ascii=False), uts_jsonl=final["uts_jsonl"])
            folder = destination / "runs" / native_value("run_name", run_key=run_key)
            if folder.exists():
                if native_value("verify_reported_bundle", run_dir=str(folder)) != receipt_id:
                    raise ValueError("REPORT_EXISTING_BUNDLE_CHANGED")
            else:
                native_value("persist_v3", output_dir=str(destination), run_key=run_key,
                             receipt_json=json.dumps({"schema_version": "core.adversary.teamwork-report-receipt.v1",
                                                      "task_key": run_id, "authority_effect": "None"}),
                             novella_md=final["novella_md"], steps_json=json.dumps(steps),
                             summary_json=json.dumps(summary, ensure_ascii=False), uts_jsonl=final["uts_jsonl"])
                if native_value("verify_reported_bundle", run_dir=str(folder)) != receipt_id:
                    raise ValueError("REPORT_PUBLISHED_BUNDLE_CHANGED")
            status.update(status="FINALIZED", bundle_directory=str(folder), receipt_id=receipt_id)
        # The last publication marker lets readers detect a crash between two
        # replace operations rather than treating mismatched views as complete.
        _atomic_write(report_dir / "reporting.json", _bytes(status))
        return status
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        status.update(status="REPORTING_FAILED", failure_code=str(exc).split(":", 1)[0],
                      detail=str(exc), task_outcome_changed=False)
        try:
            if report_dir.is_dir():
                _atomic_write(report_dir / "reporting.json", _bytes(status))
        except OSError:
            pass
        return status


def read_checkpoint_reports(state_path: Path | str) -> dict:
    """Validate the publication marker before a reader consumes working views."""
    state_path = Path(state_path).absolute()
    directory = state_path.with_suffix(".reports-v2")
    if not directory.is_dir():
        directory = state_path.with_suffix(".reports")
    status = json.loads((directory / "reporting.json").read_bytes())
    if status.get("schema_version") not in ("core.adversary.reporting-status.v1", "core.adversary.reporting-status.v2"):
        raise ValueError("REPORT_SCHEMA_UNSUPPORTED")
    if status.get("status") not in ("MATERIALIZED", "FINALIZED"):
        raise ValueError("REPORTING_INCOMPLETE")
    if hashlib.sha256(state_path.read_bytes()).hexdigest() != status["source_file_sha256"]:
        raise ValueError("REPORT_SOURCE_CHANGED")
    names = ("uns.md", "uts.jsonl", "ddc.jsonl") if status.get("schema_version") == "core.adversary.reporting-status.v2" else ("novella.md", "uts.jsonl")
    for name in names:
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != status["files"][name]:
            raise ValueError("REPORT_PUBLICATION_INCOMPLETE: " + name)
    return status
