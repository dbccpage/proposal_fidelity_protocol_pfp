# Finite Quotients

When records are merged into classes, any function of the class cannot separate merged records; the demo computes collisions, checks factorization and audits which candidate extensions add real distinctions.

## What it shows

A task declares a finite record domain, a total quotient map, a downstream map on its image, pairs of records that must be distinguished, and a finite family of candidate operations (`decl`, `del`, `ins`, `subst`) with selectors, observers and costs. Collisions are computed from the quotient, not from payload equality. A per-record table factors through the quotient only if it is constant on every class; otherwise the demo returns a concrete conflicting pair.

## Why it matters for PFP

Many PFP checks summarize proposals into classes before judging them. If two proposals fall in the same class, nothing computed from the class can tell them apart. This demo makes that loss visible and shows that adding a distinction requires an explicit new observer, which the report records as an extension rather than a recovery.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Quotient collisions for each demanded pair.
- Factorization of a downstream table through the quotient, or a counterexample pair.
- Execution of candidate operations on selected records and their observed outputs.
- Survivor accounting: which candidates separate the demanded pairs and at what cost.

## Inputs

Default: four puzzles, five drills and an enumeration follow-up. `--input file.json` checks your own task.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/finite_quotients/tests -q -p no:cacheprovider
python demos/finite_quotients/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000037/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 97 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Add a record with the same payload as an existing one but a different ID, and demand that the pair be separated; only an observer that reads the selector can do it.

## Porting notes

No code changes beyond the move.

## Where the code lives

`demos/finite_quotients/` (`run.py`, `tests/`, and a short `README.md`).
