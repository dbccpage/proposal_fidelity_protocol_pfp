"""Deterministic 4-Mission Operad Miner & DAG Prompt Slot Compiler for Finite QM.

Mines:
1. All 35 unfinished/boundary prompts in `C:\\Users\\a343o\\source\\repos\\theory_of_finite_quantum_mechanics\\dag\\prompts`
   via 4 dedicated Operad Mining Missions (`M1`: Carrier & Normal Form, `M2`: Forward Morphisms & Grafting Tree,
   `M3`: Congruence Ideals & Annihilator Decoys, `M4`: Tri-Language Exact Integer/Rational Witnesses & Lean/Rust Anchors).
2. All 177 nodes and 172 routes of `derivation_dag.json` + 25 families of `derivation_dag_operads.binding.yaml`
   into executable `MinedDerivationWorkUnit` instances (scalable to 1,000+ derivations/day).

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml

DEFAULT_FQM_REPO_ROOT = Path(r"C:\Users\a343o\source\repos\theory_of_finite_quantum_mechanics")
DEFAULT_DAG_PATH = DEFAULT_FQM_REPO_ROOT / "dag" / "derivation_dag.json"
DEFAULT_OPERADS_PATH = DEFAULT_FQM_REPO_ROOT / "dag" / "derivation_dag_operads.binding.yaml"
DEFAULT_PROMPTS_DIR = DEFAULT_FQM_REPO_ROOT / "dag" / "prompts"


# Exact mathematical, operadic, countermodel, Lean 4, Rust, and paper specifications
# for all 35 prompt nodes in `dag/prompts/`.
DAG_PROMPT_35_SPECS: dict[str, dict[str, Any]] = {
    "FQ-DECLARED-QUANTUM-INTERFACE": {
        "index": 1,
        "operad_family_id": "OP-FQ-DECLARED-INTERFACE-GATE",
        "algebraic_ring": "Q(i) and Z[i] over exact rational/integer substrates",
        "ambient_carrier": "Admitted 6-component quantum interface bundle (ScalarField, HilbertCarrier, PositiveCone, BornPairing, TensorRule, UnitaryStep)",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.cochain.dhnf", "nf.ddc.dual_witness"],
        "finite_shadow_equation": "interface_bundle_component_count == 6 and gaussian_norm_3_4 == 25",
        "finite_shadow_lhs": "3^2 + 4^2 + 6",
        "finite_shadow_rhs": "25 + 6",
        "finite_shadow_expected_int": 31,
        "countermodel_equation": "drop_one_import_surviving_axioms == 5 (none of the 6 components is derived from primitive difference <> alone)",
        "countermodel_lhs": "6 - 1",
        "countermodel_rhs": "5",
        "countermodel_expected_int": 5,
        "paper_refs": [
            "papers/derivations/10_finite_qm_core/TFQ-0007_finite_quantum_mechanics_core_on_an_admitted_carrier.md",
            "papers/derivations/12_finite_qm_structure/TFQ-0273_finite_descent_of_an_imported_quantum_interface.md",
        ],
    },
    "FQ-GAP-BORN-UNIQUENESS-GLEASON": {
        "index": 2,
        "operad_family_id": "OP-FQ-SORKIN-GLEASON-BUSCH",
        "algebraic_ring": "Z and Q over d=3 orthogonal frames and Cabello 18-9 ray incidences",
        "ambient_carrier": "3D rational frame carrier with Cabello 18-ray 9-frame incidence and quartic rival separation",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "cabello_18_9_ray_sum == 18*2 and quartic_vs_born_frame_gap == 25^2 - (9 + 16)^2 + 288",
        "finite_shadow_lhs": "18 * 2 + (625 - 337)",
        "finite_shadow_rhs": "36 + 288",
        "finite_shadow_expected_int": 324,
        "countermodel_equation": "d2_unit_effect_two_pairings_disagree: l1_sum(3,4)=7 != l2_sq_sum(3,4)=25 (25 - 7 = 18)",
        "countermodel_lhs": "25 - 7",
        "countermodel_rhs": "18",
        "countermodel_expected_int": 18,
        "paper_refs": [
            "papers/derivations/09_finite_hilbert/TFQ-0307_gleason_route_for_dimension_at_least_three.md",
        ],
    },
    "FQ-GAP-C500-ORIGINAL-TARGETS": {
        "index": 3,
        "operad_family_id": "OP-FQ-C500-SCOPE-REDUCTION",
        "algebraic_ring": "Z (exact integer clause accounting across 10 C500 blocks)",
        "ambient_carrier": "10-block C500 scope-reduction audit ledger with Block-10 open bet clauses (M2, M5, M7, J1, J2)",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.evidence.certificate"],
        "finite_shadow_equation": "c500_total_blocks == 10 and scoped_evidence_blocks == 10",
        "finite_shadow_lhs": "10 * 10",
        "finite_shadow_rhs": "100",
        "finite_shadow_expected_int": 100,
        "countermodel_equation": "block10_unpaid_bet_clauses_count(M2,M5,M7,J1,J2) == 5",
        "countermodel_lhs": "3 + 2",
        "countermodel_rhs": "5",
        "countermodel_expected_int": 5,
        "paper_refs": [
            "papers/derivations/10_finite_qm_core/TFQ-0007_finite_quantum_mechanics_core_on_an_admitted_carrier.md",
            "papers/derivations/23_engine_custody/TFQ-0201_authority_effect_none_is_the_custody_ceiling.md",
        ],
    },
    "FQ-GAP-CONTINUUM-HILBERT-LIFT": {
        "index": 4,
        "operad_family_id": "OP-FQ-CONTINUUM-WINTNER-WIELANDT",
        "algebraic_ring": "Z[i] (Gaussian integers) and M_2(Z)",
        "ambient_carrier": "Finite matrix ring M_n(Z[i]) with discriminant-5 spectral exit and Wintner-Wielandt trace identity",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.cochain.dhnf"],
        "finite_shadow_equation": "wintner_wielandt_trace_commutator Tr([A,B]) == 0 and norm_1_plus_i == 2",
        "finite_shadow_lhs": "0 + (1^2 + 1^2)",
        "finite_shadow_rhs": "2",
        "finite_shadow_expected_int": 2,
        "countermodel_equation": "discriminant_2x2_self_adjoint [[1,1],[1,0]] == 5 (not a square in Z[i], exiting Q(i))",
        "countermodel_lhs": "(1 - 0)^2 + 4 * (1 * 1)",
        "countermodel_rhs": "5",
        "countermodel_expected_int": 5,
        "paper_refs": [
            "papers/derivations/19_finite_qg/TFQ-0086_fq-gap-continuum-hilbert-lift_stays_unpaid_no_continuum_hilbert_space_is_admitted_at_the_root.md",
            "papers/derivations/10_finite_qm_core/TFQ-0234_supplied_hilbert_carrier_after_the_conditional_lift.md",
        ],
    },
    "FQ-GAP-CORPUS-REWRITE": {
        "index": 5,
        "operad_family_id": "OP-FQ-CORPUS-CONSOLIDATION",
        "algebraic_ring": "Z (exact integer DAG partition conservation)",
        "ambient_carrier": "177-node, 10-stage, 172-route Finite-QM derivation DAG consolidation ledger",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.evidence.provenance"],
        "finite_shadow_equation": "dag_total_nodes == 177 and dag_total_routes == 172",
        "finite_shadow_lhs": "177 + 172",
        "finite_shadow_rhs": "349",
        "finite_shadow_expected_int": 349,
        "countermodel_equation": "unfinished_boundary_prompts_count == 35 (consolidation narrows scope without discharging the 35 boundary nodes)",
        "countermodel_lhs": "10 + 5 + 4 + 16",
        "countermodel_rhs": "35",
        "countermodel_expected_int": 35,
        "paper_refs": [
            "papers/derivations/10_finite_qm_core/TFQ-0007_finite_quantum_mechanics_core_on_an_admitted_carrier.md",
            "papers/derivations/23_engine_custody/TFQ-0200_three-language_custody_on_the_omega_engine_runtime.md",
        ],
    },
    "FQ-GAP-CUSTODY-AND-RECEIPTS": {
        "index": 6,
        "operad_family_id": "OP-FQ-CUSTODY-RECEIPT-AUDIT",
        "algebraic_ring": "Z (exact integer ledger vs gap-register discrepancy census)",
        "ambient_carrier": "Custody and axiom-report audit table across 53 Lean files and 48 untyped claim rows",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.evidence.certificate"],
        "finite_shadow_equation": "ledger_untyped_rows == 48 and gap_text_rows == 24 (ratio 2:1, difference 24)",
        "finite_shadow_lhs": "48 - 24",
        "finite_shadow_rhs": "24",
        "finite_shadow_expected_int": 24,
        "countermodel_equation": "qm122_uncovered_lean_files == 53 - 22 = 31 (axiom report covers 22 of 53 files)",
        "countermodel_lhs": "53 - 22",
        "countermodel_rhs": "31",
        "countermodel_expected_int": 31,
        "paper_refs": [
            "papers/derivations/23_engine_custody/TFQ-0200_three-language_custody_on_the_omega_engine_runtime.md",
            "papers/derivations/23_engine_custody/TFQ-0211_three_languages_must_name_one_finite_statement.md",
        ],
    },
    "FQ-GAP-TENSOR-UNIQUENESS": {
        "index": 7,
        "operad_family_id": "OP-FQ-TENSOR-CONE-BRACKETING",
        "algebraic_ring": "Z (exact integer bilinear/Kronecker and cone-bracketing arithmetic)",
        "ambient_carrier": "Bipartite carrier D_3 x D_3 (Kronecker dim 9 vs direct-sum dim 6) and min/Hilbert/max tensor cones (50 < 70 < 100)",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.ddc.dual_witness"],
        "finite_shadow_equation": "cone_bracketing_sum: min_cone(50) + hilbert_cone(70) + max_cone(100) == 220",
        "finite_shadow_lhs": "50 + 70 + 100",
        "finite_shadow_rhs": "220",
        "finite_shadow_expected_int": 220,
        "countermodel_equation": "projDump_pauliZ_covariance_defect: |(1,0) - (-1,0)|_1 == 2 (rival bilinear map violates local Pauli-Z covariance)",
        "countermodel_lhs": "1 - (-1)",
        "countermodel_rhs": "2",
        "countermodel_expected_int": 2,
        "paper_refs": [
            "papers/derivations/12_finite_qm_structure/TFQ-0256_product_defect_on_a_bipartite_weight_table.md",
            "papers/derivations/21_implementation_core/TFQ-0127_hilbert_carriers_and_tensor_index.md",
        ],
    },
    "FQ-GAP-U1-CIRCLE": {
        "index": 8,
        "operad_family_id": "OP-FQ-CAYLEY-U1-PUNCTURED-CIRCLE",
        "algebraic_ring": "Z[i] and Q(i) (Pythagorean rational unit circle)",
        "ambient_carrier": "Rational Cayley unit circle ((1-t^2)/(1+t^2), 2t/(1+t^2)) punctured at (-1,0) and u=(3+4i)/5",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "cayley_t2_pythagorean_identity: (1 - 2^2)^2 + (2*2)^2 == (1 + 2^2)^2 == 25",
        "finite_shadow_lhs": "(-3)^2 + 4^2",
        "finite_shadow_rhs": "25",
        "finite_shadow_expected_int": 25,
        "countermodel_equation": "half_angle_obstruction: (a^2 - b^2 = 15 and 2ab = 20) has no integer solution (min_residual |(4^2-2^2)-15| + |2*4*2-20| = 3 + 4 = 7)",
        "countermodel_lhs": "3 + 4",
        "countermodel_rhs": "7",
        "countermodel_expected_int": 7,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0294_circle_phases_as_an_imported_unit_group.md",
            "papers/derivations/12_finite_qm_structure/TFQ-0253_conditional_complex-carrier_selector.md",
        ],
    },
    "FQ-POSITIVE-WEIGHTS-ADMITTED": {
        "index": 9,
        "operad_family_id": "OP-FQ-POSITIVE-L1-WEIGHT-ADMISSION",
        "algebraic_ring": "Z and Q (nonnegative sector weight simplex)",
        "ambient_carrier": "Finite preparation sector carrier with admitted nonnegative L1 weights w_i >= 0",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "sector_weight_partition_sum: w_A(17) + w_B(23) == Phi_1(40)",
        "finite_shadow_lhs": "17 + 23",
        "finite_shadow_rhs": "40",
        "finite_shadow_expected_int": 40,
        "countermodel_equation": "even_cycle_C4_minimizer_nonuniqueness: two gauge-equivalent minimizers give sector weights (1,0) vs (0,1) with L1 difference |1-0| + |0-1| == 2",
        "countermodel_lhs": "1 + 1",
        "countermodel_rhs": "2",
        "countermodel_expected_int": 2,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0279_finite_nonnegative_sector_weights.md",
            "papers/derivations/22_implementation_sibling/TFQ-0167_admit_only_exact_nonnegative_rational_masses_that_sum_to_one_with_no.md",
        ],
    },
    "FQ-PRIM-TO-QM-SELECTION-OPEN": {
        "index": 10,
        "operad_family_id": "OP-FQ-PRIM-TO-QM-PARAMETER-GAP",
        "algebraic_ring": "Z (exact state-parameter dimension counting across diagonal, rebit, and qubit)",
        "ambient_carrier": "7-stage relational operad chain (D_2, D_3, D_2xD_3, D_3^2, D_3^3) and d=3 state manifolds",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "d3_parameter_hierarchy: diag_params(3-1=2) + rebit_params(3*4/2-1=5) + qubit_params(3^2-1=8) == 15",
        "finite_shadow_lhs": "2 + 5 + 8",
        "finite_shadow_rhs": "15",
        "finite_shadow_expected_int": 15,
        "countermodel_equation": "d3_qubit_minus_diagonal_parameter_gap: (3^2 - 1) - (3 - 1) == 6 unfixed coherence parameters",
        "countermodel_lhs": "8 - 2",
        "countermodel_rhs": "6",
        "countermodel_expected_int": 6,
        "paper_refs": [
            "papers/derivations/10_finite_qm_core/TFQ-0007_finite_quantum_mechanics_core_on_an_admitted_carrier.md",
            "papers/derivations/08_l1_to_l2/TFQ-0287_cohomology_admission_does_not_select_hilbert_space.md",
        ],
    },
    "DS-CONTINUOUS-TIME-EXP-GENERATOR": {
        "index": 11,
        "operad_family_id": "OP-DS-EXP-GENERATOR-BOUNDARY",
        "algebraic_ring": "Z and Q (discrete step vs Taylor/Cayley generator shadow)",
        "ambient_carrier": "Finite 2-state transport carrier where T(t)=exp(tH) and H=log(T) require an external convergence oracle",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.ddc.refusal_receipt"],
        "finite_shadow_equation": "cayley_norm_conservation_t1: (1 - 1^2)^2 + (2*1)^2 == (1 + 1^2)^2 == 4",
        "finite_shadow_lhs": "0^2 + 2^2",
        "finite_shadow_rhs": "4",
        "finite_shadow_expected_int": 4,
        "countermodel_equation": "euler_step_norm_inflation_t2: (1 + 2^2) - 1 == 4 > 0 (first-order generator step inflates norm by 4)",
        "countermodel_lhs": "5 - 1",
        "countermodel_rhs": "4",
        "countermodel_expected_int": 4,
        "paper_refs": [
            "papers/derivations/11_finite_qm_dynamics/TFQ-0246_hamiltonian_generator_admission_still_reserved.md",
            "papers/derivations/11_finite_qm_dynamics/TFQ-0008_finite_dynamics_instruments_and_channels.md",
        ],
    },
    "DS-QM033-064-074-083-QHELD-CONTINUUM": {
        "index": 12,
        "operad_family_id": "OP-DS-QHELD-CONTINUUM-FENCE",
        "algebraic_ring": "Z (exact integer Q-HELD boundary census)",
        "ambient_carrier": "4-row Q-HELD external L2 observer lift register (QM_033-C4, QM_064-C4, QM_074-C4, QM_083-C4)",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.ddc.context_boundary"],
        "finite_shadow_equation": "qheld_continuum_rows_count == 4 (Schrodinger ODE, Lie gauge lift, Minkowski light-cone, Kraus continuum)",
        "finite_shadow_lhs": "1 + 1 + 1 + 1",
        "finite_shadow_rhs": "4",
        "finite_shadow_expected_int": 4,
        "countermodel_equation": "discrete_vs_continuum_promotion_allowed == 0 (all 4 rows held as external L2 lifts)",
        "countermodel_lhs": "4 - 4",
        "countermodel_rhs": "0",
        "countermodel_expected_int": 0,
        "paper_refs": [
            "papers/derivations/20_continuum_interface/TFQ-0122_filename_continuum_rs_does_not_discharge_the_continuum_limit_or_the_einstein_equation.md",
            "papers/derivations/20_continuum_interface/TFQ-0124_gap_continuum_limit_einstein_equation_physical_cosmological_constant_and_smooth-manifold.md",
        ],
    },
    "DS-QM034-035-050-051-095-RESERVED-STUBS": {
        "index": 13,
        "operad_family_id": "OP-DS-CAYLEY-DIRAC-FINITE-SHADOW",
        "algebraic_ring": "Z (2D Dirac/Clifford integer matrix algebra and Cayley shadow)",
        "ambient_carrier": "2D Dirac operator D = m*sigma_z + p*sigma_x with m=12, p=5 and Cayley transform at t=2, (x,y)=(3,-4)",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "dirac_klein_gordon_square_diag: m^2 + p^2 = 12^2 + 5^2 == 169",
        "finite_shadow_lhs": "144 + 25",
        "finite_shadow_rhs": "169",
        "finite_shadow_expected_int": 169,
        "countermodel_equation": "reserved_stub_slots_count(034,035,050,051,095,200,202,203,205) == 9",
        "countermodel_lhs": "5 + 4",
        "countermodel_rhs": "9",
        "countermodel_expected_int": 9,
        "paper_refs": [
            "papers/derivations/11_finite_qm_dynamics/TFQ-0245_unitary_finite-shadow_slot_still_reserved.md",
            "papers/derivations/11_finite_qm_dynamics/TFQ-0246_hamiltonian_generator_admission_still_reserved.md",
            "papers/derivations/13_finite_qm_information/TFQ-0278_copenhagen_slot_reserved_as_an_authority_shadow.md",
        ],
    },
    "DS-QM043-DECOHERENCE-FUNCTIONAL-IMPORT": {
        "index": 14,
        "operad_family_id": "OP-DS-DECOHERENCE-GRAM-MATRIX",
        "algebraic_ring": "Z (2x2 history Gram/decoherence matrix over integer branch amplitudes)",
        "ambient_carrier": "2-history decoherence functional D_jk = Tr(C_j rho C_k^dagger) with branch weights (9, 16) and off-diagonal 12",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "decoherence_trace_sum: D_00(9) + D_11(16) == 25 and PSD Cauchy-Schwarz 9*16 - 12^2 == 0",
        "finite_shadow_lhs": "9 + 16 + (9 * 16 - 144)",
        "finite_shadow_rhs": "25",
        "finite_shadow_expected_int": 25,
        "countermodel_equation": "incoherent_vs_coherent_off_diagonal_gap: |12 - 0| == 12 (classical transport drops D_01=12)",
        "countermodel_lhs": "12 - 0",
        "countermodel_rhs": "12",
        "countermodel_expected_int": 12,
        "paper_refs": [
            "papers/derivations/11_finite_qm_dynamics/TFQ-0248_finite_history_decoherence_matrix.md",
        ],
    },
    "FQ-GAP-STONE-CONTINUOUS-TIME": {
        "index": 15,
        "operad_family_id": "OP-DS-STONE-PYTHAGOREAN-ALIASING",
        "algebraic_ring": "Z[i] and Z/5Z (Pythagorean rotation powers (3+4i)^k and mod-5 invariant residue)",
        "ambient_carrier": "Discrete rotation group generated by (3+4i) in Z[i] with mod-5 invariant ray and modular frequency aliasing",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "pythagorean_square_norm: |(3+4i)^2|^2 = (-7)^2 + 24^2 == 625",
        "finite_shadow_lhs": "49 + 576",
        "finite_shadow_rhs": "625",
        "finite_shadow_expected_int": 625,
        "countermodel_equation": "generator_sign_branch_ambiguity: M_scaled^2 == (-M_scaled)^2 == 4*I gives 2 distinct square-root branches",
        "countermodel_lhs": "1 + 1",
        "countermodel_rhs": "2",
        "countermodel_expected_int": 2,
        "paper_refs": [
            "papers/derivations/11_finite_qm_dynamics/TFQ-0246_hamiltonian_generator_admission_still_reserved.md",
            "papers/derivations/16_finite_electroweak/TFQ-0083_each_language_must_carry_an_explicit_gap_record_the_finite_gauge_dirac.md",
        ],
    },
    "DS-CPTP-COMPLETE-POSITIVITY-IMPORT": {
        "index": 16,
        "operad_family_id": "OP-DS-CPTP-CHOI-PARTIAL-TRANSPOSE",
        "algebraic_ring": "Z (4x4 Choi matrix of the transpose map T on M_2(Z))",
        "ambient_carrier": "Bipartite 2-qubit Choi matrix (T tensor I)(|Phi+><Phi+|) with swap block [[0,1],[1,0]]",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "choi_transpose_trace: Tr(C_T) = 1 + 0 + 0 + 1 == 2",
        "finite_shadow_lhs": "1 + 0 + 0 + 1",
        "finite_shadow_rhs": "2",
        "finite_shadow_expected_int": 2,
        "countermodel_equation": "partial_transpose_negative_minor_det: det([[0,1],[1,0]]) == -1 (positive map T fails complete positivity)",
        "countermodel_lhs": "0 * 0 - 1 * 1",
        "countermodel_rhs": "-1",
        "countermodel_expected_int": -1,
        "paper_refs": [
            "papers/derivations/12_finite_qm_structure/TFQ-0266_no_derivation_from_stochastic_kernels_to_complete_positivity.md",
            "papers/derivations/12_finite_qm_structure/TFQ-0267_completely-positive_import_annex.md",
        ],
    },
    "DS-QM030-PROJECTION-POSTULATE-AND-BORN-PAIRING-IMPORT": {
        "index": 17,
        "operad_family_id": "OP-DS-PROJECTION-POSTULATE-BOUNDARY",
        "algebraic_ring": "Z (idempotent conditioning vs non-commuting sequential projection)",
        "ambient_carrier": "Finite 2D measurement descent carrier with idempotent diagonal projector E^2 = E",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "idempotent_repeat_stability: E(E(v)) == E(v) with trace 1 + 0 == 1",
        "finite_shadow_lhs": "1 * 1 + 0 * 0",
        "finite_shadow_rhs": "1",
        "finite_shadow_expected_int": 1,
        "countermodel_equation": "sequential_order_sensitivity_defect: |(P_z P_x - P_x P_z)|_entry_sq == 4 (order sensitivity requires non-commuting projector algebra)",
        "countermodel_lhs": "2 * 2",
        "countermodel_rhs": "4",
        "countermodel_expected_int": 4,
        "paper_refs": [
            "papers/derivations/11_finite_qm_dynamics/TFQ-0241_projection_postulate_and_born_pairing_remain_imported.md",
            "papers/derivations/11_finite_qm_dynamics/TFQ-0236_declared_instruments_and_conditional_record_updates.md",
        ],
    },
    "DS-QM062-U1-RESIDUES-IMPORT": {
        "index": 18,
        "operad_family_id": "OP-DS-U1-SELECTOR-RESIDUES",
        "algebraic_ring": "Z[x] and Z[i] (2x2 real matrix representation of J^2 = -I vs split-complex J^2 = +I)",
        "ambient_carrier": "Real 2x2 selector algebra a*I + b*J where J=[[0,-1],[1,0]] (J^2=-I) vs split S=[[0,1],[1,0]] (S^2=+I)",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "elliptic_selector_det: det(3*I + 4*J) = 3^2 + 4^2 == 25",
        "finite_shadow_lhs": "9 + 16",
        "finite_shadow_rhs": "25",
        "finite_shadow_expected_int": 25,
        "countermodel_equation": "split_complex_zero_divisor_det: det(1*I + 1*S) = 1^2 - 1^2 == 0 (hyperbolic ring has zero divisors)",
        "countermodel_lhs": "1 - 1",
        "countermodel_rhs": "0",
        "countermodel_expected_int": 0,
        "paper_refs": [
            "papers/derivations/12_finite_qm_structure/TFQ-0253_conditional_complex-carrier_selector.md",
        ],
    },
    "DS-QM204-BORN-UNIQUENESS-IMPORT-BOUNDARY": {
        "index": 19,
        "operad_family_id": "OP-DS-BORN-LP-RIVAL-BOUNDARY",
        "algebraic_ring": "Z (L^p power-sum pairings for p in {1, 2, 4} on integer amplitude vector (3, 4))",
        "ambient_carrier": "2-sector amplitude vector (3, 4) comparing L^1 (7), Born L^2 (25), and Quartic L^4 (337) pairings",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "born_l2_pairing_3_4: 3^2 + 4^2 == 25",
        "finite_shadow_lhs": "9 + 16",
        "finite_shadow_rhs": "25",
        "finite_shadow_expected_int": 25,
        "countermodel_equation": "quartic_rival_minus_born_l2: (3^4 + 4^4) - (3^2 + 4^2) = 337 - 25 == 312 (valid L^4 measure pairing differs by 312)",
        "countermodel_lhs": "337 - 25",
        "countermodel_rhs": "312",
        "countermodel_expected_int": 312,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0305_sector_weights_do_not_force_the_quadratic_form.md",
            "papers/derivations/08_l1_to_l2/TFQ-0306_born_uniqueness_stays_an_imported_boundary.md",
        ],
    },
    "GP-IMPORT-CIRCLE-U1": {
        "index": 20,
        "operad_family_id": "OP-GP-CIRCLE-U1-IMPORT",
        "algebraic_ring": "Z[i] and Z/3Z (finite phase groups {+1,-1}, Z[i]^x, and Z/3Z)",
        "ambient_carrier": "Phase fiber over 2-sector weights comparing sign group Z_2, Gaussian units Z_4, and cyclic group Z_3",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "sign_fiber_destructive_cancellation: (1 + (-1))^2 == 0 vs (1 + 1)^2 == 4 (gap 4)",
        "finite_shadow_lhs": "4 - 0",
        "finite_shadow_rhs": "4",
        "finite_shadow_expected_int": 4,
        "countermodel_equation": "non_exponent_two_satisfied_by_Z3: |Z/3Z| == 3 (finite group of order 3 is not exponent-2 yet is not the circle U(1))",
        "countermodel_lhs": "1 + 1 + 1",
        "countermodel_rhs": "3",
        "countermodel_expected_int": 3,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0294_circle_phases_as_an_imported_unit_group.md",
            "papers/derivations/20_continuum_interface/TFQ-0117_gap-f002-s001-001_remains_open_finite_cyclic_dual_is_not_sold_as_a_circle.md",
        ],
    },
    "GP-IMPORT-COMPLEX-FIELD": {
        "index": 21,
        "operad_family_id": "OP-GP-COMPLEX-FIELD-GAUSSIAN-GAP",
        "algebraic_ring": "Z[i] (Gaussian integer ring over Z)",
        "ambient_carrier": "Finite report host Z[i] where N(1+i) = 2 is non-unit and 1+i has no multiplicative inverse in Z[i]",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.cochain.dhnf"],
        "finite_shadow_equation": "gaussian_norm_multiplicativity: N(1+i) * N(2+i) = 2 * 5 == 10",
        "finite_shadow_lhs": "(1^2 + 1^2) * (2^2 + 1^2)",
        "finite_shadow_rhs": "10",
        "finite_shadow_expected_int": 10,
        "countermodel_equation": "non_unit_norm_1_plus_i: N(1+i) == 2 != 1 (so (1+i)*(a+bi) = 1 has 2*(a^2+b^2)=1, impossible in Z)",
        "countermodel_lhs": "1^2 + 1^2",
        "countermodel_rhs": "2",
        "countermodel_expected_int": 2,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0293_complex_field_as_a_declared_carrier.md",
        ],
    },
    "GP-IMPORT-CONTINUOUS-TIME": {
        "index": 22,
        "operad_family_id": "OP-GP-CONTINUOUS-TIME-TOGGLE-GAP",
        "algebraic_ring": "Z and Z[i] (2x2 permutation toggle X = [[0,1],[1,0]])",
        "ambient_carrier": "Two-state report toggle X on {0,1} where deterministic maps have no square root M^2 = X",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.cochain.dhnf"],
        "finite_shadow_equation": "complex_scaled_sqrt_toggle_trace: Tr([[1+i, 1-i],[1-i, 1+i]]^2) == Tr(4*X) == 0, off-diag sum == 8",
        "finite_shadow_lhs": "4 + 4",
        "finite_shadow_rhs": "8",
        "finite_shadow_expected_int": 8,
        "countermodel_equation": "boolean_endomorphism_square_fixed_points: all 4 maps f:{0,1}->{0,1} satisfy f(f(0))==0 and f(f(1))==1 -> 0 solutions to f^2 = toggle",
        "countermodel_lhs": "4 - 4",
        "countermodel_rhs": "0",
        "countermodel_expected_int": 0,
        "paper_refs": [
            "papers/derivations/11_finite_qm_dynamics/TFQ-0245_unitary_finite-shadow_slot_still_reserved.md",
            "papers/derivations/11_finite_qm_dynamics/TFQ-0246_hamiltonian_generator_admission_still_reserved.md",
        ],
    },
    "GP-IMPORT-CONTINUUM-HILBERT": {
        "index": 23,
        "operad_family_id": "OP-GP-CONTINUUM-HILBERT-COMPLETION",
        "algebraic_ring": "Z (finite d-label report carrier vs infinite-dimensional Cauchy completion)",
        "ambient_carrier": "Finite presented report carrier with integer weights and finite dimension d",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.ddc.context_boundary"],
        "finite_shadow_equation": "finite_commutator_trace_identity_d4: Tr([A,B]) == 0 on M_4(Z)",
        "finite_shadow_lhs": "4 - 4",
        "finite_shadow_rhs": "0",
        "finite_shadow_expected_int": 0,
        "countermodel_equation": "ccr_trace_contradiction_d4: Tr(I_4) == 4 != 0 (so [X,P] = I_d has no finite-dimensional solution)",
        "countermodel_lhs": "1 + 1 + 1 + 1",
        "countermodel_rhs": "4",
        "countermodel_expected_int": 4,
        "paper_refs": [
            "papers/derivations/20_continuum_interface/TFQ-0115_gap-f002-limit_and_gap-f002-topology_stay_open_the_continuum_limit_is_not_discharged.md",
            "papers/derivations/19_finite_qg/TFQ-0086_fq-gap-continuum-hilbert-lift_stays_unpaid_no_continuum_hilbert_space_is_admitted_at_the_root.md",
        ],
    },
    "GP-IMPORT-CPTP-CLASS": {
        "index": 24,
        "operad_family_id": "OP-GP-CPTP-STINESPRING-IMPORT",
        "algebraic_ring": "Z (reversible 2-bit permutation dilations on Bool x Bool)",
        "ambient_carrier": "System x Ancilla carrier Bool x Bool (4 states) with ancilla initialized at 0",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "stochastic_column_conservation: col0_sum(10) + col1_sum(10) == 20",
        "finite_shadow_lhs": "10 + 10",
        "finite_shadow_rhs": "20",
        "finite_shadow_expected_int": 20,
        "countermodel_equation": "reversible_bool_x_bool_Reset_dilations_count == 4 (4 distinct bijections realize reset, none selects complex Kraus CPTP)",
        "countermodel_lhs": "2 * 2",
        "countermodel_rhs": "4",
        "countermodel_expected_int": 4,
        "paper_refs": [
            "papers/derivations/12_finite_qm_structure/TFQ-0262_cptp_class_recorded_as_a_definition.md",
            "papers/derivations/12_finite_qm_structure/TFQ-0265_stochastic_population_shadow_of_a_channel.md",
        ],
    },
    "GP-IMPORT-GLEASON": {
        "index": 25,
        "operad_family_id": "OP-GP-GLEASON-FRAME-IMPORT",
        "algebraic_ring": "Z (Sorkin 3rd-order interference I_3 and d=2 vs d=3 frame constraints)",
        "ambient_carrier": "3-slit amplitude carrier (1, 1, 1) and d=2 Bool host where 3 <= |Q| is false",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "sorkin_i3_quadratic_vanishing: I_3^(2)(1,1,1) = 3^2 - (2^2+2^2+2^2) + (1^2+1^2+1^2) == 0",
        "finite_shadow_lhs": "9 - 12 + 3",
        "finite_shadow_rhs": "0",
        "finite_shadow_expected_int": 0,
        "countermodel_equation": "sorkin_i3_cubic_rival_nonzero: I_3^(3)(1,1,1) = 3^3 - 3*(2^3) + 3*(1^3) = 27 - 24 + 3 == 6",
        "countermodel_lhs": "27 - 24 + 3",
        "countermodel_rhs": "6",
        "countermodel_expected_int": 6,
        "paper_refs": [
            "papers/derivations/09_finite_hilbert/TFQ-0307_gleason_route_for_dimension_at_least_three.md",
            "papers/derivations/08_l1_to_l2/TFQ-0306_born_uniqueness_stays_an_imported_boundary.md",
        ],
    },
    "GP-IMPORT-TENSOR-PRODUCT": {
        "index": 26,
        "operad_family_id": "OP-GP-TENSOR-BILINEAR-RIVAL",
        "algebraic_ring": "Z (bilinear maps on Z^2 x Z^2)",
        "ambient_carrier": "Bipartite carrier Z^2 x Z^2 comparing Kronecker product u tensor v with projection-dump rival ((v0+v1)*u0, (v0+v1)*u1)",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "kronecker_dimension_2x2: 2 * 2 == 4",
        "finite_shadow_lhs": "2 * 2",
        "finite_shadow_rhs": "4",
        "finite_shadow_expected_int": 4,
        "countermodel_equation": "projDump_collision_defect: ||projDump(e0,e0) - projDump(e0,e1)||_1 == ||(1,0) - (1,0)||_1 == 0 (collapses distinct second-system states)",
        "countermodel_lhs": "1 - 1",
        "countermodel_rhs": "0",
        "countermodel_expected_int": 0,
        "paper_refs": [
            "papers/derivations/12_finite_qm_structure/TFQ-0256_product_defect_on_a_bipartite_weight_table.md",
            "papers/derivations/21_implementation_core/TFQ-0127_hilbert_carriers_and_tensor_index.md",
        ],
    },
    "L1-IMP-COMPLEX-FIELD": {
        "index": 27,
        "operad_family_id": "OP-L1-COMPLEX-FIELD-H007",
        "algebraic_ring": "Z[i] (Gaussian integer stand-in for C, H007 gi_not_embedded)",
        "ambient_carrier": "Gaussian integer ring Z[i] with norm N(a+bi) = a^2 + b^2",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.cochain.dhnf"],
        "finite_shadow_equation": "gaussian_unit_group_cardinality: |{1, -1, i, -i}| == 4",
        "finite_shadow_lhs": "1 + 1 + 1 + 1",
        "finite_shadow_rhs": "4",
        "finite_shadow_expected_int": 4,
        "countermodel_equation": "non_invertible_gaussian_integer_norm: N(2 + i) = 2^2 + 1^2 == 5 != 1 (not a field element inverse in Z[i])",
        "countermodel_lhs": "4 + 1",
        "countermodel_rhs": "5",
        "countermodel_expected_int": 5,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0293_complex_field_as_a_declared_carrier.md",
        ],
    },
    "L1-IMP-HAAR-INDEPENDENT-PHASES": {
        "index": 28,
        "operad_family_id": "OP-L1-HAAR-VS-FINITE-Z4-AVERAGE",
        "algebraic_ring": "Z[i] (4-point Z_4 phase average over {1, -1, i, -i})",
        "ambient_carrier": "2-sector phase average over finite group Z_4^2 (16 pairs) vs 2-point subgroup {1,-1}",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "z4_squared_16_pair_diagonal_sum: 16 * (|3|^2 + |4|^2) == 16 * 25 == 400",
        "finite_shadow_lhs": "16 * (9 + 16)",
        "finite_shadow_rhs": "400",
        "finite_shadow_expected_int": 400,
        "countermodel_equation": "correlated_equal_phase_subgroup_cross_term: 4 * (2 * 3 * 4) == 96 != 0 (without independent phases, cross term 96 survives)",
        "countermodel_lhs": "4 * 24",
        "countermodel_rhs": "96",
        "countermodel_expected_int": 96,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0301_haar-independent_phases_are_not_the_finite_average.md",
            "papers/derivations/08_l1_to_l2/TFQ-0302_phase-averaged_shadow_under_declared_phases.md",
        ],
    },
    "L1-IMP-HILBERT-INNER-PRODUCT": {
        "index": 29,
        "operad_family_id": "OP-L1-GRAM-INNER-PRODUCT-H005",
        "algebraic_ring": "Z (positive-definite Gram matrices on Z^2, H005 gram_not_unique)",
        "ambient_carrier": "2D linearized carrier Z^2 with standard Gram G_std = I_2 vs anisotropic Gram G_anis = diag(2, 3)",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "standard_gram_norm_v11: (1,1)^T I_2 (1,1) = 1 + 1 == 2",
        "finite_shadow_lhs": "1 + 1",
        "finite_shadow_rhs": "2",
        "finite_shadow_expected_int": 2,
        "countermodel_equation": "anisotropic_gram_norm_gap_v11: (1,1)^T diag(2,3) (1,1) - (1,1)^T I_2 (1,1) = 5 - 2 == 3 (distinct admissible Gram forms)",
        "countermodel_lhs": "(2 + 3) - 2",
        "countermodel_rhs": "3",
        "countermodel_expected_int": 3,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0296_hilbert_inner_product_is_admitted_structure.md",
            "papers/derivations/07_l1_emergence/TFQ-0355_stop_at_the_open_residual-to-weight_gap_and_do_not_import_a_hilbert.md",
        ],
    },
    "L1-IMP-LINEAR-ISOMETRIC-DYNAMICS": {
        "index": 30,
        "operad_family_id": "OP-L1-ISOMETRIC-DYNAMICS-H003",
        "algebraic_ring": "Z (deterministic many-to-one report map vs permutation isometry, H003 & H006)",
        "ambient_carrier": "2-state carrier with constant reset map R=[[1,1],[0,0]] vs swap permutation P=[[0,1],[1,0]]",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "permutation_l2_norm_preservation: ||P(3,4)||_2^2 = 4^2 + 3^2 == 25",
        "finite_shadow_lhs": "16 + 9",
        "finite_shadow_rhs": "25",
        "finite_shadow_expected_int": 25,
        "countermodel_equation": "reset_map_l2_norm_distortion: ||R(3,4)||_2^2 - ||(3,4)||_2^2 = (3+4)^2 - 25 = 49 - 25 == 24 != 0",
        "countermodel_lhs": "49 - 25",
        "countermodel_rhs": "24",
        "countermodel_expected_int": 24,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0303_linear_isometric_dynamics_are_an_import.md",
        ],
    },
    "L1-IMP-ORTHOGONAL-ADDITIVITY": {
        "index": 31,
        "operad_family_id": "OP-L1-ORTHOGONAL-ADDITIVITY-H013",
        "algebraic_ring": "Z (H013 frame additivity eliminating quartic rival on rotated 3D frame)",
        "ambient_carrier": "3D orthogonal frame with vector v=(3,4,0) of L^2 norm 25 and rotated frame vectors",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "quadratic_frame_sum_invariance: 3^2 + 4^2 + 0^2 == 25",
        "finite_shadow_lhs": "9 + 16 + 0",
        "finite_shadow_rhs": "25",
        "finite_shadow_expected_int": 25,
        "countermodel_equation": "quartic_frame_additivity_defect: 25^2 - (3^4 + 4^4) = 625 - 337 == 288 != 0 (quartic rule violates orthogonal frame additivity)",
        "countermodel_lhs": "625 - 337",
        "countermodel_rhs": "288",
        "countermodel_expected_int": 288,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0299_orthogonal_additivity_is_an_extra_frame_law.md",
        ],
    },
    "L1-IMP-SQRT-FIELD": {
        "index": 32,
        "operad_family_id": "OP-L1-SQRT-FIELD-EXTENSION",
        "algebraic_ring": "Q and Z (rational square-root obstruction for non-square sector weights)",
        "ambient_carrier": "2-sector weight vector w = (1/3, 2/3) (scaled integer weights (1, 2) with sum 3)",
        "normal_form_contracts": ["nf.epistemic.authority", "nf.ddc.refusal_receipt"],
        "finite_shadow_equation": "pythagorean_square_weights_lift: sqrt(9) + sqrt(16) = 3 + 4 == 7",
        "finite_shadow_lhs": "3 + 4",
        "finite_shadow_rhs": "7",
        "finite_shadow_expected_int": 7,
        "countermodel_equation": "non_square_weight_2_gap: min_{z in Z} |z^2 - 2| == 1 (2 has no square root in Z or Q; exact_amplitudes returns None)",
        "countermodel_lhs": "2 - 1^2",
        "countermodel_rhs": "1",
        "countermodel_expected_int": 1,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0292_square-root_field_for_amplitude_coordinates.md",
            "papers/derivations/09_finite_hilbert/TFQ-0318_float_lift_helper_is_not_the_exact_embedding.md",
        ],
    },
    "L1-IMP-U1-PHASES": {
        "index": 33,
        "operad_family_id": "OP-L1-U1-PHASE-GROUP-H011",
        "algebraic_ring": "Z and Z[i] (sign group Z_2 = {+1,-1} vs Z_4 = {1,-1,i,-i}, H011)",
        "ambient_carrier": "2-sector amplitude lift c_k = s_k * a_k comparing exponent-2 sign phases with order-4 Gaussian phases",
        "normal_form_contracts": ["nf.cochain.dhnf", "nf.epistemic.authority"],
        "finite_shadow_equation": "gaussian_phase_order_4: i^4 = 1 and |{1, i, -1, -i}| == 4",
        "finite_shadow_lhs": "2 + 2",
        "finite_shadow_rhs": "4",
        "finite_shadow_expected_int": 4,
        "countermodel_equation": "sign_group_exponent_two_bound: (-1)^2 == 1 and |{+1,-1}| == 2 (sign group suffices for binary destructive interference)",
        "countermodel_lhs": "1 + 1",
        "countermodel_rhs": "2",
        "countermodel_expected_int": 2,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0294_circle_phases_as_an_imported_unit_group.md",
        ],
    },
    "L1-QM020-THM2B-MINKOWSKI": {
        "index": 34,
        "operad_family_id": "OP-L1-MINKOWSKI-LP-SUBADDITIVITY",
        "algebraic_ring": "Z (strict L^2 squared-norm superadditivity on disjoint supports vs L^1 exact additivity)",
        "ambient_carrier": "Disjoint-support nonnegative integer vectors u=(3,0), v=(0,4) with u+v=(3,4)",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "l1_disjoint_support_exact_additivity: ||u+v||_1 = 3 + 4 == 7 == ||u||_1 + ||v||_1",
        "finite_shadow_lhs": "3 + 4",
        "finite_shadow_rhs": "7",
        "finite_shadow_expected_int": 7,
        "countermodel_equation": "minkowski_l2_strict_subadditivity_gap: (||u||_2 + ||v||_2)^2 - ||u+v||_2^2 = (3+4)^2 - (9+16) = 49 - 25 == 24 > 0",
        "countermodel_lhs": "49 - 25",
        "countermodel_rhs": "24",
        "countermodel_expected_int": 24,
        "paper_refs": [
            "papers/derivations/08_l1_to_l2/TFQ-0291_disjoint_aggregation_and_the_real_p_1_import.md",
        ],
    },
    "L1-QM020-THM6-P2-GLEASON": {
        "index": 35,
        "operad_family_id": "OP-L1-GLEASON-BORN-UNIQUENESS",
        "algebraic_ring": "Z (7-assumption Born-uniqueness firewall and d=3 vs d=2 frame audit, H017)",
        "ambient_carrier": "7-premise Born-uniqueness package (AdditiveWeights, ComplexHilbert, PhaseBlindDescent, OrthogonalAdditivity, IsometricDynamics, BilinearInterference, FrameStructure)",
        "normal_form_contracts": ["nf.ddc.dual_witness", "nf.epistemic.authority"],
        "finite_shadow_equation": "gleason_firewall_premise_count == 7 and min_hilbert_dim == 3 (sum 10)",
        "finite_shadow_lhs": "7 + 3",
        "finite_shadow_rhs": "10",
        "finite_shadow_expected_int": 10,
        "countermodel_equation": "d2_bloch_hemisphere_noncontextual_defect: d_min(3) - d_qubit(2) == 1 (dim 2 admits Kochen-Specker noncontextual dispersion-free countermodels without POVM)",
        "countermodel_lhs": "3 - 2",
        "countermodel_rhs": "1",
        "countermodel_expected_int": 1,
        "paper_refs": [
            "papers/derivations/09_finite_hilbert/TFQ-0307_gleason_route_for_dimension_at_least_three.md",
        ],
    },
}

from omega_engine_pfp.tests.demo_004.finite_qm_derivation_pfp.operad_mining.remaining_142_specs import (
    STAGE_RANK,
    build_remaining_142_specs,
)

DAG_REMAINING_142_SPECS: dict[str, dict[str, Any]] = build_remaining_142_specs(
    DEFAULT_DAG_PATH,
    set(DAG_PROMPT_35_SPECS.keys()),
)
DAG_ALL_177_SPECS: dict[str, dict[str, Any]] = {
    **DAG_PROMPT_35_SPECS,
    **DAG_REMAINING_142_SPECS,
}


@dataclass(frozen=True)
class DagPromptMinedOperads:
    """Output of the 4 Operad Mining Missions for a single DAG prompt node."""

    node_id: str
    stage: str
    status: str
    prompt_filename: str
    slot_m1_layer0_ambient_carrier: dict[str, Any]
    slot_m2_layer1_forward_morphisms: dict[str, Any]
    slot_m3_layer2_ideals_and_annihilators: dict[str, Any]
    slot_m4_tri_language_witness_anchors: dict[str, Any]
    rendered_system_prompt: str
    rendered_user_prompt: str
    response_schema: dict[str, Any]
    expected_ground_truth: dict[str, Any]
    rendered_user_prompt_without_m3: str = ""


def build_dag_prompt_response_schema(node_id: str, stage: str, status: str) -> dict[str, Any]:
    """Strict JSON schema (`additionalProperties: false`) for a 177-node DAG prompt run."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "derived_under_policy",
            "authority_effect",
            "firewall_status",
            "node_id",
            "stage",
            "dag_status",
            "operad_family_id",
            "p_star_tree_potentials",
            "p_star_chord_potential",
            "p_star_holonomy_gamma2",
            "cochain_d1_d0_exact_zero",
            "finite_shadow_witness_int",
            "countermodel_witness_int",
            "unpaid_import_count",
            "unconditional_promotion_refused",
            "lean4_theorem_anchor",
            "rust_witness_anchor",
            "should_continue",
        ],
        "properties": {
            "derived_under_policy": {"type": "string", "enum": ["SPK-001"]},
            "authority_effect": {"type": "string", "enum": ["None"]},
            "firewall_status": {
                "type": "string",
                "enum": ["stated region only; mints no authority."],
            },
            "node_id": {"type": "string", "enum": [node_id]},
            "stage": {"type": "string", "enum": [stage]},
            "dag_status": {"type": "string", "enum": [status]},
            "operad_family_id": {"type": "string"},
            "p_star_tree_potentials": {
                "type": "array",
                "items": {"type": "integer"},
                "minItems": 3,
                "maxItems": 3,
            },
            "p_star_chord_potential": {"type": "integer"},
            "p_star_holonomy_gamma2": {"type": "integer"},
            "cochain_d1_d0_exact_zero": {"type": "boolean"},
            "finite_shadow_witness_int": {"type": "integer"},
            "countermodel_witness_int": {"type": "integer"},
            "unpaid_import_count": {"type": "integer"},
            "unconditional_promotion_refused": {"type": "boolean"},
            "lean4_theorem_anchor": {"type": "string"},
            "rust_witness_anchor": {"type": "string"},
            "should_continue": {"type": "boolean"},
        },
    }


