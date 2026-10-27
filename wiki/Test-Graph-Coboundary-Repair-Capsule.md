# Test: Graph Coboundary Repair Capsule

A worked challenge from graph cohomology with two independent checkers. Each
input is a graph whose edges carry a weight and a claimed difference between
their endpoints. Usually the claims are inconsistent around some cycle. The
task is to find the cheapest repair (weighted L1) that makes every claim an
exact difference of a vertex potential, and to prove the repair is optimal
with a dual certificate. The tests check that the reference answers pass both
checkers and that 40 corrupted answers fail both. Ported from an internal test
suite.

## Why it matters to PFP

The Proposal Fidelity Protocol accepts an answer only when a check outside the
proposer can confirm it (see [Core Concepts](Core-Concepts.md)). This capsule
shows what such a check looks like for an optimization problem: the answer
carries its own certificate (a potential, a repair and a dual circulation), so
the checker never has to trust the solver or re-solve the problem. Two checkers
written separately must agree; a disagreement is itself a failure. The minimum
repair cost, called Phi1 here, measures the obstruction: it is zero exactly
when the claims are already a coboundary (a difference of potentials).

## Setup and inputs

`demos/certified_challenges/c011_cycle_rank_ladder_coboundary_repair/`

- `reference_solver/` builds a spanning tree, finds the cycle basis, solves the
  minimum-L1 repair exactly with rational numbers, and emits the certificate.
  `ddc_tracer.py` records the solver's steps as a hash-chained trace.
- `judge_packet/checkers/circulation_checker.py` (checker 1) verifies the
  coboundary relation, primal cost, dual capacity, flow conservation at every
  vertex, complementary slackness, and equal primal and dual objectives.
- `judge_packet/checkers/potential_checker.py` (checker 2) checks the same
  certificate by an independent route and also checks that the repaired claims
  have zero holonomy around every fundamental cycle.
- `judge_packet/checkers/dual_evaluator.py` runs both and returns PASS only if
  both accept.
- `judge_packet/cases/`: 32 base graphs (trees, ladders, complete graphs), 8
  gauge controls (relabelled vertices, reversed edges, shifted potentials,
  rescaled weights, which must give the same Phi1 up to scale) and 6 poisoned
  cases (ties, huge values, dense fractions, traps for greedy repairs).
- `judge_packet/mutation_suite/mutations/`: 40 corrupted answers, for example a
  dual flow that leaks at a vertex, Phi1 off by a fraction, a float where an
  exact rational is required, `2/1` instead of `2`, a refusal on a solvable
  case, or a suboptimal repair on chords only.

All numbers on the wire are canonical rational strings such as `"3/2"`.

## How to run

From the repository root:

    python -m pytest demos/certified_challenges/test_c011_reference_cases.py demos/certified_challenges/c011_cycle_rank_ladder_coboundary_repair -q

Expected: `104 passed`. `python -m pytest demos/certified_challenges -q` runs all fifty challenge packages.

## What a failure means

- A failure in `test_c011_reference_cases.py` means the solver produced an
  answer one or both checkers reject, or the checkers disagree. Either the
  solver or a checker has a bug.
- A failure in `test_checker_mutations.py` means a corrupted answer was
  accepted. That is the serious case: the check has a hole a wrong proposer
  could pass through.
- `test_case_inventory` fails if case files were added or removed.

## How to modify it

Add a case by dropping a JSON file with `vertices` and `edges` (`id`, `u`,
`v`, `weight`, `claim`) into `cases/base/`, then update the expected count in
`test_case_inventory`. Add a mutation by saving a JSON object with `case`,
`result` (the corrupted answer) and `description` as `mut_NN_name.json` in
`mutation_suite/mutations/`. A good mutation is wrong in exactly one way.

## Ported notes

The package imports were rewritten to run from this repository; the mutation
suite logic was not changed. `test_c011_reference_cases.py` is new and runs
every case through the solver and the dual evaluator. The governance and
run-orchestration files of the original challenge were not ported. Related
pages: [Lattice Gauge Gauss Law Capsule](Test-Lattice-Gauge-Gauss-Law-Capsule.md),
[Commuting Pauli Ground State Capsule](Test-Commuting-Pauli-Ground-State-Capsule.md),
[Equational Proof Capsule](Test-Equational-Proof-Capsule.md).
