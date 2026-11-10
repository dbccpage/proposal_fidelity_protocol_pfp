"""
benchmark_arm4_hybrid.py — Empirical Arm 4 Hybrid Benchmark on 50 Hidden Consistency Cases.

Compares:
- Arm 2: Numeric-Constrained Topological Scratchpad (Baseline)
- Arm 4: Hybrid Schema (DDC Hieroglyphic + Numeric Scratchpad + Canary Antibody)

Model: nousresearch/hermes-3-llama-3.1-405b
Budget Ceiling: $2.00 (Target < $0.20)
Verification: Exact Host Oracle (verify_consistency_certificate)
Statistics: Paired exact McNemar significance tests across arm pairs.

Notice (2026-09-29): this script compares prompt/decoding arms of one hosted model; it
issues no verdict. Its receipt records ``terminal_verdict: null`` with ``verdict_status:
NOT_ADJUDICATED`` (earlier versions wrote a pass label). The Woland swarm is the only final
evaluator. OPENROUTER_API_KEY is read from the environment only (no .env file is loaded),
and every run is written to a new time-stamped folder under the intelligence root; an
existing run folder is never overwritten and no copy is written under the working directory.
"""

from __future__ import annotations

import datetime
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure the repository root is on sys.path (marker search, no parents[N] arithmetic)
for _parent in Path(__file__).resolve().parents:
    if (_parent / "omega_engine_projects").exists() and (
        _parent / "omega_engine_providers"
    ).exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

