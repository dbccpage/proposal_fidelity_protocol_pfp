# WF27: Hinted retraction with a stationary-loop detector

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF9](../wf09_bounded_check_and_repair/README.md).

**Goal:** Repair to zero residual within the turn cap, with unassisted and assisted arms kept separate.

## How it works

1. Inject the residual vector and the non-zero cell ids each turn
2. Detect a stationary loop after 3 repeats
3. Force a structural lift or reframe
4. Stop at the turn cap

## The check

Host check: host residual gate (Phi1 = 0).

- `residual r_t = d c_t; stationary if r_t = r_{t-3}; path-integrated retry uses B_T^{-1}, not edge-local B_T`

## Where it comes from

Sources: F challenges_findings_and_updates §4, §10.1, P008 §10, P027 §5.9.

Live, 28 trials on 7-8B models: baseline 0%, hinted 100% (the hint was the full repair, so only copying is shown).

## Team

Pattern `proposer_with_residual_feedback`: coder ×1 (sonnet); host_checker ×1 (none).

Boost: when stationary loop: forced lift or reframe (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf27) · [machine-readable entry](../dag/workflow_dag.json)
