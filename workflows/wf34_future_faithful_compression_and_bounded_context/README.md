# WF34: Future-faithful compression and bounded context

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF8](../wf08_staged_sealed_packets/README.md), [WF22](../wf22_certified_cost_ladder/README.md).

**Goal:** Smaller context with no lost future operation.

## How it works

1. Compress state only if enablement, cost, successors and terminal labels all survive
2. Stage boundaries require equal states, not equal diagnostics
3. Bounded context keeps root, champion, two recent attempts and evidence references
4. Compare with a full-history arm at the same ceiling

## The check

Host check: endpoint-state equality and reference retention.

- `coarsest stable refinement; states equal under every finite continuation`

## Where it comes from

Sources: P026 §1-6, §8, P029 §4.

Proof and replay; the bounded-context harness arm is implemented and NOT_RUN.

## Team

Pattern `relay`: coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when dropped reference: refuse (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf34) · [machine-readable entry](../dag/workflow_dag.json)
