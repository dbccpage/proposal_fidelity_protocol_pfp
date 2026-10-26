"""Tests for normal_forms/nf_domain_index.py: typing, negative controls, parity.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

import omega_engine_pfp.domain.normal_forms.nf_domain_index as nf
from omega_engine_pfp.infrastructure.normal_form_loading import (
    check_contract_file,
)
from omega_engine_pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR

NF = NORMAL_FORMS_DIR


def _raw() -> dict:
    return yaml.safe_load((NF / "nf_domain_index.yaml").read_text(encoding="utf-8"))


def test_yaml_validates_and_matches_contract_files() -> None:
    index = nf.NfDomainIndex.model_validate(_raw(), strict=False)
    for entry in index.contracts:
        check_contract_file(entry, NF)


def test_domain_entries_are_in_the_full_resource_catalog() -> None:
    index = nf.NfDomainIndex.model_validate(_raw(), strict=False)
    indexed = {c.nf_id for c in index.contracts}
    full = yaml.safe_load((NF / "index.yaml").read_text(encoding="utf-8"))
    catalog_ids = {nf_id for ids in full["contracts"].values() for nf_id in ids}
    assert indexed <= catalog_ids
    assert indexed == nf.DOMAIN_CONTRACT_IDS
    assert "nf.experimental.qm_classical" in indexed
    assert all((NF / (name + ".yaml")).is_file() for name in indexed)


def test_contract_files_do_not_claim_true_normal_form() -> None:
    for entry in _raw()["contracts"]:
        path = NF / (entry["nf_id"] + ".yaml")
        text = path.read_text(encoding="utf-8")
        assert "qualifies_as_true_normal_form: true" not in text


def test_tbnf_alphabet_has_38_characters() -> None:
    assert len(nf.TBNF_ALPHABET) == 38
    assert nf.is_tbnf_token_string("<a<b>>0")
    assert not nf.is_tbnf_token_string("<a b>")
    assert not nf.is_tbnf_token_string("<A>")


def test_readme_links_new_files() -> None:
    text = (NF / "README.md").read_text(encoding="utf-8")
    model_link = "../../../domain/normal_forms/nf_domain_index.py"
    assert "(" + model_link + ")" in text and "(nf_domain_index.yaml)" in text
    assert (NF / model_link).resolve().is_file()


def test_negative_true_normal_form_claim_rejected() -> None:
    entry = dict(_raw()["contracts"][0])
    entry["qualifies_as_true_normal_form"] = True
    with pytest.raises(ValidationError):
        nf.NfIndexEntry.model_validate(entry, strict=False)


def test_negative_non_bool_flag_rejected() -> None:
    entry = dict(_raw()["contracts"][0])
    entry["qualifies_as_true_normal_form"] = 0
    with pytest.raises(ValidationError):
        nf.NfIndexEntry.model_validate(entry)


def test_negative_wrong_count_and_duplicate() -> None:
    raw = _raw()
    with pytest.raises(ValidationError):
        nf.NfDomainIndex.model_validate({**raw, "contracts": raw["contracts"][:-1]}, strict=False)
    dup = list(raw["contracts"])
    dup[8] = dict(dup[7])
    with pytest.raises(ValidationError):
        nf.NfDomainIndex.model_validate({**raw, "contracts": dup}, strict=False)


def test_negative_same_count_unknown_replacement_rejected() -> None:
    raw = _raw()
    entries = [dict(entry) for entry in raw["contracts"]]
    entries[0]["nf_id"] = "nf.experimental.unknown"
    with pytest.raises(ValidationError, match="complete canonical contract set"):
        nf.NfDomainIndex.model_validate({**raw, "contracts": entries}, strict=False)


def test_negative_duplicate_short_name_rejected() -> None:
    raw = _raw()
    entries = [dict(entry) for entry in raw["contracts"]]
    entries[0]["short_name"] = entries[1]["short_name"]
    with pytest.raises(ValidationError, match="short_name values must be unique"):
        nf.NfDomainIndex.model_validate({**raw, "contracts": entries}, strict=False)


def test_negative_unknown_family_and_category() -> None:
    entry = dict(_raw()["contracts"][0])
    with pytest.raises(ValidationError):
        nf.NfIndexEntry.model_validate({**entry, "family": "other"}, strict=False)
    with pytest.raises(ValidationError):
        nf.NfIndexEntry.model_validate({**entry, "form_category": "True Normal Form"}, strict=False)


def test_negative_family_disagreeing_with_file_detected() -> None:
    entry = nf.NfIndexEntry.model_validate(_raw()["contracts"][0], strict=False)
    wrong = entry.model_copy(update={"family": nf.NfFamily.EVIDENCE})
    with pytest.raises(ValueError):
        check_contract_file(wrong, NF)
