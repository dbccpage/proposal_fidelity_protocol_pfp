# Role Submission Comparison

Compares two frozen role submissions about the same task literally, preserves disagreements, and runs a separate finite check before any claim is promoted.

## What it shows

A task holds a claim ID, a proposition, required input names and supplied text. Two roles, Red and Green, each submit a tag, a stance, observations and an optional revised task. A comparator (Blue) checks them field by field without treating similar prose as equal, and keeps both sides of every disagreement. Propositions are either opaque text or the exact finite predicate `sum(left) <= sum(right)` on bounded integers, which the host can actually check.

## Why it matters for PFP

PFP uses several roles to review a proposal, but agreement between roles is not evidence. Only a host check can move a claim from unverified to checked. This demo makes that concrete: consensus alone produces a refusal, opaque claims stay unverified even when everyone agrees, and requests for global action authority are refused even after a passing check.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Canonical task digests that both submissions must name.
- Literal field comparison with preserved disagreements and original and revised tasks.
- The finite integer predicate check giving `CHECKED` or `CONTRADICTED`.
- Refusal (`ref<2>`) of consensus-only promotion and of action-authority requests.
- Retention of eight contextual tags (for example STANDARD, DERIVED, CONJECTURE) without letting them change computed truth.

## Inputs

Default: the worksheet puzzles and drills. `--input file.json` supplies a task, Red, Green, a requested status and a host-check switch.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/role_submission_comparison/tests -q -p no:cacheprovider
python demos/role_submission_comparison/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000035/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 121 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Make Red and Green agree on an opaque claim and request promotion; the result stays `UNVERIFIED`. Change one integer in the predicate so the sum comparison flips to `CONTRADICTED`.

## Porting notes

A comment that pointed at the original README was reworded to point at the original worksheet. No behavior changes.

## Where the code lives

`demos/role_submission_comparison/` (`run.py`, `tests/`, and a short `README.md`).
