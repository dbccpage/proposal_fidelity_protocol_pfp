# WF40: Restart boundary after exhausted repair

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF9](../wf09_bounded_check_and_repair/README.md), [WF20](../wf20_derivation_loop_with_lift_grants/README.md).

**Goal:** End every exhausted repair with a lawful typed outcome.

## How it works

1. When bounded repair ends with a positive residual, choose exactly one of: typed refusal, lift request, restart seed carrying the residual
2. A lift needs a preservation witness
3. A changed claim set is a new problem, not a repair

## The check

Host check: trichotomy and lift-witness check.

- `cochain trichotomy: exact / unclosed / closed non-exact; lift authorised only with Delta > 0`

## Where it comes from

Sources: P029(boundary) §2.4, §6, P004 §6, P005 §2-5.

Code and tests; offline scripted demos only.

## Team

Pattern `proposer_with_residual_feedback`: coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when none: terminal by design (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf40) · [machine-readable entry](../dag/workflow_dag.json)
