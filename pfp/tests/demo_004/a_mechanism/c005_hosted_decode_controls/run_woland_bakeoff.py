"""
run_woland_bakeoff.py — C005 hosted decoding controls bake-off and its four-file run bundle.

What this runner does, and what it does not do:

1. It runs the C005 arms (A-none, A-bias, A-schema, A-gbnf and a frontier arm under JSON
   schema) on the first 20 hidden base cases through ``GovernedClient``. By default
   (``use_mock=True``, or when no ``OPENROUTER_API_KEY`` is in the environment) every arm
   runs against the client's mock responses; the bundle records ``execution_mode`` as
   ``MOCK`` or ``LIVE``. Arm scoring is done by ``runner.run_c005_arm``.
2. It compares hosted model arms. It is not a reference self-check and it issues no
   verdict: every bundle records ``terminal_verdict: null`` with ``verdict_status:
   NOT_ADJUDICATED``. The Woland swarm is the only final evaluator.
3. Every number in novella.md, summary.json and receipt.json is taken from the arm
   results; Phi_1 and Gamma_2 are not measured here and are recorded as null.
4. Run folders are new, time-stamped folders under
   ``resolve_intelligence_repo_root()``/_intelligence/_woland/runs. They are staged
   beside the destination and moved into place with ``os.replace``; an existing folder
   is never replaced and nothing is deleted. There is no second copy under the working
   directory.

``persist_run_folder`` and ``persist_benchmark_run`` are shared with the two C005
benchmark scripts and with ``run_150_tests_suite.py``.

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

for _parent in Path(__file__).resolve().parents:
    if (_parent / "omega_engine_pfp").is_dir() and (
        _parent / "omega_engine_woland"
    ).exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.budget_controller import (  # noqa: E402
    BudgetController,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.cases import (  # noqa: E402
    get_hidden_base_cases,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.client import (  # noqa: E402
    GovernedClient,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.controls import (  # noqa: E402
    ControlKind,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.poisoned_cases import (  # noqa: E402
    POISONED_CASES,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.probes import (  # noqa: E402
    CONTROL_HONORED_PROBES,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.runner import (  # noqa: E402
    ArmResult,
    compare_arms_mcnemar,
    run_c005_arm,
)

from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (  # noqa: E402
    resolve_intelligence_repo_root,
)

VERDICT_STATUS_NOT_ADJUDICATED = "NOT_ADJUDICATED"
VERDICT_NOTE = "No verdict is issued here; the Woland swarm is the only final evaluator."
RUN_FOLDER_EXISTS = "RUN_FOLDER_EXISTS"
FAILURE_RECEIPT_NAME = "failure_receipt.json"


class RunFolderExistsError(FileExistsError):
    """Raised instead of replacing an existing run folder."""

    def __init__(self, message: str) -> None:
        self.code = RUN_FOLDER_EXISTS
        super().__init__(f"{RUN_FOLDER_EXISTS}: {message}")


def not_adjudicated_fields() -> dict[str, Any]:
    """The verdict fields every C005 comparison bundle carries: no verdict is issued."""
    return {
        "terminal_verdict": None,
        "verdict_note": VERDICT_NOTE,
        "verdict_status": VERDICT_STATUS_NOT_ADJUDICATED,
    }


def utc_run_stamp() -> str:
    """Compact UTC time stamp used to give every run its own folder."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def woland_runs_root(intelligence_repo_root: Path | None = None) -> Path:
    """``<root>/_intelligence/_woland/runs``, where root defaults to ``resolve_intelligence_repo_root()``."""
    root = (
        intelligence_repo_root
        if intelligence_repo_root is not None
        else resolve_intelligence_repo_root()
    )
    return Path(root) / "_ic/darpa/woland" / "runs"


