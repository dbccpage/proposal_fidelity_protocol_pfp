# Test: QA Receipt Invariants

A software QA receipt is a small, sealed record that says what was tested,
what a static audit found, which deliberate code mutations were caught, and
a SHA-256 digest over all of it. This test suite tries to break the receipt's
value objects one invariant at a time and checks that each break is refused.
It is a direct example of the PFP habit of treating evidence as a typed,
checkable object rather than a log line (see [Core Concepts](Core-Concepts.md)).

## What it tests

The receipt is built from four parts:

- `StrictAuditSummary`: counts from a strict inspector (mock ornaments,
  silent skips, bare returns, blanket exceptions, layer-boundary violations,
  auto-repair rounds) and a veto status of `CLEAN`, `VETOED` or `BLOCKED`.
- `ExaminerTestRecord`: one test's result, with an examiner class from 1 to 5
  (Invariant, Negative Matrix, Pinned Digest, Golden Vector, Mutation
  Target). Class 0, meaning "decorative test that checks nothing", is illegal.
- `MutationEvidenceRecord`: one deliberate source mutation and whether a
  test killed it.
- `SoftwareQaReceiptV1`: the whole receipt, with `AuthorityEffect` fixed to
  `None` and a content digest that `verify_integrity()` recomputes.

Each of the 13 tests is written in a fixed four-part form:
INVARIANT (the rule), BREAK (the input that violates it), WITNESS (what the
test observes), and MUTATION (the one-line source change the test would
catch). The rules covered:

- examiner class 0 is refused; negative durations are refused;
- a `bool` is not accepted where a count `int` is required;
- auto-repair rounds may be 3 but not 4;
- an empty rollback-failure message is refused, and a rollback refusal is an
  `Err` carrying a typed `MutationRollbackFailure`, never a bare string;
- a receipt cannot be `PASSED` when the strict audit is not `CLEAN`;
- `tree_dirty=1` is refused (it must be an exact `bool`);
- equality is exact-type: a subclass with the same fields is not equal;
- an empty content digest fails integrity rather than being silently
  recomputed;
- only `killed`, `survived` and `equivalent` mutants count toward the
  mutation score denominator;
- the `qa_evidence` package imports nothing from outer layers or frameworks
  (checked by walking its AST).

## Why it matters to PFP

PFP asks that every claim of "done" be backed by a receipt someone else can
re-check. A receipt that can be built in an inconsistent state (passed
while vetoed, sealed with no digest, counting unknown mutants) would let a
proposal claim more than its evidence supports. These tests pin the
smallest set of rules that stop that.

## Setup and inputs

No external inputs. The tests construct receipts in memory with small
helper functions (`_audit`, `_examiner`, `_receipt`). Needs Python 3.12+
and pytest; no other dependencies.

## How to run

From the repository root:

    python -m pytest demos/qa_receipt_invariants -q

## Expected output

    13 passed

## What a failure means

Each test name states the rule it guards. A failure means the value objects
in `qa_evidence/qa_receipt.py` now accept an input they should refuse (or
refuse one they should accept). The `MUTATION` comment above the failing test
shows the kind of source change that causes it.

## How to modify it

- Add a rule: write the check in the relevant `__post_init__`, then add a
  test in the same INVARIANT / BREAK / WITNESS / MUTATION form.
- Try the mutations by hand: apply the one-line change from a test's
  `MUTATION` comment and confirm that test (and ideally only that test)
  turns red, then revert.

## Port notes

Ported from an internal test suite. The package was renamed to a local
`qa_evidence` package and its shared railway `Result` type was replaced by a
minimal `Err` class in `qa_evidence/result.py` with the same `is_ok`,
`is_err` and `unwrap_err()` behaviour. Field and class names were changed
to neutral role names; the checks are unchanged.

## Location

`demos/qa_receipt_invariants/` (tests in
`demos/qa_receipt_invariants/test_qa_evidence_falsification.py`, code in
`demos/qa_receipt_invariants/qa_evidence/`).
