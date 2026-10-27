# Test: Exact LP Dual Certificates

A linear-programming challenge in which every answer carries a certificate the checker can verify with exact rational arithmetic. A claimed optimum must come with a dual solution that proves it optimal; a claimed infeasible problem must come with a Farkas vector; a claimed unbounded problem must come with a feasible point and an improving ray. The tests confirm that the reference solver passes both checkers and that every corrupted answer fails both.

## What it tests and why it matters to PFP

The problem is: maximise `c^T x` subject to `A x <= b`, `x >= 0`, with all
numbers given as exact rationals. A proposer (for example a language model) can
easily state a wrong optimum. The PFP point is that the checker never re-solves
the problem and never trusts the proposer: it checks the certificate.

- **OPTIMAL**: `x` is feasible, `y >= 0` with `A^T y >= c`, and
  `c^T x = b^T y` (weak duality made tight).
- **INFEASIBLE**: a Farkas vector `y >= 0` with `A^T y >= 0` and `b^T y < 0`.
- **UNBOUNDED**: a feasible `x` and a ray `d >= 0` with `A d <= 0` and
  `c^T d > 0`.
- All numbers must be canonical rational strings (`"3"`, `"-1/2"`, never
  `"2/4"`, `"02"`, `"2.0"` or an integer). This blocks answers that pass by
  format looseness.

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

The 64 judge cases cover degenerate vertices (including Beale's cycling
example), small and dense matrices, infeasible systems, unbounded rays and
malformed inputs. The 48 mutations include flipped dual signs, primal values
off by a small fraction, spoofed objective values, zero or negative Farkas
vectors, zero rays, floats, Booleans, unreduced fractions and wrong status
claims.

## How to run

From the repository root (Python 3.12 standard library plus pytest):

    python -m pytest demos/certified_challenges/c051_exact_lp_solver_with_duals -q

Score the reference solver on the 14 public examples (the runner takes the
path of any solver file that defines `solve(case)`):

    python demos/certified_challenges/c051_exact_lp_solver_with_duals/participant_packet/runner.py demos/certified_challenges/c051_exact_lp_solver_with_duals/reference_solver/solver.py

## Expected output

`36 passed`. The runner prints `Runner result: 14/14 passed.`

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

- To test your own solver, write a file with `solve(case) -> dict` and pass
  its path to `runner.py`, then run both checkers over `judge_packet/cases`.
- To add a corrupted answer, copy a file in `hostile_mutations/` and change
  one field; the test
  `test_reference_solver_passes_and_every_hostile_mutation_fails_both_checkers`
  picks it up automatically.
- The parametrised tests list the non-canonical strings and non-numeric case
  entries checked; extend those lists to probe the parsers further.

## Where it lives

`demos/certified_challenges/c051_exact_lp_solver_with_duals`. Ported from an internal test suite. Imports were changed from the
original package path to the package's own name, and the `conftest.py` in
`demos/certified_challenges/` puts that folder on `sys.path`. The checkers,
cases and assertions are unchanged.

See also [Certified Run Replay Store](Test-Certified-Run-Replay-Store.md),
[Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).
