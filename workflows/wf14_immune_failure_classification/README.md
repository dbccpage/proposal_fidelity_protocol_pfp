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

- [`pilots/pilot_0000125/`](pilots/pilot_0000125/) — pilot_0000125 — C081 Thymus Negative Selection Against a Sealed Self Panel
- [`pilots/pilot_0000126/`](pilots/pilot_0000126/) — pilot_0000126 — C082 Two-Signal Danger Gate vs Prompt Injection
- [`pilots/pilot_0000127/`](pilots/pilot_0000127/) — pilot_0000127 — C083 Clonal Affinity Maturation under a Budget
- [`pilots/pilot_0000128/`](pilots/pilot_0000128/) — pilot_0000128 — C084 Treg Peripheral Tolerance for Overactive Detectors
- [`pilots/pilot_0000129/`](pilots/pilot_0000129/) — pilot_0000129 — C085 Kinetic Proofreading Inside the Retraction Loop
- [`pilots/pilot_0000130/`](pilots/pilot_0000130/) — pilot_0000130 — C086 Allosteric Quorum Across Heterogeneous Small Models
- [`pilots/pilot_0000131/`](pilots/pilot_0000131/) — pilot_0000131 — C087 MHC Partial-View Detection of Local-Green Global-Red Errors
- [`pilots/pilot_0000132/`](pilots/pilot_0000132/) — pilot_0000132 — C088 Complement Cascade with Regulators
- [`pilots/pilot_0000133/`](pilots/pilot_0000133/) — pilot_0000133 — C089 Immune Memory: Second Exposure at Half the Cost
- [`pilots/pilot_0000134/`](pilots/pilot_0000134/) — pilot_0000134 — C090 Antimorphism Farm as a Judge-Suite Generator

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
