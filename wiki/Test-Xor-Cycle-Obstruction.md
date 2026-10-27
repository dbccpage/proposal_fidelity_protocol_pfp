# XOR Cycle Obstruction

Local edge constraints on an odd three-cycle can each be satisfied while no global 0/1 assignment satisfies all of them; the checker finds the obstruction and every least-cost repair.

## What it shows

Three vertices a, b, c carry values 0 or 1, and each cycle edge demands a parity (XOR) between its endpoints. Every single edge has a local witness, but the three demands together are inconsistent: the sum of the right-hand sides around the cycle is odd. The demo enumerates all eight assignments, reports zero global solutions, and lists all three one-edge repairs of minimum cost instead of picking one silently.

## Why it matters for PFP

A proposal that reports one repair as if it were the only one hides a choice. PFP asks the host to recompute the complete answer set and compare it with what the proposal claims. This demo is a small, exact instance of that rule: local consistency does not imply global consistency, and an incomplete repair set is a defect even when each listed repair is valid.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- All 2^3 assignments and the count that satisfy every edge (0 for the odd cycle).
- A local witness for each edge on its own.
- All least-cost one-edge repairs (cost 1, three of them).
- A consistent cyclic relabeling of the vertices, checked for equivalence.
- Grading of an optional candidate JSON report against host recomputation, including problem digest, edge coverage, witnesses and the full repair set.

## Inputs

With no arguments the original odd cycle is used. `--input problem.json` supplies another problem and `--proposal report.json` a candidate report to grade. Input files are strict UTF-8 JSON of at most 65,536 bytes; duplicate keys, non-finite numbers, booleans or floats as bits, undeclared vertices and missing or duplicate edges are refused.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/xor_cycle_obstruction/tests -q -p no:cacheprovider
python demos/xor_cycle_obstruction/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000026/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "COMPUTED", "output": "..."}` and exit code 0. `summary.md` reports checked edges ab, bc, ca, zero global assignments and minimum repair cost 1. A graded proposal yields `ACCEPTED` (exit 0) or `REJECTED` (exit 1); unreadable input is `REFUSED` (exit 2).

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 67 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Change the right-hand sides in a problem file so their sum is even and the checker should report global assignments. Edit `tests/test_cycle.py` to add a cycle relabeling or a proposal that omits one repair; the grading test should reject it.

## Porting notes

One test (`test_deep_json_returns_controlled_refusal`) was adapted: on Python 3.14 a 7,000-level nested JSON array parses without a `RecursionError`, so it reaches validation and is rejected there (exit 1) instead of refused before parsing (exit 2). The test now accepts either controlled outcome and still requires that no crash occurs.

## Where the code lives

`demos/xor_cycle_obstruction/` (`run.py`, `tests/`, and a short `README.md`).
