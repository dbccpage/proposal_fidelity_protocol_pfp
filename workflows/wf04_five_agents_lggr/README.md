# WF4: Five agents + LGGR

**Status:** implemented and runnable. **Kind:** procedure extension. **Builds on:** [WF3](../wf03_mine_then_solve/README.md).

**Goal:** Five isolated answers whose local checks pass and which agree globally.

## Run it

Step-by-step guide: [Workflow-WF4 on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_wf4). Install: [Workflow-Running](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_running).

Offline, from the repository root after `pip install ".[workflows]"` (fixture replies: no model call, no cost):

```bash
python -m pfp.workflows.wf0004 prepare --task pfp/workflows/wf0004/examples/integer_sum.task.json --output runs/wf4-preview
```

Live (needs `OPENROUTER_API_KEY`; set `PFP_REASONING=off` for reasoning models):

```bash
python -m pfp.workflows.wf0004 run --task pfp/workflows/wf0004/examples/integer_sum.task.json --output runs/wf4-live --model deepseek/deepseek-v4.1-flash --budget-microusd 4999
python -m pfp.workflows.wf0004 replay --run runs/wf4-live
```

## Source files

- Code: [`pfp/workflows/wf0004/`](../../pfp/workflows/wf0004/) (also installed as the `pfp-wf4` command)
- Example task and fixture replies: [`pfp/workflows/wf0004/examples/`](../../pfp/workflows/wf0004/examples/)
- Tests: [`pfp/workflows/wf0004/tests/`](../../pfp/workflows/wf0004/tests/)
- Recorded evidence: [`../library/`](../library/README.md) (Oct 28 runs) and [`../library/evidence/live_20261106/`](../library/evidence/live_20261106/measurements.json) (Nov 6 runs)

**Latest live run (Nov 6, DeepSeek V4.1 Flash):** accepted, all five agents correct ($0.00059).

## How it works

1. One shared mining call
2. Five isolated solvers
3. Local checks per agent
4. One global compatibility check (local green, global red)

## The check

Host check: typed_envelope_and_independent_exact_sum.

- `global accept iff every local check passes and the local answers glue: a_1 = ... = a_5 = f(x)`

## Team

Pattern `parallel_isolated_then_global`: miner ×1 (run_o); coder ×5 (sonnet); host_checker ×1 (none).

Boost: when global disagreement: none on the base path (limit 0).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| handoff object | full trace vs summary vs answer only | — | theory | P028 §11 |
| consensus | majority vote vs component-level descent | — | code | P030 |
| trials for a zero-failure bound | n = 8 vs n = 299 | upper bound ~31% vs <1% | planning | P003 §7 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf4) · [machine-readable entry](../dag/workflow_dag.json)
