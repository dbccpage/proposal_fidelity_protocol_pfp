# WF14: Immune failure classification

**Status:** proposal: no runner and no run yet. **Kind:** meta workflow. **Builds on:** [WF7](../wf07_typed_refusal/README.md), [WF12](../wf12_mechanism_control_arms/README.md).

**Goal:** Detectors that catch the recorded failures and never fire on the sealed self panel.

## How it works

1. Seal a self panel of known-good outputs
2. Propose candidate detectors (antibodies) from observed failures
3. Reject any detector that fires on the self panel
4. Admit a detector only with two signals: a failure match and a host check

## The check

Host check: detector admission check over the sealed panel.

- `negative selection: keep d iff for all s in Self, match(d, s) < theta`
- `two-signal gate: admit iff signal_1 (pattern) and signal_2 (host evidence)`
- `self-tolerance = 1 - false positives on Self / |Self|`

## Where it comes from

Sources: 0000125-0000134.

Ten planned capsules (C081-C090), e.g. negative selection against a sealed self panel; none dispatched.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/pilot035/`](pilots/pilot035/) — Tao cross-ratio task packet with an immune fence; its antibody admissions are in eis/antibodies/admissions

## Team

Pattern `red_team_pair`: coder ×1 (sonnet); adversary ×1 (fable); host_checker ×1 (none).

Boost: when a detector fires on Self: discard it; opus may propose one narrower detector (limit 1).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| calibration set | 4 cases vs one per class; omit a class | omitting a class breaks adequacy (sharp) | code | P030 §2.4 |
| toxicity threshold and decay | 1/5 threshold; decay tau = 5 | policy arithmetic, not a rate | offline | P006 §8 |
| self-panel diversity | 1000 rows, 40 distinct | effective n = 40 | offline | P003; P006 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf14) · [machine-readable entry](../dag/workflow_dag.json)
