# Provenance of the PFP Lab core

AuthorityEffect: None.

`graph.py`, `obstruction.py` and `governor.py` port the discrete L1 governor of
the Paper 005 practitioner guide:

| Field | Value |
| --- | --- |
| Source | `papers/005_pfp_practitioners_field_manual/code/l1_symbol_game_governor.py` |
| Source blob (git) | `984718747f35c6dd495d4d1a78bed277bf52bf4b` |
| Source SHA-256 (committed bytes) | `7e2eb54566f3b92a25130ca2cf781c5bc35b62d7b645adabd4ad0c383a35a263` |
| Commit that last touched it | `a9eaa83e3da69662da7b6e6e10e69b223f3284dd` |
| Its own vendoring header | names the earlier repository path, commits and digests it was copied from |

The source file is not modified. `pfp_lab/tests/test_differential.py` loads it
by path as an independent oracle and checks, on random graphs and random move
sequences, that every verdict (step id, admitted, status, defect before and
after) and the resulting section and claims agree exactly.

## What changed in the port

| Area | Paper 005 | PFP Lab | Why |
| --- | --- | --- | --- |
| Value admission | `type(value) not in (int, Fraction)` checks inside each move | One admission layer (`admission.py`, `contracts.py`) admits canonical rational strings and refuses bools and floats before the governor runs | RULE_PY_001, RULE_PY_002, RULE_PY_004 |
| Graph validation | Endpoint checks only | Names, sizes, weights (1 to 1000), self-loops, duplicate vertices and duplicate directed edges all refused at construction | Bounded, typed carrier |
| Phi_1 search | Cartesian product of every component's candidate potentials | Minimum taken per component and summed; same tie-breaking (zero potential first, include-before-exclude tree order, first strict minimum) | The defect is a sum over components, so the result is identical and the cost is a sum, not a product |
| Search bound | None | `SearchBudget` charges every enumeration step and raises `BudgetExceededError` | Gate 5: no unbounded search on reachable input |
| Native calculator | Optional executable chosen by an environment variable | Not ported | The core stays pure Python and dependency-free |
| Unexact-value refusals | `IncompleteProposal` for non-exact section or claim values | Unreachable: the contracts refuse such input first | Same outcome, earlier |
| Function size | 917-line module, long move methods | One handler per move, helpers for checks | Gate 5 ceilings |
| State snapshots | Mutable dict copies in a mutable record | Tuples in frozen records | RULE_PY_005 |
| Detail strings | Original wording | Reworded | Not part of the compared verdict |

## Worked numbers

The `paper-005-worked-session` pack reproduces the guide's Section 4 session:
Phi_1 = 3 after the three ASSERTs, the defect-raising CUT is refused (3 to 5),
the repair is ExactRepair (3 to 0), VERIFY ZERO_OBSTRUCTION passes, and RETRACT
restores Phi_1 = 3. `pfp_lab/tests/test_packs.py` checks these values, which
come from the guide rather than from this code.
