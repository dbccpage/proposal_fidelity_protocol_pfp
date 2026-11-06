# WF2: Full slots

**Status:** implemented and runnable. **Kind:** procedure extension. **Builds on:** [WF1](../wf01_typed_answer/README.md).

**Goal:** A complete slot record plus an accepted answer.

## Run it

Step-by-step guide: [Workflow-WF2 on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-WF2). Install: [Workflow-Running](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-Running).

Offline, from the repository root after `pip install ".[workflows]"` (fixture replies: no model call, no cost):

```bash
python -m pfp.workflows.wf0002 prepare pfp/workflows/wf0002/examples/integer_sum.task.json --output runs/wf2
python -m pfp.workflows.wf0002 check runs/wf2 pfp/workflows/wf0002/examples/integer_sum.reply.fixture.json --fixture
python -m pfp.workflows.wf0002 replay runs/wf2
```

Live (needs `OPENROUTER_API_KEY`; set `PFP_REASONING=off` for reasoning models):

```bash
python -m pfp.workflows.wf0002 run pfp/workflows/wf0002/examples/integer_sum.task.json --output runs/wf2-live --model deepseek/deepseek-v4.1-flash --max-output-tokens 3000 --max-estimated-cost-microusd 4999
python -m pfp.workflows.wf0002 replay runs/wf2-live
```

## Source files

- Code: [`pfp/workflows/wf0002/`](../../pfp/workflows/wf0002/) (also installed as the `pfp-wf2` command)
- Example task and fixture replies: [`pfp/workflows/wf0002/examples/`](../../pfp/workflows/wf0002/examples/)
- Tests: [`pfp/workflows/wf0002/tests/`](../../pfp/workflows/wf0002/tests/)
- Recorded evidence: [`../library/`](../library/README.md) (Oct 28 runs) and [`../library/evidence/live_20261106/`](../library/evidence/live_20261106/measurements.json) (Nov 6 runs)

**Latest live run (Nov 6, DeepSeek V4.1 Flash):** accepted ($0.00084).

## How it works

1. Freeze the slot catalogue
2. One reply filling operations, missing information and repair moves
3. Check slots and exact answer

## The check

Host check: typed_envelope_and_independent_exact_sum.

- `slot coverage: every declared slot s has a typed value or an explicit absence`

## Team

Pattern `solo`: coder ×1 (sonnet); host_checker ×1 (none).

Boost: when missing slot: none on the base path (limit 0).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| arm | unstaged vs staged vs no-model oracle | oracle 100% | live | P027 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf2) · [machine-readable entry](../dag/workflow_dag.json)
