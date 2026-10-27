# Test: Lattice Gauge Gauss Law Capsule

A worked physics challenge with two independent checkers. The input is a
closed surface given as a cell complex (vertices, edges, oriented faces), for
example a tetrahedron, a torus grid, the projective plane or a genus-2 surface.
On that surface the Z2 lattice gauge model (the toric code) has star operators
at vertices and plaquette operators on faces. The answer reports the Euler
characteristic, the ranks of the star and plaquette operators, the number of
logical qubits k, the ground-state degeneracy 2^k, and explicit logical
operators. A second query type asks for the dimension of a Gauss-law charge
sector. Non-manifold inputs must be refused. The tests check reference answers
and 48 corrupted answers. Ported from an internal test suite.

## Why it matters to PFP

This is a check where a plausible shortcut is wrong. Many solvers compute k as
twice the genus, which is right for orientable surfaces and wrong for the
projective plane and other non-orientable ones; the poisoned cases and several
mutations target exactly that. PFP asks that a check verify the claim itself,
not its plausibility (see [Core Concepts](Core-Concepts.md)). The two checkers
use different mathematics:

- Checker 1 (stabilizer tableau) works over F2: it checks operator ranks,
  that each logical commutes with every stabilizer, that logical Z and X pair
  as a symplectic basis, and that no logical lies in the stabilizer span.
- Checker 2 (homology and cohomology) builds the cellular chain complex over
  Z2, checks Betti numbers, cycle and cocycle conditions, the intersection
  pairing, and for small complexes the ground-space dimension by exact dense
  linear algebra.

## Setup and inputs

`demos/certified_challenges/c039_lattice_z2_gauge_theory_gauss_law/`

- `reference_solver/`: `cell_complex.py`, `f2_algebra.py`, `gauss_sector.py`,
  `solver.py`, and a step tracer.
- `judge_packet/checkers/`: the two checkers and `dual_evaluator.py`.
- `judge_packet/cases/`: 32 base cases, 10 controls (relabelled, subdivided,
  refined and dual complexes, which must give the same k) and 6 poisoned cases
  (projective plane, Dyck surface, repeated edges, a pinched and a branched
  non-manifold).
- `judge_packet/mutation_suite/mutations/`: 48 corrupted answers such as k
  computed as 2g on a non-orientable surface, an anticommuting logical, a
  logical that is secretly a product of plaquettes, an under-reported rank, a
  wrong charge-sector dimension, an unwarranted refusal, a SOLVED answer on a
  non-manifold, a float or boolean in an integer field, or an extra key.

## How to run

From the repository root:

    python -m pytest demos/certified_challenges/test_c039_reference_cases.py demos/certified_challenges/c039_lattice_z2_gauge_theory_gauss_law -q

Expected: `76 passed` (49 reference-case tests, 4 mutation-suite tests and the package's own 23; the
mutation suite loops over all 48 files inside each test). Running
`python -m pytest demos/certified_challenges -q` runs all fifty challenge packages.

## What a failure means

- A reference-case failure: the solver gave an answer a checker rejects, or
  the checkers disagree.
- A mutation-suite failure lists the escaped mutation files by name. Any escape
  means a checker would accept a wrong physical claim.
- `test_mutation_count` requires exactly 48 mutation files.

## How to modify it

A case has `vertices`, `edges` (pairs of vertex ids), `faces` (lists of
`[edge index, orientation]`), `case_id` and `query` (`degeneracy` or
`gauss_law_sector`). Add it under `cases/base/` and update `test_case_inventory`. New
mutations go in `mutation_suite/mutations/` as `{"case", "result"}` objects;
update the expected count in `test_mutation_count`.

## Ported notes

Imports were rewritten to run from this repository; the mutation suite logic
is unchanged. `test_c039_reference_cases.py` is new. Governance and
run-orchestration files were not ported. Related:
[Graph Coboundary Repair Capsule](Test-Graph-Coboundary-Repair-Capsule.md),
[Commuting Pauli Ground State Capsule](Test-Commuting-Pauli-Ground-State-Capsule.md).