def _load_dag_maps(
    dag_path: Path = DEFAULT_DAG_PATH,
) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]], dict[str, list[str]]]:
    dag = json.loads(dag_path.read_text(encoding="utf-8"))
    nodes_by_id = {n["id"]: n for n in dag["nodes"]}
    in_routes: dict[str, list[str]] = {}
    out_routes: dict[str, list[str]] = {}
    for r in dag["routes"]:
        rid = r["id"]
        out_id = r.get("output")
        if out_id:
            in_routes.setdefault(out_id, []).append(rid)
        for inp in r.get("inputs", []):
            out_routes.setdefault(inp, []).append(rid)
    return nodes_by_id, in_routes, out_routes


def get_ordered_dag_prompt_files(prompts_dir: Path = DEFAULT_PROMPTS_DIR) -> list[Path]:
    """Return prompt YAML files ordered deterministically by `DAG_ALL_177_SPECS[node_id]['index']` (1..177)."""
    files = list(prompts_dir.glob("*.yaml"))

    def _sort_key(p: Path) -> tuple[int, str]:
        parts = p.stem.split("__")
        nid = parts[1] if len(parts) >= 2 else p.stem
        idx = int(DAG_ALL_177_SPECS.get(nid, {}).get("index", 9999))
        return (idx, p.name)

    return sorted(files, key=_sort_key)


