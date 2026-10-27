# Test: Certified Run Replay Store

A small SQLite store for challenge runs, and tests that replay stored runs
against the challenge checkers with no network access. A run records the case,
the answer, each checker's verdict, token usage and cost. Replay reloads the
case and answer from the database and runs the checkers again, so a recorded
verdict can always be re-derived from the stored data rather than trusted.

## What it tests and why it matters to PFP

PFP keeps evidence: a result is only as good as your ability to re-check it
later. The tests show three things for each of the six certified challenges
(start at [Exact LP Dual Certificates](Test-Exact-LP-Dual-Certificates.md)):

1. The reference solver's answers pass both checkers (the "exact" and the
   "independent" checker), each run is stored, and replaying every stored run
   from SQLite passes again with the same outcome.
2. A sample of hostile mutations (corrupted answers) is rejected by at least
   one checker.
3. Runs from two different harnesses (labelled `PFP` and `ADVERSARY`) can
   share one database and be replayed concurrently from four threads with
   identical verdicts (not in the SQL challenge's file; see Adaptations).

The store never interprets an answer itself. If a checker raises an exception
during replay, the replay records `CRASH: ...` and fails, rather than passing.

## Setup and inputs

- `demos/certified_challenges/sqlite_pilot_store.py`: `PilotRunRecord` (one
  run) and `SqlitePilotStore` with `record_run`, `get_run`, `list_runs` and
  `replay_run`. Standard library only.
- `test_c051_replay_custody.py` to `test_c059_replay_custody.py`: one file per
  challenge. C051 uses its first 12 judge cases; the others use the small case
  set in each package's `matrix_cases.py`.
- Each test writes its database under pytest's `tmp_path`.

## How to run

From the repository root:

    python -m pytest demos/certified_challenges/test_c051_replay_custody.py demos/certified_challenges/test_c052_replay_custody.py demos/certified_challenges/test_c053_replay_custody.py demos/certified_challenges/test_c054_replay_custody.py demos/certified_challenges/test_c055_replay_custody.py demos/certified_challenges/test_c059_replay_custody.py -q

## Expected output

`11 passed` (two tests for each of C051 to C055, one for C059).

## What a failure means

- `all_passed` false on replay: either the stored answer was altered, or a
  checker changed behaviour since the run was recorded. Both are worth knowing;
  the replay is the evidence.
- A mutation accepted by both checkers: a hole in the checkers (see the
  challenge's own page).
- A mismatch under threaded replay: shared state in a checker or in the store.

## Adaptations

Ported from an internal test suite. The original files had one more test that
sent synthetic model replies through a provider-and-budget boundary that is not
part of this repository; it was removed. For C059 the concurrent two-harness
test depended on that boundary too and was removed. The second harness label
was renamed, and the model name in stored records is now `synthetic-model`.
The `matrix_cases.py` files keep only the case data from the original model
matrix scripts.

## How to modify it

- Point `SqlitePilotStore` at a real file path and keep it to build a replay
  archive of your own solver's runs.
- Pass different `(name, checker)` pairs to `replay_run` to re-judge old runs
  with a new checker.
- Widen the mutation sample (`[:5]`, `[:3]`) to all 48.

## Where it lives

`demos/certified_challenges/sqlite_pilot_store.py` and
`demos/certified_challenges/test_c05*_replay_custody.py`. See also
[Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).
