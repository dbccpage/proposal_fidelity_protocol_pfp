"""Bounded serial C005 benchmark through the existing accounted PFP boundary.

Original arm prompts, schemas, factorizers and exact final checks are retained.
Host dry fixtures establish finite schema/certificate self-consistency only.
Requested structured output and PFP wrapping do not prove provider-honored
controls; intermediate scratchpad values are not validated by the final judge.
Outputs go only to an explicitly selected fresh directory, with no new receipt.
AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

_worktree_root = next((parent for parent in Path(__file__).resolve().parents
    if (parent / "omega_engine_pfp").is_dir() and (parent / "omega_engine_woland").is_dir()), None)
if _worktree_root is not None and str(_worktree_root) not in sys.path:
    sys.path.insert(0, str(_worktree_root))

from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.cases import get_hidden_base_cases
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.checkers import verify_consistency_certificate
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.run_woland_bakeoff import (
    not_adjudicated_fields, persist_benchmark_run as persist_benchmark_run,
)
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.schemas import CONSISTENCY_JSON_SCHEMA
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.budget_controller import BudgetController
from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.empirical_001_runner import _complete_case
from omega_engine_pfp.infrastructure.pilot_matrix import _scope, make_pilot_gateways, validate_pilot_gateways
from omega_engine_pfp.infrastructure.synthesis_matrix import RunnerRefusal, prepare_output_dir
from omega_engine_woland.domain.providers.types import DecodingParamsV1
from jsonschema import Draft202012Validator
from decimal import Decimal, InvalidOperation
from uuid import uuid4
import argparse

# ------------------------------------------------------------------------------
# Schemas for Arms 2 and 3
# ------------------------------------------------------------------------------

# Arm 2 Schema: Topological Scratchpad with Strict Numeric Constraints
ARM2_NUMERIC_SCRATCHPAD_SCHEMA: dict[str, Any] = {
    "name": "arm2_numeric_scratchpad_consistency",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "scratchpad_tree_potentials": {
                "type": "object",
                "description": "Sequential integer potential propagation fixing n0=0, then computing potential(v) = potential(u) + delta for each tree edge.",
                "additionalProperties": {
                    "type": "string",
                    "pattern": "^-?[0-9]+$",
                },
            },
            "chord_validations": {
                "type": "array",
                "description": "Evaluation of each chord edge: diff = potential(v) - potential(u), compared against declared delta.",
                "items": {
                    "type": "object",
                    "properties": {
                        "chord": {"type": "string"},
                        "computed_diff": {"type": "string", "pattern": "^-?[0-9]+$"},
                        "target_delta": {"type": "string", "pattern": "^-?[0-9]+$"},
                        "is_satisfied": {"type": "boolean"},
                    },
                    "required": ["chord", "computed_diff", "target_delta", "is_satisfied"],
                    "additionalProperties": False,
                },
            },
            "verdict": {
                "type": "string",
                "enum": ["CONSISTENT", "INCONSISTENT"],
                "description": "CONSISTENT if and only if all chord edges are satisfied; INCONSISTENT otherwise.",
            },
            "certificate": {
                "type": "object",
                "description": "If CONSISTENT, map every node to its integer potential string (e.g. '0', '-7'). If INCONSISTENT, return empty object {}.",
                "additionalProperties": {
                    "type": "string",
                    "pattern": "^-?[0-9]+$",
                },
            },
        },
        "required": [
            "scratchpad_tree_potentials",
            "chord_validations",
            "verdict",
            "certificate",
        ],
        "additionalProperties": False,
    },
}

# Arm 3 Schema: Spanning-Tree Factorized Hieroglyphic Evaluation
ARM3_FACTORIZED_HIEROGLYPHIC_SCHEMA: dict[str, Any] = {
    "name": "arm3_hieroglyphic_chord_evaluation",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "chord_evaluations": {
                "type": "array",
                "description": "Direct evaluation of holonomy residuals for each fundamental cycle chord.",
                "items": {
                    "type": "object",
                    "properties": {
                        "chord_id": {"type": "string"},
                        "delta_pi": {
                            "type": "string",
                            "pattern": "^-?[0-9]+$",
                            "description": "pi(v) - pi(u)",
                        },
                        "declared_w": {
                            "type": "string",
                            "pattern": "^-?[0-9]+$",
                            "description": "Declared edge weight w",
                        },
                        "residual": {
                            "type": "string",
                            "pattern": "^-?[0-9]+$",
                            "description": "delta_pi - declared_w",
                        },
                        "cancels": {"type": "boolean"},
                    },
                    "required": ["chord_id", "delta_pi", "declared_w", "residual", "cancels"],
                    "additionalProperties": False,
                },
            },
            "verdict": {
                "type": "string",
                "enum": ["CONSISTENT", "INCONSISTENT"],
                "description": "CONSISTENT if all residuals == 0; INCONSISTENT if any residual != 0.",
            },
            "certificate": {
                "type": "object",
                "description": "Map from node to integer potential string if CONSISTENT, else empty object {}.",
                "additionalProperties": {
                    "type": "string",
                    "pattern": "^-?[0-9]+$",
                },
            },
        },
        "required": ["chord_evaluations", "verdict", "certificate"],
        "additionalProperties": False,
    },
}


# ------------------------------------------------------------------------------
# Factorization Helper for Arm 3
# ------------------------------------------------------------------------------


def factorize_case_to_hieroglyphics(case: dict[str, Any]) -> tuple[str, dict[str, str]]:
    """
    Decomposes graph into spanning tree potentials and fundamental cycle chords.
    Formats as compact DDC Hieroglyphic Runes:
    ∇Γ_T: (n0:0, n1:d1, ...)
    ∮_chords: (u→v:w)
    ?∮=0
    """
    edges = case["edges"]
    # Tree edges are n0->n1, n1->n2, ..., n_{k-1}->n_k
    # All nodes
    all_nodes = sorted(list({e[0] for e in edges} | {e[1] for e in edges}))

    # Breadth-first / linear spanning tree computation
    potentials: dict[str, int] = {all_nodes[0]: 0}
    tree_edges: list[tuple[str, str, int]] = []
    chord_edges: list[tuple[str, str, int]] = []

    # Identify spanning tree edges
    adj: dict[str, list[tuple[str, int]]] = {n: [] for n in all_nodes}
    for u, v, d in edges:
        adj[u].append((v, d))

    visited = {all_nodes[0]}
    queue = [all_nodes[0]]
    tree_edge_set = set()

    while queue:
        curr = queue.pop(0)
        for nxt, delta in adj[curr]:
            if nxt not in visited:
                visited.add(nxt)
                potentials[nxt] = potentials[curr] + delta
                tree_edges.append((curr, nxt, delta))
                tree_edge_set.add((curr, nxt, delta))
                queue.append(nxt)

    for u, v, d in edges:
        if (u, v, d) not in tree_edge_set:
            chord_edges.append((u, v, d))

    # Format dense hieroglyphic prompt
    tree_str = ", ".join(f"{n}:{potentials[n]}" for n in all_nodes)
    chord_str = (
        " ".join(f"({u}→{v}:{d:+d})" for u, v, d in chord_edges) if chord_edges else "(NONE)"
    )

    rune_prompt = (
        f"DDC Holonomy Verification ∇Γ:\n"
        f"Anchored Spanning Tree Potentials: [{tree_str}]\n"
        f"Fundamental Cycle Chords: {chord_str}\n"
        f"Evaluate holonomy residual ∮_i = (pi(v) - pi(u)) - w for each chord. "
        f"If all residuals == 0, output CONSISTENT with certificate; else INCONSISTENT."
    )

    cert_str_map = {n: str(potentials[n]) for n in all_nodes}
    return rune_prompt, cert_str_map


# ------------------------------------------------------------------------------
# Statistical Test Helpers
# ------------------------------------------------------------------------------


def compute_mcnemar(results_a: list[bool], results_b: list[bool]) -> dict[str, Any]:
    """Computes 2x2 contingency table and exact binomial p-value for paired McNemar test."""
    assert len(results_a) == len(results_b)
    len(results_a)

    # b: A correct, B incorrect
    # c: A incorrect, B correct
    a = sum(1 for ra, rb in zip(results_a, results_b) if ra and rb)
    b = sum(1 for ra, rb in zip(results_a, results_b) if ra and not rb)
    c = sum(1 for ra, rb in zip(results_a, results_b) if not ra and rb)
    d = sum(1 for ra, rb in zip(results_a, results_b) if not ra and not rb)

    # Exact two-tailed binomial test on discordant pairs (b, c)
    total_discordant = b + c
    if total_discordant == 0:
        p_value = 1.0
        statistic = 0.0
    else:
        # Normal approximation with continuity correction
        statistic = ((abs(b - c) - 1.0) ** 2) / total_discordant
        # Exact two-tailed binomial p-value
        k = min(b, c)
        p_val_sum = 0.0
        for i in range(k + 1):
            p_val_sum += math.comb(total_discordant, i) * (0.5**total_discordant)
        p_value = min(1.0, 2.0 * p_val_sum)

    return {
        "contingency_table": {"both_correct": a, "a_only": b, "b_only": c, "both_incorrect": d},
        "mcnemar_statistic": round(statistic, 4),
        "p_value": round(p_value, 6),
        "statistically_significant": p_value < 0.05,
    }


# ------------------------------------------------------------------------------
# Main Benchmark Execution
# ------------------------------------------------------------------------------


def _numeric_prompt(case):
    return (
        f"{case['prompt']}\n"
        f"Step 1: In scratchpad_tree_potentials, assign integer potentials setting n0='0', then recursively computing "
        f"potential(v) = potential(u) + delta for each tree edge as integer strings.\n"
        f"Step 2: In chord_validations, test whether potential(v) - potential(u) == target_delta for all chords.\n"
        f"Step 3: Conclude CONSISTENT (with full certificate of integer strings) or INCONSISTENT."
    )


def _arm_specs(case):
    rune_prompt, _ = factorize_case_to_hieroglyphics(case)
    return [
        ("arm1", "Arm 1: Direct Schema (Verdict First Baseline)", CONSISTENCY_JSON_SCHEMA, case["prompt"], 256, None),
        ("arm2", "Arm 2: Numeric-Constrained Topological Scratchpad", ARM2_NUMERIC_SCRATCHPAD_SCHEMA, _numeric_prompt(case), 512, None),
        ("arm3", "Arm 3: Spanning-Tree Factorized Hieroglyphic Prompt", ARM3_FACTORIZED_HIEROGLYPHIC_SCHEMA, rune_prompt, 512, None),
    ]


def _host_fixture(case, arm, canary_expected):
    """Schema/final-certificate fixture, not an intermediate-reasoning oracle."""
    _, potentials = factorize_case_to_hieroglyphics(case)
    result = dict(verdict=case["expected_verdict"], certificate=case["expected_certificate"])
    if arm == "arm2":
        result.update(scratchpad_tree_potentials=potentials, chord_validations=[])
    elif arm == "arm3":
        result["chord_evaluations"] = []
    elif arm == "arm4":
        result.update(scratchpad_potentials=potentials, chord_residuals=[],
            canary_check=dict(canary_edge="host_fixture", canary_expected_residual=str(canary_expected),
                canary_actual_residual=str(canary_expected), canary_passed=True))
    return result


def _summarize(records, name, *, canary=False):
    completed = [row for row in records if row["completed"]]
    count, correct = len(completed), sum(row["correct"] for row in completed)
    costs = [row["cost"] for row in records]
    known = sum(cost for cost in costs if cost is not None)
    total = None if any(cost is None for cost in costs) else known
    result = dict(arm_name=name, total_cases=len(records), completed_cases=count,
        incomplete_cases=len(records) - count, verified_correct_count=correct,
        verified_correct_rate=correct / count if count else None,
        parseable_rate=sum(row["parseable"] for row in records) / len(records) if records else None,
        total_spend_usd=total, known_cost_subtotal_usd=known,
        cost_per_verified_success_usd=total / correct if total is not None and correct else None,
        average_latency_sec=sum(row["duration"] for row in records) / len(records) if records else None)
    if canary:
        detected = sum(row.get("canary_detected", False) for row in completed)
        result.update(canaries_detected=detected, canary_detection_rate=detected / count if count else None)
    return result


def _paired(first, second, compute):
    a = {row["case_id"]: row for row in first if row["completed"]}
    b = {row["case_id"]: row for row in second if row["completed"]}
    ids = sorted(a.keys() & b.keys())
    if not ids:
        return dict(status="UNAVAILABLE", paired_total=0, contingency_table=None,
            mcnemar_statistic=None, p_value=None, statistically_significant=None)
    return dict(compute([a[key]["correct"] for key in ids], [b[key]["correct"] for key in ids]),
        status="AVAILABLE", paired_total=len(ids),
        scope="Complete observed pairs only; no provider-honoring or causal claim")


def _run_benchmark(*, model, gateway, gateways, output_dir, max_cases, max_provider_calls,
    max_tokens, max_estimated_cost_microusd, env_file, dry_run, budget_limit_usd, cases,
    specs, checker, compute, benchmark_name, summary_keys, comparisons):
    if type(max_cases) is not int or max_cases < 1:
        raise RunnerRefusal("INVALID_CASE_LIMIT", "select a positive bounded case count")
    if type(max_provider_calls) is not int or not 0 < max_provider_calls <= 64:
        raise RunnerRefusal("INVALID_CALL_LIMIT", "provider allowance must be from 1 to 64")
    if max_tokens is not None and (type(max_tokens) is not int or max_tokens < 1):
        raise RunnerRefusal("INVALID_OUTPUT_BOUND", "output override must be a positive integer")
    try:
        ceiling = Decimal(str(budget_limit_usd))
    except InvalidOperation as exc:
        raise RunnerRefusal("INVALID_BUDGET_CEILING", "ceiling must be finite and positive") from exc
    if not ceiling.is_finite() or ceiling <= 0:
        raise RunnerRefusal("INVALID_BUDGET_CEILING", "ceiling must be finite and positive")
    if max_estimated_cost_microusd is not None and (
        type(max_estimated_cost_microusd) is not int or not 0 < max_estimated_cost_microusd <= 50000):
        raise RunnerRefusal("INVALID_ESTIMATED_BUDGET", "estimated allowance must be from 1 to 50000 microUSD")
    bank = list(get_hidden_base_cases() if cases is None else cases)
    selected = [case for case in bank if case["kind"] == "consistency"][:max_cases]
    if not selected:
        raise RunnerRefusal("NO_CASE_SELECTED", "no consistency cases selected")
    if len({case["case_id"] for case in selected}) != len(selected):
        raise RunnerRefusal("DUPLICATE_CASE_ID", "case IDs must be unique")
    first_specs = specs(selected[0])
    bounds = {arm: max_tokens if max_tokens is not None else original for arm, _, _, _, original, _ in first_specs}
    distinct = set(bounds.values())
    if gateway is not None and gateways is not None:
        raise RunnerRefusal("AMBIGUOUS_GATEWAY", "supply one gateway form")
    if gateway is not None:
        if len(distinct) != 1:
            raise RunnerRefusal("PFP_OUTPUT_BOUND_MISMATCH", "mixed default bounds need gateways or an explicit common override")
        gateways = {next(iter(distinct)): gateway}
    if not dry_run:
        if gateways is None:
            if max_estimated_cost_microusd is None:
                raise RunnerRefusal("PFP_ACCOUNTED_GATEWAY_REQUIRED", "supply accounted gateways or explicit estimated policy")
            if output_dir is None:
                raise RunnerRefusal("OUTPUT_DIR_REQUIRED", "composed accounting requires an explicit new directory")
            if Decimal(max_estimated_cost_microusd) > ceiling * 1_000_000:
                raise RunnerRefusal("LEGACY_BUDGET_CEILING_CONFLICT", "gateway allowance exceeds the legacy ceiling")
        else:
            scopes = []
            try:
                for bound in sorted(distinct):
                    owner = gateways[bound]
                    validate_pilot_gateways({model: owner}, [model], max_tokens=bound)
                    scopes.append(_scope(owner, model, bound))
            except (KeyError, ValueError) as exc:
                raise RunnerRefusal(str(exc), "accounted gateway preflight failed") from exc
            if any(scope != scopes[0] for scope in scopes[1:]):
                raise RunnerRefusal("PFP_SHARED_ACCOUNTING_REQUIRED", "all arms must share one continuing allowance")
            if scopes[0][3] > max_provider_calls:
                raise RunnerRefusal("PFP_CALL_ALLOWANCE_CONFLICT", "gateway exceeds requested call cap")
            if Decimal(scopes[0][2]) > ceiling * 1_000_000:
                raise RunnerRefusal("LEGACY_BUDGET_CEILING_CONFLICT", "gateway allowance exceeds the legacy ceiling")
            if max_estimated_cost_microusd is not None and scopes[0][2] > max_estimated_cost_microusd:
                raise RunnerRefusal("PFP_COST_ALLOWANCE_CONFLICT", "gateway exceeds requested cost cap")
    out = prepare_output_dir(Path(output_dir)) if output_dir is not None else None
    if not dry_run and gateways is None:
        try:
            gateways = {bound: make_pilot_gateways([model], max_output_tokens=bound,
                max_estimated_cost_microusd=max_estimated_cost_microusd, max_calls=max_provider_calls,
                accounting_path=out / "accounting.sqlite3", env_file=env_file)[model] for bound in sorted(distinct)}
        except ValueError as exc:
            raise RunnerRefusal(str(exc), "gateway composition failed") from exc
    budget = BudgetController(ceiling_usd=budget_limit_usd, hard_kill_usd=budget_limit_usd)
    records = {arm: [] for arm, *_ in first_specs}
    start, run_id, stop, attempted = time.monotonic(), uuid4().hex, None, []
    for index, case in enumerate(selected):
        attempted.append(case["case_id"])
        for arm, name, schema, prompt, original, canary_expected in specs(case):
            bound = bounds[arm]
            exchange = _complete_case(case, None if dry_run else gateways[bound], model, budget,
                prompt=prompt, decoding=DecodingParamsV1(temperature=0.0,
                    response_format={"type": "json_schema", "json_schema": schema}),
                task_id=f"C005:{run_id}", attempt_id=f"{run_id}:case-{index}:{arm}",
                max_tokens=bound, dry_run=dry_run, mock_solution=_host_fixture(case, arm, canary_expected))
            content = exchange.get("observed_content", "")
            try:
                payload = json.loads(content)
                parseable = True
            except (ValueError, TypeError):
                payload, parseable = {}, False
            valid = parseable and Draft202012Validator(schema["schema"]).is_valid(payload)
            eligible = exchange["ok"] and valid
            correct, canary_detected, error = False, False, exchange["error"]
            if eligible:
                check = checker(case["edges"], payload.get("verdict", ""), payload.get("certificate"))
                correct = check.is_valid and payload.get("verdict") == case["expected_verdict"]
                error = check.error_message
                if canary_expected is not None:
                    actual = payload.get("canary_check", {}).get("canary_actual_residual")
                    canary_detected = actual is not None and str(actual) == str(canary_expected)
                    correct = correct and canary_detected
                    error = error if not check.is_valid else "Canary failed" if not canary_detected else None
            elif exchange["ok"]:
                error = "SCHEMA_ERROR" if parseable else "PARSE_ERROR"
            completed = dry_run or (not exchange["stop"] and exchange.get("attempt_state") in {"CompletedSettled", "CompletedPendingSettlement"})
            row = dict(case_id=case["case_id"], correct=correct,
                verdict=payload.get("verdict") if isinstance(payload, dict) else None,
                expected=case["expected_verdict"], cost=exchange["cost"], duration=exchange["elapsed"],
                error=error, parseable=parseable, schema_valid=valid, completed=completed,
                judge_eligible=eligible, exchange=exchange, max_output_tokens=bound,
                original_max_output_tokens=original, prompt=prompt, proposal=payload)
            if canary_expected is not None:
                row["canary_detected"] = canary_detected
            records[arm].append(row)
            if exchange["stop"]:
                stop = exchange["error"] or "PFP_TERMINAL_STOP"
                break
        if stop:
            break
    summaries = {summary_keys[arm]: _summarize(records[arm], name, canary=arm == "arm4") for arm, name, *_ in first_specs}
    costs = [row["cost"] for values in records.values() for row in values]
    known = sum(cost for cost in costs if cost is not None)
    total = None if any(cost is None for cost in costs) else known
    complete_ids = set.intersection(*({row["case_id"] for row in values if row["completed"]} for values in records.values()))
    report = dict(benchmark_name=benchmark_name, timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        model=model, sample_size=len(attempted), planned_cases=len(selected), completed_cases=len(complete_ids),
        incomplete_case_ids=[key for key in attempted if key not in complete_ids],
        unattempted_case_ids=[case["case_id"] for case in selected if case["case_id"] not in attempted],
        total_billed_spend_usd=total, known_cost_subtotal_usd=known, budget_limit_usd=budget_limit_usd,
        execution_duration_sec=time.monotonic() - start, summary=summaries,
        statistical_tests={key: _paired(records[a], records[b], compute) for key, a, b in comparisons},
        case_details={arm + "_records": values for arm, values in records.items()},
        stop_reason=stop, actual_concurrency=1, max_output_tokens_by_arm=bounds,
        output_token_override=max_tokens, original_max_output_tokens_by_arm={arm: original for arm, _, _, _, original, _ in first_specs},
        evidence_grade="HOST_REFERENCE_SELF_CONSISTENCY" if dry_run else "PFP_BOUND_PROPOSAL",
        controls_honored=None, **not_adjudicated_fields(),
        claim_hygiene=dict(supports="Finite original certificate/canary checks on the recorded attempted arms.",
            does_not_support="Dry fixtures do not establish model performance. Payloads and PFP/schema success do not prove provider-honored controls, intermediate scratchpad reasoning or causal superiority.",
            narrowest_defensible_claim="Host schema/certificate self-consistency only." if dry_run else "Recorded bound/accounted model proposals with separate host checks; incomplete arms remain explicit.",
            next_test_needed="Explicit control-honoring probes and a predeclared paired empirical design."))
    if out is not None:
        summary = dict(
            benchmark_name=report["benchmark_name"], budget_limit_usd=budget_limit_usd,
            claim_discipline=report["claim_hygiene"], model=model,
            sample_size=report["sample_size"], statistical_significance=report["statistical_tests"],
            summary=summaries, total_spend_usd=total, known_cost_subtotal_usd=known,
            evidence_grade=report["evidence_grade"], stop_reason=stop,
            completed_cases=report["completed_cases"], planned_cases=len(selected),
            max_output_tokens_by_arm=bounds, output_token_override=max_tokens,
            **not_adjudicated_fields(),
        )
        for name, value in (("master_evaluation_report.json", report), ("summary.json", summary)):
            (out / name).write_text(json.dumps(value, sort_keys=True, indent=2), encoding="utf-8", newline="\n")
    return report


def run_3arm_benchmark(*, model="nousresearch/hermes-3-llama-3.1-405b", gateway=None,
    gateways=None, output_dir=None, max_cases=5, max_provider_calls=15, max_tokens=None,
    max_estimated_cost_microusd=None, env_file=None, dry_run=False, budget_limit_usd=2.00,
    cases=None) -> dict[str, Any]:
    return _run_benchmark(model=model, gateway=gateway, gateways=gateways, output_dir=output_dir,
        max_cases=max_cases, max_provider_calls=max_provider_calls, max_tokens=max_tokens,
        max_estimated_cost_microusd=max_estimated_cost_microusd, env_file=env_file,
        dry_run=dry_run, budget_limit_usd=budget_limit_usd, cases=cases, specs=_arm_specs,
        checker=verify_consistency_certificate, compute=compute_mcnemar,
        benchmark_name="3-Arm Decoding Controls & Prompt Factorization Bakeoff",
        summary_keys={"arm1": "arm_1_direct_schema", "arm2": "arm_2_numeric_scratchpad", "arm3": "arm_3_factorized_hieroglyphics"},
        comparisons=(("arm1_vs_arm2_mcnemar", "arm1", "arm2"), ("arm1_vs_arm3_mcnemar", "arm1", "arm3"), ("arm2_vs_arm3_mcnemar", "arm2", "arm3")))


def _main(run, argv=None, *, max_calls=15):
    parser = argparse.ArgumentParser(description="Bounded serial C005 benchmark; dry mode is a host fixture.")
    parser.add_argument("--model", default="nousresearch/hermes-3-llama-3.1-405b")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--max-cases", type=int, default=5)
    parser.add_argument("--max-provider-calls", type=int, default=max_calls)
    parser.add_argument("--max-output-tokens", dest="max_tokens", type=int)
    parser.add_argument("--max-estimated-cost-microusd", type=int)
    parser.add_argument("--budget-limit-usd", type=float, default=2.00)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    try:
        result = run(**vars(parser.parse_args(argv)))
    except RunnerRefusal as exc:
        print(f"REFUSED {exc}")
        return 2
    print(json.dumps(result, indent=2))
    return 2 if result["stop_reason"] else 0


def main(argv=None):
    return _main(run_3arm_benchmark, argv)


if __name__ == "__main__":
    raise SystemExit(main())
