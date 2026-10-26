"""Reference self-consistency gate and run-folder persistence for C041 (Lean 4 Proofs of Hidden Finite Lemmas).

AuthorityEffect: None.

This gate scores the frozen reference solver against this package's own judge
packet. It evaluates no model and it is not a Woland verdict: the Woland swarm
(``omega_engine_woland``) is the only final evaluator. Its labels are:

- REFERENCE_SELF_CONSISTENT: at least one case was scored; every case outcome
  has ``verified`` exactly True and a defect count of exactly 0; when a mutation
  suite was run it held at least one mutation and every mutation was rejected;
  every exact defect value that was measured is zero.
- REFERENCE_SELF_INCONSISTENT: anything else, including an empty suite.
- OPEN_RESIDUAL: consistent, but the caller declared a closed residual.

Run folders hold a four-file bundle (report written as novella.md,
dda_actions.jsonl, summary.json, receipt.json) in both
``_intelligence/_woland/runs/<task_key>/`` and
``_intelligence/symbol_game/runs/<task_key>/``. Every value in the bundle is
derived from the inputs; nothing is templated. Each bundle is staged beside its
destination and moved into place with os.replace. If writing fails, a
failure_receipt.json is written and the staged files are moved into the run
folder anyway: nothing under ``_intelligence/`` is ever deleted.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    resolve_intelligence_repo_root,
)

CHALLENGE_ID = "c041_lean4_finite_lemma_proofs"
CHALLENGE_TITLE = "C041 (Lean 4 Proofs of Hidden Finite Lemmas)"

GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"
TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
TERMINAL_REFUSE = "REFERENCE_SELF_INCONSISTENT"
TERMINAL_OPEN_RESIDUAL = "OPEN_RESIDUAL"
TERMINAL_VERDICTS = (TERMINAL_REFERENCE_SELF_CONSISTENT, TERMINAL_REFUSE, TERMINAL_OPEN_RESIDUAL)

RUN_FOLDER_EXISTS = "RUN_FOLDER_EXISTS"
FAILURE_RECEIPT_NAME = "failure_receipt.json"
DDC_ALPHABET = frozenset({"E", "R", "C", "I", "Λ", "D", "M", "T"})


class RunFolderExistsError(FileExistsError):
    """Raised when attempting to overwrite an existing run directory."""

    def __init__(self, message: str) -> None:
        self.code = RUN_FOLDER_EXISTS
        super().__init__(f"{RUN_FOLDER_EXISTS}: {message}")


def utc_timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sanitize_run_key(key: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]", "_", key.strip())
    if not clean or clean == "_":
        return f"c041_run_{int(datetime.now(timezone.utc).timestamp())}"
    return clean


def sha256_file(path: Path) -> str:
    """SHA-256 of the file bytes with CRLF normalised to LF (equal to git-blob content)."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def exact_defect_value(name: str, value: Any) -> Fraction | None:
    """Return an exact defect value, or None when it was not measured. Floats and booleans are refused."""
    if value is None:
        return None
    if type(value) is int or type(value) is Fraction:
        return Fraction(value)
    raise TypeError(
        f"{name} must be an exact int or Fraction, or None when not measured; got {type(value).__name__}"
    )


def exact_wire(value: Fraction | None) -> str | None:
    """Serialise an exact value as 'p/q' (integers without a slash); None stays None."""
    return None if value is None else str(value)


def _require_count(name: str, value: Any) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a non-negative int; got {value!r}")
    return value


def _optional_count(name: str, value: Any) -> int | None:
    return None if value is None else _require_count(name, value)


def case_passed(outcome: Mapping[str, Any]) -> bool:
    """True when the reference handled the case as the judge expects.

    That is a verified answer (``verified`` exactly True) or a refusal the checkers
    call warranted (``warranted_refusal`` exactly True), with a defect count of 0
    and no fatal error. A warranted refusal is consistent but is never counted as
    a verified answer: reports give the two counts separately.
    """
    defects = _require_count("defects", outcome.get("defects"))
    handled = outcome.get("verified") is True or outcome.get("warranted_refusal") is True
    return handled and defects == 0 and not outcome.get("fatal_error")


def case_warranted_refusal(outcome: Mapping[str, Any]) -> bool:
    """True for a consistent case whose answer is a warranted refusal rather than a verified answer."""
    return case_passed(outcome) and outcome.get("verified") is not True


