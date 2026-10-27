# Grammar Profiles

Recognizes a submitted packet under one named syntax profile without trimming, repairing or reinterpreting its bytes, and keeps syntax acceptance separate from meaning.

## What it shows

Four small bracket-packet grammars are implemented as named profiles: `mss-boundary-v1`, `historical-packet-v1`, `quiz-packet-v1` and `glyph-graph-v1`. Given raw bytes and a profile, the recognizer accepts only if the whole document matches. Leading or trailing whitespace, a byte-order mark, a NUL byte, a trailing root, empty items and look-alike non-ASCII letters are rejected rather than cleaned up. A reference EBNF interpreter in `tests/ebnf_reference.py` cross-checks the hand-written recognizers against grammar files.

## Why it matters for PFP

PFP packets travel as exact bytes. If a host silently trims or repairs input, the bytes it checks are not the bytes the model sent, and hashes no longer bind the evidence. This demo makes the rule testable: select the grammar explicitly, recognize the complete input, and report syntax acceptance without claiming the content is true.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Whole-document recognition for each of four profiles.
- SHA-256 of the raw bytes, recorded with the verdict.
- Refusal of whitespace, BOM, control bytes and homoglyphs (a Cyrillic letter that looks like `a`).
- Agreement with a generic EBNF reference over shared conformance cases (`tests/conformance_cases.json`).

## Inputs

Default: the worked exercises. `--input packet.bin --profile <name>` checks your own raw bytes (not JSON).

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/grammar_profiles/tests -q -p no:cacheprovider
python demos/grammar_profiles/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000028/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "COMPUTED", ...}`, exit 0. `summary.md` states that only bounded syntax recognition was performed.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 117 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Write a packet such as `<a<b>>` to a file and try each profile. Add rows to `tests/conformance_cases.json` to extend the cross-check; both the recognizer and the EBNF reference must agree.

## Porting notes

The homoglyph test inputs were rewritten as `\u0430` escapes so the source files are pure ASCII; the bytes under test are identical.

## Where the code lives

`demos/grammar_profiles/` (`run.py`, `tests/`, and a short `README.md`).
