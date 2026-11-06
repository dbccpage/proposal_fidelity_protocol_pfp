# WF26: Multi-round antibody dialogue

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF9](../wf09_bounded_check_and_repair/README.md), [WF14](../wf14_immune_failure_classification/README.md).

**Goal:** Converge to an accepted answer as antibodies accumulate, without leaking the answer.

## How it works

1. Run up to R dialogue rounds on one task
2. Turn each recorded hallucination into a typed negative-constraint antibody
3. Carry accumulated antibodies into the next round
4. Accept only on the exact oracle

## The check

Host check: exact oracle.

- `antibody set A_{t+1} = A_t ∪ {typed constraint from failure_t}; stop when check passes or t = R`

## Where it comes from

Sources: F symbol_game_challenge_and_demos_findings §2.

Live: 5 models, 22 calls, $0.015; two models reached 4/4 by round 2-3. The prompts leaked the answer (erratum), so this is plumbing evidence only.

## Team

Pattern `proposer_with_residual_feedback`: coder ×1 (sonnet); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when two rounds without progress: run_o rewrites the antibody set once (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf26) · [machine-readable entry](../dag/workflow_dag.json)
