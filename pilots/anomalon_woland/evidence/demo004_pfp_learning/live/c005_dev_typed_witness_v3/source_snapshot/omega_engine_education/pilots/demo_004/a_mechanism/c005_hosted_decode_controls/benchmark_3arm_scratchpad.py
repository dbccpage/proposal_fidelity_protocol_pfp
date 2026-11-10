"""
benchmark_3arm_scratchpad.py — Empirical 3-Arm Benchmark on 50 Hidden Consistency Cases.

Compares:
- Arm 1: Direct Schema (Verdict First Baseline)
- Arm 2: Numeric-Constrained Topological Scratchpad (Intermediate Potential Propagation First)
- Arm 3: Spanning-Tree Factorized Hieroglyphic Prompt (Dense DDC Runes & Fundamental Cycle Inversion)

Model: nousresearch/hermes-3-llama-3.1-405b
Budget Ceiling: $2.00 (Target < $0.10)
Verification: Exact Host Oracle (verify_consistency_certificate)
Statistics: Paired exact McNemar significance tests across all arm pairs.

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
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls.schemas import (  # noqa: E402
    CONSISTENCY_JSON_SCHEMA,
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


def run_3arm_benchmark() -> dict[str, Any]:
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
    print("3-ARM DECODING CONTROLS BENCHMARK: 50 HIDDEN CONSISTENCY CASES")
    print(f"Model: {model} | Total Queries: {num_cases * 3} | Budget Ceiling: $2.00")
    print("=" * 80)

    import concurrent.futures

    def evaluate_single_case(
        idx: int, case: dict[str, Any]
    ) -> tuple[int, dict[str, Any], dict[str, Any], dict[str, Any]]:
        case_id = case["case_id"]
        expected_verdict = case["expected_verdict"]
        edges = case["edges"]

        # Arm 1: Direct Schema Baseline
        t0 = time.time()
        try:
            BENCHMARK_BUDGET.check_can_call(0.001)
            resp1 = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": case["prompt"]}],
                response_format={"type": "json_schema", "json_schema": CONSISTENCY_JSON_SCHEMA},
                temperature=0.0,
                max_tokens=256,
            )
            cost1 = float(getattr(resp1.usage, "cost", 0.00015) or 0.00015)
            BENCHMARK_BUDGET.record_call(cost1, model, resp1.id)
            c1_str = resp1.choices[0].message.content or ""
            d1 = json.loads(c1_str)
            chk1 = verify_consistency_certificate(
                edges, d1.get("verdict", ""), d1.get("certificate")
            )
            correct1 = chk1.is_valid and (d1.get("verdict") == expected_verdict)
            err1 = chk1.error_message
            parseable1 = True
        except Exception as e:
            cost1 = 0.0
            correct1 = False
            parseable1 = False
            err1 = str(e)
            d1 = {}
        dur1 = round(time.time() - t0, 3)
        r1 = {
            "case_id": case_id,
            "correct": correct1,
            "verdict": d1.get("verdict"),
            "expected": expected_verdict,
            "cost": cost1,
            "duration": dur1,
            "error": err1,
            "parseable": parseable1,
        }

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

        # Arm 3: Factorized Hieroglyphic Prompt
        t0 = time.time()
        rune_prompt, _ = factorize_case_to_hieroglyphics(case)
        try:
            BENCHMARK_BUDGET.check_can_call(0.001)
            resp3 = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": rune_prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": ARM3_FACTORIZED_HIEROGLYPHIC_SCHEMA,
                },
                temperature=0.0,
                max_tokens=512,
            )
            cost3 = float(getattr(resp3.usage, "cost", 0.00025) or 0.00025)
            BENCHMARK_BUDGET.record_call(cost3, model, resp3.id)
            c3_str = resp3.choices[0].message.content or ""
            d3 = json.loads(c3_str)
            chk3 = verify_consistency_certificate(
                edges, d3.get("verdict", ""), d3.get("certificate")
            )
            correct3 = chk3.is_valid and (d3.get("verdict") == expected_verdict)
            err3 = chk3.error_message
            parseable3 = True
        except Exception as e:
            cost3 = 0.0
            correct3 = False
            parseable3 = False
            err3 = str(e)
            d3 = {}
        dur3 = round(time.time() - t0, 3)
        r3 = {
            "case_id": case_id,
            "correct": correct3,
            "verdict": d3.get("verdict"),
            "expected": expected_verdict,
            "cost": cost3,
            "duration": dur3,
            "error": err3,
            "parseable": parseable3,
        }

        return idx, r1, r2, r3

    raw_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {
            executor.submit(evaluate_single_case, idx, case): idx
            for idx, case in enumerate(all_cases, start=1)
        }
        for future in concurrent.futures.as_completed(future_map):
            idx, r1, r2, r3 = future.result()
            raw_results.append((idx, r1, r2, r3))
            completed = len(raw_results)
            if completed % 5 == 0 or completed == num_cases:
                print(
                    f"[{completed:02d}/{num_cases}] Cases Completed | "
                    f"Current Spend: ${BENCHMARK_BUDGET.total_billed_usd:.5f} | "
                    f"Active Workers: 5"
                )

    raw_results.sort(key=lambda x: x[0])
    arm1_records = [x[1] for x in raw_results]
    arm2_records = [x[2] for x in raw_results]
    arm3_records = [x[3] for x in raw_results]

    # Compute aggregate metrics
    def summarize_arm(records: list[dict[str, Any]], name: str) -> dict[str, Any]:
        n = len(records)
        corr = sum(1 for r in records if r["correct"])
        pars = sum(1 for r in records if r["parseable"])
        cost = sum(r["cost"] for r in records)
        dur = sum(r["duration"] for r in records)
        return {
            "arm_name": name,
            "total_cases": n,
            "verified_correct_count": corr,
            "verified_correct_rate": round(corr / n, 4),
            "parseable_rate": round(pars / n, 4),
            "total_spend_usd": round(cost, 5),
            "cost_per_verified_success_usd": round(cost / corr, 5) if corr > 0 else None,
            "average_latency_sec": round(dur / n, 3),
        }

    s1 = summarize_arm(arm1_records, "Arm 1: Direct Schema (Verdict First Baseline)")
    s2 = summarize_arm(arm2_records, "Arm 2: Numeric-Constrained Topological Scratchpad")
    s3 = summarize_arm(arm3_records, "Arm 3: Spanning-Tree Factorized Hieroglyphic Prompt")

    # McNemar Significance Comparisons
    c1_list = [r["correct"] for r in arm1_records]
    c2_list = [r["correct"] for r in arm2_records]
    c3_list = [r["correct"] for r in arm3_records]

    mc_1_vs_2 = compute_mcnemar(c1_list, c2_list)
    mc_1_vs_3 = compute_mcnemar(c1_list, c3_list)
    mc_2_vs_3 = compute_mcnemar(c2_list, c3_list)

    total_benchmark_duration = round(time.time() - start_time, 2)
    total_spend = round(BENCHMARK_BUDGET.total_billed_usd, 5)

    # Build Master Evaluation Report
    master_report = {
        "benchmark_name": "3-Arm Decoding Controls & Prompt Factorization Bakeoff",
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": model,
        "sample_size": num_cases,
        "total_billed_spend_usd": total_spend,
        "budget_limit_usd": 2.00,
        "execution_duration_sec": total_benchmark_duration,
        "summary": {
            "arm_1_direct_schema": s1,
            "arm_2_numeric_scratchpad": s2,
            "arm_3_factorized_hieroglyphics": s3,
        },
        "statistical_tests": {
            "arm1_vs_arm2_mcnemar": mc_1_vs_2,
            "arm1_vs_arm3_mcnemar": mc_1_vs_3,
            "arm2_vs_arm3_mcnemar": mc_2_vs_3,
        },
        **not_adjudicated_fields(),
        "case_details": {
            "arm1_records": arm1_records,
            "arm2_records": arm2_records,
            "arm3_records": arm3_records,
        },
        "claim_hygiene": {
            "supports": (
                f"On {num_cases} hidden consistency cases with {model}, host-verified correct counts were "
                f"Arm 1 {s1['verified_correct_count']}/{num_cases}, Arm 2 {s2['verified_correct_count']}/{num_cases} "
                f"and Arm 3 {s3['verified_correct_count']}/{num_cases}; see the McNemar tests for the paired differences."
            ),
            "does_not_support": (
                "Does not support that connectionist language models achieve general exactness on arbitrary graph "
                "topologies without external host verification or discrete solver delegation."
            ),
            "narrowest_defensible_claim": (
                f"Across {num_cases} hidden consistency cases on {model}, host-verified correctness was "
                f"{s1['verified_correct_rate'] * 100:.1f}% (Arm 1), {s2['verified_correct_rate'] * 100:.1f}% (Arm 2) and "
                f"{s3['verified_correct_rate'] * 100:.1f}% (Arm 3) under a total recorded spend of ${total_spend:.5f}; no verdict is issued."
            ),
            "next_test_needed": (
                "Deploy a production client-side packet transpiler that compiles natural user inputs directly into "
                "Arm 3 factorized hieroglyphic envelopes with embedded antibody canary checks."
            ),
        },
    }

    # Persist report, summary and receipt into a new run folder under the intelligence root
    task_key = "c005_3arm_scratchpad_hieroglyphic_bakeoff"
    dest_dir = persist_benchmark_run(master_report, task_key=task_key)

    print("\n" + "=" * 80)
    print("BENCHMARK EXECUTION COMPLETED")
    print(
        f" - Arm 1 (Direct Schema):        {s1['verified_correct_count']}/{num_cases} ({s1['verified_correct_rate'] * 100:.1f}%) | Cost/Success: ${s1['cost_per_verified_success_usd']}"
    )
    print(
        f" - Arm 2 (Numeric Scratchpad):   {s2['verified_correct_count']}/{num_cases} ({s2['verified_correct_rate'] * 100:.1f}%) | Cost/Success: ${s2['cost_per_verified_success_usd']}"
    )
    print(
        f" - Arm 3 (Factorized Hieroglyph):{s3['verified_correct_count']}/{num_cases} ({s3['verified_correct_rate'] * 100:.1f}%) | Cost/Success: ${s3['cost_per_verified_success_usd']}"
    )
    print(f" - Total Spend: ${total_spend:.5f} (Hard Limit: $2.00)")
    print(f" - Duration: {total_benchmark_duration}s")
    print("=" * 80)
    print(f"Artifacts persisted to:\n - {dest_dir}")

    return master_report


if __name__ == "__main__":
    run_3arm_benchmark()
