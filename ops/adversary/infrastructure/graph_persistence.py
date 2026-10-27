"""Graph evidence in Adversary's native reported bundle, with retained checkpoints.

Receipt SHA is returned as an external custody pin. Existing folders are
never overwritten. AuthorityEffect: None.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.evidence import sha256_ref
from adversary.domain.graph_ports import GraphRunReferenceV1
from adversary.domain.graph_task import GraphTaskResultV1, GraphTaskV1, read_json
from adversary.infrastructure.native import invoke as native_invoke
from adversary.infrastructure.native import value as native_value

from .teamwork_reporting import _atomic_write, checkpoint_reports


class GraphRunPersistence:
    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)
        self._working_directory: Path | None = None

    def _state_path(self, task: GraphTaskV1) -> Path:
        if self._working_directory is None:
            working = self.output_dir / "working"
            working.mkdir(parents=True, exist_ok=True)
            self._working_directory = Path(tempfile.mkdtemp(
                prefix="graph-" + task.task_ref[-12:] + "-", dir=working))
        return self._working_directory / "state.json"

    def checkpoint(self, task: GraphTaskV1, history: dict) -> dict:
        """Retain captures before projection; reporting cannot decide a graph check."""
        state_path = self.output_dir / "working"
        try:
            state_path = self._state_path(task)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            raw = (json.dumps(history, ensure_ascii=False, sort_keys=True,
                indent=2, allow_nan=False) + "\n").encode("utf-8")
            _atomic_write(state_path, raw)
            # Tuples in typed model metadata serialize as JSON arrays. Compare
            # the actual wire with that same wire, retaining the strict source
            # change check in the shared reporter.
            wire_history = read_json(raw, 16_777_216)
            return checkpoint_reports(state_path, wire_history, context=wire_history["report_context"])
        except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
            return {"status": "REPORTING_FAILED", "state_path": str(state_path),
                "detail": str(exc), "task_outcome_changed": False}

    def persist(
        self, task: GraphTaskV1, result: GraphTaskResultV1
    ) -> Result[GraphRunReferenceV1, Refusal]:
        rows = []
        for label, item in [
            ("Original", result.original),
            *(("Catalog", e) for e in result.evaluations),
        ]:
            measured = item.measurement
            rows.append(
                f"| {label} | {item.candidate_ref} | {measured.phi1 if measured else 'NOT_MEASURED'} | {measured.gamma2 if measured else 'NOT_MEASURED'} | {item.edit_cost if item.edit_cost is not None else 'NOT_MEASURED'} | {item.observer_sound} |"
            )
        narrative = (
            f"# Declared graph execution: {task.task_id}\n\n"
            f"Task: `{task.task_ref}`. Mode: `{result.mode}`. AuthorityEffect: None.\n\n"
            "The original diagnosis is retained separately from permitted candidate states. "
            "Source interpretation is declared by the caller; its natural-language faithfulness is unproved.\n\n"
            "| State | Candidate | Phi1 | Gamma2 | Edit cost | Observer coverage |\n"
            "|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
            f"Search: {result.search_status}. Optimality certified within the declared catalog: {result.optimality_certified}. "
            "Learning outputs remain inert review candidates.\n"
        )
        steps = tuple(read_json(raw) for raw in result.source_events)
        summary = {
            "schema_version": "core.adversary.graph-run.v1",
            "task_key": task.task_id,
            "task_ref": task.task_ref,
            "selected_candidate_id": result.selected_candidate_ref,
            "task_hex": task.to_bytes().hex(),
            "result": result.to_dict(),
            "authority_effect": "None",
        }
        complete = result.search_complete or (
            result.mode == "diagnose" and result.original.independently_checked)
        context = {"work_status": "COMPLETED" if complete else "PARTIAL",
            "evidence_verdict": "DECLARED_FINITE_GRAPH_CHECKS" if complete else "INCOMPLETE",
            "search_status": result.search_status, "mode": result.mode,
            "optimality_scope": "declared finite catalog only", "authority_effect": "None"}
        summary.update(original_seed=task.carrier.prompt, submitted_narrative=narrative,
            report_context=context,
            candidate_checks=[{"candidate_ref": item.candidate_ref,
                "checker_verdict": item.check.verdict.value,
                "independently_checked": item.independently_checked,
                "verified_repair": item.verified_repair, "reason": item.reason}
                for item in (result.original, *result.evaluations)])
        state_path = self.output_dir / "working"
        try:
            state_path = self._state_path(task)
            working = self.checkpoint(task, summary)
            if working["status"] == "REPORTING_FAILED":
                raise ValueError(working["detail"])
            projection = native_value("project_run_reports",
                history_json=json.dumps(summary, ensure_ascii=False),
                context_json=json.dumps(context, ensure_ascii=False), source_reference="summary.json")
            identity = native_value("receipt_id_v3", novella_md=projection["novella_md"],
                steps_json=json.dumps(steps, ensure_ascii=False),
                summary_json=json.dumps(summary, ensure_ascii=False), uts_jsonl=projection["uts_jsonl"])
            summary["receipt_id"] = identity
            receipt = {"schema_version": "core.adversary.graph-run-receipt.v1",
                "task_key": task.task_id, "receipt_id": identity, "task_ref": task.task_ref,
                "selected_candidate_id": result.selected_candidate_ref, "authority_effect": "None"}
            stored = native_invoke("persist_v3", output_dir=str(self.output_dir), run_key=task.task_id,
                receipt_json=json.dumps(receipt, ensure_ascii=False), novella_md=projection["novella_md"],
                steps_json=json.dumps(steps, ensure_ascii=False),
                summary_json=json.dumps(summary, ensure_ascii=False), uts_jsonl=projection["uts_jsonl"])
        except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
            return Err(Refusal("GRAPH_REPORTING_FAILED", str(exc), "adversary.graph.reporting",
                (("state_path", str(state_path)), ("task_outcome_changed", "False"))))
        if stored.is_err:
            return stored
        directory = Path(stored.unwrap())
        return Ok(
            GraphRunReferenceV1(
                str(directory),
                sha256_ref((directory / "receipt.json").read_bytes()),
                identity,
                result,
            )
        )
