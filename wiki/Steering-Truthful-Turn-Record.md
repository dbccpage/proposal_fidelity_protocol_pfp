# Steering: truthful turn record

A run's record steers the next run: later prompts quote it, learning reads it,
and reviewers trust it. The source project found places where its record was
not what the model had actually said: a candidate rebuilt from keywords in the
task, replies hashed lossily, a critique not tied to the candidate it judged.
It fixed them so that **the recorded output is the supplied turn, not an
invented implementation**.

## What the source did

- **Exact reply bytes.** The recorded candidate is the exact reply, not code
  generated from keywords in the objective. Two different invalid-UTF-8 replies
  stay distinct and recoverable.
- **Bound critique.** A critic receives the candidate's actual bytes, and the
  record keeps the critic's actual reply and a digest of what it judged. An
  absent or altered candidate payload is refused before the critic is called.
- **No silent truncation.** A candidate near the context ceiling is neither
  concatenated with other material nor cut short.
- **No fabricated turns.** A turn with no configured executor refuses instead of
  producing a reply. An executor failure stays a typed refusal. A non-fixture
  run without an executor writes no success artifacts.
- **No minted authority.** An executor's output cannot carry authority, and the
  run's terminal status is computed from bound evidence, not inferred from the
  request.

Each rule had a mutation control: restoring the old behaviour (for example
substituting keyword-generated code, or bypassing digest matching) made the
corresponding test fail.

## Replicate it here

In the local swarm (see [running the local swarm](Steering.md#running-the-local-swarm)), `teamwork submit` takes the
reply file as raw bytes. A reply whose input digest does not match the pending
turn is not counted as that role's contribution: the command exits with code 2
and the run is marked `blocked` (checked). The receipt side is shown here too: a
[PFP Lab](PFP-Lab.md) receipt is content-addressed, and `verify` replays it and
refuses one whose bytes were altered.

```powershell
python -m pfp_lab.cli.main run --pack retract-stale-claim --receipt r.json
python -m pfp_lab.cli.main verify r.json
```

Change one recorded `defect_after` in `r.json` and run `verify` again: it
reports `NOT VALID`, names the digest mismatch and the verdict that differs from
the replay, and exits with code 5 (checked). The [QA receipt invariants](Test-Qa-Receipt-Invariants.md)
and [stage receipt tape](Test-Stage-Receipt-Tape.md) demos test the same
property for software QA and paper review records.

## How it relates to PFP, EIS and PCIV

- **PFP.** The prompt-reply binding is only as good as the record of the reply.
  PFP checks the actual completion bytes.
- **EIS.** Antibodies are minted from recorded failures. A record that invents
  or loses replies would mint antibodies against things no model did.
- **PCIV.** Lineage built on an untruthful record would select for the
  recorder's inventions; the [prompt family](Steering-Prompt-Families.md) keeps
  failed calls as data for the same reason.

## Where the code lives

`ops/adversary/use_cases/act_helpers.py`, `ops/adversary/runtime.py` and
`pfp/domain/value_objects/seat_turn.py`.
