# Checkerboard Paths

Counts lattice paths on a 1+1 dimensional checkerboard exactly, by number of direction changes, and sums them with declared corner weights.

## What it shows

Points are integer pairs [t, x]. Each step has dt = 1 and dx = +1 or -1. For a horizon of up to 32 steps the demo enumerates paths between two points, groups them by the number of corners (direction changes), and forms a weighted sum with a declared weight per corner (from the epsilon and mass parameters). Results are exact: path counts are integers and amplitudes are pairs of rationals.

## Why it matters for PFP

The demo is a compact example of the PFP rule that the host recomputes the full answer. Histograms by corner count and by direction are checked field by field, so a proposal that gets the total right but the breakdown wrong is rejected. It also records what is not claimed: no normalization, unitarity or continuum limit.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Total path counts and corner histograms between two points.
- Weighted path sums (amplitudes) for given epsilon and mass parameters.
- Direction-split histograms and amplitudes.
- Edge cases: empty path, single step, unreachable endpoints.

## Inputs

Default: four puzzles, seven drills and seven controls. `--input submission.json` with `request` and `proposal` (`input_sha256` over the canonical request JSON, and `answer`).

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/checkerboard_paths/tests -q -p no:cacheprovider
python demos/checkerboard_paths/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000043/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 112 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Request a kernel for horizon 4 and check the histogram against a hand count. Change the mass parameter and watch the amplitude change while the counts stay fixed.

## Porting notes

A code comment that pointed at the original README was reworded. No behavior changes.

## Where the code lives

`demos/checkerboard_paths/` (`run.py`, `tests/`, and a short `README.md`).
