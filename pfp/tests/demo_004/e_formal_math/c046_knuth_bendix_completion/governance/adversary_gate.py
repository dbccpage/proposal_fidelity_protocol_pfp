"""Reference self-consistency gate and run-folder persistence for C046 (Knuth-Bendix Completion).

AuthorityEffect: None.

This gate scores the frozen reference solver against this package's own judge
packet. It evaluates no model and it is not a Adversary verdict: the Adversary swarm
(``adversary``) is the only final evaluator. Labels are computed from
exact counts only:

- REFERENCE_SELF_CONSISTENT: at least one case and at least one mutation were
  run, every case passed, the two checkers never disagreed, and every mutation
  was rejected.
- REFERENCE_SELF_INCONSISTENT: anything else, including an empty judge suite or
  an empty mutation suite.
- OPEN_RESIDUAL: consistent, but the caller declared a closed residual in
  ``scoring['residuals']``. Custody facts such as a missing judge manifest or
  pre-run commitment go in ``scoring['informational_residuals']``: they are
  recorded and do not change the label.

``emit_quad_bundle`` recomputes the label from the scoring counts and refuses a
caller label that differs. The run folder
``<intelligence root>/_intelligence/_adversary/runs/<name>`` holds a report
(novella.md), dda_actions.jsonl, summary.json and receipt.json, all derived from
the inputs. It is built in a staging directory beside the destination and moved
into place with os.replace; an existing folder is never overwritten. If writing
fails, a failure_receipt.json is written and the staged files are moved into
the run folder anyway: nothing under ``_intelligence/`` is ever deleted.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from operating_system.adapters.intelligence_custody.intelligence_root import (
    resolve_intelligence_repo_root,
)

CHALLENGE_ID = "c046_knuth_bendix_completion"
CHALLENGE_TITLE = "C046 (Knuth-Bendix Completion)"

GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"
TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
TERMINAL_REFUSE = "REFERENCE_SELF_INCONSISTENT"
TERMINAL_OPEN_RESIDUAL = "OPEN_RESIDUAL"
TERMINAL_VERDICTS = (TERMINAL_REFERENCE_SELF_CONSISTENT, TERMINAL_REFUSE, TERMINAL_OPEN_RESIDUAL)

RUN_FOLDER_EXISTS = "RUN_FOLDER_EXISTS"
LABEL_MISMATCH = "LABEL_MISMATCH"
FAILURE_RECEIPT_NAME = "failure_receipt.json"
COUNT_KEYS = ("total_cases", "passed_cases", "disagreements", "mutations_killed", "total_mutations")


class RunFolderExistsError(FileExistsError):
    """Raised instead of overwriting an existing run folder."""

    def __init__(self, message: str) -> None:
        self.code = RUN_FOLDER_EXISTS
        super().__init__(f"{RUN_FOLDER_EXISTS}: {message}")


class LabelMismatchError(ValueError):
    """A caller-supplied label differs from the label computed from the counts."""

    def __init__(self, message: str) -> None:
        self.code = LABEL_MISMATCH
        super().__init__(f"{LABEL_MISMATCH}: {message}")


def utc_timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sanitize_run_key(key: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]", "_", str(key).strip())
    return clean if clean.strip("_") else "run"


def _require_count(name: str, value: Any) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a non-negative int; got {value!r}")
    return value


def evaluate_label(
    total_cases: int,
    passed_cases: int,
    disagreements: int,
    mutations_killed: int,
    total_mutations: int,
    *,
    residuals: Sequence[str] = (),
) -> tuple[str, str]:
    """Return (label, reason) from exact counts. Empty suites are inconsistent; there is no threshold."""
    _require_count("total_cases", total_cases)
    _require_count("passed_cases", passed_cases)
    _require_count("disagreements", disagreements)
    _require_count("mutations_killed", mutations_killed)
    _require_count("total_mutations", total_mutations)
    if passed_cases > total_cases:
        raise ValueError(f"passed_cases ({passed_cases}) exceeds total_cases ({total_cases})")
    if mutations_killed > total_mutations:
        raise ValueError(
            f"mutations_killed ({mutations_killed}) exceeds total_mutations ({total_mutations})"
        )
    if isinstance(residuals, str) or any(type(r) is not str for r in residuals):
        raise TypeError("residuals must be a sequence of strings")

    if total_cases == 0:
        return TERMINAL_REFUSE, "Empty judge suite: 0 cases scored."
    if total_mutations == 0:
        return TERMINAL_REFUSE, "Empty mutation suite: 0 mutations run."
    if disagreements != 0:
        return TERMINAL_REFUSE, f"The checkers disagreed on {disagreements} of {total_cases} cases."
    if passed_cases != total_cases:
        return TERMINAL_REFUSE, f"{total_cases - passed_cases} of {total_cases} cases did not pass."
    if mutations_killed != total_mutations:
        return (
            TERMINAL_REFUSE,
            f"{total_mutations - mutations_killed} of {total_mutations} mutations were not rejected.",
        )
    if residuals:
        return (
            TERMINAL_OPEN_RESIDUAL,
            f"All {total_cases} cases passed; residuals: {', '.join(residuals)}.",
        )
    return TERMINAL_REFERENCE_SELF_CONSISTENT, (
        f"All {total_cases} cases passed; {mutations_killed}/{total_mutations} mutations rejected."
    )


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _chain(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    chained: list[dict[str, Any]] = []
    parent = "0" * 64
    for idx, row in enumerate(rows):
        item = {**row, "parent_sha256": parent, "step_index": idx}
        item["sha256"] = hashlib.sha256(
            json.dumps(item, sort_keys=True).encode("utf-8")
        ).hexdigest()
        parent = item["sha256"]
        chained.append(item)
    return chained


class AdversaryGateC046:
    """Reference self-consistency gate for C046 (historical class name kept for callers).

    Constructing the gate creates no directory; the run folder is created only
    when a bundle is persisted.

    AuthorityEffect: None.
    """

    def __init__(self, run_id: str, *, intelligence_repo_root: Path | None = None) -> None:
        self.run_id = run_id
        self.challenge_id = CHALLENGE_ID
        self.repo_root = (
            intelligence_repo_root
            if intelligence_repo_root is not None
            else resolve_intelligence_repo_root()
        )
        self.output_dir = (
            self.repo_root
            / "_ic/darpa/adversary"
            / "runs"
            / f"c046_eval_{sanitize_run_key(run_id)}"
        )

    def evaluate_verdict(
        self,
        total_cases: int,
        passed_cases: int,
        disagreements: int,
        mutations_killed: int,
        total_mutations: int,
        *,
        residuals: Sequence[str] = (),
    ) -> str:
        """Return the label computed from exact counts (see evaluate_label)."""
        return evaluate_label(
            total_cases,
            passed_cases,
            disagreements,
            mutations_killed,
            total_mutations,
            residuals=residuals,
        )[0]

    def emit_quad_bundle(
        self,
        verdict: str,
        scoring: Mapping[str, Any],
        case_records: Sequence[Mapping[str, Any]],
    ) -> Path:
        """Write the four files for a label recomputed from ``scoring``; return the run folder."""
        counts = {key: scoring.get(key) for key in COUNT_KEYS}
        raw_residuals = scoring.get("residuals", ())
        if isinstance(raw_residuals, str):
            raise TypeError("scoring['residuals'] must be a sequence of strings, not a string")
        residuals = list(raw_residuals)
        raw_notes = scoring.get("informational_residuals", ())
        if isinstance(raw_notes, str) or any(type(r) is not str for r in raw_notes):
            raise TypeError("scoring['informational_residuals'] must be a sequence of strings")
        notes = list(raw_notes)
        label, reason = evaluate_label(**counts, residuals=residuals)
        if verdict != label:
            raise LabelMismatchError(
                f"caller label {verdict!r} differs from computed label {label!r}"
            )

        target = self.output_dir
        if target.exists():
            raise RunFolderExistsError(f"Refusing to overwrite existing run directory: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.staging.", dir=str(target.parent)))

        try:
            novella_bytes = self._render_report(
                label,
                reason,
                counts,
                residuals,
                notes,
                scoring.get("mutations_rejected_by_both_checkers"),
            ).encode("utf-8")
            (staging / "novella.md").write_bytes(novella_bytes)

            rows: list[dict[str, Any]] = [
                {
                    "action": "intake_judge_cases",
                    "case_count": counts["total_cases"],
                    "letter": "C",
                    "mutation_count": counts["total_mutations"],
                },
            ]
            rows += [
                {"action": "score_case", "details": dict(rec), "letter": "R"}
                for rec in case_records
            ]
            rows.append(
                {
                    "action": "run_hostile_mutations",
                    "letter": "D",
                    "mutations_killed": counts["mutations_killed"],
                }
            )
            rows.append(
                {
                    "action": "emit_self_consistency_label",
                    "label": label,
                    "letter": "T",
                    "scope": GATE_SCOPE,
                }
            )
            dda_bytes = "".join(json.dumps(r, sort_keys=True) + "\n" for r in _chain(rows)).encode(
                "utf-8"
            )
            (staging / "dda_actions.jsonl").write_bytes(dda_bytes)

            summary = {
                **counts,
                "authority_effect": "None",
                "case_records": [dict(rec) for rec in case_records],
                "challenge_id": self.challenge_id,
                "gate_scope": GATE_SCOPE,
                "reason": reason,
                "residuals": residuals,
                "run_id": self.run_id,
                "timestamp_utc": utc_timestamp_now(),
                "verdict": label,
            }
            summary_bytes = _json_bytes(summary)
            (staging / "summary.json").write_bytes(summary_bytes)

            receipt = {
                **counts,
                "authority_effect": "None",
                "challenge_id": self.challenge_id,
                "dda_actions_sha256": hashlib.sha256(dda_bytes).hexdigest(),
                "gate_scope": GATE_SCOPE,
                "novella_sha256": hashlib.sha256(novella_bytes).hexdigest(),
                "residuals": residuals,
                "run_id": self.run_id,
                "scoring": dict(scoring),
                "summary_sha256": hashlib.sha256(summary_bytes).hexdigest(),
                "timestamp_utc": utc_timestamp_now(),
                "verdict": label,
            }
            (staging / "receipt.json").write_bytes(_json_bytes(receipt))
        except BaseException as error:
            try:
                failure = {
                    "authority_effect": "None",
                    "challenge_id": self.challenge_id,
                    "error_message": str(error),
                    "error_type": type(error).__name__,
                    "files_present": sorted(p.name for p in staging.iterdir()),
                    "run_id": self.run_id,
                    "status": "RUN_FAILED",
                    "timestamp_utc": utc_timestamp_now(),
                }
                (staging / FAILURE_RECEIPT_NAME).write_bytes(_json_bytes(failure))
                os.replace(staging, target)
            except OSError as custody_error:
                error.add_note(
                    f"failure receipt not moved into place: {custody_error!r}; staging kept at {staging}"
                )
            raise

        os.replace(staging, target)
        return target

    def _render_report(
        self,
        label: str,
        reason: str,
        counts: Mapping[str, int],
        residuals: list[str],
        notes: list[str] | None = None,
        rejected_by_both: int | None = None,
    ) -> str:
        lines = [
            f"# Reference self-consistency report: {CHALLENGE_TITLE}",
            "",
            f"- Run ID: `{self.run_id}`",
            f"- Label: `{label}`",
            f"- Scope: `{GATE_SCOPE}`: the frozen reference solver scored against this package's own judge packet; "
            "no model was evaluated and this is not a Adversary verdict.",
            f"- Reason: {reason}",
            f"- Judge cases passed: {counts['passed_cases']}/{counts['total_cases']}",
            f"- Cases on which the two checkers disagreed: {counts['disagreements']}",
            f"- Hostile mutations rejected by the dual evaluator: {counts['mutations_killed']}/{counts['total_mutations']}",
            "- Hostile mutations rejected by both checkers: "
            + (
                "not reported"
                if rejected_by_both is None
                else f"{rejected_by_both}/{counts['total_mutations']}"
            ),
            f"- Closed residuals (change the label): {', '.join(residuals) if residuals else 'none declared'}",
            f"- Recorded residuals (label unchanged): {', '.join(notes) if notes else 'none'}",
            "",
        ]
        return "\n".join(lines)


__all__ = [
    "CHALLENGE_ID",
    "FAILURE_RECEIPT_NAME",
    "GATE_SCOPE",
    "LABEL_MISMATCH",
    "LabelMismatchError",
    "RUN_FOLDER_EXISTS",
    "RunFolderExistsError",
    "TERMINAL_OPEN_RESIDUAL",
    "TERMINAL_REFERENCE_SELF_CONSISTENT",
    "TERMINAL_REFUSE",
    "TERMINAL_VERDICTS",
    "AdversaryGateC046",
    "evaluate_label",
    "sanitize_run_key",
]
