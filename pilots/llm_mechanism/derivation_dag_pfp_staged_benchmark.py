"""Bounded paired Finite-QM Derivation DAG + Coloured Operad + `P*` + `pfp-staged.0.3`
benchmark (`DAG-QM-S1`) across 3 multi-node Finite-QM derivation slices (`dag_qm_slice_01`,
`dag_qm_slice_02`, `dag_qm_slice_03`) loaded directly from
`C:\\Users\\a343o\\source\\repos\\theory_of_finite_quantum_mechanics\\dag\\derivation_dag.json`
(with fallback to the in-repo copy), comparing:

1. `unstaged_1shot_derivation_dag`:
   Direct 1-shot JSON derivation certificate generation from the raw derivation problem
   (without `CongruenceIdeal` distractor annihilation, `P*` spanning-tree/chord basis
   materialization, or `pfp-staged.0.3` stage verification).
2. `p_star_2stage_operad_derivation_dag`:
   Two-stage Coloured Operad + `P*` Guarded Basis-to-Extraction pipeline:
   - Step 0: Operad Congruence Ideal projection (`I_distractor -> NullTree`) annihilating
     bracketed `[Note ...]` / `[Decoy-Claim ...]` distractor spans from the raw prompt text
     and extracting the 9-vertex interferometric cochain complex `(V, E, c)` (`|V|=9, |E|=13,
     |T|=8, b_1=5`) and the declared `derivation_dag.json` node/route records.
   - Stage 1 (`P*` Basis Materialization: `1a` spanning-tree potential integration
     `p_T^* = B_T^{-1} c|_T` with path-integrated `B_T^{-1}` diagnostic retry `G_T`, plus
     `1b` depth-1 chord difference materialization `c_hat_m^* = p_T^*(v_m) - p_T^*(u_m)`
     under `G_C`).
   - Stage 2 (Coloured Operad `o_i` Slot-Grafted Extraction): Grafts the verified `P*`
     basis values (`p_T^*`, `r^* = c_hat^* - c|_{E\\T}`, single-edge syndrome decode,
     sector lift `Phi_1, Gamma_2, Xi`, Gaussian holonomy intensity, Sorkin `I_2, I_3`,
     `K_{2,3}` duality, Mermin-Peres `F_2` obstruction, and DAG route statuses) as
     immutable `LeafTextSpan` operands into a 6-colour `ColouredOperadPrompt` with
     `AnnihilatorDecoy` refutations (`O^-`), extracting the verified 8-node derivation
     certificate in a single extraction turn.
3. `operad_p_star_pfp_staged_0_3`:
   Feeds the `P*`-materialized Coloured Operad container into the Fable 5.5 upgraded
   11-stage `pfp-staged.0.3` pipeline (`ExecuteStagePipelineUseCase`):
   - Stage 1 (`admit`, `host`, 0 model calls): admits the seed `declaration` (`declaration_source="seed"`).
   - Stage 2 (`ideation`, `model`, `seat_gauge_breaker`, 1 model call): proposes 5-7 candidates
     (`construction`, `refutation`, `weakening`), with >= 1 refutation/weakening and >= 2
     `check_without_llm: true`.
   - Stage 3 (`audit`, `model`, `seat_defect_hunter`, 1 model call): audits Stage 2 candidates
     and routes the constructive derivation candidate to `"extract"`.
   - Stage 4 (`l2_extraction`, `model`, `seat_gauge_breaker`, 1 model call): extracts the
     complete 8-node derivation certificate into `candidate_schema`.
   - Stage 5 (`evaluation`, `host`, `seat_adversary`, 0 model calls): `DerivationDagHostVerifier.verify`
     independently checks all 8 exact mathematical and DAG-status invariants.
   - Stage 6 (`adversarial`, `model`, `seat_primal_dual`, 1 model call): proposes concrete
     mutated negative-control challenge witnesses (`expected_accept: false`).
   - Stage 7 (`challenge_replay`, `host`, 0 model calls): `DerivationDagHostVerifier.verify_challenges`
     independently replays Stage 6 challenges on the host, verifying `ReplayOutcome.CONTROL`,
     `checked_count >= 1`, and `obstruction_indices == []`.
   - Stage 8 (`selection`, `host`, `seat_manuscript_truth`, 0 model calls): selects the single
     surviving candidate (`disposition="SELECT"`).
   - Stage 9 (`receipt`, `host`, 0 model calls): computes `terminal="VERIFIED"`,
     `remaining_obligations=[]`, `diagnostic_only=False` from host facts only.
   - Stage 10 (`hand_off`, `host`, 0 model calls): emits the hand-off record
     (`terminal="VERIFIED"`, `routing_terminal="CheckPassed"`).
   - Stage 11 (`evidence_plan`, `model`, 0 model calls): automatically skipped by
     `RunPfpPipelineUseCase.dispatch` (`skipped="NOT_DIAGNOSTIC_ONLY"`).
4. `no_model_exact_derivation_dag_baseline`:
   Deterministic `NO_LLM` exact baseline confirming `3/3 = 100.0%` verified certificates
   and `3/3 = 100.0%` `pfp-staged.0.3` `TerminalStatus.VERIFIED` receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import time
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from pfp.domain.carrier_decoding import parse_integer_slots
from pfp.domain.kernel.ports import (
    PfpDemoCatalogPort,
    PfpHostVerifierPort,
    PfpLlmProviderPort,
)
from pfp.domain.kernel.result import TerminalStatus
from pfp.domain.operad import (
    AnnihilatorDecoy,
    ColouredOperadPrompt,
    CongruenceIdeal,
    LeafTextSpan,
    NullTree,
    OperadTreeNode,
    PromptColour,
    PromptOperator,
)
from pfp.domain.prompts.prompts import PromptPacket
from pfp.domain.stages.stages import (
    ChallengeReplay,
    Stage5Response,
    WitnessReplay,
    replay_outcome,
)
from pfp.infrastructure.pilot_matrix import (
    complete_pilot_turn,
    make_pilot_gateways,
)
from pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from pfp.use_cases.execute_stage_pipeline import ExecuteStagePipelineUseCase
from adversary.domain.providers.types import (
    CandidateRequest,
    ChatMessage,
    DecodingParamsV1,
    Provider,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
EXTERNAL_DAG_PATH = Path(
    r"C:\Users\a343o\source\repos\theory_of_finite_quantum_mechanics\dag\derivation_dag.json"
)
IN_REPO_DAG_PATH = (
    REPO_ROOT
    / "atlas"
    / "coda_atlas"
    / "F004_papers"
    / "003_quantum_foundations"
    / "dag_pregenesis_to_finite_qm"
    / "derivation_dag.json"
)
DEFAULT_RECEIPT_PATH = (
    Path(__file__).resolve().parent / "derivation_dag_pfp_staged_receipt.json"
)
DEFAULT_BUDGET_CAP_MICROUSD = 50_000
PROTOCOL_SHA256 = sha256(
    b"core.pfp.derivation_dag_pfp_staged_benchmark.v1"
).hexdigest()

TARGET_DAG_NODE_IDS: tuple[str, ...] = (
    "L1-WDP-WINDOW-PHI1-GAMMA2",
    "DS-QM206-BOUNDARY-SYNTHESIS",
    "L1-RESIDUAL-SECTOR-WEIGHTS-DECLARED",
    "L1-DENSITY-LIFT-SIGNED-SQRT-PUB009",
    "L1-QM020-THM4-HILBERT-LIFT-REDUNDANCY",
    "DS-QM060-SUPERPOSITION-QUOTIENT-FIBER",
    "DS-QM061-L1-CANNOT-COMPUTE-INTERFERENCE",
    "DS-QM063-HOLONOMY-COHERENT-INTENSITY",
    "FQ-SORKIN-READOUT-CLASS-QM208",
    "FQ-TRACE-ZERO-DUALITY-K23",
    "DS-QM120-MERMIN-PERES-F2-OBSTRUCTION",
    "GP-DROP-ONE-CENSUS",
)
TARGET_DAG_ROUTE_IDS: tuple[str, ...] = (
    "L1-R-RESIDUAL-TO-WEIGHTS",
    "L1-R-SIGNED-SQRT-LIFT",
    "FQ-R-SORKIN-EXCLUSION",
    "FQ-R-TRACE-ZERO-DUALITY",
)

_RELATION_LINE_RE = re.compile(
    r"^Relation \(([^,]+),\s*([^)]+)\) declares: r\(\2\) - r\(\1\) = (-?\d+)\.$"
)


@dataclass(frozen=True)
class DerivationDagSliceSpec:
    """One multi-node Finite-QM derivation slice grounded in `derivation_dag.json`."""

    slice_id: str
    title: str
    items: tuple[str, ...]
    root_item: str
    non_root_items: tuple[str, ...]
    edges: tuple[tuple[str, str, int], ...]
    tree_edges: tuple[tuple[str, str, int], ...]
    chord_edges: tuple[tuple[str, str, int], ...]
    perturbed_edge: tuple[str, str]
    perturbed_edge_kind: str  # "tree" or "chord"
    true_repaired_value: int
    perturbation_shift: int
    sector_weights: tuple[int, int, int]
    fiber_amplitudes: tuple[int, int]
    gaussian_path_1: tuple[int, int]
    gaussian_path_2: tuple[int, int]
    sorkin_amplitudes: tuple[int, int, int]
    distractor_lines: tuple[str, ...]
    raw_prompt_text: str


@dataclass(frozen=True)
class CarrierDerivationProjection:
    """Carrier cochain and expected ground-truth certificate extracted after `CongruenceIdeal`."""

    slice_id: str
    items: tuple[str, ...]
    root_item: str
    non_root_items: tuple[str, ...]
    edges: tuple[tuple[str, str, int], ...]
    tree_edges: tuple[tuple[str, str, int], ...]
    chord_edges: tuple[tuple[str, str, int], ...]
    syndrome_matrix_columns: dict[tuple[str, str], tuple[int, ...]]
    dropped_distractor_lines: tuple[str, ...]
    carrier_text: str
    expected_tree_potentials: dict[str, int]
    expected_tree_slots: tuple[int, ...]
    expected_chord_expected_diffs: tuple[int, ...]
    expected_chord_syndromes: tuple[int, ...]
    expected_certificate: dict[str, Any]


def load_derivation_dag_metadata() -> dict[str, Any]:
    """Load `derivation_dag.json` from the external repo (or in-repo mirror) and extract target nodes/routes."""
    dag_path = EXTERNAL_DAG_PATH if EXTERNAL_DAG_PATH.exists() else IN_REPO_DAG_PATH
    raw_bytes = dag_path.read_bytes()
    dag_sha256 = sha256(raw_bytes).hexdigest()
    dag = json.loads(raw_bytes.decode("utf-8"))
    nodes_by_id = {n["id"]: n for n in dag["nodes"]}
    routes_by_id = {r["id"]: r for r in dag["routes"]}
    selected_nodes = {
        nid: {
            "id": nodes_by_id[nid]["id"],
            "stage": nodes_by_id[nid]["stage"],
            "status": nodes_by_id[nid]["status"],
            "statement": nodes_by_id[nid]["statement"],
        }
        for nid in TARGET_DAG_NODE_IDS
        if nid in nodes_by_id
    }
    selected_routes = {
        rid: {
            "id": routes_by_id[rid]["id"],
            "inputs": routes_by_id[rid].get("inputs", []),
            "output": routes_by_id[rid].get("output", ""),
            "status": routes_by_id[rid]["status"],
            "source": routes_by_id[rid].get("source", []),
        }
        for rid in TARGET_DAG_ROUTE_IDS
        if rid in routes_by_id
    }
    return {
        "dag_path": str(dag_path),
        "dag_sha256": dag_sha256,
        "total_nodes": len(dag["nodes"]),
        "total_routes": len(dag["routes"]),
        "selected_nodes": selected_nodes,
        "selected_routes": selected_routes,
    }


def _build_slice_spec(
    *,
    slice_id: str,
    title: str,
    true_potentials: Mapping[str, int],
    chord_pairs: Sequence[tuple[str, str]],
    perturbed_edge: tuple[str, str],
    perturbation_shift: int,
    sector_weights: tuple[int, int, int],
    fiber_amplitudes: tuple[int, int],
    gaussian_path_1: tuple[int, int],
    gaussian_path_2: tuple[int, int],
    sorkin_amplitudes: tuple[int, int, int],
) -> DerivationDagSliceSpec:
    items = ("A", "B", "C", "D", "E", "F", "G", "H", "I")
    root_item = "A"
    non_root_items = items[1:]
    tree_pairs = tuple((items[i], items[i + 1]) for i in range(len(items) - 1))
    all_pairs = tree_pairs + tuple(chord_pairs)
    edges_list: list[tuple[str, str, int]] = []
    true_repaired_value = 0
    for u, v in all_pairs:
        exact_diff = true_potentials[v] - true_potentials[u]
        if (u, v) == perturbed_edge:
            true_repaired_value = exact_diff
            val = exact_diff + perturbation_shift
        else:
            val = exact_diff
        edges_list.append((u, v, val))
    tree_edges = tuple(edges_list[: len(items) - 1])
    chord_edges = tuple(edges_list[len(items) - 1 :])
    perturbed_kind = "tree" if perturbed_edge in tree_pairs else "chord"

    w1, w2, w3 = sector_weights
    a_fib, b_fib = fiber_amplitudes
    z1_re, z1_im = gaussian_path_1
    z2_re, z2_im = gaussian_path_2
    s1, s2, s3 = sorkin_amplitudes

    distractor_lines = (
        f"[Note: unverified shadow telemetry reports r(B) - r(A) = {tree_edges[0][2] + 999} and r(E) - r(D) = {tree_edges[3][2] - 777}; ignore bracketed telemetry notes.]",
        "[Note: decoy heuristic claims route L1-R-RESIDUAL-TO-WEIGHTS has status DERIVED_EXACT because L1 minimizers on C_4 are unique; this is a known false lure.]",
        f"[Note: phase-blind approximation sets interference_fiber_gap = 0 for ({a_fib}, {b_fib}) vs ({a_fib}, -{b_fib}).]",
        f"[Note: uncalibrated quartic Sorkin fit suggests sorkin_quartic_i3_111 = 0 and sorkin_beta_quartic_coeff = 1.]",
        f"[Note: classical relaxation reports mermin_peres_global_sections_count = 64 and contextuality_verdict = CONSISTENT.]",
        f"[Note: uncentered K_{{2,3}} heuristic reports k23_trace_zero_gap_num = 0 and k23_trace_zero_gap_den = 1.]",
        f"[Note: corrupted chord cache suggests repairing edge ('A', 'I') to {chord_edges[0][2] + 555}.]",
        f"[Note: diagonal lift approximation claims purity_gap_rank1_minus_diag = 0 for sector weights ({w1}, {w2}, {w3}).]",
    )

    lines: list[str] = [
        f"FINITE-QM DERIVATION DAG BENCHMARK SLICE: {slice_id} ({title})",
        "Source DAG: theory_of_finite_quantum_mechanics/dag/derivation_dag.json",
        "Items: " + ", ".join(items),
        "Root convention: r(A) = 0.",
        "Carrier Relations (interferometric 1-cochain c on G=(V,E), |V|=9, |E|=13, b_1=5):",
    ]
    # Interleave carrier relation lines with bracketed distractors
    for idx, (u, v, val) in enumerate(edges_list):
        lines.append(f"Relation ({u}, {v}) declares: r({v}) - r({u}) = {val}.")
        if idx < len(distractor_lines):
            lines.append(distractor_lines[idx])

    lines.extend(
        [
            "",
            "COUPLED FINITE-QM DERIVATION OBLIGATIONS (Nodes 1..8):",
            "1. [L1-WDP-WINDOW-PHI1-GAMMA2 & DS-QM206-BOUNDARY-SYNTHESIS] Integrate the spanning-tree vertex potentials "
            "p_T = [r(B), r(C), r(D), r(E), r(F), r(G), r(H), r(I)] along the 8 chain edges (A,B)..(H,I) with r(A)=0; "
            "compute the 5 chord holonomy syndromes r*_m = (p_T(v_m) - p_T(u_m)) - c(u_m, v_m) on the 5 chords; "
            "and identify the unique single-edge coboundary repair (repaired_edge=[u, v], repaired_value=c'_{u,v}) "
            "that restores Phi_1(c') = 0 and d_1(d_0 r) = 0 (d1_d0_zero = true).",
            "2. [L1-RESIDUAL-SECTOR-WEIGHTS-DECLARED & L1-R-RESIDUAL-TO-WEIGHTS] In derivation_dag.json, on even cycle C_4 "
            "with holonomy 2, minimizers r^(1)=(1,1,0,0) and r^(2)=(0,0,1,1) both achieve Phi_1=2 with 2-sector weights "
            "(2,0) != (0,2), while the C_4 cyclic-orbit average assigns (1,1). Report c4_minimizer_sector_gap = 2 - 0 = 2 "
            "and the exact DAG route status of L1-R-RESIDUAL-TO-WEIGHTS ('GAP_NO_DERIVATION', 'DERIVED_EXACT', or 'CONDITIONAL_ON_IMPORT').",
            f"3. [L1-DENSITY-LIFT-SIGNED-SQRT-PUB009 & L1-QM020-THM4-HILBERT-LIFT-REDUNDANCY] For positive sector weight vector "
            f"w = ({w1}, {w2}, {w3}), compute Phi_1(w) = w_1+w_2+w_3, Gamma_2(w) = w_1^2+w_2^2+w_3^2, the reduced rational "
            f"participation ratio Xi(w) = Phi_1(w)^2 / Gamma_2(w) = xi_num / xi_den in lowest terms (gcd(xi_num, xi_den)=1), "
            f"and the unnormalized rank-1 vs diagonal lift purity gap purity_gap_rank1_minus_diag = Phi_1(w)^2 - Gamma_2(w).",
            f"4. [DS-QM060-SUPERPOSITION-QUOTIENT-FIBER & DS-QM061-L1-CANNOT-COMPUTE-INTERFERENCE] For two-branch signed lifts "
            f"c_+ = ({a_fib}, {b_fib}) and c_- = ({a_fib}, -{b_fib}) sharing the same L1 modulus shadow (|{a_fib}|, |{b_fib}|), "
            f"compute coherent intensities I_+ = ({a_fib}+{b_fib})^2, I_- = ({a_fib}-{b_fib})^2, and interference_fiber_gap = I_+ - I_- = 4*{a_fib}*{b_fib}.",
            f"5. [DS-QM063-HOLONOMY-COHERENT-INTENSITY & DS-QM043-OFFDIAG-GLOBAL-WEIGHT-IDENTITY] For two Gaussian-integer path "
            f"amplitudes z_1 = ({z1_re}) + ({z1_im})i and z_2 = ({z2_re}) + ({z2_im})i in Z[i], compute norm_z1_sq = |z_1|^2, "
            f"norm_z2_sq = |z_2|^2, holonomy_cross_term = 2*Re(conj(z_1)*z_2) = 2*(a_1*a_2 + b_1*b_2), and coherent_total_intensity = |z_1 + z_2|^2.",
            f"6. [FQ-SORKIN-READOUT-CLASS-QM208] For three-slit amplitudes (s_1, s_2, s_3) = ({s1}, {s2}, {s3}), compute "
            f"second-order interference sorkin_i2_12 = (s_1+s_2)^2 - s_1^2 - s_2^2 = 2*s_1*s_2, third-order quadratic Sorkin sum "
            f"sorkin_i3_quadratic = (s_1+s_2+s_3)^2 - (s_1+s_2)^2 - (s_1+s_3)^2 - (s_2+s_3)^2 + s_1^2 + s_2^2 + s_3^2, "
            f"quartic three-slit sum at unit amplitudes sorkin_quartic_i3_111 = 3^4 - 3*(2^4) + 3*(1^4), and the resulting "
            f"quartic coefficient sorkin_beta_quartic_coeff in R(c) = alpha|c|^2 + beta|c|^4.",
            "7. [FQ-TRACE-ZERO-DUALITY-K23] On K_{2,3} with alternating cochain c = (1, -1, -1, 1, 1, -1), report the scalar "
            "zero-duality-gap value k23_scalar_primal_dual_val = Phi_1 = <y*, c> = 4, and for operator defects D_k = 3 E_{kk} - I_3 "
            "where trace-zero repair costs 6 and all-Hermitian repair costs 9/2, report the reduced gap 6 - 9/2 = k23_trace_zero_gap_num / k23_trace_zero_gap_den.",
            "8. [DS-QM120-MERMIN-PERES-F2-OBSTRUCTION] On the 3x3 Mermin-Peres parity grid with row targets (0,0,0) and column "
            "targets (0,0,1) over F_2, report mermin_peres_f2_defect = (0+0+0) xor (0+0+1), mermin_peres_global_sections_count "
            "out of 512, mermin_peres_max_satisfiable_contexts out of 6, and contextuality_verdict = 'OBSTRUCTED_LOCAL_GREEN_GLOBAL_RED'.",
        ]
    )

    return DerivationDagSliceSpec(
        slice_id=slice_id,
        title=title,
        items=items,
        root_item=root_item,
        non_root_items=non_root_items,
        edges=tuple(edges_list),
        tree_edges=tree_edges,
        chord_edges=chord_edges,
        perturbed_edge=perturbed_edge,
        perturbed_edge_kind=perturbed_kind,
        true_repaired_value=true_repaired_value,
        perturbation_shift=perturbation_shift,
        sector_weights=sector_weights,
        fiber_amplitudes=fiber_amplitudes,
        gaussian_path_1=gaussian_path_1,
        gaussian_path_2=gaussian_path_2,
        sorkin_amplitudes=sorkin_amplitudes,
        distractor_lines=distractor_lines,
        raw_prompt_text="\n".join(lines),
    )


def build_derivation_dag_slices() -> tuple[DerivationDagSliceSpec, ...]:
    """Construct the 3 deterministic multi-node Finite-QM derivation slices."""
    slice_01 = _build_slice_spec(
        slice_id="dag_qm_slice_01",
        title="Internal Spanning-Tree Perturbation ('D','E') + 8-Node Finite-QM Derivation",
        true_potentials={
            "A": 0,
            "B": 1420,
            "C": -1415,
            "D": 1775,
            "E": 30,
            "F": 2640,
            "G": -840,
            "H": 1085,
            "I": -1225,
        },
        chord_pairs=(("A", "F"), ("B", "G"), ("C", "H"), ("D", "I"), ("E", "I")),
        perturbed_edge=("D", "E"),
        perturbation_shift=-1350,
        sector_weights=(12, 15, 25),
        fiber_amplitudes=(17, 23),
        gaussian_path_1=(7, -24),
        gaussian_path_2=(20, 15),
        sorkin_amplitudes=(7, 11, 13),
    )
    slice_02 = _build_slice_spec(
        slice_id="dag_qm_slice_02",
        title="Chord Perturbation ('B','G') + 8-Node Finite-QM Derivation",
        true_potentials={
            "A": 0,
            "B": -1860,
            "C": 940,
            "D": -2310,
            "E": 1540,
            "F": -780,
            "G": 2490,
            "H": -1120,
            "I": 1970,
        },
        chord_pairs=(("A", "E"), ("B", "G"), ("C", "H"), ("D", "I"), ("F", "I")),
        perturbed_edge=("B", "G"),
        perturbation_shift=1640,
        sector_weights=(8, 19, 27),
        fiber_amplitudes=(19, 31),
        gaussian_path_1=(9, 40),
        gaussian_path_2=(28, -45),
        sorkin_amplitudes=(9, 14, 19),
    )
    slice_03 = _build_slice_spec(
        slice_id="dag_qm_slice_03",
        title="Internal Spanning-Tree Perturbation ('C','D') + 8-Node Finite-QM Derivation",
        true_potentials={
            "A": 0,
            "B": 2150,
            "C": -1080,
            "D": 2460,
            "E": -920,
            "F": 1830,
            "G": -1470,
            "H": 2090,
            "I": -640,
        },
        chord_pairs=(("A", "G"), ("B", "F"), ("C", "I"), ("A", "D"), ("B", "H")),
        perturbed_edge=("C", "D"),
        perturbation_shift=1480,
        sector_weights=(14, 21, 35),
        fiber_amplitudes=(29, 37),
        gaussian_path_1=(12, -35),
        gaussian_path_2=(15, 36),
        sorkin_amplitudes=(11, 17, 23),
    )
    return (slice_01, slice_02, slice_03)


def _tree_path_edges(
    items: Sequence[str], u: str, v: str
) -> list[tuple[tuple[str, str], int]]:
    idx_u = items.index(u)
    idx_v = items.index(v)
    if idx_u <= idx_v:
        return [((items[k], items[k + 1]), 1) for k in range(idx_u, idx_v)]
    return [((items[k], items[k + 1]), -1) for k in range(idx_v, idx_u)]


def project_carrier_from_raw_prompt(
    spec: DerivationDagSliceSpec,
) -> CarrierDerivationProjection:
    """Apply Operad Congruence Ideal (`I_distractor -> NullTree`) to `spec.raw_prompt_text`."""
    raw_lines = spec.raw_prompt_text.splitlines()
    kept_lines: list[str] = []
    dropped_lines: list[str] = []
    edges: list[tuple[str, str, int]] = []

    for line in raw_lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            dropped_lines.append(stripped)
            continue
        kept_lines.append(line)
        m_rel = _RELATION_LINE_RE.match(stripped)
        if m_rel:
            u, v, val_s = m_rel.group(1).strip(), m_rel.group(2).strip(), int(m_rel.group(3))
            edges.append((u, v, val_s))

    items = spec.items
    root_item = spec.root_item
    non_root_items = spec.non_root_items
    n_tree = len(items) - 1
    tree_edges = tuple(edges[:n_tree])
    chord_edges = tuple(edges[n_tree:])

    expected_tree_potentials: dict[str, int] = {root_item: 0}
    for u, v, val in tree_edges:
        expected_tree_potentials[v] = expected_tree_potentials[u] + val

    expected_tree_slots = tuple(expected_tree_potentials[item] for item in non_root_items)
    expected_chord_expected_diffs = tuple(
        expected_tree_potentials[v] - expected_tree_potentials[u]
        for u, v, _ in chord_edges
    )
    expected_chord_syndromes = tuple(
        expected_chord_expected_diffs[m] - chord_edges[m][2]
        for m in range(len(chord_edges))
    )

    syndrome_matrix_columns: dict[tuple[str, str], tuple[int, ...]] = {}
    chord_tree_paths = [
        dict(_tree_path_edges(items, u_m, v_m)) for u_m, v_m, _ in chord_edges
    ]
    for u, v, _ in tree_edges:
        col = tuple(chord_tree_paths[m].get((u, v), 0) for m in range(len(chord_edges)))
        syndrome_matrix_columns[(u, v)] = col
    for m_idx, (u_m, v_m, _) in enumerate(chord_edges):
        col = tuple(-1 if m == m_idx else 0 for m in range(len(chord_edges)))
        syndrome_matrix_columns[(u_m, v_m)] = col

    # Decode unique single-edge repair from syndrome vector r^* = delta * S_{., e}
    decoded_edge: list[str] = []
    decoded_value: int = 0
    for u, v, val in edges:
        col = syndrome_matrix_columns[(u, v)]
        nz = [m for m, c_m in enumerate(col) if c_m != 0]
        if not nz:
            continue
        m0 = nz[0]
        if expected_chord_syndromes[m0] == 0:
            continue
        delta = expected_chord_syndromes[m0] * col[m0]
        if all(expected_chord_syndromes[m] == delta * col[m] for m in range(len(chord_edges))):
            decoded_edge = [u, v]
            decoded_value = val - delta
            break

    w1, w2, w3 = spec.sector_weights
    phi1_w = w1 + w2 + w3
    gamma2_w = w1 * w1 + w2 * w2 + w3 * w3
    xi_num_raw = phi1_w * phi1_w
    xi_den_raw = gamma2_w
    g_xi = math.gcd(xi_num_raw, xi_den_raw)
    xi_num = xi_num_raw // g_xi
    xi_den = xi_den_raw // g_xi
    purity_gap = phi1_w * phi1_w - gamma2_w

    a_fib, b_fib = spec.fiber_amplitudes
    i_plus = (a_fib + b_fib) ** 2
    i_minus = (a_fib - b_fib) ** 2
    interference_fiber_gap = i_plus - i_minus

    z1_re, z1_im = spec.gaussian_path_1
    z2_re, z2_im = spec.gaussian_path_2
    norm_z1_sq = z1_re * z1_re + z1_im * z1_im
    norm_z2_sq = z2_re * z2_re + z2_im * z2_im
    holonomy_cross_term = 2 * (z1_re * z2_re + z1_im * z2_im)
    coherent_total_intensity = (z1_re + z2_re) ** 2 + (z1_im + z2_im) ** 2

    s1, s2, s3 = spec.sorkin_amplitudes
    sorkin_i2_12 = (s1 + s2) ** 2 - s1 * s1 - s2 * s2
    sorkin_i3_quadratic = (
        (s1 + s2 + s3) ** 2
        - (s1 + s2) ** 2
        - (s1 + s3) ** 2
        - (s2 + s3) ** 2
        + s1 * s1
        + s2 * s2
        + s3 * s3
    )
    sorkin_quartic_i3_111 = (3**4) - 3 * (2**4) + 3 * (1**4)

    expected_certificate = {
        "slice_id": spec.slice_id,
        "tree_potentials": list(expected_tree_slots),
        "chord_syndromes": list(expected_chord_syndromes),
        "repaired_edge": decoded_edge,
        "repaired_value": decoded_value,
        "d1_d0_zero": True,
        "c4_minimizer_sector_gap": 2,
        "route_l1_r_residual_to_weights_status": "GAP_NO_DERIVATION",
        "sector_phi1": phi1_w,
        "sector_gamma2": gamma2_w,
        "sector_xi_num": xi_num,
        "sector_xi_den": xi_den,
        "purity_gap_rank1_minus_diag": purity_gap,
        "interference_i_plus": i_plus,
        "interference_i_minus": i_minus,
        "interference_fiber_gap": interference_fiber_gap,
        "norm_z1_sq": norm_z1_sq,
        "norm_z2_sq": norm_z2_sq,
        "holonomy_cross_term": holonomy_cross_term,
        "coherent_total_intensity": coherent_total_intensity,
        "sorkin_i2_12": sorkin_i2_12,
        "sorkin_i3_quadratic": sorkin_i3_quadratic,
        "sorkin_quartic_i3_111": sorkin_quartic_i3_111,
        "sorkin_beta_quartic_coeff": 0,
        "k23_scalar_primal_dual_val": 4,
        "k23_trace_zero_gap_num": 3,
        "k23_trace_zero_gap_den": 2,
        "mermin_peres_f2_defect": 1,
        "mermin_peres_global_sections_count": 0,
        "mermin_peres_max_satisfiable_contexts": 5,
        "contextuality_verdict": "OBSTRUCTED_LOCAL_GREEN_GLOBAL_RED",
    }

    return CarrierDerivationProjection(
        slice_id=spec.slice_id,
        items=items,
        root_item=root_item,
        non_root_items=non_root_items,
        edges=tuple(edges),
        tree_edges=tree_edges,
        chord_edges=chord_edges,
        syndrome_matrix_columns=syndrome_matrix_columns,
        dropped_distractor_lines=tuple(dropped_lines),
        carrier_text="\n".join(kept_lines),
        expected_tree_potentials=expected_tree_potentials,
        expected_tree_slots=expected_tree_slots,
        expected_chord_expected_diffs=expected_chord_expected_diffs,
        expected_chord_syndromes=expected_chord_syndromes,
        expected_certificate=expected_certificate,
    )


def derivation_candidate_json_schema() -> dict[str, Any]:
    """Host-declared `candidate_schema` for Stage 4 L2 extraction and Stage 6 adversarial witnesses."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "slice_id": {"type": "string"},
            "tree_potentials": {
                "type": "array",
                "items": {"type": "integer"},
                "minItems": 8,
                "maxItems": 8,
            },
            "chord_syndromes": {
                "type": "array",
                "items": {"type": "integer"},
                "minItems": 5,
                "maxItems": 5,
            },
            "repaired_edge": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "maxItems": 2,
            },
            "repaired_value": {"type": "integer"},
            "d1_d0_zero": {"type": "boolean"},
            "c4_minimizer_sector_gap": {"type": "integer"},
            "route_l1_r_residual_to_weights_status": {
                "type": "string",
                "enum": [
                    "GAP_NO_DERIVATION",
                    "DERIVED_EXACT",
                    "CONDITIONAL_ON_IMPORT",
                ],
            },
            "sector_phi1": {"type": "integer"},
            "sector_gamma2": {"type": "integer"},
            "sector_xi_num": {"type": "integer"},
            "sector_xi_den": {"type": "integer"},
            "purity_gap_rank1_minus_diag": {"type": "integer"},
            "interference_i_plus": {"type": "integer"},
            "interference_i_minus": {"type": "integer"},
            "interference_fiber_gap": {"type": "integer"},
            "norm_z1_sq": {"type": "integer"},
            "norm_z2_sq": {"type": "integer"},
            "holonomy_cross_term": {"type": "integer"},
            "coherent_total_intensity": {"type": "integer"},
            "sorkin_i2_12": {"type": "integer"},
            "sorkin_i3_quadratic": {"type": "integer"},
            "sorkin_quartic_i3_111": {"type": "integer"},
            "sorkin_beta_quartic_coeff": {"type": "integer"},
            "k23_scalar_primal_dual_val": {"type": "integer"},
            "k23_trace_zero_gap_num": {"type": "integer"},
            "k23_trace_zero_gap_den": {"type": "integer"},
            "mermin_peres_f2_defect": {"type": "integer"},
            "mermin_peres_global_sections_count": {"type": "integer"},
            "mermin_peres_max_satisfiable_contexts": {"type": "integer"},
            "contextuality_verdict": {"type": "string"},
        },
        "required": [
            "slice_id",
            "tree_potentials",
            "chord_syndromes",
            "repaired_edge",
            "repaired_value",
            "d1_d0_zero",
            "c4_minimizer_sector_gap",
            "route_l1_r_residual_to_weights_status",
            "sector_phi1",
            "sector_gamma2",
            "sector_xi_num",
            "sector_xi_den",
            "purity_gap_rank1_minus_diag",
            "interference_i_plus",
            "interference_i_minus",
            "interference_fiber_gap",
            "norm_z1_sq",
            "norm_z2_sq",
            "holonomy_cross_term",
            "coherent_total_intensity",
            "sorkin_i2_12",
            "sorkin_i3_quadratic",
            "sorkin_quartic_i3_111",
            "sorkin_beta_quartic_coeff",
            "k23_scalar_primal_dual_val",
            "k23_trace_zero_gap_num",
            "k23_trace_zero_gap_den",
            "mermin_peres_f2_defect",
            "mermin_peres_global_sections_count",
            "mermin_peres_max_satisfiable_contexts",
            "contextuality_verdict",
        ],
    }


