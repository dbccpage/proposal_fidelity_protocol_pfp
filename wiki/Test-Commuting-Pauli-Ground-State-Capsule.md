# Test: Commuting Pauli Ground State Capsule

A worked quantum challenge with two independent checkers. The input is a
Hamiltonian on up to 8 qubits written as a weighted sum of Pauli-word terms,
each term rewarding a target eigenvalue of +1 or -1. When all terms commute the
answer is exact: the ground energy as a rational number, the ground-space
degeneracy, an independent generator basis, how each term decomposes over that
basis (with its sign), and every minimizing assignment. When two terms
anticommute the correct answer is OUT_OF_SCOPE with the offending pair as a
witness. The tests check that reference answers pass both checkers and that 51
corrupted answers fail. Ported from an internal test suite.

## Why it matters to PFP

PFP treats an answer as a proposal that must survive an independent check (see
[Core Concepts](Core-Concepts.md)). Here the two checkers do not share a
method. Checker 1 is algebraic: it works over the binary symplectic
representation of Pauli words and checks the certificate's internal structure.
Checker 2 never looks at the basis or decomposition: it builds the full matrix
H - E0*I over exact complex rationals and checks that it is positive
semidefinite with a kernel of exactly the claimed dimension. An answer that
fools one method is unlikely to fool the other. The capsule also shows typed
refusals: bad input gets a closed-list UNKNOWN code, not a guess.

## Setup and inputs

`demos/dual_checker_capsules/c021_q40_r/`

- `reference_solver/pauli.py` implements Pauli strings with exact phase
  tracking (Y = iXZ); `solver.py` finds the basis, enumerates the 2^k joint
  eigenvalue assignments and returns the certificate.
- `judge_packet/checkers/algebraic_checker.py` (checker 1),
  `spectral_checker.py` (checker 2; NumPy, if installed, adds a labelled
  secondary numeric check), and `dual_evaluator.py`.
- `judge_packet/cases/`: 30 base cases (21 solvable, 6 noncommuting, 3
  malformed), 8 controls (qubit permutation, term reordering, renaming,
  weight rescaling, local Clifford changes of basis) and 6 poisoned cases (a
  single anticommuting pair buried among 23 terms, Y-count phase traps,
  unreduced fractions, duplicate ids).
- `judge_packet/mutation_suite/mutations/`: 51 corrupted answers, for example
  a wrong energy, a float where an integer is required, a boolean in place of
  a count, an extra non-minimal assignment, a duplicate generator, a wrong
  decomposition mask, a false OUT_OF_SCOPE claim, or an empty object.

## How to run

From the repository root:

    python -m pytest demos/dual_checker_capsules/test_c021_reference_cases.py demos/dual_checker_capsules/c021_q40_r -q

Expected: `97 passed`. Running `python -m pytest demos/dual_checker_capsules -q` runs all four capsules (`351 passed`).

## What a failure means

- `test_c021_reference_cases.py` failing: the solver and checkers disagree on
  a case, or the two checkers disagree with each other.
- `test_checker_mutations.py` failing: a corrupted answer was accepted by at
  least one checker or by the dual evaluator. Fix the checker, not the
  mutation.

## How to modify it

A case is `{"id", "n", "terms": [{"id", "P", "w": [p, q], "target"}]}` where
`P` is a Pauli word of length `n` and `w` is a positive fraction p/q. Add one
to `cases/base/` and update the count in `test_case_inventory`. A mutation is a
JSON object with `case`, `result` and `description` in
`mutation_suite/mutations/`.

## Ported notes

Imports were rewritten to run from this repository; the mutation suite logic
is unchanged. `test_c021_reference_cases.py` is new. The original challenge's
governance and run-orchestration files were not ported. Related:
[Graph Coboundary Repair Capsule](Test-Graph-Coboundary-Repair-Capsule.md),
[Lattice Gauge Gauss Law Capsule](Test-Lattice-Gauge-Gauss-Law-Capsule.md).
