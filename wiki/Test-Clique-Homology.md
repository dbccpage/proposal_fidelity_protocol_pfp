# Clique Homology

Builds the clique complex of a small graph, reduces its boundary matrices over the rationals and reports exact Betti numbers.

## What it shows

A request gives a simple undirected graph of at most six vertices, either as JSON or as a compact glyph text such as `0>1<>1>2<>0>2`, plus a maximum dimension. The demo enumerates all cliques up to that dimension, forms signed boundary matrices, row-reduces them with exact rationals and reports the Betti numbers. Loops, repeated edges and undeclared endpoints are refused.

## Why it matters for PFP

Betti numbers are a standard invariant for checking whether two structures could be the same. In PFP terms the point is again full recomputation and exact arithmetic: the complete answer object, including the selected dimension and Betti numbers, must match.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Clique enumeration up to the declared `max_dimension` (0 to 4), with truncation reported.
- Signed boundary matrices reduced over Q (ordinary unreduced homology).
- Betti numbers for each degree.
- Grading of a proposal against the host answer, bound by a request digest.

## Inputs

Default: nine historical question and answer pairs plus seven controls. `--input document.json` with `request` and `proposal`.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/clique_homology/tests -q -p no:cacheprovider
python demos/clique_homology/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000044/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 111 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Compare a 4-cycle (Betti 1 = 1) with the same cycle plus one diagonal (Betti 1 = 0).

## Porting notes

No code changes beyond the move. Rational homology only; integral torsion is out of scope.

## Where the code lives

`demos/clique_homology/` (`run.py`, `tests/`, and a short `README.md`).
