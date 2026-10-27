# Normalization Readout

Normalizing three weights and checking a square-root lift is exact arithmetic; it is not a derivation of a measurement law.

## What it shows

Weights (2,1,0) normalize to (2/3,1/3,0). A declared nonnegative square-root lift has those rational radicands, and squaring recovers the same probabilities by construction. The demo checks a submitted total, probability vector and lift radicands against the original weights; a false radicand is rejected even when the proposed probabilities sum to one. Two representations, simplex with identity readout and square-root with squared-magnitude readout, give the same vector, which does not make either unique.

## Why it matters for PFP

PFP separates what was computed from what was assumed. The tempting error here is to present a normalization identity as evidence for a physical law. The demo keeps the Born interpretation as an explicit assumption field: without it, amplitude readouts are arithmetic only.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Exact normalization of nonnegative integer weights, with negative weights and booleans refused.
- A lift certificate check binding radicands to the original weights.
- Amplitude readout for normalized amplitudes, with and without the declared assumption.
- Refusal of an ordinary-sum normalization where a squared norm is required.

## Inputs

Default: the worked exercises. `--input problem.json --proposal proposal.json` grades your own. Samples: `amplitudes.json`, `amplitude_prediction.json`, `lift_certificate.json`.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/normalization_readout/tests -q -p no:cacheprovider
python demos/normalization_readout/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000032/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "COMPUTED", ...}`, exit 0. The summary says the Born interpretation is an explicit assumption.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 72 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Edit `lift_certificate.json` so one radicand is wrong and grade it; the check should fail on `lift_radicands_match_weights`.

## Porting notes

No code changes beyond the move. Pairs with [Interference Weights](Test-Interference-Weights.md).

## Where the code lives

`demos/normalization_readout/` (`run.py`, `tests/`, and a short `README.md`).
