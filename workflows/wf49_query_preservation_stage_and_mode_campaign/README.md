# WF49: Query-preservation stage and mode campaign

**Status:** proposal: no runner and no run yet. **Kind:** experiment design. **Builds on:** [WF8](../wf08_staged_sealed_packets/README.md), [WF22](../wf22_certified_cost_ladder/README.md).

**Goal:** Measure which stages and modes preserve the query at scale.

## How it works

1. Run declared stages and mode contracts over task families
2. Independent oracle per family
3. Stop a lane on any safety regression

## The check

Host check: per-family oracles.

- `a stage passes only if the decoded query is unchanged`

## Where it comes from

Sources: P011 §3-5.

Proposed: zero campaign cases executed; 17 live records from earlier rounds.

## Team

Pattern `sweep_with_shared_judge`: coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when safety regression: stop the lane (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf49) · [machine-readable entry](../dag/workflow_dag.json)
