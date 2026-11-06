# WF22: Certified cost ladder

**Status:** proposal: no runner and no run yet. **Kind:** experiment design. **Builds on:** [WF6](../wf06_dialect_sweep/README.md), [WF8](../wf08_staged_sealed_packets/README.md), [WF18](../wf18_dossier_replay_campaign/README.md).

**Goal:** Decide each pre-registered hypothesis on this bank, at this rung, with this gate.

## How it works

1. Pre-register items, arms and hypotheses
2. Every arm ends with one canonical ANSWER line or ANSWER: UNRESOLVED <code>
3. Run every item under every arm
4. Evaluate hypotheses item by item with refutation criteria

## The check

Host check: family certificate checkers; hypothesis evaluator.

- `cost to certified correct: C_arm = total spend / #accepted`
- `paired test on discordant items (McNemar-style): b = #(A ok, B fail), c = #(A fail, B ok)`
- `bluff rate per arm, as in WF7`

## Where it comes from

Sources: certified_ladder.

Pre-registered design with fourteen falsifiable hypotheses (H0-H13) and pinned baseline models; arms vary stage count 1-8, rewrites, model tier and antibodies.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/certified_ladder/`](pilots/certified_ladder/) — pilot material
- [`pilots/evidence/`](pilots/evidence/) — recorded campaign evidence (raw replies, ledgers, receipts)

## Team

Pattern `sweep_with_shared_judge`: coder ×2 (sonnet); deep_researcher ×1 (opus); adversary ×1 (fable); host_checker ×1 (none).

Boost: when none: a ladder run never escalates mid-campaign: boosted arms are separate pre-registered arms (limit 0).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| cross-architecture transfer | 70B vs a reasoning model on C017 | same pass rate and failure modes | live | F §3.5 |
| context policy | compressed vs full history at the same ceiling | — | not run | P026; P029 |
| arrival vs completion rate | cohort vs window counting | — | code | P005(gap) §3.3 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf22) · [machine-readable entry](../dag/workflow_dag.json)
