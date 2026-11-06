# WF45: Finite terminal selector and plenitude test

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF7](../wf07_typed_refusal/README.md).

**Goal:** Never report a unique answer the evidence cannot separate.

## How it works

1. Check every candidate against evidence with tolerances
2. Return Accepted, Underdetermined, Refuted or Refused for the family
3. Add indistinguishable candidates and check the survivor count rises
4. Deleting competitors is not evidence

## The check

Host check: deterministic verifier and survivor set.

- `unique acceptance is only relative to the declared family`

## Where it comes from

Sources: P003(representation) §2-5.

Code and tests; stress test with 100 candidates.

## Team

Pattern `solo`: coder ×1 (sonnet); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when none: typed verdict (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf45) · [machine-readable entry](../dag/workflow_dag.json)
