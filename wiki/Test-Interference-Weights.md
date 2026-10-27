# Interference Weights

Two quantum states with identical measurement probabilities give opposite results after a Hadamard gate, so probability weights alone cannot predict interference.

## What it shows

The states (1,1)/sqrt(2) and (1,-1)/sqrt(2) both have computational-basis probabilities (1/2, 1/2). After the explicitly admitted Hadamard operator they become (1,0) and (0,1). A global minus sign gives (-1,0), which has the same probabilities as (1,0). For supplied nonnegative weights a chosen square-root lift reproduces w_i/W by construction; that is a phase convention, not a reconstruction of phase. All arithmetic is exact; nothing is rounded to floating point.

## Why it matters for PFP

A proposal can look right because a summary statistic matches. PFP checks the full declared object. Here the summary (probabilities) matches while the object (amplitudes) differs, and the difference changes an observable outcome. The demo also refuses to treat a by-construction identity as an independent experimental result.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Exact post-Hadamard amplitudes for the plus and minus states and for complex global phases such as i.
- Equality of the initial probabilities and inequality of the amplitudes.
- A square-root lift of supplied weights and its Born probabilities, with negative weights and zero total refused.
- Grading of proposed probabilities against the exact calculation.

## Inputs

Default: the worked exercises. `--input problem.json --proposal probabilities.json` checks a proposal. `phase_i.json` and `prediction.json` are sample inputs.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/interference_weights/tests -q -p no:cacheprovider
python demos/interference_weights/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000031/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "COMPUTED", ...}`, exit 0. The summary names the Born and Hadamard rules as imported assumptions.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 64 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Write a state with phase i on the second component and compare its post-Hadamard amplitudes with the plus state. A mutation test shows what happens if the code takes absolute values too early.

## Porting notes

No code changes beyond the move. This is arithmetic in a declared model, not a quantum-computer experiment.

## Where the code lives

`demos/interference_weights/` (`run.py`, `tests/`, and a short `README.md`).
