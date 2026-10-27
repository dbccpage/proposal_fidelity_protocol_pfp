#!/usr/bin/env python3
"""eval_epistemic_immune_transfer.py — Non-Abelian Holonomy (Gamma_2 > 0) Immune Transfer Test.

Evaluates whether the Epistemic Immune System with typed antibodies transfers from
Abelian Z_2 sign cancellation (FSP) to Non-Abelian holonomy obstructions (Gamma_2 > 0)
in Challenge C017 (S3, Q8 lattices).

AuthorityEffect: None.
Protocol: SG-CP v1 (Challenge C017).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

REPO_ROOT = next(
    (
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "pfp").is_dir() and (parent / "adversary").is_dir()
    ),
    None,
)
if REPO_ROOT is not None and str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pfp.infrastructure.estimated_gateway import (
    DurableRunGateway,
    EstimatedBudgetGateway,
)
from pfp.infrastructure.pilot_matrix import (
    complete_pilot_turn,
    make_pilot_gateways,
    validate_pilot_gateways,
)
from pfp.infrastructure.synthesis_matrix import RunnerRefusal, prepare_output_dir
from pfp.tests.demo_004.b_cohomology.c017_nonabelian_lattice_holonomy.judge_packet.checkers.dual_evaluator import (  # noqa: E402
    evaluate_dual,
)
from pfp.tests.demo_004.b_cohomology.c017_nonabelian_lattice_holonomy.reference_solver.solver import (  # noqa: E402
    solve as reference_solve,
)
from adversary.domain.providers.types import CandidateRequest, DecodingParamsV1


def _model_slug(model_id: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in model_id)


MODEL_PRICING = {
    "meta-llama/llama-3.3-70b-instruct": (0.12, 0.30),
}


class BudgetExceededError(RuntimeError):
    """Raised before a request that could exceed the configured spend ceiling."""


class BudgetGuard:
    """Enforce a configured-price ceiling using conservative request reservations."""

    def __init__(self, ceiling_usd: float) -> None:
        if ceiling_usd <= 0:
            raise ValueError("ceiling_usd must be positive")
        self.ceiling_usd = ceiling_usd
        self.total_spent = 0.0
        self.reserved_usd = 0.0

    def reserve_call(self, model: str, prompt: str, max_output_tokens: int) -> float:
        p_in, p_out = MODEL_PRICING.get(model, (0.20, 0.60))
        input_token_bound = len(prompt.encode("utf-8"))
        reservation = (input_token_bound * p_in + max_output_tokens * p_out) / 1e6
        projected = self.total_spent + self.reserved_usd + reservation
        if projected > self.ceiling_usd:
            raise BudgetExceededError(
                "BUDGET CEILING: refusing request because the configured-price "
                f"upper bound ${projected:.4f} exceeds ${self.ceiling_usd:.2f}."
            )
        self.reserved_usd += reservation
        return reservation

    def record_call(
        self,
        model: str,
        in_tokens: int,
        out_tokens: int,
        reservation: float,
    ) -> float:
        p_in, p_out = MODEL_PRICING.get(model, (0.20, 0.60))
        cost = (in_tokens * p_in + out_tokens * p_out) / 1e6
        self.reserved_usd = max(0.0, self.reserved_usd - reservation)
        self.total_spent += cost
        if self.total_spent + self.reserved_usd > self.ceiling_usd:
            raise BudgetExceededError(
                f"BUDGET CEILING BREACH: accounted spend ${self.total_spent:.4f} "
                f"exceeds configured ceiling ${self.ceiling_usd:.2f}."
            )
        return cost


def load_api_key(env_file: Path | None) -> str:
    """Load an explicitly requested dotenv file, then read the provider key."""
    if env_file is not None:
        try:
            from dotenv import load_dotenv
        except ImportError as exc:
            raise RuntimeError(
                'Using --env-file requires the benchmark dependencies: pip install -e ".[bench]"'
            ) from exc
        load_dotenv(env_file)
    return os.getenv("OPENROUTER_API_KEY", "")


def write_json(path: Path, value: object) -> bytes:
    """Write deterministic UTF-8/LF JSON and return the exact artifact bytes."""
    payload = json.dumps(value, indent=2, sort_keys=True).encode("utf-8")
    path.write_bytes(payload)
    return payload


# Non-Abelian Typed Antibodies
NONABELIAN_ANTIBODIES = [
    {
        "code": "ANTI_ORDER_REVERSAL",
        "axiom": "Path holonomy must multiply edges strictly along traversal direction: U(P) = U_{01} * U_{12} * U_{23} * U_{30}. In non-Abelian groups, A * B != B * A; reverse-order multiplication causes false flatness certifications.",
    },
    {
        "code": "ANTI_ABELIANIZATION_TRAP",
        "axiom": "Plaquette flatness (Gamma_2 = 0) requires the ordered product to equal the identity element 'e'. Evaluating 1D scalar characters (determinants, parity signs, traces) is insufficient; non-trivial elements in commutator subgroups (e.g., r^2 in S_3, -1 in Q_8) possess determinant +1 yet have non-trivial curvature Gamma_2 > 0.",
    },
    {
        "code": "ANTI_TORUS_TRIVIALITY_CONFUSION",
        "axiom": "On periodic boundaries (Torus T^2), zero local curvature on all plaquettes does NOT imply pure gauge. You must evaluate the non-contractible cycles A and B across periodic boundaries; if either holonomy is non-identity, the connection is FLAT_NONTRIVIAL.",
    },
    {
        "code": "ANTI_INVERSE_MISMATCH_BYPASS",
        "axiom": "Every oriented edge u->v with element U must have v->u with element U^{-1}. If any edge violates this, the input is OUT_OF_SCOPE with reason INVERSE_MISMATCH.",
    },
]


def build_c017_prompt(case: dict, include_antibodies: bool = False) -> str:
    """Build structured prompt for non-Abelian lattice holonomy deduction."""
    group = case["group"]
    prompt = f"""NON-ABELIAN LATTICE HOLONOMY CHALLENGE (C017)

