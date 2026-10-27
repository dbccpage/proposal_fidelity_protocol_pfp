# Test: Stage Receipt Tape

Each review stage of a paper (red team, improver, adversary, proof sign-off,
release preflight, public build, final red team) leaves a receipt on an
append-only tape, one JSON line per receipt in `stages.ndjson`. These tests
check that the tape keeps history byte for byte, refuses receipts that break
the role rules or the rebuild rule, and never writes anything when it refuses.

## What it tests

`test_paper_run_stage_tape.py` (14 tests):

- Role gate: a receipt in which a proposer claims a pass is refused with
  "transition refused", using the same validator as
  [Paper-Run Role-Gated Transitions](Test-Paper-Run-Role-Gated-Transitions.md).
- Rebuild rule: once the public-build stage has completed, a later receipt
  that reports a source change is refused ("rebuild required") unless it is
  itself a new build stage.
- Exact contents: for each status (STARTED, COMPLETED, SKIPPED, FAILED) the
  stored line equals an expected dictionary, including the default role
  (evaluator) and event type chosen for that status, and nothing else is
  written to the job folder.
- History is preserved: a tape with older, differently formatted lines (extra
  field, CRLF, blank line) keeps those bytes untouched; the new line is
  appended after them.
- A real write failure (the tape path is a directory) raises `OSError` rather
  than being reported as success.
- A refused receipt neither creates the tape nor extends an existing one.
- A receipt cannot claim global green or a non-`None` authority effect.

## Why it matters to PFP

A receipt trail only helps if it is append-only and if refused steps leave no
trace that could later be mistaken for evidence. These tests pin both, and
they pin the rule that editing after the build invalidates the build until a
new one is recorded. The docstring is explicit about the limits: the tape is
not authenticated or tamper-evident, and a receipt records what a caller
submitted, not proof that a stage ran. See [Core Concepts](Core-Concepts.md).

## Setup and inputs

Each test makes a fresh job folder under pytest's temporary directory.
Receipts are built either with fixed fields (so the stored bytes are
predictable) or with `StageReceipt.issue`, which fills in an id and time.

## How to run

From the repository root:

    python -m pytest demos/paper_run_rules/test_paper_run_stage_tape.py -q

## Expected output

`14 passed` in under a second.

## What a failure means

- Byte comparison failures: the writer reformatted or rewrote earlier lines,
  so a reviewer can no longer trust that history is what was first recorded.
- A refusal test that finds a tape file: a refused step left a record.
- The rebuild test passing a mutation: a paper could be edited after its
  public build without the build being redone.

## How to modify it

The writer is `paperrun/stage_driver.py`. `StageDriver.append_receipt` runs
the authority check, then `enforce_rebuild_contract`, then
`enforce_transition`, and only then opens the tape. Keep that order: every
check must run before the first byte is written.

## Port notes

Ported from an internal test suite; two test files were merged. A
subprocess test about an internal tracing library and a test of a letter
summary of the tape were not ported, and that letter feature was removed from
the ported driver. Stage and schema names were made neutral. The
global-green and authority test is new.

## Location

`demos/paper_run_rules/` (package `paperrun/`).
