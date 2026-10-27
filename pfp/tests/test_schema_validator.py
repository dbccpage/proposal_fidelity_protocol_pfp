"""Optional schema-engine availability must never turn into validation success."""

from __future__ import annotations

import builtins
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from pfp.infrastructure.schema_validator import (
    PfpSchemaValidatorAdapter,
)


def test_core_import_without_optional_schema_engine():
    root = Path(__file__).resolve().parents[2]
    probe = """
import builtins
import sys
original_import = builtins.__import__
def without_jsonschema(name, *args, **kwargs):
    if name == 'jsonschema' or name.startswith('jsonschema.'):
        raise ModuleNotFoundError("No module named 'jsonschema'")
    return original_import(name, *args, **kwargs)
builtins.__import__ = without_jsonschema
from pfp.infrastructure.pilot_runner import build_requests
requests = build_requests('import_probe', 'linear_algebra')
if not requests:
    raise RuntimeError('Core pilot import did not produce requests')
from pfp.infrastructure.pilot_runner import build_p_star_yaml
build_p_star_yaml('IMPORT_PROBE', 'linear_algebra')
from pfp.infrastructure.schema_validator import PfpSchemaValidatorAdapter
validation = PfpSchemaValidatorAdapter.validate_payload({'type': 'object', 'additionalProperties': False}, {})
if validation.is_valid or validation.errors != ["ValidatorException: No module named 'jsonschema'"]:
    raise RuntimeError('Missing schema engine allowed a contract check')

"""
    result = subprocess.run(
        [sys.executable, "-c", probe], cwd=root, capture_output=True,
        text=True, timeout=45, check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("payload", [{"answer": 3}, {"answer": "invalid"}])
def test_missing_schema_engine_fails_closed(monkeypatch, payload):
    original_import = builtins.__import__

    def without_jsonschema(name, *args, **kwargs):
        if name == "jsonschema" or name.startswith("jsonschema."):
            raise ModuleNotFoundError("No module named 'jsonschema'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_jsonschema)
    schema = {"$id": "availability_probe", "type": "object"}
    result = PfpSchemaValidatorAdapter.validate_payload(schema, payload)
    assert result.is_valid is False
    assert result.schema_id == "availability_probe"
    assert result.errors == ["ValidatorException: No module named 'jsonschema'"]
    assert result.authority_effect == "None"


@pytest.mark.skipif(importlib.util.find_spec("jsonschema") is None, reason="Optional jsonschema engine is not installed")
@pytest.mark.parametrize("payload, valid", [({"answer": 3}, True), ({"answer": "3"}, False), ({"extra": 3}, False)])
def test_installed_schema_engine_enforces_contract(payload, valid):
    schema = {
        "type": "object", "additionalProperties": False, "required": ["answer"],
        "properties": {"answer": {"type": "integer"}},
    }
    result = PfpSchemaValidatorAdapter.validate_payload(schema, payload, schema_id="contract_probe")
    assert result.is_valid is valid
    assert bool(result.errors) is not valid
