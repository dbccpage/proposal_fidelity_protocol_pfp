# Tautological assertion lint

A small AST scanner that flags test code which cannot fail: `assert True`,
`assert 10 <= 32`, and `pytest.raises` blocks whose only statement is a manual
`raise`. Ported from an internal test suite. Standard library only.

Run from the repository root:

    python -m pytest demos/tautology_lint -q

Expected: `4 passed`.

Files: `tautology_lint.py` (the scanner), `test_tautology_lint.py` (its tests).
Wiki page: Test-Tautological-Assertion-Lint.