def verify_derivation_candidate(
    proj: CarrierDerivationProjection, candidate: Any
) -> tuple[bool, tuple[str, ...], dict[str, bool]]:
    """Independent deterministic host checker over all 8 coupled Finite-QM derivation nodes."""
    if not isinstance(candidate, Mapping):
        return False, ("NOT_A_MAPPING",), {}
    exp = proj.expected_certificate
    node_checks: dict[str, bool] = {
        "node1_cochain_tree_chord_repair": (
            candidate.get("tree_potentials") == exp["tree_potentials"]
            and candidate.get("chord_syndromes") == exp["chord_syndromes"]
            and candidate.get("repaired_edge") == exp["repaired_edge"]
            and candidate.get("repaired_value") == exp["repaired_value"]
            and candidate.get("d1_d0_zero") is True
        ),
        "node2_sector_weight_route_gap": (
            candidate.get("c4_minimizer_sector_gap") == exp["c4_minimizer_sector_gap"]
            and candidate.get("route_l1_r_residual_to_weights_status")
            == exp["route_l1_r_residual_to_weights_status"]
        ),
        "node3_density_lift_phi1_gamma2_xi_purity": (
            candidate.get("sector_phi1") == exp["sector_phi1"]
            and candidate.get("sector_gamma2") == exp["sector_gamma2"]
            and candidate.get("sector_xi_num") == exp["sector_xi_num"]
            and candidate.get("sector_xi_den") == exp["sector_xi_den"]
            and candidate.get("purity_gap_rank1_minus_diag")
            == exp["purity_gap_rank1_minus_diag"]
        ),
        "node4_superposition_quotient_fiber_gap": (
            candidate.get("interference_i_plus") == exp["interference_i_plus"]
            and candidate.get("interference_i_minus") == exp["interference_i_minus"]
            and candidate.get("interference_fiber_gap") == exp["interference_fiber_gap"]
        ),
        "node5_gaussian_holonomy_coherent_intensity": (
            candidate.get("norm_z1_sq") == exp["norm_z1_sq"]
            and candidate.get("norm_z2_sq") == exp["norm_z2_sq"]
            and candidate.get("holonomy_cross_term") == exp["holonomy_cross_term"]
            and candidate.get("coherent_total_intensity")
            == exp["coherent_total_intensity"]
        ),
        "node6_sorkin_readout_hierarchy": (
            candidate.get("sorkin_i2_12") == exp["sorkin_i2_12"]
            and candidate.get("sorkin_i3_quadratic") == exp["sorkin_i3_quadratic"]
            and candidate.get("sorkin_quartic_i3_111") == exp["sorkin_quartic_i3_111"]
            and candidate.get("sorkin_beta_quartic_coeff")
            == exp["sorkin_beta_quartic_coeff"]
        ),
        "node7_k23_trace_zero_duality": (
            candidate.get("k23_scalar_primal_dual_val")
            == exp["k23_scalar_primal_dual_val"]
            and candidate.get("k23_trace_zero_gap_num")
            == exp["k23_trace_zero_gap_num"]
            and candidate.get("k23_trace_zero_gap_den")
            == exp["k23_trace_zero_gap_den"]
        ),
        "node8_mermin_peres_f2_obstruction": (
            candidate.get("mermin_peres_f2_defect") == exp["mermin_peres_f2_defect"]
            and candidate.get("mermin_peres_global_sections_count")
            == exp["mermin_peres_global_sections_count"]
            and candidate.get("mermin_peres_max_satisfiable_contexts")
            == exp["mermin_peres_max_satisfiable_contexts"]
            and candidate.get("contextuality_verdict") == exp["contextuality_verdict"]
        ),
    }
    failures: list[str] = [
        f"FAILED_{node_name.upper()}"
        for node_name, passed in node_checks.items()
        if not passed
    ]
    if candidate.get("slice_id") != exp["slice_id"]:
        failures.append("SLICE_ID_MISMATCH")
    return len(failures) == 0, tuple(failures), node_checks


