"""Focused unit, integration, security, and mutation-style BQNF boundary tests."""

from __future__ import annotations

import ast
from pathlib import Path

from omega_engine_pfp.domain.normal_forms.bqnf_validator import (
    BqnfBoundary,
    BqnfCdcEvent,
    BqnfValidator,
)
from omega_engine_pfp.domain.normal_forms.fixture_ports import parse_bqnf_fixture_payload
from omega_engine_pfp.infrastructure.normal_forms.bqnf_fixture_loader import (
    JsonYamlBqnfFixtureLoader,
)


def test_pure_fixture_parser_normalizes_supported_envelopes() -> None:
    direct = parse_bqnf_fixture_payload([{"case_id": "direct"}])
    enveloped = parse_bqnf_fixture_payload({"fixtures": [{"case_id": "wrapped"}]})

    assert direct.unwrap() == ({"case_id": "direct"},)
    assert enveloped.unwrap() == ({"case_id": "wrapped"},)


def test_pure_fixture_parser_refuses_non_mapping_cases() -> None:
    refusal = parse_bqnf_fixture_payload({"fixtures": ["not-a-case"]})

    assert refusal.is_err
    assert refusal.unwrap_err().code == "BQNF_FIXTURE_CASE_REFUSED"


def test_adapter_loads_json_and_yaml(tmp_path: Path) -> None:
    json_path = tmp_path / "cases.json"
    yaml_path = tmp_path / "cases.yaml"
    json_path.write_text('[{"case_id":"json"}]', encoding="utf-8")
    yaml_path.write_text("fixtures:\n  - case_id: yaml\n", encoding="utf-8")
    loader = JsonYamlBqnfFixtureLoader()

    assert loader.load(str(json_path)).unwrap()[0]["case_id"] == "json"
    assert loader.load(str(yaml_path)).unwrap()[0]["case_id"] == "yaml"


def test_adapter_fails_closed_for_missing_and_malicious_yaml(tmp_path: Path) -> None:
    loader = JsonYamlBqnfFixtureLoader()
    malicious = tmp_path / "unsafe.yaml"
    malicious.write_text("!!python/object/apply:os.system ['echo unsafe']", encoding="utf-8")

    assert (
        loader.load(str(tmp_path / "missing.json")).unwrap_err().code == "BQNF_FIXTURE_READ_REFUSED"
    )
    assert loader.load(str(malicious)).unwrap_err().code == "BQNF_FIXTURE_PARSE_REFUSED"


def test_domain_validator_has_no_fixture_io_imports() -> None:
    module_path = Path(BqnfValidator.__module__.replace(".", "/") + ".py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert not imports.intersection({"json", "yaml", "pathlib", "Path"})


def test_typed_evaluation_boundary_refuses_malformed_numeric_value() -> None:
    boundary = BqnfBoundary(attributes=("amount",), aggregates=("SUM(amount)",))
    event = BqnfCdcEvent(op="INSERT", relation="orders", new={"amount": object()})

    outcome = BqnfValidator.evaluate_result(boundary, event)

    assert outcome.is_err
    assert outcome.unwrap_err().code == "BQNF_EVALUATION_REFUSED"


def test_missing_evidence_mutant_cannot_be_certified() -> None:
    boundary = BqnfBoundary(attributes=("amount",), aggregates=("SUM(amount)",))
    missing = BqnfCdcEvent(op="INSERT", relation="orders", new={})
    complete = BqnfCdcEvent(op="INSERT", relation="orders", new={"amount": 4})

    missing_result = BqnfValidator.evaluate(boundary, missing)
    complete_result = BqnfValidator.evaluate(boundary, complete)

    assert (missing_result.certified, missing_result.evidence_sufficient) == (False, False)
    assert (complete_result.certified, complete_result.evidence_sufficient) == (True, True)
