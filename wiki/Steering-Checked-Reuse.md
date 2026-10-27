# Steering: checked reuse

Once a task has been solved and checked, the tempting shortcut is to show the
model the old answer and ask it to "adapt" it. The source project did something
narrower. It registered the checked procedure, let the model **acknowledge** a
registered recipe by id and digest, and had the host apply the checked bytes,
followed by fresh checks of both the source and the target task.

## What the source did

- A pinned registry entry binds the source and target seeds and premises, the
  contract bytes, the declared checker sources, the original candidate, the
  native procedure and a seed-only graph-rewrite rule. Every other candidate
  field is protected.
- An unknown recipe, changed premise, stale checker or candidate, altered
  procedure, or an attempt to reuse the old mathematical verdict is refused.
  A known rule name with an altered body does not authorize anything.
- The reuse command takes an operator-chosen check command, placed last, with
  literal `{candidate}`, `{seed}`, `{premises_json}` and `{contract}` slots
  replaced in a single pass. Braces inside the seed stay data, and no shell is
  involved.
- Both source and target are checked afresh. A failed target is kept. The
  checker's output digest is computed by the host from the captured output, and
  a checker that changes the candidate cannot report acceptance of the original.
- In a full run the builder role returns only the acknowledgement. A model
  acknowledgement does not generate the reused candidate or borrow a pass. A
  reused clarification stays a clarification (`NOT_SOLVED`).

## Replicate it here

Partly runnable. The registry and its validation are pure Python in
`ops/adversary/domain/checked_reuse.py` (imports with `$env:PYTHONPATH = "ops;."`);
applying a procedure goes through `ops/adversary/use_cases/checked_ddc_reuse.py`,
which needs the native host. The finite rewrite rule it relies on is
`pfp/domain/rewriting/finite_dpo.py`.

The principle that a reused result is not a result until it is checked again
can be seen in [PFP Lab](PFP-Lab.md): a receipt from one run says nothing about
another scenario. `verify` replays the receipt against its own scenario only.

```powershell
python -m pfp_lab.cli.main run --pack section-repair --receipt section.json
python -m pfp_lab.cli.main verify section.json
```

## How it relates to PFP, EIS and PCIV

- **PFP.** Reuse is a proposal like any other; the reused bytes are checked
  fresh, and no verdict is inherited.
- **Operads.** A registered procedure is a typed composite with a fixed
  rewrite rule ([Operads: rewriting and packetization](Operads-Rewriting-and-Packetization.md),
  [WDP: DDC](Rewriting-WDP-DDC.md)).
- **PCIV.** A registered recipe is a retrievable, inherited trait; retrieval
  does not carry fitness with it ([PCIV: selection and retrieval](PCIV-Selection-and-Retrieval.md)).

## Where the code lives

`ops/adversary/domain/checked_reuse.py`, `ops/adversary/use_cases/checked_ddc_reuse.py`,
`ops/adversary/entrypoints/checked_reuse_cli.py` and
`pfp/domain/rewriting/finite_dpo.py`.
