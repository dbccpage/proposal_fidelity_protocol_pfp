# WF41: Detector adequacy and two-signal admission

**Status:** proposal: no runner and no run yet. **Kind:** meta workflow. **Builds on:** [WF14](../wf14_immune_failure_classification/README.md).

**Goal:** Detectors whose adequacy is shown, not assumed.

## How it works

1. Admit a detector only with positive, negative, collision and metamorphic cases plus one representative per class
2. Two signals: pattern match and structural defect; pattern alone is diagnostic only
3. Bind a human decision to the receipt digest
4. Report effective diversity of the self panel

## The check

Host check: calibration record and two-signal table.

- `finite calibration completeness: D = A iff D = A on a class-representative set R (sharp)`

## Where it comes from

Sources: P030 §2, P003 §3, App A, P006 §7.

Lemmas checked exhaustively offline; no detector admitted; the six-arm effectiveness experiment is proposed (~299 opportunities needed for a <1% bound).

## Team

Pattern `red_team_pair`: coder ×1 (sonnet); adversary ×1 (fable); host_checker ×1 (none).

Boost: when a class is missing: DetectorInadequate (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf41) · [machine-readable entry](../dag/workflow_dag.json)
