# WF37: Evidence-bound harness evolution

**Status:** proposal: no runner and no run yet. **Kind:** meta workflow. **Builds on:** [WF19](../wf19_failure_derived_rule_transfer/README.md), [WF22](../wf22_certified_cost_ladder/README.md).

**Goal:** A harness change that wins on fresh confirmation and transfers.

## How it works

1. An outer model rewrites a small harness (prompt, workflow, search and context policy)
2. UCB1 plus softmax search over strategies; scoped failure memory
3. Public and private grading split
4. Fresh confirmation before replacing the incumbent
5. Untouched transfer and ablation panels

## The check

Host check: frozen checkers, isolation, reserved budget.

- `paired bootstrap, exact sign test, Holm correction over transfer and ablation contrasts`

## Where it comes from

Sources: P029 §2-8, P004-P006 extensions.

Implemented offline; NOT_RUN live ($40 plan).

## Team

Pattern `research_cell`: coder ×1 (sonnet); deep_researcher ×1 (run_o); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when no confirmed gain: retain incumbent (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf37) · [machine-readable entry](../dag/workflow_dag.json)
