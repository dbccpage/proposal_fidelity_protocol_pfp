# WF31: Multi-agent tournament with held-out cross-validation

**Status:** proposal: no runner and no run yet. **Kind:** experiment design. **Builds on:** [WF1](../wf01_typed_answer/README.md).

**Goal:** A ranking that holds on held-out parts of each instance.

## How it works

1. Several proposers answer the same packet each round
2. Include a random-baseline negative control
3. Proposers see a training share of the instance; the host scores the held-out share
4. Rank per budget

## The check

Host check: exact rational referee.

- `exact referee: SO(4N), det = +1, defect <= tolerance; held-out score on the 30% the proposer never saw`

## Where it comes from

Sources: P022 §3-4.

Offline deterministic strategies and live-capable; the earlier rates were withdrawn. Held-out split: random baseline 0/16, others 16/16 (offline).

## Team

Pattern `sweep_with_shared_judge`: coder ×1 (sonnet); deep_researcher ×1 (run_o); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when none: tournaments do not escalate mid-round (limit 0).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| difficulty and noise | N=2 vs N=4 modes; noise budget 1/100 vs 1/50; four targets | random 0/16, others 16/16 | offline | P022 §4.2 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf31) · [machine-readable entry](../dag/workflow_dag.json)