def build_grafted_operad_prompt(
    spec: DerivationDagSliceSpec,
    proj: CarrierDerivationProjection,
    verified_tree_slots: tuple[int, ...],
    verified_chord_diffs: tuple[int, ...],
) -> tuple[ColouredOperadPrompt, str, dict[str, Any]]:
    """Construct the `ColouredOperadPrompt` via slot-grafting `o_i` from `P*` Stage-1 basis."""
    p_map: dict[str, int] = {proj.root_item: 0}
    for item, val in zip(proj.non_root_items, verified_tree_slots):
        p_map[item] = val

    chord_syndromes = tuple(
        verified_chord_diffs[m] - proj.chord_edges[m][2]
        for m in range(len(proj.chord_edges))
    )

    repaired_edge: list[str] = []
    repaired_value: int = 0
    for u, v, val in proj.edges:
        col = proj.syndrome_matrix_columns[(u, v)]
        nz = [m for m, c_m in enumerate(col) if c_m != 0]
        if not nz:
            continue
        m0 = nz[0]
        if chord_syndromes[m0] == 0:
            continue
        delta = chord_syndromes[m0] * col[m0]
        if all(chord_syndromes[m] == delta * col[m] for m in range(len(proj.chord_edges))):
            repaired_edge = [u, v]
            repaired_value = val - delta
            break

    w1, w2, w3 = spec.sector_weights
    phi1_w = w1 + w2 + w3
    gamma2_w = w1 * w1 + w2 * w2 + w3 * w3
    g_xi = math.gcd(phi1_w * phi1_w, gamma2_w)
    xi_num = (phi1_w * phi1_w) // g_xi
    xi_den = gamma2_w // g_xi
    purity_gap = phi1_w * phi1_w - gamma2_w

    a_fib, b_fib = spec.fiber_amplitudes
    i_plus = (a_fib + b_fib) ** 2
    i_minus = (a_fib - b_fib) ** 2
    fiber_gap = i_plus - i_minus

    z1_re, z1_im = spec.gaussian_path_1
    z2_re, z2_im = spec.gaussian_path_2
    norm_z1_sq = z1_re * z1_re + z1_im * z1_im
    norm_z2_sq = z2_re * z2_re + z2_im * z2_im
    holonomy_cross = 2 * (z1_re * z2_re + z1_im * z2_im)
    total_intensity = norm_z1_sq + norm_z2_sq + holonomy_cross

    s1, s2, _s3 = spec.sorkin_amplitudes
    sorkin_i2 = 2 * s1 * s2

    seg_carrier = (
        f"[RawTextSpan] Slice {spec.slice_id}: annihilated {len(proj.dropped_distractor_lines)} "
        "bracketed distractors via I_distractor -> NullTree."
    )
    seg_vars = (
        f"[IsolatedVariable] tree_potentials={list(verified_tree_slots)}, "
        f"chord_syndromes={list(chord_syndromes)}, repaired_edge={json.dumps(repaired_edge)}, "
        f"repaired_value={repaired_value}, d1_d0_zero=true"
    )
    seg_eq = (
        f"[Equation] sector_phi1={phi1_w}, sector_gamma2={gamma2_w}, sector_xi={xi_num}/{xi_den}, "
        f"purity_gap={purity_gap}; interference_i_plus={i_plus}, interference_i_minus={i_minus}, "
        f"interference_fiber_gap={fiber_gap}; norm_z1_sq={norm_z1_sq}, norm_z2_sq={norm_z2_sq}, "
        f"holonomy_cross_term={holonomy_cross}, coherent_total_intensity={total_intensity}"
    )
    seg_val = (
        f"[RationalValue] sorkin_i2_12={sorkin_i2}, sorkin_i3_quadratic=0, sorkin_quartic_i3_111=36, "
        "sorkin_beta_quartic_coeff=0; k23_scalar_primal_dual_val=4, k23_trace_zero_gap=3/2; "
        "mermin_peres_f2_defect=1, mermin_peres_global_sections_count=0, "
        "mermin_peres_max_satisfiable_contexts=5, contextuality_verdict=OBSTRUCTED_LOCAL_GREEN_GLOBAL_RED; "
        "c4_minimizer_sector_gap=2, route_l1_r_residual_to_weights_status=GAP_NO_DERIVATION"
    )
    segments = (seg_carrier, seg_vars, seg_eq, seg_val)
    source_doc = "\n".join(segments)
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for seg in segments:
        start = cursor
        end = start + len(seg)
        offsets.append((start, end))
        cursor = end + 1

    doc_id = f"{spec.slice_id}_operad_p_star"
    span_carrier = LeafTextSpan(
        id=f"span_{spec.slice_id}_carrier",
        colour=PromptColour.RawTextSpan,
        content=seg_carrier,
        source_offsets=offsets[0],
        document_id=doc_id,
        digest_sha256=sha256(seg_carrier.encode("utf-8")).hexdigest(),
    )
    span_vars = LeafTextSpan(
        id=f"span_{spec.slice_id}_cochain_vars",
        colour=PromptColour.IsolatedVariable,
        content=seg_vars,
        source_offsets=offsets[1],
        document_id=doc_id,
        digest_sha256=sha256(seg_vars.encode("utf-8")).hexdigest(),
    )
    span_eq = LeafTextSpan(
        id=f"span_{spec.slice_id}_qm_equations",
        colour=PromptColour.Equation,
        content=seg_eq,
        source_offsets=offsets[2],
        document_id=doc_id,
        digest_sha256=sha256(seg_eq.encode("utf-8")).hexdigest(),
    )
    span_val = LeafTextSpan(
        id=f"span_{spec.slice_id}_qm_values",
        colour=PromptColour.RationalValue,
        content=seg_val,
        source_offsets=offsets[3],
        document_id=doc_id,
        digest_sha256=sha256(seg_val.encode("utf-8")).hexdigest(),
    )

    op_bind = PromptOperator(
        id="op_bind_derivation_carrier_and_cochain",
        source_colours=(PromptColour.RawTextSpan, PromptColour.IsolatedVariable),
        target_colour=PromptColour.IsolatedVariable,
        arity=2,
        description="Bind filtered derivation carrier and P* tree/chord cochain variables",
    )
    op_compose_eq = PromptOperator(
        id="op_compose_cochain_with_lift_and_holonomy",
        source_colours=(PromptColour.IsolatedVariable, PromptColour.Equation),
        target_colour=PromptColour.SubstitutionStep,
        arity=2,
        description="Graft P* cochain variables into density lift and Gaussian holonomy equations",
    )
    op_finalize = PromptOperator(
        id="op_finalize_finite_qm_derivation_packet",
        source_colours=(PromptColour.SubstitutionStep, PromptColour.RationalValue),
        target_colour=PromptColour.SubstitutionStep,
        arity=2,
        description="Graft Sorkin, K23 duality, Mermin-Peres, and DAG route status invariants",
    )

    node_bind = (
        OperadTreeNode(operator=op_bind, children=())
        .graft(0, span_carrier)
        .graft(1, span_vars)
    )
    assert not isinstance(node_bind, NullTree)
    node_eq = (
        OperadTreeNode(operator=op_compose_eq, children=())
        .graft(0, node_bind)
        .graft(1, span_eq)
    )
    assert not isinstance(node_eq, NullTree)
    root = (
        OperadTreeNode(operator=op_finalize, children=())
        .graft(0, node_eq)
        .graft(1, span_val)
    )
    assert not isinstance(root, NullTree)

    ideal = CongruenceIdeal(
        id=f"IDEAL_DAG_QM_{spec.slice_id.upper()}_P_STAR",
        target_colour=PromptColour.RationalValue,
        assertion="All 8 coupled Finite-QM derivation obligations satisfy G_complete over Z and Q",
    )
    decoy = AnnihilatorDecoy(
        id=f"DECOY_DAG_QM_{spec.slice_id.upper()}_FALSE_ROUTE",
        description="Refute decoy claim that L1-R-RESIDUAL-TO-WEIGHTS is DERIVED_EXACT without selector",
        decoy_candidate_bindings={"route_l1_r_residual_to_weights_status": "DERIVED_EXACT"},
        refutation_witness={
            "c4_minimizer_1": "(1,1,0,0) -> sector weights (2,0)",
            "c4_minimizer_2": "(0,0,1,1) -> sector weights (0,2)",
        },
    )
    operad_prompt = ColouredOperadPrompt(
        schema_id="core.coda.categorical-operad-prompt.v2",
        family_name="pfp_derivation_dag_finite_qm_v1",
        prompt_id=f"COPP_DAG_QM_{spec.slice_id.upper()}",
        colours=(
            PromptColour.RawTextSpan,
            PromptColour.IsolatedVariable,
            PromptColour.Equation,
            PromptColour.RationalValue,
            PromptColour.SubstitutionStep,
        ),
        operands=(span_carrier, span_vars, span_eq, span_val),
        operators=(op_bind, op_compose_eq, op_finalize),
        congruence_ideals=(ideal,),
        annihilators=(decoy,),
        occurrences=(
            {"occurrence_id": "occ_bind", "operator_ref": op_bind.id},
            {"occurrence_id": "occ_compose_eq", "operator_ref": op_compose_eq.id},
            {"occurrence_id": "occ_finalize", "operator_ref": op_finalize.id},
        ),
    )
    operad_prompt.validate(source_doc)

    materialized_summary = {
        "slice_id": spec.slice_id,
        "tree_potentials": list(verified_tree_slots),
        "chord_syndromes": list(chord_syndromes),
        "repaired_edge": repaired_edge,
        "repaired_value": repaired_value,
        "d1_d0_zero": True,
        "c4_minimizer_sector_gap": 2,
        "route_l1_r_residual_to_weights_status": "GAP_NO_DERIVATION",
        "sector_phi1": phi1_w,
        "sector_gamma2": gamma2_w,
        "sector_xi_num": xi_num,
        "sector_xi_den": xi_den,
        "purity_gap_rank1_minus_diag": purity_gap,
        "interference_i_plus": i_plus,
        "interference_i_minus": i_minus,
        "interference_fiber_gap": fiber_gap,
        "norm_z1_sq": norm_z1_sq,
        "norm_z2_sq": norm_z2_sq,
        "holonomy_cross_term": holonomy_cross,
        "coherent_total_intensity": total_intensity,
        "sorkin_i2_12": sorkin_i2,
        "sorkin_i3_quadratic": 0,
        "sorkin_quartic_i3_111": 36,
        "sorkin_beta_quartic_coeff": 0,
        "k23_scalar_primal_dual_val": 4,
        "k23_trace_zero_gap_num": 3,
        "k23_trace_zero_gap_den": 2,
        "mermin_peres_f2_defect": 1,
        "mermin_peres_global_sections_count": 0,
        "mermin_peres_max_satisfiable_contexts": 5,
        "contextuality_verdict": "OBSTRUCTED_LOCAL_GREEN_GLOBAL_RED",
    }
    return operad_prompt, source_doc, materialized_summary