Lattice: {case["L"]}x{case["M"]} square grid with boundary='{case["boundary"]}'.
Gauge Group: {group["name"]} (Order {group["order"]}, Identity='{group["identity"]}').
Elements: {group["elements"]}

Multiplication Table:
{json.dumps(group["table"], indent=2)}

Inverses:
{json.dumps(group["inverses"], indent=2)}

Edge Connections (U_uv on directed edge u->v):
{json.dumps(case["edges"], indent=2)}

TASK:
Determine whether this non-Abelian lattice connection possesses curvature obstruction (Gamma_2 > 0),
is pure gauge, is flat-nontrivial on the torus, or is out of scope.

Possible Verdicts:
1. "NOT_FLAT": If any plaquette [v0, v1, v2, v3] has holonomy U_01 * U_12 * U_23 * U_30 != identity.
2. "PURE_GAUGE": If all plaquettes are flat and there exists a vertex gauge g: V -> G flattening every edge.
3. "FLAT_NONTRIVIAL": If boundary='periodic', all plaquettes are flat, but global non-contractible loops A or B have non-identity holonomies.
4. "OUT_OF_SCOPE": If any edge has U_{{vu}} != (U_{{uv}})^{-1}.
"""

    if include_antibodies:
        prompt += "\nEPISTEMIC IMMUNE CONSTRAINTS (TYPED ANTIBODIES):\n"
        for ab in NONABELIAN_ANTIBODIES:
            prompt += f"- [{ab['code']}]: {ab['axiom']}\n"

    prompt += """