def reference_claim_hygiene(
    verdict: str,
    total: int,
    passed: int,
    mutations_total: int | None,
    mutations_killed: int | None,
) -> dict[str, str]:
    """Claim hygiene derived from the measured counts of this run."""
    if mutations_total is None:
        mutation_text = "No mutation suite was run."
    else:
        mutation_text = f"{mutations_killed}/{mutations_total} hostile mutations were rejected."
    return {
        "supports": (
            f"The frozen reference solver's outputs were accepted, and matched the declared expectation, "
            f"on {passed}/{total} judge cases. {mutation_text}"
        ),
        "does_not_support": (
            "Any statement about a model (none was evaluated), about checker soundness or independence, "
            "about the Lean toolchain beyond the one that ran, or a Woland verdict."
        ),
        "narrowest_defensible_claim": (
            f"Reference self-consistency label {verdict} on the {total} judge cases scored in this run."
        ),
        "next_test_needed": (
            "Score a participant submission under a commitment made before the run and have the Woland swarm "
            "evaluate the bound checker receipts."
        ),
    }


def _write_failure_receipt(staging_dir: Path, target_dir: Path, error: BaseException) -> None:
    payload = {
        "authority_effect": "None",
        "challenge_id": CHALLENGE_ID,
        "error_message": str(error),
        "error_type": type(error).__name__,
        "files_present": sorted(p.name for p in staging_dir.iterdir()),
        "status": "RUN_FAILED",
        "target_dir": target_dir.name,
        "timestamp_utc": utc_timestamp_now(),
    }
    (staging_dir / FAILURE_RECEIPT_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def persist_single_bundle(
    target_dir: Path,
    novella_md: str,
    dda_steps: Sequence[Mapping[str, Any]],
    summary_data: Mapping[str, Any],
    receipt_data: Mapping[str, Any],
) -> tuple[Path, dict[str, Any]]:
    """Persist the 4-file bundle into target_dir (staging directory beside it, then os.replace).

    On failure a failure_receipt.json is written and the staged files are moved
    into target_dir; if that move fails the staging directory is left in place.
    Nothing is deleted. Returns the directory and the receipt payload written.
    """
    if target_dir.exists():
        raise RunFolderExistsError(f"Refusing to overwrite existing run directory: {target_dir}")
    parent_dir = target_dir.parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = Path(tempfile.mkdtemp(prefix=f".{target_dir.name}.staging.", dir=str(parent_dir)))

    try:
        novella_bytes = novella_md.encode("utf-8")
        (temp_dir / "novella.md").write_bytes(novella_bytes)
        novella_sha256 = hashlib.sha256(novella_bytes).hexdigest()

        dda_bytes = "".join(json.dumps(s, sort_keys=True) + "\n" for s in dda_steps).encode("utf-8")
        (temp_dir / "dda_actions.jsonl").write_bytes(dda_bytes)
        dda_actions_sha256 = hashlib.sha256(dda_bytes).hexdigest()
        dda_head_sha256 = dda_steps[-1].get("sha256") if dda_steps else None

        summary_payload = dict(summary_data)
        summary_payload["authority_effect"] = "None"
        summary_payload["dda_actions_sha256"] = dda_actions_sha256
        summary_payload["dda_head_sha256"] = dda_head_sha256
        summary_payload["novella_sha256"] = novella_sha256
        summary_bytes = (json.dumps(summary_payload, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        (temp_dir / "summary.json").write_bytes(summary_bytes)
        summary_sha256 = hashlib.sha256(summary_bytes).hexdigest()

        receipt_payload = dict(receipt_data)
        receipt_payload["authority_effect"] = "None"
        receipt_payload["files"] = {
            "dda_actions_sha256": dda_actions_sha256,
            "dda_head_sha256": dda_head_sha256,
            "novella_sha256": novella_sha256,
            "summary_sha256": summary_sha256,
        }
        receipt_bytes = (json.dumps(receipt_payload, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        (temp_dir / "receipt.json").write_bytes(receipt_bytes)
    except BaseException as error:
        try:
            _write_failure_receipt(temp_dir, target_dir, error)
            os.replace(temp_dir, target_dir)
        except OSError as custody_error:
            # The staging directory stays where it is; nothing is deleted.
            error.add_note(
                f"failure receipt not moved into place: {custody_error!r}; staging kept at {temp_dir}"
            )
        raise

    os.replace(temp_dir, target_dir)
    receipt_payload["receipt_sha256"] = hashlib.sha256(receipt_bytes).hexdigest()
    return target_dir, receipt_payload


class WolandRealityGate:
    """Reference self-consistency gate for C041 (historical class name kept for callers).

    ``intelligence_root`` is the directory that contains ``_intelligence/`` (the
    repository root), as before; it defaults to ``resolve_intelligence_repo_root()``.
    No directory is created until a bundle is persisted.

    AuthorityEffect: None.
    """

    def __init__(self, intelligence_root: Path | None = None) -> None:
        self.repo_root = (
            intelligence_root if intelligence_root is not None else resolve_intelligence_repo_root()
        )
        self.woland_runs_dir = self.repo_root / "_ic/darpa/woland" / "runs"
        self.symbol_game_runs_dir = self.repo_root / "_ic/darpa/symbol_game" / "runs"

    def determine_terminal_verdict(
        self,
        case_outcomes: Sequence[Mapping[str, Any]],
        *,
        mutations_total: int | None = None,
        mutations_killed: int | None = None,
        phi1: Fraction | int | None = None,
        gamma2: Fraction | int | None = None,
        has_closed_residual: bool = False,
    ) -> str:
        """Return REFERENCE_SELF_CONSISTENT, REFERENCE_SELF_INCONSISTENT or OPEN_RESIDUAL from exact counts."""
        return self._verdict_and_rationale(
            case_outcomes,
            mutations_total=mutations_total,
            mutations_killed=mutations_killed,
            phi1=phi1,
            gamma2=gamma2,
            has_closed_residual=has_closed_residual,
        )[0]

    def _verdict_and_rationale(
        self,
        case_outcomes: Sequence[Mapping[str, Any]],
        *,
        mutations_total: int | None,
        mutations_killed: int | None,
        phi1: Fraction | int | None,
        gamma2: Fraction | int | None,
        has_closed_residual: bool,
    ) -> tuple[str, str]:
        if type(has_closed_residual) is not bool:
            raise TypeError("has_closed_residual must be a bool")
        m_total = _optional_count("mutations_total", mutations_total)
        m_killed = _optional_count("mutations_killed", mutations_killed)
        if (m_total is None) != (m_killed is None):
            raise TypeError(
                "mutations_total and mutations_killed must both be given or both be None"
            )
        if m_total is not None and m_killed is not None and m_killed > m_total:
            raise ValueError(f"mutations_killed ({m_killed}) exceeds mutations_total ({m_total})")
        phi1_exact = exact_defect_value("phi1", phi1)
        gamma2_exact = exact_defect_value("gamma2", gamma2)

        total = len(case_outcomes)
        passed = sum(1 for c in case_outcomes if case_passed(c))
        total_defects = sum(_require_count("defects", c.get("defects")) for c in case_outcomes)

        if total == 0:
            return TERMINAL_REFUSE, "Empty judge suite: 0 cases scored."
        if passed != total or total_defects != 0:
            return (
                TERMINAL_REFUSE,
                f"{total - passed} of {total} cases did not pass; {total_defects} defects reported.",
            )
        if m_total is not None and m_total == 0:
            return TERMINAL_REFUSE, "Empty mutation suite: 0 mutations run."
        if m_total is not None and m_killed != m_total:
            return (
                TERMINAL_REFUSE,
                f"{m_total - m_killed} of {m_total} mutations were accepted by the checkers.",
            )
        if (phi1_exact is not None and phi1_exact != 0) or (
            gamma2_exact is not None and gamma2_exact != 0
        ):
            return TERMINAL_REFUSE, "A measured exact defect value is non-zero."
        if has_closed_residual:
            return (
                TERMINAL_OPEN_RESIDUAL,
                f"All {total} cases passed; the caller declared a closed residual.",
            )
        return (
            TERMINAL_REFERENCE_SELF_CONSISTENT,
            f"All {total} cases passed with zero reported defects.",
        )

    def evaluate(
        self,
        task_key: str,
        case_outcomes: Sequence[Mapping[str, Any]],
        budget_summary: Mapping[str, Any],
        ddc_steps: Sequence[Mapping[str, Any]] | None = None,
        narrative: str | None = None,
        *,
        mutations_total: int | None = None,
        mutations_killed: int | None = None,
        phi1: Fraction | int | None = None,
        gamma2: Fraction | int | None = None,
        has_closed_residual: bool = False,
    ) -> dict[str, Any]:
        """Label the run and persist the bundle to both run stores; return the receipt payload.

        ``narrative`` is optional caller text. It is kept in the report under a
        heading that marks it as not measured by this gate.
        """
        safe_task_key = sanitize_run_key(task_key)
        woland_target = self.woland_runs_dir / safe_task_key
        symbol_game_target = self.symbol_game_runs_dir / safe_task_key
        for target in (woland_target, symbol_game_target):
            if target.exists():
                raise RunFolderExistsError(f"Run folder already exists: {target}")

        verdict, verdict_rationale = self._verdict_and_rationale(
            case_outcomes,
            mutations_total=mutations_total,
            mutations_killed=mutations_killed,
            phi1=phi1,
            gamma2=gamma2,
            has_closed_residual=has_closed_residual,
        )

        total_cases = len(case_outcomes)
        passed_cases = sum(1 for c in case_outcomes if case_passed(c))
        warranted_refusal_cases = sum(1 for c in case_outcomes if case_warranted_refusal(c))
        failed_cases = total_cases - passed_cases
        total_defects = sum(_require_count("defects", c.get("defects")) for c in case_outcomes)
        phi1_wire = exact_wire(exact_defect_value("phi1", phi1))
        gamma2_wire = exact_wire(exact_defect_value("gamma2", gamma2))

        claim_hygiene = reference_claim_hygiene(
            verdict, total_cases, passed_cases, mutations_total, mutations_killed
        )
        novella_content = self._render_default_novella(
            task_key=safe_task_key,
            verdict=verdict,
            rationale=verdict_rationale,
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            claim_hygiene=claim_hygiene,
            mutations_total=mutations_total,
            mutations_killed=mutations_killed,
            phi1=phi1_wire,
            gamma2=gamma2_wire,
            narrative=narrative,
        )
        chain_events = self._build_chained_ddc_events(
            ddc_steps or [],
            task_key=safe_task_key,
            verdict=verdict,
            total_cases=total_cases,
            passed_cases=passed_cases,
            mutations_total=mutations_total,
            mutations_killed=mutations_killed,
        )

        timestamp = utc_timestamp_now()
        summary_data = {
            "budget_reconciliation": dict(budget_summary),
            "case_metrics": {
                "failed": failed_cases,
                "passed": passed_cases,
                "total": total_cases,
                "total_defects": total_defects,
                "verified_answers": passed_cases - warranted_refusal_cases,
                "warranted_refusals": warranted_refusal_cases,
            },
            "case_outcomes": [dict(c) for c in case_outcomes],
            "challenge_id": CHALLENGE_ID,
            "claim_hygiene": claim_hygiene,
            "gamma2": gamma2_wire,
            "gate_scope": GATE_SCOPE,
            "has_closed_residual": has_closed_residual,
            "mutations_killed": mutations_killed,
            "mutations_total": mutations_total,
            "phi1": phi1_wire,
            "rationale": verdict_rationale,
            "task_key": safe_task_key,
            "timestamp_utc": timestamp,
            "verdict": verdict,
        }
        receipt_data = {
            "challenge_id": CHALLENGE_ID,
            "gamma2": gamma2_wire,
            "gate_scope": GATE_SCOPE,
            "mutations_killed": mutations_killed,
            "mutations_total": mutations_total,
            "passed_cases": passed_cases,
            "phi1": phi1_wire,
            "protocol": "SG-CP v1",
            "verified_answer_cases": passed_cases - warranted_refusal_cases,
            "warranted_refusal_cases": warranted_refusal_cases,
            "receipt_id": f"rcpt_{safe_task_key}",
            "task_key": safe_task_key,
            "timestamp_utc": timestamp,
            "total_cases": total_cases,
            "verdict": verdict,
        }

        _, receipt_payload = persist_single_bundle(
            woland_target, novella_content, chain_events, summary_data, receipt_data
        )
        persist_single_bundle(
            symbol_game_target, novella_content, chain_events, summary_data, receipt_data
        )
        return receipt_payload

    def _render_default_novella(
        self,
        task_key: str,
        verdict: str,
        rationale: str,
        total_cases: int,
        passed_cases: int,
        failed_cases: int,
        claim_hygiene: Mapping[str, str],
        *,
        mutations_total: int | None = None,
        mutations_killed: int | None = None,
        phi1: str | None = None,
        gamma2: str | None = None,
        narrative: str | None = None,
    ) -> str:
        """Render the run report from measured values only (kept under the historical method name)."""
        mutation_cell = (
            "not run" if mutations_total is None else f"{mutations_killed}/{mutations_total}"
        )
        lines = [
            f"# Reference self-consistency report: {CHALLENGE_TITLE}",
            "",
            f"**Task key**: `{task_key}`  ",
            f"**Label**: `{verdict}`  ",
            f"**Scope**: `{GATE_SCOPE}`: the frozen reference solver scored against this package's own judge packet. "
            "No model was evaluated and this is not a Woland verdict.  ",
            "**AuthorityEffect**: None  ",
            f"**Timestamp**: {utc_timestamp_now()}  ",
            "",
            "## Measured values",
            "",
            "| Quantity | Value |",
            "| --- | --- |",
            f"| Judge cases scored | {total_cases} |",
            f"| Cases handled as the judge expects | {passed_cases} |",
            f"| Cases not passed | {failed_cases} |",
            f"| Hostile mutations rejected | {mutation_cell} |",
            f"| Phi_1 (exact) | {'not measured' if phi1 is None else phi1} |",
            f"| Gamma_2 (exact) | {'not measured' if gamma2 is None else gamma2} |",
            "",
            f"Rationale: {rationale}",
            "",
            "## Four-Part Claim Hygiene Summary",
            "",
            f"1. **Supports**: {claim_hygiene['supports']}",
            f"2. **Does not support**: {claim_hygiene['does_not_support']}",
            f"3. **Narrowest defensible claim**: {claim_hygiene['narrowest_defensible_claim']}",
            f"4. **Next test needed**: {claim_hygiene['next_test_needed']}",
            "",
        ]
        if narrative is not None:
            if type(narrative) is not str:
                raise TypeError("narrative must be a str or None")
            lines += ["## Caller-supplied notes (not measured by this gate)", "", narrative, ""]
        return "\n".join(lines)

    def _build_chained_ddc_events(
        self,
        raw_steps: Sequence[Mapping[str, Any]],
        *,
        task_key: str | None = None,
        verdict: str | None = None,
        total_cases: int | None = None,
        passed_cases: int | None = None,
        mutations_total: int | None = None,
        mutations_killed: int | None = None,
    ) -> list[dict[str, Any]]:
        """Hash-chain the caller's measured steps between an intake step and a label step.

        Every caller step needs a DDC letter and an action; nothing is filled in
        by default. ``phi1`` is carried only when the caller measured it, as an
        exact value serialised to a string.
        """
        steps: list[dict[str, Any]] = []
        if verdict is not None:
            steps.append(
                {
                    "action": "intake_judge_cases",
                    "details": {"case_count": total_cases, "mutation_count": mutations_total},
                    "letter": "C",
                }
            )
        for idx, step in enumerate(raw_steps):
            letter = step.get("letter")
            action = step.get("action")
            if letter not in DDC_ALPHABET:
                raise ValueError(
                    f"DDC step {idx} has letter {letter!r}, not in {sorted(DDC_ALPHABET)}"
                )
            if type(action) is not str or not action:
                raise ValueError(f"DDC step {idx} needs a non-empty action string")
            event: dict[str, Any] = {
                "action": action,
                "details": dict(step.get("details") or {}),
                "letter": letter,
            }
            if "phi1" in step:
                event["phi1"] = exact_wire(exact_defect_value("phi1", step["phi1"]))
            if "active_count" in step:
                event["active_count"] = _require_count("active_count", step["active_count"])
            steps.append(event)
        if verdict is not None:
            steps.append(
                {
                    "action": "emit_self_consistency_label",
                    "details": {
                        "label": verdict,
                        "mutations_killed": mutations_killed,
                        "passed_cases": passed_cases,
                        "scope": GATE_SCOPE,
                        "task_key": task_key,
                    },
                    "letter": "T",
                }
            )

        chained: list[dict[str, Any]] = []
        parent_sha = "0" * 64
        for idx, step in enumerate(steps):
            event = {
                **step,
                "parent_sha256": parent_sha,
                "step_index": idx,
                "timestamp": utc_timestamp_now(),
            }
            event_sha = hashlib.sha256(
                json.dumps(event, sort_keys=True).encode("utf-8")
            ).hexdigest()
            event["sha256"] = event_sha
            parent_sha = event_sha
            chained.append(event)
        return chained


__all__ = [
    "CHALLENGE_ID",
    "DDC_ALPHABET",
    "FAILURE_RECEIPT_NAME",
    "GATE_SCOPE",
    "RUN_FOLDER_EXISTS",
    "RunFolderExistsError",
    "TERMINAL_OPEN_RESIDUAL",
    "TERMINAL_REFERENCE_SELF_CONSISTENT",
    "TERMINAL_REFUSE",
    "TERMINAL_VERDICTS",
    "WolandRealityGate",
    "case_passed",
    "case_warranted_refusal",
    "exact_defect_value",
    "exact_wire",
    "persist_single_bundle",
    "reference_claim_hygiene",
    "sanitize_run_key",
    "sha256_file",
    "utc_timestamp_now",
]
