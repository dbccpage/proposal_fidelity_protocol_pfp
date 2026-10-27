# Test: Max Flow Min Cut Certificates

A maximum-flow challenge where an answer is accepted only with a minimum-cut certificate. The checker verifies the flow and the cut with integer arithmetic and the max-flow min-cut theorem; it does not need to trust the solver's algorithm. The ported test runs the reference solver through both checkers, stores the runs and replays them, and confirms a sample of corrupted answers is rejected.

## What it tests and why it matters to PFP

Given a directed graph with integer capacities, a source `s` and a sink `t`,
the answer is a flow on every arc plus a set `S` of nodes containing `s` and
not `t`. The checkers confirm:

- every arc flow is between 0 and its capacity, and flow is conserved at every
  inner node;
- the flow value equals the capacity of the cut leaving `S`;
- every arc leaving `S` is saturated and every arc entering `S` carries zero.

By the max-flow min-cut theorem these conditions together prove the flow is
maximum. This is the PFP pattern: a cheap check of a certificate replaces
trust in an expensive computation.

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

The 64 judge cases include layered graphs, adversarial bottlenecks,
bipartite matchings, unreachable sinks, parallel and antiparallel arcs, grids,
capacities up to 2^63 and sums beyond 10^18 (exact integers, no overflow),
node relabelings and malformed inputs. The 48 mutations cover over-capacity
arcs, broken conservation, wrong cut sets, unsaturated cut arcs, floats,
scientific notation, Booleans, missing fields and spoofed statuses.
`matrix_cases.py` holds ten small cases used by the replay test.

## How to run

From the repository root (Python 3.12 standard library plus pytest):

This package has no test folder of its own; its test is the replay-custody
test:

    python -m pytest demos/certified_challenges/test_c052_replay_custody.py -q

Score the reference solver on the public examples:

    python demos/certified_challenges/c052_maxflow_mincut_certificates/participant_packet/runner.py --all-examples

## Expected output

`2 passed`. The runner prints one `[PASS]` line per example and `Summary: 14/14 passed.`

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

- The replay test only samples the first five mutations. To check all 48,
  change `[:5]` to `[:]` in `test_c052_replay_custody.py`, or loop over
  `judge_packet/hostile_mutations` with both checkers.
- `runner.py --case <file>` scores a single input file.
- Add graphs to `matrix_cases.py` to widen the replay test.

## Where it lives

`demos/certified_challenges/c052_maxflow_mincut_certificates`. Ported from an internal test suite. Imports were changed from the
original package path to the package's own name, and the `conftest.py` in
`demos/certified_challenges/` puts that folder on `sys.path`. The checkers,
cases and assertions are unchanged.

See also [Certified Run Replay Store](Test-Certified-Run-Replay-Store.md),
[Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).
