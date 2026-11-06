# WF12: Mechanism-control arms

**Status:** proposal: no runner and no run yet. **Kind:** experiment design. **Builds on:** [WF6](../wf06_dialect_sweep/README.md), [WF3](../wf03_mine_then_solve/README.md).

**Goal:** An arm comparison on a fixed carrier whose only difference is the mechanism note.

## How it works

1. Hold the carrier fixed; vary only the mechanism note
2. Run baseline, typed-witness and mechanism arms on the same items
3. Grade with one registered checker
4. Compare arms item by item

## The check

Host check: integer rank-difference certificate (to be registered).

- `rank difference: r_i - r_j recovered from a gauge-fixed assignment; gauge freedom r -> r + c leaves differences unchanged`
- `paired effect: d_i = 1[check(arm_B, i)] - 1[check(arm_A, i)]`

## Where it comes from

Sources: 0000052.

Ten planned capsules (c001-c010) on one integer rank-difference carrier with three distractor spans; no model was called and the checker id is not registered.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/c001_attention_distractor_mask/`](pilots/c001_attention_distractor_mask/) — masking attention to distractor keys, with a McNemar comparison of arms (needs a local model with attention hooks)
- [`pilots/c005_hosted_decode_controls/`](pilots/c005_hosted_decode_controls/) — a bake-off of hosted decoding controls (budgets, scratchpads, hybrids) on checkable cases
- [`pilots/consistency_teaching/`](pilots/consistency_teaching/) — rank-difference tasks, clean or poisoned, with direct and chain-of-thought prompts
- [`pilots/planned/`](pilots/planned/) — the C006 host scratch-space protocol (the other planned write-ups were removed)

## Team

Pattern `sweep_with_shared_judge`: coder ×1 (sonnet); deep_researcher ×1 (opus); adversary ×1 (fable); host_checker ×1 (none).

Boost: when leak found: rebuild the carrier; discard affected runs (limit 0).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| validity gate | baseline, null-hook gate, distractor mask, string delete (0.5B) | null hook matched baseline tokens 100% | live | F §8.1 |
| C017 prompt arms | arms 1, 2, 5, 6 | 0/5, 0/5, 3/5, 3/5 (4/5 with decimation) | live | P010 §3 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf12) · [machine-readable entry](../dag/workflow_dag.json)
