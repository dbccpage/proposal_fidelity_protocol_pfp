# WF28: Eight-role audit dialogue

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF15](../wf15_adversary_tribunal/README.md).

**Goal:** A role sequence whose final packet the host accepts or refuses with a typed reason.

## How it works

1. Proposer, adversary, solver, overconfidence probe, stabilizer, schema auditor, truth repair, terminal arbiter in sequence
2. Each role sees only frozen earlier outputs
3. Host check decides; the arbiter cannot accept

## The check

Host check: strict l1 descent in the host.

- `strict descent of the l1 defect across the role sequence`

## Where it comes from

Sources: F challenges_findings_and_updates §2.

6 run folders; verdict counts are reference self-scores.

## Team

Pattern `tribunal`: coder ×1 (sonnet); adversary ×1 (fable); defender ×1 (opus); host_checker ×1 (none).

Boost: when arbiter and host disagree: host wins; record the disagreement (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf28) · [machine-readable entry](../dag/workflow_dag.json)
