# Triangle Fan Pairing

Computes exact angle data for a fan of unit equilateral triangles around a center, and evaluates finite signed pairing sums on a separate carrier.

## What it shows

Two carriers are kept separate. The first is an intrinsic fan: 3 to 12 abstract unit-length triangles that all contain a declared center vertex, whose link must be a single cycle. Each center angle is exactly 1/6 of a full turn, so with n triangles the normalized deficit is 1 - n/6: six triangles are flat, five give +1/6, seven give -1/6. The demo also reports the f-vector (n+1, 2n, n), Euler characteristic 1 and rim turning. The second carrier is a finite list of pairs, each with one positive and one negative weighted member, for which the demo computes signed pairing sums exactly.

## Why it matters for PFP

Mixing two carriers in one answer is a common way for a proposal to claim more than it computed. PFP keeps each carrier and its operations explicit. The demo also shows that a correct refusal can match the host answer without the refused claim being accepted.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Fan validation: every triangle contains the center, every rim vertex has degree 2, the link is connected; duplicates and open fans are rejected.
- Center angle list, sum, exact signed deficit and its zero/positive/negative classification.
- f-vector, Euler characteristic and total rim turning as extra finite checks.
- Signed pairing sums on the second carrier.
- Four source cases and seven controls.

## Inputs

Default: the four source cases and controls. `--input document.json` with `request` and `proposal`.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/triangle_fan_pairing/tests -q -p no:cacheprovider
python demos/triangle_fan_pairing/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000045/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 128 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Use six triangles for a flat fan (defect 0), five for a positive defect and seven for a negative one.

## Porting notes

No code changes beyond the move.

## Where the code lives

`demos/triangle_fan_pairing/` (`run.py`, `tests/`, and a short `README.md`).
