# WF25: Hierarchical decimation

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF24](../wf24_pinned_token_operational_scratchpad/README.md).

**Goal:** Fit large lattices inside the token limit without losing exactness.

## How it works

1. Certify trivially flat sub-blocks at zero tokens
2. Evaluate only the non-contractible loops
3. Check that the remaining holonomies commute
4. Optional second pass aggregates macro-blocks

## The check

Host check: dual checkers.

- `flat blocks contribute the identity; global flatness reduces to the cycle holonomies of the quotient`

## Where it comes from

Sources: F symbol_game_challenge_and_demos_findings §3.6, §15, F challenges_findings_and_updates §12.

Live on one torus case: tokens fell from over 8,000 to 2,810 and overall 4/5 passed. Two-pass quad-tree aggregation is proposed, not run.

## Team

Pattern `solo`: coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when token ceiling reached: split into macro-blocks and rerun once (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf25) · [machine-readable entry](../dag/workflow_dag.json)