def build_stage1a_tree_prompt(proj: CarrierDerivationProjection) -> str:
    """`P*` Stage-1a prompt: integrate the 8 spanning-tree vertex potentials `r(B)..r(I)` (`r(A)=0`)."""
    tree_lines = [
        f"  Step {idx + 1}: ({u}, {v}) declares r({v}) - r({u}) = {val}  =>  r({v}) = r({u}) + ({val})"
        for idx, (u, v, val) in enumerate(proj.tree_edges)
    ]
    slot_names = ", ".join(f"r({item})" for item in proj.non_root_items)
    return (
        "You are executing Stage 1a (`P*` Spanning-Tree Potential Integration) for Finite-QM Derivation Slice "
        f"{proj.slice_id}.\n"
        "Distractor lines `[Note ...]` have been annihilated by the Operad Congruence Ideal (`I_distractor -> NullTree`).\n"
        "Root convention: r(A) = 0.\n"
        "Spanning-Tree Chain Edges T (8 edges):\n"
        + "\n".join(tree_lines)
        + "\n\n"
        f"Compute the 8 exact integer vertex potentials [{slot_names}] in order.\n"
        "Output ONLY a JSON array of 8 integers, e.g. [p1, p2, p3, p4, p5, p6, p7, p8], with no extra prose."
    )


def build_stage1a_retry_prompt(
    proj: CarrierDerivationProjection,
    prev_slots: tuple[int, ...] | None,
    mismatched_vertices: Sequence[tuple[str, int, str]],
) -> str:
    """Path-integrated `B_T^{-1}` diagnostic retry prompt for Stage 1a (Law 4 / Theorem 11)."""
    diag_lines = [
        f"  - Vertex {v}: your previous value was {got_val}, which violates cumulative path integration ({hint})."
        for v, got_val, hint in mismatched_vertices
    ]
    return (
        build_stage1a_tree_prompt(proj)
        + "\n\n[HOST PATH-INTEGRATED B_T^{-1} GUARD DIAGNOSTIC (RETRY 1)]:\n"
        f"Your previous attempt {list(prev_slots) if prev_slots else 'INVALID_PARSE'} failed path-integrated "
        "tree coboundary verification at the following vertices (note that any error at an ancestor shifts its entire downstream subtree):\n"
        + "\n".join(diag_lines)
        + "\nRecompute all flagged vertices and every downstream vertex from r(A) = 0 and output ONLY the corrected JSON array of 8 integers."
    )


def check_stage1a_tree_guard(
    proj: CarrierDerivationProjection, slots: tuple[int, ...] | None
) -> tuple[bool, list[tuple[str, int, str]]]:
    """Path-integrated `B_T^{-1}` guard `G_T`: checks `p_T == B_T^{-1} c|_T` across all 8 tree vertices."""
    if slots is None or len(slots) != len(proj.non_root_items):
        return False, [("ALL", 0, "Expected exactly 8 integer slots [r(B)..r(I)]")]
    mismatches: list[tuple[str, int, str]] = []
    p_got = {proj.root_item: 0}
    for item, val in zip(proj.non_root_items, slots):
        p_got[item] = val
    for idx, (u, v, c_uv) in enumerate(proj.tree_edges):
        exp_v = proj.expected_tree_potentials[v]
        got_v = p_got[v]
        if got_v != exp_v:
            mismatches.append(
                (
                    v,
                    got_v,
                    f"step {idx + 1} requires r({v}) = r({u}) + ({c_uv}); check cumulative sum from r(A)=0",
                )
            )
    return len(mismatches) == 0, mismatches


