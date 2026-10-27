"""Bounded serial C005 benchmark through the existing accounted PFP boundary.

Original arm prompts, schemas, factorizers and exact final checks are retained.
Host dry fixtures establish finite schema/certificate self-consistency only.
Requested structured output and PFP wrapping do not prove provider-honored
controls; intermediate scratchpad values are not validated by the final judge.
Outputs go only to an explicitly selected fresh directory, with no new receipt.
AuthorityEffect: None.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

_worktree_root = next((parent for parent in Path(__file__).resolve().parents
    if (parent / "pfp").is_dir() and (parent / "adversary").is_dir()), None)
if _worktree_root is not None and str(_worktree_root) not in sys.path:
    sys.path.insert(0, str(_worktree_root))

from pilots.llm_mechanism.c005_hosted_decode_controls.cases import get_hidden_base_cases as get_hidden_base_cases
from pilots.llm_mechanism.c005_hosted_decode_controls.checkers import verify_consistency_certificate
from pilots.llm_mechanism.c005_hosted_decode_controls.run_adversary_bakeoff import (
    not_adjudicated_fields as not_adjudicated_fields, persist_benchmark_run as persist_benchmark_run,
)
from pilots.llm_mechanism.c005_hosted_decode_controls.benchmark_3arm_scratchpad import (
    _numeric_prompt, _run_benchmark, _main,
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


def _arm_specs(case):
    edges = case["edges"]
    rune_prompt, _, chord_edges, potentials = factorize_case_to_hieroglyphics(case)
    if chord_edges:
        canary_u, canary_v, canary_d = chord_edges[0]
    else:
        canary_u, canary_v, canary_d = edges[0]
    true_canary_residual = potentials[canary_v] - potentials[canary_u] - canary_d
    rune_prompt += f"\nCanary Antibody: Verify chord ({canary_u}→{canary_v}:{canary_d:+d}) has residual = pi(v) - pi(u) - d. Report in canary_check."
    return [
        ("arm2", "Arm 2: Numeric-Constrained Topological Scratchpad", ARM2_NUMERIC_SCRATCHPAD_SCHEMA, _numeric_prompt(case), 512, None),
        ("arm4", "Arm 4: Hybrid Schema with Canary", ARM4_HYBRID_SCHEMA, rune_prompt, 512, true_canary_residual),
    ]


def run_hybrid_benchmark(*, model="nousresearch/hermes-3-llama-3.1-405b", gateway=None,
    gateways=None, output_dir=None, max_cases=5, max_provider_calls=10, max_tokens=None,
    max_estimated_cost_microusd=None, env_file=None, dry_run=False, budget_limit_usd=2.00,
    cases=None) -> dict[str, Any]:
    return _run_benchmark(model=model, gateway=gateway, gateways=gateways, output_dir=output_dir,
        max_cases=max_cases, max_provider_calls=max_provider_calls, max_tokens=max_tokens,
        max_estimated_cost_microusd=max_estimated_cost_microusd, env_file=env_file,
        dry_run=dry_run, budget_limit_usd=budget_limit_usd, cases=cases, specs=_arm_specs,
        checker=verify_consistency_certificate, compute=compute_mcnemar,
        benchmark_name="Arm 4 Hybrid Schema with Canary Antibody Benchmark",
        summary_keys={"arm2": "arm_2_numeric_scratchpad", "arm4": "arm_4_hybrid_schema"},
        comparisons=(("arm2_vs_arm4_mcnemar", "arm2", "arm4"),))


def main(argv=None):
    return _main(run_hybrid_benchmark, argv, max_calls=10)


if __name__ == "__main__":
    raise SystemExit(main())
