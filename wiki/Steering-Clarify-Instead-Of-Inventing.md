# Steering: clarify instead of inventing

When a task is missing an input, a model under pressure to answer tends to
invent the missing premise and solve a different problem. The source project
gave the model a second legal outcome: a checked request for the missing
inputs. The request is never counted as a solution.

## What the source did

A task declares the inputs it needs, for example an object model and a choice
of coefficients for a homology question. The model may reply with the outcome
`QUERY_USER_MORE_INFO`, the exact seed it was given, the list of missing fields
and one question per field. The host accepts that reply only if:

- the seed is byte-for-byte the one it sent;
- the listed fields are exactly the declared inputs that are absent (an explicit
  `false` or `0` counts as supplied, not absent);
- there is one non-empty question per missing field, and the `proposal` is empty.

Asking when nothing is missing is refused, so the outcome cannot be used to dodge
the work. An accepted query carries `mathematical_acceptance = NOT_SOLVED`.

In the source project's runs a strict policy let such a query proceed to the
original task checker even when reviewing roles kept repeating the missing
premises as findings. Only the checker's exact output, showing
`QUERY_USER_MORE_INFO` and `NOT_SOLVED`, could settle the outcome; a role saying
so could not.

## Replicate it here

Runs here now (checked). From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "ops;."
python -B clarify.py
```

with `clarify.py`:

```python
from pfp.use_cases.clarification import check_clarification

seed = "Compute the homology of the complex."
required = ("object_model", "coefficients")
supplied = {"object_model": "triangle boundary"}

query = {
    "outcome": "QUERY_USER_MORE_INFO",
    "seed": seed,
    "missing_fields": ["coefficients"],
    "questions": [{"field": "coefficients", "question": "Integers, rationals or Z/2?"}],
    "proposal": "",
}
print(check_clarification(query, seed=seed, required_fields=required, supplied_fields=supplied))

# Asking for something that was already supplied is refused.
greedy = dict(query, missing_fields=["object_model", "coefficients"])
print(check_clarification(greedy, seed=seed, required_fields=required, supplied_fields=supplied))

# Querying when nothing is missing is refused: the model has to attempt the task.
print(check_clarification(query, seed=seed, required_fields=required,
                          supplied_fields={"object_model": "triangle boundary", "coefficients": "Z"}))
```

Expected: the first call returns `Ok(ClarificationCheck(outcome='QUERY_USER_MORE_INFO', ..., mathematical_acceptance='NOT_SOLVED'))`,
the second `CLARIFICATION_BINDING_MISMATCH`, the third
`QUERY_WITHOUT_MISSING_INPUTS`.

To use it as steering, put the declared input list and the reply shape in the
prompt, then route the reply through `check_clarification` before any solver
check. The full multi-role version in `ops/adversary/` is not runnable here yet.

## How it relates to PFP, EIS and PCIV

- **PFP.** This is a typed residual: the proposal reports what is missing
  instead of filling it. The host checks the residual against the task's own
  contract, just as it checks a repair against an obstruction
  ([Rewriting: residual repair](Rewriting-PFP-Residual-Repair.md)).
- **EIS.** Inventing a premise is one of the failure patterns the immune system
  is meant to catch; giving the model a legal way to say "missing" removes the
  pressure that produces it.
- **PCIV.** A prompt that leads to accepted queries rather than invented answers
  is a fitter variant, but only when the checker, not the model, says so.

## Where the code lives

`pfp/use_cases/clarification.py`. The strict query policy and its use in a full
run are in `ops/adversary/domain/checked_reuse.py` and
`ops/adversary/entrypoints/teamwork_cli.py`.
