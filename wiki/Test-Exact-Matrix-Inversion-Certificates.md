# Test: Exact Matrix Inversion Certificates

An exact matrix-inversion challenge (fraction-free Bareiss elimination in the reference solver). An invertible answer must give the determinant, the adjugate and the inverse; a singular answer must give a nonzero null vector. The tests pin down two real checker bugs found in an audit and confirm every corrupted answer is rejected.

## What it tests and why it matters to PFP

For an invertible matrix `A` the checkers verify `A adj(A) = det(A) I` and
`A A^-1 = I`; for a singular one they verify `A v = 0` with `v != 0`. The
interesting lesson is the audit bug this test pins: with `A = I`, an answer of
`det = 5`, `adj = 5I` and `inverse = I` satisfies `A adj(A) = det I` and
`inverse = adj / det`, yet the determinant is 1. A checker that only tests the
identities, and not the determinant itself, accepts a wrong answer. The fixed
exact checker pins the determinant; the test
`test_scaled_determinant_and_adjugate_are_rejected` keeps it fixed.

The second pinned bug: both checkers once accepted the non-canonical strings
`"4/1"` and `"0/1"`. Both now share one canonical-rational parser
(`judge_packet/canonical_rational.py`), and a test checks that this parser's
text is identical to the copy used by the linear-systems challenge.

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

64 judge cases: scaled identities, diagonal, triangular, dense and circulant
matrices, rational and Hilbert matrices, large integers (64-bit determinants),
singular matrices of several ranks, row permutations and malformed inputs.
48 mutations: wrong determinants, corrupted or untransposed adjugates, the
undivided adjugate passed off as the inverse, singular matrices claimed
invertible and the reverse, invalid null vectors, floats, Booleans, raw
integers and spoofed statuses.

## How to run

From the repository root (Python 3.12 standard library plus pytest):

    python -m pytest demos/certified_challenges/c053_bareiss_fraction_free_matrix_inversion -q
    python -m pytest demos/certified_challenges/test_c053_replay_custody.py -q
    python demos/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/participant_packet/runner.py --all-examples

## Expected output

`35 passed`, then `2 passed`, then `Summary: 14/14 passed.`

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

- Add canonical and non-canonical strings to the parametrised parser tests
  to probe `canonical_rational.py`.
- Add known determinants to `test_bareiss_determinant_matches_known_values`.
- If you change `canonical_rational.py`, change the copy in
  `c054_exact_linear_systems/judge_packet/` too, or the shared-text test
  fails by design.

## Where it lives

`demos/certified_challenges/c053_bareiss_fraction_free_matrix_inversion`. Ported from an internal test suite. Imports were changed from the
original package path to the package's own name, and the `conftest.py` in
`demos/certified_challenges/` puts that folder on `sys.path`. The checkers,
cases and assertions are unchanged.

See also [Certified Run Replay Store](Test-Certified-Run-Replay-Store.md),
[Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).
