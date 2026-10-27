# Test: Calibration Task Bank

A bank of five small tasks for calibrating a reviewer, whether a person or a
model, against answers that are computed rather than typed in. Each task is a
`prompt.md` the reviewer reads and an independent `check.py` that scores the
reviewer's JSON answer. The tests confirm that every checker accepts its own
computed reference and refuses deliberately wrong answers. Ported from an
internal test suite.

## Why it matters to PFP

The Proposal Fidelity Protocol separates the proposer from the check, and asks
that checks state exactly what they test (see [Core Concepts](Core-Concepts.md)).
This bank applies that to reviewing itself:

- The truth of every claim comes from the checker's own computation, never
  from a hand-written answer list.
- Some claims are planted as unsupported, for example "the checker has already
  accepted every claim". A reviewer cannot have seen that, so the correct move
  is to flag it, not to trust it.
- By default a checker prints only `{"pass": true}` or `{"pass": false}`, so a
  repair loop reading its output cannot learn which items were wrong.
- A checker refuses to score if its prompt no longer shows the exact data and
  claims it scores against, so a drifted prompt cannot silently change the
  task.

## The tasks

| Task | Kind | The reviewer must |
|---|---|---|
| `graph_cycle_rank` | exact | give vertex, edge and component counts, component sizes, cycle rank and a spanning forest of a 12-vertex multigraph |
| `hodge_split` | exact | give the discrete Hodge decomposition of an edge flow on a small 2-complex, as exact fractions |
| `review_graph_claims` | review | flag the false or unsupported claims among ten about that graph |
| `review_hodge_claims` | review | flag the false or unsupported claims among nine about that decomposition |
| `review_code_claims` | review | flag the false or unsupported claims among nine about a small word-count function |

A review answer is exactly `{"flagged_claims": ["c2", "c6"]}`. The code
checker executes only its own copy of the function, never reviewer text.

## What the tests check

1. For each review task: the computed reference passes; dropping one flagged
   claim (a miss), adding a true claim (a false alarm), adding an extra key, or
   wrapping the JSON in a code fence each fail.
2. For each review task: every claim in `check.py` appears verbatim in the
   prompt, and the prompt's format example names no real claim id.
3. Editing the code prompt (`lower()` to `upper()`) makes the checker refuse
   with "does not show the checked data or claims".
4. The two exact tasks accept their reference answers.

## How to run

From the repository root:

    python -m pytest demos/calibration_task_bank -q

To try a task by hand, write an answer file and run its checker:

    python -I demos/calibration_task_bank/tasks/review_graph_claims/check.py --reference
    python -I demos/calibration_task_bank/tasks/review_graph_claims/check.py --detail answer.json

`--reference` prints the computed answer key; `--detail` prints misses and
false alarms. Exit status 0 is pass, 1 is fail.

## Expected output

    .........                                                                [100%]
    9 passed

## What a failure means

- A reference failing its own checker: the computation and the scoring
  disagree, so the task is broken.
- A planted mistake passing: the checker is too lenient and would score a
  careless reviewer as correct.
- The drift test passing a changed prompt: the task could be altered without
  anyone noticing.

## How to modify it

Add a task as a new folder under `tasks/` with `prompt.md` and `check.py`.
Compute every claim's truth in `check.py`, call `review_common.run(...)` with
the prompt fragments that must appear, then add the folder name to
`REVIEW_TASKS` in the test.

## Where it lives

- Tasks: `demos/calibration_task_bank/tasks/`
- Tests: `demos/calibration_task_bank/test_calibration_tasks.py`

Port notes: the task folder moved next to the test, so the test's path to it
changed. The checkers and prompts are unchanged.
