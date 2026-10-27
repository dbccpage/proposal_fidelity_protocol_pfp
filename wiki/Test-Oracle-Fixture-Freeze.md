# Test: Oracle Fixture Freeze

When code is re-implemented in another language, the old implementation can
serve as an oracle: you record exactly what it does on a fixed set of inputs,
freeze that record before writing the new code, and require the new code to
reproduce it byte for byte. This demo contains three such freezers for
Python behaviours that are easy to get subtly wrong, and a test that checks
the freezers themselves are deterministic and truthful.

## What it tests

- `freeze_python_case.py`: full-string `upper()` and `lower()` for 20 tricky
  strings (German sharp s, ligatures, Turkish dotted i, combining accents,
  Greek final sigma), every Unicode scalar whose case mapping changes, the
  "cased" and "case-ignorable" sets that decide the final-sigma rule, and
  SHA-256 fingerprints over all 1.1 million scalar values. With
  `--emit-data` it also writes the same tables as Rust constants.
- `freeze_python_repr.py`: `repr()` of 19 strings (quotes, backslashes,
  control characters, non-breaking and zero-width spaces, private-use and
  emoji characters) and a fingerprint of `repr(chr(c))` for every scalar.
- `freeze_json_acceptance.py`: `bool(json.loads(raw))` for 21 edge-case JSON
  values, and a digest of `json.dumps()` over 262,144 floats generated from
  a seeded 64-bit generator (so NaN, infinities, subnormals and negative zero
  all appear).

`test_oracle_fixture_freeze.py` runs each freezer twice into a temporary
folder and checks:

- the two runs produce identical bytes;
- every recorded vector equals what the running interpreter returns;
- known facts hold: `"ß".upper() == "SS"`, `"ΟΣ".lower()` ends in the final
  sigma `ς`, `[null]` is truthy while `[]`, `""`, `0` and `-0.0` are falsy;
- a different seed gives a different float digest;
- the casing freezer refuses to run on any Unicode version other than 15.0.0
  and writes nothing.

## Why it matters to PFP

PFP prefers claims that are checked against a frozen, hashed reference over
claims that "it behaves the same". Freezing the oracle before the port is
written means the port cannot quietly redefine what "correct" means. The
digests let a reviewer confirm the reference with one comparison. See
[Core Concepts](Core-Concepts.md) for how receipts and digests are used.

## Setup and inputs

No inputs beyond the Python standard library. The casing oracle is pinned
to Unicode 15.0.0, which is what Python 3.12 ships; Python 3.13 and later
use newer Unicode tables, so on those versions that one test is skipped and
the refusal test runs instead.

## How to run

From the repository root:

    py -3.12 -m pytest demos/oracle_fixture_freeze -q

To write the fixtures to a folder:

    py -3.12 demos/oracle_fixture_freeze/freeze_python_case.py --out oracle_fixtures --emit-data
    python demos/oracle_fixture_freeze/freeze_python_repr.py --out oracle_fixtures
    python demos/oracle_fixture_freeze/freeze_json_acceptance.py --out oracle_fixtures

On a machine without the `py` launcher, use any Python 3.12 interpreter.

## Expected output

With Python 3.12: `3 passed, 1 skipped` in about 15 seconds (the full scalar
scans take most of that). With Python 3.13 or later: `3 passed, 1 skipped`,
where the skipped test is the casing freeze. The scripts each print a one-line
summary and the path they wrote. On Python 3.12 the casing and repr fixtures
are byte-identical to the ones the internal suite froze.

## What a failure means

- Non-identical runs: something in a freezer depends on ordering or state
  that is not fixed (for example, iterating a set).
- A vector mismatch: the fixture no longer describes the interpreter, so a
  native port checked against it would be checked against the wrong thing.
- A changed digest between Python versions is expected for repr and float
  output only if that version changed the behaviour; compare the vectors to
  find out what moved.

## How to modify it

Add strings to `TEXTS`, `SAMPLES` or `RAWS` to cover a new edge case, then
re-run the test. To freeze a new behaviour, copy one freezer: compute a
payload, write it with `newline="\n"`, and add a determinism and
self-consistency test.

## Port notes

Ported from an internal test suite, where these scripts wrote straight into
a Rust crate's fixture folder. Here they take an `--out` folder instead and
expose a `freeze()` function; the computed content is unchanged. The test
file is new to this repository. Three related freezers became one page.

## Location

`demos/oracle_fixture_freeze/`.