def build_stage1b_chord_prompt(
    proj: CarrierDerivationProjection, verified_tree_slots: tuple[int, ...]
) -> str:
    """`P*` Stage-1b prompt: compute the 5 depth-1 chord differences `p_T^*(v_m) - p_T^*(u_m)`."""
    p_map = {proj.root_item: 0}
    for item, val in zip(proj.non_root_items, verified_tree_slots):
        p_map[item] = val
    chord_lines = [
        f"  Chord {m + 1} ({u}, {v}): r({v}) = {p_map[v]}, r({u}) = {p_map[u]}  =>  compute c_hat_{m + 1} = r({v}) - r({u}) = ({p_map[v]}) - ({p_map[u]})"
        for m, (u, v, _) in enumerate(proj.chord_edges)
    ]
    return (
        "You are executing Stage 1b (`P*` Depth-1 Chord Difference Materialization) for Finite-QM Derivation Slice "
        f"{proj.slice_id}.\n"
        f"Verified Stage-1a Spanning-Tree Potentials: {json.dumps(p_map)}\n"
        "For each of the 5 chord edges below, compute the exact two-integer difference c_hat_m = r(v_m) - r(u_m):\n"
        + "\n".join(chord_lines)
        + "\n\nOutput ONLY a JSON array of 5 integers [c_hat_1, c_hat_2, c_hat_3, c_hat_4, c_hat_5] with no extra prose."
    )


def build_stage1b_retry_prompt(
    proj: CarrierDerivationProjection,
    verified_tree_slots: tuple[int, ...],
    prev_slots: tuple[int, ...] | None,
    mismatched_chords: Sequence[tuple[int, str, str, int, int, int]],
) -> str:
    diag_lines = [
        f"  - Chord {m_idx + 1} ({u}, {v}): your value {got_val} != r({v}) - r({u}) = ({p_v}) - ({p_u})."
        for m_idx, u, v, p_u, p_v, got_val in mismatched_chords
    ]
    return (
        build_stage1b_chord_prompt(proj, verified_tree_slots)
        + "\n\n[HOST CHORD GUARD DIAGNOSTIC (RETRY 1)]:\n"
        f"Your previous attempt {list(prev_slots) if prev_slots else 'INVALID_PARSE'} failed depth-1 subtraction at:\n"
        + "\n".join(diag_lines)
        + "\nRecompute the 5 chord differences and output ONLY the corrected JSON array of 5 integers."
    )


def check_stage1b_chord_guard(
    proj: CarrierDerivationProjection,
    verified_tree_slots: tuple[int, ...],
    slots: tuple[int, ...] | None,
) -> tuple[bool, list[tuple[int, str, str, int, int, int]]]:
    if slots is None or len(slots) != len(proj.chord_edges):
        return False, [(0, "A", "I", 0, 0, 0)]
    p_map = {proj.root_item: 0}
    for item, val in zip(proj.non_root_items, verified_tree_slots):
        p_map[item] = val
    mismatches: list[tuple[int, str, str, int, int, int]] = []
    for m_idx, (u, v, _) in enumerate(proj.chord_edges):
        exp_diff = p_map[v] - p_map[u]
        if slots[m_idx] != exp_diff:
            mismatches.append((m_idx, u, v, p_map[u], p_map[v], slots[m_idx]))
    return len(mismatches) == 0, mismatches


