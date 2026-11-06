# WF5: Checked rewrite

**Status:** implemented and runnable. **Kind:** procedure extension. **Builds on:** [WF4](../wf04_five_agents_lggr/README.md).

**Goal:** A rewrite that preserves the protected query, then a WF4 pass.

## Run it

Step-by-step guide: [Workflow-WF5 on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-WF5). Install: [Workflow-Running](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-Running).

Offline, from the repository root after `pip install ".[workflows]"` (fixture replies: no model call, no cost):

```bash
python -m pfp.workflows.wf0005 prepare --task pfp/workflows/wf0005/examples/integer_sum.task.json --output runs/wf5-preview
```

Live (needs `OPENROUTER_API_KEY`; set `PFP_REASONING=off` for reasoning models):

```bash
python -m pfp.workflows.wf0005 run --task pfp/workflows/wf0005/examples/integer_sum.task.json --output runs/wf5-live --model deepseek/deepseek-v4.1-flash --budget-microusd 4999
python -m pfp.workflows.wf0005 replay --run runs/wf5-live
```

## Source files

- Code: [`pfp/workflows/wf0005/`](../../pfp/workflows/wf0005/) (also installed as the `pfp-wf5` command)
- Example task and fixture replies: [`pfp/workflows/wf0005/examples/`](../../pfp/workflows/wf0005/examples/)
- Tests: [`pfp/workflows/wf0005/tests/`](../../pfp/workflows/wf0005/tests/)
- Recorded evidence: [`../library/`](../library/README.md) (Oct 28 runs) and [`../library/evidence/live_20261106/`](../library/evidence/live_20261106/measurements.json) (Nov 6 runs)

**Latest live run (Nov 6, DeepSeek V4.1 Flash):** refused: the miner reply failed the strict schema.

## How it works

1. Label every source span
2. Rewrite the whole seed into one grammar
3. Parse, decode and check preservation
4. Run WF4 against the original public input

## The check

Host check: typed_envelope_and_independent_exact_sum.

- `preservation: decode(rewrite(s)) = query(s) on the declared finite language`

## Team

Pattern `parallel_isolated_then_global`: coder ×1 (sonnet); miner ×1 (opus); coder ×5 (sonnet); host_checker ×1 (none).

Boost: when preservation check fails: stop; never solve an unpreserved task (limit 0).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| representation | raw edge list, distractor-masked, 8-letter glyphs, full hybrid | glyphs compressed prompts 56-74% | live | F §2.3 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf5) · [machine-readable entry](../dag/workflow_dag.json)
