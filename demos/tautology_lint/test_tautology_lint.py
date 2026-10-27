"""Tests for AST test sensitivity and anti-tautology validator. AuthorityEffect: None."""

from __future__ import annotations

from tautology_lint import find_tautological_assertions


def test_detects_literal_comparison() -> None:
    code = "def test_bad():\n    assert 10 <= 32\n"
    issues = find_tautological_assertions(code)
    assert len(issues) == 1
    assert "Tautological literal comparison" in issues[0]


def test_detects_constant_assert() -> None:
    code = "def test_bad():\n    assert True\n"
    issues = find_tautological_assertions(code)
    assert len(issues) == 1
    assert "Tautological assertion of constant" in issues[0]


def test_detects_manual_raise_in_pytest_raises() -> None:
    code = "def test_bad():\n    with pytest.raises(ValueError):\n        raise ValueError('forced')\n"
    issues = find_tautological_assertions(code)
    assert len(issues) == 1
    assert "Self-certifying pytest.raises block" in issues[0]


def test_passes_valid_assertions() -> None:
    code = "def test_good(val):\n    assert val.status == 'PASS'\n    with pytest.raises(ValueError):\n        val.execute()\n"
    issues = find_tautological_assertions(code)
    assert len(issues) == 0
