# Test: Candidate Revision Telemetry

When a candidate program is revised over several rounds, each round leaves
something worth recording: did the new version parse, what changed, and is the
search going anywhere. This demo ports three small standard-library tools for
that, and five tests that pin their behaviour: an AST fault tracer, a diff
telemetry record, and a checkpoint tree that recommends backtracking after
repeated rejections. Ported from an internal test suite.

## Why it matters to PFP

Under the Proposal Fidelity Protocol each revised candidate is a new proposal,
checked independently and either accepted or refused (see
[Core Concepts](Core-Concepts.md)). These tools do not decide acceptance. They
produce plain, reproducible records about each round: a structural fault
report, a content-hashed diff between parent and child, and a history of
verdicts that tells the loop when to return to an earlier, better candidate
instead of patching a failing one again.

## The pieces

**AST fault tracer** (`trace_ast_faults(code)`). Parses the code and returns an
`AstFaultReport` with: whether it failed to parse and why, the names of
declared functions, the names it reads, and "illegal nodes". The only illegal
node today is a float literal, reported as `FloatConstant(value=..., line=...)`,
for work that must use exact rational arithmetic.

**Diff telemetry** (`compute_dense_diff_telemetry(...)`). Builds a unified diff
from the parent candidate to the new one and records the diff text, its
`sha256:` hash, lines added and removed, the ratio of changed lines to parent
lines, and an "amortization score": changed lines per 1000 tokens billed for
the round.

**Checkpoint tree** (`MctsStateGraph`). Starts with a root checkpoint. Each
`record_candidate` call adds a child of the current tip and moves the tip
there. `check_need_backtrack(threshold_failures)` counts consecutive
non-`ACCEPTED` verdicts walking up from the tip; at or above the threshold it
recommends the ancestor with the highest oracle score. `backtrack_to(id)` moves
the tip.

## What the tests check

1. Clean code parses, its function is listed, and no illegal nodes are found.
2. Malformed code (`def invalid_syntax(` with no closing parenthesis) is
   reported as a `SyntaxError`.
3. Code containing `3.14159` reports a `FloatConstant` illegal node.
4. Replacing one line with two gives 2 added and 1 removed lines, a `sha256:`
   hash, a positive amortization score, and the new text in the diff.
5. After one rejected candidate no backtrack is recommended; after a second the
   tree recommends an ancestor (`root` or `c1`), and backtracking moves the tip
   there.

## How to run

From the repository root:

    python -m pytest demos/candidate_telemetry -q

## Expected output

    .....                                                                    [100%]
    5 passed

## What a failure means

- Tests 1 to 3: the tracer misreports structure, so a checker relying on it
  could pass unparseable code or miss floats where exact arithmetic is required.
- Test 4: diff counts or hashes are wrong, so round-to-round records cannot be
  compared or reproduced.
- Test 5: the backtracking rule changed; a loop could keep patching a branch
  that keeps failing, or abandon one too early.

## How to modify it

- Add illegal node types in `_AstFaultVisitor` (for example forbidding `eval`
  calls) with a test per node type.
- Change the threshold passed to `check_need_backtrack` to see how many failed
  rounds the loop tolerates.
- The scores here are floats for telemetry only; they are not used as evidence.

## Where it lives

- `demos/candidate_telemetry/ast_fault_tracer.py`
- `demos/candidate_telemetry/diff_telemetry.py`
- `demos/candidate_telemetry/state_graph_recovery.py`
- `demos/candidate_telemetry/test_candidate_telemetry.py`

Port notes: the original exposed the three modules through a lazily loading
package; here the test imports each module directly from its folder. An unused
import was removed. The checks are unchanged.
