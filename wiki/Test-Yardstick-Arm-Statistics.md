# Test: Yardstick Arm Statistics

This demo ports a statistics module and its tests. The module answers one
question for any set of "arms" (a model, a prompt, or a configuration of
reviewing roles): how often is the arm right, and what does each right answer
cost? "Right" never means "close to the truth" as judged by the arm itself; it
means an independent checker accepted the answer. The tests pin each statistic
to values that can be checked by hand, so the numbers a PFP experiment reports
can be trusted to mean what they say.

## Why it matters to PFP

PFP (see [Core Concepts](Core-Concepts.md)) separates what a proposer claims
from what a checker verifies. When you compare two ways of producing proposals,
the honest score is the rate of checker-accepted results, with an uncertainty
interval, and the cost per accepted result. This yardstick is that score. It
also shows a guarded learning loop: a new composition of reviewing roles is
only promoted when it measurably beats the baseline, and a tool that keeps
finding nothing is retired. The composition of roles is described in
[Operads](Operads.md).

## What is tested

- **Wilson interval.** The 95% score interval for a success rate matches
  published values (for example 5 of 10 gives about 0.2366 to 0.7634) and
  refuses impossible counts (negative, more wins than trials, or a boolean).
- **Summary per arm.** Mean cost, median wall time, cost per correct answer and
  time per correct answer. An arm with no successes has no cost per success
  (`None`), not infinity or zero.
- **Exact McNemar test.** Two-sided exact p-value on discordant pairs (tasks
  where only one of two arms was right).
- **Distance to a reference arm.** Only tasks both arms ran are compared, and
  repeated trials are paired one to one, not just the first trial per task.
- **Pareto frontier.** An arm survives unless another arm is at least as good
  on success rate, mean cost and wall time, and strictly better on one.
- **Seat value.** A reviewing role ("seat") gets credit for a finding only when
  no other seat in the same run raised the same text (case and surrounding
  spaces ignored), and a repeated finding counts once per seat per run.
- **Schedule telemetry.** One record per run with the schedule name, total
  cost to the micro-dollar, per-seat value and resolved obstructions.
- **Thompson sampling.** With a fixed seed, the schedule with high success per
  unit cost is chosen; an empty candidate list is refused.
- **Operand promotion.** A candidate composition is admitted only when its
  yield improves on the baseline by at least the threshold; otherwise it stays
  a candidate.
- **Yield per dollar and retirement.** Unique failures found per dollar; an
  operad is retired only after enough evaluation runs with zero yield, so a new
  one is not retired early.

## How to run

From the repository root:

    python -m pytest demos/yardstick -q

Only the standard library and pytest are needed.

## Expected output

    18 passed

## What a failure means

A failure in the Wilson, McNemar or summary tests means a reported rate,
interval or p-value would be wrong, so any comparison built on it is suspect.
A failure in the distance or seat-value tests means credit is being given for
work that was not paired or not unique. A failure in the promotion or
retirement tests means the learning loop could keep a change that did not help,
or drop a tool before it was fairly measured.

## How to modify it

Add cases with the `trial(arm, task, ok, cost, wall, tokens)` helper in the
test file. To check a new interval value, compute it independently (any
statistics package's Wilson score interval) and add it to the parametrized
list. To change the promotion rule, edit `promote_candidate_operand` in
`arm_yardstick.py` and update the threshold cases.

## Notes on the port

Ported from an internal test suite. Two source test files were merged into
one. Imports were changed to load the module from the demo folder. Role names
in the fixtures were replaced with plain role words. Two checks were not
ported: a thin wrapper that only forwards to `thompson_sampling_schedule`, and
a test that attaches reproduced failures to a prompt family, which needs
modules not in this repository. One attribute read by `Trial.from_run` was
renamed to `panel_coverage`.

## Location

`demos/yardstick/arm_yardstick.py` and `demos/yardstick/test_arm_yardstick.py`.
