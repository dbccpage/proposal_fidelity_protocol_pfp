# WF24: Pinned-token operational scratchpad

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF2](../wf02_full_slots/README.md).

**Goal:** An accepted answer whose scratchpad follows the pinned grammar.

## How it works

1. Pin canonical coordinate tokens in the reply grammar
2. Require an operational scratchpad of the exact computation (e.g. path products)
3. Check the final answer with dual independent checkers

## The check

Host check: dual holonomy checkers that must agree.

- `holonomy along a loop: g_acc <- g_acc * U(e) for each edge e, compared with the identity`

## Where it comes from

Sources: F symbol_game_challenge_and_demos_findings §3.4, F challenges_findings_and_updates §8.2 (C017).

Live, 5 cases: 0/5 became 3/5 on a 70B model and on a reasoning model. Historical; the findings carry errata.

## Team

Pattern `solo`: coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when checker rejects: run_o repairs the scratchpad from the residual (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf24) · [machine-readable entry](../dag/workflow_dag.json)