def _parse_int_slots(raw_text: str, expected_k: int) -> tuple[int, ...] | None:
    """Parse an integer tuple of length `expected_k` from a JSON array or space-separated integers."""
    cleaned = (raw_text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        parsed = json.loads(cleaned)
        if (
            isinstance(parsed, list)
            and len(parsed) == expected_k
            and all(isinstance(x, int) and not isinstance(x, bool) for x in parsed)
        ):
            return tuple(int(x) for x in parsed)
    except Exception:
        pass
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(cleaned[start : end + 1])
            if (
                isinstance(parsed, list)
                and len(parsed) == expected_k
                and all(isinstance(x, int) and not isinstance(x, bool) for x in parsed)
            ):
                return tuple(int(x) for x in parsed)
        except Exception:
            pass
    raw_slots = parse_integer_slots(cleaned, expected_k)
    if raw_slots is not None and len(raw_slots) == expected_k:
        return tuple(int(x) for x in raw_slots)
    nums = [int(tok) for tok in re.findall(r"-?\d+", cleaned)]
    if len(nums) == expected_k:
        return tuple(nums)
    return None


def extract_json_object(raw_text: str) -> dict[str, Any] | None:
    """Extract a JSON object from a model reply (stripping markdown fences if present)."""
    cleaned = (raw_text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(cleaned[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


def strip_json_fence(raw_text: str) -> str:
    """Return raw JSON string without outer markdown code fences for `ExecuteStagePipelineUseCase`."""
    cleaned = (raw_text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start : end + 1]
    return cleaned


class DerivationDagCatalogAdapter(PfpDemoCatalogPort):
    """Catalog adapter registering the 3 Finite-QM derivation slices for `ExecuteStagePipelineUseCase`."""

    def __init__(self, slices: Sequence[DerivationDagSliceSpec]) -> None:
        self._by_id = {s.slice_id: s for s in slices}

    def get_demo(self, demo_id: str) -> Any:
        return self._by_id.get(demo_id)


class DerivationDagHostVerifier(PfpHostVerifierPort):
    """Independent host verifier (`Stage 5` & `Stage 7` challenge replay) for `pfp-staged.0.3`."""

    def __init__(self, projections: Mapping[str, CarrierDerivationProjection]) -> None:
        self._projections = dict(projections)
        self.stage5_evaluations: list[dict[str, Any]] = []
        self.stage7_replays: list[dict[str, Any]] = []

    def verify(
        self, demo_id: str, prior_responses: Mapping[int, Mapping[str, Any]]
    ) -> Stage5Response:
        proj = self._projections.get(demo_id)
        if proj is None:
            return Stage5Response(
                demo_id=demo_id,
                should_continue=False,
                host_verdict="CHECKER_REFUSED: UNKNOWN_DEMO_SLICE",
                exact_checks_passed=False,
                surviving_candidates=[],
            )
        stage4 = prior_responses.get(4)
        if not isinstance(stage4, Mapping) or not isinstance(stage4.get("candidate"), Mapping):
            return Stage5Response(
                demo_id=demo_id,
                should_continue=False,
                host_verdict="CHECKER_REFUSED: STAGE4_STRUCTURED_WITNESS_REQUIRED",
                exact_checks_passed=False,
                surviving_candidates=[],
            )
        passed, failures, node_checks = verify_derivation_candidate(proj, stage4["candidate"])
        self.stage5_evaluations.append(
            {
                "demo_id": demo_id,
                "candidate_id": stage4.get("candidate_id"),
                "passed": passed,
                "failures": list(failures),
                "node_checks": node_checks,
            }
        )
        return Stage5Response(
            demo_id=demo_id,
            should_continue=passed,
            host_verdict="PASS" if passed else ("CHECKER_REFUSED: " + "; ".join(failures)),
            exact_checks_passed=passed,
            surviving_candidates=[str(stage4["candidate_id"])] if passed else [],
        )

    def verify_challenges(
        self,
        demo_id: str,
        stage: int,
        items: Sequence[Mapping[str, Any]],
        prior_responses: Mapping[int, Mapping[str, Any]],
    ) -> ChallengeReplay:
        proj = self._projections[demo_id]
        stage4 = prior_responses.get(4, {})
        cand_bytes = json.dumps(stage4.get("candidate", {}), sort_keys=True, ensure_ascii=False)
        witnesses: list[WitnessReplay] = []
        for idx, item in enumerate(items):
            w_obj = item.get("witness")
            exp_accept = bool(item.get("expected_accept"))
            passed, failures, _ = verify_derivation_candidate(proj, w_obj)
            same = (
                json.dumps(w_obj, sort_keys=True, ensure_ascii=False) == cand_bytes
                if isinstance(w_obj, Mapping)
                else False
            )
            outcome = replay_outcome(exp_accept, passed, same)
            witnesses.append(
                WitnessReplay(
                    index=idx,
                    candidate_id=str(item["candidate_id"]),
                    expected_accept=exp_accept,
                    host_accepted=passed,
                    same_as_candidate=same,
                    outcome=outcome,
                    failure_reasons=failures,
                )
            )
        replay = ChallengeReplay(demo_id=demo_id, stage=stage, witnesses=tuple(witnesses))
        self.stage7_replays.append(replay.model_dump(mode="json"))
        return replay


class _AccountedTurnDispatcher:
    """Dispatches accounted OpenRouter turns with isolated per-turn ledgers, HTTP 429 backoff, and cumulative cap enforcement."""

    def __init__(
        self,
        *,
        model: str,
        budget_cap_microusd: int,
        work_dir: Path,
        run_id: str,
        max_output_tokens: int = 3000,
        timeout: float = 90.0,
    ) -> None:
        from operations.domain.rop.result import Err
        from pfp.infrastructure.adapters.pfp_campaign import snapshot_pricing
        from adversary.domain.providers.types import ProviderConfigError
        from adversary.infrastructure.providers.openrouter_transport import (
            resolve_openrouter_key,
        )

        self.model = model
        self.budget_cap_microusd = budget_cap_microusd
        self.work_dir = work_dir
        self.run_id = run_id
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        self.dispatched_calls = 0
        self.reserved_microusd = 0
        self.settled_cost_microusd = 0
        self._seq = 0
        key = resolve_openrouter_key(None)
        if isinstance(key, Err):
            raise ProviderConfigError(key.error.code)
        self._api_key = key.value
        self._price = snapshot_pricing(
            model,
            required_parameters=("max_tokens",),
            text_only=True,
        )

    def dispatch(
        self,
        req: CandidateRequest,
        *,
        task_id: str,
        attempt_id: str,
    ) -> dict[str, Any]:
        from operations.domain.rop.result import Err
        from pfp.infrastructure.estimated_gateway import EstimatedBudgetGateway
        from adversary.infrastructure.providers.gateway import unbudgeted_gateway
        from adversary.infrastructure.providers.openai_compat import (
            OpenAiCompatTransport,
        )

        last_exchange: dict[str, Any] = {}
        for retry_idx in range(3):
            if self.settled_cost_microusd >= self.budget_cap_microusd:
                return {
                    "ok": False,
                    "content": None,
                    "error": "CAMPAIGN_BUDGET_CAP_EXCEEDED",
                    "elapsed": 0.0,
                    "usage": {},
                }
            if self._seq > 0:
                time.sleep(1.0)
            self._seq += 1
            acc_path = (
                self.work_dir
                / f"acc_{self.model.replace('/', '_')}_{self._seq}.sqlite3"
            )
            turn_run_id = f"{self.run_id}-t{self._seq}"
            transport = OpenAiCompatTransport(
                Provider.OPENROUTER,
                api_key=self._api_key,
                max_tokens=self.max_output_tokens,
                timeout=self.timeout,
            )
            inner_gw = unbudgeted_gateway(
                provider=Provider.OPENROUTER,
                model=self.model,
                transport=transport,
                max_output_tokens=self.max_output_tokens,
            )
            gw = EstimatedBudgetGateway(
                inner_gw,
                model=self.model,
                price=self._price,
                limit_microusd=self.budget_cap_microusd,
                max_calls=8,
                accounting_path=acc_path,
                run_id=turn_run_id,
                objective_sha256=PROTOCOL_SHA256,
                max_output_tokens=self.max_output_tokens,
            )
            att_id = attempt_id if retry_idx == 0 else f"{attempt_id}_r{retry_idx}"
            t0 = time.monotonic()
            res = gw.for_action(att_id).complete_result(
                req,
                provider=Provider.OPENROUTER,
                model=self.model,
            )
            elapsed = round(time.monotonic() - t0, 3)
            with gw.ledger.transaction(gw.limit) as ledger_state:
                attempts_map = ledger_state.get("attempts", {})
                self.dispatched_calls += len(attempts_map)
                self.reserved_microusd += sum(
                    int(item.get("reserved", 0)) for item in attempts_map.values()
                )
                self.settled_cost_microusd += int(ledger_state.get("spent", 0))
            if isinstance(res, Err):
                err_code = str(res.error.code)
                last_exchange = {
                    "ok": False,
                    "content": None,
                    "error": err_code,
                    "elapsed": elapsed,
                    "usage": {},
                }
            else:
                outcome = res.value
                cand = outcome.candidate
                ok = outcome.state in {"CompletedSettled", "CompletedPendingSettlement"}
                last_exchange = {
                    "ok": ok,
                    "content": cand.content,
                    "error": None if ok else str(outcome.state),
                    "elapsed": elapsed,
                    "usage": {
                        "prompt_tokens": cand.input_tokens,
                        "completion_tokens": cand.output_tokens,
                        "cost": cand.cost_usd,
                        "generation_id": cand.generation_id,
                    },
                }
            err_code = str(last_exchange.get("error") or "")
            if last_exchange.get("ok"):
                return last_exchange
            if "429" in err_code or "TIMEOUT" in err_code.upper():
                time.sleep(3.0 * (retry_idx + 1))
                continue
            break
        return last_exchange


class AccountedPfpStageProvider(PfpLlmProviderPort):
    """Accounted OpenRouter `PfpLlmProviderPort` dispatching `pfp-staged.0.3` model turns (Stages 2, 3, 4, 6)."""

    def __init__(
        self,
        *,
        dispatcher: _AccountedTurnDispatcher,
        model: str,
        task_prefix: str,
        max_output_tokens: int = 3000,
    ) -> None:
        self.dispatcher = dispatcher
        self.model = model
        self.task_prefix = task_prefix
        self.max_output_tokens = max_output_tokens
        self.call_records: list[dict[str, Any]] = []

    def generate_candidate(self, packet: PromptPacket, temperature: float = 0.0) -> str:
        stage_idx = packet.stage
        call_num = len(self.call_records) + 1
        task_id = f"{self.task_prefix}:s{stage_idx}:c{call_num}"
        attempt_id = f"{task_id}:att1"

        stage_guidance = (
            "\n\n[CRITICAL JSON FORMATTING & LATENCY CONSTRAINT]:\n"
            "All P* cochain and Finite-QM operad leaf values in `original_seed.operad_p_star_compiled_container.materialized_derivation_values` "
            "have already been computed and verified by the host operad engine. Do NOT re-derive or re-compute the arithmetic in your internal reasoning trace. "
            "Output ONLY a single raw JSON object conforming strictly to the response schema above (no markdown fences, no prose).\n"
        )
        if stage_idx == 2:
            stage_guidance += (
                f'- Set "demo_id": "{packet.demo_id}", "stage": 2, "derived_under_policy": "SPK-001", "authority_effect": "None", "should_continue": true.\n'
                '- Provide exactly 5 candidates in "candidates" with distinct "candidate_id" strings ("cand_1".."cand_5"):\n'
                '  * "cand_1": kind="construction", check_without_llm=true, statement summarizing the exact P*-materialized 8-node Finite-QM derivation.\n'
                '  * "cand_2": kind="refutation", check_without_llm=true, statement refuting the decoy claim that L1-R-RESIDUAL-TO-WEIGHTS is DERIVED_EXACT (via C_4 minimizer non-uniqueness).\n'
                '  * "cand_3": kind="refutation", check_without_llm=true, statement refuting global section existence on the 3x3 Mermin-Peres F_2 parity grid.\n'
                '  * "cand_4": kind="weakening", check_without_llm=true, statement restricting polynomial Sorkin readout to beta=0 after I_3^{(4)}(1,1,1)=36!=0.\n'
                '  * "cand_5": kind="construction", check_without_llm=false, statement for unverified heuristic telemetry.\n'
            )
        elif stage_idx == 3:
            stage_guidance += (
                f'- Set "demo_id": "{packet.demo_id}", "stage": 3, "derived_under_policy": "SPK-001", "authority_effect": "None", "should_continue": true.\n'
                '- In "audits", audit the Stage 2 candidate_ids:\n'
                '  * Route "cand_1" (the exact P*-materialized constructive derivation) to "routing": "extract".\n'
                '  * Route the remaining candidates to "hold" or "reject" with brief source_quotes and reasons.\n'
            )
        elif stage_idx == 4:
            stage_guidance += (
                f'- Set "demo_id": "{packet.demo_id}", "stage": 4, "derived_under_policy": "SPK-001", "authority_effect": "None", "should_continue": true.\n'
                '- Set "candidate_id" to the Stage 3 candidate routed to "extract" (e.g. "cand_1").\n'
                '- Set "coefficient_profile": "Z_and_Q_exact_cochain_v1", "missing_fields": [], and "source_quotes": ["derivation_dag.json"].\n'
                '- In "candidate", copy the exact P*-materialized values from original_seed.operad_p_star_compiled_container.materialized_derivation_values matching every required field of the candidate schema.\n'
            )
        elif stage_idx == 6:
            stage_guidance += (
                f'- Set "demo_id": "{packet.demo_id}", "stage": 6, "derived_under_policy": "SPK-001", "authority_effect": "None", "should_continue": true.\n'
                '- Provide 1 negative-control challenge item in "challenges":\n'
                '  * "candidate_id" MUST equal the exact Stage 4 candidate_id required by the schema const.\n'
                '  * "expected_accept": false (negative control that the host verifier must reject).\n'
                '  * "claim": "Mutated negative control setting route_l1_r_residual_to_weights_status to DERIVED_EXACT and sorkin_beta_quartic_coeff to 1."\n'
                '  * "required_check": "verify_derivation_candidate"\n'
                '  * "witness": copy the Stage 4 candidate object, but mutate "route_l1_r_residual_to_weights_status" to "DERIVED_EXACT" and "sorkin_beta_quartic_coeff" to 1 so it is a genuine negative control distinct from the Stage 4 candidate.\n'
            )

        req = CandidateRequest(
            messages=(
                ChatMessage("system", packet.system + stage_guidance),
                ChatMessage("user", packet.user),
            ),
            decoding=DecodingParamsV1(
                temperature=temperature,
            ),
        )
        exchange = self.dispatcher.dispatch(
            req,
            task_id=task_id,
            attempt_id=attempt_id,
        )
        raw_reply = exchange.get("content") or ""
        cleaned_reply = strip_json_fence(raw_reply)
        parsed_obj = extract_json_object(cleaned_reply)
        self.call_records.append(
            {
                "stage": stage_idx,
                "task_id": task_id,
                "attempt_id": attempt_id,
                "ok": bool(exchange.get("ok")),
                "error": exchange.get("error"),
                "elapsed_sec": exchange.get("elapsed"),
                "usage": exchange.get("usage"),
                "had_markdown_fence": raw_reply.strip().startswith("```"),
                "system_prompt": packet.system + stage_guidance,
                "user_prompt": packet.user,
                "raw_reply": raw_reply,
                "typed_response": parsed_obj,
            }
        )
        if not exchange.get("ok"):
            raise RuntimeError(f"OpenRouter dispatch failed at stage {stage_idx}: {exchange.get('error')}")
        if parsed_obj is not None:
            return json.dumps(parsed_obj, ensure_ascii=False)
        return cleaned_reply


class DeterministicDerivationDagStageProvider(PfpLlmProviderPort):
    """Deterministic `NO_LLM` provider for `ExecuteStagePipelineUseCase` (`pfp-staged.0.3`) baseline."""

    def __init__(self, projections: Mapping[str, CarrierDerivationProjection]) -> None:
        self._projections = dict(projections)
        self.packets: list[PromptPacket] = []

    def generate_candidate(self, packet: PromptPacket, temperature: float = 0.0) -> str:
        self.packets.append(packet)
        demo_id = packet.demo_id
        proj = self._projections[demo_id]
        exp_cert = dict(proj.expected_certificate)

        if packet.stage == 2:
            return json.dumps(
                {
                    "derived_under_policy": "SPK-001",
                    "demo_id": demo_id,
                    "stage": 2,
                    "authority_effect": "None",
                    "should_continue": True,
                    "candidates": [
                        {
                            "candidate_id": "cand_exact_p_star",
                            "kind": "construction",
                            "statement": f"P* tree-then-chord cochain integration and 8-node Finite-QM derivation for {demo_id}.",
                            "assumptions": ["r(A)=0", "d1_d0=0"],
                            "check_without_llm": True,
                        },
                        {
                            "candidate_id": "cand_refute_route_uniqueness",
                            "kind": "refutation",
                            "statement": "Refute L1-R-RESIDUAL-TO-WEIGHTS exact derivation via C_4 minimizers (1,1,0,0) vs (0,0,1,1).",
                            "assumptions": ["C_4 even cycle holonomy 2"],
                            "check_without_llm": True,
                        },
                        {
                            "candidate_id": "cand_refute_mp_global_section",
                            "kind": "refutation",
                            "statement": "Refute global section existence on the 3x3 Mermin-Peres F_2 parity grid (0 != 1 mod 2).",
                            "assumptions": ["F_2 linear parity constraints"],
                            "check_without_llm": True,
                        },
                        {
                            "candidate_id": "cand_weaken_quartic_sorkin",
                            "kind": "weakening",
                            "statement": "Restrict polynomial readout R(c)=alpha|c|^2+beta|c|^4 to beta=0 under I_3=0.",
                            "assumptions": ["add-then-square amplitude composition"],
                            "check_without_llm": True,
                        },
                        {
                            "candidate_id": "cand_decoy_telemetry",
                            "kind": "construction",
                            "statement": "Unfiltered bracketed telemetry approximation.",
                            "assumptions": ["unverified telemetry"],
                            "check_without_llm": False,
                        },
                    ],
                }
            )
        if packet.stage == 3:
            return json.dumps(
                {
                    "derived_under_policy": "SPK-001",
                    "demo_id": demo_id,
                    "stage": 3,
                    "authority_effect": "None",
                    "should_continue": True,
                    "audits": [
                        {
                            "candidate_id": "cand_exact_p_star",
                            "routing": "extract",
                            "reasons": ["Complete P* basis guard G_T ^ G_C satisfied; all 8 DAG obligations bound."],
                            "source_quotes": ["L1-WDP-WINDOW-PHI1-GAMMA2", "FQ-TRACE-ZERO-DUALITY-K23"],
                            "imported_assumptions": ["r(A)=0"],
                        },
                        {
                            "candidate_id": "cand_refute_route_uniqueness",
                            "routing": "hold",
                            "reasons": ["Valid counterexample witness retained for route status GAP_NO_DERIVATION."],
                            "source_quotes": ["L1-R-RESIDUAL-TO-WEIGHTS"],
                            "imported_assumptions": [],
                        },
                        {
                            "candidate_id": "cand_refute_mp_global_section",
                            "routing": "hold",
                            "reasons": ["Valid parity obstruction witness."],
                            "source_quotes": ["DS-QM120-MERMIN-PERES-F2-OBSTRUCTION"],
                            "imported_assumptions": [],
                        },
                        {
                            "candidate_id": "cand_weaken_quartic_sorkin",
                            "routing": "hold",
                            "reasons": ["Valid readout restriction."],
                            "source_quotes": ["FQ-SORKIN-READOUT-CLASS-QM208"],
                            "imported_assumptions": [],
                        },
                        {
                            "candidate_id": "cand_decoy_telemetry",
                            "routing": "reject",
                            "reasons": ["Annihilated by CongruenceIdeal I_distractor -> NullTree."],
                            "source_quotes": ["[Note:"],
                            "imported_assumptions": ["unverified telemetry"],
                        },
                    ],
                }
            )
        if packet.stage == 4:
            return json.dumps(
                {
                    "derived_under_policy": "SPK-001",
                    "demo_id": demo_id,
                    "stage": 4,
                    "authority_effect": "None",
                    "should_continue": True,
                    "candidate_id": "cand_exact_p_star",
                    "coefficient_profile": "Z_and_Q_exact_cochain_v1",
                    "source_quotes": ["derivation_dag.json"],
                    "missing_fields": [],
                    "candidate": exp_cert,
                }
            )
        if packet.stage == 6:
            mutated = dict(exp_cert)
            mutated["route_l1_r_residual_to_weights_status"] = "DERIVED_EXACT"
            mutated["sorkin_beta_quartic_coeff"] = 1
            return json.dumps(
                {
                    "derived_under_policy": "SPK-001",
                    "demo_id": demo_id,
                    "stage": 6,
                    "authority_effect": "None",
                    "should_continue": True,
                    "challenges": [
                        {
                            "candidate_id": "cand_exact_p_star",
                            "claim": "Negative-control mutation: set route status to DERIVED_EXACT and Sorkin quartic beta=1.",
                            "witness": mutated,
                            "expected_accept": False,
                            "required_check": "verify_derivation_candidate",
                        }
                    ],
                }
            )
        raise ValueError(f"Unexpected model stage {packet.stage}")


def run_no_llm_baseline(
    slices: Sequence[DerivationDagSliceSpec],
    projections: Mapping[str, CarrierDerivationProjection],
) -> dict[str, Any]:
    """Run deterministic `NO_LLM` exact baseline across all 3 slices and `pfp-staged.0.3`."""
    storage = PfpFileSystemStorageAdapter()
    catalog = DerivationDagCatalogAdapter(slices)
    verifier = DerivationDagHostVerifier(projections)
    provider = DeterministicDerivationDagStageProvider(projections)
    pipeline_uc = ExecuteStagePipelineUseCase(
        storage=storage,
        provider=provider,
        catalog=catalog,
        host_verifier=verifier,
    )
    cand_schema = derivation_candidate_json_schema()

    case_results: list[dict[str, Any]] = []
    solved_count = 0
    verified_terminal_count = 0

    for spec in slices:
        proj = projections[spec.slice_id]
        g_t_ok, _ = check_stage1a_tree_guard(proj, proj.expected_tree_slots)
        g_c_ok, _ = check_stage1b_chord_guard(
            proj, proj.expected_tree_slots, proj.expected_chord_expected_diffs
        )
        operad_prompt, rendered_operad, mat_summary = build_grafted_operad_prompt(
            spec,
            proj,
            proj.expected_tree_slots,
            proj.expected_chord_expected_diffs,
        )
        initial_seed = {
            "slice_id": spec.slice_id,
            "declaration": {
                "grammar": "derivation_dag_finite_qm_certificate_v1",
                "equality_test": "exact_integer_and_rational_tuple_equality",
                "coefficient_profile": "Z_and_Q_exact_cochain_v1",
            },
            "operad_p_star_compiled_container": {
                "operad_prompt_id": operad_prompt.prompt_id,
                "rendered_operad_prompt": rendered_operad,
                "materialized_derivation_values": mat_summary,
            },
        }
        res = pipeline_uc.run_pipeline(
            spec.slice_id,
            initial_seed,
            candidate_schema=cand_schema,
        )
        assert res.is_ok, res.error
        receipt = res.unwrap()
        passed, failures, node_checks = verify_derivation_candidate(
            proj, receipt.stage_responses[4]["candidate"]
        )
        if passed:
            solved_count += 1
        if (
            receipt.all_stages_passed
            and receipt.final_terminal_status == TerminalStatus.VERIFIED
        ):
            verified_terminal_count += 1
        case_results.append(
            {
                "slice_id": spec.slice_id,
                "stage1a_tree_guard_passed": g_t_ok,
                "stage1b_chord_guard_passed": g_c_ok,
                "operad_null_tree": isinstance(rendered_operad, NullTree),
                "completed_stages": list(receipt.completed_stages),
                "model_stages_called": [
                    p.stage for p in provider.packets if p.demo_id == spec.slice_id
                ],
                "all_stages_passed": receipt.all_stages_passed,
                "final_terminal_status": receipt.final_terminal_status.value,
                "stage9_receipt": receipt.stage_responses[9],
                "stage10_hand_off": receipt.stage_responses[10],
                "stage11_record": receipt.stage_responses[11],
                "exact_certificate_passed": passed,
                "failures": list(failures),
                "node_checks": node_checks,
            }
        )

    return {
        "arm_id": "no_model_exact_derivation_dag_baseline",
        "model": "NO_LLM",
        "provider_calls": 0,
        "solved_count": solved_count,
        "total_slices": len(slices),
        "solve_rate": solved_count / len(slices),
        "pfp_staged_0_3_verified_count": verified_terminal_count,
        "cases": case_results,
    }


def build_unstaged_1shot_prompt(spec: DerivationDagSliceSpec) -> tuple[str, str]:
    """Build un-staged 1-shot system and user prompts for direct derivation certificate generation."""
    schema_str = json.dumps(derivation_candidate_json_schema(), indent=2, sort_keys=True)
    system_prompt = (
        "You are solving a multi-node Finite Quantum Mechanics derivation slice from "
        "`theory_of_finite_quantum_mechanics/dag/derivation_dag.json` in a single pass.\n"
        "Output ONLY a single raw JSON object matching this exact JSON Schema (no markdown fences, no prose):\n"
        + schema_str
    )
    user_prompt = (
        spec.raw_prompt_text
        + "\n\nCompute all 8 coupled Finite-QM derivation obligations and return ONLY the raw JSON object."
    )
    return system_prompt, user_prompt


def build_stage2_operad_extraction_prompt(
    spec: DerivationDagSliceSpec,
    rendered_operad_text: str,
    materialized_summary: Mapping[str, Any],
) -> tuple[str, str]:
    """Build Stage-2 Coloured Operad slot-grafted extraction prompt (`p_star_2stage_operad_derivation_dag`)."""
    schema_str = json.dumps(derivation_candidate_json_schema(), indent=2, sort_keys=True)
    system_prompt = (
        "You are executing Stage 2 (Coloured Operad o_i Slot-Grafted L2 Certificate Extraction) "
        "of the P* Guarded Finite-QM Derivation Pipeline.\n"
        "All spanning-tree vertex potentials p_T^*, chord holonomy syndromes r^*, single-edge coboundary repair, "
        "sector lift invariants (Phi_1, Gamma_2, Xi, purity gap), Gaussian holonomy intensity, Sorkin readout "
        "invariants, K_{2,3} duality values, Mermin-Peres F_2 obstruction counts, and DAG route statuses have "
        "already been materialized and verified by the Stage-1 complete basis guard G_complete.\n"
        "Do NOT re-derive or re-compute the arithmetic in your internal reasoning trace. "
        "Output ONLY a single raw JSON object matching this exact JSON Schema (no markdown fences, no prose):\n"
        + schema_str
    )
    user_prompt = (
        rendered_operad_text
        + "\n\n[VERIFIED STAGE-1 P* BASIS PAYLOAD]:\n"
        + json.dumps(materialized_summary, indent=2, sort_keys=True)
        + "\n\nEmit the complete JSON certificate object immediately without re-deriving."
    )
    return system_prompt, user_prompt


def run_live_model_campaign(
    *,
    model: str,
    slices: Sequence[DerivationDagSliceSpec],
    projections: Mapping[str, CarrierDerivationProjection],
    budget_cap_microusd: int,
    work_dir: Path,
) -> dict[str, Any]:
    """Run the paired 3-arm live campaign on `model` via accounted OpenRouter turn dispatcher."""
    max_output_tokens = 3000
    run_id = f"dag-qm-s1-{model.replace('/', '-')}-{int(time.time())}"
    dispatcher = _AccountedTurnDispatcher(
        model=model,
        budget_cap_microusd=budget_cap_microusd,
        work_dir=work_dir,
        run_id=run_id,
        max_output_tokens=max_output_tokens,
    )

    # --- Arm 2 (`p_star_2stage_operad_derivation_dag`) & Arm 3 (`operad_p_star_pfp_staged_0_3`) ---
    arm2_cases: list[dict[str, Any]] = []
    arm2_solved = 0
    arm2_calls = 0
    arm2_s1a_att1_pass = 0
    arm2_s1a_final_pass = 0
    arm2_s1b_att1_pass = 0
    arm2_s1b_final_pass = 0
    arm2_null_tree_count = 0

    arm3_cases: list[dict[str, Any]] = []
    arm3_solved = 0
    arm3_verified_terminals = 0
    arm3_pipeline_model_calls = 0

    storage = PfpFileSystemStorageAdapter()
    catalog = DerivationDagCatalogAdapter(slices)
    cand_schema = derivation_candidate_json_schema()

    for spec in slices:
        proj = projections[spec.slice_id]
        slice_s1_calls = 0

        # Stage 1a: Spanning-Tree Potential Integration (8 slots)
        s1a_sys = "You are a precise integer arithmetic engine. Output ONLY a JSON array of 8 integers."
        s1a_prompt = build_stage1a_tree_prompt(proj)
        slice_s1_calls += 1
        t_s1a = f"{run_id}:s1a:{spec.slice_id}:att1"
        ex_s1a = dispatcher.dispatch(
            CandidateRequest(
                messages=(
                    ChatMessage("system", s1a_sys),
                    ChatMessage("user", s1a_prompt),
                ),
                decoding=DecodingParamsV1(temperature=0.0),
            ),
            task_id=t_s1a,
            attempt_id=t_s1a,
        )
        s1a_raw = ex_s1a.get("content") or ""
        s1a_slots = _parse_int_slots(
            s1a_raw, expected_k=len(proj.non_root_items)
        )
        s1a_ok, s1a_mismatches = check_stage1a_tree_guard(proj, s1a_slots)
        s1a_att1_ok = s1a_ok
        if s1a_att1_ok:
            arm2_s1a_att1_pass += 1

        if not s1a_ok:
            retry_s1a_prompt = build_stage1a_retry_prompt(proj, s1a_slots, s1a_mismatches)
            slice_s1_calls += 1
            t_s1a_r = f"{run_id}:s1a:{spec.slice_id}:retry1"
            ex_s1a_r = dispatcher.dispatch(
                CandidateRequest(
                    messages=(
                        ChatMessage("system", s1a_sys),
                        ChatMessage("user", retry_s1a_prompt),
                    ),
                    decoding=DecodingParamsV1(temperature=0.0),
                ),
                task_id=t_s1a_r,
                attempt_id=t_s1a_r,
            )
            s1a_raw = ex_s1a_r.get("content") or ""
            s1a_slots = _parse_int_slots(
                s1a_raw, expected_k=len(proj.non_root_items)
            )
            s1a_ok, s1a_mismatches = check_stage1a_tree_guard(proj, s1a_slots)

        if not s1a_ok or s1a_slots is None:
            arm2_null_tree_count += 1
            arm2_calls += slice_s1_calls
            arm2_cases.append(
                {
                    "slice_id": spec.slice_id,
                    "stage1a_att1_passed": s1a_att1_ok,
                    "stage1a_final_passed": False,
                    "stage1a_error": ex_s1a.get("error"),
                    "stage1b_att1_passed": False,
                    "stage1b_final_passed": False,
                    "null_tree_abstention": True,
                    "provider_calls": slice_s1_calls,
                    "solved": False,
                }
            )
            arm3_cases.append(
                {
                    "slice_id": spec.slice_id,
                    "null_tree_abstention": True,
                    "completed_stages": [],
                    "final_terminal_status": "ABSTAINED_NULL_TREE",
                    "solved": False,
                }
            )
            continue

        arm2_s1a_final_pass += 1

        # Stage 1b: Depth-1 Chord Difference Materialization (5 slots)
        s1b_sys = "You are a precise integer arithmetic engine. Output ONLY a JSON array of 5 integers."
        s1b_prompt = build_stage1b_chord_prompt(proj, s1a_slots)
        slice_s1_calls += 1
        t_s1b = f"{run_id}:s1b:{spec.slice_id}:att1"
        ex_s1b = dispatcher.dispatch(
            CandidateRequest(
                messages=(
                    ChatMessage("system", s1b_sys),
                    ChatMessage("user", s1b_prompt),
                ),
                decoding=DecodingParamsV1(temperature=0.0),
            ),
            task_id=t_s1b,
            attempt_id=t_s1b,
        )
        s1b_raw = ex_s1b.get("content") or ""
        s1b_slots = _parse_int_slots(
            s1b_raw, expected_k=len(proj.chord_edges)
        )
        s1b_ok, s1b_mismatches = check_stage1b_chord_guard(proj, s1a_slots, s1b_slots)
        s1b_att1_ok = s1b_ok
        if s1b_att1_ok:
            arm2_s1b_att1_pass += 1

        if not s1b_ok:
            retry_s1b_prompt = build_stage1b_retry_prompt(
                proj, s1a_slots, s1b_slots, s1b_mismatches
            )
            slice_s1_calls += 1
            t_s1b_r = f"{run_id}:s1b:{spec.slice_id}:retry1"
            ex_s1b_r = dispatcher.dispatch(
                CandidateRequest(
                    messages=(
                        ChatMessage("system", s1b_sys),
                        ChatMessage("user", retry_s1b_prompt),
                    ),
                    decoding=DecodingParamsV1(temperature=0.0),
                ),
                task_id=t_s1b_r,
                attempt_id=t_s1b_r,
            )
            s1b_raw = ex_s1b_r.get("content") or ""
            s1b_slots = _parse_int_slots(
                s1b_raw, expected_k=len(proj.chord_edges)
            )
            s1b_ok, s1b_mismatches = check_stage1b_chord_guard(proj, s1a_slots, s1b_slots)

        if not s1b_ok or s1b_slots is None:
            arm2_null_tree_count += 1
            arm2_calls += slice_s1_calls
            arm2_cases.append(
                {
                    "slice_id": spec.slice_id,
                    "stage1a_att1_passed": s1a_att1_ok,
                    "stage1a_final_passed": True,
                    "stage1b_att1_passed": s1b_att1_ok,
                    "stage1b_final_passed": False,
                    "stage1b_error": ex_s1b.get("error"),
                    "null_tree_abstention": True,
                    "provider_calls": slice_s1_calls,
                    "solved": False,
                }
            )
            arm3_cases.append(
                {
                    "slice_id": spec.slice_id,
                    "null_tree_abstention": True,
                    "completed_stages": [],
                    "final_terminal_status": "ABSTAINED_NULL_TREE",
                    "solved": False,
                }
            )
            continue

        arm2_s1b_final_pass += 1

        # Build the Coloured Operad `o_i` slot-grafted prompt container from verified `P*` basis
        operad_prompt, rendered_operad, mat_summary = build_grafted_operad_prompt(
            spec, proj, s1a_slots, s1b_slots
        )
        assert isinstance(rendered_operad, str)

        # --- Arm 2 Stage 2: Direct Coloured Operad Slot-Grafted Extraction (1 turn) ---
        sys_s2, usr_s2 = build_stage2_operad_extraction_prompt(
            spec, rendered_operad, mat_summary
        )
        t_s2 = f"{run_id}:arm2_s2:{spec.slice_id}:att1"
        ex_s2 = dispatcher.dispatch(
            CandidateRequest(
                messages=(
                    ChatMessage("system", sys_s2),
                    ChatMessage("user", usr_s2),
                ),
                decoding=DecodingParamsV1(temperature=0.0),
            ),
            task_id=t_s2,
            attempt_id=t_s2,
        )
        arm2_slice_calls = slice_s1_calls + 1
        arm2_calls += arm2_slice_calls
        s2_raw = ex_s2.get("content") or ""
        s2_parsed = extract_json_object(s2_raw)
        s2_passed, s2_failures, s2_node_checks = verify_derivation_candidate(proj, s2_parsed)
        if s2_passed:
            arm2_solved += 1
        arm2_cases.append(
            {
                "slice_id": spec.slice_id,
                "stage1a_att1_passed": s1a_att1_ok,
                "stage1a_final_passed": True,
                "stage1a_prompt": s1a_prompt,
                "stage1a_raw_reply": s1a_raw,
                "stage1a_typed_slots": list(s1a_slots),
                "stage1a_elapsed_sec": ex_s1a.get("elapsed"),
                "stage1b_att1_passed": s1b_att1_ok,
                "stage1b_final_passed": True,
                "stage1b_prompt": s1b_prompt,
                "stage1b_raw_reply": s1b_raw,
                "stage1b_typed_slots": list(s1b_slots),
                "stage1b_elapsed_sec": ex_s1b.get("elapsed"),
                "rendered_operad_prompt": rendered_operad,
                "stage2_system_prompt": sys_s2,
                "stage2_user_prompt": usr_s2,
                "stage2_raw_reply": s2_raw,
                "stage2_typed_response": s2_parsed,
                "stage2_elapsed_sec": ex_s2.get("elapsed"),
                "stage2_error": ex_s2.get("error"),
                "null_tree_abstention": False,
                "provider_calls": arm2_slice_calls,
                "solved": s2_passed,
                "failures": list(s2_failures),
                "node_checks": s2_node_checks,
            }
        )

        # --- Arm 3: Full `pfp-staged.0.3` (`ExecuteStagePipelineUseCase`, Stages 1..11) ---
        stage_provider = AccountedPfpStageProvider(
            dispatcher=dispatcher,
            model=model,
            task_prefix=f"{run_id}:arm3:{spec.slice_id}",
            max_output_tokens=max_output_tokens,
        )
        verifier = DerivationDagHostVerifier(projections)
        pipeline_uc = ExecuteStagePipelineUseCase(
            storage=storage,
            provider=stage_provider,
            catalog=catalog,
            host_verifier=verifier,
        )
        initial_seed = {
            "slice_id": spec.slice_id,
            "declaration": {
                "grammar": "derivation_dag_finite_qm_certificate_v1",
                "equality_test": "exact_integer_and_rational_tuple_equality",
                "coefficient_profile": "Z_and_Q_exact_cochain_v1",
            },
            "operad_p_star_compiled_container": {
                "operad_prompt_id": operad_prompt.prompt_id,
                "rendered_operad_prompt": rendered_operad,
                "materialized_derivation_values": mat_summary,
                "dropped_distractor_count": len(proj.dropped_distractor_lines),
            },
        }
        pipe_res = pipeline_uc.run_pipeline(
            spec.slice_id,
            initial_seed,
            candidate_schema=cand_schema,
        )
        arm3_pipeline_model_calls += len(stage_provider.call_records)
        if pipe_res.is_ok:
            receipt = pipe_res.unwrap()
            stage4_cand = receipt.stage_responses.get(4, {}).get("candidate")
            p_ok, p_failures, p_node_checks = verify_derivation_candidate(proj, stage4_cand)
            if p_ok:
                arm3_solved += 1
            if (
                receipt.all_stages_passed
                and receipt.final_terminal_status == TerminalStatus.VERIFIED
            ):
                arm3_verified_terminals += 1
            arm3_cases.append(
                {
                    "slice_id": spec.slice_id,
                    "null_tree_abstention": False,
                    "stage1_basis_calls": slice_s1_calls,
                    "pfp_staged_model_calls": len(stage_provider.call_records),
                    "total_calls_including_p_star": slice_s1_calls + len(stage_provider.call_records),
                    "completed_stages": list(receipt.completed_stages),
                    "all_stages_passed": receipt.all_stages_passed,
                    "final_terminal_status": receipt.final_terminal_status.value,
                    "stage_responses": {
                        str(k): v for k, v in receipt.stage_responses.items()
                    },
                    "stage5_verdict": receipt.stage_responses.get(5),
                    "stage7_challenge_replay": receipt.stage_responses.get(7),
                    "stage8_selection": receipt.stage_responses.get(8),
                    "stage9_receipt": receipt.stage_responses.get(9),
                    "stage10_hand_off": receipt.stage_responses.get(10),
                    "stage11_record": receipt.stage_responses.get(11),
                    "solved": p_ok,
                    "failures": list(p_failures),
                    "node_checks": p_node_checks,
                    "model_call_records": stage_provider.call_records,
                }
            )
        else:
            err = pipe_res.unwrap_err()
            arm3_cases.append(
                {
                    "slice_id": spec.slice_id,
                    "null_tree_abstention": False,
                    "stage1_basis_calls": slice_s1_calls,
                    "pfp_staged_model_calls": len(stage_provider.call_records),
                    "total_calls_including_p_star": slice_s1_calls + len(stage_provider.call_records),
                    "completed_stages": [],
                    "all_stages_passed": False,
                    "final_terminal_status": f"ERROR_{err.code.name}_STAGE_{err.stage}",
                    "error_message": err.message,
                    "solved": False,
                    "model_call_records": stage_provider.call_records,
                }
            )

    # --- Arm 1: Un-staged 1-shot derivation certificate generation ---
    arm1_cases: list[dict[str, Any]] = []
    arm1_solved = 0
    arm1_calls = 0
    arm1_node_pass_counts: dict[str, int] = {}

    for spec in slices:
        proj = projections[spec.slice_id]
        sys_p, usr_p = build_unstaged_1shot_prompt(spec)
        arm1_calls += 1
        task_id = f"{run_id}:arm1:{spec.slice_id}"
        attempt_id = f"{task_id}:att1"
        exchange = dispatcher.dispatch(
            CandidateRequest(
                messages=(
                    ChatMessage("system", sys_p),
                    ChatMessage("user", usr_p),
                ),
                decoding=DecodingParamsV1(temperature=0.0),
            ),
            task_id=task_id,
            attempt_id=attempt_id,
        )
        raw_reply = exchange.get("content") or ""
        parsed = extract_json_object(raw_reply)
        passed, failures, node_checks = verify_derivation_candidate(proj, parsed)
        if passed:
            arm1_solved += 1
        for k, v in node_checks.items():
            arm1_node_pass_counts[k] = arm1_node_pass_counts.get(k, 0) + (1 if v else 0)
        arm1_cases.append(
            {
                "slice_id": spec.slice_id,
                "perturbed_edge": list(spec.perturbed_edge),
                "perturbed_edge_kind": spec.perturbed_edge_kind,
                "provider_calls": 1,
                "elapsed_sec": exchange.get("elapsed"),
                "error": exchange.get("error"),
                "parsed_json": parsed is not None,
                "solved": passed,
                "failures": list(failures),
                "node_checks": node_checks,
                "system_prompt": sys_p,
                "user_prompt": usr_p,
                "raw_reply": raw_reply,
                "typed_response": parsed,
                "submitted_repaired_edge": parsed.get("repaired_edge") if isinstance(parsed, Mapping) else None,
                "submitted_repaired_value": parsed.get("repaired_value") if isinstance(parsed, Mapping) else None,
                "submitted_route_status": (
                    parsed.get("route_l1_r_residual_to_weights_status")
                    if isinstance(parsed, Mapping)
                    else None
                ),
                "submitted_tree_potentials": (
                    parsed.get("tree_potentials") if isinstance(parsed, Mapping) else None
                ),
                "submitted_chord_syndromes": (
                    parsed.get("chord_syndromes") if isinstance(parsed, Mapping) else None
                ),
                "usage": exchange.get("usage"),
            }
        )

    return {
        "model": model,
        "run_id": run_id,
        "budget_cap_microusd": budget_cap_microusd,
        "provider_summary": {
            "dispatched_calls": dispatcher.dispatched_calls,
            "reserved_microusd": dispatcher.reserved_microusd,
            "settled_cost_microusd": dispatcher.settled_cost_microusd,
        },
        "arms": {
            "unstaged_1shot_derivation_dag": {
                "arm_id": "unstaged_1shot_derivation_dag",
                "provider_calls": arm1_calls,
                "solved_count": arm1_solved,
                "total_slices": len(slices),
                "solve_rate": arm1_solved / len(slices),
                "node_pass_counts": arm1_node_pass_counts,
                "cases": arm1_cases,
            },
            "p_star_2stage_operad_derivation_dag": {
                "arm_id": "p_star_2stage_operad_derivation_dag",
                "provider_calls": arm2_calls,
                "stage1a_att1_pass_count": arm2_s1a_att1_pass,
                "stage1a_final_pass_count": arm2_s1a_final_pass,
                "stage1b_att1_pass_count": arm2_s1b_att1_pass,
                "stage1b_final_pass_count": arm2_s1b_final_pass,
                "null_tree_abstentions": arm2_null_tree_count,
                "solved_count": arm2_solved,
                "total_slices": len(slices),
                "solve_rate": arm2_solved / len(slices),
                "conditional_stage2_precision": (
                    arm2_solved / arm2_s1b_final_pass if arm2_s1b_final_pass > 0 else 1.0
                ),
                "cases": arm2_cases,
            },
            "operad_p_star_pfp_staged_0_3": {
                "arm_id": "operad_p_star_pfp_staged_0_3",
                "pfp_staged_model_calls": arm3_pipeline_model_calls,
                "total_calls_including_shared_p_star": (
                    (arm2_calls - len(slices)) + arm3_pipeline_model_calls
                ),
                "solved_count": arm3_solved,
                "pfp_staged_0_3_verified_count": arm3_verified_terminals,
                "total_slices": len(slices),
                "solve_rate": arm3_solved / len(slices),
                "verified_terminal_rate": arm3_verified_terminals / len(slices),
                "cases": arm3_cases,
            },
        },
    }


def _build_receipt_payload(
    dag_meta: dict[str, Any],
    slices: list[DerivationSliceSpec],
    projections: dict[str, CarrierProjectionReceipt],
    no_llm_result: dict[str, Any],
    live_campaigns: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "core.pfp.derivation_dag_pfp_staged_receipt.v1",
        "trial_id": "DAG-QM-S1",
        "protocol_sha256": PROTOCOL_SHA256,
        "authority_effect": "None",
        "stage_controller_version": "pfp-staged.0.3",
        "derivation_dag_metadata": dag_meta,
        "slice_summaries": [
            {
                "slice_id": s.slice_id,
                "title": s.title,
                "num_vertices": len(s.items),
                "num_edges": len(s.edges),
                "tree_rank": len(s.tree_edges),
                "cycle_rank_b1": len(s.chord_edges),
                "perturbed_edge": list(s.perturbed_edge),
                "perturbed_edge_kind": s.perturbed_edge_kind,
                "true_repaired_value": s.true_repaired_value,
                "perturbation_shift": s.perturbation_shift,
                "dropped_distractor_count": len(projections[s.slice_id].dropped_distractor_lines),
                "expected_certificate": projections[s.slice_id].expected_certificate,
            }
            for s in slices
        ],
        "no_llm_baseline": no_llm_result,
        "live_campaigns": live_campaigns,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Finite-QM Derivation DAG + Coloured Operad + P* + pfp-staged.0.3 benchmark."
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["deepseek/deepseek-v4-flash", "deepseek/deepseek-v4.1-flash"],
        help="OpenRouter models to evaluate.",
    )
    parser.add_argument(
        "--budget-cap-microusd",
        type=int,
        default=DEFAULT_BUDGET_CAP_MICROUSD,
        help="Per-model budget cap in micro-USD.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_RECEIPT_PATH,
        help="Output receipt JSON path.",
    )
    parser.add_argument(
        "--no-llm-only",
        action="store_true",
        help="Run only the deterministic NO_LLM baseline.",
    )
    args = parser.parse_args()

    dag_meta = load_derivation_dag_metadata()
    slices = build_derivation_dag_slices()
    projections = {s.slice_id: project_carrier_from_raw_prompt(s) for s in slices}

    no_llm_result = run_no_llm_baseline(slices, projections)

    work_dir = Path(__file__).resolve().parent / "_tmp_dag_pfp_staged_run"
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    live_campaigns: dict[str, Any] = {}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        if not args.no_llm_only:
            for model in args.models:
                live_campaigns[model] = run_live_model_campaign(
                    model=model,
                    slices=slices,
                    projections=projections,
                    budget_cap_microusd=args.budget_cap_microusd,
                    work_dir=work_dir,
                )
                partial_receipt = _build_receipt_payload(
                    dag_meta=dag_meta,
                    slices=slices,
                    projections=projections,
                    no_llm_result=no_llm_result,
                    live_campaigns=live_campaigns,
                )
                args.output.write_text(
                    json.dumps(partial_receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    receipt = _build_receipt_payload(
        dag_meta=dag_meta,
        slices=slices,
        projections=projections,
        no_llm_result=no_llm_result,
        live_campaigns=live_campaigns,
    )
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote receipt to {args.output}")
    print(
        f"NO_LLM baseline: {no_llm_result['solved_count']}/{no_llm_result['total_slices']} solved, "
        f"{no_llm_result['pfp_staged_0_3_verified_count']}/{no_llm_result['total_slices']} VERIFIED"
    )
    for model, camp in live_campaigns.items():
        arms = camp["arms"]
        a1 = arms["unstaged_1shot_derivation_dag"]
        a2 = arms["p_star_2stage_operad_derivation_dag"]
        a3 = arms["operad_p_star_pfp_staged_0_3"]
        print(
            f"[{model}] calls={camp['provider_summary']['dispatched_calls']} "
            f"reserved={camp['provider_summary']['reserved_microusd']}uUSD | "
            f"Arm1(1-shot)={a1['solved_count']}/{a1['total_slices']} | "
            f"Arm2(P* 2-stage Operad)={a2['solved_count']}/{a2['total_slices']} | "
            f"Arm3(P* + pfp-staged.0.3 VERIFIED)={a3['pfp_staged_0_3_verified_count']}/{a3['total_slices']}"
        )


if __name__ == "__main__":
    main()
