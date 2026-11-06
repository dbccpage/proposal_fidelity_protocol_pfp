# WF48: Commit-reveal with a hostile mutation gate

**Status:** proposal: no runner and no run yet. **Kind:** harness gate. **Builds on:** [WF11](../wf11_dual_certificate_synthesis/README.md), [WF23](../wf23_judge_packet_custody_audit/README.md).

**Goal:** Scores that could not have been tuned to the hidden cases.

## How it works

1. Commit the judge manifest
2. Freeze the solver and commit its hash
3. Reveal hidden cases (base, relabel/gauge controls, poison bait) and score
4. Kill a hostile certificate-mutation suite with both checkers

## The check

Host check: dual checkers plus mutation suite.

- `commit H(salt || artifact) before reveal; both checkers must reject every mutant`

## Where it comes from

Sources: F symbol_game_challenge_and_demos_findings §7-14, F challenges_findings_and_updates §9.3-9.5, F c043-c059 template.

All C043-C060 reference solvers passed 64/64 and killed 48/48 mutants; these are reference self-scores, not model results.

## Team

Pattern `red_team_pair`: coder ×1 (sonnet); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when mutant survives: block the checker (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf48) · [machine-readable entry](../dag/workflow_dag.json)
