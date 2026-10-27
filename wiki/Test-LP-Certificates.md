# LP Certificates

Checks a proposed primal/dual certificate for a two-variable linear program with exact rational arithmetic, keeping feasibility, optimality and uniqueness separate.

## What it shows

The problem is: maximize c*x subject to Ax <= b and x, y >= 0, with rational data. A candidate supplies a primal point and nonnegative dual multipliers. The checker verifies every primal row and sign constraint, dual feasibility (A-transpose times lambda >= c) and exact equality of the two objective values. It is a certificate checker, not a solver. It also checks a supplied gap-reduction trace step by step.

## Why it matters for PFP

In PFP a model may propose an answer together with evidence; the host must check the evidence instead of trusting the claim. LP duality is a classic case where a short certificate proves optimality. The demo shows the traps: equal objective values without feasibility prove nothing, and a single optimal certificate does not show uniqueness. A second distinct feasible point with the same value establishes non-uniqueness.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Primal feasibility of the proposed point, row by row, plus nonnegativity.
- Dual feasibility and nonnegativity of the multipliers.
- Exact equality c*x = b*lambda using Python `Fraction`.
- Uniqueness status: unestablished from one certificate, refuted by a second optimal point.
- A supplied improvement trace (from the second worksheet) checked step by step; the trace is not produced by an optimizer.

## Inputs

Default: the worked exercises. `--input problem.json` with `--proposal certificate.json` or `--trace trace.json` grades a custom case. Example files ship in the demo folder: `example_certificate.json`, `quiz03_problem.json`, `quiz03_trace.json`, `quiz03_certificate.json`.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/lp_certificates/tests -q -p no:cacheprovider
python demos/lp_certificates/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000027/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "COMPUTED", ...}` and exit 0 for the default run. Grading a proposal prints `ACCEPTED` or `REJECTED`.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 136 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Perturb one coordinate of `example_certificate.json` and run with `--input` and `--proposal`; the checker should report the violated row. Add a test case with a degenerate LP to explore the uniqueness branch.

## Porting notes

No code changes beyond the move. Data files were copied unchanged.

## Where the code lives

`demos/lp_certificates/` (`run.py`, `tests/`, and a short `README.md`).
