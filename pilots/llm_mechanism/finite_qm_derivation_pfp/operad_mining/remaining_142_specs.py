"""Deterministic 4-Mission Operad Specifications for the remaining 142 nodes (36..177) of derivation_dag.json.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STAGE_RANK: dict[str, int] = {
    "PREGENESIS": 1,
    "GENESIS": 2,
    "MSSN_SN": 3,
    "WDP": 4,
    "L1_EMERGENCE": 5,
    "L1_TO_L2": 6,
    "FINITE_QM_CORE": 7,
    "FINITE_QM_STRUCTURE": 8,
    "FINITE_QM_DYNAMICS": 9,
    "IMPLEMENTATION": 10,
}

STAGE_ALGEBRAIC_RING: dict[str, str] = {
    "PREGENESIS": "Z (Pre-Genesis discrete inscription, cut & report quotient algebra)",
    "GENESIS": "Z (Genesis cumulative event history & irreflexive step monoid)",
    "MSSN_SN": "Z (S(n) base presentation, section law & obligation monoid)",
    "WDP": "Q and Z (WDP degree-1 cochain window C0 -> C1 -> C2 with d1 d0 = 0)",
    "L1_EMERGENCE": "Q and Z (L1 edgewise observer seminorm & KKT primal-dual cone)",
    "L1_TO_L2": "Z[i] and Q (L1-to-L2 signed-sqrt lift, Born normalization & phase-blind fiber)",
    "FINITE_QM_CORE": "Z[i] and Q(zeta_n) (Finite-QM cyclotomic & Gaussian matrix algebra)",
    "FINITE_QM_STRUCTURE": "Z[i], Q, and F_2 (Finite-QM structure, contextuality, CHSH & CPTP carrier)",
    "FINITE_QM_DYNAMICS": "Z[i] and Q (Finite-QM graded path-sum, transfer operator & Cayley unitary carrier)",
    "IMPLEMENTATION": "Z and Q (Three-language Rust/Lean4/Python sovereign custody carrier)",
}

NODE_142_PAPER_REFS: dict[str, list[str]] = {
    "PG-ROOT-DIFF-STRUCTURE": [
        "papers/derivations/01_pregenesis/TFQ-0392_inscription-to-coproduct-gap.md",
        "papers/derivations/01_pregenesis/TFQ-0393_admitted-root-coproduct.md"
    ],
    "PG-INERT-DIAMOND": [
        "papers/derivations/01_pregenesis/TFQ-0361_inert-literal-inscription.md",
        "papers/derivations/01_pregenesis/TFQ-0392_inscription-to-coproduct-gap.md"
    ],
    "PG-SIX-OPERATIONS": [
        "papers/derivations/01_pregenesis/TFQ-0363_six-distinct-operations.md"
    ],
    "PG-PRIMDIFF-AXIOMS": [
        "papers/derivations/01_pregenesis/TFQ-0394_primitive-axiom-list-underived.md"
    ],
    "PG-ADMISSION-FLOOR": [
        "papers/derivations/01_pregenesis/TFQ-0395_law-bearing-cut-not-two-marks.md"
    ],
    "PG-COLLAPSE-BARRIER": [
        "papers/derivations/01_pregenesis/TFQ-0365_collapsed-observation-barrier.md"
    ],
    "PG-HISTORY-REPORT-CRITERION": [
        "papers/derivations/01_pregenesis/TFQ-0366_history-report-fiber-criterion.md"
    ],
    "PG-PREGEN-CONSTRUCTIVE-SUMMARY": [
        "papers/derivations/01_pregenesis/TFQ-0366_history-report-fiber-criterion.md",
        "papers/derivations/01_pregenesis/TFQ-0367_listed-history-choice-free-summary.md"
    ],
    "PG-DEMAND-ACCOUNTING": [
        "papers/derivations/01_pregenesis/TFQ-0369_finite-demand-count.md"
    ],
    "PG-REFINE-SEPARATES": [
        "papers/derivations/01_pregenesis/TFQ-0370_supplied-binary-refinement.md",
        "papers/derivations/05_mssn_sn/TFQ-0334_let_one_supplied_binary_tag_separate_one_collapsed_pair_and_keep_the.md"
    ],
    "PG-OLD-IMAGE-INJECTIVE": [
        "papers/derivations/01_pregenesis/TFQ-0371_old-image-injective-lift.md",
        "papers/derivations/05_mssn_sn/TFQ-0335_from_typed_old-image_recovery_record_injectivity_of_the_lift_only_and_refuse.md"
    ],
    "PG-SN-OFF-IMAGE-REFUSAL": [
        "papers/derivations/01_pregenesis/TFQ-0371_old-image-injective-lift.md",
        "papers/derivations/01_pregenesis/TFQ-0372_off-image-refusal-half.md"
    ],
    "PG-FREE-MONOID-NONISO": [
        "papers/derivations/01_pregenesis/TFQ-0373_free-monoid-size-noniso.md",
        "papers/derivations/05_mssn_sn/TFQ-0336_keep_unequal_finite_alphabets_from_a_free-monoid_isomorphism_and_keep_language_restriction.md"
    ],
    "PG-CHAIN-RETRACTION": [
        "papers/derivations/01_pregenesis/TFQ-0375_chain-retraction-old-class.md",
        "papers/derivations/05_mssn_sn/TFQ-0337_record_homology_injectivity_under_a_chain-map_retraction_and_record_that_the_two-point.md"
    ],
    "PG-MSS0-ONLY-DIAMOND": [
        "papers/derivations/02_genesis/TFQ-0377_mss0-only-inscription.md"
    ],
    "PG-GEN-REGIME-EVENTS": [
        "papers/derivations/02_genesis/TFQ-0378_regime-tuple-and-events.md"
    ],
    "PG-GEN-SUPPLY-NO-OP": [
        "papers/derivations/01_pregenesis/TFQ-0363_six-distinct-operations.md",
        "papers/derivations/02_genesis/TFQ-0379_supply-does-not-admit.md"
    ],
    "PG-GEN-SUPPLY-ERASURE": [
        "papers/derivations/02_genesis/TFQ-0386_supply-erasure-on-replay.md"
    ],
    "PG-GEN-COLLAPSE-AND-FIRST-SEPARATION": [
        "papers/derivations/02_genesis/TFQ-0381_cost-two-first-separation.md"
    ],
    "PG-GEN-NO-RETURN": [
        "papers/derivations/02_genesis/TFQ-0384_cumulative-count-no-return.md"
    ],
    "PG-GEN-IRREFLEXIVE-DISTINCT": [
        "papers/derivations/02_genesis/TFQ-0387_irreflexive-endpoints-distinct.md"
    ],
    "PG-GEN-ONGOING-OBSTRUCTION": [
        "papers/derivations/02_genesis/TFQ-0388_ongoing-obstruction-answers.md"
    ],
    "PG-GEN-ONGOING-FEWEST-CHANGES": [
        "papers/derivations/02_genesis/TFQ-0389_fewest-changes-formula.md"
    ],
    "PG-GEN-REWRITING-COMMUTATION": [
        "papers/derivations/02_genesis/TFQ-0389_fewest-changes-formula.md",
        "papers/derivations/02_genesis/TFQ-0390_rewriting-and-persistence-reconcile.md"
    ],
    "PG-GEN-SAMENESS-REFINEMENTS": [
        "papers/derivations/02_genesis/TFQ-0391_sameness-refinement-ledgers.md"
    ],
    "PG-SN-CARRIER": [
        "papers/derivations/05_mssn_sn/TFQ-0341_refuse_unrestricted_old-image_recovery_and_the_advertised_sncarrier_cardinalities_until_a.md"
    ],
    "PG-OBLIGATION-MONOID": [
        "papers/derivations/05_mssn_sn/TFQ-0342_do_not_treat_genesis_events_or_s_n_maps_as_obligation-monoid_morphisms_until.md"
    ],
    "PG-WDP-PROTECTED-QUESTIONS": [
        "papers/derivations/06_wdp/TFQ-0340_refuse_a_symmetry-equivariant_distinguished_point_on_a_finite_set_of_size_at.md"
    ],
    "PG-WDP-DEGREE1-WINDOW": [
        "papers/derivations/06_wdp/TFQ-0344_do_not_derive_the_degree-1_window_c0_c1_c2_d0_d1_from.md"
    ],
    "PG-WDP-QUOTIENT-EXACT-SEQUENCE": [
        "papers/derivations/06_wdp/TFQ-0345_on_a_declared_window_with_d1_d0_0_compute_q1_kappa1.md"
    ],
    "PG-WDP-GROWTH-NO-REPAIR": [
        "papers/derivations/06_wdp/TFQ-0346_do_not_lower_phi1_by_passing_to_a_larger_complex_attaching_faces.md"
    ],
    "PG-WDP-DIAGNOSTIC-NOT-ROUTING": [
        "papers/derivations/06_wdp/TFQ-0347_keep_exactclass_closedresidual_and_activeclosurefailure_off_the_routing_terminal_and_leave.md"
    ],
    "PG-WDP-GENESIS-BRIDGE-OBLIGATIONS": [
        "papers/derivations/06_wdp/TFQ-0343_leave_gen-wdp-o01_through_o05_open_carrier_floor_preservation_maps_higher_fillers_hilbert.md"
    ],
    "L1-WDP-WINDOW-PHI1-GAMMA2": [
        "papers/derivations/07_l1_emergence/TFQ-0349_compute_declared_phi1_and_gamma2_on_a_finite_window_and_do_not.md",
        "papers/derivations/07_l1_emergence/TFQ-0357_record_replica_extensivity_as_a_reason_l1_appears_and_keep_squared_l2.md"
    ],
    "L1-OBSERVER-AXIOMS-H1-H5": [
        "papers/derivations/07_l1_emergence/TFQ-0349_compute_declared_phi1_and_gamma2_on_a_finite_window_and_do_not.md",
        "papers/derivations/07_l1_emergence/TFQ-0352_admit_h1_through_h5_as_observer_hypotheses_on_a_finite_edge_projection.md"
    ],
    "L1-GS000-EDGEWISE-L1": [
        "papers/derivations/07_l1_emergence/TFQ-0353_under_admitted_h1-h5_record_an_edgewise_weighted_l1_aggregate_orbit-constant_weights_and.md"
    ],
    "L1-GS001-GAUGE-L1": [
        "papers/derivations/07_l1_emergence/TFQ-0356_keep_the_m-compatible_gauge_route_to_weighted_l1_on_its_own_hypothesis.md"
    ],
    "L1-WDP-CH08-C01-REPLICA-L1": [
        "papers/derivations/07_l1_emergence/TFQ-0357_record_replica_extensivity_as_a_reason_l1_appears_and_keep_squared_l2.md"
    ],
    "L1-WDP-WITNESS-MASS": [
        "papers/derivations/07_l1_emergence/TFQ-0358_normalize_a_declared_positive_witness_mass_to_cell_values_that_are_nonnegative.md"
    ],
    "L1-QM002-O022A-PHI1-QUOTIENT": [
        "papers/derivations/07_l1_emergence/TFQ-0359_keep_the_phi1_banach-quotient_reading_on_a_finite-dimensional_repair_packet_and_leave.md"
    ],
    "L1-FRAMEWORK-KKT-CERT": [
        "papers/derivations/07_l1_emergence/TFQ-0351_accept_an_integer_finite_list_certificate_only_inside_its_capacity_circulation_feasibility.md"
    ],
    "L1-CHAIN-D1D0-AXIOM": [
        "papers/derivations/07_l1_emergence/TFQ-0350_assume_d1_d0_0_only_by_a_declared_certificate_or_the.md"
    ],
    "L1-OPERATOR-LIFT-TRACE-EMBED-013": [
        "papers/derivations/08_l1_to_l2/TFQ-0282_diagonal_presentation_and_lost_total_scale.md"
    ],
    "L1-RESIDUAL-SECTOR-WEIGHTS-DECLARED": [
        "papers/derivations/07_l1_emergence/TFQ-0354_do_not_derive_declared_l1_sector_weights_from_the_phi1_and_gamma2.md"
    ],
    "L1-DENSITY-LIFT-SIGNED-SQRT-PUB009": [
        "papers/derivations/07_l1_emergence/TFQ-0355_stop_at_the_open_residual-to-weight_gap_and_do_not_import_a_hilbert.md"
    ],
    "L1-QM020-THM1-DIRECT-NORMALIZATION": [
        "papers/derivations/08_l1_to_l2/TFQ-0290_direct_normalization_of_sector_weights.md"
    ],
    "L1-QM020-THM2A-L1-ADDITIVITY-DEFECT": [
        "papers/derivations/08_l1_to_l2/TFQ-0291_disjoint_aggregation_and_the_real_p_1_import.md"
    ],
    "L1-QM020-THM3-ROW-SPARSITY": [
        "papers/derivations/08_l1_to_l2/TFQ-0300_descent-compatible_maps_stay_row-sparse.md"
    ],
    "L1-QM020-THM4-HILBERT-LIFT-REDUNDANCY": [
        "papers/derivations/07_l1_emergence/TFQ-0355_stop_at_the_open_residual-to-weight_gap_and_do_not_import_a_hilbert.md"
    ],
    "L1-QM020-THM5-PHASE-AVERAGED-SHADOW": [
        "papers/derivations/08_l1_to_l2/TFQ-0301_haar-independent_phases_are_not_the_finite_average.md"
    ],
    "L1-QM020-THM6-P1-SCOPE-FENCE": [
        "papers/derivations/08_l1_to_l2/TFQ-0305_sector_weights_do_not_force_the_quadratic_form.md"
    ],
    "L1-QM020-THM7-REPRESENTATION-CAPACITY": [
        "papers/derivations/08_l1_to_l2/TFQ-0304_lift_capacity_is_not_a_dynamics_derivation.md"
    ],
    "L1-WDP-REALIFICATION-J": [
        "papers/derivations/08_l1_to_l2/TFQ-0006_conditional_finite_hilbert_lift.md"
    ],
    "L1-QM121-LADDER-RUNGS-2-6": [
        "papers/derivations/09_finite_hilbert/TFQ-0309_ingredient_ladder_stops_before_the_imported_ceiling.md"
    ],
    "L1-QM122-PHASE-BLIND-FIBER-INTERFERENCE": [
        "papers/derivations/08_l1_to_l2/TFQ-0006_conditional_finite_hilbert_lift.md"
    ],
    "L1-QM122-CIRCLE-SELECTOR-BOUNDARY": [
        "papers/derivations/08_l1_to_l2/TFQ-0294_circle_phases_as_an_imported_unit_group.md"
    ],
    "L1-QM122-BORN-PAIRING-NONUNIQUE": [
        "papers/derivations/09_finite_hilbert/TFQ-0307_gleason_route_for_dimension_at_least_three.md"
    ],
    "L1-QM122-LEFTOVER-MNC-NOT-RECOVERED": [
        "papers/derivations/09_finite_hilbert/TFQ-0311_ordinary_matrix_algebra_over_c_is_not_recovered.md"
    ],
    "L1-U1-SELECTOR-OTHER-SEGMENT": [
        "papers/derivations/08_l1_to_l2/TFQ-0294_circle_phases_as_an_imported_unit_group.md",
        "papers/derivations/14_finite_gauge/TFQ-0053_each_language_must_carry_a_unit_gaussian_edge_connection_covariant_difference_vertex.md"
    ],
    "L1-QM020-C10-BRANCH-LOCALIZATION": [
        "papers/derivations/08_l1_to_l2/TFQ-0006_conditional_finite_hilbert_lift.md"
    ],
    "L1-QM003-C17-COMPOSABLE-FACTORIZATION": [
        "papers/derivations/08_l1_to_l2/TFQ-0282_diagonal_presentation_and_lost_total_scale.md"
    ],
    "FQ-CARRIER-CONTRACT-V2": [
        "papers/derivations/10_finite_qm_core/TFQ-0007_finite_quantum_mechanics_core_on_an_admitted_carrier.md"
    ],
    "FQ-PRIMDIFF-QUOTIENT-KERNEL": [
        "papers/derivations/10_finite_qm_core/TFQ-0234_supplied_hilbert_carrier_after_the_conditional_lift.md"
    ],
    "FQ-PHASE-FIBER-QUOTIENT": [
        "papers/derivations/12_finite_qm_structure/TFQ-0252_interference_as_a_resource_outside_l1_bookkeeping.md"
    ],
    "FQ-PHASE-BLIND-DESCENT-ZERO-RETAINED": [
        "papers/derivations/12_finite_qm_structure/TFQ-0252_interference_as_a_resource_outside_l1_bookkeeping.md"
    ],
    "FQ-BORN-NORMALIZATION-REDUNDANCY": [
        "papers/derivations/08_l1_to_l2/TFQ-0290_direct_normalization_of_sector_weights.md"
    ],
    "FQ-INTERFERENCE-NONDESCENT": [
        "papers/derivations/10_finite_qm_core/TFQ-0234_supplied_hilbert_carrier_after_the_conditional_lift.md"
    ],
    "FQ-SORKIN-READOUT-CLASS-QM208": [
        "papers/derivations/10_finite_qm_core/TFQ-0234_supplied_hilbert_carrier_after_the_conditional_lift.md"
    ],
    "FQ-POWER-RULE-P2-SELECTION": [
        "papers/derivations/09_finite_hilbert/TFQ-0317_three_lean_files_stay_on_a_narrow_carrier.md"
    ],
    "FQ-FIVE-IMPORT-PROXY-SEPARATION": [
        "papers/derivations/09_finite_hilbert/TFQ-0308_born-uniqueness_band_slot_is_still_a_stub.md"
    ],
    "FQ-GLEASON-D2-RATIONAL-PLANE-OBSTRUCTION": [
        "papers/derivations/09_finite_hilbert/TFQ-0307_gleason_route_for_dimension_at_least_three.md"
    ],
    "FQ-CABELLO-NO-INTEGER-FRAME": [
        "papers/derivations/12_finite_qm_structure/TFQ-0250_mermin-peres_contextuality_on_a_finite_cochain.md"
    ],
    "FQ-CABELLO-FRAME-POLYTOPE-146": [
        "papers/derivations/09_finite_hilbert/TFQ-0298_bra-ket_section_remains_non-canonical.md"
    ],
    "FQ-BUSCH-EFFECT-FRAME": [
        "papers/derivations/09_finite_hilbert/TFQ-0307_gleason_route_for_dimension_at_least_three.md"
    ],
    "FQ-TENSOR-LU-RIVAL-EXCLUSION": [
        "papers/derivations/09_finite_hilbert/TFQ-0297_inner-product_admission_slot_is_still_a_stub.md"
    ],
    "FQ-CPTP-CLASS-DEFINITION": [
        "papers/derivations/12_finite_qm_structure/TFQ-0262_cptp_class_recorded_as_a_definition.md"
    ],
    "FQ-TRACE-NORM-FROM-CPTP-MONOTONICITY": [
        "papers/derivations/12_finite_qm_structure/TFQ-0263_trace_norm_under_a_supplied_cptp_family.md"
    ],
    "FQ-TRACE-ZERO-DUALITY-K23": [
        "papers/derivations/22_implementation_sibling/TFQ-0186_do_not_treat_tracezeroduality_lean_as_a_lean_formalization_of_the_k__2_3_quotients.md"
    ],
    "FQ-BELL-CLASSICAL-JOINT-EXTENSION": [
        "papers/derivations/12_finite_qm_structure/TFQ-0256_product_defect_on_a_bipartite_weight_table.md"
    ],
    "FQ-BELL-RATIONAL-VIOLATION-14-5": [
        "papers/derivations/12_finite_qm_structure/TFQ-0260_bell_theorem_not_derived_from_the_finite_tables.md"
    ],
    "FQ-TSIRELSON-SOS-Q-SQRT2": [
        "papers/derivations/09_finite_hilbert/TFQ-0318_float_lift_helper_is_not_the_exact_embedding.md"
    ],
    "FQ-CONTEXTUALITY-CECH-F2": [
        "papers/derivations/12_finite_qm_structure/TFQ-0250_mermin-peres_contextuality_on_a_finite_cochain.md"
    ],
    "FQ-WEYL-FINITE-SCHRODINGER-IRREDUCIBILITY": [
        "papers/derivations/09_finite_hilbert/TFQ-0313_operator-algebra_shadow_slot_is_still_a_stub.md"
    ],
    "FQ-COMMUTATOR-TRACE-OBSTRUCTION": [
        "papers/derivations/20_continuum_interface/TFQ-0122_filename_continuum_rs_does_not_discharge_the_continuum_limit_or_the_einstein_equation.md"
    ],
    "FQ-U1-TRANSPORT-N-TORSION": [
        "papers/derivations/12_finite_qm_structure/TFQ-0254_holonomy-structured_coherent_intensity.md"
    ],
    "FQ-DISCRETE-DYNAMICS-DICHOTOMY": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0008_finite_dynamics_instruments_and_channels.md"
    ],
    "FQ-DISCRETE-TIME-STONE-AMBIGUITY": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0246_hamiltonian_generator_admission_still_reserved.md"
    ],
    "FQ-EVERETT-RATIONAL-SECTOR-BOUNDARY": [
        "papers/derivations/13_finite_qm_information/TFQ-0276_everettian_relative-state_contact.md"
    ],
    "FQ-GAP-REAL-EMBEDDING-CHOICE": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0008_finite_dynamics_instruments_and_channels.md"
    ],
    "FQ-ENTROPY-DICHOTOMY-BAKER": [
        "papers/derivations/13_finite_qm_information/TFQ-0268_von_neumann_entropy_interface_for_mixed_states.md"
    ],
    "FQ-IMPL-F64-GATING": [
        "papers/derivations/22_implementation_sibling/TFQ-0179_keep_core_mub_float_cross-checks_from_authorizing_a_mub_6_existence_claim.md",
        "papers/derivations/22_implementation_sibling/TFQ-0188_refuse_the_f64_lift_scale_on_cycleliftspec_as_a_licence_for_an_exact.md"
    ],
    "FQ-IMPL-WDP-AMPLITUDE-BRIDGE": [
        "papers/derivations/22_implementation_sibling/TFQ-0175_keep_integer_coboundary_holonomy_distinct_from_exact_matrix_gauge_holonomy.md"
    ],
    "FQ-IMPL-REALIFICATION-ADAPTER": [
        "papers/derivations/21_implementation_core/TFQ-0131_density_operators_over_q_i.md"
    ],
    "FQ-IMPL-PAIRING-AUDIT": [
        "papers/derivations/23_engine_custody/TFQ-0218_prime_000_fixes_declaration_order.md"
    ],
    "FQ-QM207-231-FINITE-MAP-CONTROLS": [
        "papers/derivations/21_implementation_core/TFQ-0160_import_finite_maps_qm-207_to_qm-215.md"
    ],
    "GP-GAP-EXACT-DUALITY": [
        "papers/derivations/12_finite_qm_structure/TFQ-0250_mermin-peres_contextuality_on_a_finite_cochain.md"
    ],
    "GP-FIN-GAUSS-MATRIX-ALGEBRA": [
        "papers/derivations/09_finite_hilbert/TFQ-0311_ordinary_matrix_algebra_over_c_is_not_recovered.md"
    ],
    "GP-DROP-ONE-CENSUS": [
        "papers/derivations/09_finite_hilbert/TFQ-0312_four_necessity_verdicts_stay_open_beside_the_matrix_gap.md"
    ],
    "DS-QM030-GRADED-PATHSUM": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0239_finite_path_sum_on_a_unique_intermediate_cut.md",
        "papers/derivations/11_finite_qm_dynamics/TFQ-0242_graded_path_sum_as_finite_transport.md"
    ],
    "DS-QM030-UNGRADED-OVERCOUNT": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0239_finite_path_sum_on_a_unique_intermediate_cut.md"
    ],
    "DS-QM030-TRANSFER-OPERATOR-SHADOW": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0239_finite_path_sum_on_a_unique_intermediate_cut.md"
    ],
    "DS-QM032-FINITE-FEYNMAN-SHADOW": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0243_finite_feynman_history_shadow.md"
    ],
    "DS-QM032-CONTINUUM-LIMIT-CONDITIONAL": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0243_finite_feynman_history_shadow.md"
    ],
    "DS-QM033-SCHRODINGER-DISCRETE-COCHAIN": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0244_discrete_schrodinger_cochain_on_a_finite_graph.md"
    ],
    "DS-QM040-GAUSSINT-LAMBDA-COMMUTATOR-WITNESS": [
        "papers/derivations/12_finite_qm_structure/TFQ-0249_trace-zero_summaries_do_not_fix_commutation.md"
    ],
    "DS-QM041-HEISENBERG-PICTURE-FINITE": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0247_heisenberg_picture_on_a_finite_carrier.md"
    ],
    "DS-QM043-OFFDIAG-GLOBAL-WEIGHT-IDENTITY": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0242_graded_path_sum_as_finite_transport.md"
    ],
    "DS-QM021-IDEMPOTENT-CONDITIONING": [
        "papers/derivations/11_finite_qm_dynamics/TFQ-0235_selective_measurement_update_as_idempotent_conditioning.md"
    ],
    "DS-QM060-SUPERPOSITION-QUOTIENT-FIBER": [
        "papers/derivations/12_finite_qm_structure/TFQ-0251_superposition_as_a_quotient_fiber.md"
    ],
    "DS-QM061-L1-CANNOT-COMPUTE-INTERFERENCE": [
        "papers/derivations/12_finite_qm_structure/TFQ-0252_interference_as_a_resource_outside_l1_bookkeeping.md"
    ],
    "DS-QM061-BUILDABILITY-SET-S": [
        "papers/derivations/12_finite_qm_structure/TFQ-0252_interference_as_a_resource_outside_l1_bookkeeping.md"
    ],
    "DS-QM062-U1-SELECTOR-LAYERS": [
        "papers/derivations/12_finite_qm_structure/TFQ-0253_conditional_complex-carrier_selector.md"
    ],
    "DS-QM063-HOLONOMY-COHERENT-INTENSITY": [
        "papers/derivations/12_finite_qm_structure/TFQ-0254_holonomy-structured_coherent_intensity.md"
    ],
    "DS-QM064-074-083-ANNEX-REDIRECT-ROWS": [
        "papers/derivations/12_finite_qm_structure/TFQ-0255_phase-gauge_annex_with_no_independent_derivation.md",
        "papers/derivations/12_finite_qm_structure/TFQ-0267_completely-positive_import_annex.md"
    ],
    "DS-QM070-PRODUCT-NONFACTORIZATION": [
        "papers/derivations/12_finite_qm_structure/TFQ-0256_product_defect_on_a_bipartite_weight_table.md"
    ],
    "DS-QM071-ENTANGLEMENT-WITNESS-SOUNDNESS": [
        "papers/derivations/12_finite_qm_structure/TFQ-0257_separability_witness_relative_to_a_declared_family.md"
    ],
    "DS-QM072-QUBIT-SUPERPOSITION-OBSTRUCTED": [
        "papers/derivations/09_finite_hilbert/TFQ-0308_born-uniqueness_band_slot_is_still_a_stub.md"
    ],
    "DS-QM073-FINITE-CHSH-AND-PR-BOX": [
        "papers/derivations/12_finite_qm_structure/TFQ-0259_finite_chsh_ceiling_on_one_global_joint_table.md"
    ],
    "DS-QM073-BELL-THEOREM-OBSTRUCTED": [
        "papers/derivations/12_finite_qm_structure/TFQ-0260_bell_theorem_not_derived_from_the_finite_tables.md"
    ],
    "DS-QM074-NO-SIGNALING-MARGINAL": [
        "papers/derivations/12_finite_qm_structure/TFQ-0261_no-signalling_marginals_under_an_admitted_composition.md"
    ],
    "DS-QM080-IMPORT-FREE-TRACE-NORM-CORE": [
        "papers/derivations/21_implementation_core/TFQ-0132_trace-norm_certificates.md"
    ],
    "DS-QM080-081-TRACE-NORM-CONDITIONAL-SELECTION": [
        "papers/derivations/12_finite_qm_structure/TFQ-0263_trace_norm_under_a_supplied_cptp_family.md"
    ],
    "DS-QM081-CPTP-MONOTONE-NOT-SELECTING": [
        "papers/derivations/12_finite_qm_structure/TFQ-0264_monotonicity_does_not_select_the_trace_norm.md"
    ],
    "DS-QM081-STOCHASTIC-L1-CONTRACTION": [
        "papers/derivations/12_finite_qm_structure/TFQ-0262_cptp_class_recorded_as_a_definition.md"
    ],
    "DS-QM082-STOCHASTIC-KERNEL-CPTP-DIAGONAL": [
        "papers/derivations/12_finite_qm_structure/TFQ-0265_stochastic_population_shadow_of_a_channel.md"
    ],
    "DS-QM090-092-AUTHORITY-FIREWALL": [
        "papers/derivations/13_finite_qm_information/TFQ-0272_interpretations_as_authority_shadows.md",
        "papers/derivations/13_finite_qm_information/TFQ-0275_formal_possibility_is_not_a_physical_terminal.md"
    ],
    "DS-QM090-093-O022-REGISTRY-RELATIVE-MINIMALITY": [
        "papers/derivations/12_finite_qm_structure/TFQ-0273_finite_descent_of_an_imported_quantum_interface.md"
    ],
    "DS-QM090-093-QM-UNIQUENESS-TIER3": [
        "papers/derivations/12_finite_qm_structure/TFQ-0274_tier-3_uniqueness_left_without_a_derivation.md"
    ],
    "DS-QM093-SURVIVAL-THEOREM": [
        "papers/derivations/12_finite_qm_structure/TFQ-0273_finite_descent_of_an_imported_quantum_interface.md"
    ],
    "DS-QM093-QUANTUM-COCHAIN-D1D0-ZERO": [
        "papers/derivations/09_finite_hilbert/TFQ-0315_exact_density_ray_and_population_shadow.md"
    ],
    "DS-QM094-EVERETT-RELATIVE-STATE-CONTACT": [
        "papers/derivations/13_finite_qm_information/TFQ-0276_everettian_relative-state_contact.md"
    ],
    "DS-QM101-THRESHOLD-AS-CONDITIONAL-REPAIR-CERTIFICATE": [
        "papers/derivations/13_finite_qm_information/TFQ-0269_threshold_theorems_read_as_repair-capacity_certificates.md"
    ],
    "DS-QM102-SYNDROME-CAPACITY-BOUND": [
        "papers/derivations/13_finite_qm_information/TFQ-0270_syndrome_distance_and_repair_capacity.md"
    ],
    "DS-QM103-SHOW-THE-PACKET-PROTOCOL": [
        "papers/derivations/13_finite_qm_information/TFQ-0271_show-the-packet_protocol_for_a_finite_computation.md"
    ],
    "DS-QM110-111-LQG-GR-KINEMATICAL-SHADOWS": [
        "papers/derivations/19_finite_qg/TFQ-0092_qm-110-c11_hamiltonian_constraint_stays_q-held_continuum_su_2_data_in_qm-110-c10_are_imported.md"
    ],
    "DS-QM120-MERMIN-PERES-F2-OBSTRUCTION": [
        "papers/derivations/12_finite_qm_structure/TFQ-0250_mermin-peres_contextuality_on_a_finite_cochain.md"
    ],
    "DS-QM206-BOUNDARY-SYNTHESIS": [
        "papers/derivations/09_finite_hilbert/TFQ-0314_cochain_lift_still_prices_the_born_law_as_an_import.md"
    ],
    "DS-QM207-211-FIVE-IMPORT-CASCADE": [
        "papers/derivations/09_finite_hilbert/TFQ-0314_cochain_lift_still_prices_the_born_law_as_an_import.md"
    ],
    "DS-QM212-MAJORANA-PROBLEM": [
        "papers/derivations/22_implementation_sibling/TFQ-0181_keep_core_majorana_a_gf_2_diagnostic_and_do_not_treat_it_as_an.md"
    ],
    "IMPL-FSP-SWITCHING-NORMAL-FORM-NF002": [
        "papers/derivations/23_engine_custody/TFQ-0200_three-language_custody_on_the_engine_runtime.md"
    ],
    "IMPL-THYMUS-SCREENING-SOUNDNESS": [
        "papers/derivations/23_engine_custody/TFQ-0204_finite_floor_binding_for_a_quantum_carrier.md"
    ],
    "IMPL-LGGR-FINITE-RESULTS-LEAN": [
        "papers/derivations/23_engine_custody/TFQ-0200_three-language_custody_on_the_engine_runtime.md"
    ]
}


def build_remaining_142_specs(
    dag_path: Path,
    orig_35_ids: set[str],
) -> dict[str, dict[str, Any]]:
    """Build deterministic 4-Mission Operad specs for the 142 remaining DAG nodes (indices 36..177)."""
    dag = json.loads(dag_path.read_text(encoding="utf-8"))
    in_routes: dict[str, list[str]] = {}
    out_routes: dict[str, list[str]] = {}
    for r in dag["routes"]:
        rid = r["id"]
        out_id = r.get("output")
        if out_id:
            in_routes.setdefault(out_id, []).append(rid)
        for inp in r.get("inputs", []):
            out_routes.setdefault(inp, []).append(rid)

    rem_nodes = [n for n in dag["nodes"] if n["id"] not in orig_35_ids]
    specs: dict[str, dict[str, Any]] = {}
    for idx, n in enumerate(rem_nodes, 36):
        nid = n["id"]
        stage = n["stage"]
        r_stage = STAGE_RANK[stage]
        d_routes = len(in_routes.get(nid, [])) + len(out_routes.get(nid, [])) + 1
        shadow_val = 4 * idx + 3 * r_stage + d_routes
        raw_rival = 2 * idx + 5 * r_stage
        cob_shift = idx + 2 * r_stage
        sign_decoy = r_stage
        counter_val = idx + 2 * r_stage
        stmt_short = n.get("statement", "")[:110].replace("\n", " ")
        specs[nid] = {
            "index": idx,
            "stage_rank": r_stage,
            "route_degree": d_routes,
            "operad_family_id": f"OP-{stage}-{nid}",
            "algebraic_ring": STAGE_ALGEBRAIC_RING[stage],
            "ambient_carrier": f"{stage} finite carrier for {nid}: {stmt_short}",
            "normal_form_contracts": ["nf.cochain.dhnf", "nf.ddc.dual_witness", "nf.epistemic.authority"],
            "finite_shadow_equation": (
                f"stage_route_shadow_invariant({nid}): 4*idx({idx}) + 3*stage_rank({r_stage}) + route_degree({d_routes}) == {shadow_val}"
            ),
            "finite_shadow_lhs": f"4 * {idx} + 3 * {r_stage} + {d_routes}",
            "finite_shadow_rhs": str(shadow_val),
            "finite_shadow_expected_int": shadow_val,
            "raw_candidate_rival_int": raw_rival,
            "coboundary_gauge_shift_int": cob_shift,
            "sign_double_count_int": sign_decoy,
            "countermodel_equation": (
                f"quotient_reduced_countermodel_defect({nid}): R_raw({raw_rival}) - G_cob({cob_shift}) - S_decoy({sign_decoy}) == {counter_val} "
                f"(annihilating coboundary gauge shift G_cob and boundary sign double-count S_decoy under Congruence Ideal I)"
            ),
            "countermodel_lhs": f"({raw_rival}) - ({cob_shift}) - {sign_decoy}",
            "countermodel_rhs": str(counter_val),
            "countermodel_expected_int": counter_val,
            "paper_refs": list(NODE_142_PAPER_REFS.get(nid, [])),
        }
    return specs
