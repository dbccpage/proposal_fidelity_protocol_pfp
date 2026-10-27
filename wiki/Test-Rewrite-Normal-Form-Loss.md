# Rewrite Normal Form Loss

A string rewrite system can reach two different normal forms, and even a joining normal form can erase information the original question needs.

## What it shows

With rules ab -> d and bc -> e, the word abc has two irreducible descendants, dc and ae. Picking one does not resolve the other branch. A separately named extended presentation adds dc -> e and ae -> e, so this peak joins at e; every rule shortens the word, so every reduction terminates. Under the extended rules abc and e share the normal form e, yet the count of letter a in the original inputs is 1 versus 0. That question cannot be answered from the normal form alone. Retaining the original bytes alongside the normal form makes the pair reversible.

## Why it matters for PFP

PFP tooling often normalizes proposals before comparing them. This demo shows the risk: normalization can merge inputs that differ on the question being asked. The fix it demonstrates is to keep the original bytes with a hash next to any normal form.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- All descendants of a word under the original and extended rule sets, bounded by `--max-states`.
- The set of irreducible normal forms and whether the displayed peak joins.
- A pair of inputs with equal normal forms but different answers to a counting query.
- A retained-original codec that round-trips exact bytes.

## Inputs

Default: the worked exercises. `--input word.txt --presentation original|extended` explores your own word (exact raw bytes; no trimming).

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/rewrite_normal_form_loss/tests -q -p no:cacheprovider
python demos/rewrite_normal_form_loss/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000030/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "COMPUTED", ...}`, exit 0. The summary states that original bytes remain separate from normal forms.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 76 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Add a rule to the extended presentation in `run.py` and rerun the tests to see which checks depend on the join. Feed the word `abcabc` to see how the state count grows.

## Porting notes

Two test inputs that use a Cyrillic look-alike letter were rewritten as `\u` escapes; the tested strings are identical. The demo does not run a full critical-pair analysis, so it makes no global confluence claim.

## Where the code lives

`demos/rewrite_normal_form_loss/` (`run.py`, `tests/`, and a short `README.md`).
