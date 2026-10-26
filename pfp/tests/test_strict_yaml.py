"""Tests for fail-closed StrictYamlLoader and YAML 1.2 boolean / duplicate key invariants.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from omega_engine_pfp.domain.types.base import PfpBaseModel, PfpDomainModel
from omega_engine_pfp.infrastructure.model_loading import load_yaml_model
from omega_engine_pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from omega_engine_pfp.infrastructure.yaml_loading import (
    StrictYamlError,
    strict_yaml_load,
    strict_yaml_load_all,
)


class DummyModel(PfpBaseModel):
    key: str | bool
    count: int = 0


class DummyDomainModel(PfpDomainModel):
    name: str
    flag: bool = False


# =============================================================================
# DUPLICATE KEY REJECTION TESTS
# =============================================================================

def test_strict_yaml_loader_rejects_top_level_duplicate_keys():
    doc = """
    alpha: 1
    beta: 2
    alpha: 3
    """
    with pytest.raises((StrictYamlError, ValueError), match="duplicate key|Duplicate key"):
        strict_yaml_load(doc)


def test_strict_yaml_loader_rejects_nested_duplicate_keys():
    doc = """
    parent:
      child_a: 10
      child_b: 20
      child_a: 30
    """
    with pytest.raises((StrictYamlError, ValueError), match="duplicate key|Duplicate key"):
        strict_yaml_load(doc)


def test_strict_yaml_loader_accepts_unique_keys():
    doc = """
    alpha: 1
    beta: 2
    nested:
      child_a: 10
      child_b: 20
    """
    data = strict_yaml_load(doc)
    assert data == {
        "alpha": 1,
        "beta": 2,
        "nested": {"child_a": 10, "child_b": 20},
    }


def test_strict_yaml_loader_load_all():
    doc = "doc1:\n  key1: val1\n---\ndoc2:\n  key2: val2\n"
    docs = list(strict_yaml_load_all(doc))
    assert len(docs) == 2
    assert docs[0] == {"doc1": {"key1": "val1"}}
    assert docs[1] == {"doc2": {"key2": "val2"}}


# =============================================================================
# BOOLEAN COERCION REJECTION TESTS (YAML 1.1 vs 1.2 PARITY)
# =============================================================================

@pytest.mark.parametrize("scalar", [
    "yes", "no", "on", "off",
    "Yes", "No", "On", "Off",
    "YES", "NO", "ON", "OFF",
])
def test_strict_yaml_loader_rejects_unquoted_yaml11_booleans(scalar: str):
    doc = f"flag: {scalar}\n"
    with pytest.raises((StrictYamlError, ValueError), match="forbidden|unquoted"):
        strict_yaml_load(doc)


@pytest.mark.parametrize("scalar", [
    "yes", "no", "on", "off", "y", "n",
    "Yes", "No", "On", "Off", "Y", "N",
    "YES", "NO", "ON", "OFF",
])
def test_strict_yaml_loader_accepts_quoted_yaml11_strings(scalar: str):
    doc = f'flag: "{scalar}"\n'
    data = strict_yaml_load(doc)
    assert data == {"flag": scalar}
    assert isinstance(data["flag"], str)

    # Single quotes
    doc_sq = f"flag: '{scalar}'\n"
    data_sq = strict_yaml_load(doc_sq)
    assert data_sq == {"flag": scalar}
    assert isinstance(data_sq["flag"], str)


@pytest.mark.parametrize("scalar, expected", [
    ("true", True),
    ("false", False),
    ("True", True),
    ("False", False),
    ("TRUE", True),
    ("FALSE", False),
])
def test_strict_yaml_loader_accepts_strict_yaml12_booleans(scalar: str, expected: bool):
    doc = f"flag: {scalar}\n"
    data = strict_yaml_load(doc)
    assert data == {"flag": expected}
    assert isinstance(data["flag"], bool)


# =============================================================================
# INTEGRATION WITH STORAGE, MODEL LOADING, AND DOMAIN TYPES
# =============================================================================

def test_pfp_base_model_from_yaml_duplicate_key_rejection():
    doc = """
    key: "value1"
    key: "value2"
    """
    with pytest.raises((StrictYamlError, ValueError)):
        DummyModel.from_yaml(doc)


def test_pfp_base_model_from_yaml_unquoted_boolean_rejection():
    doc = """
    key: yes
    """
    with pytest.raises((StrictYamlError, ValueError)):
        DummyModel.from_yaml(doc)


def test_pfp_domain_model_from_yaml_duplicate_key_rejection():
    doc = """
    name: "first"
    name: "second"
    """
    with pytest.raises((StrictYamlError, ValueError)):
        DummyDomainModel.from_yaml(doc)


def test_pfp_domain_model_from_yaml_unquoted_boolean_rejection():
    doc = """
    name: "test"
    flag: on
    """
    with pytest.raises((StrictYamlError, ValueError)):
        DummyDomainModel.from_yaml(doc)


def test_load_yaml_model_duplicate_key_rejection():
    doc = """
    key: "value1"
    key: "value2"
    """
    with pytest.raises((StrictYamlError, ValueError)):
        load_yaml_model(DummyModel, doc)


def test_load_yaml_model_unquoted_boolean_rejection():
    doc = """
    key: no
    """
    with pytest.raises((StrictYamlError, ValueError)):
        load_yaml_model(DummyModel, doc)


def test_storage_adapter_duplicate_key_rejection(tmp_path: Path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("a: 1\na: 2\n", encoding="utf-8")
    adapter = PfpFileSystemStorageAdapter(data_root=Path("omega_engine_pfp/infrastructure/yaml"))
    with pytest.raises((StrictYamlError, ValueError)):
        adapter._load_yaml(bad_yaml)


# =============================================================================
# WHOLE REPOSITORY YAML REPERTOIRE SCAN TEST
# =============================================================================

def test_all_infrastructure_yaml_files_pass_strict_loading():
    yaml_dir = Path("omega_engine_pfp/infrastructure/yaml")
    assert yaml_dir.is_dir(), f"Missing yaml directory at {yaml_dir}"
    yaml_files = list(yaml_dir.rglob("*.yaml"))
    assert len(yaml_files) >= 200, f"Expected >= 200 YAML files, found {len(yaml_files)}"

    failures = []
    for p in yaml_files:
        try:
            content = p.read_text(encoding="utf-8")
            for _ in strict_yaml_load_all(content):
                pass
        except Exception as e:
            failures.append((str(p.relative_to(yaml_dir)), str(e)))

    assert len(failures) == 0, f"Found {len(failures)} YAML files that failed strict loading: {failures}"
