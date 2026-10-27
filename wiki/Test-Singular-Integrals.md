# Singular Integrals

Computes integrals of c/(x-p) exactly, distinguishes a divergent improper integral from a Cauchy principal value, and checks supplied before/after states.

## What it shows

Inputs declare rationals a < b, p and c != 0, with f(x) = c/(x-p). With the pole outside [a, b] the integral is c ln(|b-p|/|a-p|). With an interior pole the two one-sided limits diverge to opposite infinities, so the ordinary improper integral does not exist. The principal value, using the same cutoff on both sides, is c ln(R/L) where L = p-a and R = b-p. Any fixed ratio of cutoffs gives its own finite limit, so the answer depends on a declared limiting procedure.

## Why it matters for PFP

A proposal that cancels two infinities and reports a number has hidden a choice. PFP asks that every such choice be declared. This demo reports which procedure produced each value and rejects forged answers. It also replays declared teaching routes from a start state to an end state.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Proper integrals with the pole outside the interval, as exact log expressions.
- Divergence classification for interior and endpoint poles.
- Principal values and paired-cutoff limits.
- Nine worksheet rows, two route replays, four controls and four counterexamples (forged answers expected to be `MISMATCH`).

## Inputs

Default: the worksheet. `--input file.json` supplies a request and proposal to grade.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/singular_integrals/tests -q -p no:cacheprovider
python demos/singular_integrals/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000038/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 103 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Set p to the midpoint of [a, b] and confirm the principal value is zero. Change the cutoff ratio to see the limit change.

## Porting notes

No code changes beyond the move. Some tests write into the default output root (see below).

## Where the code lives

`demos/singular_integrals/` (`run.py`, `tests/`, and a short `README.md`).
