"""Tests for grammar/grammar_types.py and grammar_types.yaml.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

HERE = Path(__file__).resolve()
candidates = [
    *HERE.parents,
    *(p / "education/documentation/004_oepfp" for p in HERE.parents),
    *(p / "education/documentation/030_the_symbol_game_proposal_fidelity_protocol_pfp" for p in HERE.parents),
]
ROOT = next(p for p in candidates if (p / "grammar" / "grammar_types.py").is_file())
GRAMMAR = ROOT / "grammar"


def _load():
    name = "pfp_grammar_types_under_test"
    spec = importlib.util.spec_from_file_location(name, GRAMMAR / "grammar_types.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gt = _load()
SPEC = yaml.safe_load((GRAMMAR / "grammar_types.yaml").read_text(encoding="utf-8"))


def _entry(**kw):
    base = {"grammar_file": "a.ebnf", "profile_id": "a-v1", "start_symbol": "s", "scope": "x"}
    base.update(kw)
    return gt.GrammarProfileEntry(**base)


def test_yaml_registry_validates_and_matches_files():
    reg = gt.GrammarRegistry(
        governing_standard=SPEC["governing_standard"],
        profiles=[gt.GrammarProfileEntry(**p) for p in SPEC["profiles"]],
    )
    assert len(reg.profiles) == 6
    for p in reg.profiles:
        assert (GRAMMAR / p.grammar_file).is_file()


def test_yaml_authority_effect_none():
    assert SPEC["authority_effect"] == "None"


def test_alphabet_parity():
    assert SPEC["alphabets"]["sigma36"] == gt.SIGMA36
    assert SPEC["alphabets"]["gamma38"] == gt.GAMMA38
    assert len(gt.SIGMA36) == 36 and len(gt.GAMMA38) == 38


def test_verdict_enum_parity():
    assert [v.value for v in gt.ConformanceVerdict] == SPEC["conformance_verdicts"]


def test_readme_inventory_parity():
    readme = (GRAMMAR / "README.md").read_text(encoding="utf-8")
    for p in SPEC["profiles"]:
        assert f"`{p['profile_id']}`" in readme
        assert f"`{p['start_symbol']}`" in readme


def test_pfp_cases_parse():
    cases = json.loads((GRAMMAR / "pfp_conformance_cases.json").read_text(encoding="utf-8"))
    parsed = [gt.PfpConformanceCase(**c) for c in cases]
    assert len(parsed) == 28
    assert len({c.id for c in parsed}) == len(parsed)


def test_profile_cases_parse():
    cases = json.loads((GRAMMAR / "conformance_cases.json").read_text(encoding="utf-8"))
    parsed = [gt.ProfileConformanceCase(**c) for c in cases]
    assert parsed and len({c.id for c in parsed}) == len(parsed)
    assert parsed[0].verdict is gt.ConformanceVerdict.ACCEPT


def test_negative_extra_field_rejected():
    with pytest.raises(ValidationError):
        gt.PfpConformanceCase(id="X1", start="p", text="<>", accept=True, extra=1)


def test_negative_accept_must_be_bool():
    with pytest.raises(ValidationError):
        gt.PfpConformanceCase(id="X1", start="p", text="<>", accept=1)


def test_negative_uppercase_grammar_file():
    with pytest.raises(ValidationError):
        _entry(grammar_file="PFP.ebnf")


def test_negative_authority_effect():
    with pytest.raises(ValidationError):
        _entry(authority_effect="Granted")


def test_negative_duplicate_profile():
    e = _entry()
    with pytest.raises(ValidationError):
        gt.GrammarRegistry(governing_standard="g", profiles=[e, e])


def test_negative_frozen():
    e = _entry()
    with pytest.raises(ValidationError):
        e.scope = "y"
