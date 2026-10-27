# Steering: selected hint

A hint is the smallest steering move: one extra piece of context attached to a
task. The source project made hints typed and registered. A selected hint is a
single fixed attachment to a stored session, and its effect is judged by
rerunning the original task checker inside an evaluation the run had already
budgeted.

## What the source did

- The stored session was a typed graph of parts and links. Attaching the hint
  added exactly one part and one link (in the recorded run, 48 parts and 47
  links became 49 and 48). The source bytes stayed identical.
- The hint was a registered rule, applied by the host. It was an actual child in
  the existing composition, not text pasted into a prompt.
- The recheck used the run's second already-budgeted original-task evaluation.
  No checker override and no metadata rewrite were used.
- An invalid binding or a missing checker could not trigger an original-task
  check, and a result could not substitute a different source or promote
  "preserved" into authority.
- Scope was stated plainly: the recheck accepted, but this was a checked
  structural hint and a software-task recheck, **not evidence that the hint
  improves a model** or repairs a nonzero cochain.

## Replicate it here

The hint rule and its native composition are not runnable here yet
(`ops/adversary/infrastructure/typed_operad.py`).

The idea of a hint as one admissible move that is then checked can be shown with
[PFP Lab](PFP-Lab.md). In the `cheapest-repair` pack, two candidate repairs are
offered for the same loop; the governor refuses the one on the heavy edge and
admits the one on the lightest edge, and only `VERIFY` after the exact repair
succeeds:

```powershell
python -m pfp_lab.cli.main run --pack cheapest-repair
```

```text
step_006     CUT      no  DefectIncrease         9 -> 12
step_007     CUT      yes MonotonicDescent       9 -> 3
step_009     CUT      yes ExactRepair            3 -> 0
step_010     VERIFY   yes Verified               0 -> 0
```

Treat a hint the same way: apply it as one recorded move, then let the host
decide whether the task now passes.

## How it relates to PFP, EIS and PCIV

- **PFP.** A hint is a proposal to change the context; acceptance still comes
  from the original checker, inside the original budget.
- **Operads.** The hint is a typed child in the session's composition, applied by
  a registered rewrite ([Operads: bounded repair](Operads-Bounded-Repair.md)).
- **PCIV.** A hint that helps across many tasks is a candidate trait; one
  accepting recheck is not enough to call it one.

## Where the code lives

`ops/adversary/infrastructure/typed_operad.py`,
`ops/adversary/infrastructure/gate_occurrences.py` and
`ops/adversary/infrastructure/operad_binding.py`.
