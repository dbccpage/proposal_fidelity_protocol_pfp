# WF46: Boundary sufficiency and gluing diagnostic

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF4](../wf04_five_agents_lggr/README.md).

**Goal:** Measure how often local passes hide a global failure.

## How it works

1. Check that the handoff object between isolated agents keeps everything the global evaluator needs
2. Report NGD over runs; undefined when no run is locally accepted
3. Report completed share and backlog

## The check

Host check: global evaluator on the glued trace.

- `NGD = Pr(global fail | all locals pass)`

## Where it comes from

Sources: P028(finite authority) §11, P005(authority gap) §3.

Theory plus finite Lean split; NGD code not yet run on WF4 data.

## Team

Pattern `parallel_isolated_then_global`: coder ×1 (sonnet); deep_researcher ×1 (opus); host_checker ×1 (none).

Boost: when none: diagnostic only (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf46) · [machine-readable entry](../dag/workflow_dag.json)