def _write_failure_receipt(staging_dir: Path, target_dir: Path, error: BaseException) -> None:
    payload = {
        "authority_effect": "None",
        "error_message": str(error),
        "error_type": type(error).__name__,
        "files_present": sorted(p.name for p in staging_dir.iterdir()),
        "status": "RUN_FAILED",
        "target_dir": target_dir.name,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    (staging_dir / FAILURE_RECEIPT_NAME).write_bytes(
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )


def persist_run_folder(target_dir: Path, files: Sequence[tuple[str, bytes]]) -> Path:
    """Write ``files`` (in order) into a new run folder and return it.

    An existing ``target_dir`` raises ``RunFolderExistsError`` and is left untouched.
    The files are staged in a sibling folder and moved into place with ``os.replace``.
    If writing fails, ``failure_receipt.json`` is written into the staging folder and the
    staging folder is moved into place (or left where it is if that move fails); the
    original error is re-raised. Nothing is deleted.
    """
    target = Path(target_dir)
    if target.exists():
        raise RunFolderExistsError(f"Refusing to overwrite existing run folder: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.staging.", dir=target.parent))
    try:
        for name, payload in files:
            (staging / name).write_bytes(payload)
    except BaseException as error:
        try:
            _write_failure_receipt(staging, target, error)
            os.replace(staging, target)
        except OSError as custody_error:
            error.add_note(
                f"failure receipt not moved into place: {custody_error!r}; staging kept at {staging}"
            )
        raise
    os.replace(staging, target)
    return target


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(payload), indent=2, sort_keys=True) + "\n").encode("utf-8")


def persist_benchmark_run(
    master_report: Mapping[str, Any],
    *,
    task_key: str,
    intelligence_repo_root: Path | None = None,
    run_stamp: str | None = None,
) -> Path:
    """Persist a C005 benchmark report, its summary and a receipt into a new run folder.

    The folder is ``<runs>/<task_key>_<utc stamp>``. The receipt binds the SHA-256 of
    the report and summary bytes and records that no verdict is issued.
    """
    report_bytes = _json_bytes(master_report)
    summary_data = {
        "benchmark_name": master_report["benchmark_name"],
        "budget_limit_usd": master_report["budget_limit_usd"],
        "claim_discipline": master_report["claim_hygiene"],
        "model": master_report["model"],
        "sample_size": master_report["sample_size"],
        "statistical_significance": master_report["statistical_tests"],
        "summary": master_report["summary"],
        "total_spend_usd": master_report["total_billed_spend_usd"],
        **not_adjudicated_fields(),
    }
    summary_bytes = _json_bytes(summary_data)
    receipt_data = {
        "artifact_hashes": {
            "master_evaluation_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
            "summary_sha256": hashlib.sha256(summary_bytes).hexdigest(),
        },
        "benchmark_name": master_report["benchmark_name"],
        "sample_size": master_report["sample_size"],
        "schema_version": "1.0.0",
        "task_key": task_key,
        "timestamp_utc": master_report["timestamp_utc"],
        "total_spend_usd": master_report["total_billed_spend_usd"],
        **not_adjudicated_fields(),
    }
    target = woland_runs_root(intelligence_repo_root) / f"{task_key}_{run_stamp or utc_run_stamp()}"
    return persist_run_folder(
        target,
        [
            ("master_evaluation_report.json", report_bytes),
            ("summary.json", summary_bytes),
            ("receipt.json", _json_bytes(receipt_data)),
        ],
    )


