# Certified challenges: exact solvers with checkable certificates

Six self-contained challenge packages. Each one has a reference solver, two
independently written checkers (an "exact" checker and an "independent"
checker), 64 judge cases, 48 hostile mutations (deliberately corrupted answers)
and 14 public examples. A solver must return a certificate that the checkers can
verify without trusting the solver.

| Folder | Problem | Wiki page |
| --- | --- | --- |
| `c051_exact_lp_solver_with_duals` | Linear programming with dual / Farkas / ray certificates | Test-Exact-LP-Dual-Certificates |
| `c052_maxflow_mincut_certificates` | Max flow with a min-cut certificate | Test-Max-Flow-Min-Cut-Certificates |
| `c053_bareiss_fraction_free_matrix_inversion` | Exact determinant, adjugate and inverse | Test-Exact-Matrix-Inversion-Certificates |
| `c054_exact_linear_systems` | Linear systems with rank, nullspace and inconsistency witnesses | Test-Exact-Linear-System-Witnesses |
| `c055_assignment_with_potentials` | Assignment with dual potentials or a Hall violator | Test-Assignment-Dual-Potentials |
| `c059_sql_null_total_query_synthesis` | SQL synthesis under three-valued NULL logic | Test-SQL-Null-Safe-Query-Synthesis |

`sqlite_pilot_store.py` and the `test_c05*_replay_custody.py` files store runs
in SQLite and replay them against both checkers (wiki page
Test-Certified-Run-Replay-Store).

Run everything from the repository root (standard library plus pytest):

    python -m pytest demos/certified_challenges -q

Expected: `442 passed`.

`conftest.py` puts this folder on `sys.path`, so the packages import by their
own names (for example `c054_exact_linear_systems.judge_packet.exact_checker`).
The `generate_*.py` scripts rebuild the case, mutation and example files; on
Windows they write CRLF line endings, so normalise to LF before comparing.
