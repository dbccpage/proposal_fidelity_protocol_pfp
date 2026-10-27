# Certified challenges: exact solvers with checkable certificates

Fifty self-contained challenge packages, C011 to C060. Each one poses a hard
exact problem, ships a reference solver, and judges any answer with checkers
that verify a certificate (a witness, a proof, a dual solution, a
counterexample) instead of comparing to a stored answer. Most packages have two
independently written checkers, about 40 to 64 judge cases (base cases,
relabelled "gauge" controls and poisoned or malformed inputs) and a set of
deliberately corrupted answers that the checkers must reject.

Everything here runs offline with the standard library and pytest. Nothing
calls a language model. The experiments that ran models against these
challenges are in [`pilots/`](../../pilots/README.md) and the private runtime.

Run everything from the repository root:

    python -m pytest demos/certified_challenges -q

Expected: about 5,100 passed, 3 skipped and 1 xfailed, in about seven minutes.
One challenge at a time:

    python -m pytest demos/certified_challenges/c045_knot_polynomials_from_pd -q

Each package's `participant_packet/runner.py` runs the reference solver on the
public examples, and `CHALLENGE.md` (or `README.md` for C051 to C054 and C059)
states the problem and what counts as a valid answer.

## Index

"Tests" is the number of pytest items in the package plus its root-level test
file, if any.

### Graphs, homology and cohomology

| Folder | What it checks | Tests |
| --- | --- | --- |
| `c011_cycle_rank_ladder_coboundary_repair` | Minimum-L1 repair of edge claims into a potential difference, certified by an LP dual circulation | 58 |
| `c012_cellular_sheaf_h0_h1` | Cellular sheaf cohomology H^0 and H^1 with explicit bases | 68 |
| `c013_integral_homology_torsion` | Integral homology with torsion, certified by Smith normal form | 40 |
| `c014_discrete_hodge_decomposition` | Exact discrete Hodge decomposition of a cochain | 42 |
| `c015_persistent_homology_barcodes` | Persistence barcodes with reduction certificates | 12 |
| `c016_cohomology_ring_cup_products` | Telling spaces apart by cup products | 20 |
| `c017_nonabelian_lattice_holonomy` | Flatness of a nonabelian lattice connection, or a plaquette with nontrivial holonomy | 26 |
| `c018_signed_graph_frustration_index` | Frustration index of a signed graph with a switching certificate | 27 |
| `c019_h2_obstruction_extension` | Degree-2 obstructions to extending a cochain | 23 |
| `c020_spectral_sequence_double_complex` | Spectral sequence pages of a double complex | 11 |

### Quantum information

| Folder | What it checks | Tests |
| --- | --- | --- |
| `c021_q40_r` | Ground energy and degeneracy of a commuting Pauli Hamiltonian | 321 |
| `c022_stabilizer_code_distance` | Stabilizer code distance with lower-bound certificates | 94 |
| `c023_clifford_tableau_synthesis` | Clifford circuit synthesis from a tableau | 62 |
| `c024_local_clifford_graph_state_equivalence` | Local-Clifford equivalence of graph states | 67 |
| `c025_mub_prime_power_exact` | Exact mutually unbiased bases in prime-power dimensions | 20 |
| `c026_frustration_free_projector_hamiltonians` | Frustration-free projector Hamiltonians | 19 |
| `c027_kochen_specker_contextuality` | Kochen-Specker sets and contextuality certificates (see note) | 28 |
| `c028_jordan_wigner_majorana_mapping` | Fermion-to-qubit mappings with exact anticommutation checks | 21 |
| `c029_surface_code_min_weight_decoding` | Minimum-weight surface-code decoding | 18 |
| `c030_tensor_network_contraction_order` | Tensor-network contraction order under a cost bound | 29 |

### Mathematical physics

| Folder | What it checks | Tests |
| --- | --- | --- |
| `c031_anomaly_free_u1_charges` | Anomaly-free chiral U(1) charge assignments | 76 |
| `c032_six_d_sugra_anomaly_cancellation` | Six-dimensional supergravity anomaly cancellation | 190 |
| `c033_lie_algebra_weight_multiplicities` | Weight multiplicities of simple Lie algebras (Freudenthal and Kostant) | 105 |
| `c034_calabi_yau_hodge_numbers` | Calabi-Yau Hodge numbers from reflexive polytopes | 89 |
| `c035_k3_elliptic_genus_mathieu_moonshine` | Mathieu moonshine coefficients from the K3 elliptic genus | 82 |
| `c036_quintic_gromov_witten_mirror` | Genus-zero invariants of the quintic via mirror symmetry | 85 |
| `c037_virasoro_minimal_model_fusion` | Fusion rules from the Verlinde formula | 73 |
| `c038_regge_combinatorial_curvature` | Combinatorial curvature and discrete Gauss-Bonnet | 39 |
| `c039_lattice_z2_gauge_theory_gauss_law` | Z2 lattice gauge theory: Gauss law and topological degeneracy | 28 |
| `c040_m_theory_toroidal_cremmer_julia_scalar_count` | Scalar counting for M-theory on tori | 22 |

