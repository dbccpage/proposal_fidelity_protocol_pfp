# Certified challenges: exact solvers with checkable certificates

Eleven self-contained challenge packages. Each one has a reference solver, two
independently written checkers (an "exact" checker and an "independent"
checker), 64 judge cases, 48 hostile mutations (deliberately corrupted answers)
and 12 or 14 public examples. A solver must return a certificate that the checkers can
verify without trusting the solver.

| Folder | Problem | Wiki page |
| --- | --- | --- |
| `c047_sequence_law_discovery` | Polynomial recurrences, or a nonzero minor proving none exists within bounds | Test-Recurrence-Absence-Certificates |
| `c048_ternary_quadratic_forms` | A point on `ax^2+by^2+cz^2=0`, or a place with Hilbert symbol -1 | Test-Quadratic-Form-Local-Obstructions |
| `c051_exact_lp_solver_with_duals` | Linear programming with dual / Farkas / ray certificates | Test-Exact-LP-Dual-Certificates |
| `c052_maxflow_mincut_certificates` | Max flow with a min-cut certificate | Test-Max-Flow-Min-Cut-Certificates |
| `c053_bareiss_fraction_free_matrix_inversion` | Exact determinant, adjugate and inverse | Test-Exact-Matrix-Inversion-Certificates |
| `c054_exact_linear_systems` | Linear systems with rank, nullspace and inconsistency witnesses | Test-Exact-Linear-System-Witnesses |
| `c055_assignment_with_potentials` | Assignment with dual potentials or a Hall violator | Test-Assignment-Dual-Potentials |
| `c056_dfa_minimization_equivalence` | Minimal DFAs with Myhill-Nerode certificates; regex equivalence | Test-DFA-Minimality-Certificates |
| `c057_sorting_network_synthesis` | Sorting networks checked by the zero-one principle | Test-Sorting-Network-Zero-One-Principle |
| `c058_straight_line_superoptimization` | Shorter bit-vector programs; exhaustive at 8 bits, sampled above | Test-Superoptimizer-Equivalence-Limits |
| `c059_sql_null_total_query_synthesis` | SQL synthesis under three-valued NULL logic | Test-SQL-Null-Safe-Query-Synthesis |

`sqlite_pilot_store.py` and the `test_c05*_replay_custody.py` files store runs
in SQLite and replay them against both checkers (wiki page
Test-Certified-Run-Replay-Store).

Run everything from the repository root (standard library plus pytest):

    python -m pytest demos/certified_challenges -q

Expected: `546 passed` (under a minute; C057 builds networks up to 12 channels).

The packages C047, C048 and C056 to C058 moved here from `pfp/tests/demo_004` on
2026-10-27. Each keeps its challenge statement as `CHALLENGE.md`; its links point
into the source repository's challenge tree and do not resolve here. The scripts
that ran language models on these challenges need the unpublished runtime and
were left behind.

`findings/` holds the working notes from those model runs (C043 to C059). Read
their dated notices first: the model scores are exploratory, every
`PASS_TO_MASTER` label is a reference self-score, and where a note and a paper
in `papers/` disagree, the paper is authoritative.

`conftest.py` puts this folder on `sys.path`, so the packages import by their
own names (for example `c054_exact_linear_systems.judge_packet.exact_checker`).
The `generate_*.py` scripts rebuild the case, mutation and example files; on
Windows they write CRLF line endings, so normalise to LF before comparing.
