# Cochains Hodge Adapter

Computes signed coboundaries on a small oriented complex, separates closed from exact integer cochains, and applies a declared diagonal Hodge map to a constructed dual.

## What it shows

A task declares vertices, oriented edges and oriented faces; list order is basis order and orientation matters. The demo builds the coboundary matrices d0 and d1, checks d1 d0 = 0, and classifies an integer edge cochain as exact (with a vertex potential) or closed but not exact (with a cycle witness). A separate adapter constructs the cellular dual and applies a declared positive diagonal edge weight.

## Why it matters for PFP

Cochains and coboundaries are the algebra under several PFP consistency checks (see [Operads](Operads.md) and [Core Concepts](Core-Concepts.md)). The point here is discipline: closed does not mean exact, a smooth-geometry claim is refused instead of imported, and a proposal must match the full structured answer, bound by a hash of the task and query.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- d0 and d1 matrices and the nilpotency check.
- d0 and d1 applied to integer cochains.
- Closed versus exact classification, with a potential or cycle witness.
- Dual cells and a rational edge image under the declared adapter.
- A typed refusal for unsupported smooth imports.

## Inputs

Default: ten worksheet rows plus counterexamples. `--input packet.json` with exactly `task`, `query` and `proposal`; the proposal carries `problem_sha256` and the structured `answer`.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/cochains_hodge_adapter/tests -q -p no:cacheprovider
python demos/cochains_hodge_adapter/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000040/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0. A graded proposal gives `MATCH` (exit 0) or `MISMATCH` (exit 1).

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 87 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Take a hollow triangle and the cochain (1, 1, 1) around it: closed but not exact. Add the face and the same cochain is no longer closed.

## Porting notes

A code comment that pointed at the original README was reworded. No behavior changes.

## Where the code lives

`demos/cochains_hodge_adapter/` (`run.py`, `tests/`, and a short `README.md`).
