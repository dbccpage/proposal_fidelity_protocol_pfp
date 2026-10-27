"""Filesystem and text loading retain the same validated PFP models."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pfp.domain.types.base import PfpDomainModel
from pfp.infrastructure.model_loading import load_yaml_model


class InputModel(PfpDomainModel):
    name: str


def test_file_bom_and_pure_text_construct_the_same_model(tmp_path):
    path = tmp_path / "input.yaml"
    path.write_bytes(b"\xef\xbb\xbfname: finite\n")
    assert load_yaml_model(InputModel, path) == InputModel.from_yaml("name: finite\n")
    assert load_yaml_model(InputModel, str(path)) == InputModel(name="finite")


def test_file_loader_keeps_domain_unknown_field_refusal(tmp_path):
    path = tmp_path / "invalid.yaml"
    path.write_text("name: finite\nunknown: true\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_yaml_model(InputModel, path)


def test_model_text_parser_does_not_accept_a_filesystem_path():
    with pytest.raises(TypeError, match="requires YAML text"):
        InputModel.from_yaml(Path("input.yaml"))


@pytest.mark.parametrize("content", ["- list\n", "null\n", "true\n"])
def test_non_mapping_yaml_is_refused(content):
    with pytest.raises(ValueError, match="must be a mapping"):
        load_yaml_model(InputModel, content)