def initialize_unfilled_dag_prompt_yaml(
    prompt_path: Path,
    dag_path: Path = DEFAULT_DAG_PATH,
) -> dict[str, Any]:
    """Write the Phase A multi-stage PFP YAML prompt with UNFILLED operad slots (`not at first`)."""
    nodes_by_id, in_routes, out_routes = _load_dag_maps(dag_path)
    stage, node_id, status = prompt_path.stem.split("__")
    node = nodes_by_id[node_id]
    spec = DAG_ALL_177_SPECS[node_id]

    doc: dict[str, Any] = {
        "schema_id": "omega.pfp.finite_qm.dag_prompt.v1",
        "packet_type": "PromptPacketV0_1",
        "policy_id": "SPK-001",
        "stage_controller_version": "pfp-staged.0.3",
        "operad_template": "COPP-v2-COMPACT",
        "authority_effect": "None",
        "firewall": "stated region only; mints no authority.",
        "dag_node": {
            "prompt_index": spec["index"],
            "node_id": node_id,
            "stage": stage,
            "status": status,
            "source_status": node.get("source_status", ""),
            "statement": node.get("statement", ""),
            "bottleneck": node.get("bottleneck", ""),
            "imported_structure": list(node.get("imported_structure", [])),
            "incoming_routes": in_routes.get(node_id, []),
            "outgoing_routes": out_routes.get(node_id, []),
            "source_refs": list(node.get("source", [])),
            "lean_refs": list(node.get("lean", [])),
            "rust_refs": list(node.get("rust", [])),
            "paper_refs": list(spec["paper_refs"]),
        },
        "pfp_modes_active": [
            "mode_02_packets_and_sealed_envelopes",
            "mode_04_epistemic_antibody_injections",
            "mode_05_skill_injection_and_operad_morphisms",
            "mode_08_discrete_cochain_involutions",
            "mode_09_lean4_proof_kernel_elaboration",
            "mode_10_cemetery_dag_mining",
            "mode_14_fail_closed_typed_refusal",
        ],
        "stages_plan": [
            {"stage": 1, "name": "admit", "executor": "host", "gate": "Verify YAML schema & 4 operad mining slots"},
            {"stage": "1a_1b", "name": "p_star_cochain_syndrome", "executor": "model_and_host", "gate": "G1_COCHAIN_EXACT_SEQUENCE_D1D0 + G2_P_STAR_TREE_CHORD_SYNDROME_DECODE"},
            {"stage": 2, "name": "ideation", "executor": "model", "seat": "seat_begemot", "gate": "Candidate finite shadow + countermodel ideation"},
            {"stage": 3, "name": "audit", "executor": "model", "seat": "seat_koroviev", "gate": "Congruence Ideal I & Annihilator Decoy O^- audit"},
            {"stage": 4, "name": "l2_extraction", "executor": "model", "seat": "seat_begemot", "gate": "G0_STRICT_TYPED_JSON_SCHEMA"},
            {"stage": 5, "name": "evaluation", "executor": "host", "seat": "seat_woland", "gate": "Sovereign exact integer/rational + Lean4/Rust anchor verification (< 2 ms)"},
            {"stage": 9, "name": "receipt", "executor": "host", "gate": "Emit cryptographic receipt to evidence/receipts/pfp_dag_prompts/ and update papers/"},
        ],
        "operad_slots": {
            "slot_m1_layer0_ambient_carrier": {
                "mining_status": "UNFILLED_PENDING_MINING",
                "mission_id": "M1_CARRIER_AND_NORMAL_FORM_MINING",
                "target_operad_family_hint": spec["operad_family_id"],
                "algebraic_ring": None,
                "ambient_carrier": None,
                "normal_form_contracts": [],
                "observer_budget": None,
                "p_star_cochain_syndrome": None,
            },
            "slot_m2_layer1_forward_morphisms": {
                "mining_status": "UNFILLED_PENDING_MINING",
                "mission_id": "M2_OPERAD_MORPHISMS_AND_GRAFTING_TREE_MINING",
                "operad_family_id": None,
                "source_colours": [],
                "target_colour": None,
                "operators": [],
                "planar_grafting_sequence": [],
            },
            "slot_m3_layer2_ideals_and_annihilators": {
                "mining_status": "UNFILLED_PENDING_MINING",
                "mission_id": "M3_CONGRUENCE_IDEALS_AND_DECOY_ANTIBODIES_MINING",
                "concrete_spans": {},
                "congruence_ideals": [],
                "annihilator_antibodies": [],
            },
            "slot_m4_tri_language_witness_anchors": {
                "mining_status": "UNFILLED_PENDING_MINING",
                "mission_id": "M4_TRI_LANGUAGE_EXACT_WITNESS_MINING",
                "finite_shadow_equation": None,
                "finite_shadow_lhs": None,
                "finite_shadow_rhs": None,
                "countermodel_equation": None,
                "countermodel_lhs": None,
                "countermodel_rhs": None,
                "lean4_theorem_anchor": None,
                "rust_witness_anchor": None,
            },
        },
        "system_prompt": (
            "You are a precise JSON extraction engine under SPK-001 (AuthorityEffect: None). "
            "Output ONLY a single raw JSON object matching response_schema with no markdown fences and no prose."
        ),
        "user_prompt": (
            f"[PENDING_OPERAD_MINING] Node {node_id} ({stage} / {status}). "
            "Run the 4-Mission Operad Miner (M1..M4) to populate operad_slots before live model execution."
        ),
        "response_schema": build_dag_prompt_response_schema(node_id, stage, status),
    }

    prompt_path.write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=110),
        encoding="utf-8",
    )
    return doc


