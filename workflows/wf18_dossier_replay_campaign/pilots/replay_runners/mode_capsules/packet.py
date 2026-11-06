"""Sealed packet records for the local mode trials.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from importlib.resources import files
import json
from pathlib import Path

import yaml

from .._paths import pilots_root


PILOTS = pilots_root(Path(__file__))
MODES = files("pfp").joinpath("infrastructure", "yaml", "modes")
MODE_DIRS = {
    1: "mode_01_hieroglyphics_and_glyph_alphabets",
    2: "mode_02_packets_and_sealed_envelopes",
    3: "mode_03_attention_head_and_logit_steering",
    4: "mode_04_epistemic_antibody_injections",
    5: "mode_05_skill_injection_and_operad_morphisms",
    6: "mode_06_cot_scratchpad_boundary_probes",
    7: "mode_07_sn_permutation_and_braid_equivariance",
    8: "mode_08_discrete_cochain_involutions",
    9: "mode_09_lean4_proof_kernel_elaboration",
    10: "mode_10_cemetery_dag_mining",
    11: "mode_11_adversarial_tribunal",
    12: "mode_12_simplicial_triangulation_and_regge",
    13: "mode_13_normal_form_confluent_chase",
    14: "mode_14_fail_closed_typed_refusal",
    15: "mode_15_interactive_tui_repl_board",
    16: "mode_16_4e_cognitive_autopoiesis",
    17: "mode_17_polygraph_confluence_consensus",
    18: "mode_18_mub6_moduli_variety",
    19: "mode_19_genesis_first_cut_arb",
    20: "mode_20_multi_agent_debate_oversight",
}
GLYPHS = ("E", "R", "C", "I", "Λ", "D", "M", "T")


class Literal(str):
    """YAML block scalar marker."""


def _represent_literal(dumper: yaml.SafeDumper, data: Literal):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: object) -> bool:
        return True


NoAliasDumper.add_representer(Literal, _represent_literal)


def digest(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def seal(problem: dict, candidate: dict, contract: dict, status: str) -> dict:
    return {
        "schema": "pfp.sealed-packet.v1",
        "authority_effect": "None",
        "problem": problem,
        "candidate": candidate,
        "contract": contract,
        "receipt": {
            "problem_digest": digest(problem),
            "candidate_digest": digest(candidate),
            "contract_digest": digest(contract),
            "verification_status": status,
        },
    }


def digests_match(packet: dict) -> bool:
    receipt = packet["receipt"]
    return (
        receipt["problem_digest"] == digest(packet["problem"])
        and receipt["candidate_digest"] == digest(packet["candidate"])
        and receipt["contract_digest"] == digest(packet["contract"])
    )


def variation(
    variation_id: str,
    role: str,
    status: str,
    observation: str,
    *,
    claim_held: bool,
    failure_mode: str | None = None,
    evidence: dict | None = None,
) -> dict:
    return {
        "variation_id": variation_id,
        "role": role,
        "status": status,
        "claim_held": claim_held,
        "failure_mode": failure_mode,
        "observation": observation,
        "evidence": evidence or {},
    }


def _pilot_id(index: int) -> str:
    return f"pilot_{index:07d}"


def _contract_path(mode_id: int) -> str:
    return f"pfp/infrastructure/yaml/modes/{MODE_DIRS[mode_id]}/contract.yaml"


def _finished(
    index: int,
    mode_id: int,
    coordinate: str,
    *,
    overwrite_mode: bool,
    family: str,
    rung: int,
    seed_prompt: str,
    answer: object,
    packet: dict,
    variations: list[dict],
    advantages: list[str],
    disadvantages: list[str],
    winning_condition_executed: bool,
    execution_limit: str,
    stage_count: int | None = None,
    antibody_ids: list[str] | None = None,
) -> dict:
    if not digests_match(packet):
        raise RuntimeError(f"{_pilot_id(index)} winning packet digest mismatch")
    return {
        "pilot_index": index,
        "pilot_id": _pilot_id(index),
        "mode_id": mode_id,
        "mode_coordinate": coordinate,
        "overwrite_mode": overwrite_mode,
        "mode_contract": _contract_path(mode_id),
        "task_family": family,
        "difficulty_rung": rung,
        "seed_prompt": seed_prompt,
        "answer": answer,
        "packet": packet,
        "variations": variations,
        "advantages": advantages,
        "disadvantages": disadvantages,
        "winning_condition_executed": winning_condition_executed,
        "execution_limit": execution_limit,
        "stage_count": stage_count,
        "antibody_ids": antibody_ids or [],
        "provider_calls": 0,
        "target_spend_usd": 0.0,
    }
