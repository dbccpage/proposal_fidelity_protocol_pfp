# Run WF1–WF5 in the standalone repository

**Start with WF1.** All five runners now live in separate `pfp/workflows/wf0001`
through `wf0005` folders. You need Python 3.12+.

The commands below target the migration branch while its source PR is open.
After merging, a normal checkout of `main` includes them.

## 1. Install

```powershell
git clone --branch codex/workflow-library-guides https://github.com/dbccpage/proposal_fidelity_protocol_pfp.git
cd proposal_fidelity_protocol_pfp
python -m venv .venv
$pfpPython = (Resolve-Path .venv/Scripts/python.exe).Path
& $pfpPython -m pip install ".[workflows]"
```

The commands below use the explicit PowerShell `$pfpPython` variable, so they
keep using the environment you just installed. On macOS/Linux, run them with
`.venv/bin/python` in place of `& $pfpPython`.
The package also installs `pfp-wf1` through `pfp-wf5` console commands.
No separate engine checkout or native build is needed for these estimated-budget workflows.

## 2. Get a first checked receipt, offline

These are **hand-authored fixtures**, not fresh model responses. Run each command
from the repository root, using a fresh output folder:

```powershell
& $pfpPython -m pfp.workflows.wf0001 prepare pfp/workflows/wf0001/examples/integer_sum.task.json --output runs/wf1-offline
& $pfpPython -m pfp.workflows.wf0001 check runs/wf1-offline pfp/workflows/wf0001/examples/integer_sum.reply.fixture.json --fixture
& $pfpPython -m pfp.workflows.wf0001 replay runs/wf1-offline
```

**Checkpoint:** the check reports `HOST_ACCEPTED`; replay reports
`replay_verified: true` and makes zero provider calls. Keep the whole run folder.
Change `wf0001` to `wf0002` and use `runs/wf2-offline` for the WF2 fixture.

WF3 has separate mining and solver controls:

```powershell
& $pfpPython -m pfp.workflows.wf0003 prepare pfp/workflows/wf0003/examples/integer_sum.task.json --output runs/wf3-offline
& $pfpPython -m pfp.workflows.wf0003 check-mining runs/wf3-offline pfp/workflows/wf0003/examples/mining.reply.fixture.json --fixture
& $pfpPython -m pfp.workflows.wf0003 check runs/wf3-offline pfp/workflows/wf0003/examples/solver.reply.fixture.json --fixture
& $pfpPython -m pfp.workflows.wf0003 replay runs/wf3-offline
```

WF4/WF5 can prepare without a key or charge:

```powershell
& $pfpPython -m pfp.workflows.wf0004 prepare --task pfp/workflows/wf0004/examples/integer_sum.task.json --output runs/wf4-preview
& $pfpPython -m pfp.workflows.wf0005 prepare --task pfp/workflows/wf0005/examples/integer_sum.task.json --output runs/wf5-preview
```

Preparation does not claim a completed six-call run. WF5 also writes its rewrite
and preservation check. Unsupported seed language is refused before model dispatch.

## 3. Run with OpenRouter

Set `OPENROUTER_API_KEY` in your environment using your usual secret-management
method. The following commands **can incur charges**. Keep preview folders and
live run folders separate; `run` creates a new attempt and never overwrites one.

```powershell
& $pfpPython -m pfp.workflows.wf0001 run pfp/workflows/wf0001/examples/integer_sum.task.json --output runs/wf1-live --model meta-llama/llama-3.3-70b-instruct --max-output-tokens 3000 --max-estimated-cost-microusd 4999
& $pfpPython -m pfp.workflows.wf0002 run pfp/workflows/wf0002/examples/integer_sum.task.json --output runs/wf2-live --model meta-llama/llama-3.3-70b-instruct --max-output-tokens 3000 --max-estimated-cost-microusd 4999
& $pfpPython -m pfp.workflows.wf0003 run pfp/workflows/wf0003/examples/integer_sum.task.json --output runs/wf3-live --model meta-llama/llama-3.3-70b-instruct --budget-microusd 4999
& $pfpPython -m pfp.workflows.wf0004 run --task pfp/workflows/wf0004/examples/integer_sum.task.json --output runs/wf4-live --budget-microusd 4999
& $pfpPython -m pfp.workflows.wf0005 run --task pfp/workflows/wf0005/examples/integer_sum.task.json --output runs/wf5-live --budget-microusd 4999
```

Choose **one** command for the workflow you need. This block is a menu, not a
request to buy all five runs. WF4/WF5 pin Llama 3.3 70B internally.

| Workflow | Maximum new calls on its normal path | Output ceilings per call |
| --- | ---: | --- |
| WF1 | 1 | Explicit caller choice, at most 3,000. |
| WF2 | 1 | Explicit caller choice, at most 3,000. |
| WF3 | 2 | Miner 1,000; solver 1,300. |
| WF4 | 6 | Miner 1,000; each of five solvers 400. |
| WF5 | 6 | Deterministic rewrite 0 calls; miner 1,000; each solver 224. |

`4999` micro-USD means **$0.004999** for the complete run, including its miner
and all solvers. The gateway reserves conservative estimates with 2× headroom
and stops at 80% of that original allowance. Prices are snapshotted at dispatch.
A batch reserves all five liabilities atomically before any solver starts.

This is **estimated host accounting**, not a vendor-enforced dollar cap.
An over-estimate charge or unknown cost is retained and blocks later actions;
the system does not turn missing cost into zero. Native hard-budget mode is a
separate optional integration and is not needed by these commands.

## 4. Replay; do not silently retry

```powershell
& $pfpPython -m pfp.workflows.wf0001 replay runs/wf1-live
& $pfpPython -m pfp.workflows.wf0002 replay runs/wf2-live
& $pfpPython -m pfp.workflows.wf0003 replay runs/wf3-live
& $pfpPython -m pfp.workflows.wf0004 replay --run runs/wf4-live
& $pfpPython -m pfp.workflows.wf0005 replay --run runs/wf5-live
```

Replay is read-only and checks retained bytes, manifests, implementation identity
and the declared task predicates. A changed implementation is refused rather
than accepted by rewriting a manifest. A refused/partial run may have only a
`stopped.json` or `failure.json`; keep it even when it cannot replay as a completed run.

For WF5, an explicit `--previous-attempt PATH` on `prepare` or `run` can continue
a sealed failed-miner history. It verifies the task, hashes, settled accounting
and prior chain, then **reduces** the allowance. It accepts only the supported
failed-miner shape, not an accepted or unaccounted run. Older source identities
remain historical; they are not regraded by the new runner.

Keep continuations in one linear chain. The recipe does not allocate a shared
allowance across separately forked sibling continuations.

WF3's programmatic reused-miner continuation remains explicit, with a separately
declared remaining repair allowance. Its historical repair campaign is not
automatically restarted by these fresh-run commands.

## What was tested for this migration?

The full migrated regression suite and additional CLI controls ran offline.
Every CLI `run` path was exercised using scripted accounted providers; WF4/WF5
included actual concurrent host invocation and independent global rejection of
wrong unanimous answers. A built wheel was checked outside the checkout for
resource lookup and entry points. No new live model call was made.

The [migration validation receipt](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/docs/workflows/migration_validation.json)
records the exact checks and their limits. Existing [October 28 results](Workflow-Results.md)
remain historical measurements, with their original versions and raw replies intact.

[Choose a workflow](Workflows.md) · [Troubleshooting](Workflow-Troubleshooting.md)
