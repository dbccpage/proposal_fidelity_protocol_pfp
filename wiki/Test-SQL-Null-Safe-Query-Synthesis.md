# Test: SQL Null Safe Query Synthesis

A challenge where the answer is a SQL query compiled from a relational-algebra specification, and it must be correct under SQL's three-valued logic for NULL. The answer is judged by running it on hidden test databases in SQLite and comparing the result bag with two independent references: a judge-owned, node-by-node evaluation of the specification in a private SQLite database, and a pure-Python relational interpreter. The tests also check that each judge works without importing the proposer, and that a candidate query cannot write to the fixture databases.

## What it tests and why it matters to PFP

SQL comparisons with NULL return UNKNOWN, which `WHERE` treats as false. That
makes `NOT IN` with a NULL in the subquery return nothing, makes `=` differ
from `IS NOT DISTINCT FROM`, and changes `COUNT(col)` versus `COUNT(*)`.
These are classic places where a confident proposer writes a query that looks
right and silently drops rows. The answer also includes a `preflight_sql`
query that finds NULLs in protected columns, and a `null_ledger` listing the
NULL-sensitive constructs used.

What the tests guard, in PFP terms:

- **Judge independence.** The first judge (SQLite oracle), the second judge
  (pure-Python interpreter) and the shared contracts each run in a fresh
  process with every import of the reference solver blocked. A judge that
  quietly reused the proposer's compiler would accept the proposer's mistakes.
- **No inherited corruption.** If the proposer's compiler is patched to emit a
  wrong query, the first judge still rejects it.
- **Read-only execution.** Candidate SQL runs under an SQLite authoriser that
  allows only reads; `DELETE ... RETURNING`, writes in the preflight query and
  non-query statements are refused and the fixture rows stay unchanged.
- **Exact result bags.** Column headings must match exactly, even for an empty
  result; extra or missing columns are not hidden by NULL padding; row order
  does not matter but multiplicity does.

## Package layout

Every challenge package in `demos/certified_challenges/` has the same shape:

- `participant_packet/TASK.md`: the problem statement and the exact answer
  format a solver must produce.
- `participant_packet/examples/`: 14 public examples, each an input with an
  expected answer, and `runner.py`, which scores a solver on them.
- `reference_solver/`: one correct solver (the "proposer" in PFP terms).
- `judge_packet/exact_checker.py` and `judge_packet/independent_checker.py`:
  two checkers written separately. A reply counts only if both accept it.
- `judge_packet/cases/`: 64 judge cases, including malformed inputs that must
  be refused with `OUT_OF_SCOPE`.
- `judge_packet/hostile_mutations/`: 48 corrupted answers, each paired with its
  case. Every one must be rejected.
- `generate_*.py`: the scripts that built those fixture files.

## Inputs

64 judge cases (each operator and predicate, joins, anti- and semi-joins,
grouping with NULL groups, aggregates over NULL, unions, renames, nested
pipelines, relabelings and poisoned specs) and 48 mutations (for example `<>`
in place of `IS DISTINCT FROM`, `NOT IN` in place of a NULL-safe anti-join, a
dropped `WHERE`, `COUNT(col)` for `COUNT(*)`, a preflight that checks the
wrong table, syntax errors and false refusals). Test databases are built by
`generate_cases.create_sample_dbs()`.

## How to run

From the repository root (Python 3.12 standard library plus pytest):

    python -m pytest demos/certified_challenges/c059_sql_null_total_query_synthesis -q
    python -m pytest demos/certified_challenges/test_c059_replay_custody.py -q
    python demos/certified_challenges/c059_sql_null_total_query_synthesis/participant_packet/runner.py

The fixture generators are modules in the package; run them from inside
`demos/certified_challenges` as
`python -m c059_sql_null_total_query_synthesis.generate_cases`.

## Expected output

`256 passed`, then `1 passed`, then fourteen `[PASS]` lines and `Result: 14/14 examples passed (100.0%)`.

## What a failure means

- A reference answer rejected by a checker: the solver and that checker
  disagree about the answer format or the mathematics. One of them is wrong;
  the failing message names the field.
- A hostile mutation accepted: the checker has a hole. Some wrong answer would
  be counted as correct, which is exactly what PFP is meant to prevent.
- A refuse-everything or empty responder scoring points: the scoring rewards
  saying nothing. The original suite found and fixed this bug (an answer of
  `OUT_OF_SCOPE` is accepted only for a malformed case).

## Adaptations

Besides the import paths, the five tests that start a fresh Python process now
pass `cwd=` set to `demos/certified_challenges`, so the child process can
import the package by name. A code comment that named SQLite's temporary
schema table now uses its alias `sqlite_temp_schema`.

## How to modify it

- Add a `(spec, sql)` pair to `tests/test_null_boundaries.py` to compare the
  interpreter with SQLite on a new NULL corner case.
- Add a mutation by copying a file in `judge_packet/hostile_mutations/` and
  changing the `candidate` SQL; `tests/test_sql_read_boundary.py` checks every
  retained mutation against each judge.
- Needs an SQLite build with `IS DISTINCT FROM` (SQLite 3.39 or later, as
  bundled with current Python 3.12 releases).

## Where it lives

`demos/certified_challenges/c059_sql_null_total_query_synthesis`. Ported from an internal test suite. Imports were changed from the
original package path to the package's own name, and the `conftest.py` in
`demos/certified_challenges/` puts that folder on `sys.path`. The checkers,
cases and assertions are unchanged.

See also [Certified Run Replay Store](Test-Certified-Run-Replay-Store.md),
[Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).
