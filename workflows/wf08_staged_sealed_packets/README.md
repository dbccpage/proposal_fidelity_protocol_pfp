# WF8: Staged sealed packets

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF2](../wf02_full_slots/README.md), [WF5](../wf05_checked_rewrite/README.md).

**Goal:** Each stage produces a sealed, typed output; the final answer checks.

## How it works

1. Choose a mode contract and wire encoding
2. Split the task into k declared stages
3. Seal each stage output (hash chain) before the next stage reads it
4. Check every stage receipt and the final answer

## The check

Host check: per-stage receipts plus the family checker.

- `composition F = f_k o ... o f_1 with typed interfaces between stages`
- `seal chain h_0 = H(seed), h_i = H(h_{i-1} || payload_i); any edit breaks every later h_j`

## Where it comes from

Sources: 0000001-0000025, 0000033.

Mode trials mode_01..mode_20 and wire encodings (EBNF wire, S(n) wire, boundary packets, glyph alphabets); pilot 20 runs two local stages with zero provider calls; pilot 33 documents a two-pass loop the old runner did not implement.

## Team

Pattern `relay`: coder ×k (sonnet); deep_researcher ×1 (opus); host_checker ×1 (none).

Boost: when a stage receipt fails: rerun that stage once with opus and the receipt residual; earlier seals are reused (limit 1).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| stage interface | diagnostic-equal vs endpoint-state-equal | — | code | P026 §5, §8 |
| stage count and slots | 1-turn vs 2-turn; 3 vs 4 slots; guard retry 2 | gpt-4o-mini: 5/8, 3/8, 5/8; guarded 5 admitted, 3 abstained | live | P027 T2 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf8) · [machine-readable entry](../dag/workflow_dag.json)
