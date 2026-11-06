# WF1: Typed answer

**Status:** implemented and runnable. **Kind:** base. **Builds on:** nothing (this is the base).

**Goal:** One schema-valid answer that the host check accepts, or a typed refusal.

## Run it

Step-by-step guide: [Workflow-WF1 on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-WF1). Install: [Workflow-Running](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-Running).

Offline, from the repository root after `pip install ".[workflows]"` (fixture replies: no model call, no cost):

```bash
python -m pfp.workflows.wf0001 prepare pfp/workflows/wf0001/examples/integer_sum.task.json --output runs/wf1
python -m pfp.workflows.wf0001 check runs/wf1 pfp/workflows/wf0001/examples/integer_sum.reply.fixture.json --fixture
python -m pfp.workflows.wf0001 replay runs/wf1
```

Live (needs `OPENROUTER_API_KEY`; set `PFP_REASONING=off` for reasoning models):

```bash
python -m pfp.workflows.wf0001 run pfp/workflows/wf0001/examples/integer_sum.task.json --output runs/wf1-live --model deepseek/deepseek-v4.1-flash --max-output-tokens 3000 --max-estimated-cost-microusd 4999
python -m pfp.workflows.wf0001 replay runs/wf1-live
```

## Source files

- Code: [`pfp/workflows/wf0001/`](../../pfp/workflows/wf0001/) (also installed as the `pfp-wf1` command)
- Example task and fixture replies: [`pfp/workflows/wf0001/examples/`](../../pfp/workflows/wf0001/examples/)
- Tests: [`pfp/workflows/wf0001/tests/`](../../pfp/workflows/wf0001/tests/)
- Recorded evidence: [`../library/`](../library/README.md) (Oct 28 runs) and [`../library/evidence/live_20261106/`](../library/evidence/live_20261106/measurements.json) (Nov 6 runs)

**Latest live run (Nov 6, DeepSeek V4.1 Flash):** accepted ($0.00005).

## How it works

1. Freeze the task and response schema
2. One solver reply
3. Parse the typed envelope
4. Independent exact check

## The check

Host check: typed_envelope_and_independent_exact_sum.

- `accept(r) iff parse(r) = v and v = f(x) for the host-computed f`

## Team

Pattern `solo`: coder ×1 (sonnet); host_checker ×1 (none).

Boost: when host check rejects: none on the base path; WF9 adds bounded repair (limit 0).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| scratchpad | JSON verdict-first vs numeric scratchpad vs glyph runes vs runes+scratchpad+canary (405B, 50 cases) | 50% vs 74% (McNemar p=0.035) vs 48% vs 8% | live | F §4; P008 §9.3 |
| model size ladder | 8B, 70B, a reasoning model across C043-C060 | task-dependent, not monotonic; reruns changed 5/10 outcomes | live | F c043-c059; P010 §4.1 |
| completion ceiling | 2048 / 4096 / 8000 tokens | reasoning model returned empty replies at the cap; budget confounds reasoning vs dense | live | F c045, c046 |
| arithmetic | float vs exact rational | floats give spurious holonomy ~1e-16 | offline | F challenges §6.2 |
| case identifiers | descriptive vs neutral ids | descriptive ids leaked verdicts; a bare refusal passed | offline | P010 §4.2 |
| decode controls | attention bias, grammar mask, activation patching, KV surgery, steering, repeated sampling N=1..16 | attention bias raised mass, not correctness; the rest not run | proposed | F challenges §8.1 |
| gate subset | C1-C8 subsets; replay on/off; leakage audit on/off | — | code | P028 §6 |
| self-report | self-critique or self-verified flag included vs stripped | never read by the host | code | P028 §7; P030 |
| schema examples | with vs without example values | 8B copied placeholder keys | live | F c043-c059 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf1) · [machine-readable entry](../dag/workflow_dag.json)
