# WF32: Claim-scoped receipt

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF1](../wf01_typed_answer/README.md), [WF2](../wf02_full_slots/README.md).

**Goal:** A receipt that says exactly which claims were checked.

## How it works

1. Record the exact set of admitted claims J_checked
2. Check each claim with its own checker
3. A correct witness admits nothing around it (prose, universals, quotes)
4. Quotes need source bytes and a span

## The check

Host check: per-claim independent checkers.

- `admitted(J) = {j : C_j(witness_j) = accept}; everything else stays unadmitted`

## Where it comes from

Sources: P023 §1-4.

Proof and finite replay; no model runs.

## Team

Pattern `solo`: coder ×1 (sonnet); host_checker ×1 (none).

Boost: when unchecked claim found: drop it from the receipt (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf32) · [machine-readable entry](../dag/workflow_dag.json)
