# Test: Assignment Dual Potentials

An assignment-problem challenge (the reference solver is the Hungarian algorithm). An optimal answer must include dual potentials that prove optimality; an infeasible one must include a Hall violator, a set of rows that together reach too few columns. The tests check typed permutations, the optimisation sense and canonical numbers, and that every corrupted answer is rejected.

## What it tests and why it matters to PFP

Given an `n x n` cost matrix (with `null` for forbidden pairs) and a sense
(`min` or `max`):

- **OPTIMAL**: a permutation `sigma` using allowed entries, and integer
  potentials `u`, `v` with `u_i + v_j <= c_ij` for every allowed pair and
  `sum(u) + sum(v)` equal to the cost of `sigma`. By linear-programming
  duality this proves no cheaper assignment exists. For `max` the inequality
  is reversed.
- **NO_PERFECT_ASSIGNMENT**: a set `S` of rows whose allowed columns number
  fewer than `|S|`. By Hall's theorem no perfect assignment exists.

The tests close specific holes found by audit: a Boolean permutation
(`True` is 1 in Python) was accepted, a non-integer permutation crashed the
checker, and an unknown `sense` value was not refused.

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

64 judge cases: 1x1 up to 15x15, Hall violators, all-null rows and columns,
negative costs, ties, maximisation, sparse matrices, 10^9 and 10^18 values,
low-rank costs and row, column and transposition relabelings. 48 mutations:
raised potentials, sum mismatches, forbidden entries in `sigma`, duplicate or
out-of-range columns, swapped verdicts, fake Hall sets, max-sense dual
violations, floats, Booleans, raw integers, missing fields and a suboptimal
permutation.

## How to run

From the repository root (Python 3.12 standard library plus pytest):

    python -m pytest demos/certified_challenges/c055_assignment_with_potentials -q
    python -m pytest demos/certified_challenges/test_c055_replay_custody.py -q
    python demos/certified_challenges/c055_assignment_with_potentials/participant_packet/runner.py

## Expected output

`59 passed`, then `2 passed`, then `Result: 14/14 passed.` and `ALL EXAMPLES PASSED SUCCESSFULLY.`

## What a failure means

- A reference answer rejected by a checker: the solver and that checker
  disagree about the answer format or the mathematics. One of them is wrong;
  the failing message names the field.
- A hostile mutation accepted: the checker has a hole. Some wrong answer would
  be counted as correct, which is exactly what PFP is meant to prevent.
- A refuse-everything or empty responder scoring points: the scoring rewards
  saying nothing. The original suite found and fixed this bug (an answer of
  `OUT_OF_SCOPE` is accepted only for a malformed case).

## How to modify it

- Add more bad `sense` values or permutation shapes to the parametrised tests.
- A new case only needs `case_id`, `cost` and optionally `sense`; run the
  reference solver on it and both checkers on the result.
- `judge_packet/generate_mutations.py` regenerates the mutations and reports
  whether both checkers kill all 48.

## Where it lives

`demos/certified_challenges/c055_assignment_with_potentials`. Ported from an internal test suite. Imports were changed from the
original package path to the package's own name, and the `conftest.py` in
`demos/certified_challenges/` puts that folder on `sys.path`. The checkers,
cases and assertions are unchanged.

See also [Certified Run Replay Store](Test-Certified-Run-Replay-Store.md),
[Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).
