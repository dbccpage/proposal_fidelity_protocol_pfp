# Finite Provenance

Checks a supplied event ledger of presentations (supply, mention, designate, admit) for internal consistency, and keeps record identity, string equality and observation profiles apart.

## What it shows

A task supplies presentation records, an ordered event ledger, a transition relation, observation tables and interpretation declarations. Two records can hold the same string; different strings need not differ on any observation. The relation is enumerated only at the queried seed: no outgoing edge means local quiescence, and a sole successor is one permitted successor, not an inevitable one. Admission must point back to an earlier matching supply event and the current designation.

## Why it matters for PFP

PFP keeps provenance explicit: where a piece of evidence came from, whether it was only mentioned or actually supplied, and whether it was admitted. This demo checks a ledger for those distinctions. It checks consistency of what was supplied; it does not authenticate an issuer or discover real history.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Successor enumeration at a seed, with fabricated successors rejected.
- Separate comparison of inscription strings and declared observation profiles.
- Ledger checks: supply before admit, current designation, unique receipt IDs, bound prior-event prefix.
- Interpretation lookups that return declared-not-validated or an explicit refusal for undeclared interpretations.

## Inputs

Default: three puzzles, a refusal trap and five drills. `--input file.json` checks your own task.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/finite_provenance/tests -q -p no:cacheprovider
python demos/finite_provenance/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000036/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "DEMONSTRATED", ...}`, exit 0.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 94 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Move an `admit` event before its `supply` event in a task file; the ledger check should refuse it.

## Porting notes

No code changes beyond the move.

## Where the code lives

`demos/finite_provenance/` (`run.py`, `tests/`, and a short `README.md`).
