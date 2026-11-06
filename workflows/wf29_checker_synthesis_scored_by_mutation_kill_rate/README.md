# WF29: Checker synthesis scored by mutation kill rate

**Status:** proposal: no runner and no run yet. **Kind:** task preset. **Builds on:** [WF11](../wf11_dual_certificate_synthesis/README.md).

**Goal:** A checker that kills every mutant and accepts every valid case.

## How it works

1. The model writes a checker for a declared certificate
2. Run it against valid cases and a hostile mutation suite
3. Score by kills and by false rejections

## The check

Host check: mutation suite plus valid-case panel.

- `kill rate = killed / mutants; soundness requires zero false rejections on valid cases`

## Where it comes from

Sources: F challenges_findings_and_updates §11 (C060).

Live: reasoning model 10/10, 70B 5/10, 8B 0/10.

## Team

Pattern `red_team_pair`: coder ×1 (sonnet); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when a mutant survives: run_o patches the checker once (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf29) · [machine-readable entry](../dag/workflow_dag.json)
