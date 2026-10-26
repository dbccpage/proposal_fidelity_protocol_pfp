# Challenge census for Paper 008

This file lists the evidence behind the categories in Section 9 of the
[manuscript](../paper.md). It records what each challenge folder contains; it
is not a claim that any package's tests pass.

## Census commit and scope

The census reads the tree of commit `a623568eb0f853b968bc419bf06dfc6af256ab02`
(2026-09-28). The challenge folder `omega_engine_projects/mssn_sn_symgam/challenges/`
is inspected at that historical revision; its layout is not asserted for
current main. Folder paths below are relative to that challenge folder.
The [machine-readable inventory](historical_census_inventory.json) records
the forty solver/checker packages and the two measurement specifications and
eight remaining specifications from the five untruncated category trees.

The paper covers C001 to C050. C051 lies outside that range and is listed
because it is the one other delivered package at the census commit. The
folder also holds specifications C052 to C100 and G01 to G25, which the paper
does not audit.

At the code baseline `52cb5457f6c485ba548cfd292f6012a941ed22cf` (2026-09-27)
the delivered packages were C001, C005, C011 to C021, and C031 to C040.
C022 to C030 and C041 to C051 were added after that commit.

## Category rules

The three categories are disjoint.

- **A. Delivered solver with two checkers.** The folder has a
  `reference_solver/` directory, two checker modules under `judge_packet/`,
  and executable checks. C011 to C046 have pytest test files. C047 has a
  test-named score-printing script, `judge_packet/test_cases_runner.py`, with
  no assertions or failing exit status; it checks cases rather than mutation
  files. C048 to C051 have no pytest test file. No common all-hidden-case and
  mutation execution is inferred from the presence of their scoring programs.
- **B. Model measurement.** The deliverable is a measurement of a language
  model rather than a reference solver: C001 and C005. This is a deliverable
  category, not an assertion of a completed measurement.
- **C. Specification only.** A specification file exists and no reference
  solver is delivered: C002, C003, C004, C006, C007, C008, C009, and C010.

Whether the two checkers are independent in the sense of the challenge
protocol (written separately) is as declared by each package; this census did
not audit it.

## Category A

The Test files column counts test-named Python files, not collected pytest
functions: C047's value of one refers to its print-only script. The
machine-readable inventory records file-level identities, not list lengths.
Hidden cases below are JSON files under
`judge_packet/cases/` or `judge_packet/hidden_cases/` (or list entries when a
single file holds them), and mutations are JSON files under
`judge_packet/mutation_suite/` or `judge_packet/hostile_mutations/` (or list
entries). The scoring record is the retained receipt as written by the package.
"Pass recorded" means that the receipt's verdict field reads PASS or
PASS_TO_MASTER; the case tally and date are copied from the receipt, and
"undated" means the receipt carries no timestamp. "None retained" means that
no scoring receipt is in the folder. The September 28 author record reports only the five test-file runs listed
in Section 9.2 of the manuscript; the present review did not rerun the
historical challenge packages.

