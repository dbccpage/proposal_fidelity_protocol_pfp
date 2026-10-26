"""Tests for schemas/schema_register.py: typing, negative controls, parity.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from omega_engine_pfp.infrastructure.contract_loading import load_schema_register_from_files
from pydantic import ValidationError

from omega_engine_pfp.domain.contracts import schema_register as sr

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2] / "infrastructure" / "yaml"
SCHEMAS = ROOT / "schemas"


def _raw() -> dict:
    return yaml.safe_load((SCHEMAS / "schema_register.yaml").read_text(encoding="utf-8"))


def test_yaml_validates() -> None:
    reg = sr.SchemaRegister.model_validate(_raw(), strict=False)
    assert (len(reg.envelope_schemas), len(reg.grammar_schemas)) == (9, 4)


def test_yaml_parity_with_schema_files() -> None:
    from_files = sr.SchemaRegister.model_validate(
        load_schema_register_from_files(SCHEMAS), strict=False
    )
    committed = sr.SchemaRegister.model_validate(_raw(), strict=False)
    assert committed == from_files


def test_every_schema_file_is_registered() -> None:
    reg = sr.SchemaRegister.model_validate(_raw(), strict=False)
    listed = {e.file for e in reg.envelope_schemas} | {g.file for g in reg.grammar_schemas}
    on_disk = {p.name for p in SCHEMAS.glob("*.yaml") if p.name != "schema_register.yaml"}
    assert listed == on_disk


def test_readme_links_new_files() -> None:
    text = (SCHEMAS / "README.md").read_text(encoding="utf-8")
    assert "(schema_register.py)" in text and "(schema_register.yaml)" in text


def test_negative_wrong_counts() -> None:
    raw = _raw()
    with pytest.raises(ValidationError):
        sr.SchemaRegister.model_validate(
            {**raw, "grammar_schemas": raw["grammar_schemas"][:-1]}, strict=False
        )


def test_negative_extra_missing_id() -> None:
    raw = _raw()
    env = [dict(e) for e in raw["envelope_schemas"]]
    env[0].pop("schema_dollar_id", None)
    with pytest.raises(ValidationError):
        sr.SchemaRegister.model_validate({**raw, "envelope_schemas": env}, strict=False)


def test_negative_duplicate_identifier() -> None:
    raw = _raw()
    env = [dict(e) for e in raw["envelope_schemas"]]
    ids = [i for i, e in enumerate(env) if "schema_dollar_id" in e]
    env[ids[1]]["schema_dollar_id"] = env[ids[0]]["schema_dollar_id"]
    with pytest.raises(ValidationError):
        sr.SchemaRegister.model_validate({**raw, "envelope_schemas": env}, strict=False)


def test_negative_wrong_dialect_and_namespace() -> None:
    entry = dict(_raw()["envelope_schemas"][0])
    with pytest.raises(ValidationError):
        sr.EnvelopeSchemaEntry.model_validate(
            {**entry, "dialect": "http://json-schema.org/draft-07/schema#"}, strict=False
        )
    with pytest.raises(ValidationError):
        sr.EnvelopeSchemaEntry.model_validate({**entry, "schema_dollar_id": "evil.x"}, strict=False)


def test_negative_bad_grammar_id() -> None:
    entry = dict(_raw()["grammar_schemas"][0])
    with pytest.raises(ValidationError):
        sr.GrammarSchemaEntry.model_validate({**entry, "schema_id": "ddc-tape"}, strict=False)
    with pytest.raises(ValidationError):
        sr.GrammarSchemaEntry.model_validate({**entry, "authority_effect": "Grant"}, strict=False)
