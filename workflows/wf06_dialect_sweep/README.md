# WF6: Dialect sweep

**Status:** proposal: no runner and no run yet. **Kind:** experiment design. **Builds on:** [WF5](../wf05_checked_rewrite/README.md).

**Goal:** Measure, item by item, which presentation of the same task the host accepts more often, without changing the task.

## How it works

1. Freeze one seed and its host answer
2. Compile P* and k checked rewrites (dialects) of seed and P*
3. Dispatch each capsule once under the same model and parameters
4. Grade every reply with the same host checker
5. Report acceptance per dialect, item by item

## The check

Host check: family checker (e.g. exact linear algebra, graph facts, graph repair, typed refusal).

- `dialect family {rho_k}: decode(rho_k(s)) = q(s) for every k (preservation precondition)`
- `acceptance A_k = (1/N) sum_i 1[check(r_ik)] compared pairwise on the same items`
- `exact rational structure delta: Net = Delta_created - Delta_removed`

## Where it comes from

Sources: 0000000-0000019.

Pilots 0-10 retain 53-83 test capsules each (seed, P*, ten seed rewrites, ten P* rewrites); a few capsules hold manual live replies, most are offline controls.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/pilot_0000000/`](pilots/pilot_0000000/) — pilot_0000000 — Linear Algebra (Rung 1)
- [`pilots/pilot_0000001/`](pilots/pilot_0000001/) — pilot_0000001
- [`pilots/pilot_0000002/`](pilots/pilot_0000002/) — pilot_0000002
- [`pilots/pilot_0000004/`](pilots/pilot_0000004/) — pilot_0000004

## Team

Pattern `sweep_with_shared_judge`: coder ×1 (sonnet); coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when a dialect fails preservation: run_o proposes a corrected rewrite from the preservation residual; recheck before any dispatch (limit 1).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| channel | free, null, carrier filter, grammar mask | 0/8 for all on a 0.5B model | live | P027 T1 |
| gauge and relabel twins | 8-16 invariance controls per challenge | — | offline | F c011, c051 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf6) · [machine-readable entry](../dag/workflow_dag.json)
