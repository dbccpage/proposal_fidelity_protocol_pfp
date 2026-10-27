# Test: Exact Linear System Witnesses

An exact linear-systems challenge. For a consistent system the answer gives a solution, a nullspace basis, the rank and two minors that certify the rank and the basis; for an inconsistent one it gives a witness vector that proves no solution exists. The tests make sure malformed replies are typed rejections rather than checker crashes, and that every corrupted answer is rejected.

## What it tests and why it matters to PFP

Given `A` and `b` over the rationals:

- **CONSISTENT**: `x` with `A x = b`; a nullspace basis `N` with `A N = 0`; the
  rank `r`; row and column indices of an `r x r` minor of `A` with nonzero
  determinant (so the rank is at least `r`); row indices of a square minor of
  `N` with nonzero determinant (so the basis is independent); and
  `r + len(N) = n` (so it is complete).
- **INCONSISTENT**: a vector `y` with `y^T A = 0` and `y^T b != 0`. Then
  `0 = y^T A x = y^T b != 0`, so no `x` exists.

Every claim is backed by something the checker can verify in polynomial time.
The test file's theme is robustness of the checker itself: a checker that
crashes on an odd reply (a list instead of an object, a string index, a
Boolean) is not a reliable refusal, so each such reply must produce
`(False, message)`.

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

64 judge cases from 0x0 and 1x1 systems up to 15x15, wide and tall,
rank-deficient consistent and inconsistent systems, Hilbert and Vandermonde
matrices, large denominators and 64-bit values, row permutations and malformed
inputs. 48 mutations: wrong `x` or `y`, swapped verdicts, overstated or
understated rank, singular minors, out-of-range or duplicate indices,
dependent bases, floats, unreduced fractions, Booleans and missing fields.

## How to run

From the repository root (Python 3.12 standard library plus pytest):

    python -m pytest demos/certified_challenges/c054_exact_linear_systems -q
    python -m pytest demos/certified_challenges/test_c054_replay_custody.py -q
    python demos/certified_challenges/c054_exact_linear_systems/participant_packet/runner.py

## Expected output

`45 passed`, then `2 passed`, then `Result: 14/14 passed.` and `ALL EXAMPLES PASSED SUCCESSFULLY.`

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

- Add odd reply shapes to `test_non_object_reply_is_a_typed_rejection`.
- `judge_packet/generate_mutations.py` regenerates the mutations and itself
  reports whether both checkers kill all 48.
- The empty 0x0 system has its own test: even a trivial system must carry a
  real certificate.

## Where it lives

`demos/certified_challenges/c054_exact_linear_systems`. Ported from an internal test suite. Imports were changed from the
original package path to the package's own name, and the `conftest.py` in
`demos/certified_challenges/` puts that folder on `sys.path`. The checkers,
cases and assertions are unchanged.

See also [Certified Run Replay Store](Test-Certified-Run-Replay-Store.md),
[Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).