def initialize_all_35_unfilled_dag_prompts(
    prompts_dir: Path = DEFAULT_PROMPTS_DIR,
    dag_path: Path = DEFAULT_DAG_PATH,
) -> list[Path]:
    """Initialize the initial 35 `.yaml` files in `dag/prompts/` with unfilled operad slots (`Phase A`)."""
    nodes_by_id, _, _ = _load_dag_maps(dag_path)
    updated: list[Path] = []
    for nid, spec in sorted(DAG_PROMPT_35_SPECS.items(), key=lambda kv: int(kv[1]["index"])):
        node = nodes_by_id[nid]
        pf = prompts_dir / f"{node['stage']}__{nid}__{node['status']}.yaml"
        initialize_unfilled_dag_prompt_yaml(pf, dag_path=dag_path)
        updated.append(pf)
    return updated


def initialize_remaining_142_unfilled_dag_prompts(
    prompts_dir: Path = DEFAULT_PROMPTS_DIR,
    dag_path: Path = DEFAULT_DAG_PATH,
) -> list[Path]:
    """Initialize the remaining 142 `.yaml` files (`36..177`) in `dag/prompts/` with unfilled operad slots."""
    nodes_by_id, _, _ = _load_dag_maps(dag_path)
    updated: list[Path] = []
    for nid, spec in sorted(DAG_REMAINING_142_SPECS.items(), key=lambda kv: int(kv[1]["index"])):
        node = nodes_by_id[nid]
        pf = prompts_dir / f"{node['stage']}__{nid}__{node['status']}.yaml"
        initialize_unfilled_dag_prompt_yaml(pf, dag_path=dag_path)
        updated.append(pf)
    return updated


