# Steering: learning from runs

The strongest steering is what a system learns and feeds into its next prompts.
It is also the easiest to corrupt: one odd run, or one critic's label, can turn
into permanent guidance. The source project put explicit thresholds between a
run and a lesson, and between a failure and an antibody.

## What the source did

**Lessons from a run's own record.** After a run, a digestion step proposed
lessons of the form "when this trigger occurs, this outcome follows". The host
validated them only against recorded host facts:

- a lesson is admitted only when **two or more runs** support it and **no run is
  a counterexample**; support from a single run keeps it a candidate;
- a counterexample rejects it;
- the claimed outcome must follow the trigger in the record, and the cited
  evidence must resolve and match the recorded bytes;
- duplicate and vacuous lessons are rejected, and malformed candidates are
  refused at parse time;
- the catalogue entry pins the excerpt that witnesses the lesson.

**Antibodies from failures.** A separate miner harvested proposals only after
independent host replay:

- a skill candidate needs a replay, and is stored only as a review candidate;
- an unavailable replay is an explicit residual, not a pass;
- a reproduced, typed refutation yields an **inert** antibody (it still needs
  review before it acts);
- a critic's label without a host refutation cannot mint an antibody;
- a rule candidate needs distinct recurring events: the same source event
  repeated does not meet the threshold, and the threshold is an exact integer of
  at least two;
- the harvest is byte-identical whatever the order of the batch.

**Carrying lessons forward.** When a report is turned into the next worker's
brief, detailed findings and vetoes are not collapsed to a status, a "pass" in
markdown does not erase a recorded veto, and objections that were not selected
as lessons are still carried into the next brief.

## Replicate it here

The miner is in `ops/adversary/use_cases/intelligence_miner.py`
(`mine_intelligence(observations, replay_port, recurrence_threshold, native_support)`);
it needs the native host for replay and is not runnable here as a whole. The
self-digestion validator was not copied into this repository.

The thresholds are simple enough to apply by hand to [PFP Lab](PFP-Lab.md)
receipts: run two different scenarios that share a pattern (for example
`cheapest-repair` and `ledger-reconciliation`, where the repair lands on the
least-weighted or least-trusted edge), and only record "repairs land on the
lightest edge" as a lesson if both receipts show it and no receipt contradicts
it.

```powershell
python -m pfp_lab.cli.main run --pack cheapest-repair
python -m pfp_lab.cli.main run --pack ledger-reconciliation
```

## How it relates to PFP, EIS and PCIV

- **EIS.** This is the antibody lifecycle's intake: reproduced refutations become
  inert antibodies, and only reviewed ones act
  ([EIS: antibody lifecycle](EIS-Antibody-Lifecycle.md),
  [regulation and custody](EIS-Regulation-and-Custody.md)).
- **PCIV.** Admitted lessons are what later prompt generations inherit
  ([PCIV: mutation and inheritance](PCIV-Mutation-and-Inheritance.md)); the
  two-run rule is a guard against inheriting noise.
- **PFP.** A lesson is a proposal about runs, checked against recorded host
  facts, exactly as a repair is checked against an obstruction.

## Where the code lives

`ops/adversary/use_cases/intelligence_miner.py`,
`ops/adversary/domain/intelligence_mining.py`,
`ops/adversary/use_cases/intelligence_digestion/` and
`ops/adversary/infrastructure/report_learning_host.py`.
