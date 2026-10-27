# Test: Equational Proof Capsule

A worked logic challenge with two independent checkers. Each input is a set of
equational axioms (for example associativity, a unit law, an involution) and a
goal equation between two terms. The answer is either a PROOF, a chain of
rewrite steps where each step names an axiom, a direction, a position in the
term and a substitution, or a COUNTERMODEL, a finite operation table in which
every axiom holds and the goal fails. Malformed input must be answered
OUT_OF_SCOPE. The tests check that the reference solver's answers pass both
checkers on 64 cases and that 48 hostile answers fail both. Ported from an
internal test suite.

## Why it matters to PFP

A proof or a countermodel is a certificate that can be checked step by step
without trusting whoever produced it, which is the core move in PFP (see
[Core Concepts](Core-Concepts.md)). The capsule tests the check in both
directions: valid certificates must be accepted (no false rejections) and
forged ones must be rejected (no false acceptances). The second checker parses
and evaluates terms with its own code, so a bug shared by the solver and the
first checker does not automatically pass.

## Setup and inputs

`demos/certified_challenges/c050_equational_theorem_proving/`

- `reference_solver/terms.py` (terms, positions, substitution, one rewrite
  step), `prover.py` (bounded bidirectional breadth-first rewrite search),
  `countermodel.py` (finite model search and checking), `solver.py`.
- `judge_packet/exact_checker.py` replays each rewrite step and checks
  countermodels. `judge_packet/independent_checker.py` does the same with
  independent parsing and evaluation.
- `judge_packet/cases/`: 36 base cases (groups, monoids, lattices, Boolean
  identities, combinators; some provable, some refutable), 16 gauge cases
  (renamed symbols and reoriented axioms that must not change the outcome) and
  12 poisoned cases (misleading notes that claim a law holds, malformed
  axioms or goals).
- `judge_packet/hostile_mutations/`: 48 forged answers, six each of: invalid
  position, forged step result, bad substitution, skipped step, wrong goal
  right-hand side, countermodel in which the goal actually holds, countermodel
  too large, and a false OUT_OF_SCOPE.

Terms are JSON: a variable or constant is a string, an application is a list
`["f", arg1, ...]`.

## How to run

From the repository root:

    python -m pytest demos/certified_challenges/test_c050_reference_and_mutations.py -q

Expected: `113 passed` (1 inventory test, 64 case tests, 48 mutation tests).
`python -m pytest demos/certified_challenges -q` runs all fifty challenge packages.

## What a failure means

- `test_reference_answer_passes_both_checkers` failing: the solver's proof or
  countermodel was rejected. Either the solver produced an invalid
  certificate or a checker is too strict.
- `test_hostile_mutation_rejected_by_both_checkers` failing: a forged
  certificate was accepted, so the check has a hole.
- `test_inventory` fails if case or mutation files were added or removed.

## How to modify it

Add a case as `{"case_id", "axioms": [[lhs, rhs], ...], "goal": [s, t]}` to
`judge_packet/cases/` and update `test_inventory`. Add a hostile answer as
`{"mutation_id", "case", "candidate", "expected_rejection"}` to
`judge_packet/hostile_mutations/`. The prover has a search budget, so a goal
that needs a long proof may come back UNKNOWN and fail the reference test.

## Ported notes

The test file is new for this repository: the original capsule ran its cases
and mutations inside a larger campaign runner that was not ported. The solver
and both checkers are unchanged apart from import paths. Related:
[Graph Coboundary Repair Capsule](Test-Graph-Coboundary-Repair-Capsule.md).