def mine_operads_for_dag_prompt_node(
    node_id: str,
    dag_path: Path = DEFAULT_DAG_PATH,
    operads_path: Path = DEFAULT_OPERADS_PATH,
) -> DagPromptMinedOperads:
    """Execute the 4 Operad Mining Missions (`M1`..`M4`) for any of the 177 DAG prompt nodes."""
    nodes_by_id, in_routes, out_routes = _load_dag_maps(dag_path)
    _ = yaml.safe_load(operads_path.read_text(encoding="utf-8"))
    node = nodes_by_id[node_id]
    spec = DAG_ALL_177_SPECS[node_id]

    idx = int(spec["index"])
    stage = str(node["stage"])
    status = str(node["status"])
    r_stage = int(spec.get("stage_rank", STAGE_RANK.get(stage, 1)))
    prompt_filename = f"{stage}__{node_id}__{status}.yaml"

    # Deterministic P* 4-vertex cycle C_4 syndrome parameters for Stage 1a/1b
    # V = {0, 1, 2, 3}, v_0 = 0 (gauge root), tree edges: e0=(0,1), e1=(1,2), e2=(2,3), chord e3=(0,3)
    du_tree = [10 * idx, -30 * idx, 35 * idx]
    tree_potentials = [
        du_tree[0],
        du_tree[0] + du_tree[1],
        du_tree[0] + du_tree[1] + du_tree[2],
    ]  # [10*idx, -20*idx, 15*idx]
    chord_potential = tree_potentials[2] - 0  # 15*idx
    chord_measured_omega = -5 * idx
    holonomy_gamma2 = abs(chord_measured_omega - chord_potential)  # | -5*idx - 15*idx | = 20*idx

    lean_refs = list(node.get("lean", []))
    rust_refs = list(node.get("rust", []))
    lean_anchor = (
        lean_refs[-1]
        if lean_refs
        else "lean4/quantum_mechanics/DerivationDagQMClosure.lean::QuantumMechanics.DerivationDagQMClosure"
    )
    rust_anchor = (
        rust_refs[-1]
        if rust_refs
        else "omega_engine/crates_rs/omega_symbol_game/src/derivation_dag_witnesses.rs::build_derivation_dag_master_witness_receipt"
    )
    imported_list = list(node.get("imported_structure", []))
    unpaid_import_count = len(imported_list)

    raw_rival_int = int(spec.get("raw_candidate_rival_int", int(spec["countermodel_expected_int"]) + idx + 3 * r_stage))
    cob_shift_int = int(spec.get("coboundary_gauge_shift_int", idx + 2 * r_stage))
    sign_decoy_int = int(spec.get("sign_double_count_int", r_stage))

    # Mission M1: Layer 0 Ambient Carrier & Normal Form Mining
    slot_m1 = {
        "mining_status": "FILLED_BY_4MISSION_MINER",
        "mission_id": "M1_CARRIER_AND_NORMAL_FORM_MINING",
        "algebraic_ring": spec["algebraic_ring"],
        "ambient_carrier": spec["ambient_carrier"],
        "normal_form_contracts": list(spec["normal_form_contracts"]),
        "observer_budget": "B_O = 100 (exact integer accounting, zero float tolerance)",
        "p_star_cochain_syndrome": {
            "carrier_graph": "C_4(V=4, E=4, F=1) with gauge root v_0 = 0",
            "spanning_tree_edges": [
                {"edge": [0, 1], "du": du_tree[0]},
                {"edge": [1, 2], "du": du_tree[1]},
                {"edge": [2, 3], "du": du_tree[2]},
            ],
            "chord_edge": {"edge": [0, 3], "measured_omega": chord_measured_omega},
            "coboundary_law": "v_b - v_a = du_e on tree; chord_potential = v_3 - v_0; gamma_2 = |measured_omega - chord_potential|",
        },
    }

    # Mission M2: Layer 1 Forward Operad Morphisms & Grafting Tree Mining
    slot_m2 = {
        "mining_status": "FILLED_BY_4MISSION_MINER",
        "mission_id": "M2_OPERAD_MORPHISMS_AND_GRAFTING_TREE_MINING",
        "operad_family_id": spec["operad_family_id"],
        "incoming_routes": in_routes.get(node_id, []),
        "outgoing_routes": out_routes.get(node_id, []),
        "source_colours": ["CochainCarrierC4", "FiniteShadowSpan", "CountermodelSpan", "ImportBoundaryList"],
        "target_colour": "TypedDerivationCertificate",
        "operators": [
            {
                "id": "op_stage1_p_star_syndrome",
                "signature": "(CochainCarrierC4) -> PStarSyndromeReceipt",
                "arity": 1,
                "rule": "Integrate tree coboundaries v_1, v_2, v_3 from v_0=0, evaluate chord_potential = v_3 - v_0, and compute holonomy_gamma2 = |measured_omega - chord_potential|.",
            },
            {
                "id": "op_finite_shadow_witness",
                "signature": "(FiniteShadowSpan) -> ExactIntegerShadowWitness",
                "arity": 1,
                "rule": f"Evaluate exact finite shadow identity: {spec['finite_shadow_equation']} -> {spec['finite_shadow_lhs']} == {spec['finite_shadow_rhs']}.",
            },
            {
                "id": "op_countermodel_separation",
                "signature": "(CountermodelSpan) -> ExactCountermodelWitness",
                "arity": 1,
                "rule": f"Evaluate exact finite countermodel/obstruction: {spec['countermodel_equation']} -> {spec['countermodel_lhs']} == {spec['countermodel_rhs']}.",
            },
            {
                "id": "op_import_boundary_certificate",
                "signature": "(PStarSyndromeReceipt, ExactIntegerShadowWitness, ExactCountermodelWitness, ImportBoundaryList) -> TypedDerivationCertificate",
                "arity": 4,
                "rule": "Bind unpaid_import_count, refuse unconditional promotion (unconditional_promotion_refused = true), and attach Lean 4 and Rust anchors.",
            },
        ],
        "planar_grafting_sequence": [
            "op_stage1_p_star_syndrome -> slot_0(op_import_boundary_certificate)",
            "op_finite_shadow_witness -> slot_1(op_import_boundary_certificate)",
            "op_countermodel_separation -> slot_2(op_import_boundary_certificate)",
            "ImportBoundaryList -> slot_3(op_import_boundary_certificate)",
        ],
    }

    # Mission M3: Layer 2 Congruence Ideals & Annihilator Antibodies Mining
    slot_m3 = {
        "mining_status": "FILLED_BY_4MISSION_MINER",
        "mission_id": "M3_CONGRUENCE_IDEALS_AND_DECOY_ANTIBODIES_MINING",
        "concrete_spans": {
            "node_statement": node.get("statement", ""),
            "node_bottleneck": node.get("bottleneck", ""),
            "imported_assumptions": imported_list,
            "finite_shadow_lhs_expr": spec["finite_shadow_lhs"],
            "countermodel_lhs_expr": spec["countermodel_lhs"],
            "raw_candidate_rival_int": raw_rival_int,
            "coboundary_gauge_shift_int": cob_shift_int,
            "sign_double_count_int": sign_decoy_int,
        },
        "congruence_ideals": [
            "IDEAL_ZERO_FLOAT_TOLERANCE: All output numbers must be exact integers (no floats).",
            "IDEAL_AUTHORITY_EFFECT_NONE: authority_effect == 'None' and firewall_status == 'stated region only; mints no authority.'",
            "IDEAL_COCHAIN_D1D0_ZERO: cochain_d1_d0_exact_zero == true on the P* C_4 complex.",
            "IDEAL_QUOTIENT_COBOUNDARY_ANNIHILATION: Both coboundary_gauge_shift G_cob and boundary sign_double_count S_decoy lie in Congruence Ideal I and must be subtracted from R_raw.",
            f"IDEAL_NON_PROMOTION_FENCE: Node status is {status}; under SPK-001 (stated region only; mints no authority), unconditional_promotion_refused MUST be true even when status is PROVED_LEAN, DEFINITION, or ADMITTED_PRIMITIVE.",
        ],
        "annihilator_antibodies": [
            {
                "antibody_id": "AB_RAW_RIVAL_DECOY_TRAP",
                "target_decoy": f"Reporting unquotiented R_raw={raw_rival_int} or partially quotiented R_raw - G_cob={raw_rival_int - cob_shift_int} instead of {spec['countermodel_lhs']} == {spec['countermodel_rhs']}",
                "refutation_witness": f"NullTree: Congruence Ideal I annihilates both G_cob={cob_shift_int} and S_decoy={sign_decoy_int}, leaving {spec['countermodel_rhs']}.",
            },
            {
                "antibody_id": "AB_FALSE_UNCONDITIONAL_PROMOTION",
                "target_decoy": f"Setting unconditional_promotion_refused = false because DAG status is {status}",
                "refutation_witness": "NullTree: SPK-001 firewall refuses unconditional authority/continuum promotion for all DAG statuses.",
            },
            {
                "antibody_id": "AB_CONTINUUM_FLOAT_DRIFT",
                "target_decoy": "Emitting floating-point approximations instead of exact integer invariants",
                "refutation_witness": "NullTree: G0_STRICT_TYPED_JSON_SCHEMA rejects non-integer scalars.",
            },
        ],
    }

    # Mission M4: Tri-Language Exact Witness & Anchor Mining
    slot_m4 = {
        "mining_status": "FILLED_BY_4MISSION_MINER",
        "mission_id": "M4_TRI_LANGUAGE_EXACT_WITNESS_MINING",
        "finite_shadow_equation": spec["finite_shadow_equation"],
        "finite_shadow_lhs": spec["finite_shadow_lhs"],
        "finite_shadow_rhs": spec["finite_shadow_rhs"],
        "finite_shadow_expected_int": spec["finite_shadow_expected_int"],
        "countermodel_equation": spec["countermodel_equation"],
        "countermodel_lhs": spec["countermodel_lhs"],
        "countermodel_rhs": spec["countermodel_rhs"],
        "countermodel_expected_int": spec["countermodel_expected_int"],
        "unpaid_import_count_expected": unpaid_import_count,
        "lean4_theorem_anchor": lean_anchor,
        "rust_witness_anchor": rust_anchor,
        "paper_refs": list(spec["paper_refs"]),
    }

    rendered_system_prompt = (
        "You are a precise, fast JSON extraction engine under SPK-001 (AuthorityEffect: None). "
        "Do NOT write long reasoning; keep any thinking under 150 tokens and immediately output "
        "ONLY a single raw JSON object matching response_schema with no markdown fences and no prose."
    )

    # Full 4-Mission Operad Prompt (WITH Mission M3 Decoy Equations)
    rendered_user_prompt = (
        f"[COPP-v2-COMPACT + P* MULTI-STAGE DERIVATION TASK: {node_id}]\n"
        f"Policy: SPK-001 | AuthorityEffect: None | Firewall: stated region only; mints no authority.\n"
        f"Node: {node_id} | Stage: {stage} | DAG Status: {status}\n"
        f"Operad Family: {spec['operad_family_id']}\n\n"
        f"Layer 0 (M1 — Ambient Carrier & P* Cochain Syndrome):\n"
        f"- Algebraic Ring: {spec['algebraic_ring']}\n"
        f"- Carrier: {spec['ambient_carrier']}\n"
        f"- P* Cycle C_4 (v_0 = 0): tree edges (0->1) du={du_tree[0]}, (1->2) du={du_tree[1]}, (2->3) du={du_tree[2]}; "
        f"chord (0->3) measured_omega={chord_measured_omega}.\n"
        f"  Compute p_star_tree_potentials = [v_1, v_2, v_3] where v_1 = {du_tree[0]}, v_2 = v_1 + ({du_tree[1]}), v_3 = v_2 + ({du_tree[2]}).\n"
        f"  Compute p_star_chord_potential = v_3 - v_0 = v_3.\n"
        f"  Compute p_star_holonomy_gamma2 = |measured_omega - p_star_chord_potential| = |{chord_measured_omega} - v_3|.\n"
        f"  Set cochain_d1_d0_exact_zero = true.\n\n"
        f"Layer 1 (M2 — Operad Morphisms O^+ & Planar Grafting o_i):\n"
        f"- Op 1 (Finite Shadow Witness): {spec['finite_shadow_equation']}\n"
        f"  Evaluate finite_shadow_witness_int = {spec['finite_shadow_lhs']} (which equals {spec['finite_shadow_rhs']}).\n\n"
        f"Layer 2 (M3 — Congruence Ideals I & Annihilator Decoy Equations O^-):\n"
        f"- Decoy Equation 1 (Quotient Countermodel Reduction): {spec['countermodel_equation']}\n"
        f"  Annihilate coboundary shift G_cob={cob_shift_int} and boundary sign double-count S_decoy={sign_decoy_int} "
        f"(do NOT report unreduced R_raw={raw_rival_int} or partial {raw_rival_int - cob_shift_int}):\n"
        f"  Evaluate countermodel_witness_int = {spec['countermodel_lhs']} (which equals {spec['countermodel_rhs']}).\n"
        f"- Decoy Equation 2 (SPK-001 Non-Promotion Fence): Imported assumptions list has {unpaid_import_count} items {imported_list}.\n"
        f"  Even when DAG Status is {status}, SPK-001 refuses unconditional authority/continuum promotion beyond the stated finite carrier.\n"
        f"  Set unpaid_import_count = {unpaid_import_count} and unconditional_promotion_refused = true.\n\n"
        f"Layer 3 (M4 — Tri-Language Anchors & Exact Output Contract):\n"
        f"- Set derived_under_policy = \"SPK-001\"\n"
        f"- Set authority_effect = \"None\"\n"
        f"- Set firewall_status = \"stated region only; mints no authority.\"\n"
        f"- Set node_id = \"{node_id}\", stage = \"{stage}\", dag_status = \"{status}\"\n"
        f"- Set operad_family_id = \"{spec['operad_family_id']}\"\n"
        f"- Set lean4_theorem_anchor = \"{lean_anchor}\"\n"
        f"- Set rust_witness_anchor = \"{rust_anchor}\"\n"
        f"- Set should_continue = false\n\n"
        f"Return ONLY the raw JSON object with these exact 18 keys."
    )

    # Ablated Control Prompt (WITHOUT Mission M3 Decoy Equations — slot_m3_layer2_ideals_and_annihilators omitted)
    rendered_user_prompt_without_m3 = (
        f"[COPP-v2-COMPACT + P* MULTI-STAGE DERIVATION TASK (ABLATED WITHOUT M3 DECOY EQUATIONS): {node_id}]\n"
        f"Policy: SPK-001 | AuthorityEffect: None | Firewall: stated region only; mints no authority.\n"
        f"Node: {node_id} | Stage: {stage} | DAG Status: {status}\n"
        f"Statement: {node.get('statement', '')}\n"
        f"Operad Family: {spec['operad_family_id']}\n\n"
        f"Layer 0 (M1 — Ambient Carrier & P* Cochain Syndrome):\n"
        f"- Algebraic Ring: {spec['algebraic_ring']}\n"
        f"- Carrier: {spec['ambient_carrier']}\n"
        f"- P* Cycle C_4 (v_0 = 0): tree edges (0->1) du={du_tree[0]}, (1->2) du={du_tree[1]}, (2->3) du={du_tree[2]}; "
        f"chord (0->3) measured_omega={chord_measured_omega}.\n"
        f"  Compute p_star_tree_potentials = [v_1, v_2, v_3] where v_1 = {du_tree[0]}, v_2 = v_1 + ({du_tree[1]}), v_3 = v_2 + ({du_tree[2]}).\n"
        f"  Compute p_star_chord_potential = v_3 - v_0 = v_3.\n"
        f"  Compute p_star_holonomy_gamma2 = |measured_omega - p_star_chord_potential| = |{chord_measured_omega} - v_3|.\n"
        f"  Set cochain_d1_d0_exact_zero = true.\n\n"
        f"Layer 1 (M2 — Operad Morphisms O^+ & Candidate Witness Parameters [M3 Decoy Equations Omitted]):\n"
        f"- Op 1 (Finite Shadow Witness): {spec['finite_shadow_equation']}\n"
        f"  Evaluate finite_shadow_witness_int = {spec['finite_shadow_lhs']} (which equals {spec['finite_shadow_rhs']}).\n"
        f"- Op 2 (Candidate Countermodel Parameters — Unreduced): "
        f"Candidate rival functional raw value R_raw = {raw_rival_int}, coboundary gauge shift parameter G_cob = {cob_shift_int}, "
        f"boundary sign double-count parameter S_decoy = {sign_decoy_int}. "
        f"Determine integer countermodel_witness_int for node {node_id}.\n"
        f"- Op 3 (Import Boundary & Promotion): Imported assumptions list has {unpaid_import_count} items {imported_list}. "
        f"Set unpaid_import_count = {unpaid_import_count}. Given DAG Status = {status} and Policy = SPK-001, "
        f"determine boolean unconditional_promotion_refused.\n\n"
        f"Layer 3 (M4 — Tri-Language Anchors & Exact Output Contract):\n"
        f"- Set derived_under_policy = \"SPK-001\"\n"
        f"- Set authority_effect = \"None\"\n"
        f"- Set firewall_status = \"stated region only; mints no authority.\"\n"
        f"- Set node_id = \"{node_id}\", stage = \"{stage}\", dag_status = \"{status}\"\n"
        f"- Set operad_family_id = \"{spec['operad_family_id']}\"\n"
        f"- Set lean4_theorem_anchor = \"{lean_anchor}\"\n"
        f"- Set rust_witness_anchor = \"{rust_anchor}\"\n"
        f"- Set should_continue = false\n\n"
        f"Return ONLY the raw JSON object with these exact 18 keys."
    )

    expected_ground_truth = {
        "derived_under_policy": "SPK-001",
        "authority_effect": "None",
        "firewall_status": "stated region only; mints no authority.",
        "node_id": node_id,
        "stage": stage,
        "dag_status": status,
        "operad_family_id": spec["operad_family_id"],
        "p_star_tree_potentials": tree_potentials,
        "p_star_chord_potential": chord_potential,
        "p_star_holonomy_gamma2": holonomy_gamma2,
        "cochain_d1_d0_exact_zero": True,
        "finite_shadow_witness_int": int(spec["finite_shadow_expected_int"]),
        "countermodel_witness_int": int(spec["countermodel_expected_int"]),
        "unpaid_import_count": unpaid_import_count,
        "unconditional_promotion_refused": True,
        "lean4_theorem_anchor": lean_anchor,
        "rust_witness_anchor": rust_anchor,
        "should_continue": False,
    }

    return DagPromptMinedOperads(
        node_id=node_id,
        stage=stage,
        status=status,
        prompt_filename=prompt_filename,
        slot_m1_layer0_ambient_carrier=slot_m1,
        slot_m2_layer1_forward_morphisms=slot_m2,
        slot_m3_layer2_ideals_and_annihilators=slot_m3,
        slot_m4_tri_language_witness_anchors=slot_m4,
        rendered_system_prompt=rendered_system_prompt,
        rendered_user_prompt=rendered_user_prompt,
        response_schema=build_dag_prompt_response_schema(node_id, stage, status),
        expected_ground_truth=expected_ground_truth,
        rendered_user_prompt_without_m3=rendered_user_prompt_without_m3,
    )


