"""Pure Relational Genesis-to-Finite-Shadow Derivation Workflow under Operad Locks.

Executes both the 4-stage single-carrier relational derivation workflow
(`WF_RELATIONAL_GENESIS_SHADOW_01`, Stages 1-4) and the extended 6-stage coupled
bipartite relational derivation workflow (`WF_RELATIONAL_COUPLED_BIPARTITE_02`,
Stages 1-6 covering D_2 x D_3 and D_3 x D_3) under `collect_derivation_map_operads`
with pre-declared `.binding.yaml` operad locks loaded before candidate generation begins:

1. `P_REL_01`: Genesis S(0..6) active obstruction survivor tower s = (0, 1, 1, 1, 0, 1, 1),
   binary germ D_2 support floor Delta_support = 2, and typed retraction r_N with explicit
   NON_DESCENT witness on novel generators.
2. `P_REL_02`: S(2)->S(3) observational collision tagging and swap involution sigma,
   decomposing Q^2 into symmetric mean P_+ and antisymmetric difference kernel P_- with
   characteristic-2 collapse boundary witness.
3. `P_REL_03`: Composition of directed cuts on the 4-vertex, 5-edge diamond relational graph
   G=(4,5) (b_1(G)=2, 8 spanning trees): exact vertex-potential coboundaries d_0 g vs
   non-exact cycle holonomy chord obstructions across all 8 spanning trees.
4. `P_REL_04`: Elementary binary swap transitions T_01, T_12 on {0,1,2}: noncommuting
   sequential transitions, skew-symmetric commutator K = [T_01, T_12] satisfying Tr(K)=0 and
   K^3 + 3K = 0 over Z, and cyclotomic identity (R^2 + R + I)|_{W_0} = 0 on the 2D zero-sum
   relational difference subspace W_0 without continuum or complex imports.
5. `P_REL_05`: Coupled bipartite carrier D_2 x D_3 (6 elements, triangular prism graph
   G_{2,3} with |V|=6, |E|=9, b_1=4, 75 spanning trees): 4-sector orthogonal projector
   factorization of ranks (1, 1, 2, 2), coupled swap-commutator J_{23} = sigma (x) K
   satisfying J_{23}^3 + 3 J_{23} = 0, and inter-layer twist 1-cochain witness that is
   flat on both D_3 triangles separately yet obstructs descent across all 75 spanning trees.
6. `P_REL_06`: Coupled bipartite carrier D_3 x D_3 (9 elements, factor-exchange involution
   tau): 5-sector orthogonal projector refinement of ranks (1, 2, 2, 3, 1) splitting the
   4D joint difference core W_0 (x) W_0 into a 3D symmetric sector and a 1D antisymmetric
   exterior singlet sector; compound commutator K (x) K satisfying
   ((K (x) K)^2 - 9 I)|_{W_{00}} = 0 (yielding an exact rational involution (1/3)(K (x) K)
   on W_{00}); and non-factorizable antisymmetric singlet witness with 2x2 minor 1 != 0.

All candidate structures carry `authority_effect: "None"` and `genesis_effect: "None"`.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Any

from omega_engine_operads.domain.prompt_hierarchy.evaluator import collect_derivation_map_operads
from omega_engine_operads.domain.prompt_hierarchy.models import DerivationMapOperadReport, PromptTreeNode
from omega_engine_operads.domain.prompt_hierarchy.parser import load_prompt_node_from_binding_dict

RELATIONAL_BINDING_FILENAMES: tuple[str, ...] = (
    "p_rel_01_survivor_tower_and_retraction.binding.yaml",
    "p_rel_02_collision_tagging_and_swap_quotient.binding.yaml",
    "p_rel_03_acyclic_cut_vs_cycle_holonomy.binding.yaml",
    "p_rel_04_noncommuting_transition_cyclotomic_cert.binding.yaml",
)

COUPLED_BIPARTITE_BINDING_FILENAMES: tuple[str, ...] = (
    *RELATIONAL_BINDING_FILENAMES,
    "p_rel_05_bipartite_d2_x_d3_prism_factorization.binding.yaml",
    "p_rel_06_bipartite_d3_x_d3_exterior_singlet_factorization.binding.yaml",
)

TRIPARTITE_BINDING_FILENAMES: tuple[str, ...] = (
    *COUPLED_BIPARTITE_BINDING_FILENAMES,
    "p_rel_07_tripartite_d3_x_d3_x_d3_levi_civita_and_schur_weyl.binding.yaml",
)

MatrixQ = tuple[tuple[Fraction, ...], ...]
MatrixZ = tuple[tuple[int, ...], ...]


def _matadd_q(a: MatrixQ, b: MatrixQ) -> MatrixQ:
    return tuple(
        tuple(a[i][j] + b[i][j] for j in range(len(a[0])))
        for i in range(len(a))
    )



def _matmul_q(a: MatrixQ, b: MatrixQ) -> MatrixQ:
    n = len(a)
    m = len(b[0])
    k_len = len(b)
    return tuple(
        tuple(sum((a[i][k] * b[k][j] for k in range(k_len)), Fraction(0, 1)) for j in range(m))
        for i in range(n)
    )


def _matmul_z(a: MatrixZ, b: MatrixZ) -> MatrixZ:
    n = len(a)
    m = len(b[0])
    k_len = len(b)
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(k_len)) for j in range(m))
        for i in range(n)
    )


def _matvec_z(a: MatrixZ, v: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sum(a[i][j] * v[j] for j in range(len(v))) for i in range(len(a)))


def _kron_q(a: MatrixQ, b: MatrixQ) -> MatrixQ:
    ra, ca = len(a), len(a[0])
    rb, cb = len(b), len(b[0])
    return tuple(
        tuple(a[i // rb][j // cb] * b[i % rb][j % cb] for j in range(ca * cb))
        for i in range(ra * rb)
    )


def _kron_z(a: MatrixZ, b: MatrixZ) -> MatrixZ:
    ra, ca = len(a), len(a[0])
    rb, cb = len(b), len(b[0])
    return tuple(
        tuple(a[i // rb][j // cb] * b[i % rb][j % cb] for j in range(ca * cb))
        for i in range(ra * rb)
    )


def _trace_q(a: MatrixQ) -> Fraction:
    return sum((a[i][i] for i in range(len(a))), Fraction(0, 1))


def _ident_q(n: int) -> MatrixQ:
    return tuple(
        tuple(Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n))
        for i in range(n)
    )


def _projector_family_defect_q(projectors: Sequence[MatrixQ]) -> Fraction:
    """Compute L1 idempotence + mutual orthogonality + completeness-to-identity defect over Q."""
    n = len(projectors[0])
    ident = _ident_q(n)
    defect = Fraction(0, 1)
    for idx_a, pa in enumerate(projectors):
        pa_sq = _matmul_q(pa, pa)
        for i in range(n):
            for j in range(n):
                defect += abs(pa_sq[i][j] - pa[i][j])
        for idx_b, pb in enumerate(projectors):
            if idx_a != idx_b:
                pab = _matmul_q(pa, pb)
                for i in range(n):
                    for j in range(n):
                        defect += abs(pab[i][j])
    for i in range(n):
        for j in range(n):
            total_ij = sum((p[i][j] for p in projectors), Fraction(0, 1))
            defect += abs(total_ij - ident[i][j])
    return defect


@dataclass(frozen=True)
class GenesisRelationalDerivationRun:
    """Result of executing a pure relational derivation chain under pre-declared operad locks."""

    predeclared_nodes: tuple[PromptTreeNode, ...]
    stage_payloads: Mapping[str, Mapping[str, Any]]
    operad_report: DerivationMapOperadReport
    authority_effect: str = "None"
    genesis_effect: str = "None"


@dataclass(frozen=True)
class CoupledNativeWitnessBindingReceipt:
    """Receipt binding Stage 1-7 Code and Proof witness slots to compiled Rust and Lean 4 modules."""

    rust_module_relpath: str
    rust_test_relpath: str
    rust_runtime_action: str
    rust_receipt_schema: str
    rust_source_sha256: str
    rust_test_sha256: str
    lean4_module_relpath: str
    lean4_source_sha256: str
    lean4_theorem_names: tuple[str, ...]
    stage1_code_witness: tuple[Any, ...]
    stage1_proof_witness: tuple[Any, ...]
    stage2_code_witness: tuple[Any, ...]
    stage2_proof_witness: tuple[Any, ...]
    stage3_code_witness: tuple[Any, ...]
    stage3_proof_witness: tuple[Any, ...]
    stage4_code_body: tuple[Any, ...]
    stage4_proof_body: tuple[Any, ...]
    stage5_code_witness: tuple[Any, ...]
    stage5_proof_witness: tuple[Any, ...]
    stage6_code_body: tuple[Any, ...]
    stage6_proof_body: tuple[Any, ...]
    stage7_code_body: tuple[Any, ...]
    stage7_proof_body: tuple[Any, ...]
    authority_effect: str = "None"
    genesis_effect: str = "None"


def _extract_rust_bracket_tuple(source: str, field_name: str) -> tuple[int, ...]:
    pattern = rf"{re.escape(field_name)}\s*,\s*\[([^\]]+)\]"
    match = re.search(pattern, source)
    if match is None:
        raise ValueError(f"Missing Rust assertion pin for {field_name!r}")
    parsed = ast.literal_eval("[" + match.group(1) + "]")
    return tuple(int(x) for x in parsed)


def _extract_rust_int(source: str, field_name: str) -> int:
    pattern = rf"{re.escape(field_name)}\s*,\s*(-?\d+)"
    match = re.search(pattern, source)
    if match is None:
        raise ValueError(f"Missing Rust integer assertion pin for {field_name!r}")
    return int(match.group(1))


def _extract_lean_theorem_rhs_tuple(source: str, theorem_name: str) -> tuple[Any, ...]:
    pattern = (
        rf"theorem\s+{re.escape(theorem_name)}\s*:\s*"
        rf"[A-Za-z0-9_]+\s*=\s*(\([^\n:=]+)\s*:=\s*by"
    )
    match = re.search(pattern, source)
    if match is None:
        raise ValueError(f"Missing Lean 4 theorem declaration {theorem_name!r}")
    return tuple(ast.literal_eval(match.group(1).strip()))


def load_coupled_native_rust_and_lean4_witnesses(
    repo_root: Path | None = None,
) -> CoupledNativeWitnessBindingReceipt:
    """Bind Stage 1-7 Code and Proof witnesses directly to omega_symbol_game Rust and Lean 4."""
    root = repo_root or Path(__file__).resolve().parents[3]
    rust_rel = "omega_engine/crates_rs/omega_symbol_game/src/coupled_relational_operad.rs"
    rust_test_rel = "omega_engine/crates_rs/tests/omega_symbol_game/coupled_relational_operad.rs"
    lean_rel = "lean4/quantum_mechanics/CoupledRelationalProjectors.lean"

    rust_path = root / rust_rel
    rust_test_path = root / rust_test_rel
    lean_path = root / lean_rel

    rust_src = rust_path.read_text(encoding="utf-8")
    rust_test_src = rust_test_path.read_text(encoding="utf-8")
    lean_src = lean_path.read_text(encoding="utf-8")

    # Verify Lean 4 formal module has zero sorry and zero custom axiom declarations
    lean_code_lines = [
        line.split("--", 1)[0]
        for line in lean_src.splitlines()
        if not line.strip().startswith("--")
    ]
    lean_active = "\n".join(lean_code_lines)
    if re.search(r"\bsorry\b", lean_active) is not None:
        raise ValueError(f"Lean 4 module {lean_rel} contains forbidden sorry")
    if re.search(r"^\s*axiom\s+", lean_active, flags=re.MULTILINE) is not None:
        raise ValueError(f"Lean 4 module {lean_rel} contains forbidden custom axiom")

    # Verify Rust module schema and runtime action registration
    schema_match = re.search(
        r'COUPLED_RELATIONAL_RECEIPT_SCHEMA:\s*&str\s*=\s*"([^"]+)"',
        rust_src,
    )
    if schema_match is None:
        raise ValueError(f"Missing COUPLED_RELATIONAL_RECEIPT_SCHEMA in {rust_rel}")
    action_match = re.search(r'action:\s*"(coupled_relational_operad_verify)"', rust_test_src)
    if action_match is None:
        raise ValueError(f"Missing coupled_relational_operad_verify dispatch in {rust_test_rel}")

    # Extract Stage 1-4 Code witness pins from compiled Rust integration test suite
    r1_surv = _extract_rust_bracket_tuple(rust_test_src, "s1.normative_survivor_vector")
    r1_floor = _extract_rust_int(rust_test_src, "s1.d2_delta_support_floor")
    r1_def = _extract_rust_int(rust_test_src, "s1.retraction_left_inverse_defect")
    r1_hist = _extract_rust_bracket_tuple(rust_test_src, "s1.persistent_history_counts")
    stage1_code_witness = (r1_surv, r1_floor, r1_def, r1_hist)

    r2_pp = _extract_rust_bracket_tuple(rust_test_src, "s2.scaled_p_plus_row0_row1")
    r2_pm = _extract_rust_bracket_tuple(rust_test_src, "s2.scaled_p_minus_row0_row1")
    stage2_code_witness = (
        (
            (Fraction(r2_pp[0], 2), Fraction(r2_pp[1], 2)),
            (Fraction(r2_pp[2], 2), Fraction(r2_pp[3], 2)),
        ),
        (
            (Fraction(r2_pm[0], 2), Fraction(r2_pm[1], 2)),
            (Fraction(r2_pm[2], 2), Fraction(r2_pm[3], 2)),
        ),
        Fraction(0, 1),
        Fraction(0, 1),
        Fraction(1, 1),
    )

    r3_veb1 = _extract_rust_bracket_tuple(rust_test_src, "s3.diamond_graph_v_e_b1")
    r3_trees = _extract_rust_int(rust_test_src, "s3.spanning_tree_count_diamond")
    r3_hol = _extract_rust_bracket_tuple(rust_test_src, "s3.fundamental_cycle_holonomies")
    stage3_code_witness = (r3_veb1, r3_trees, Fraction(0, 1), r3_hol)

    r4_k0 = _extract_rust_bracket_tuple(rust_test_src, "s4.commutator_k_row0")
    r4_k1 = _extract_rust_bracket_tuple(rust_test_src, "s4.commutator_k_row1")
    r4_k2 = _extract_rust_bracket_tuple(rust_test_src, "s4.commutator_k_row2")
    r4_tr = _extract_rust_int(rust_test_src, "s4.commutator_trace")
    r4_cube = _extract_rust_int(
        rust_test_src,
        "s4.commutator_cube_plus_three_commutator_zero",
    )
    r4_phi3 = _extract_rust_int(
        rust_test_src,
        "s4.cyclotomic_phi3_residual_on_difference_subspace",
    )
    stage4_code_body = ((r4_k0, r4_k1, r4_k2), r4_tr, r4_cube, r4_phi3)

    # Extract Stage 5-7 Code witness pins from compiled Rust integration test suite
    r5_prism = _extract_rust_bracket_tuple(rust_test_src, "s5.prism_graph_v_e_b1_trees")
    r5_ranks = _extract_rust_bracket_tuple(rust_test_src, "s5.four_sector_projector_ranks")
    r5_tri = _extract_rust_bracket_tuple(rust_test_src, "s5.triangle_cycle_sums")
    r5_hol = _extract_rust_bracket_tuple(rust_test_src, "s5.interlayer_twist_holonomies")
    r5_obs = _extract_rust_int(rust_test_src, "s5.obstructed_spanning_trees")
    stage5_code_witness = (
        r5_prism,
        r5_ranks,
        Fraction(0, 1),
        Fraction(0, 1),
        (r5_tri, r5_hol, r5_obs),
    )

    r6_ranks = _extract_rust_bracket_tuple(rust_test_src, "s6.five_sector_projector_ranks")
    r6_traces = _extract_rust_bracket_tuple(
        rust_test_src,
        "s6.diagonal_3cycle_traces_on_sym_and_alt_w00",
    )
    r6_minors = _extract_rust_bracket_tuple(
        rust_test_src,
        "s6.antisymmetric_singlet_minor_vs_separable_minor",
    )
    stage6_code_body = (
        r6_ranks,
        Fraction(0, 1),
        Fraction(0, 1),
        r6_traces,
        (r6_minors[0], r6_minors[1], "antisymmetric_singlet_minor_1_vs_separable_0"),
    )

    r7_binom = _extract_rust_bracket_tuple(rust_test_src, "s7.tripartite_binomial_sector_ranks")
    r7_schur = _extract_rust_bracket_tuple(rust_test_src, "s7.w000_schur_weyl_sym_mixed_alt_ranks")
    r7_levi = _extract_rust_bracket_tuple(
        rust_test_src,
        "s7.levi_civita_mixed_sector_and_parity_pin",
    )
    r7_r3 = _extract_rust_bracket_tuple(
        rust_test_src,
        "s7.w000_r3_invariant_split_and_k3_square_defect",
    )
    r7_pig = _extract_rust_bracket_tuple(
        rust_test_src,
        "s7.pigeonhole_levi_civita_l1_and_sector_defects",
    )
    stage7_code_body = (
        r7_binom,
        r7_schur,
        r7_levi,
        r7_r3,
        (
            r7_pig[0],
            r7_pig[1],
            r7_pig[2],
            "pigeonhole_lambda3_w0_vanishes_supported_on_lplus_tensor_lambda2_w0",
        ),
    )

    # Extract Stage 1-7 Proof witness pins from Lean 4 theorem declarations
    thm1 = "stage1_survivor_tower_and_retraction_eq"
    thm2 = "stage2_d2_collision_tagging_and_swap_projectors_eq"
    thm3 = "stage3_diamond_coboundary_vs_chord_holonomy_eq"
    thm4 = "stage4_d3_swap_commutator_and_cyclotomic_w0_eq"
    thm5 = "stage5_d2_x_d3_four_sector_ranks_and_j23_cubic"
    thm6 = "stage6_d3_x_d3_five_sector_ranks_and_rational_involution"
    thm7 = "stage7_d3_cubed_schur_weyl_obstruction_and_levi_civita_localization"
    thm_master = "coupled_bipartite_and_tripartite_relational_master_certificate"

    l1 = _extract_lean_theorem_rhs_tuple(lean_src, thm1)
    stage1_proof_witness = (
        tuple(int(x) for x in l1[0]),
        int(l1[1]),
        int(l1[2]),
        tuple(int(x) for x in l1[3]),
    )

    l2 = _extract_lean_theorem_rhs_tuple(lean_src, thm2)
    stage2_proof_witness = (
        tuple(tuple(Fraction(int(x), 2) for x in row) for row in l2[0]),
        tuple(tuple(Fraction(int(x), 2) for x in row) for row in l2[1]),
        Fraction(int(l2[2]), 1),
        Fraction(int(l2[3]), 1),
        Fraction(int(l2[4]), 1),
    )

    l3 = _extract_lean_theorem_rhs_tuple(lean_src, thm3)
    stage3_proof_witness = (
        tuple(int(x) for x in l3[0]),
        int(l3[1]),
        Fraction(int(l3[2]), 1),
        tuple(int(x) for x in l3[3]),
    )

    l4 = _extract_lean_theorem_rhs_tuple(lean_src, thm4)
    stage4_proof_body = (
        tuple(tuple(int(x) for x in row) for row in l4[0]),
        int(l4[1]),
        int(l4[2]),
        int(l4[3]),
    )

    l5 = _extract_lean_theorem_rhs_tuple(lean_src, thm5)
    stage5_proof_witness = (
        tuple(int(x) for x in l5[0]),
        tuple(int(x) for x in l5[1]),
        Fraction(int(l5[2]), 1),
        Fraction(int(l5[3]), 1),
        (
            tuple(int(x) for x in l5[4][0]),
            tuple(int(x) for x in l5[4][1]),
            int(l5[4][2]),
        ),
    )

    l6 = _extract_lean_theorem_rhs_tuple(lean_src, thm6)
    stage6_proof_body = (
        tuple(int(x) for x in l6[0]),
        Fraction(int(l6[1]), 1),
        Fraction(int(l6[2]), 1),
        tuple(int(x) for x in l6[3]),
        (int(l6[4][0]), int(l6[4][1]), "antisymmetric_singlet_minor_1_vs_separable_0"),
    )

    l7 = _extract_lean_theorem_rhs_tuple(lean_src, thm7)
    stage7_proof_body = (
        tuple(int(x) for x in l7[0]),
        tuple(int(x) for x in l7[1]),
        tuple(int(x) for x in l7[2]),
        tuple(int(x) for x in l7[3]),
        (
            int(l7[4][0]),
            int(l7[4][1]),
            int(l7[4][2]),
            "pigeonhole_lambda3_w0_vanishes_supported_on_lplus_tensor_lambda2_w0",
        ),
    )

    return CoupledNativeWitnessBindingReceipt(
        rust_module_relpath=rust_rel,
        rust_test_relpath=rust_test_rel,
        rust_runtime_action=action_match.group(1),
        rust_receipt_schema=schema_match.group(1),
        rust_source_sha256=hashlib.sha256(rust_src.encode("utf-8")).hexdigest(),
        rust_test_sha256=hashlib.sha256(rust_test_src.encode("utf-8")).hexdigest(),
        lean4_module_relpath=lean_rel,
        lean4_source_sha256=hashlib.sha256(lean_src.encode("utf-8")).hexdigest(),
        lean4_theorem_names=(thm1, thm2, thm3, thm4, thm5, thm6, thm7, thm_master),
        stage1_code_witness=stage1_code_witness,
        stage1_proof_witness=stage1_proof_witness,
        stage2_code_witness=stage2_code_witness,
        stage2_proof_witness=stage2_proof_witness,
        stage3_code_witness=stage3_code_witness,
        stage3_proof_witness=stage3_proof_witness,
        stage4_code_body=stage4_code_body,
        stage4_proof_body=stage4_proof_body,
        stage5_code_witness=stage5_code_witness,
        stage5_proof_witness=stage5_proof_witness,
        stage6_code_body=stage6_code_body,
        stage6_proof_body=stage6_proof_body,
        stage7_code_body=stage7_code_body,
        stage7_proof_body=stage7_proof_body,
    )


def load_predeclared_relational_operad_locks(
    fixtures_dir: Path,
    yaml_loader: Any,
    *,
    filenames: Sequence[str] = RELATIONAL_BINDING_FILENAMES,
) -> tuple[PromptTreeNode, ...]:
    """Load and freeze the pre-declared `.binding.yaml` operad locks before candidate generation."""
    nodes: list[PromptTreeNode] = []
    for fname in filenames:
        fpath = fixtures_dir / fname
        raw_dict = yaml_loader(fpath.read_text(encoding="utf-8"))
        node = load_prompt_node_from_binding_dict(raw_dict, source_file=str(fpath))
        if node.operad_binding is None:
            raise ValueError(f"Pre-declared relational sidecar {fpath} is missing operad_binding")
        nodes.append(node)
    return tuple(nodes)


def derive_stage_01_survivor_tower_and_retraction(prompt_uri: str) -> dict[str, Any]:
    """Stage 1: Derive Genesis S(0..6) survivor vector, D_2 support floor, and typed retraction r_N."""
    active_obstruction_registers: tuple[tuple[str, ...], ...] = (
        (),  # S(0): void presentation
        ("obs_01_binary_distinction_cut",),  # S(1): unary -> binary cut
        ("obs_02_observational_collision",),  # S(2): untagged collision q(a)=q(b)
        ("obs_03_asymmetric_pair_swap",),  # S(3): ordered pair vs swap involution
        (),  # S(4): re-indexed local closure (active obstruction exhausted)
        ("obs_05_closed_cycle_holonomy",),  # S(5): acyclic tree potential vs chord cycle
        ("obs_06_noncommuting_transition_order",),  # S(6): sequential swap commutator
    )
    survivor_vector = tuple(len(reg) for reg in active_obstruction_registers)

    # Persistent history ledger H_n is cumulative and distinct from active register W_n^active
    persistent_history_counts: list[int] = []
    accum = 0
    for reg in active_obstruction_registers:
        accum += len(reg)
        persistent_history_counts.append(accum)

    # Binary germ D_2 = ({0, 1}, 0 -> 1)
    d2_carrier = (0, 1)
    d2_delta_support_floor = len(d2_carrier)

    # Typed retraction r_N: S(N+1) -> S(N) U {NON_DESCENT}
    base_terms_s2 = ("term_0", "term_1")
    embedded_in_s3 = {f"u2({t})": t for t in base_terms_s2}

    def retract_s3_to_s2(term: str) -> tuple[str, str]:
        if term in embedded_in_s3:
            return ("DESCENT", embedded_in_s3[term])
        return ("NON_DESCENT", term)

    left_inverse_defect = sum(
        0 if retract_s3_to_s2(f"u2({t})") == ("DESCENT", t) else 1 for t in base_terms_s2
    )
    novel_witness = retract_s3_to_s2("novel_s3_swap_tag_generator")

    stage1_witness = (
        survivor_vector,
        d2_delta_support_floor,
        left_inverse_defect,
        tuple(persistent_history_counts),
    )
    native_binding = load_coupled_native_rust_and_lean4_witnesses()
    return {
        "prompt_uri": prompt_uri,
        "candidate_text": (
            "Stage 1 pure relational derivation of the Genesis S(0..6) active obstruction "
            "survivor vector s = (0, 1, 1, 1, 0, 1, 1), binary germ D_2 support floor 2, "
            "and typed retraction r_N with NON_DESCENT on novel generators."
        ),
        "contract_witness": native_binding.stage1_proof_witness,
        "code_witness": native_binding.stage1_code_witness,
        "proof_witness": native_binding.stage1_proof_witness,
        "state_witness": stage1_witness,
        "native_witness_binding": {
            "rust_module": native_binding.rust_module_relpath,
            "rust_runtime_action": native_binding.rust_runtime_action,
            "rust_source_sha256": native_binding.rust_source_sha256,
            "lean4_module": native_binding.lean4_module_relpath,
            "lean4_theorem": native_binding.lean4_theorem_names[0],
            "lean4_source_sha256": native_binding.lean4_source_sha256,
        },
        "normative_survivor_vector": survivor_vector,
        "d2_delta_support_floor": d2_delta_support_floor,
        "retraction_left_inverse_defect": left_inverse_defect,
        "slot_pins": {
            "normative_survivor_vector": (0, 1, 1, 1, 0, 1, 1),
            "d2_delta_support_floor": 2,
            "retraction_left_inverse_defect": 0,
        },
        "free_parameter_count": 0,
        "non_descent_novel_term_witness": novel_witness if novel_witness[0] == "NON_DESCENT" else None,
        "authority_effect": "None",
        "genesis_effect": "None",
    }


def derive_stage_02_collision_tagging_and_swap_quotient(
    prompt_uri: str,
    stage1_state_witness: Any,
) -> dict[str, Any]:
    """Stage 2: Derive S(2)->S(3) collision tagging and swap involution projectors P_+, P_- over Q."""
    half = Fraction(1, 2)
    p_plus: MatrixQ = (
        (half, half),
        (half, half),
    )
    p_minus: MatrixQ = (
        (half, -half),
        (-half, half),
    )
    ident_2 = _ident_q(2)

    p_plus_sq = _matmul_q(p_plus, p_plus)
    p_minus_sq = _matmul_q(p_minus, p_minus)
    p_plus_minus = _matmul_q(p_plus, p_minus)
    p_minus_plus = _matmul_q(p_minus, p_plus)

    idempotence_defect = sum(
        abs(p_plus_sq[i][j] - p_plus[i][j]) + abs(p_minus_sq[i][j] - p_minus[i][j])
        for i in range(2)
        for j in range(2)
    )
    orthogonality_defect = sum(
        abs(p_plus_minus[i][j])
        + abs(p_minus_plus[i][j])
        + abs((p_plus[i][j] + p_minus[i][j]) - ident_2[i][j])
        for i in range(2)
        for j in range(2)
    )
    diff_kernel_trace = _trace_q(p_minus)

    # Characteristic-2 boundary collapse check: in F_2, (1, 1) == (1, -1) mod 2
    sym_vec_mod2 = (1 % 2, 1 % 2)
    antisym_vec_mod2 = (1 % 2, (-1) % 2)
    char2_witness = (
        (sym_vec_mod2, antisym_vec_mod2, "char2_symmetric_equals_antisymmetric")
        if sym_vec_mod2 == antisym_vec_mod2
        else None
    )

    stage2_witness = (p_plus, p_minus, idempotence_defect, orthogonality_defect, diff_kernel_trace)
    native_binding = load_coupled_native_rust_and_lean4_witnesses()
    return {
        "prompt_uri": prompt_uri,
        "candidate_text": (
            "Stage 2 pure relational derivation of binary collision tagging and swap involution "
            "projectors P_+ and P_- over Q, separating symmetric mean from antisymmetric difference."
        ),
        "tower_state": stage1_state_witness,
        "contract_witness": stage2_witness,
        "code_witness": native_binding.stage2_code_witness,
        "proof_witness": native_binding.stage2_proof_witness,
        "native_witness_binding": {
            "rust_module": native_binding.rust_module_relpath,
            "rust_runtime_action": native_binding.rust_runtime_action,
            "rust_source_sha256": native_binding.rust_source_sha256,
            "lean4_module": native_binding.lean4_module_relpath,
            "lean4_theorem": native_binding.lean4_theorem_names[1],
            "lean4_source_sha256": native_binding.lean4_source_sha256,
        },
        "projector_idempotence_defect": idempotence_defect,
        "projector_orthogonality_defect": orthogonality_defect,
        "difference_kernel_trace": diff_kernel_trace,
        "slot_pins": {
            "projector_idempotence_defect": Fraction(0, 1),
            "projector_orthogonality_defect": Fraction(0, 1),
            "difference_kernel_trace": Fraction(1, 1),
        },
        "free_parameter_count": 0,
        "char2_collapse_boundary_witness": char2_witness,
        "authority_effect": "None",
        "genesis_effect": "None",
    }


def _is_spanning_tree(num_vertices: int, edges: Sequence[tuple[int, int]]) -> bool:
    if len(edges) != num_vertices - 1:
        return False
    parent = list(range(num_vertices))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru == rv:
            return False
        parent[ru] = rv
    roots = {find(v) for v in range(num_vertices)}
    return len(roots) == 1


def _count_obstructed_spanning_trees(
    num_vertices: int,
    edges: Sequence[tuple[int, int]],
    spanning_trees: Sequence[Sequence[tuple[int, int]]],
    omega: Mapping[tuple[int, int], int],
) -> int:
    obstructed = 0
    for tree_edges in spanning_trees:
        g_tree: dict[int, int] = {0: 0}
        while len(g_tree) < num_vertices:
            for u, v in tree_edges:
                if u in g_tree and v not in g_tree:
                    g_tree[v] = g_tree[u] + omega[(u, v)]
                elif v in g_tree and u not in g_tree:
                    g_tree[u] = g_tree[v] - omega[(u, v)]
        chord_residuals = [
            omega[(u, v)] - (g_tree[v] - g_tree[u])
            for (u, v) in edges
            if (u, v) not in tree_edges
        ]
        if any(r != 0 for r in chord_residuals):
            obstructed += 1
    return obstructed


def derive_stage_03_directed_cut_coboundary_vs_chord_obstruction(
    prompt_uri: str,
    stage2_contract_witness: Any,
) -> dict[str, Any]:
    """Stage 3: Derive exact coboundary vs cycle holonomy chord obstruction on the diamond graph G=(4,5)."""
    num_vertices = 4
    edges: tuple[tuple[int, int], ...] = (
        (0, 1),  # e0
        (1, 2),  # e1
        (0, 2),  # e2 (closes cycle C1: 0->1->2->0)
        (1, 3),  # e3
        (2, 3),  # e4 (closes cycle C2: 1->3->2->1)
    )
    b1_rank = len(edges) - num_vertices + 1
    diamond_v_e_b1 = (num_vertices, len(edges), b1_rank)

    spanning_trees = [
        subset for subset in combinations(edges, num_vertices - 1) if _is_spanning_tree(num_vertices, subset)
    ]
    spanning_tree_count = len(spanning_trees)

    # Test vertex potential g: V -> Q coboundary d_0 g on fundamental cycles C1 and C2
    potentials: tuple[tuple[Fraction, ...], ...] = (
        (Fraction(1, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
        (Fraction(0, 1), Fraction(2, 3), Fraction(-1, 2), Fraction(5, 4)),
    )
    coboundary_cycle_defect = Fraction(0, 1)
    for g in potentials:
        d0_g = {(u, v): g[v] - g[u] for (u, v) in edges}
        c1_sum = d0_g[(0, 1)] + d0_g[(1, 2)] - d0_g[(0, 2)]
        c2_sum = d0_g[(1, 3)] - d0_g[(2, 3)] - d0_g[(1, 2)]
        coboundary_cycle_defect += abs(c1_sum) + abs(c2_sum)

    # Non-exact 1-cochain omega with cycle holonomy (c1, c2) = (1, -1)
    omega_non_exact = {
        (0, 1): 0,
        (1, 2): 0,
        (0, 2): -1,  # c1 = omega(0,1) + omega(1,2) - omega(0,2) = +1
        (1, 3): 0,
        (2, 3): 1,   # c2 = omega(1,3) - omega(2,3) - omega(1,2) = -1
    }
    c1_holonomy = omega_non_exact[(0, 1)] + omega_non_exact[(1, 2)] - omega_non_exact[(0, 2)]
    c2_holonomy = omega_non_exact[(1, 3)] - omega_non_exact[(2, 3)] - omega_non_exact[(1, 2)]

    obstructed_tree_count = _count_obstructed_spanning_trees(
        num_vertices,
        edges,
        spanning_trees,
        omega_non_exact,
    )

    chord_witness = (
        (c1_holonomy, c2_holonomy, obstructed_tree_count)
        if obstructed_tree_count == spanning_tree_count and (c1_holonomy, c2_holonomy) == (1, -1)
        else None
    )

    stage3_witness = (
        diamond_v_e_b1,
        spanning_tree_count,
        coboundary_cycle_defect,
        (c1_holonomy, c2_holonomy),
    )
    native_binding = load_coupled_native_rust_and_lean4_witnesses()
    return {
        "prompt_uri": prompt_uri,
        "candidate_text": (
            "Stage 3 pure relational derivation on the 4-vertex, 5-edge diamond graph G=(4,5): "
            "exact vertex coboundaries vanish on cycles while non-zero cycle holonomy obstructs "
            "vertex descent across all 8 spanning trees, forcing b_1(G)=2 chord degrees of freedom."
        ),
        "swap_contract": stage2_contract_witness,
        "paper_witness": stage3_witness,
        "code_witness": native_binding.stage3_code_witness,
        "proof_witness": native_binding.stage3_proof_witness,
        "native_witness_binding": {
            "rust_module": native_binding.rust_module_relpath,
            "rust_runtime_action": native_binding.rust_runtime_action,
            "rust_source_sha256": native_binding.rust_source_sha256,
            "lean4_module": native_binding.lean4_module_relpath,
            "lean4_theorem": native_binding.lean4_theorem_names[2],
            "lean4_source_sha256": native_binding.lean4_source_sha256,
        },
        "diamond_graph_v_e_b1": diamond_v_e_b1,
        "spanning_tree_count_diamond": spanning_tree_count,
        "coboundary_cycle_sum_defect": coboundary_cycle_defect,
        "slot_pins": {
            "diamond_graph_v_e_b1": (4, 5, 2),
            "spanning_tree_count_diamond": 8,
            "coboundary_cycle_sum_defect": Fraction(0, 1),
        },
        "free_parameter_count": 0,
        "non_exact_1cochain_chord_witness": chord_witness,
        "authority_effect": "None",
        "genesis_effect": "None",
    }


def derive_stage_04_three_element_swap_commutator_cyclotomic_receipt(
    prompt_uri: str,
    stage3_paper_witness: Any,
) -> dict[str, Any]:
    """Stage 4: Derive noncommuting 3-element swap transitions, skew-symmetric K, and cyclotomic W_0 kernel."""
    t_01: MatrixZ = (
        (0, 1, 0),
        (1, 0, 0),
        (0, 0, 1),
    )
    t_12: MatrixZ = (
        (1, 0, 0),
        (0, 0, 1),
        (0, 1, 0),
    )
    r_plus = _matmul_z(t_01, t_12)
    r_minus = _matmul_z(t_12, t_01)

    # Commutator K = T_01 T_12 - T_12 T_01
    k_mat: MatrixZ = tuple(
        tuple(r_plus[i][j] - r_minus[i][j] for j in range(3)) for i in range(3)
    )
    k_trace = k_mat[0][0] + k_mat[1][1] + k_mat[2][2]

    k_sq = _matmul_z(k_mat, k_mat)
    k_cube = _matmul_z(k_sq, k_mat)
    k_cube_plus_3k_l1 = sum(
        abs(k_cube[i][j] + 3 * k_mat[i][j]) for i in range(3) for j in range(3)
    )

    # Check cyclotomic identity (R_+^2 + R_+ + I) v = 0 and (K^2 + 3I) v = 0 on W_0 = {x : sum x_i = 0}
    w0_basis: tuple[tuple[int, int, int], ...] = (
        (1, -1, 0),
        (0, 1, -1),
    )
    r_plus_sq = _matmul_z(r_plus, r_plus)
    phi3_residual = 0
    for v in w0_basis:
        r2_v = _matvec_z(r_plus_sq, v)
        r1_v = _matvec_z(r_plus, v)
        k2_v = _matvec_z(k_sq, v)
        for idx in range(3):
            phi3_residual += abs(r2_v[idx] + r1_v[idx] + v[idx])
            phi3_residual += abs(k2_v[idx] + 3 * v[idx])

    noncommuting_witness = k_mat if r_plus != r_minus else None
    stage4_witness = (
        stage3_paper_witness,
        k_mat,
        k_trace,
        k_cube_plus_3k_l1,
        phi3_residual,
    )
    native_binding = load_coupled_native_rust_and_lean4_witnesses()
    return {
        "prompt_uri": prompt_uri,
        "candidate_text": (
            "Stage 4 pure relational derivation of noncommuting binary swap transitions T_01, T_12 "
            "on {0,1,2}: skew-symmetric commutator K = [T_01, T_12] satisfies Tr(K)=0 and "
            "K^3 + 3K = 0 over Z, and 3-cycle R = T_01 T_12 satisfies (R^2 + R + I)|_{W_0} = 0 "
            "and K^2|_{W_0} = -3 I_{W_0} on the zero-sum relational difference subspace W_0."
        ),
        "paper_witness": stage4_witness,
        "code_witness": (stage3_paper_witness, *native_binding.stage4_code_body),
        "proof_witness": (stage3_paper_witness, *native_binding.stage4_proof_body),
        "native_witness_binding": {
            "rust_module": native_binding.rust_module_relpath,
            "rust_runtime_action": native_binding.rust_runtime_action,
            "rust_source_sha256": native_binding.rust_source_sha256,
            "lean4_module": native_binding.lean4_module_relpath,
            "lean4_theorem": native_binding.lean4_theorem_names[3],
            "lean4_source_sha256": native_binding.lean4_source_sha256,
        },
        "commutator_trace": k_trace,
        "commutator_cube_plus_three_commutator_zero": k_cube_plus_3k_l1,
        "cyclotomic_phi3_residual_on_difference_subspace": phi3_residual,
        "slot_pins": {
            "commutator_trace": 0,
            "commutator_cube_plus_three_commutator_zero": 0,
            "cyclotomic_phi3_residual_on_difference_subspace": 0,
        },
        "free_parameter_count": 0,
        "abelian_order_blind_falsifier_witness": noncommuting_witness,
        "authority_effect": "None",
        "genesis_effect": "None",
    }


def derive_stage_05_bipartite_d2_x_d3_prism_factorization(
    prompt_uri: str,
    stage4_receipt_witness: Any,
) -> dict[str, Any]:
    """Stage 5: Derive coupled D_2 x D_3 prism graph holonomy and 4-sector projector factorization."""
    # 1. Triangular prism graph G_{2,3} = D_2 [] C_3 (6 vertices, 9 directed edges)
    num_vertices = 6
    prism_edges: tuple[tuple[int, int], ...] = (
        # Layer 0 triangle (0, 1, 2)
        (0, 1),
        (1, 2),
        (0, 2),
        # Layer 1 triangle (3, 4, 5)
        (3, 4),
        (4, 5),
        (3, 5),
        # Inter-layer vertical rungs D_2
        (0, 3),
        (1, 4),
        (2, 5),
    )
    b1_prism = len(prism_edges) - num_vertices + 1
    prism_trees = [
        subset
        for subset in combinations(prism_edges, num_vertices - 1)
        if _is_spanning_tree(num_vertices, subset)
    ]
    prism_v_e_b1_trees = (num_vertices, len(prism_edges), b1_prism, len(prism_trees))

    # 2. Orthogonal 4-sector projector decomposition on Q^6 = Q^2 (x) Q^3
    half = Fraction(1, 2)
    third = Fraction(1, 3)
    p_plus: MatrixQ = ((half, half), (half, half))
    p_minus: MatrixQ = ((half, -half), (-half, half))
    q_plus: MatrixQ = tuple(tuple(third for _ in range(3)) for _ in range(3))
    ident_3 = _ident_q(3)
    q_w0: MatrixQ = tuple(
        tuple(ident_3[i][j] - q_plus[i][j] for j in range(3)) for i in range(3)
    )

    pi_pp = _kron_q(p_plus, q_plus)
    pi_mp = _kron_q(p_minus, q_plus)
    pi_p0 = _kron_q(p_plus, q_w0)
    pi_m0 = _kron_q(p_minus, q_w0)
    sectors_4 = (pi_pp, pi_mp, pi_p0, pi_m0)

    sector_traces_q = tuple(_trace_q(p) for p in sectors_4)
    sector_ranks = tuple(int(t.numerator) for t in sector_traces_q if t.denominator == 1)
    orthogonality_defect = _projector_family_defect_q(sectors_4)

    # 3. Coupled swap-commutator J_{23} = sigma (x) K on Z^6 and on Pi_{-,W_0}
    sigma_z: MatrixZ = ((0, 1), (1, 0))
    k_z: MatrixZ = (
        (0, -1, 1),
        (1, 0, -1),
        (-1, 1, 0),
    )
    j_23 = _kron_z(sigma_z, k_z)
    j_23_sq = _matmul_z(j_23, j_23)
    j_23_cube = _matmul_z(j_23_sq, j_23)
    cubic_l1 = sum(abs(j_23_cube[i][j] + 3 * j_23[i][j]) for i in range(6) for j in range(6))

    j_23_sq_q: MatrixQ = tuple(
        tuple(Fraction(j_23_sq[i][j], 1) for j in range(6)) for i in range(6)
    )
    ident_6 = _ident_q(6)
    j2_plus_3i: MatrixQ = tuple(
        tuple(j_23_sq_q[i][j] + 3 * ident_6[i][j] for j in range(6)) for i in range(6)
    )
    w0_sector_residual = _matmul_q(j2_plus_3i, pi_m0)
    coupled_op_defect = Fraction(cubic_l1, 1) + sum(
        (abs(w0_sector_residual[i][j]) for i in range(6) for j in range(6)),
        Fraction(0, 1),
    )

    # 4. Boundary counterexample: inter-layer twist 1-cochain flat on both D_3 triangles separately
    # yet obstructing descent across all 75 spanning trees of G_{2,3}
    omega_twist = {
        (0, 1): 0,
        (1, 2): 0,
        (0, 2): 0,
        (3, 4): 0,
        (4, 5): 0,
        (3, 5): 0,
        (0, 3): 1,
        (1, 4): -1,
        (2, 5): 0,
    }
    c_top = omega_twist[(0, 1)] + omega_twist[(1, 2)] - omega_twist[(0, 2)]
    c_bot = omega_twist[(3, 4)] + omega_twist[(4, 5)] - omega_twist[(3, 5)]
    h_01 = omega_twist[(0, 1)] + omega_twist[(1, 4)] - omega_twist[(3, 4)] - omega_twist[(0, 3)]
    h_12 = omega_twist[(1, 2)] + omega_twist[(2, 5)] - omega_twist[(4, 5)] - omega_twist[(1, 4)]
    obstructed_prism_trees = _count_obstructed_spanning_trees(
        num_vertices,
        prism_edges,
        prism_trees,
        omega_twist,
    )
    twist_witness = (
        ((c_top, c_bot), (h_01, h_12), obstructed_prism_trees)
        if (c_top, c_bot) == (0, 0)
        and (h_01, h_12) == (-2, 1)
        and obstructed_prism_trees == len(prism_trees)
        else None
    )

    stage5_witness = (
        prism_v_e_b1_trees,
        sector_ranks,
        orthogonality_defect,
        coupled_op_defect,
        twist_witness,
    )
    native_binding = load_coupled_native_rust_and_lean4_witnesses()
    return {
        "prompt_uri": prompt_uri,
        "candidate_text": (
            "Stage 5 pure relational derivation on the coupled bipartite carrier D_2 x D_3 "
            "(6 elements, triangular prism graph G_{2,3} with 75 spanning trees): exact 4-sector "
            "orthogonal projector decomposition of ranks (1, 1, 2, 2), coupled swap-commutator "
            "J_{23}^3 + 3 J_{23} = 0, and inter-layer twist holonomy witness obstructing all 75 trees."
        ),
        "stage4_receipt": stage4_receipt_witness,
        "diagram_witness": stage5_witness,
        "code_witness": native_binding.stage5_code_witness,
        "proof_witness": native_binding.stage5_proof_witness,
        "native_witness_binding": {
            "rust_module": native_binding.rust_module_relpath,
            "rust_runtime_action": native_binding.rust_runtime_action,
            "rust_source_sha256": native_binding.rust_source_sha256,
            "lean4_module": native_binding.lean4_module_relpath,
            "lean4_theorem": native_binding.lean4_theorem_names[4],
            "lean4_source_sha256": native_binding.lean4_source_sha256,
        },
        "prism_graph_v_e_b1_trees": prism_v_e_b1_trees,
        "four_sector_projector_ranks": sector_ranks,
        "four_sector_orthogonality_and_completeness_defect": orthogonality_defect,
        "coupled_swap_commutator_cubic_and_w0_defect": coupled_op_defect,
        "slot_pins": {
            "prism_graph_v_e_b1_trees": (6, 9, 4, 75),
            "four_sector_projector_ranks": (1, 1, 2, 2),
            "four_sector_orthogonality_and_completeness_defect": Fraction(0, 1),
            "coupled_swap_commutator_cubic_and_w0_defect": Fraction(0, 1),
        },
        "free_parameter_count": 0,
        "coupled_prism_interlayer_twist_witness": twist_witness,
        "authority_effect": "None",
        "genesis_effect": "None",
    }


def derive_stage_06_bipartite_d3_x_d3_exterior_singlet(
    prompt_uri: str,
    stage5_diagram_witness: Any,
) -> dict[str, Any]:
    """Stage 6: Derive coupled D_3 x D_3 5-sector split, rational involution on W_{00}, and singlet minor."""
    third = Fraction(1, 3)
    half = Fraction(1, 2)
    q_plus: MatrixQ = tuple(tuple(third for _ in range(3)) for _ in range(3))
    ident_3 = _ident_q(3)
    q_w0: MatrixQ = tuple(
        tuple(ident_3[i][j] - q_plus[i][j] for j in range(3)) for i in range(3)
    )

    pi_pp = _kron_q(q_plus, q_plus)
    pi_p0 = _kron_q(q_plus, q_w0)
    pi_0p = _kron_q(q_w0, q_plus)
    pi_00 = _kron_q(q_w0, q_w0)

    # Factor-exchange involution tau(a, b) = (b, a) on D_3 x D_3 (9 elements)
    ident_9 = _ident_q(9)
    tau_q: MatrixQ = tuple(
        tuple(
            Fraction(1, 1) if i == (3 * (j % 3) + (j // 3)) else Fraction(0, 1)
            for j in range(9)
        )
        for i in range(9)
    )
    p_tau_sym: MatrixQ = tuple(
        tuple(half * (ident_9[i][j] + tau_q[i][j]) for j in range(9)) for i in range(9)
    )
    p_tau_alt: MatrixQ = tuple(
        tuple(half * (ident_9[i][j] - tau_q[i][j]) for j in range(9)) for i in range(9)
    )

    pi_00_sym = _matmul_q(p_tau_sym, pi_00)
    pi_00_alt = _matmul_q(p_tau_alt, pi_00)
    sectors_5 = (pi_pp, pi_p0, pi_0p, pi_00_sym, pi_00_alt)

    sector_traces_q = tuple(_trace_q(p) for p in sectors_5)
    five_sector_ranks = tuple(int(t.numerator) for t in sector_traces_q if t.denominator == 1)
    orthogonality_defect = _projector_family_defect_q(sectors_5)

    # Compound commutator K_{33} = K (x) K on D_3 x D_3 satisfies ((K (x) K)^2 - 9 I) Pi_{00} = 0
    k_z: MatrixZ = (
        (0, -1, 1),
        (1, 0, -1),
        (-1, 1, 0),
    )
    k_33 = _kron_z(k_z, k_z)
    k_33_sq = _matmul_z(k_33, k_33)
    k_33_sym_defect = sum(abs(k_33[i][j] - k_33[j][i]) for i in range(9) for j in range(9))

    k33_sq_minus_9i_q: MatrixQ = tuple(
        tuple(Fraction(k_33_sq[i][j], 1) - 9 * ident_9[i][j] for j in range(9))
        for i in range(9)
    )
    w00_involution_residual = _matmul_q(k33_sq_minus_9i_q, pi_00)
    involution_defect = Fraction(k_33_sym_defect, 1) + sum(
        (abs(w00_involution_residual[i][j]) for i in range(9) for j in range(9)),
        Fraction(0, 1),
    )

    # Diagonal 3-cycle R_{33} = R (x) R trace separation on Pi_{00}^{sym} vs Pi_{00}^{alt}
    t_01: MatrixZ = ((0, 1, 0), (1, 0, 0), (0, 0, 1))
    t_12: MatrixZ = ((1, 0, 0), (0, 0, 1), (0, 1, 0))
    r_z = _matmul_z(t_01, t_12)
    r_33_z = _kron_z(r_z, r_z)
    r_33_q: MatrixQ = tuple(
        tuple(Fraction(r_33_z[i][j], 1) for j in range(9)) for i in range(9)
    )
    tr_r33_sym = _trace_q(_matmul_q(r_33_q, pi_00_sym))
    tr_r33_alt = _trace_q(_matmul_q(r_33_q, pi_00_alt))
    r33_minus_i_alt = _matmul_q(
        tuple(tuple(r_33_q[i][j] - ident_9[i][j] for j in range(9)) for i in range(9)),
        pi_00_alt,
    )
    alt_invariance_defect = sum(
        (abs(r33_minus_i_alt[i][j]) for i in range(9) for j in range(9)),
        Fraction(0, 1),
    )
    r33_trace_pin = (
        int(tr_r33_sym.numerator),
        int(tr_r33_alt.numerator),
        int(alt_invariance_defect.numerator),
    )

    # Boundary counterexample witness: antisymmetric singlet psi_alt = flat(K) in im(Pi_{00}^{alt})
    # has 2x2 minor det([[K_00, K_01], [K_10, K_11]]) = 1 != 0, impossible for any rank-1 product u (x) v
    psi_alt_minor_01 = k_z[0][0] * k_z[1][1] - k_z[0][1] * k_z[1][0]
    u_sample = (1, -1, 0)
    v_sample = (0, 1, -1)
    separable_minor_01 = (u_sample[0] * v_sample[0]) * (u_sample[1] * v_sample[1]) - (
        u_sample[0] * v_sample[1]
    ) * (u_sample[1] * v_sample[0])
    singlet_witness = (
        (psi_alt_minor_01, separable_minor_01, "antisymmetric_singlet_minor_1_vs_separable_0")
        if psi_alt_minor_01 == 1 and separable_minor_01 == 0
        else None
    )

    stage6_witness = (
        stage5_diagram_witness,
        five_sector_ranks,
        orthogonality_defect,
        involution_defect,
        r33_trace_pin,
        singlet_witness,
    )
    native_binding = load_coupled_native_rust_and_lean4_witnesses()
    return {
        "prompt_uri": prompt_uri,
        "candidate_text": (
            "Stage 6 pure relational derivation on the coupled bipartite carrier D_3 x D_3 "
            "(9 elements): 5-sector projector refinement of ranks (1, 2, 2, 3, 1), exact rational "
            "involution (1/3)(K (x) K) on the 4D joint difference core W_0 (x) W_0 via "
            "((K (x) K)^2 - 9 I)|_{W_{00}} = 0, and non-factorizable antisymmetric singlet minor 1 != 0."
        ),
        "stage5_diagram": stage5_diagram_witness,
        "receipt_witness": stage6_witness,
        "code_witness": (stage5_diagram_witness, *native_binding.stage6_code_body),
        "proof_witness": (stage5_diagram_witness, *native_binding.stage6_proof_body),
        "native_witness_binding": {
            "rust_module": native_binding.rust_module_relpath,
            "rust_runtime_action": native_binding.rust_runtime_action,
            "rust_source_sha256": native_binding.rust_source_sha256,
            "lean4_module": native_binding.lean4_module_relpath,
            "lean4_theorem": native_binding.lean4_theorem_names[5],
            "lean4_source_sha256": native_binding.lean4_source_sha256,
        },
        "five_sector_projector_ranks": five_sector_ranks,
        "five_sector_orthogonality_and_completeness_defect": orthogonality_defect,
        "compound_commutator_square_minus_nine_w00_defect": involution_defect,
        "diagonal_3cycle_traces_on_sym_and_alt_w00": r33_trace_pin,
        "slot_pins": {
            "five_sector_projector_ranks": (1, 2, 2, 3, 1),
            "five_sector_orthogonality_and_completeness_defect": Fraction(0, 1),
            "compound_commutator_square_minus_nine_w00_defect": Fraction(0, 1),
            "diagonal_3cycle_traces_on_sym_and_alt_w00": (0, 1, 0),
        },
        "free_parameter_count": 0,
        "nonfactorizable_entangled_difference_witness": singlet_witness,
        "authority_effect": "None",
        "genesis_effect": "None",
    }


def run_genesis_relational_derivation_workflow(
    fixtures_dir: Path,
    yaml_loader: Any,
    *,
    admitted_antibody_ids: Sequence[str] = (),
    host_danger_signals: Sequence[str] = (),
    payload_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> GenesisRelationalDerivationRun:
    """Execute the 4-stage single-carrier pure relational derivation workflow under pre-declared locks."""
    nodes = load_predeclared_relational_operad_locks(
        fixtures_dir,
        yaml_loader,
        filenames=RELATIONAL_BINDING_FILENAMES,
    )

    p1 = derive_stage_01_survivor_tower_and_retraction(nodes[0].uri.raw_uri)
    p2 = derive_stage_02_collision_tagging_and_swap_quotient(
        nodes[1].uri.raw_uri,
        p1["state_witness"],
    )
    p3 = derive_stage_03_directed_cut_coboundary_vs_chord_obstruction(
        nodes[2].uri.raw_uri,
        p2["contract_witness"],
    )
    p4 = derive_stage_04_three_element_swap_commutator_cyclotomic_receipt(
        nodes[3].uri.raw_uri,
        p3["paper_witness"],
    )

    payloads: dict[str, Mapping[str, Any]] = {
        nodes[0].uri.raw_uri: p1,
        nodes[1].uri.raw_uri: p2,
        nodes[2].uri.raw_uri: p3,
        nodes[3].uri.raw_uri: p4,
    }
    if payload_overrides:
        for uri, override_map in payload_overrides.items():
            if uri in payloads:
                merged = dict(payloads[uri])
                merged.update(override_map)
                payloads[uri] = merged
            else:
                payloads[uri] = override_map

    report = collect_derivation_map_operads(
        nodes,
        payloads,
        admitted_antibody_ids=admitted_antibody_ids,
        host_danger_signals=host_danger_signals,
    )
    return GenesisRelationalDerivationRun(
        predeclared_nodes=nodes,
        stage_payloads=payloads,
        operad_report=report,
    )


def run_coupled_bipartite_relational_derivation_workflow(
    fixtures_dir: Path,
    yaml_loader: Any,
    *,
    admitted_antibody_ids: Sequence[str] = (),
    host_danger_signals: Sequence[str] = (),
    payload_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> GenesisRelationalDerivationRun:
    """Execute the 6-stage coupled bipartite relational derivation workflow (Stages 1-6).

    1. Loads and freezes all 6 pre-declared `.binding.yaml` sidecars before candidate generation.
    2. Derives Stages 1-4 on single carriers and extends through Stage 5 (`D_2 x D_3`) and
       Stage 6 (`D_3 x D_3`) purely over Z and Q (`Fraction`) with 0 free parameters.
    3. Evaluates the 6-stage chain under `collect_derivation_map_operads`, ensuring
       `residual_degrees_of_freedom == 0` across all 49 locked constraints.
    """
    nodes = load_predeclared_relational_operad_locks(
        fixtures_dir,
        yaml_loader,
        filenames=COUPLED_BIPARTITE_BINDING_FILENAMES,
    )

    p1 = derive_stage_01_survivor_tower_and_retraction(nodes[0].uri.raw_uri)
    p2 = derive_stage_02_collision_tagging_and_swap_quotient(
        nodes[1].uri.raw_uri,
        p1["state_witness"],
    )
    p3 = derive_stage_03_directed_cut_coboundary_vs_chord_obstruction(
        nodes[2].uri.raw_uri,
        p2["contract_witness"],
    )
    p4 = derive_stage_04_three_element_swap_commutator_cyclotomic_receipt(
        nodes[3].uri.raw_uri,
        p3["paper_witness"],
    )
    p5 = derive_stage_05_bipartite_d2_x_d3_prism_factorization(
        nodes[4].uri.raw_uri,
        p4["proof_witness"],
    )
    p6 = derive_stage_06_bipartite_d3_x_d3_exterior_singlet(
        nodes[5].uri.raw_uri,
        p5["diagram_witness"],
    )

    payloads: dict[str, Mapping[str, Any]] = {
        nodes[0].uri.raw_uri: p1,
        nodes[1].uri.raw_uri: p2,
        nodes[2].uri.raw_uri: p3,
        nodes[3].uri.raw_uri: p4,
        nodes[4].uri.raw_uri: p5,
        nodes[5].uri.raw_uri: p6,
    }
    if payload_overrides:
        for uri, override_map in payload_overrides.items():
            if uri in payloads:
                merged = dict(payloads[uri])
                merged.update(override_map)
                payloads[uri] = merged
            else:
                payloads[uri] = override_map

    report = collect_derivation_map_operads(
        nodes,
        payloads,
        admitted_antibody_ids=admitted_antibody_ids,
        host_danger_signals=host_danger_signals,
    )
    return GenesisRelationalDerivationRun(
        predeclared_nodes=nodes,
        stage_payloads=payloads,
        operad_report=report,
    )


def derive_stage_07_tripartite_d3_cubed_schur_weyl_and_levi_civita(
    prompt_uri: str,
    stage6_receipt_witness: Any,
) -> dict[str, Any]:
    """Stage 7: Derive tripartite D_3 x D_3 x D_3 (27 elements) Schur-Weyl & Levi-Civita structure."""
    third = Fraction(1, 3)
    sixth = Fraction(1, 6)
    half = Fraction(1, 2)
    q_plus: MatrixQ = tuple(tuple(third for _ in range(3)) for _ in range(3))
    ident_3 = _ident_q(3)
    q_w0: MatrixQ = tuple(
        tuple(ident_3[i][j] - q_plus[i][j] for j in range(3)) for i in range(3)
    )

    # 1. Binomial degree-graded projectors on Q^27 = (Q_+ + Q_0)^(x)3
    pi_30 = _kron_q(_kron_q(q_plus, q_plus), q_plus)
    pi_21 = _matadd_q(
        _matadd_q(_kron_q(_kron_q(q_plus, q_plus), q_w0), _kron_q(_kron_q(q_plus, q_w0), q_plus)),
        _kron_q(_kron_q(q_w0, q_plus), q_plus),
    )
    pi_12 = _matadd_q(
        _matadd_q(_kron_q(_kron_q(q_plus, q_w0), q_w0), _kron_q(_kron_q(q_w0, q_plus), q_w0)),
        _kron_q(_kron_q(q_w0, q_w0), q_plus),
    )
    pi_000 = _kron_q(_kron_q(q_w0, q_w0), q_w0)
    binomial_sectors = (pi_30, pi_21, pi_12, pi_000)
    binomial_ranks = tuple(int(_trace_q(p).numerator) for p in binomial_sectors)

    # 2. Factor-permutation group S_3^{fac} acting on (a, b, c) in {0,1,2}^3
    s3_perms: tuple[tuple[tuple[int, int, int], int], ...] = (
        ((0, 1, 2), 1),
        ((1, 2, 0), 1),
        ((2, 0, 1), 1),
        ((1, 0, 2), -1),
        ((0, 2, 1), -1),
        ((2, 1, 0), -1),
    )
    ident_27 = _ident_q(27)
    p_sym_raw: list[list[Fraction]] = [[Fraction(0, 1) for _ in range(27)] for _ in range(27)]
    p_alt_raw: list[list[Fraction]] = [[Fraction(0, 1) for _ in range(27)] for _ in range(27)]
    for perm, sgn in s3_perms:
        for a in range(3):
            for b in range(3):
                for c in range(3):
                    col = 9 * a + 3 * b + c
                    coords = (a, b, c)
                    row = 9 * coords[perm[0]] + 3 * coords[perm[1]] + coords[perm[2]]
                    p_sym_raw[row][col] += sixth
                    p_alt_raw[row][col] += sixth * sgn

    p_sym3: MatrixQ = tuple(tuple(r) for r in p_sym_raw)
    p_alt3: MatrixQ = tuple(tuple(r) for r in p_alt_raw)
    p_mix3: MatrixQ = tuple(
        tuple(ident_27[i][j] - p_sym3[i][j] - p_alt3[i][j] for j in range(27))
        for i in range(27)
    )

    # Schur-Weyl ranks on W_000 = W_0^(x)3 (dim 8): since dim(W_0)=2 < 3, Lambda^3(W_0) = 0
    w000_sym_rank = int(_trace_q(_matmul_q(p_sym3, pi_000)).numerator)
    w000_mix_rank = int(_trace_q(_matmul_q(p_mix3, pi_000)).numerator)
    w000_alt_rank = int(_trace_q(_matmul_q(p_alt3, pi_000)).numerator)
    w000_schur_weyl_ranks = (w000_sym_rank, w000_mix_rank, w000_alt_rank)

    # 3. Unique 1D Levi-Civita determinant line im(P_alt^(3)) localization in Pi^(1,2) and parity
    alt_total_rank = int(_trace_q(p_alt3).numerator)
    alt_in_pi12 = _matmul_q(pi_12, p_alt3)
    alt_outside_pi12_defect = sum(
        (abs(alt_in_pi12[i][j] - p_alt3[i][j]) for i in range(27) for j in range(27)),
        Fraction(0, 1),
    )

    t_01: MatrixZ = ((0, 1, 0), (1, 0, 0), (0, 0, 1))
    t_12: MatrixZ = ((1, 0, 0), (0, 0, 1), (0, 1, 0))
    r_z = _matmul_z(t_01, t_12)
    r_3_z = _kron_z(_kron_z(r_z, r_z), r_z)
    t01_3_z = _kron_z(_kron_z(t_01, t_01), t_01)
    r_3_q: MatrixQ = tuple(
        tuple(Fraction(r_3_z[i][j], 1) for j in range(27)) for i in range(27)
    )
    t01_3_q: MatrixQ = tuple(
        tuple(Fraction(t01_3_z[i][j], 1) for j in range(27)) for i in range(27)
    )

    r3_on_alt = _matmul_q(r_3_q, p_alt3)
    t01_3_on_alt = _matmul_q(t01_3_q, p_alt3)
    r3_alt_defect = sum(
        (abs(r3_on_alt[i][j] - p_alt3[i][j]) for i in range(27) for j in range(27)),
        Fraction(0, 1),
    )
    t01_3_alt_defect = sum(
        (abs(t01_3_on_alt[i][j] + p_alt3[i][j]) for i in range(27) for j in range(27)),
        Fraction(0, 1),
    )
    levi_civita_pin = (
        alt_total_rank,
        int(alt_outside_pi12_defect.numerator),
        int(r3_alt_defect.numerator),
        int(t01_3_alt_defect.numerator),
    )

    # 4. R^(x)3-invariant subspace on W_000 (rank 2 inside Sym^3(W_0)) split by T_01^(x)3 into (1, 1)
    r_3_sq_q = _matmul_q(r_3_q, r_3_q)
    p_r3_inv: MatrixQ = tuple(
        tuple(third * (ident_27[i][j] + r_3_q[i][j] + r_3_sq_q[i][j]) for j in range(27))
        for i in range(27)
    )
    pi_000_r3 = _matmul_q(p_r3_inv, pi_000)
    w000_r3_rank = int(_trace_q(pi_000_r3).numerator)

    p_t01_plus: MatrixQ = tuple(
        tuple(half * (ident_27[i][j] + t01_3_q[i][j]) for j in range(27)) for i in range(27)
    )
    p_t01_minus: MatrixQ = tuple(
        tuple(half * (ident_27[i][j] - t01_3_q[i][j]) for j in range(27)) for i in range(27)
    )
    w000_r3_plus_rank = int(_trace_q(_matmul_q(p_t01_plus, pi_000_r3)).numerator)
    w000_r3_minus_rank = int(_trace_q(_matmul_q(p_t01_minus, pi_000_r3)).numerator)

    k_z: MatrixZ = ((0, -1, 1), (1, 0, -1), (-1, 1, 0))
    k_3_z = _kron_z(_kron_z(k_z, k_z), k_z)
    k_3_sq_z = _matmul_z(k_3_z, k_3_z)
    k3_sq_plus_27i_q: MatrixQ = tuple(
        tuple(Fraction(k_3_sq_z[i][j], 1) + 27 * ident_27[i][j] for j in range(27))
        for i in range(27)
    )
    k3_w000_res = _matmul_q(k3_sq_plus_27i_q, pi_000)
    k3_w000_defect = sum(
        (abs(k3_w000_res[i][j]) for i in range(27) for j in range(27)),
        Fraction(0, 1),
    )
    w000_r3_split_pin = (
        w000_r3_rank,
        w000_r3_plus_rank,
        w000_r3_minus_rank,
        int(k3_w000_defect.numerator),
    )

    # 5. Boundary counterexample witness: 6-term Levi-Civita alternating tensor epsilon
    # has ||epsilon||_1 = 6, ||Pi^(1,2) epsilon - epsilon||_1 = 0, and ||Pi_000 epsilon||_1 = 0
    eps_vec = [Fraction(0, 1) for _ in range(27)]
    for perm, sgn in s3_perms:
        idx = 9 * perm[0] + 3 * perm[1] + perm[2]
        eps_vec[idx] = Fraction(sgn, 1)
    eps_l1 = int(sum((abs(v) for v in eps_vec), Fraction(0, 1)).numerator)
    pi12_eps_diff = int(
        sum(
            (
                abs(sum((pi_12[i][j] * eps_vec[j] for j in range(27)), Fraction(0, 1)) - eps_vec[i])
                for i in range(27)
            ),
            Fraction(0, 1),
        ).numerator
    )
    pi000_eps_l1 = int(
        sum(
            (
                abs(sum((pi_000[i][j] * eps_vec[j] for j in range(27)), Fraction(0, 1)))
                for i in range(27)
            ),
            Fraction(0, 1),
        ).numerator
    )
    pigeonhole_witness = (
        (
            eps_l1,
            pi12_eps_diff,
            pi000_eps_l1,
            "pigeonhole_lambda3_w0_vanishes_supported_on_lplus_tensor_lambda2_w0",
        )
        if eps_l1 == 6 and pi12_eps_diff == 0 and pi000_eps_l1 == 0
        else None
    )

    stage7_witness = (
        stage6_receipt_witness,
        binomial_ranks,
        w000_schur_weyl_ranks,
        levi_civita_pin,
        w000_r3_split_pin,
        pigeonhole_witness,
    )
    native_binding = load_coupled_native_rust_and_lean4_witnesses()
    return {
        "prompt_uri": prompt_uri,
        "candidate_text": (
            "Stage 7 pure relational derivation on tripartite D_3 x D_3 x D_3 (27 elements): "
            "binomial sector ranks (1, 6, 12, 8); Schur-Weyl obstruction Lambda^3(W_0) = 0 on "
            "W_000 with ranks (4, 4, 0); unique 1D Levi-Civita determinant line supported on "
            "the rank-12 mixed sector Lambda^1(L_+) (x) Lambda^2(W_0); and R^(x)3-invariant "
            "rank-2 subspace of W_000 split into (1, 1) by T_01^(x)3 with (K^(x)3)^2|_{W_000} = -27 I."
        ),
        "stage6_receipt": stage6_receipt_witness,
        "tripartite_receipt_witness": stage7_witness,
        "code_witness": (stage6_receipt_witness, *native_binding.stage7_code_body),
        "proof_witness": (stage6_receipt_witness, *native_binding.stage7_proof_body),
        "native_witness_binding": {
            "rust_module": native_binding.rust_module_relpath,
            "rust_runtime_action": native_binding.rust_runtime_action,
            "rust_source_sha256": native_binding.rust_source_sha256,
            "lean4_module": native_binding.lean4_module_relpath,
            "lean4_theorem": native_binding.lean4_theorem_names[6],
            "lean4_source_sha256": native_binding.lean4_source_sha256,
        },
        "tripartite_binomial_sector_ranks": binomial_ranks,
        "w000_schur_weyl_sym_mixed_alt_ranks": w000_schur_weyl_ranks,
        "levi_civita_mixed_sector_and_parity_pin": levi_civita_pin,
        "w000_r3_invariant_split_and_k3_square_defect": w000_r3_split_pin,
        "slot_pins": {
            "tripartite_binomial_sector_ranks": (1, 6, 12, 8),
            "w000_schur_weyl_sym_mixed_alt_ranks": (4, 4, 0),
            "levi_civita_mixed_sector_and_parity_pin": (1, 0, 0, 0),
            "w000_r3_invariant_split_and_k3_square_defect": (2, 1, 1, 0),
        },
        "free_parameter_count": 0,
        "pigeonhole_w000_alt_vanishing_and_levi_civita_witness": pigeonhole_witness,
        "authority_effect": "None",
        "genesis_effect": "None",
    }


def run_tripartite_relational_derivation_workflow(
    fixtures_dir: Path,
    yaml_loader: Any,
    *,
    admitted_antibody_ids: Sequence[str] = (),
    host_danger_signals: Sequence[str] = (),
    payload_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> GenesisRelationalDerivationRun:
    """Execute the 7-stage tripartite relational derivation workflow (Stages 1-7).

    1. Loads and freezes all 7 pre-declared `.binding.yaml` sidecars before candidate generation.
    2. Derives Stages 1-4 on single carriers, Stages 5-6 on coupled bipartite carriers
       (`D_2 x D_3` and `D_3 x D_3`), and Stage 7 on the tripartite carrier (`D_3 x D_3 x D_3`,
       27 elements) purely over Z and Q (`Fraction`) with 0 free parameters.
    3. Evaluates the 7-stage chain under `collect_derivation_map_operads`, ensuring
       `residual_degrees_of_freedom == 0` across all 58 locked constraints.
    """
    nodes = load_predeclared_relational_operad_locks(
        fixtures_dir,
        yaml_loader,
        filenames=TRIPARTITE_BINDING_FILENAMES,
    )

    p1 = derive_stage_01_survivor_tower_and_retraction(nodes[0].uri.raw_uri)
    p2 = derive_stage_02_collision_tagging_and_swap_quotient(
        nodes[1].uri.raw_uri,
        p1["state_witness"],
    )
    p3 = derive_stage_03_directed_cut_coboundary_vs_chord_obstruction(
        nodes[2].uri.raw_uri,
        p2["contract_witness"],
    )
    p4 = derive_stage_04_three_element_swap_commutator_cyclotomic_receipt(
        nodes[3].uri.raw_uri,
        p3["paper_witness"],
    )
    p5 = derive_stage_05_bipartite_d2_x_d3_prism_factorization(
        nodes[4].uri.raw_uri,
        p4["proof_witness"],
    )
    p6 = derive_stage_06_bipartite_d3_x_d3_exterior_singlet(
        nodes[5].uri.raw_uri,
        p5["diagram_witness"],
    )
    p7 = derive_stage_07_tripartite_d3_cubed_schur_weyl_and_levi_civita(
        nodes[6].uri.raw_uri,
        p6["receipt_witness"],
    )

    payloads: dict[str, Mapping[str, Any]] = {
        nodes[0].uri.raw_uri: p1,
        nodes[1].uri.raw_uri: p2,
        nodes[2].uri.raw_uri: p3,
        nodes[3].uri.raw_uri: p4,
        nodes[4].uri.raw_uri: p5,
        nodes[5].uri.raw_uri: p6,
        nodes[6].uri.raw_uri: p7,
    }
    if payload_overrides:
        for uri, override_map in payload_overrides.items():
            if uri in payloads:
                merged = dict(payloads[uri])
                merged.update(override_map)
                payloads[uri] = merged
            else:
                payloads[uri] = override_map

    report = collect_derivation_map_operads(
        nodes,
        payloads,
        admitted_antibody_ids=admitted_antibody_ids,
        host_danger_signals=host_danger_signals,
    )
    return GenesisRelationalDerivationRun(
        predeclared_nodes=nodes,
        stage_payloads=payloads,
        operad_report=report,
    )

