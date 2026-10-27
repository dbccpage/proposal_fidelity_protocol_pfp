# Integer Obstruction Lift

Shows that a problem with no integer solution can have a rational one, and that the rational witness does not repair the integer problem.

## What it shows

Multiplication by 2 on the integers has the cycle 1 that is not a boundary, so its class in H1 = Z/2Z is nonzero. Over the rationals 1/2 solves the separately declared rational problem, and H1 over Q vanishes, but H0 = Q, so the rational complex is not acyclic. The integral minimum of |1 - 2c| is 1, attained at c = 0 and c = 1. A hollow and a filled triangle share the same edge boundary map but differ in their declared 2-cells.

## Why it matters for PFP

A frequent proposal defect is to change the carrier (here, from integers to rationals) and then report success on the original problem. PFP requires the carrier to stay fixed unless a change is explicitly declared. This demo computes both answers exactly and keeps them in separate fields, so a reader can see that the obstruction survives.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Integer homology class of the cycle and the Z/2Z result.
- The rational witness 1/2 for the declared rational problem.
- The integer minimum residual and both minimizers.
- Matrix certificates for a three-edge chain complex; hollow versus filled triangle.
- Rejection of averaged signed residuals presented as a zero-residual integer solution.

## Inputs

Default: the four worked exercises. `--input problem.json --proposal witness.json` grades a scalar or three-edge problem with a witness, minimum or kernel certificate. `rational_witness.json` is a sample proposal.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/integer_obstruction_lift/tests -q -p no:cacheprovider
python demos/integer_obstruction_lift/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000029/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "COMPUTED", ...}`, exit 0. `summary.md` reads "Exact scalar and matrix-certificate checks; no authorized carrier change or applied repair."

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 101 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Write a scalar problem file and a proposal; try a proposal that claims an integer zero residual; it should be rejected.

## Porting notes

No code changes beyond the move.

## Where the code lives

`demos/integer_obstruction_lift/` (`run.py`, `tests/`, and a short `README.md`).
