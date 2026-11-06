# WF11: Dual-certificate synthesis

**Status:** proposal: no runner and no run yet. **Kind:** task preset. **Builds on:** [WF3](../wf03_mine_then_solve/README.md), [WF9](../wf09_bounded_check_and_repair/README.md).

**Goal:** A frozen solver whose every output carries a certificate the judge accepts on hidden cases.

## How it works

1. Publish the participant packet; keep the judge packet sealed
2. Team writes a solver that emits certificates, not just answers
3. Commit H(salt || solver) before hidden cases are revealed
4. Judge checks each certificate with exact dot products

## The check

Host check: exact certificate checker plus an independent second checker.

- `LP optimality: x >= 0, A x <= b, y >= 0, A^T y >= c, c.x = b.y (weak duality closes the gap)`
- `infeasibility (Farkas): y >= 0, A^T y >= 0, b.y < 0`
- `max-flow value = min-cut capacity; assignment potentials u_i + v_j <= c_ij with equality on the matching`
- `Bareiss fraction-free elimination keeps every intermediate an exact integer`

## Where it comes from

Sources: 0000027, 0000053, 0000054, 0000095, 0000115-0000124, 0000171, 0000180, c051, c052, c053, c054, c055, c059.

Challenge folders c051-c055 and c059 hold participant packets, judge packets, reference solvers and commit-reveal scripts; dossier LP pilots are planned capsules.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/c051_exact_lp_solver_with_duals/`](pilots/c051_exact_lp_solver_with_duals/) — pilot material
- [`pilots/c052_maxflow_mincut_certificates/`](pilots/c052_maxflow_mincut_certificates/) — pilot material
- [`pilots/c053_bareiss_fraction_free_matrix_inversion/`](pilots/c053_bareiss_fraction_free_matrix_inversion/) — pilot material
- [`pilots/c054_exact_linear_systems/`](pilots/c054_exact_linear_systems/) — pilot material
- [`pilots/c055_assignment_with_potentials/`](pilots/c055_assignment_with_potentials/) — pilot material
- [`pilots/c059_sql_null_total_query_synthesis/`](pilots/c059_sql_null_total_query_synthesis/) — pilot material

## Team

Pattern `research_cell`: coder ×2 (sonnet); deep_researcher ×1 (opus); adversary ×1 (fable); host_checker ×1 (none).

Boost: when a certificate is rejected on public cases: opus reads the rejected certificate and the checker message, proposes one patch; sonnet applies it (limit 2).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| norm family | p=1 simplex, p=2 Hodge, p=inf Chebyshev, interior p, Schatten-1 | only p in {1, 2, inf} certified exactly | code | P002(l1); P003(l1) |
| mutation suites | C011, C012, C022, C031 | 150-188 mutants, all rejected by both checkers | offline | F §9.1; P021 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf11) · [machine-readable entry](../dag/workflow_dag.json)
