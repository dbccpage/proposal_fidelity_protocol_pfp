# WF43: Gate-honesty and answer-free leak audit

**Status:** proposal: no runner and no run yet. **Kind:** harness gate. **Builds on:** [WF23](../wf23_judge_packet_custody_audit/README.md).

**Goal:** Show no answer-free reply can pass.

## How it works

1. Ask which operation produced each verdict
2. Probe with input replacement, keyword adjudication, phantom evidence and templated receipts
3. Replay constant refusals, empty objects and constant verdicts against both checkers

## The check

Host check: replay against the audited checkers.

- `a gate is honest only if no answer-free reply passes and every verdict traces to a check`

## Where it comes from

Sources: P009 §4, App A, P010 §4.1-4.2.

Executed offline: a bare refusal passed 10/10 on two challenges before identifiers were neutralised.

## Team

Pattern `red_team_pair`: coder ×1 (sonnet); adversary ×1 (fable); host_checker ×1 (none).

Boost: when leak found: block until resealed (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf43) · [machine-readable entry](../dag/workflow_dag.json)
