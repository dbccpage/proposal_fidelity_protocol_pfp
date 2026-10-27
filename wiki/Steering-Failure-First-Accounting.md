# Steering: failure-first accounting

A multi-reviewer run is easy to steer with approvals: if enough reviewers say
"looks good", the run feels done. The source project changed what counts. In
its accounting, **an approval carries zero acceptance weight**, "no failure
found" is absence of evidence, and only a reviewer finding that the host
reproduces counts as a detected failure.

## What the source did

**Failure-first currency.**

- An approval adds nothing to acceptance.
- "None found" is recorded as absence of evidence, never as proof of
  correctness.
- A reviewer finding that the host checker confirms is a reproduced failure and
  triggers repair.
- A finding the host does not confirm is recorded as a false alarm. False alarms
  are tracked, but they cannot block clearance once every real defect is caught.
- Several reviewers' claims are evaluated independently against the host's
  ground truth.

**Roster accounting.** For each run the record keeps five fields for the role
roster: declared, scheduled, contributed, missing, and whether the run is
complete. Any unscheduled role that did not contribute makes the run incomplete.
Reporting a skipped role as having contributed fails the audit. Under a reduced
schedule only the scheduled roles are expected.

Mutation tests guard each rule: counting an unreproduced claim as a detection,
treating "none found" or an approval as a pass, switching off a required role,
ignoring the quorum count, or reporting a skipped role as observed all fail
closed.

The same accounting feeds arm comparisons: each trial records reproduced
failures and false alarms alongside cost, so a reviewer configuration is valued
by the unique failures it finds, not by how often it agrees.

## Replicate it here

The statistics half is a runnable demo: [Yardstick arm statistics](Test-Yardstick-Arm-Statistics.md)
covers Wilson intervals, exact McNemar, the Pareto frontier and the
unique-finding value of each reviewer.

```powershell
python -m pytest demos/yardstick -q
```

The accounting rules are in `ops/adversary/use_cases/yardstick.py` (`Trial`,
`ArmStats`, `seat_value`) and `ops/adversary/use_cases/teamwork.py`; every
`teamwork` command prints the roster record as `panel_coverage` (declared,
scheduled, contributed, missing, reproduced failures, false alarms); see
[running the local swarm](Steering.md#running-the-local-swarm).

[PFP Lab](PFP-Lab.md) has the same asymmetry in miniature: an admitted `ASSERT`
or `CUT` is not a verification, and the only move that establishes zero
obstruction is a `VERIFY` that the Lab recomputes.

## How it relates to PFP, EIS and PCIV

- **PFP.** Reviewers are proposers. Their findings are claims the host checks;
  their approvals are not claims at all.
- **EIS.** Reproduced failures are Signal 2 evidence; false alarms are
  Signal 1 without damage, which the [two-signal rule](Steering-Self-Certification-Screen.md)
  treats as diagnostic only.
- **PCIV.** Selection on approvals would breed agreeable variants. Selection on
  reproduced failures found per unit cost breeds useful reviewers.

## Where the code lives

`ops/adversary/use_cases/yardstick.py`, `ops/adversary/use_cases/teamwork.py`
and `ops/adversary/use_cases/teamwork_schedule.py`.
