# Steering: critique loop

Asking one model to critique another is a popular way to steer toward better
answers. The source project kept the loop but took the decision away from the
critic. Critiques are typed findings with counterexamples, an external diff
oracle decides each round, rejected candidates are buried in a ledger, and a
blocking challenge cannot be talked away later.

## What the source did

**Rounds.** A model proposes a code change. The host computes the unified diff
against the base module, checks syntax and static invariants (for example, no
floating-point constants where exact arithmetic is required), runs the tests in
isolation, and writes a receipt bound to the exact candidate bytes. A failing
candidate is buried in a ledger of rejected candidates with its diff, and the
next round gets the counterexample. There are at most three repair rounds. An
offline verifier later reproduces every digest, recomputes every diff and reruns
the oracle.

**Typed critiques.** A critic must end its reply with exactly one block holding
`blocking`, `counterexample` and an optional `kind`. A blocking critique must
give a non-empty counterexample. A missing block, two blocks or bad JSON make the
critique malformed, and **a malformed critique blocks**. Keywords in prose decide
nothing (see [Honest verdicts](Steering-Honest-Verdicts.md)).

**Selection.** Blocking challenges survive the step from critique to selection:

- a blocked candidate is skipped but its evidence is kept;
- if every candidate is blocked, the run holds, even if admission was requested;
- a later non-blocking opinion does not clear an earlier countermodel;
- a defect without a kill disposition cannot reach selection.

**Stopping.** Malformed replies, or replies whose cost is unknown, stop the loop
before they reach the oracle or another round. The stop keeps the real
candidate and the exact raw reply, and no receipt is invented.

## Replicate it here

The critique service is in `ops/adversary/use_cases/multi_round_critique_service.py`
and the oracle in `ops/adversary/infrastructure/diff_oracle.py`; parsing the
critique block needs the native host, so the loop is not runnable here as a
whole.

Two runnable pieces show the parts:

- [Candidate revision telemetry](Test-Candidate-Revision-Telemetry.md) has the
  fault tracing, content-hashed diffs and checkpoint backtracking used between
  rounds:
  `python -m pytest demos/candidate_telemetry -q`
- [PFP Lab](PFP-Lab.md) keeps every refused move in its receipt, which is the
  same idea as the ledger of buried candidates. In `refusal-gallery`, twelve of
  thirteen proposals are refused and each one stays in the record:
  `python -m pfp_lab.cli.main run --pack refusal-gallery --json`

## How it relates to PFP, EIS and PCIV

- **PFP.** The critic is another proposer. Its finding counts only when the
  oracle reproduces it; see [Failure-first accounting](Steering-Failure-First-Accounting.md).
- **EIS.** Buried candidates with reproduced counterexamples are the raw material
  for antibodies ([Learning from runs](Steering-Learning-From-Runs.md)).
- **PCIV.** The ledger of rejected candidates is the lineage's death record;
  regression tests against it stop a later generation from reviving a known
  failure (`ops/adversary/use_cases/cemetery_regression.py`).

## Where the code lives

`ops/adversary/use_cases/multi_round_critique_service.py`,
`ops/adversary/infrastructure/diff_oracle.py`,
`ops/adversary/domain/evidence.py` and
`pfp/domain/entities/cemetery_entry.py`.