### Logic, algebra and formal proof

| Folder | What it checks | Tests |
| --- | --- | --- |
| `c041_lean4_finite_lemma_proofs` | Lean 4 proofs of hidden finite lemmas, checked by the Lean kernel | 38 |
| `c042_sat_with_drat_certificates` | SAT answers with models or DRAT/LRAT refutations | 32 |
| `c043_ramsey_vdw_constructions` | Ramsey and van der Waerden lower-bound constructions | 34 |
| `c044_finite_group_identification` | Finite group identification with isomorphism witnesses | 5 |
| `c045_knot_polynomials_from_pd` | Knot polynomials from planar-diagram codes | 126 |
| `c046_knuth_bendix_completion` | Knuth-Bendix completion with joinability certificates | 149 |
| `c047_sequence_law_discovery` | Recurrences, or a nonzero minor proving none exists within bounds | 17 |
| `c048_ternary_quadratic_forms` | A point on `ax^2+by^2+cz^2=0`, or a place with Hilbert symbol -1 | 11 |
| `c049_finite_category_universal_constructions` | Limits and colimits in finite categories (see note) | 114 |
| `c050_equational_theorem_proving` | Equational proofs by rewriting, or a finite countermodel | 113 |

### Algorithms and program synthesis

| Folder | What it checks | Tests |
| --- | --- | --- |
| `c051_exact_lp_solver_with_duals` | Linear programming with dual, Farkas or ray certificates | 38 |
| `c052_maxflow_mincut_certificates` | Max flow with a min-cut certificate | 2 |
| `c053_bareiss_fraction_free_matrix_inversion` | Exact determinant, adjugate and inverse | 37 |
| `c054_exact_linear_systems` | Linear systems with rank, nullspace and inconsistency witnesses | 47 |
| `c055_assignment_with_potentials` | Assignment with dual potentials or a Hall violator | 61 |
| `c056_dfa_minimization_equivalence` | Minimal DFAs with Myhill-Nerode certificates; regex equivalence | 12 |
| `c057_sorting_network_synthesis` | Sorting networks checked by the zero-one principle | 43 |
| `c058_straight_line_superoptimization` | Shorter bit-vector programs; exhaustive at 8 bits, sampled above | 21 |
| `c059_sql_null_total_query_synthesis` | SQL synthesis under three-valued NULL logic | 257 |
| `c060_self_verifying_checker_synthesis` | Checker synthesis scored by mutation kill rate | 10 |

## Known limits

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

## Other files

`test_c0*_reference_cases.py` and `test_c0*_reference_and_mutations.py` run
the reference answer and every corrupted answer through both checkers for
C011, C021, C039, C049 and C050. `test_malformed_cohomology_certificates.py`
feeds malformed certificates to the C013 and C016 checkers.

`sqlite_pilot_store.py` and the `test_c05*_replay_custody.py` files store runs
in SQLite and replay them against both checkers (wiki page
Test-Certified-Run-Replay-Store).

`findings/` holds the working notes from the model runs (C043 to C060). Read
their dated notices first: the model scores are exploratory, every
`PASS_TO_MASTER` label is a reference self-score, and where a note and a paper
in `papers/` disagree, the paper is authoritative.

`conftest.py` puts this folder on `sys.path`, so the packages import by their
own names (for example `c054_exact_linear_systems.judge_packet.exact_checker`).
Test files that would otherwise share a name carry their challenge number
(`test_c033_dual_checkers.py`). The `generate_*.py` scripts rebuild case,
mutation and example files; on Windows they write CRLF line endings, so
normalise to LF before comparing. `demos/` is pinned to LF in `.gitattributes`
because the manifests pin file bytes by SHA-256.

## History

C047, C048 and C056 to C058 moved here from `pfp/tests/demo_004` on
2026-10-27 (PR #29); the other packages from C011 to C050 and C060 followed the
same day. When they moved, the parts that only run against the private model
runtime were removed: per-package budget gates, adversary gates, commit-reveal
runners, matrix runners, freeze records and the tests of those. The old combined
cohomology and quantum harnesses were dropped because the packages replace
them, and the four "dual checker capsules" were merged into the full packages
they duplicated. All of it remains in git history and in the source repository.
