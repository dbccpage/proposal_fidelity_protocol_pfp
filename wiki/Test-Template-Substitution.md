# Template Substitution

Shows that building a prompt by successive string replacement can rewrite the inserted data, while a single template substitution does not.

## What it shows

Two fixed templates place a question before or after some data, using placeholders `${question}` and `${data}`. A single standard-library `string.Template.substitute` call inserts both values once. The baseline instead replaces `${data}` first and then `${question}` across the whole intermediate string. If the data itself contains `${question}`, the second replacement changes the data.

## Why it matters for PFP

A PFP prompt must carry the caller's data exactly. Prompt construction is a place where data can be silently altered before any model sees it. This demo checks prompt construction only: preserving inserted text does not make it trusted and does not prevent prompt injection inside a model.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- The single-pass rendering and the sequential-replacement rendering.
- Whether the two differ, plus byte and code point counts.
- Strict request validation (typed fields, size limit of 16,384 bytes).

## Inputs

Default: data that contains the literal text `${question}`. `--input examples/request.json` (relative to the demo folder) or your own JSON request.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/template_substitution/tests -q -p no:cacheprovider
python demos/template_substitution/run.py
python demos/template_substitution/run.py --input demos/template_substitution/examples/request.json
```

## Expected output

A JSON object with `rendered`, `sequential`, `differs: true`, byte and code point counts and `provider_calls: 0`. In `rendered` the data keeps `${question}`; in `sequential` it has been replaced by the question text.

The test suite has 26 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Remove `${question}` from the data and confirm `differs` becomes false. Put `${data}` in the question to see the other ordering problem.

## Porting notes

Only `run.py`, the example request and its main test file were ported. A separate coverage and mutation orchestration script (`check.py`) and its test were not ported because they need the `coverage` package, which is not a declared dependency. This demo needs Pydantic, which is a declared dependency.

## Where the code lives

`demos/template_substitution/` (`run.py`, `tests/`, and a short `README.md`).
