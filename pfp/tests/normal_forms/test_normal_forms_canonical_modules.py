"""Canonical-module, property, security, and mutation-style coverage.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import importlib.util
from fractions import Fraction
from pathlib import Path

import pytest

from omega_engine_pfp.domain.normal_forms.contract_validation import validate_contract_dict
from omega_engine_pfp.domain.normal_forms.examples import order_line
from omega_engine_pfp.domain.normal_forms.reconciliation import verify_loss_ledger_integrity
from omega_engine_pfp.domain.normal_forms.relational import (
    FunctionalDependency,
    JoinDependency,
    compute_attribute_closure,
    find_candidate_keys,
)
from omega_engine_pfp.domain.normal_forms.tower_forms import verify_zfnf

DOMAIN = Path(__file__).resolve().parents[2] / "domain" / "normal_forms"
INFRASTRUCTURE = Path(__file__).resolve().parents[2] / "infrastructure" / "normal_forms"
CANONICAL_MODULES = {
    "asrf",
    "bqnf_fsign",
    "contract_validation",
    "quantum_forms",
    "reconciliation",
    "relational",
    "relational_advanced",
    "relational_extensions",
    "topology",
    "tower_forms",
}


def test_canonical_split_has_no_legacy_harness_or_oversized_module() -> None:
    assert importlib.util.find_spec("omega_engine_pfp.domain.normal_forms.harness") is None
    assert importlib.util.find_spec("omega_engine_pfp.infrastructure.normal_forms.nf_harness") is None
    assert not (INFRASTRUCTURE / "nf_examples.py").exists()
    for module in CANONICAL_MODULES:
        path = DOMAIN / f"{module}.py"
        assert path.is_file()
        assert len(path.read_text(encoding="utf-8").splitlines()) < 1_000


def test_domain_modules_have_no_outer_layer_or_wildcard_imports() -> None:
    forbidden = ("infrastructure", "use_cases", "controllers", "entrypoints")
    for module in CANONICAL_MODULES:
        tree = ast.parse((DOMAIN / f"{module}.py").read_text(encoding="utf-8"))
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert all(alias.name != "*" for node in imports for alias in node.names)
        assert all(not any(part in forbidden for part in (node.module or "").split(".")) for node in imports)


def test_relational_closure_is_monotone_on_example_schema() -> None:
    schema = order_line()
    smaller = frozenset({"OrderId"})
    larger = frozenset({"OrderId", "LineNo"})
    assert compute_attribute_closure(smaller, schema.dependencies) <= compute_attribute_closure(
        larger, schema.dependencies
    )
    assert find_candidate_keys(schema) == [larger]


@pytest.mark.parametrize(
    ("wire", "expected"),
    [
        ("*(AB;BC;AC)", ({"A", "B"}, {"B", "C"}, {"A", "C"})),
        ("⋈([A,B], [B,C], [A,C])", ({"A", "B"}, {"B", "C"}, {"A", "C"})),
    ],
)
def test_join_dependency_parser_delimiters_are_behaviorally_equivalent(
    wire: str, expected: tuple[set[str], ...]
) -> None:
    parsed = JoinDependency.from_str(wire)
    assert parsed.components == tuple(frozenset(component) for component in expected)


def test_fail_closed_security_and_mutation_branches() -> None:
    defects = validate_contract_dict({"schema_version": object()})
    assert defects
    with pytest.raises(ValueError, match="FloatContaminationRefusal"):
        verify_zfnf(0.5, Fraction(1, 2))
    ok, reason = verify_loss_ledger_integrity(
        {
            "erased_attributes": ["secret"],
            "sealed": True,
            "entries": [{"value": 1}],
            "record_count": 1,
            "merkle_digest": "0" * 64,
        }
    )
    assert ok is False
    assert reason is not None and "Digest mismatch" in reason


def test_functional_dependency_value_object_rejects_empty_sides() -> None:
    with pytest.raises(ValueError, match="Determinant"):
        FunctionalDependency(frozenset(), frozenset({"A"}))
    with pytest.raises(ValueError, match="Dependent"):
        FunctionalDependency(frozenset({"A"}), frozenset())
