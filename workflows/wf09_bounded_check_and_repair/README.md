# WF9: Bounded check-and-repair

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF2](../wf02_full_slots/README.md).

**Goal:** An accepted reply within L attempts, or a recorded stop at the limit.

## How it works

1. Check the reply
2. On rejection return only the typed residual (never the expected answer)
3. Allow at most L repair attempts
4. Stop at the first accepted reply or at the limit

## The check

Host check: repair checker (coboundary or parity).

- `XOR cycle: a consistent assignment exists iff the cycle sum of edge labels is 0 mod 2`
- `minimal repair: argmin |Delta| subject to c + Delta in im(delta_0) for the edge cochain c`
- `termination: attempts <= L, and each attempt is charged`

## Where it comes from

Sources: 0000002, 0000006, 0000010, 0000026, 0000049, 0000055, 0000062, 0000096.

Pilot 49 is a deterministic mock (41 then 42, two mock calls, zero provider cost); pilot 26 retains all three least-cost repairs of an odd XOR cycle; graph-repair rungs use PFP-03.

## Team

Pattern `proposer_with_residual_feedback`: coder ×1 (sonnet); host_checker ×1 (none).

Boost: when two rejections in a row: final attempt goes to run_o with the full residual history (limit 1).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| prompt condition | baseline, partially masked, scratchpad, hinted | baseline and masked failed; hinted passed by copying | live | P008 §10.1; F §4.1 |
| turn cap and loop trigger | 12 turns; loop after 3 repeats; 5 dialogue rounds | — | live | F §4.1, §2.3 |
| fuel | 1 vs 2 attempts | UNKNOWN vs CHECKED | offline | P000 §8 |
| cut mode | strict descent vs non-increase | strict descent alone does not terminate over Q | offline | P001 §5; P005 §4 |
| accept policy | lexicographic (Phi, Gamma, X) vs Phi only; ratio ceiling; tolerance | — | code | P026 §3-4; P018 |
| negative control | deletion edit that makes the ratio test pass vacuously | passes: a known gap | code | P018 CE 3.1 |
| retry kind | blind retry vs packet-changing retry | blind retry saturates as (1-p)^n p | theory | P028 §10.3 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf9) · [machine-readable entry](../dag/workflow_dag.json)
