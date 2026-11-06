"""
runner.py — Experiment runner and statistical evaluator for Challenge C005.

Orchestrates:
1. Probe verification for each arm (probe_before_trust.v1)
2. Execution across hidden base cases and poisoned cases
3. Accounting tracking (generation_id, tokens, billed cost, honored flag)
4. Primary metric evaluation: host-verified correct rate, exact McNemar paired test,
   Wilson score intervals for parseability, and false-witness laundering rates.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .client import GovernedClient
from .controls import ControlKind
from .poisoned_cases import POISONED_CASES
from .probes import run_control_probes
from .solve import solve_c005_case


def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Compute Wilson score interval for a binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    p_hat = successes / total
    denominator = 1.0 + (z**2) / total
    center = (p_hat + (z**2) / (2 * total)) / denominator
    spread = (z * math.sqrt((p_hat * (1 - p_hat) + (z**2) / (4 * total)) / total)) / denominator
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return (round(lower, 4), round(upper, 4))


def mcnemar_exact_p_value(b: int, c: int) -> float:
    """Exact two-tailed McNemar test using the binomial distribution."""
    n = b + c
    if n == 0:
        return 1.0
    p = 0.5
    min_discordant = min(b, c)
    cumulative = 0.0
    for k in range(min_discordant + 1):
        cumulative += math.comb(n, k) * (p**k) * ((1 - p) ** (n - k))
    return min(1.0, 2.0 * cumulative)


@dataclass
class ArmResult:
    arm_name: str
    control: str
    model: str
    honored: bool
    total_cases: int
    parseable_count: int
    parseable_rate: float
    parseable_wilson: tuple[float, float]
    verified_correct_count: int
    verified_correct_rate: float
    poisoned_total: int
    poisoned_laundered_count: int
    poisoned_laundering_rate: float
    total_cost_usd: float
    cost_per_verified_success: float | None
    case_results: list[dict[str, Any]] = field(default_factory=list)


def run_c005_arm(
    arm_name: str,
    control: ControlKind,
    client: GovernedClient,
    cases: list[dict[str, Any]],
    poisoned_cases: list[dict[str, Any]] | None = None,
) -> ArmResult:
    """Run one complete arm of Challenge C005."""
    # 1. Run probes to establish if control is honored
    honored, probe_results = (
        run_control_probes(
            completion_fn=lambda prompt, ctrl: client.complete(
                prompt,
                config=client.complete.__wrapped_config__
                if hasattr(client, "__wrapped_config__")
                else None,  # handled in solve
            ).content
            if False
            else client.complete(
                prompt, config=client.complete.__annotations__.get("control_config")
            ).content
            if False
            else client._execute_mock(prompt, config=None, max_tokens=64, t0=0).content
            if False
            else "mock",
            control=control,
        )
        if False
        else (True, [])
    )  # Handled cleanly below via actual client wrapper

    # Actual probe execution using client:
    from .controls import get_control_config

    def probe_caller(prompt: str, ctrl: ControlKind) -> str:
        cfg = get_control_config(kind=ctrl, task_family="consistency")
        rec = client.complete(prompt, control_config=cfg, max_tokens=64)
        return rec.content

    honored, probe_results = run_control_probes(probe_caller, control=control)

    parseable = 0
    correct = 0
    case_records: list[dict[str, Any]] = []

    # 2. Run standard / hidden cases
    for case in cases:
        res = solve_c005_case(case, client=client, control=control, control_honored=honored)
        is_parseable = res.refusal != "UNPARSEABLE"
        is_correct = res.status in ("SOLVED", "CONSISTENT", "INCONSISTENT") and res.refusal is None
        if is_parseable:
            parseable += 1
        if is_correct:
            correct += 1
        case_records.append(
            {
                "case_id": case.get("case_id"),
                "status": res.status,
                "refusal": res.refusal,
                "cost_usd": res.cost_usd,
                "is_parseable": is_parseable,
                "is_correct": is_correct,
            }
        )

    # 3. Run poisoned cases to check laundering (schema_is_shape_only.v1)
    p_cases = poisoned_cases or [
        {
            "case_id": pc.case_id,
            "kind": pc.kind,
            "prompt": pc.prompt,
            "edges": pc.edges,
            "weights": pc.weights,
        }
        for pc in POISONED_CASES
    ]

    poison_laundered = 0
    for pcase in p_cases:
        pres = solve_c005_case(pcase, client=client, control=control, control_honored=honored)
        # Laundering occurs if the output passed schema but was an invalid/suboptimal witness
        if pres.refusal in ("FALSE_WITNESS", "SUBOPTIMAL_OR_INVALID_REPAIR"):
            poison_laundered += 1

    total_n = len(cases)
    p_rate = round(parseable / total_n, 4) if total_n > 0 else 0.0
    c_rate = round(correct / total_n, 4) if total_n > 0 else 0.0
    w_interval = wilson_score_interval(parseable, total_n)
    laundering_rate = round(poison_laundered / len(p_cases), 4) if p_cases else 0.0

    total_cost = round(client.budget_controller.total_billed_usd, 6)
    cost_per_success = round(total_cost / correct, 6) if correct > 0 else None

    return ArmResult(
        arm_name=arm_name,
        control=control.value,
        model=client.model,
        honored=honored,
        total_cases=total_n,
        parseable_count=parseable,
        parseable_rate=p_rate,
        parseable_wilson=w_interval,
        verified_correct_count=correct,
        verified_correct_rate=c_rate,
        poisoned_total=len(p_cases),
        poisoned_laundered_count=poison_laundered,
        poisoned_laundering_rate=laundering_rate,
        total_cost_usd=total_cost,
        cost_per_verified_success=cost_per_success,
        case_results=case_records,
    )


def compare_arms_mcnemar(arm_a: ArmResult, arm_b: ArmResult) -> dict[str, Any]:
    """Compute paired McNemar test between two arms evaluated on identical cases."""
    assert arm_a.total_cases == arm_b.total_cases, "Arms must have identical case counts"
    n = arm_a.total_cases

    b = 0  # A correct, B incorrect
    c = 0  # A incorrect, B correct
    both_correct = 0
    both_incorrect = 0

    for res_a, res_b in zip(arm_a.case_results, arm_b.case_results):
        corr_a = res_a["is_correct"]
        corr_b = res_b["is_correct"]
        if corr_a and not corr_b:
            b += 1
        elif not corr_a and corr_b:
            c += 1
        elif corr_a and corr_b:
            both_correct += 1
        else:
            both_incorrect += 1

    p_val = mcnemar_exact_p_value(b, c)
    return {
        "arm_a": arm_a.arm_name,
        "arm_b": arm_b.arm_name,
        "n": n,
        "contingency_table": {
            "both_correct": both_correct,
            "a_correct_b_incorrect (b)": b,
            "a_incorrect_b_correct (c)": c,
            "both_incorrect": both_incorrect,
        },
        "mcnemar_exact_p_value": p_val,
        "statistically_significant": p_val < 0.05,
    }
