# WF18: Dossier replay campaign

**Status:** proposal: no runner and no run yet. **Kind:** harness gate. **Builds on:** [WF6](../wf06_dialect_sweep/README.md), [WF12](../wf12_mechanism_control_arms/README.md).

**Goal:** A replayable 5 x 5 + 5 campaign whose every grade reproduces from stored bytes.

## How it works

1. Fix five carriers and five representations (including emoji and glyph carrier encodings with an explicit legend)
2. Run the 5 x 5 baseline
3. Run five matched guidance trials
4. Replay from stored bytes and extract learning

## The check

Host check: family checker; replay must reproduce every grade.

- `frustrated spin triangle: no s in {+1,-1}^3 satisfies s_i s_j = -1 on all three edges (odd cycle)`
- `weighted cycle duality: a feasible potential exists iff no negative cycle exists`
- `design: 25 baseline cells + 5 matched cells, compared per carrier`

## Where it comes from

Sources: 0000188-0000191.

Each pilot crosses five finite carriers with five wrapped representations plus five matched guidance trials (30 capsules each); replay and learning runners exist in the source estate.

## Team

Pattern `sweep_with_shared_judge`: coder ×2 (sonnet); deep_researcher ×1 (opus); host_checker ×1 (none).

Boost: when replay grade differs: stop the campaign; investigate custody before any new call (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf18) · [machine-readable entry](../dag/workflow_dag.json)
