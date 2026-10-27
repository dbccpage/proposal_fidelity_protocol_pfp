# Steering: prompt families

Steering is usually described as "a better prompt". The source project argued
that a prompt is not better or worse on its own: it is a relation between some
bytes and a reader, and repairing it is a problem with a residual, like any other
PFP problem. It recorded prompts, readers, calls and repairs as a typed family.

## What the source did

A prompt family is a directed acyclic graph of typed records:

| Record | Meaning |
| --- | --- |
| Reader | Who read the prompt: model, router, seat, tier, sampling settings, configuration. Unknown fields stay `None`. |
| Prompt node | One prompt as read by one reader. The same bytes read by a different reader are a different node. |
| Call record | One model call, including failed ones. Failures are data. |
| Repair step | Input node to output node, with the rewrite letter used, the residual before and after, the calls, and a fitness vector. |
| Terminal | Exactly one of Repaired, BudgetExhausted or TypedResidual. |

The validator enforced honesty rules:

- nothing unknown is filled in on a model's behalf;
- a domain label stays **proposed** until a host check receipt confirms it;
- a fitness verdict (accept or reject) needs a checker id, and that checker may
  not be one of the readers that proposed the step, so a model cannot grade its
  own prompt;
- `Repaired` needs an external accept and an exact final residual;
- cycles are refused;
- replaying an old call ledger never invents billing: a call with missing cost
  is not a free call.

The source states that nothing here supports a claim about model quality. The
family is a record of what happened, so that later comparisons are honest.

## Replicate it here

The records are pure Python in `ops/adversary/domain/prompt_family.py`
(`ReaderV1`, `PromptNodeV1`, `CallRecordV1`, `RepairStepV1`, `TerminalV1`,
`PromptFamilyV1`). They import with `$env:PYTHONPATH = "ops;."`.
`validate_family(family, native_support)` needs the native host, because the
checks run in Rust. Replay from a run's call ledger is
`ops/adversary/use_cases/prompt_family_replay.py`.

A [PFP Lab](PFP-Lab.md) receipt has the same shape on a small scale: each move
is a step with a residual (the defect) before and after, refusals are kept as
data, and the result is decided by recomputation, not by whoever proposed the
move. Writing each prompt variant's proposed claims as a Lab scenario gives a
receipt per variant that can be compared on the defect alone.

## How it relates to PFP, EIS and PCIV

- **PCIV.** This is the prompt civilization's genome and lineage record
  ([PCIV: genomes and lineage](PCIV-Genomes-and-Lineage.md)): nodes are
  individuals, repair steps are mutations, and fitness must come from an
  external checker ([PCIV: selection](PCIV-Selection-and-Retrieval.md)).
- **PFP.** A repair step is a PFP move on prompts: a residual before, a
  proposal, a residual after, and a host verdict.
- **EIS.** A label confirmed by a host receipt can later support an antibody;
  a proposed label cannot (see [Learning from runs](Steering-Learning-From-Runs.md)).

## Where the code lives

`ops/adversary/domain/prompt_family.py`,
`ops/adversary/use_cases/prompt_family_replay.py` and
`ops/adversary/infrastructure/prompt_family_binder.py`.