# OPENROUTER_API_KEY must come from the launching environment; no .env file is read.
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.budget_controller import (  # noqa: E402
    BudgetController,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.cases import (  # noqa: E402
    get_hidden_base_cases,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.checkers import (  # noqa: E402
    verify_consistency_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.run_woland_bakeoff import (  # noqa: E402
    not_adjudicated_fields,
    persist_benchmark_run,
)
from openai import OpenAI  # noqa: E402

# Budget Controller with $2.00 ceiling
BENCHMARK_BUDGET = BudgetController(
    ceiling_usd=2.00,
    target_spend_usd=0.20,
    hard_kill_usd=2.00,
    fail_closed_on_unreported=False,
)

# ------------------------------------------------------------------------------
# Schemas for Arms 2 and 4
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

# Arm 4 Schema: Hybrid Schema
ARM4_HYBRID_SCHEMA: dict[str, Any] = {
    "name": "arm4_hybrid_schema",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "canary_check": {
                "type": "object",
                "properties": {
                    "canary_edge": {"type": "string"},
                    "canary_expected_residual": {"type": "string", "pattern": "^-?[0-9]+$"},
                    "canary_actual_residual": {"type": "string", "pattern": "^-?[0-9]+$"},
                    "canary_passed": {"type": "boolean"},
                },
                "required": [
                    "canary_edge",
                    "canary_expected_residual",
                    "canary_actual_residual",
                    "canary_passed",
                ],
                "additionalProperties": False,
            },
            "scratchpad_potentials": {
                "type": "object",
                "description": "Sequential integer potential propagation",
                "additionalProperties": {
                    "type": "string",
                    "pattern": "^-?[0-9]+$",
                },
            },
            "chord_residuals": {
                "type": "array",
                "description": "Evaluation of each chord edge",
                "items": {
                    "type": "object",
                    "properties": {
                        "chord": {"type": "string"},
                        "pi_diff": {"type": "string", "pattern": "^-?[0-9]+$"},
                        "declared_delta": {"type": "string", "pattern": "^-?[0-9]+$"},
                        "residual": {"type": "string", "pattern": "^-?[0-9]+$"},
                        "zero": {"type": "boolean"},
                    },
                    "required": ["chord", "pi_diff", "declared_delta", "residual", "zero"],
                    "additionalProperties": False,
                },
            },
            "verdict": {"type": "string", "enum": ["CONSISTENT", "INCONSISTENT"]},
            "certificate": {
                "type": "object",
                "description": "Map from node to integer potential string if CONSISTENT, else empty object {}.",
                "additionalProperties": {
                    "type": "string",
                    "pattern": "^-?[0-9]+$",
                },
            },
        },
        "required": [
            "canary_check",
            "scratchpad_potentials",
            "chord_residuals",
            "verdict",
            "certificate",
        ],
        "additionalProperties": False,
    },
}


# ------------------------------------------------------------------------------
# Factorization Helper for Arm 4
# ------------------------------------------------------------------------------


def factorize_case_to_hieroglyphics(
    case: dict[str, Any],
) -> tuple[str, dict[str, str], list[tuple[str, str, int]], dict[str, int]]:
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
    return rune_prompt, cert_str_map, chord_edges, potentials


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


def run_hybrid_benchmark() -> dict[str, Any]:
    start_time = time.time()
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in the environment (no .env file is read)")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    # Load all 50 consistency cases
    all_cases = [c for c in get_hidden_base_cases() if c["kind"] == "consistency"]
    num_cases = len(all_cases)
    model = "nousresearch/hermes-3-llama-3.1-405b"

    print("=" * 80)
    print("ARM 4 HYBRID BENCHMARK: 50 HIDDEN CONSISTENCY CASES")
    print(f"Model: {model} | Total Queries: {num_cases * 2} | Budget Ceiling: $2.00")
    print("=" * 80)

    import concurrent.futures

    def evaluate_single_case(
        idx: int, case: dict[str, Any]
    ) -> tuple[int, dict[str, Any], dict[str, Any]]:
        case_id = case["case_id"]
        expected_verdict = case["expected_verdict"]
        edges = case["edges"]

        # Arm 2: Numeric Scratchpad
        t0 = time.time()
        arm2_prompt = (
            f"{case['prompt']}\n"
            f"Step 1: In scratchpad_tree_potentials, assign integer potentials setting n0='0', then recursively computing "
            f"potential(v) = potential(u) + delta for each tree edge as integer strings.\n"
            f"Step 2: In chord_validations, test whether potential(v) - potential(u) == target_delta for all chords.\n"
            f"Step 3: Conclude CONSISTENT (with full certificate of integer strings) or INCONSISTENT."
        )
        try:
            BENCHMARK_BUDGET.check_can_call(0.001)
            resp2 = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": arm2_prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": ARM2_NUMERIC_SCRATCHPAD_SCHEMA,
                },
                temperature=0.0,
                max_tokens=512,
            )
            cost2 = float(getattr(resp2.usage, "cost", 0.00025) or 0.00025)
            BENCHMARK_BUDGET.record_call(cost2, model, resp2.id)
            c2_str = resp2.choices[0].message.content or ""
            d2 = json.loads(c2_str)
            chk2 = verify_consistency_certificate(
                edges, d2.get("verdict", ""), d2.get("certificate")
            )
            correct2 = chk2.is_valid and (d2.get("verdict") == expected_verdict)
            err2 = chk2.error_message
            parseable2 = True
        except Exception as e:
            cost2 = 0.0
            correct2 = False
            parseable2 = False
            err2 = str(e)
            d2 = {}
        dur2 = round(time.time() - t0, 3)
        r2 = {
            "case_id": case_id,
            "correct": correct2,
            "verdict": d2.get("verdict"),
            "expected": expected_verdict,
            "cost": cost2,
            "duration": dur2,
            "error": err2,
            "parseable": parseable2,
        }

        # Arm 4: Factorized Hieroglyphic Prompt with Canary
        t0 = time.time()
        rune_prompt, _, chord_edges, potentials = factorize_case_to_hieroglyphics(case)

        if chord_edges:
            canary_u, canary_v, canary_d = chord_edges[0]
        else:
            canary_u, canary_v, canary_d = edges[0]  # Fallback

        true_canary_residual = potentials[canary_v] - potentials[canary_u] - canary_d
        rune_prompt += f"\nCanary Antibody: Verify chord ({canary_u}→{canary_v}:{canary_d:+d}) has residual = pi(v) - pi(u) - d. Report in canary_check."

        canary_detected = False
        try:
            BENCHMARK_BUDGET.check_can_call(0.001)
            resp4 = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": rune_prompt}],
                response_format={"type": "json_schema", "json_schema": ARM4_HYBRID_SCHEMA},
                temperature=0.0,
                max_tokens=512,
            )
            cost4 = float(getattr(resp4.usage, "cost", 0.00025) or 0.00025)
            BENCHMARK_BUDGET.record_call(cost4, model, resp4.id)
            c4_str = resp4.choices[0].message.content or ""
            d4 = json.loads(c4_str)

            canary_check = d4.get("canary_check", {})
            actual_res = canary_check.get("canary_actual_residual", None)
            if actual_res is not None and str(actual_res) == str(true_canary_residual):
                canary_detected = True

            chk4 = verify_consistency_certificate(
                edges, d4.get("verdict", ""), d4.get("certificate")
            )

            # Correct only if verify_consistency_certificate passes AND canary matches true residual
            correct4 = chk4.is_valid and (d4.get("verdict") == expected_verdict) and canary_detected
            err4 = (
                chk4.error_message
                if not chk4.is_valid
                else ("Canary failed" if not canary_detected else None)
            )
            parseable4 = True
        except Exception as e:
            cost4 = 0.0
            correct4 = False
            parseable4 = False
            err4 = str(e)
            d4 = {}
        dur4 = round(time.time() - t0, 3)
        r4 = {
            "case_id": case_id,
            "correct": correct4,
            "verdict": d4.get("verdict"),
            "expected": expected_verdict,
            "cost": cost4,
            "duration": dur4,
            "error": err4,
            "parseable": parseable4,
            "canary_detected": canary_detected,
        }

        return idx, r2, r4

    raw_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {
            executor.submit(evaluate_single_case, idx, case): idx
            for idx, case in enumerate(all_cases, start=1)
        }
        for future in concurrent.futures.as_completed(future_map):
            idx, r2, r4 = future.result()
            raw_results.append((idx, r2, r4))
            completed = len(raw_results)
            if completed % 5 == 0 or completed == num_cases:
                print(
                    f"[{completed:02d}/{num_cases}] Cases Completed | "
                    f"Current Spend: ${BENCHMARK_BUDGET.total_billed_usd:.5f} | "
                    f"Active Workers: 5"
                )

    raw_results.sort(key=lambda x: x[0])
    arm2_records = [x[1] for x in raw_results]
    arm4_records = [x[2] for x in raw_results]

    # Compute aggregate metrics
    def summarize_arm(records: list[dict[str, Any]], name: str) -> dict[str, Any]:
        n = len(records)
        corr = sum(1 for r in records if r["correct"])
        pars = sum(1 for r in records if r["parseable"])
        cost = sum(r["cost"] for r in records)
        dur = sum(r["duration"] for r in records)
        res = {
            "arm_name": name,
            "total_cases": n,
            "verified_correct_count": corr,
            "verified_correct_rate": round(corr / n, 4),
            "parseable_rate": round(pars / n, 4),
            "total_spend_usd": round(cost, 5),
            "cost_per_verified_success_usd": round(cost / corr, 5) if corr > 0 else None,
            "average_latency_sec": round(dur / n, 3),
        }
        if "canary_detected" in records[0]:
            canaries = sum(1 for r in records if r.get("canary_detected", False))
            res["canary_detection_rate"] = round(canaries / n, 4)
            res["canaries_detected"] = canaries
        return res

    s2 = summarize_arm(arm2_records, "Arm 2: Numeric-Constrained Topological Scratchpad")
    s4 = summarize_arm(arm4_records, "Arm 4: Hybrid Schema with Canary")

    # McNemar Significance Comparisons
    c2_list = [r["correct"] for r in arm2_records]
    c4_list = [r["correct"] for r in arm4_records]

    mc_2_vs_4 = compute_mcnemar(c2_list, c4_list)

    total_benchmark_duration = round(time.time() - start_time, 2)
    total_spend = round(BENCHMARK_BUDGET.total_billed_usd, 5)

    # Build Master Evaluation Report
    master_report = {
        "benchmark_name": "Arm 4 Hybrid Schema with Canary Antibody Benchmark",
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": model,
        "sample_size": num_cases,
        "total_billed_spend_usd": total_spend,
        "budget_limit_usd": 2.00,
        "execution_duration_sec": total_benchmark_duration,
        "summary": {
            "arm_2_numeric_scratchpad": s2,
            "arm_4_hybrid_schema": s4,
        },
        "statistical_tests": {
            "arm2_vs_arm4_mcnemar": mc_2_vs_4,
        },
        **not_adjudicated_fields(),
        "case_details": {
            "arm2_records": arm2_records,
            "arm4_records": arm4_records,
        },
        "claim_hygiene": {
            "supports": ("Supports comparing Arm 4 (hybrid with canary) against Arm 2."),
            "does_not_support": (
                "Does not support claims outside of the tested case distribution."
            ),
            "narrowest_defensible_claim": (
                f"Across {num_cases} hidden consistency cases on {model}, Arm 4 was host-verified correct on "
                f"{s4['verified_correct_count']}/{num_cases} and Arm 2 on {s2['verified_correct_count']}/{num_cases} "
                f"under a total recorded spend of ${total_spend:.5f}; no verdict is issued."
            ),
            "next_test_needed": ("Further scaling or testing against adversarial prompts."),
        },
    }

    # Persist report, summary and receipt into a new run folder under the intelligence root
    task_key = "c005_arm4_hybrid_hieroglyphic_scratchpad_canary"
    dest_dir = persist_benchmark_run(master_report, task_key=task_key)

    print("\n" + "=" * 80)
    print("BENCHMARK EXECUTION COMPLETED")
    print(
        f" - Arm 2 (Numeric Scratchpad):   {s2['verified_correct_count']}/{num_cases} ({s2['verified_correct_rate'] * 100:.1f}%) | Cost/Success: ${s2.get('cost_per_verified_success_usd', 'N/A')}"
    )
    print(
        f" - Arm 4 (Hybrid Schema):        {s4['verified_correct_count']}/{num_cases} ({s4['verified_correct_rate'] * 100:.1f}%) | Cost/Success: ${s4.get('cost_per_verified_success_usd', 'N/A')}"
    )
    print(
        f" - Canary Antibody Detection:    {s4['canaries_detected']}/{num_cases} ({s4['canary_detection_rate'] * 100:.1f}%)"
    )
    print(f" - Total Spend: ${total_spend:.5f} (Hard Limit: $2.00)")
    print(f" - Duration: {total_benchmark_duration}s")
    print("=" * 80)
    print(f"Artifacts persisted to:\n - {dest_dir}")

    return master_report


if __name__ == "__main__":
    run_hybrid_benchmark()