def populate_mined_operads_into_prompt_yaml(
    prompt_path: Path,
    dag_path: Path = DEFAULT_DAG_PATH,
    operads_path: Path = DEFAULT_OPERADS_PATH,
) -> DagPromptMinedOperads:
    """Run the 4 Operad Mining Missions for `prompt_path` and write the filled operad slots to disk."""
    _, node_id, _ = prompt_path.stem.split("__")
    mined = mine_operads_for_dag_prompt_node(
        node_id=node_id,
        dag_path=dag_path,
        operads_path=operads_path,
    )
    if not prompt_path.exists():
        doc = initialize_unfilled_dag_prompt_yaml(prompt_path, dag_path=dag_path)
    else:
        doc = yaml.safe_load(prompt_path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or "operad_slots" not in doc:
            doc = initialize_unfilled_dag_prompt_yaml(prompt_path, dag_path=dag_path)

    doc["operad_slots"]["slot_m1_layer0_ambient_carrier"] = mined.slot_m1_layer0_ambient_carrier
    doc["operad_slots"]["slot_m2_layer1_forward_morphisms"] = mined.slot_m2_layer1_forward_morphisms
    doc["operad_slots"]["slot_m3_layer2_ideals_and_annihilators"] = mined.slot_m3_layer2_ideals_and_annihilators
    doc["operad_slots"]["slot_m4_tri_language_witness_anchors"] = mined.slot_m4_tri_language_witness_anchors
    doc["system_prompt"] = mined.rendered_system_prompt
    doc["user_prompt"] = mined.rendered_user_prompt
    doc["user_prompt_without_m3_ablation"] = mined.rendered_user_prompt_without_m3
    doc["response_schema"] = mined.response_schema

    prompt_path.write_text(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=110),
        encoding="utf-8",
    )
    return mined


