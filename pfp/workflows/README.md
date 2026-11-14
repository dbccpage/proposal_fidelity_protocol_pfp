# Standalone automated PFP workflows

Five segregated workflow folders, one canonical provider/accounting boundary.
Install `python -m pip install ".[workflows]"` from the repository root, and
build the checker once: `cargo build --release -p pfp_operads --manifest-path code/rust/Cargo.toml`.
The integer-sum judge and the reply-envelope checks run in that Rust program
(`pfp_operad`); Python carries the request and the outcome.

| Folder | Contract | Maximum normal calls |
| --- | --- | ---: |
| `wf0001` | Basic P*, one typed answer | 1 |
| `wf0002` | Full slots and all emitted operad/DDC occurrences | 1 |
| `wf0003` | Screen/freeze mining, then one solver | 2 |
| `wf0004` | One miner, five simultaneous solvers and LGGR | 6 |
| `wf0005` | Full checked PFP packet rewrite, then WF4 structure | 6 |

Use [the runnable guide](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_running).
The installed console commands are `pfp-wf1` through `pfp-wf5`.

Shared task custody lives in `pfp.infrastructure.workflow_runtime`; atomic
batch admission extends the existing estimated ledger in `workflow_accounting`.
Provider, LGGR and ROP source owners remain under `ops/`; packaging maps their
existing logical `adversary`, `operations` and `governance.domain` imports.
No provider transport is copied into a workflow folder.

The default/maximum allowance is $0.004999 per run, including all its phases.
Reservations use estimated rates, 2× headroom and the 80% stop threshold.
It is not a vendor-enforced cap. Unknown cost retains liability and blocks dispatch.
Failed attempts and immutable source identity remain part of custody.

## Failure ledger

A run's failures can be kept, and the rules learned from them loaded into
later runs. The default path is unchanged: a task that was never loaded gives
the same prompts as before. Every check below is made by `pfp_operad`;
`failure_ledger.py` only carries files to it.

```
python -m pfp.workflows.failure_ledger record LEDGER.jsonl RUN_FOLDER...
python -m pfp.workflows.failure_ledger load LEDGER.jsonl TASK.json --output LOADED_TASK.json [--on-trial RULE]
python -m pfp.workflows.failure_ledger check LEDGER.jsonl LOADED_TASK.json
python -m pfp.workflows.failure_ledger trial LEDGER.jsonl RULE --pair BASELINE_TURN TREATED_TURN LOADED_TASK.rules.json
```

1. `record` hands every turn folder of a finished run (the run folder of WF1
   and WF2, the `solver` and `agent-N` folders of WF3 to WF5) to the host. The
   host judges the stored task result and appends a failure record when it is
   wrong. A correct turn, or a turn with no judge such as mining, adds nothing.
2. A rule is proposed by appending a `candidate` record that names the
   failures it comes from (`pfp_operad ledger append`).
3. `load` writes a task whose seed carries the admitted rules, plus
   `--on-trial RULE` for the treated arm of a trial, and a receipt beside it
   (`.rules.json`: the base seed, the ledger head and the rules).
4. `trial` gives the host pairs of turns on held-out tasks: one run from the
   task loaded without the rule, one with it. The host refuses a pair whose
   seeds differ by anything but that rule, scores the rest and appends the
   trial. An `admission` record is accepted only on a trial the rule won.
5. `check` asks the host whether a task's seed is exactly what the ledger
   loaded. It works on the `task.json` inside a run folder with `--receipt`.

WF1 to WF4 run a loaded task as any other. WF5 does not: its rewrite accepts
one seed language and refuses a seed with rules after it
(`WF5_UNSUPPORTED_SEED_LANGUAGE`). WF5 failures are still recorded.

Historical captures are not rewritten to match new package identities.
The baseline is reused from the original experiment; migration tests use fixtures,
not another paid baseline or fresh model performance measurements.
