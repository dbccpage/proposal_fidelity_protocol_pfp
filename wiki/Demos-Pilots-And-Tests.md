# Demos, pilots and tests

A map of every executable example in the repository: what each one checks,
where it lives and how to run it. It replaces the old `pfp/tests/demo_004`
folder, which mixed offline checks, model experiments and harness code.

| Kind | Where | Calls a model? | What it is |
| --- | --- | --- | --- |
| Demos | [`demos/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos) | No | Offline examples that run with the standard library and pytest |
| Certified challenges | [`demos/certified_challenges/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges) | No | Fifty hard exact problems judged by certificate checkers |
| Pilots | [`pilots/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pilots) | Yes | Experiments that ran language models; they need the private runtime |
| Unit tests | `pfp/tests`, `pfp_lab/tests`, `governance/tools/tests`, `code/rust/**/tests` | No | Tests of the product code, beside the code they test |

Live model testing stays in the private repository; this one holds the
canonical offline copies. The smaller demos each have a page in the
[Test Catalog](Test-Catalog.md).

Run all demos and challenges from the repository root (about seven minutes,
some 5,100 tests):

    python -m pytest demos -q

## Certified challenges

Each challenge poses an exact problem and judges an answer by checking a
certificate (a witness, a proof, a dual solution, a counterexample) rather than
comparing with a stored answer. Most have two independently written checkers,
40 to 64 judge cases (base cases, relabelled controls and poisoned inputs) and
a set of corrupted answers that the checkers must reject. "Tests" counts the
pytest items for that challenge.

### Graphs, homology and cohomology

| Challenge | What it checks | Tests |
| --- | --- | --- |
| [C011](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c011_cycle_rank_ladder_coboundary_repair) | Minimum-L1 repair of edge claims into a potential difference, certified by an LP dual circulation | 58 |
| [C012](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c012_cellular_sheaf_h0_h1) | Cellular sheaf cohomology H^0 and H^1 with explicit bases | 68 |
| [C013](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c013_integral_homology_torsion) | Integral homology with torsion, certified by Smith normal form | 40 |
| [C014](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c014_discrete_hodge_decomposition) | Exact discrete Hodge decomposition of a cochain | 42 |
| [C015](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c015_persistent_homology_barcodes) | Persistence barcodes with reduction certificates | 12 |
| [C016](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c016_cohomology_ring_cup_products) | Telling spaces apart by cup products | 20 |
| [C017](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c017_nonabelian_lattice_holonomy) | Flatness of a nonabelian lattice connection, or a plaquette with nontrivial holonomy | 26 |
| [C018](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c018_signed_graph_frustration_index) | Frustration index of a signed graph with a switching certificate | 27 |
| [C019](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c019_h2_obstruction_extension) | Degree-2 obstructions to extending a cochain | 23 |
| [C020](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c020_spectral_sequence_double_complex) | Spectral sequence pages of a double complex | 11 |

### Quantum information

| Challenge | What it checks | Tests |
| --- | --- | --- |
| [C021](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c021_q40_r) | Ground energy and degeneracy of a commuting Pauli Hamiltonian | 321 |
| [C022](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c022_stabilizer_code_distance) | Stabilizer code distance with lower-bound certificates | 94 |
| [C023](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c023_clifford_tableau_synthesis) | Clifford circuit synthesis from a tableau | 62 |
| [C024](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c024_local_clifford_graph_state_equivalence) | Local-Clifford equivalence of graph states | 67 |
| [C025](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c025_mub_prime_power_exact) | Exact mutually unbiased bases in prime-power dimensions | 20 |
| [C026](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c026_frustration_free_projector_hamiltonians) | Frustration-free projector Hamiltonians | 19 |
| [C027](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c027_kochen_specker_contextuality) | Kochen-Specker sets and contextuality certificates (see note) | 28 |
| [C028](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c028_jordan_wigner_majorana_mapping) | Fermion-to-qubit mappings with exact anticommutation checks | 21 |
| [C029](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c029_surface_code_min_weight_decoding) | Minimum-weight surface-code decoding | 18 |
| [C030](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c030_tensor_network_contraction_order) | Tensor-network contraction order under a cost bound | 29 |

### Mathematical physics

| Challenge | What it checks | Tests |
| --- | --- | --- |
| [C031](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c031_anomaly_free_u1_charges) | Anomaly-free chiral U(1) charge assignments | 76 |
| [C032](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c032_six_d_sugra_anomaly_cancellation) | Six-dimensional supergravity anomaly cancellation | 190 |
| [C033](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c033_lie_algebra_weight_multiplicities) | Weight multiplicities of simple Lie algebras (Freudenthal and Kostant) | 105 |
| [C034](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c034_calabi_yau_hodge_numbers) | Calabi-Yau Hodge numbers from reflexive polytopes | 89 |
| [C035](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c035_k3_elliptic_genus_mathieu_moonshine) | Mathieu moonshine coefficients from the K3 elliptic genus | 82 |
| [C036](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c036_quintic_gromov_witten_mirror) | Genus-zero invariants of the quintic via mirror symmetry | 85 |
| [C037](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c037_virasoro_minimal_model_fusion) | Fusion rules from the Verlinde formula | 73 |
| [C038](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c038_regge_combinatorial_curvature) | Combinatorial curvature and discrete Gauss-Bonnet | 39 |
| [C039](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c039_lattice_z2_gauge_theory_gauss_law) | Z2 lattice gauge theory: Gauss law and topological degeneracy | 28 |
| [C040](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c040_m_theory_toroidal_cremmer_julia_scalar_count) | Scalar counting for M-theory on tori | 22 |

### Logic, algebra and formal proof

| Challenge | What it checks | Tests |
| --- | --- | --- |
| [C041](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c041_lean4_finite_lemma_proofs) | Lean 4 proofs of hidden finite lemmas, checked by the Lean kernel | 38 |
| [C042](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c042_sat_with_drat_certificates) | SAT answers with models or DRAT/LRAT refutations | 32 |
| [C043](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c043_ramsey_vdw_constructions) | Ramsey and van der Waerden lower-bound constructions | 34 |
| [C044](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c044_finite_group_identification) | Finite group identification with isomorphism witnesses | 5 |
| [C045](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c045_knot_polynomials_from_pd) | Knot polynomials from planar-diagram codes | 126 |
| [C046](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c046_knuth_bendix_completion) | Knuth-Bendix completion with joinability certificates | 149 |
| [C047](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c047_sequence_law_discovery) | Recurrences, or a nonzero minor proving none exists within bounds | 17 |
| [C048](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c048_ternary_quadratic_forms) | A point on `ax^2+by^2+cz^2=0`, or a place with Hilbert symbol -1 | 11 |
| [C049](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c049_finite_category_universal_constructions) | Limits and colimits in finite categories (see note) | 114 |
| [C050](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c050_equational_theorem_proving) | Equational proofs by rewriting, or a finite countermodel | 113 |

### Algorithms and program synthesis

| Challenge | What it checks | Tests |
| --- | --- | --- |
| [C051](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c051_exact_lp_solver_with_duals) | Linear programming with dual, Farkas or ray certificates | 38 |
| [C052](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c052_maxflow_mincut_certificates) | Max flow with a min-cut certificate | 2 |
| [C053](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c053_bareiss_fraction_free_matrix_inversion) | Exact determinant, adjugate and inverse | 37 |
| [C054](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c054_exact_linear_systems) | Linear systems with rank, nullspace and inconsistency witnesses | 47 |
| [C055](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c055_assignment_with_potentials) | Assignment with dual potentials or a Hall violator | 61 |
| [C056](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c056_dfa_minimization_equivalence) | Minimal DFAs with Myhill-Nerode certificates; regex equivalence | 12 |
| [C057](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c057_sorting_network_synthesis) | Sorting networks checked by the zero-one principle | 43 |
| [C058](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c058_straight_line_superoptimization) | Shorter bit-vector programs; exhaustive at 8 bits, sampled above | 21 |
| [C059](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c059_sql_null_total_query_synthesis) | SQL synthesis under three-valued NULL logic | 257 |
| [C060](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/c060_self_verifying_checker_synthesis) | Checker synthesis scored by mutation kill rate | 10 |

## Known limits of the challenges

- **C027.** The independent checker enumerates subsets and refuses refutations
  with more than 20 rays. The 33-ray Peres set and its relabelled copy are
  therefore checked by the exact checker alone, and the dual judge fails closed
  on them.
- **C049.** The independent checker checks shape and status but does not
  re-derive the construction. It accepts 31 of the 48 corrupted answers, so
  only the exact checker is a real check here. The test for it is `xfail`.
- **C041.** Needs `lean` on `PATH`; without it the Lean tests are skipped. Its
  runner reports the last public example as FAIL because the expected answer
  there is a warranted refusal, not a proof.
- **C052.** Has no package tests of its own, only the replay test below.
- **C058.** Acceptance is a proof only at 8 bits; at 16 to 64 bits the
  checkers sample a few thousand inputs.
- **C055.** Its `CHALLENGE.md` is headed C053, the number it was planned under.


## Pilots

Kept in [`pilots/llm_mechanism/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pilots/llm_mechanism) for their tasks,
cases and checkers. Their tests need the private runtime and do not run here.

| Pilot | What it tried |
| --- | --- |
| C001 attention distractor mask | Masking attention to distractor keys, with a McNemar comparison of arms |
| C005 hosted decode controls | A bake-off of hosted decoding controls on checkable cases |
| Consistency teaching | Rank-difference constraint tasks with direct and chain-of-thought prompts |
| Derivation DAG benchmark | One-shot versus staged derivation certificates on the finite-QM derivation graph |
| Finite-QM derivation | Operad mining, prompt compilation and gates for a multi-stage derivation campaign |
| Planned C002 to C004, C006 to C010 | Write-ups of mechanism experiments that were never built |

## What was removed

When the challenges moved out of `pfp/tests/demo_004` on 2026-10-27, these
were deleted because they only run against the private model runtime or
duplicate something kept:

- per-challenge budget gates, adversary gates, commit-reveal runners, matrix
  runners, freeze records and their tests (about 290 files);
- the old combined cohomology and quantum harnesses (runner, judge, solvers and
  "swarm"), which the per-challenge packages replace;
- harness tests that checked the private repository's challenge catalogue;
- the four "dual checker capsules", which were copies of C011, C021, C039 and
  C050 (their tests now run against the full packages).

Everything removed is still in git history and in the private repository.
