"""Tests for gates/gate_types.py: typing, negative controls, YAML parity.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

from pfp.infrastructure.contract_loading import load_gate_register_from_files
from pydantic import ValidationError

from pfp.domain.contracts import gate_types as gt

HERE = Path(__file__).resolve()
GATES = HERE.parents[2] / "infrastructure" / "yaml" / "gates"


def _raw() -> dict:
    return yaml.safe_load((GATES / "gate_register.yaml").read_text(encoding="utf-8"))


def test_register_yaml_validates() -> None:
    reg = gt.GateRegister.model_validate(_raw(), strict=False)
    assert (len(reg.primary_gates), len(reg.intergates), len(reg.empirical_gates)) == (22, 10, 3)


def test_register_yaml_parity_with_gate_files() -> None:
    from_files = load_gate_register_from_files(GATES)
    expected = gt.GateRegister.model_validate(from_files, strict=False)
    committed = gt.GateRegister.model_validate(_raw(), strict=False)
    assert committed == expected


def test_intergate_edges_resolve_to_primary_ordinals() -> None:
    reg = gt.GateRegister.model_validate(_raw(), strict=False)
    ords = {gt.gate_ordinal(g.gate_id) for g in reg.primary_gates}
    for ig in reg.intergates:
        assert gt.gate_ordinal(ig.transition_from) in ords
        assert gt.gate_ordinal(ig.transition_to) in ords


def test_readme_links_new_files() -> None:
    text = (GATES / "README.md").read_text(encoding="utf-8")
    assert "(gate_types.py)" in text and "(gate_register.yaml)" in text


def test_negative_missing_primary_gate() -> None:
    raw = _raw()
    raw["primary_gates"] = raw["primary_gates"][:-1]
    with pytest.raises(ValidationError):
        gt.GateRegister.model_validate(raw, strict=False)


def test_negative_intergate_count() -> None:
    raw = _raw()
    raw["intergates"] = raw["intergates"][:-1]
    with pytest.raises(ValidationError):
        gt.GateRegister.model_validate(raw, strict=False)


def test_negative_self_loop_intergate() -> None:
    entry = dict(_raw()["intergates"][0])
    entry["transition_to"] = entry["transition_from"]
    with pytest.raises(ValidationError):
        gt.Intergate.model_validate(entry, strict=False)


def test_negative_file_prefix_mismatch() -> None:
    entry = dict(_raw()["primary_gates"][0])
    entry["file"] = "02_nocebo_plunge.yaml"
    with pytest.raises(ValidationError):
        gt.PrimaryGate.model_validate(entry, strict=False)


def test_negative_gate_id_out_of_range() -> None:
    entry = dict(_raw()["primary_gates"][0])
    entry["gate_id"] = "PFP-23-SYNTAX-PREFILTER"
    with pytest.raises(ValidationError):
        gt.PrimaryGate.model_validate(entry, strict=False)


def test_negative_bad_comparison_operator() -> None:
    entry = dict(_raw()["empirical_gates"][0])
    entry["comparison_operator"] = "NEQ"
    with pytest.raises(ValidationError):
        gt.EmpiricalGate.model_validate(entry, strict=False)


def test_negative_authority_effect_and_extra() -> None:
    entry = dict(_raw()["primary_gates"][0])
    with pytest.raises(ValidationError):
        gt.PrimaryGate.model_validate({**entry, "authority_effect": "Grant"}, strict=False)
    with pytest.raises(ValidationError):
        gt.PrimaryGate.model_validate({**entry, "surplus": 1}, strict=False)