@dataclass(frozen=True)
class MinedOperadCompositionRule:
    """Typed Coloured Operad composition rule mined from the Finite-QM DAG."""

    operad_id: str
    family_name: str
    stage: str
    source_colours: tuple[str, ...]
    target_colour: str
    arity: int
    route_ids: tuple[str, ...]
    node_ids: tuple[str, ...]
    congruence_ideal: str
    annihilator_decoy: str


@dataclass(frozen=True)
class MinedDerivationWorkUnit:
    """Self-contained executable derivation work-unit for batch or manual execution."""

    work_id: str
    ordinal: int
    operad_id: str
    stage: str
    node_id: str
    route_id: str
    status: str
    statement: str
    tree_potentials: list[int]
    chord_potentials: list[int]
    phi1_exact_int: int
    gamma2_exact_int: int
    witness_invariant_int: int
    lean_symbol: str
    rust_symbol: str

    def to_expected_ground_truth(self) -> dict[str, Any]:
        return {
            "work_id": self.work_id,
            "authority_effect": "None",
            "operad_id": self.operad_id,
            "stage": self.stage,
            "node_id": self.node_id,
            "route_id": self.route_id,
            "status": self.status,
            "tree_potentials": list(self.tree_potentials),
            "chord_potentials": list(self.chord_potentials),
            "cochain_d1_d0_zero": True,
            "phi1_exact_int": self.phi1_exact_int,
            "gamma2_exact_int": self.gamma2_exact_int,
            "witness_invariant_int": self.witness_invariant_int,
            "lean_symbol": self.lean_symbol,
            "rust_symbol": self.rust_symbol,
        }


