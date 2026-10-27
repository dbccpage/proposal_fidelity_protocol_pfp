"""Compact Coloured Operad + `P*` Prompt Compiler for the Finite-QM Derivation PFP System.

Applies Operational Laws 1 & 2:
- 1-line `system_prompt` (`AuthorityEffect: None`, `SPK-001`)
- Compact 3-Layer Coloured Operad (`COPP-v2-COMPACT`) + `P*` syndrome payload in `user_prompt`
- Strict top-level JSON schema (`additionalProperties: false`, zero float fields)

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from pfp.tests.demo_004.a_mechanism.derivation_dag_pfp_staged_benchmark import (
    CarrierDerivationProjection,
    derivation_candidate_json_schema,
)
from pfp.tests.demo_004.finite_qm_derivation_pfp.operad_mining.miner import (
    MinedDerivationWorkUnit,
)


@dataclass(frozen=True)
class CompiledFiniteQmPrompt:
    """Compiled compact PFP prompt bundle ready for live API or manual clipboard dispatch."""

    work_id: str
    mode: str
    system_prompt: str
    user_prompt: str
    response_schema: dict[str, Any]
    expected_ground_truth: dict[str, Any]
    prompt_sha256: str


def dag_work_unit_json_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "work_id",
            "authority_effect",
            "operad_id",
            "stage",
            "node_id",
            "route_id",
            "status",
            "tree_potentials",
            "chord_potentials",
            "cochain_d1_d0_zero",
            "phi1_exact_int",
            "gamma2_exact_int",
            "witness_invariant_int",
            "lean_symbol",
            "rust_symbol",
        ],
        "properties": {
            "work_id": {"type": "string"},
            "authority_effect": {"type": "string", "enum": ["None"]},
            "operad_id": {"type": "string"},
            "stage": {"type": "string"},
            "node_id": {"type": "string"},
            "route_id": {"type": "string"},
            "status": {"type": "string"},
            "tree_potentials": {"type": "array", "items": {"type": "integer"}},
            "chord_potentials": {"type": "array", "items": {"type": "integer"}},
            "cochain_d1_d0_zero": {"type": "boolean"},
            "phi1_exact_int": {"type": "integer"},
            "gamma2_exact_int": {"type": "integer"},
            "witness_invariant_int": {"type": "integer"},
            "lean_symbol": {"type": "string"},
            "rust_symbol": {"type": "string"},
        },
    }


def compile_coupled_slice_prompt(
    proj: CarrierDerivationProjection,
    mode: str = "P_STAR_2TURN_TYPED",
) -> CompiledFiniteQmPrompt:
    """Compile an 8-node coupled Finite-QM slice into the compact 871-token prompt."""
    system_prompt = (
        "You are a precise JSON extraction engine under SPK-001 (AuthorityEffect: None). "
        "Output ONLY a single raw JSON object matching the requested fields with no markdown fences and no prose."
    )
    exp = proj.expected_certificate()
    user_prompt = (
        f"Extract the exact 31-field JSON certificate for slice_id=\"{proj.slice_id}\" (AuthorityEffect=\"None\").\n"
        f"- Stage 1a tree potentials (v_1..v_8): {list(proj.tree_potentials)}\n"
        f"- Stage 1b chord potentials: {list(proj.chord_potentials)}\n"
        f"- Set authority_effect=\"None\", slice_id=\"{proj.slice_id}\", cochain_d1_d0_zero=true, "
        f"covered_nodes={list(exp['covered_nodes'])}, covered_routes={list(exp['covered_routes'])}.\n"
        f"- Node 1: sector_weights={list(proj.sector_weights)}, phi1_sector_sum={proj.phi1_sector_sum} "
        f"(sum of sector_weights), even_cycle_c4_ambiguity_gap=2.\n"
        f"- Node 2: density_trace_scaled={proj.phi1_sector_sum}, "
        f"density_off_diagonal_abs={list(proj.density_off_diagonal_abs)}, "
        f"cauchy_schwarz_Slack_zero=true, purity_tr_rho2_num={proj.purity_tr_rho2_num}, "
        f"purity_tr_rho2_den={proj.purity_tr_rho2_den}.\n"
        f"- Node 3: sign_fiber_plus_plus_intensity={proj.sign_fiber_plus_plus_intensity}, "
        f"sign_fiber_plus_minus_intensity={proj.sign_fiber_plus_minus_intensity}, "
        f"interference_cross_term_abs={proj.interference_cross_term_abs}.\n"
        f"- Node 4: gaussian_u1_re={proj.gaussian_u1_re}, gaussian_u1_im={proj.gaussian_u1_im}, "
        f"gaussian_u2_re={proj.gaussian_u2_re}, gaussian_u2_im={proj.gaussian_u2_im}, "
        f"holonomy_real_cross={proj.holonomy_real_cross}, "
        f"coherent_loop_intensity={proj.coherent_loop_intensity}, "
        f"incoherent_loop_intensity={proj.incoherent_loop_intensity}.\n"
        f"- Node 5 & 6: sorkin_i2_sum={proj.sorkin_i2_sum}, sorkin_i3_quadratic=0, "
        f"sorkin_i3_cubic_rival={proj.sorkin_i3_cubic_rival}, "
        f"gleason_quartic_rival_defect={proj.gleason_quartic_rival_defect}.\n"
        f"- Node 7: k23_primal_l1_norm={proj.k23_primal_l1_norm}, "
        f"k23_dual_pairing={proj.k23_dual_pairing}, k23_duality_gap=0.\n"
        f"- Node 8: mermin_peres_row_parities=[1,1,1], mermin_peres_col_parities=[1,1,-1], "
        f"mermin_peres_f2_coboundary_defect=1.\n"
        f"Return ONLY the raw JSON object."
    )
    digest = sha256(f"{system_prompt}\n{user_prompt}".encode("utf-8")).hexdigest()
    return CompiledFiniteQmPrompt(
        work_id=proj.slice_id,
        mode=mode,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_schema=derivation_candidate_json_schema(),
        expected_ground_truth=exp,
        prompt_sha256=digest,
    )


def compile_dag_work_unit_prompt(
    unit: MinedDerivationWorkUnit,
    mode: str = "FAST_1TURN_TYPED",
) -> CompiledFiniteQmPrompt:
    """Compile a single mined DAG work-unit into a compact 1-turn typed prompt."""
    system_prompt = (
        "You are a precise JSON extraction engine under SPK-001 (AuthorityEffect: None). "
        "Output ONLY a single raw JSON object matching the requested schema with no markdown fences and no prose."
    )
    exp = unit.to_expected_ground_truth()
    user_prompt = (
        f"[COPP-v2-COMPACT DAG WORK-UNIT: {unit.work_id}]\n"
        f"- work_id=\"{unit.work_id}\", authority_effect=\"None\", operad_id=\"{unit.operad_id}\", "
        f"stage=\"{unit.stage}\", node_id=\"{unit.node_id}\", route_id=\"{unit.route_id}\", status=\"{unit.status}\"\n"
        f"- tree_potentials={unit.tree_potentials}, chord_potentials={unit.chord_potentials}, cochain_d1_d0_zero=true\n"
        f"- phi1_exact_int = |{unit.tree_potentials[0]}| + |{unit.tree_potentials[1]}| + |{unit.tree_potentials[2]}| = {unit.phi1_exact_int}\n"
        f"- gamma2_exact_int = |{unit.chord_potentials[0]}| + |{unit.chord_potentials[1]}| = {unit.gamma2_exact_int}\n"
        f"- witness_invariant_int = 3*phi1_exact_int + 2*gamma2_exact_int + {unit.ordinal % 17} = {unit.witness_invariant_int}\n"
        f"- lean_symbol=\"{unit.lean_symbol}\", rust_symbol=\"{unit.rust_symbol}\"\n"
        f"Return ONLY the raw JSON object."
    )
    digest = sha256(f"{system_prompt}\n{user_prompt}".encode("utf-8")).hexdigest()
    return CompiledFiniteQmPrompt(
        work_id=unit.work_id,
        mode=mode,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_schema=dag_work_unit_json_schema(),
        expected_ground_truth={"work_id": unit.work_id, "expected_certificate": exp},
        prompt_sha256=digest,
    )