| ID | Folder | Checker modules | Test files | Hidden cases | Mutations | Scoring record |
| --- | --- | --- | --- | --- | --- | --- |
| C011 | `b_cohomology/c011_cycle_rank_ladder_coboundary_repair` | `circulation_checker.py` + `potential_checker.py` | 6 | 46 | 40 | `commitments/c011_scoring_receipt.json` (pass recorded, 46/46 cases, 2026-09-27) |
| C012 | `b_cohomology/c012_cellular_sheaf_h0_h1` | `sheaf_algebraic_checker.py` + `sheaf_echelon_checker.py` | 6 | 68 | 40 | `commitments/c012_scoring_receipt.json` (pass recorded, 68/68 cases, 2026-09-28) |
| C013 | `b_cohomology/c013_integral_homology_torsion` | `snf_algebraic_checker.py` + `snf_elimination_checker.py` | 6 | 68 | 40 | `commitments/c013_scoring_receipt.json` (pass recorded, 68/68 cases, 2026-09-27) |
| C014 | `b_cohomology/c014_discrete_hodge_decomposition` | `hodge_algebraic_checker.py` + `hodge_elimination_checker.py` | 7 | 68 | 40 | `commitments/c014_scoring_receipt.json` (scoring invalidated, rescore pending, 2026-09-27) |
| C015 | `b_cohomology/c015_persistent_homology_barcodes` | `f2_algebraic_checker.py` + `independent_checker.py` | 6 | 54 | 40 | none retained |
| C016 | `b_cohomology/c016_cohomology_ring_cup_products` | `algebraic_cup_checker.py` + `independent_checker.py` | 6 | 44 | 40 | none retained |
| C017 | `b_cohomology/c017_nonabelian_lattice_holonomy` | `algebraic_holonomy_checker.py` + `independent_checker.py` | 7 | 66 | 40 | none retained |
| C018 | `b_cohomology/c018_signed_graph_frustration_index` | `frustration_checker.py` + `independent_checker.py` | 6 | 68 | 40 | none retained |
| C019 | `b_cohomology/c019_h2_obstruction_extension` | `h2_obstruction_checker.py` + `independent_checker.py` | 6 | 68 | 40 | none retained |
| C020 | `b_cohomology/c020_spectral_sequence_double_complex` | `exact_checker.py` + `independent_checker.py` | 6 | 54 | 40 | none retained |
| C021 | `c_quantum/c021_q40_r` | `algebraic_checker.py` + `spectral_checker.py` | 13 | 46 | 40 | `commitments/c021_q40_r_scoring_receipt.json` (pass recorded, 46/46 cases, 2026-09-27) |
| C022 | `c_quantum/c022_stabilizer_code_distance` | `exact_checker.py` + `independent_checker.py` | 6 | 46 | 40 | `commitments/c022_stabilizer_code_distance_scoring_receipt.json` (pass recorded, 46/46 cases, undated) |
| C023 | `c_quantum/c023_clifford_tableau_synthesis` | `exact_checker.py` + `independent_checker.py` | 7 | 46 | 40 | `commitments/c023_clifford_tableau_synthesis_scoring_receipt.json` (pass recorded, 46/46 cases, undated) |
| C024 | `c_quantum/c024_local_clifford_graph_state_equivalence` | `exact_checker.py` + `independent_checker.py` | 8 | 46 | 40 | `commitments/c024_local_clifford_graph_state_equivalence_scoring_receipt.json` (pass recorded, 46/46 cases, undated) |
| C025 | `c_quantum/c025_mub_prime_power_exact` | `exact_checker.py` + `independent_checker.py` | 7 | 28 | 45 | `commitments/c025_mub_scoring_receipt.json` (pass recorded, 28/28 cases, undated) |
| C026 | `c_quantum/c026_frustration_free_projector_hamiltonians` | `exact_checker.py` + `independent_checker.py` | 6 | 38 | 47 | `commitments/c026_ff_scoring_receipt.json` (pass recorded, 38/38 cases, undated) |
| C027 | `c_quantum/c027_kochen_specker_contextuality` | `exact_checker.py` + `independent_checker.py` | 6 | 38 | 45 | `commitments/c027_ks_scoring_receipt.json` (pass recorded, 38/38 cases, undated) |
| C028 | `c_quantum/c028_jordan_wigner_majorana_mapping` | `exact_checker.py` + `independent_checker.py` | 6 | 38 | 48 | `commitments/c028_jw_scoring_receipt.json` (pass recorded, 38/38 cases, undated) |
| C029 | `c_quantum/c029_surface_code_min_weight_decoding` | `exact_checker.py` + `independent_checker.py` | 6 | 52 | 45 | `commitments/c029_sc_scoring_receipt.json` (pass recorded, 52/52 cases, undated) |
| C030 | `c_quantum/c030_tensor_network_contraction_order` | `exact_checker.py` + `independent_checker.py` | 6 | 46 | 48 | `commitments/c030_tn_scoring_receipt.json` (pass recorded, 46/46 cases, undated) |
| C031 | `d_physics_mtheory/c031_anomaly_free_u1_charges` | `u1_algebraic_checker.py` + `u1_mitm_checker.py` | 6 | 46 | 45 | `commitments/c031_scoring_receipt.json` (pass recorded, 46/46 cases, 2026-09-27) |
| C032 | `d_physics_mtheory/c032_six_d_sugra_anomaly_cancellation` | `sugra_matrix_checker.py` + `sugra_weight_checker.py` | 6 | 42 | 46 | `commitments/c032_scoring_receipt.json` (pass recorded, 42/42 cases, 2026-09-27) |
| C033 | `d_physics_mtheory/c033_lie_algebra_weight_multiplicities` | `freudenthal_checker.py` + `kostant_checker.py` | 6 | 46 | 48 | `commitments/c033_scoring_receipt.json` (pass recorded, 46/46 cases, 2026-09-27) |
| C034 | `d_physics_mtheory/c034_calabi_yau_hodge_numbers` | `affine_hnf_checker.py` + `facet_point_checker.py` | 6 | 46 | 52 | `commitments/c034_scoring_receipt.json` (pass recorded, 46/46 cases, 2026-09-27) |
| C035 | `d_physics_mtheory/c035_k3_elliptic_genus_mathieu_moonshine` | `jacobi_character_checker.py` + `matrix_inversion_checker.py` | 6 | 38 | 48 | `commitments/c035_scoring_receipt.json` (pass recorded, 38/38 cases, 2026-09-27) |
| C036 | `d_physics_mtheory/c036_quintic_gromov_witten_mirror` | `hypergeometric_mirror_checker.py` + `picard_fuchs_recurrence_checker.py` | 6 | 28 | 48 | `commitments/c036_scoring_receipt.json` (pass recorded, 28/28 cases, 2026-09-27) |
| C037 | `d_physics_mtheory/c037_virasoro_minimal_model_fusion` | `combinatorial_fusion_checker.py` + `verlinde_cyclotomic_checker.py` | 6 | 34 | 48 | `commitments/c037_scoring_receipt.json` (pass recorded, 34/34 cases, 2026-09-27) |
| C038 | `d_physics_mtheory/c038_regge_combinatorial_curvature` | `combinatorial_primal_checker.py` + `homology_dual_potential_checker.py` | 6 | 46 | 48 | `commitments/c038_scoring_receipt.json` (pass recorded, 46/46 cases, 2026-09-27) |
| C039 | `d_physics_mtheory/c039_lattice_z2_gauge_theory_gauss_law` | `homology_cohomology_checker.py` + `stabilizer_tableau_checker.py` | 6 | 48 | 48 | `commitments/c039_scoring_receipt.json` (pass recorded, 48/48 cases, 2026-09-27) |
| C040 | `d_physics_mtheory/c040_m_theory_toroidal_cremmer_julia_scalar_count` | `coset_group_theory_checker.py` + `field_reduction_checker.py` | 6 | 46 | 48 | `commitments/c040_scoring_receipt.json` (pass recorded, 46/46 cases, 2026-09-27) |
| C041 | `e_formal_math/c041_lean4_finite_lemma_proofs` | `exact_checker.py` + `independent_checker.py` | 5 | 64 | 48 | `commitments/c041_l41_scoring_receipt.json` (pass recorded, 64/64 cases, 2026-09-28) |
| C042 | `e_formal_math/c042_sat_with_drat_certificates` | `drat_checker.py` + `sat_checker.py` | 5 | 64 | 48 | `commit_reveal/c042_l41_scoring_receipt.json` (pass recorded, 64/64 cases, 2026-09-28) |
| C043 | `e_formal_math/c043_ramsey_vdw_constructions` | `independent_checker.py` + `ramsey_vdw_checker.py` | 1 | 64 | 48 | `commit_reveal/c043_l41_scoring_receipt.json` (pass recorded, 64/64 cases, 2026-09-28) |
| C044 | `e_formal_math/c044_finite_group_identification` | `exact_checker.py` + `independent_checker.py` | 1 | 64 | 48 | `commit_reveal/c044_l41_scoring_receipt.json` (pass recorded, 64/64 cases, 2026-09-28) |
| C045 | `e_formal_math/c045_knot_polynomials_from_pd` | `exact_checker.py` + `independent_checker.py` | 1 | 64 | 48 | none retained |
| C046 | `e_formal_math/c046_knuth_bendix_completion` | `exact_checker.py` + `independent_checker.py` | 1 | 64 | 48 | none retained |
| C047 | `e_formal_math/c047_sequence_law_discovery` | `exact_checker.py` + `independent_checker.py` | 1 | 64 | 48 | none retained |
| C048 | `e_formal_math/c048_ternary_quadratic_forms` | `exact_checker.py` + `independent_checker.py` | 0 | 64 | 48 | none retained |
| C049 | `e_formal_math/c049_finite_category_universal_constructions` | `exact_checker.py` + `independent_checker.py` | 0 | 64 | 48 | none retained |
| C050 | `e_formal_math/c050_equational_theorem_proving` | `exact_checker.py` + `independent_checker.py` | 0 | 64 | 48 | none retained |
| C051 | `f_program_synthesis/c051_exact_lp_solver_with_duals` | `exact_checker.py` + `independent_checker.py` | 0 | 64 | 48 | none retained |