class FiniteQmOperadMiner:
    """Mines all 177 nodes, 172 routes, and 25 operad families of the Finite-QM DAG."""

    def __init__(
        self,
        dag_path: Path = DEFAULT_DAG_PATH,
        operads_path: Path = DEFAULT_OPERADS_PATH,
    ) -> None:
        self.dag_path = Path(dag_path)
        self.operads_path = Path(operads_path)
        self.dag_data: dict[str, Any] = json.loads(self.dag_path.read_text(encoding="utf-8"))
        self.operads_data: dict[str, Any] = yaml.safe_load(self.operads_path.read_text(encoding="utf-8"))

    def mine_all_operad_rules(self) -> list[MinedOperadCompositionRule]:
        rules: list[MinedOperadCompositionRule] = []
        families = self.operads_data.get("operad_families", [])
        for idx, fam in enumerate(families, 1):
            op_id = str(fam.get("id", f"OP-FAM-{idx:02d}"))
            name = str(fam.get("name", op_id))
            stage = str(fam.get("stage", "FINITE_QM_CORE"))
            nids = tuple(str(x) for x in fam.get("nodes", fam.get("covered_nodes", [])))
            rids = tuple(str(x) for x in fam.get("routes", fam.get("covered_routes", [])))
            rules.append(
                MinedOperadCompositionRule(
                    operad_id=op_id,
                    family_name=name,
                    stage=stage,
                    source_colours=("CochainCarrier", "SectorWeights"),
                    target_colour="FiniteQmWitness",
                    arity=max(1, len(rids)),
                    route_ids=rids,
                    node_ids=nids,
                    congruence_ideal="IDEAL_EXACT_INTEGER_RATIONAL_SUBSTRATE",
                    annihilator_decoy="AB_NO_UNPAID_CONTINUUM_PROMOTION",
                )
            )
        return rules

    def generate_derivation_work_units(self, target_count: int = 1000) -> list[MinedDerivationWorkUnit]:
        nodes = self.dag_data.get("nodes", [])
        routes = self.dag_data.get("routes", [])
        units: list[MinedDerivationWorkUnit] = []
        for ordinal in range(1, target_count + 1):
            node = nodes[(ordinal - 1) % len(nodes)]
            route = routes[(ordinal - 1) % len(routes)]
            nid = str(node["id"])
            rid = str(route["id"])
            stage = str(node.get("stage", "FINITE_QM_CORE"))
            status = str(node.get("status", "PROVED_LEAN"))
            lean_list = node.get("lean", [])
            rust_list = node.get("rust", [])
            lean_sym = str(lean_list[0]) if lean_list else "DerivationDagQMClosure"
            rust_sym = str(rust_list[0]) if rust_list else "build_derivation_dag_master_witness_receipt"
            seed = int(sha256(f"{ordinal}:{nid}:{rid}".encode("utf-8")).hexdigest()[:6], 16)
            t1 = (seed % 97) - 48
            t2 = ((seed // 7) % 89) - 44
            t3 = ((seed // 13) % 83) - 41
            c1 = t3 - t1
            c2 = t2 - t1
            phi1 = abs(t1) + abs(t2) + abs(t3)
            gamma2 = abs(c1) + abs(c2)
            inv = phi1 * 3 + gamma2 * 2 + (ordinal % 17)
            units.append(
                MinedDerivationWorkUnit(
                    work_id=f"fqm_work_{ordinal:04d}_{nid[:18].lower()}",
                    ordinal=ordinal,
                    operad_id=f"OP-{stage}",
                    stage=stage,
                    node_id=nid,
                    route_id=rid,
                    status=status,
                    statement=str(node.get("statement", ""))[:160],
                    tree_potentials=[t1, t2, t3],
                    chord_potentials=[c1, c2],
                    phi1_exact_int=phi1,
                    gamma2_exact_int=gamma2,
                    witness_invariant_int=inv,
                    lean_symbol=lean_sym,
                    rust_symbol=rust_sym,
                )
            )
        return units
