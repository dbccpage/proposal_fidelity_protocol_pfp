# Triangle Angle Defects

Validates triangle metrics given as squared edge lengths and computes local angle defects at vertices, keeping exact expressions when a sum cannot be resolved.

## What it shows

A task declares vertices, edges with positive rational squared lengths and triangular faces. For squared sides x, y, z, with N = x + y - z and H = 4xy - N^2, the triangle exists and is nondegenerate exactly when H > 0, and its squared area is H/16. The demo checks every face, rejects incomplete or duplicate presentations instead of guessing, and computes angle defects (2 pi minus the sum of angles) at interior vertices where it can.

## Why it matters for PFP

PFP checks whether a proposal's structure is complete before it computes on it. Here a missing edge or length is reported, never filled in. Where an exact sum of angles cannot be reduced, the result keeps the exact expression rather than returning a rounded number that looks final.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Existence and squared area of each triangle from squared side lengths.
- Closure checks: every edge has its vertices, every face has its edges.
- Local angle defects at vertices with complete neighborhoods.
- Exact symbolic terms for sums that cannot be resolved.

## Inputs

Default: the worksheet rows. `--input file.json` supplies a task, query and proposed answer.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/triangle_angle_defects/tests -q -p no:cacheprovider
python demos/triangle_angle_defects/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000039/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0. If an exercise row lacks a fact recorded for it, the run is marked `MISMATCH` and exits 1.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 122 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Use squared sides 1, 1, 4 (degenerate, H = 0) and confirm the face is refused. Then add faces around one vertex and compare the reported local defect with a hand calculation.

## Porting notes

A code comment that pointed at the original README was reworded. No behavior changes.

## Where the code lives

`demos/triangle_angle_defects/` (`run.py`, `tests/`, and a short `README.md`).
