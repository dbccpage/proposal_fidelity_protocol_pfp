# Local checks, global compatibility

Part of [Operads](Operads.md). Previous: [Bounded repair](Operads-Bounded-Repair.md)

When several agents each solve part of a problem, each local answer can be
checked and pass, and still the answers cannot be put together.
[Paper 025](Paper-025.md) states this precisely for finite tables, and draws the
line between that question and what typed operad composition checks.

## The setting

- A finite set of variables `V`, each with a finite domain.
- Each agent `i` has a **scope** `S_i ⊆ V` and an allowed relation `R_i`: a
  table of permitted value combinations for its scope.
- A **family** picks one row `a_i ∈ R_i` for every agent.

Two checks are separate: each row is in its own table (local satisfaction), and
each pair of rows agrees on the variables they share (overlap compatibility).

## The gluing theorem

**Theorem.** A locally permitted family glues to a unique assignment on the
union of the scopes exactly when every pair agrees on its intersection. If the
scopes cover `V`, compatible families correspond one-to-one with global
solutions.

**Why.** If a global assignment exists, its restrictions agree. Conversely, for
each covered variable take its value from any scope containing it; pairwise
agreement makes the choice independent of the scope, and the result restricts
to each chosen row. An uncovered variable breaks uniqueness, or existence if
its domain is empty, which is why full-domain tables are added for uncovered
variables when a global answer is required.

This fact is standard. Its use in PFP is as a contract: keep the local evidence
and expose missing global compatibility instead of hiding it.

## Three green lights, one red

Take Boolean `x, y, z`. Agent 1 checks `x = y`, agent 2 checks `y = z`, agent 3
checks `z ≠ x`. Each table has two rows, so **every local query succeeds**. But a
global answer would need `x = z` and `x ≠ z` at once.

```text
agent 1: (x, y) = (0, 0)     ✓ locally
agent 2: (y, z) = (0, 0)     ✓ locally
agent 3: (z, x) = (0, 1)     ✓ locally
overlap on x: 0 vs 1         ✗ globally
```

The disagreement on `x` is the **obstruction**: evidence that the declared
gluing requirement fails, kept rather than discarded. Change agent 3 to `z = x`
and the two global solutions `(0,0,0)` and `(1,1,1)` appear, each with
compatible restrictions.

This is the same shape as a cycle whose edge claims do not sum to zero, the
obstruction idea in [Core concepts](Core-Concepts.md): fine on every edge,
inconsistent around the loop.

## How an integrator should check

Each agent returns its actual row and a local certificate. The integrator
replays local membership and then checks every shared variable before admitting
a global witness. A loss ledger or a narrative "we agree" cannot replace the
values. Renaming variables needs explicit bijections applied to the task and to
every witness; silently dropping an overlap changes the problem.

The reference replay in the paper's `code/replay.py` enumerates all eight
assignments, refuses the disagreeing family and accepts the compatible one. It
makes no model calls.

## Typed composition is a different obligation

The operad compiler checks that ports fit: ordered input and output slots,
declared effects, source-bound identities. That is **not** the gluing theorem.

| Question | Checked by | Not established by it |
| --- | --- | --- |
| Do the pieces fit together? | The [typed workflow](Operads-Typed-Workflows.md) compiler | That they agree on task identity, candidate bytes or shared state |
| Do local answers agree on shared variables? | An integrator replaying overlaps | That effects, timing or authority compose |
| Did the composite actually run? | Observed execution, as in [Bounded repair](Operads-Bounded-Repair.md) | That it solved the task in general |

Two callbacks with compatible types can still disagree on what they are working
on. That is why the repair workflow threads the same run key, request digest and
candidate identity through every step: the binding has to be carried and
checked, because the types alone cannot supply it.

## Across an experiment campaign

The same caution applies to comparing evaluations. Scores can be compared only
when they share experiment, source, checker, partition, model configuration and
budget identities. Agreement among several task scores is not proof of global
correctness, and a candidate that improves one family while degrading another
is kept as a rejected branch.
