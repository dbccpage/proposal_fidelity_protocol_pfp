# WF10: Local-to-global obstruction certificate

**Status:** proposal: no runner and no run yet. **Kind:** task preset. **Builds on:** [WF4](../wf04_five_agents_lggr/README.md), [WF9](../wf09_bounded_check_and_repair/README.md).

**Goal:** A checked gluing witness or a checked obstruction class for the declared cover.

## How it works

1. Declare the cover, cochains and restriction maps
2. Agents certify local sections on each patch
3. Host computes the global obstruction class
4. Accept a gluing witness or an obstruction certificate, never a prose claim

## The check

Host check: exact cochain / homology checker.

- `H^1 = ker(delta_1) / im(delta_0); a class [c] != 0 means local green, global red`
- `three-patch observer visibility: each observer sees zero on its edges, yet sum_alpha J^alpha(s) > 0 for the glued section`
- `Hodge: c = delta alpha + delta^* beta + h with h harmonic (exact rational arithmetic)`
- `integer lift: an obstruction in H^1(X; Z) can survive the map to rational coefficients only if it is non-torsion`

## Where it comes from

Sources: 0000029, 0000039-0000045, 0000051, 0000056-0000064, 0000083.

Pilot 51 records live runs on the three-patch observer-visibility obstruction; 39-45 are offline exact checkers (angle defects, Hodge, clique homology, triangle fans); 56-64 are planned capsules.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/pilot_0000051/`](pilots/pilot_0000051/) — pilot_0000051 — Projection Obstruction & Observer Visibility (Rung 4)

## Team

Pattern `parallel_isolated_then_global`: coder ×n_patches (sonnet); deep_researcher ×1 (run_o); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when local checks pass but the global check fails: run_o receives the coboundary residual and proposes either a repair (WF9) or an obstruction certificate (limit 1).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| cover and complex | add/drop 2-cells; filled vs unfilled triangle; theta graph; hexagon | — | code | P004(DSL); P018; P003(rep) |
| local tolerance | tau 1/10 vs 1/5 on a hexagon | holonomy 3/5 vs bound 6/5 | code | P003(rep) Cor 3.3 |
| extractor carrier | claim, citation, tool-trace, proof-obligation or reasoning-step graph | — | code | P033 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf10) · [machine-readable entry](../dag/workflow_dag.json)
