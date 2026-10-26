"""Executable examples use the retained data catalog after Python relocation."""

import importlib
import json

import pytest

from omega_engine_pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR


@pytest.mark.parametrize(
    "module_name",
    [
        "paid_revenue_example",
        "unverified_certificate_example",
        "observer_freshness_example",
        "reconciliation_example",
    ],
)
def test_example_data_is_readable_from_declared_resource_home(module_name):
    module = importlib.import_module(
        "omega_engine_pfp.infrastructure.normal_forms." + module_name
    )
    assert module.DATA_PATH.parent == NORMAL_FORMS_DIR / "data"
    assert json.loads(module.DATA_PATH.read_text(encoding="utf-8"))


def test_retained_evaluator_loads_contracts_from_current_resources(tmp_path):
    from omega_engine_pfp.infrastructure.normal_forms.nf_evaluator import NormalFormsEvaluator

    contract = NormalFormsEvaluator._resolve_contract("nf.derivation.pdnf")
    assert contract["identity"]["id"] == "nf.derivation.pdnf"
    override = tmp_path / "explicit.yaml"
    override.write_text('identity: {id: custom}\n', encoding="utf-8")
    assert NormalFormsEvaluator._resolve_contract("absent", override)["identity"]["id"] == "custom"
    with pytest.raises(FileNotFoundError, match="Cannot resolve contract YAML"):
        NormalFormsEvaluator._resolve_contract("absent")


def test_parser_defaults_share_the_declared_resource_catalog():
    from omega_engine_pfp.infrastructure.normal_forms import contract_paths, nf_contract_parser

    for name in ("CONTRACTS_DIR", "INDEX_PATH", "STANDARD_PATH", "SCHEMA_V1_PATH"):
        path = getattr(nf_contract_parser, name)
        assert path == getattr(contract_paths, name)
        assert path.exists()
