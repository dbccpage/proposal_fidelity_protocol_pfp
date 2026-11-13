# WF35: Proposal-channel comparison

**Status:** proposal: no runner and no run yet. **Kind:** experiment design. **Builds on:** [WF6](../wf06_dialect_sweep/README.md), [WF12](../wf12_mechanism_control_arms/README.md).

**Goal:** Find which channel changes acceptance on the same items.

## How it works

1. Fix the host check
2. Vary only the channel: prompt, glyph code, logit mask, grammar mask, typed tree, attention or activation bias
3. Compare per item

## The check

Host check: fixed exact oracle.

- `channel invariance: the accept set depends on the reply, never on the channel that produced it`

## Where it comes from

Sources: P027 §1-3, §5.1-5.2.

Offline receipts; attention, activation and steering channels were not exercised on live models. Qwen-0.5B: 0/8 exact on every channel; the null channel matched free decoding token for token.

## Team

Pattern `sweep_with_shared_judge`: coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when none: channels are arms, not boosts (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf35) · [machine-readable entry](../dag/workflow_dag.json)
