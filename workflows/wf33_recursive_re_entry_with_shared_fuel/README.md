# WF33: Recursive re-entry with shared fuel

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF9](../wf09_bounded_check_and_repair/README.md), [WF20](../wf20_derivation_loop_with_lift_grants/README.md).

**Goal:** Chains of re-entry that never reset their budget or lose their parent.

## How it works

1. An output becomes the next proposal
2. Check a backward solution map and a forward coverage map per edge
3. Bind the parent receipt
4. Charge every prefix against one original budget

## The check

Host check: per-edge maps plus parent binding.

- `at most floor(B / delta) operations under budget B; stale parent, changed task or fuel reset is refused`

## Where it comes from

Sources: P024 §1-5.

Replay only.

## Team

Pattern `relay`: coder ×1 (sonnet); deep_researcher ×1 (opus); host_checker ×1 (none).

Boost: when stale parent: refuse (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf33) · [machine-readable entry](../dag/workflow_dag.json)
