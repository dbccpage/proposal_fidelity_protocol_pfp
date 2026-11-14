# WF55: Failure ledger with trial-gated rules

**Status:** offline runner with fixtures; no model run yet. **Kind:** meta workflow. **Builds on:** [WF1](../wf01_typed_answer/README.md), [WF14](../wf14_immune_failure_classification/README.md).

**Goal:** Keep what went wrong, and load a rule in later runs only after it fixed held-out cases and broke none.

## Why

A workflow that forgets its failures repeats them. A workflow that turns every
failure into a prompt rule collects rules that do nothing or do harm. WF55 keeps
both in one ledger and makes each rule earn its place.

## How it works

1. The task carries the ledger so far, answers the host rejected in earlier
   runs, and held-out cases.
2. The host replays the ledger and lists the rules already admitted. Every
   prompt of this run carries them.
3. The host judges each reported failure itself. An answer its judge accepts
   cannot be recorded as a failure.
4. A model proposes one rule: an id, a kind, a constraint in words, and the
   failures it comes from.
5. Each held-out case is answered twice: without the proposed rule
   (`baseline`) and with it (`treated`).
6. The host judges both answers of every case and writes the trial record.
7. The ledger admits the rule only on that trial.

The outcome carries the new ledger. Pass it to the next run as `ledger`.

## The check

All of it is the Rust host [`pfp_operad`](../../code/rust/pfp_operads/README.md).
The Python asks the model and carries records between host commands.

- `witness`: is this answer a failure? If so, its ledger record.
- `trial`: the judge's verdict on every baseline and treated answer, and the
  trial record.
- `ledger append`: a rule is admitted only on its latest trial, when
  `treated_correct > baseline_correct` and no case the baseline had right went
  wrong. Held-out cases may not be failures the rule came from.
- `ledger verify`: an edited, reordered or cut ledger does not replay.

A rejected rule stays in the ledger and can be tried again. Admission means
"may be loaded", not "is correct".

## Run it offline

Build the host once (`cargo build --release -p pfp_operads` in `code/rust`), then
from the repository root:

```powershell
python -m pfp_core.workflow_families run WF55
python -m pytest pfp_core/workflow_families/tests -q -k "WF55 or learning"
```

[`examples/ledger_after_first_run.jsonl`](examples/ledger_after_first_run.jsonl)
is the ledger the first fixture leaves behind. Read it with the host:

```powershell
cd code/rust
cargo run -p pfp_operads -- ledger verify ../../workflows/wf55_failure_ledger_with_trial_gated_rules/examples/ledger_after_first_run.jsonl
cargo run -p pfp_operads -- ledger admitted ../../workflows/wf55_failure_ledger_with_trial_gated_rules/examples/ledger_after_first_run.jsonl
```

The fixture `later_run_loads_the_admitted_rule` starts from that ledger: its
prompts carry the rule the first run admitted.

## Limits

- The task is the integer sum of WF1, because the host has an exact judge for it.
- The host judges the answers it is given. It does not see that the treated
  answers were really produced with the rule loaded; the run's transcript
  records the prompts.
- A rule is words added to a prompt. Whether a model obeys it is what the trial
  measures.

## Predicted effect for a model campaign

On integer sums with negative values, a model that drops signs at baseline
answers more held-out cases correctly once an admitted sign rule is loaded, and
a rule that does not help is never loaded. Not measured yet.

More: [wiki page](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_wf55) · [machine-readable entry](../../dag/reviews/workflows_audit.json)