@dataclass
class WolandBoutContext:
    run_id: str
    target_key: str = "c005_mechanism_bakeoff"
    destination_dir: Path | None = None
    ddc_trace: list[dict[str, Any]] = field(default_factory=list)
    last_hash: str = "0" * 64
    seq_counter: int = 0

    def emit_rune(
        self, rune: str, description: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Emit hash-chained DDC action."""
        self.seq_counter += 1
        record: dict[str, Any] = {
            "seq": self.seq_counter,
            "rune": rune,
            "parent_sha256": self.last_hash,
            "description": description,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "payload": data or {},
        }
        encoded = json.dumps(record, sort_keys=True).encode("utf-8")
        rec_hash = hashlib.sha256(encoded).hexdigest()
        record["record_sha256"] = rec_hash
        self.last_hash = rec_hash
        self.ddc_trace.append(record)
        return record


def _arm_line(arm: ArmResult) -> str:
    return (
        f"`{arm.arm_name}`: parseable {arm.parseable_count}/{arm.total_cases}, host-verified correct "
        f"{arm.verified_correct_count}/{arm.total_cases}, control honored under probes: {arm.honored}, "
        f"poisoned cases laundered {arm.poisoned_laundered_count}/{arm.poisoned_total}"
    )


def execute_c005_woland_bout(
    frontier_model: str = "meta-llama/llama-3.1-405b-instruct",
    baseline_model: str = "meta-llama/llama-3.1-8b-instruct",
    use_mock: bool = True,
    *,
    intelligence_repo_root: Path | None = None,
) -> dict[str, Any]:
    """Run the C005 bake-off arms and persist a four-file bundle. No verdict is issued."""
    timestamp_str = utc_run_stamp()
    run_id = f"c005_bakeoff_{timestamp_str}"
    ctx = WolandBoutContext(run_id=run_id)
    execution_mode = "MOCK" if (use_mock or not os.getenv("OPENROUTER_API_KEY")) else "LIVE"

    budget_ctrl = BudgetController(ceiling_usd=0.10, target_spend_usd=0.05, hard_kill_usd=0.25)
    ctx.emit_rune(
        "I",
        "Intake: models, execution mode and budget controller parameters",
        {
            "baseline_model": baseline_model,
            "budget_ceiling_usd": budget_ctrl.ceiling_usd,
            "execution_mode": execution_mode,
            "frontier_model": frontier_model,
            "hard_kill_usd": budget_ctrl.hard_kill_usd,
            "target_spend_usd": budget_ctrl.target_spend_usd,
        },
    )

    evaluation_subset = get_hidden_base_cases()[:20]
    client_baseline = GovernedClient(
        provider="openrouter",
        model=baseline_model,
        budget_controller=budget_ctrl,
        mock_mode=use_mock,
    )
    client_frontier = GovernedClient(
        provider="openrouter",
        model=frontier_model,
        budget_controller=budget_ctrl,
        mock_mode=use_mock,
    )

    ctx.emit_rune(
        "C",
        "Context: each arm runs the control-honored probes before scoring",
        {
            "probes_per_arm": len(CONTROL_HONORED_PROBES),
            "cases_per_arm": len(evaluation_subset),
        },
    )

    arms: list[ArmResult] = []
    for arm_name, control, client in (
        ("A-none", ControlKind.NONE, client_baseline),
        ("A-bias", ControlKind.LOGIT_BIAS, client_baseline),
        ("A-schema", ControlKind.JSON_SCHEMA, client_baseline),
        ("A-gbnf", ControlKind.GBNF, client_baseline),
        ("Frontier-405B-schema", ControlKind.JSON_SCHEMA, client_frontier),
    ):
        arm = run_c005_arm(arm_name, control, client, evaluation_subset)
        arms.append(arm)
        ctx.emit_rune(
            "D",
            f"Arm {arm_name} completed",
            {
                "correct_count": arm.verified_correct_count,
                "honored": arm.honored,
                "model": arm.model,
                "parseable_count": arm.parseable_count,
                "poisoned_laundered_count": arm.poisoned_laundered_count,
                "poisoned_total": arm.poisoned_total,
                "total_cases": arm.total_cases,
            },
        )
    arm_none, arm_bias, arm_schema, arm_gbnf, arm_frontier_schema = arms

    ctx.emit_rune(
        "Λ",
        "Illustrative scene only: no carrier lift is computed in this bake-off",
        {
            "lift_computed": False,
        },
    )

    mcn_schema_vs_none = compare_arms_mcnemar(arm_schema, arm_none)
    mcn_frontier_vs_baseline = compare_arms_mcnemar(arm_frontier_schema, arm_schema)
    laundered_total = sum(arm.poisoned_laundered_count for arm in arms)
    poisoned_scored = sum(arm.poisoned_total for arm in arms)

    ctx.emit_rune(
        "R",
        "McNemar statistics computed from the arm results",
        {
            "frontier_vs_schema_p_value": mcn_frontier_vs_baseline["mcnemar_exact_p_value"],
            "poisoned_laundered_total": laundered_total,
            "poisoned_scored_total": poisoned_scored,
            "schema_vs_none_p_value": mcn_schema_vs_none["mcnemar_exact_p_value"],
        },
    )
    ctx.emit_rune(
        "T",
        "Run closed without a verdict",
        {
            "execution_mode": execution_mode,
            "gamma_2": None,
            "phi_1": None,
            "total_spend_usd": budget_ctrl.total_billed_usd,
            **not_adjudicated_fields(),
        },
    )

    arm_lines = "\n".join(f"- {_arm_line(arm)}" for arm in arms)
    within_limits = budget_ctrl.total_billed_usd <= budget_ctrl.ceiling_usd

    novella_md = f"""# The Master and Margarita: The Hosted Decoding Controls Bake-off
## Challenge C005 — Parameter Scale and Decoding Constraints

> **Scope.** Execution mode `{execution_mode}`. This run compares hosted decoding-control arms; it issues no verdict (`verdict_status: {VERDICT_STATUS_NOT_ADJUDICATED}`). {VERDICT_NOTE} The scenes are illustrative framing; every number in them comes from the arm results below.

## Measured values

{arm_lines}
- McNemar exact p-value, A-schema vs A-none: {mcn_schema_vs_none["mcnemar_exact_p_value"]}
- McNemar exact p-value, frontier arm vs A-schema: {mcn_frontier_vs_baseline["mcnemar_exact_p_value"]}
- Recorded spend: ${budget_ctrl.total_billed_usd:.6f} over {budget_ctrl.call_count} billed calls (ceiling ${budget_ctrl.ceiling_usd:.2f})

### Act I: Patriarchs' Ponds — The Vanity of Scale
In the warm spring twilight by Patriarchs' Ponds, Berlioz praised the frontier model `{frontier_model}`: surely a model of that size needs no constraints.

Woland leaned upon his cane. "A hosted route across an HTTP socket exposes no attention tensors and permits no key masks. Size is not an exemption from the host checker. Let us look at what the arms actually did."

### Act II: The Griboedov Restaurant — Cache & Budget Accounting
Koroviev unfurled the ledger. The budget controller's ceiling is ${budget_ctrl.ceiling_usd:.2f}, its target ${budget_ctrl.target_spend_usd:.2f} and its hard kill ${budget_ctrl.hard_kill_usd:.2f}. It recorded ${budget_ctrl.total_billed_usd:.6f} over {budget_ctrl.call_count} billed calls in `{execution_mode}` mode.

### Act III: Dr. Stravinsky's Clinic — The Probes & `probe_before_trust.v1`
"A provider's declaration is not a receipt," Dr. Stravinsky remarked. Each arm ran {len(CONTROL_HONORED_PROBES)} control-honored probes before scoring. Arms whose control was honored under the probes: {", ".join(arm.arm_name for arm in arms if arm.honored) or "none"}.

### Act IV: The Variety Theatre — The Decoding Controls Bake-off
The four controls and the frontier arm were run on {len(evaluation_subset)} hidden cases:

{arm_lines}

No 9-Dot Gauge Break is computed in this run; the scene is illustrative only.

### Act V: Apartment No. 50 — The Poisoned Cases & Laundering Detection
Azazello counted the poisoned cases each arm was scored on ({len(POISONED_CASES)} per arm). Across all arms, {laundered_total} of {poisoned_scored} poisoned runs were laundered into an accepted-looking witness.

### Act VI: The Great Ball at Satan's — McNemar Paired Tests
- A-schema vs A-none: exact McNemar p = {mcn_schema_vs_none["mcnemar_exact_p_value"]}.
- Frontier arm vs A-schema: exact McNemar p = {mcn_frontier_vs_baseline["mcnemar_exact_p_value"]}.

### Act VII: Satan's Gate — The Manuscripts Don't Burn
"Decoding controls govern output syntax; the host checker governs correctness," Woland said, and sealed the bundle.

**Verdict: not adjudicated.** {VERDICT_NOTE}
"""

    summary_data = {
        "challenge_id": "C005",
        "run_id": run_id,
        "execution_mode": execution_mode,
        "phi_1": None,
        "gamma_2": None,
        "defect_count": None,
        "total_spend_usd": round(budget_ctrl.total_billed_usd, 6),
        "target_spend_usd": budget_ctrl.target_spend_usd,
        "hard_kill_usd": budget_ctrl.hard_kill_usd,
        "arms": {
            arm.arm_name: {
                "model": arm.model,
                "honored": arm.honored,
                "parseable_rate": arm.parseable_rate,
                "verified_correct_rate": arm.verified_correct_rate,
                "wilson_interval": arm.parseable_wilson,
            }
            for arm in arms
        },
        "mcnemar_analysis": {
            "A-schema_vs_A-none": mcn_schema_vs_none,
            "Frontier-405B_vs_Baseline-8B": mcn_frontier_vs_baseline,
        },
        "poisoned_laundering_audit": {
            "poisoned_cases_per_arm": len(POISONED_CASES),
            "per_arm_laundered": {arm.arm_name: arm.poisoned_laundered_count for arm in arms},
            "laundered_total": laundered_total,
            "scored_total": poisoned_scored,
        },
        "claim_hygiene": {
            "supports": (
                f"In this {execution_mode} run on {len(evaluation_subset)} hidden cases, parseable counts were "
                + ", ".join(
                    f"{arm.arm_name} {arm.parseable_count}/{arm.total_cases}" for arm in arms
                )
                + f"; {laundered_total} of {poisoned_scored} poisoned runs were laundered."
            ),
            "does_not_support": (
                "Does not support that structured output implies mathematical correctness, that frontier model "
                "scale removes cycle-defect errors without host verification, or Layer-1 attention masking claims "
                "through Layer-2 hosted routes. A MOCK run says nothing about any hosted model."
            ),
            "narrowest_defensible_claim": (
                f"On the {len(evaluation_subset)} cases and routes of this {execution_mode} run, the arm counts "
                "above were measured by the C005 host checkers; no verdict is issued."
            ),
            "next_test_needed": (
                "Run the hosted arms live across the 100 hidden base cases under a commitment made before the run, "
                "and have the Woland swarm evaluate the bound checker receipts."
            ),
        },
        **not_adjudicated_fields(),
    }

    novella_bytes = novella_md.encode("utf-8")
    dda_bytes = ("\n".join(json.dumps(r, sort_keys=True) for r in ctx.ddc_trace) + "\n").encode(
        "utf-8"
    )
    summary_bytes = json.dumps(summary_data, indent=2, sort_keys=True).encode("utf-8")
    receipt_data = {
        "schema_version": "1.0.0",
        "challenge_id": "C005",
        "run_id": run_id,
        "target_key": ctx.target_key,
        "execution_mode": execution_mode,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "spend_accounting": {
            "total_billed_usd": round(budget_ctrl.total_billed_usd, 6),
            "billed_calls": budget_ctrl.call_count,
            "ceiling_usd": budget_ctrl.ceiling_usd,
            "target_spend_usd": budget_ctrl.target_spend_usd,
            "hard_kill_usd": budget_ctrl.hard_kill_usd,
            "budget_status": "WITHIN_LIMITS" if within_limits else "CEILING_EXCEEDED",
        },
        "artifact_hashes": {
            "novella_sha256": hashlib.sha256(novella_bytes).hexdigest(),
            "dda_actions_sha256": hashlib.sha256(dda_bytes).hexdigest(),
            "summary_sha256": hashlib.sha256(summary_bytes).hexdigest(),
            "dda_head_sha256": ctx.last_hash,
        },
        "operands_referenced": [
            "operand probe_before_trust.v1",
            "operand schema_is_shape_only.v1",
            "operand require_parameters_pin.v1",
        ],
        **not_adjudicated_fields(),
    }
    receipt_bytes = json.dumps(receipt_data, indent=2, sort_keys=True).encode("utf-8")

    dest_dir = woland_runs_root(intelligence_repo_root) / f"{ctx.target_key}_{timestamp_str}"
    ctx.destination_dir = persist_run_folder(
        dest_dir,
        [
            ("novella.md", novella_bytes),
            ("dda_actions.jsonl", dda_bytes),
            ("summary.json", summary_bytes),
            ("receipt.json", receipt_bytes),
        ],
    )

    return {
        "status": "COMPLETED",
        "execution_mode": execution_mode,
        "destination_dir": str(ctx.destination_dir),
        "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
        "summary": summary_data,
        **not_adjudicated_fields(),
    }


if __name__ == "__main__":
    result = execute_c005_woland_bout()
    print(
        f"C005 bake-off completed ({result['execution_mode']}); verdict status: {result['verdict_status']}"
    )
    print(f"Destination: {result['destination_dir']}")
    print(f"Spend: ${result['summary']['total_spend_usd']:.6f}")
