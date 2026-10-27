# Test: Tautological Assertion Lint

A test can pass without testing anything. `assert True` always passes, so does
`assert 10 <= 32`, and so does a `pytest.raises(ValueError)` block whose body is
just `raise ValueError(...)`. This demo is a small scanner that reads Python
test source as a syntax tree and reports those three patterns, plus a short
test suite that pins its behaviour. Ported from an internal test suite.

## Why it matters to PFP

In the Proposal Fidelity Protocol a check is only evidence for the property it
declares (see [Core Concepts](Core-Concepts.md)). A test that cannot fail
declares a property it never examines, so a green run built on it is not
evidence at all. When a proposer submits code together with its own tests, a
checker should refuse tests that certify themselves. This scanner is one cheap,
mechanical way to catch the most obvious cases before anything is run.

## What it checks

`find_tautological_assertions(source, filename="<source>")` parses the source
and returns a list of issue strings, one per problem, each prefixed with
`filename:line:`. It flags:

1. `assert <constant>`, such as `assert True` or `assert 1`
   ("Tautological assertion of constant").
2. `assert <literal> <op> <literal>`, where both sides are literals or
   literal-only expressions such as `[1, 2]` or `2 + 3`
   ("Tautological literal comparison in assert").
3. A `with ...raises(...)` block whose body (ignoring `pass`) is a single
   `raise` statement, so no code under test is executed
   ("Self-certifying pytest.raises block ...").

Source that does not parse returns a single `SyntaxError` issue instead.

The four tests feed one snippet for each pattern and expect exactly one issue,
then feed a well-formed test (`assert val.status == 'PASS'` and a `raises`
block that calls `val.execute()`) and expect none.

## How to run

From the repository root:

    python -m pytest demos/tautology_lint -q

Only the Python standard library and pytest are needed.

## Expected output

    ....                                                                     [100%]
    4 passed

## What a failure means

- One of the "detects" tests failing means the scanner missed a pattern it is
  meant to catch, or reported it more than once.
- `test_passes_valid_assertions` failing means the scanner raised a false
  alarm on an assertion that does depend on runtime values.

## How to modify it

- To scan a real file: `find_tautological_assertions(Path(p).read_text(), p)`.
- To add a pattern (for example `assert x == x`), add a branch in the
  `ast.Assert` case and a matching test with one positive and one negative
  snippet.
- The scanner is deliberately narrow. It does not try to decide whether a
  non-literal assertion is meaningful; it only removes the cases where the
  answer is obviously no.

## Where it lives

- Scanner: `demos/tautology_lint/tautology_lint.py`
- Tests: `demos/tautology_lint/test_tautology_lint.py`

Port notes: the import was changed to load the scanner from the same folder,
and an unused import was removed. The checks are unchanged.
