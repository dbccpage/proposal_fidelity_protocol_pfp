# WF3: Mine, then solve

**Status:** implemented and runnable. **Kind:** procedure extension. **Builds on:** [WF1](../wf01_typed_answer/README.md).

**Goal:** Useful frozen guidance, then an accepted answer.

## Run it

Step-by-step guide: [Workflow-WF3 on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-WF3). Install: [Workflow-Running](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-Running).

Offline, from the repository root after `pip install ".[workflows]"` (fixture replies: no model call, no cost):

```bash
python -m pfp.workflows.wf0003 prepare pfp/workflows/wf0003/examples/integer_sum.task.json --output runs/wf3
python -m pfp.workflows.wf0003 check-mining runs/wf3 pfp/workflows/wf0003/examples/mining.reply.fixture.json --fixture
python -m pfp.workflows.wf0003 check runs/wf3 pfp/workflows/wf0003/examples/solver.reply.fixture.json --fixture
python -m pfp.workflows.wf0003 replay runs/wf3
```

Live (needs `OPENROUTER_API_KEY`; set `PFP_REASONING=off` for reasoning models):

```bash
python -m pfp.workflows.wf0003 run pfp/workflows/wf0003/examples/integer_sum.task.json --output runs/wf3-live --model deepseek/deepseek-v4.1-flash --budget-microusd 4999
python -m pfp.workflows.wf0003 replay runs/wf3-live
```

## Source files

- Code: [`pfp/workflows/wf0003/`](../../pfp/workflows/wf0003/) (also installed as the `pfp-wf3` command)
- Example task and fixture replies: [`pfp/workflows/wf0003/examples/`](../../pfp/workflows/wf0003/examples/)
- Tests: [`pfp/workflows/wf0003/tests/`](../../pfp/workflows/wf0003/tests/)
- Recorded evidence: [`../library/`](../library/README.md) (Oct 28 runs) and [`../library/evidence/live_20261106/`](../library/evidence/live_20261106/measurements.json) (Nov 6 runs)

**Latest live run (Nov 6, DeepSeek V4.1 Flash):** refused: the solver hit its fixed 1,300-token limit.

## How it works

1. Mining call proposes operation guidance
2. Screen and freeze guidance
3. Solver call uses frozen guidance
4. Independent check

## The check

Host check: typed_envelope_and_independent_exact_sum.

- `guidance g is frozen before the solve: hash(g) recorded, never edited after the solver starts`

## Team

Pattern `relay`: miner ×1 (run_o); coder ×1 (sonnet); host_checker ×1 (none).

Boost: when guidance screen rejects: none on the base path (limit 0).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| priming | gauge-fixing algorithm primed first vs not | primed: 0% (pure-gauge bias) | live | F §3.4 |
| antibodies | prompt antibodies alone vs antibodies plus pinned tokens | alone: 0% on non-abelian; with pinned tokens helped | live | F synthesis |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf3) · [machine-readable entry](../dag/workflow_dag.json)
