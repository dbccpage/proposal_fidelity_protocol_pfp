# Hodge Decomposition

Computes an exact rational Hodge decomposition of a cochain on a small simplicial complex into exact, coexact and harmonic parts.

## What it shows

A request names a complex (by facets), a degree and a cochain with rational entries. The demo computes signed boundary matrices, the combinatorial Laplacian, and the orthogonal decomposition of the cochain into an exact part, a coexact part and a harmonic part, all in exact rationals. A separately named unit complement-face map is computed as its own operation.

## Why it matters for PFP

Decomposition answers are easy to state and easy to get subtly wrong. PFP grades the complete answer object, including bases and scope fields, against a fresh host calculation, bound by a SHA-256 digest of the canonical request. A correctly reported refusal of a continuum claim can match; matching is correspondence to the declared calculation, not acceptance of a broader claim.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Boundary matrices and Laplacians for degrees 0 to 2 on up to six vertices.
- Exact orthogonal projection onto exact, coexact and harmonic subspaces.
- The four worksheet puzzles and eight drills, as wire strings and structured answers.
- Grading of supplied `request` plus `proposal` documents.

## Inputs

Default: the worksheet. `--input document.json` with exactly `request` and `proposal`; the proposal has `input_sha256` (SHA-256 of the canonical request: sorted keys, compact separators, ASCII) and `answer`.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/hodge_decomposition/tests -q -p no:cacheprovider
python demos/hodge_decomposition/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000042/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 155 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Use the filled triangle with cochain (1, 2, 3) in degree 1, as in the example request, then remove the facet and compare the harmonic part.

## Porting notes

The cochain placeholder in the wire strings was renamed from a Greek-letter name to `form` (for example `harmonic<form_k,0>`); the mathematics is unchanged. A code comment that pointed at the original README was reworded.

## Where the code lives

`demos/hodge_decomposition/` (`run.py`, `tests/`, and a short `README.md`).
