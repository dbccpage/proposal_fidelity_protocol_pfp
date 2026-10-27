# Face Activation

Checks a single permitted state transition that switches one triangular face on, and keeps assigned toy observables separate from topology.

## What it shows

A task declares 3 to 16 vertices, 3 to 48 oriented edges and exactly one potential triangular face. An activity bit says whether the face is in the active complex. The permitted transition increments a revision counter, changes the bit from 0 to 1, and preserves every payload value exactly (1 and true stay distinct). An optional adapter assigns mass and drag values as scale times the activity bit; an absent assignment stays null.

## Why it matters for PFP

PFP checks that a proposed state change does exactly what it says and nothing else. This demo is a minimal example: one bit changes, the revision advances, and the payload is unchanged byte for byte. A matching refusal is still a match; matching the evaluator does not execute the requested transition.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Signed boundaries of the declared face and edges.
- Validation of the 0 to 1 transition and payload preservation.
- Assigned observables from rational scales, with null kept distinct from zero.
- Strict input checks: identifiers, bounds, duplicate keys, floats and unknown fields refused.

## Inputs

Default: the worksheet rows. `--input path.json` checks a proposed answer.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/face_activation/tests -q -p no:cacheprovider
python demos/face_activation/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000041/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0. The test suite includes subprocess mutation runs and takes a few minutes.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 89 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Change a payload value from 1 to true in a proposed after-state; the transition should be rejected.

## Porting notes

A code comment that pointed at the original README was reworded. No behavior changes.

## Where the code lives

`demos/face_activation/` (`run.py`, `tests/`, and a short `README.md`).
