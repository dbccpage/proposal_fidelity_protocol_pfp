# WF38: Diagnostic-trace proposal selection

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF9](../wf09_bounded_check_and_repair/README.md).

**Goal:** Select repairs only by host-recomputed diagnostics.

## How it works

1. The model proposes candidates; it never reports its own score
2. The host recomputes Phi, Gamma and other channels
3. Filter by strict lexicographic decrease and a ratio ceiling
4. Rank with fixed weights; ties by name; every observer must pass in the multi-observer form

## The check

Host check: exact rational diagnostics.

- `primal-dual witness: B^T phi = 0, ||phi||_inf <= 1, phi . c = ||h||_1; Gamma <= ||D|| Phi`

## Where it comes from

Sources: P026 §2-4, P018 §2-4, P019 §2-5.

Host checks have code and tests; no model runs.

## Team

Pattern `proposer_with_residual_feedback`: coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when no candidate passes: typed refusal (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf38) · [machine-readable entry](../dag/workflow_dag.json)