Emit ONLY valid JSON with keys:
{
  "status": "SOLVED" or "OUT_OF_SCOPE",
  "verdict": "NOT_FLAT" | "PURE_GAUGE" | "FLAT_NONTRIVIAL",
  "plaquette": ["v0", "v1", "v2", "v3"] (if NOT_FLAT),
  "holonomy": "element_name" (if NOT_FLAT),
  "gauge": {"u,v": "elem"} (if PURE_GAUGE),
  "base": "0,0", "loop_a": [...], "hol_a": "...", "loop_b": [...], "hol_b": "..." (if FLAT_NONTRIVIAL),
  "witness": {"edge": "...", "reason": "INVERSE_MISMATCH"} (if OUT_OF_SCOPE),
  "scratchpad": "step-by-step path ordered multiplication"
}
"""
    return prompt



def _accounting_states(gateway) -> dict[str, str]:
    if not isinstance(gateway, (DurableRunGateway, EstimatedBudgetGateway)):
        return {}
    limit = (
        gateway.limit
        if isinstance(gateway, EstimatedBudgetGateway)
        else gateway.scope["limit_microusd"]
    )
    with gateway.ledger.transaction(limit) as state:
        return {
            f"{kind}:{identity}": row["state"]
            for kind in ("attempts", "action_claims")
            for identity, row in state.get(kind, {}).items()
        }


def _query(
    model,
    prompt,
    *,
    dry_run,
    mock_solution,
    max_tokens,
    temperature,
    gateway=None,
    task_id=None,
    attempt_id=None,
    budget_ceiling=None,
) -> tuple[dict, dict]:
    """Keep legacy query aliases while retaining the actual checked PFP exchange."""
    if dry_run:
        solution = (
            mock_solution
            if mock_solution is not None
            else {"status": "SOLVED", "verdict": "NOT_FLAT"}
        )
        return solution, dict(
            ok=True,
            cost=0.0,
            latency=0.0,
            in_tokens=None,
            out_tokens=None,
            content=json.dumps(solution),
            reasoning=None,
            usage={"cost": 0.0},
            request={},
            pfp=None,
            provider_wire=None,
            raw_body=None,
            error=None,
            stop=False,
            attempt_state=None,
            cost_may_be_incurred=False,
            evidence_grade="HOST_REFERENCE_SELF_CONSISTENCY",
        )
    if budget_ceiling is not None:
        try:
            ceiling = Decimal(str(budget_ceiling))
        except InvalidOperation:
            ceiling = Decimal("NaN")
        code = "INVALID_BUDGET_CEILING" if not ceiling.is_finite() or ceiling <= 0 else None
        if code is None and isinstance(gateway, (DurableRunGateway, EstimatedBudgetGateway)):
            limit = (
                gateway.limit
                if isinstance(gateway, EstimatedBudgetGateway)
                else gateway.scope["limit_microusd"]
            )
            if Decimal(limit) > ceiling * 1_000_000:
                code = "LEGACY_BUDGET_CEILING_CONFLICT"
        if code is not None:
            return {}, dict(
                ok=False,
                cost=0.0,
                latency=0.0,
                in_tokens=None,
                out_tokens=None,
                content=None,
                reasoning=None,
                usage={},
                request={},
                pfp=None,
                provider_wire=None,
                raw_body=None,
                error=code,
                stop=True,
                attempt_state=None,
                cost_may_be_incurred=False,
                evidence_grade="UNVERIFIED",
            )
    before = _accounting_states(gateway)
    result = complete_pilot_turn(
        gateway,
        CandidateRequest(
            "Solve the supplied C017 task; put the JSON proposal in answer.",
            prompt,
            decoding=DecodingParamsV1(temperature=temperature),
        ),
        model=model,
        task_id=task_id or f"c017:{uuid4().hex}",
        attempt_id=attempt_id or uuid4().hex,
        max_tokens=max_tokens,
    )
    after = _accounting_states(gateway)
    incurred = bool(
        result.get("provider_wire") is not None
        or result["ok"]
        or any(after[key] != "refused_before_dispatch" for key in after.keys() - before.keys())
    )
    usage = result["usage"]
    meta = dict(
        result,
        cost=usage.get("cost") if incurred else 0.0,
        latency=result["elapsed"],
        in_tokens=usage.get("prompt_tokens"),
        out_tokens=usage.get("completion_tokens"),
        cost_may_be_incurred=incurred,
        evidence_grade="PFP_BOUND_PROPOSAL",
    )
    if not result["ok"]:
        return {}, meta
    try:
        solution = json.loads(result["content"])
    except (json.JSONDecodeError, TypeError):
        solution = None
    if not isinstance(solution, dict):
        meta.update(ok=False, error="C017_JSON_OBJECT_REQUIRED")
        return {}, meta
    return solution, meta


def query_model(
    model: str,
    prompt: str,
    api_key: str,
    budget_guard: BudgetGuard,
    dry_run: bool = False,
    mock_solution: dict | None = None,
    *,
    gateway=None,
    task_id=None,
    attempt_id=None,
    max_tokens: int = 2000,
) -> tuple[dict, dict]:
    """Use PFP accounting; the positional BudgetGuard is a retained legacy utility.

    Credentials and actual accounting belong to the injected gateway, not the
    legacy API-key or token-price estimate arguments.
    """
    return _query(
        model,
        prompt,
        dry_run=dry_run,
        mock_solution=mock_solution,
        max_tokens=max_tokens,
        temperature=0.1,
        gateway=gateway,
        task_id=task_id,
        attempt_id=attempt_id,
        budget_ceiling=budget_guard.ceiling_usd,
    )


def _run_cases(
    *,
    model,
    dry_run,
    case_files,
    arms,
    query,
    checker,
    max_tokens,
    original_max_tokens,
    output_dir,
    gateway,
    solver=reference_solve,
    max_estimated_cost_microusd,
    max_provider_calls,
    env_file,
    report_name,
    receipt_name,
    arm=None,
    budget_ceiling=None,
):
    """The three original experiments share one serial, continuing allowance."""
    if not case_files:
        raise RunnerRefusal("NO_CASE_SELECTED", "the case filter selected no original cases")
    if type(max_tokens) is not int or max_tokens < 1:
        raise RunnerRefusal("INVALID_OUTPUT_BOUND", "output tokens must be positive")
    if type(max_provider_calls) is not int or not 0 < max_provider_calls <= 64:
        raise RunnerRefusal("INVALID_CALL_LIMIT", "provider call allowance must be from 1 to 64")
    if max_estimated_cost_microusd is not None and (
        type(max_estimated_cost_microusd) is not int or not 0 < max_estimated_cost_microusd <= 50000
    ):
        raise RunnerRefusal(
            "INVALID_ESTIMATED_BUDGET", "estimated allowance must be from 1 to 50000 microUSD"
        )
    injected = gateway is not None
    ceiling = None
    if budget_ceiling is not None:
        try:
            ceiling = Decimal(str(budget_ceiling))
        except InvalidOperation as exc:
            raise RunnerRefusal(
                "INVALID_BUDGET_CEILING", "budget_ceiling must be positive and finite"
            ) from exc
        if not ceiling.is_finite() or ceiling <= 0:
            raise RunnerRefusal(
                "INVALID_BUDGET_CEILING", "budget_ceiling must be positive and finite"
            )
    if not dry_run:
        if gateway is None:
            if max_estimated_cost_microusd is None:
                raise RunnerRefusal(
                    "PFP_ACCOUNTED_GATEWAY_REQUIRED",
                    "supply a gateway or explicit estimated policy",
                )
            if output_dir is None:
                raise RunnerRefusal(
                    "OUTPUT_DIR_REQUIRED",
                    "gateway accounting needs an explicit new output directory",
                )
            if ceiling is not None and Decimal(max_estimated_cost_microusd) > ceiling * 1_000_000:
                raise RunnerRefusal(
                    "LEGACY_BUDGET_CEILING_CONFLICT", "gateway allowance exceeds budget_ceiling"
                )
        else:
            try:
                validate_pilot_gateways({model: gateway}, [model], max_tokens=max_tokens)
            except ValueError as exc:
                raise RunnerRefusal(str(exc), "PFP gateway preflight failed") from exc
            limit = (
                gateway.limit
                if isinstance(gateway, EstimatedBudgetGateway)
                else gateway.scope["limit_microusd"]
            )
            calls = (
                gateway.max_calls
                if isinstance(gateway, EstimatedBudgetGateway)
                else gateway.scope["max_calls"]
            )
            if calls > max_provider_calls:
                raise RunnerRefusal(
                    "PFP_CALL_ALLOWANCE_CONFLICT",
                    "gateway call allowance exceeds the requested cap",
                )
            if max_estimated_cost_microusd is not None and limit > max_estimated_cost_microusd:
                raise RunnerRefusal(
                    "PFP_COST_ALLOWANCE_CONFLICT",
                    "gateway financial allowance exceeds the requested cap",
                )
            if ceiling is not None and Decimal(limit) > ceiling * 1_000_000:
                raise RunnerRefusal(
                    "LEGACY_BUDGET_CEILING_CONFLICT", "gateway allowance exceeds budget_ceiling"
                )
    prepared_cases = []
    for case_id, case_path in case_files:
        case = json.loads(case_path.read_text(encoding="utf-8"))
        prepared_cases.append((case_id, case, tuple(
            (arm_id, prompt_builder(case)) for arm_id, prompt_builder in arms
        )))
    task_id = f"c017:{uuid4().hex}"
    objective = dict(
        challenge="C017",
        max_output_tokens=max_tokens,
        selected_public_tasks=[
            dict(case_id=case_id, arms=[dict(arm=arm_id, prompt=prompt)
                for arm_id, prompt in public_arms])
            for case_id, _case, public_arms in prepared_cases
        ],
    )
    objective_sha256 = hashlib.sha256(json.dumps(
        objective, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")).hexdigest()
    out = prepare_output_dir(Path(output_dir)) if output_dir is not None else None
    if not dry_run and gateway is None:
        try:
            gateway = make_pilot_gateways(
                [model],
                max_output_tokens=max_tokens,
                max_estimated_cost_microusd=max_estimated_cost_microusd,
                max_calls=max_provider_calls,
                accounting_path=out / "accounting.sqlite3",
                env_file=env_file,
                run_id=task_id,
                objective_sha256=objective_sha256,
            )[model]
        except ValueError as exc:
            raise RunnerRefusal(str(exc), "PFP gateway composition failed") from exc
    results = dict(
        timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        model=model,
        dry_run=dry_run,
        task_id=task_id,
        objective_sha256=objective_sha256,
        objective=objective,
        cases_evaluated=[],
        total_cost_usd=0.0,
        total_cost_known_subtotal_usd=0.0,
        stop_reason=None,
        evidence_grade="HOST_REFERENCE_SELF_CONSISTENCY"
        if dry_run
        else "PFP_BOUND_ORIGINAL_DUAL_JUDGES",
        original_max_output_tokens=original_max_tokens,
        max_output_tokens=max_tokens,
        selected_cases=[name for name, _ in case_files],
        attempted=0,
        financial_policy="host_fixture"
        if dry_run
        else "injected_accounted_gateway"
        if injected
        else "estimated_vendor_cost",
    )
    if arm is not None:
        results["arm"] = arm
    for index, (case_id, case, public_arms) in enumerate(prepared_cases):
        ref_solution, _ = solver(case)
        row = dict(
            case_id=case_id,
            expected_verdict=ref_solution.get("verdict", ref_solution.get("status")),
        )
        for arm_id, prompt in public_arms:
            if results["stop_reason"]:
                row[arm_id] = dict(
                    passed=False,
                    reason="NOT_RUN_AFTER_STOP",
                    meta=None,
                    verdict=None,
                    solution=None,
                    details={},
                )
                continue
            kwargs = dict(
                dry_run=dry_run,
                mock_solution=ref_solution,
                max_tokens=max_tokens,
                gateway=gateway,
                task_id=task_id,
                attempt_id=f"{task_id}:case-{index}:{arm_id}",
            )
            if arm is None:
                kwargs["budget_guard"] = BudgetGuard(budget_ceiling)
            solution, meta = query(model, prompt, "", **kwargs)
            results["attempted"] += 1
            cost = meta["cost"]
            if cost is None:
                results["total_cost_usd"] = None
            else:
                results["total_cost_known_subtotal_usd"] += cost
                if results["total_cost_usd"] is not None:
                    results["total_cost_usd"] += cost
            if meta["ok"]:
                ok, reason, details = checker(case, solution)
            else:
                ok, reason, details = False, meta["error"], {}
            scored = dict(
                verdict=solution.get("verdict"),
                passed=ok,
                reason=reason,
                solution=solution,
                meta=meta,
                details=details,
            )
            if arm is None:
                row[arm_id] = scored
            else:
                row.update(scored)
            if meta["stop"]:
                results["stop_reason"] = meta["error"] or "PFP_TERMINAL_STOP"
            print(f"{case_id} {arm_id}: {'PASS' if ok else 'REJECTED'} ({reason})", flush=True)
        results["cases_evaluated"].append(row)
        if results["stop_reason"]:
            break
    if gateway is not None and not dry_run:
        limit = (
            gateway.limit
            if isinstance(gateway, EstimatedBudgetGateway)
            else gateway.scope["limit_microusd"]
        )
        with gateway.ledger.transaction(limit) as state:
            states = {
                f"{kind}:{identity}": item["state"]
                for kind in ("attempts", "action_claims")
                for identity, item in state.get(kind, {}).items()
            }
            results["budget_summary"] = dict(
                ceiling_usd=budget_ceiling,
                gateway_limit_microusd=limit,
                ledger_spent_or_reserved_microusd=state["spent"],
                attempt_states=states,
                accounting_path=str(gateway.ledger.path),
            )
    else:
        results["budget_summary"] = dict(
            ceiling_usd=budget_ceiling, total_spent_usd=0.0, unsettled_reservation_usd=0.0
        )
    if out is not None:
        raw = write_json(out / report_name, results)
        passed = sum(
            int(entry["passed"]) if arm is not None else int(entry["immune_assisted"]["passed"])
            for entry in results["cases_evaluated"]
        )
        receipt_prefix = (
            "REC_C017_TRANSFER"
            if arm is None
            else ("REC_C017_ARM5_HYBRID" if arms[0][0] == "arm5" else "REC_C017_ARM6_DECIMATION")
        )
        scientific_outcome = "HOST_REFERENCE_SELF_CONSISTENCY"
        if not dry_run:
            if arm is None:
                scientific_outcome = (
                    "IMMUNE_ASSISTED_CASES_PASSED" if passed else "NO_IMMUNE_ASSISTED_CASE_PASSED"
                )
            else:
                scientific_outcome = (
                    "ORIGINAL_DUAL_JUDGE_CASES_PASSED"
                    if passed
                    else "NO_ORIGINAL_DUAL_JUDGE_CASE_PASSED"
                )
        receipt = dict(
            receipt_id=f"{receipt_prefix}_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}",
            model=model,
            authority_effect="None",
            sha256=hashlib.sha256(raw).hexdigest(),
            total_spent_usd=results["total_cost_usd"],
            status="PARTIAL" if results["stop_reason"] else "PASS",
            status_scope="harness_execution",
            evidence_grade=results["evidence_grade"],
            scientific_outcome=scientific_outcome,
            stop_reason=results["stop_reason"],
        )
        if arm is None:
            baseline_passed = sum(
                int(entry["baseline"]["passed"]) for entry in results["cases_evaluated"]
            )
            receipt.update(
                baseline_pass_rate=f"{baseline_passed}/{len(case_files)}",
                immune_pass_rate=f"{passed}/{len(case_files)}",
            )
        else:
            receipt[arms[0][0] + "_pass_rate"] = f"{passed}/{len(case_files)}"
        write_json(out / receipt_name, receipt)
    return results


def run_transfer_benchmark(
    model: str = "meta-llama/llama-3.3-70b-instruct",
    dry_run: bool = False,
    budget_ceiling: float = 0.50,
    env_file: Path | None = None,
    output_dir: Path | None = None,
    *,
    gateway=None,
    selected_case: str | None = None,
    max_tokens: int = 2000,
    max_estimated_cost_microusd: int | None = None,
    max_provider_calls: int = 10,
) -> dict:
    """Original paired prompts and judges, with a shared PFP financial allowance."""
    c017_cases_dir = Path(__file__).parent / "judge_packet" / "cases"
    test_cases = [
        ("pois_01_s3_commutator_trap", c017_cases_dir / "poisoned" / "pois_01.json"),
        ("base_01_s3_open_nonflat", c017_cases_dir / "base" / "base_01.json"),
        ("base_02_s3_open_puregauge", c017_cases_dir / "base" / "base_02.json"),
        ("base_03_s3_periodic_torus", c017_cases_dir / "base" / "base_03.json"),
        ("base_13_q8_open_nonflat", c017_cases_dir / "base" / "base_13.json"),
    ]
    test_cases = [c for c in test_cases if selected_case is None or selected_case in c[0]]
    return _run_cases(
        model=model,
        dry_run=dry_run,
        case_files=test_cases,
        arms=(
            ("baseline", lambda case: build_c017_prompt(case, include_antibodies=False)),
            ("immune_assisted", lambda case: build_c017_prompt(case, include_antibodies=True)),
        ),
        query=query_model,
        checker=evaluate_dual,
        max_tokens=max_tokens,
        original_max_tokens=2000,
        output_dir=output_dir,
        gateway=gateway,
        max_estimated_cost_microusd=max_estimated_cost_microusd,
        max_provider_calls=max_provider_calls,
        env_file=env_file,
        report_name="immune_transfer_report.json",
        receipt_name="receipt.json",
        budget_ceiling=budget_ceiling,
    )


def _main(run, argv, *, description, default_model, default_tokens, paired=False) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--dry-run", action="store_true", help="host reference self-consistency only"
    )
    parser.add_argument("--model", default=default_model)
    parser.add_argument("--case", help="original case-ID substring filter")
    parser.add_argument(
        "--max-output-tokens",
        "--max-tokens",
        dest="max_tokens",
        type=int,
        default=default_tokens,
        help="explicit override; estimated mode supports at most 3000",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="new directory; never overwrite historical results",
    )
    parser.add_argument(
        "--max-estimated-cost-microusd",
        type=int,
        help="explicit live estimated allowance (maximum 50000)",
    )
    parser.add_argument("--max-provider-calls", type=int, default=10)
    parser.add_argument("--env-file", type=Path, help="explicit credential file for the gateway")
    if paired:
        parser.add_argument(
            "--budget-ceiling",
            type=float,
            default=0.50,
            help="legacy USD ceiling remains an upper bound on the gateway allowance",
        )
    args = parser.parse_args(argv)
    try:
        kwargs = dict(
            model=args.model,
            dry_run=args.dry_run,
            selected_case=args.case,
            max_tokens=args.max_tokens,
            output_dir=args.output_dir,
            env_file=args.env_file,
            max_estimated_cost_microusd=args.max_estimated_cost_microusd,
            max_provider_calls=args.max_provider_calls,
        )
        if paired:
            kwargs["budget_ceiling"] = args.budget_ceiling
        result = run(**kwargs)
    except RunnerRefusal as exc:
        print(f"REFUSED {exc}")
        return 2
    print(json.dumps(result, indent=2))
    return 2 if result["stop_reason"] else 0


def main(argv=None) -> int:
    return _main(
        run_transfer_benchmark,
        argv,
        description=run_transfer_benchmark.__doc__,
        default_model="meta-llama/llama-3.3-70b-instruct",
        default_tokens=2000,
        paired=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