The C014 receipt records that its earlier scoring was invalidated and a rescore
is pending. No scoring receipt is retained for C015 to C020 or C045 to C051.

## Category B

| ID | Folder | Contents | Test files | Retained result |
| --- | --- | --- | --- | --- |
| C001 | `a_mechanism/c001_attention_distractor_mask` | A real-weights harness for Qwen2.5-0.5B-Instruct (`empirical_neural_mcnemar_evaluation.py`) and a 200-case McNemar module that labels itself a synthetic fixture with injected baseline failures (`mcnemar_arms_evaluation.py`) | 12 | None. The harness writes its report only to an untracked run folder, and it lists the full 200-case sweep as a next test. |
| C005 | `a_mechanism/c005_hosted_decode_controls` | Host checker `checkers.py`, case generator `cases.py`, and the two benchmark scripts `benchmark_3arm_scratchpad.py` and `benchmark_arm4_hybrid.py` | 1 | Aggregate counts in `omega_engine_atlas/coda_atlas/omega_engine_pfp/c005_structured_decoding_controls_empirical_results.md`. The per-case rows were written to an untracked run folder and are not in the repository. |

## Category C

Each of these challenges has only its specification file under `a_mechanism/`:
`c002_attention_steering_sweep_correctness.md`,
`c003_head_attribution_activation_patching.md`,
`c004_grammar_masked_decode_ladder.md`, `c006_host_scratch_space_vs_cot.md`,
`c007_context_compaction_kv_surgery.md`,
`c008_activation_steering_sign_discipline.md`,
`c009_model_size_ladder_advantage_curve.md`, and
`c010_repeated_sampling_frontier.md`.
