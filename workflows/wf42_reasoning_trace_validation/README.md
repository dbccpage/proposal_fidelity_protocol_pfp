# WF42: Reasoning-trace validation

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF10](../wf10_local_to_global_obstruction_certificate/README.md), [WF21](../wf21_structural_prompt_rewriting/README.md).

**Goal:** Validate the structure of a reasoning trace, not its fluency.

## How it works

1. A fixed extractor turns the model's text into a claim, citation or tool graph
2. The host computes the obstruction and a dual witness
3. Emit a typed status
4. Run an adversarial battery against the extractor

## The check

Host check: rational LP primal-dual check.

- `Exact only describes the extractor's image; a three-claim cycle with Phi = 1 and phi = (1,1,1) is the worked obstruction`

## Where it comes from

Sources: P033 §2-8.

Code and tests; the extractor adequacy battery is specified, not certified.

## Team

Pattern `red_team_pair`: coder ×1 (sonnet); adversary ×1 (run_f); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when extractor collapses: CarrierFailure (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf42) · [machine-readable entry](../dag/workflow_dag.json)
