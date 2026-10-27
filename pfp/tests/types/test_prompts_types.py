"""Typed-contract tests for the PFP prompts folder.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pfp.domain.prompts import pfp_prompt as P
from pfp.domain.rewriting import prompt_containment as C

_here = Path(__file__).resolve()
ROOT = _here.parents[2] / "infrastructure" / "yaml"

PROMPT_SCHEMA = yaml.safe_load((ROOT / "prompts/schemas/template_schema_prompt.yaml").read_text("utf-8"))
CATALOG = yaml.safe_load((ROOT / "prompts/schemas/template_schema_containment.yaml").read_text("utf-8"))
H = "d" * 64


def _prompt(text="Summarize this.", **over) -> dict:
    base = {
        "schema_version": "core.pfp.prompt.v1",
        "prompt_id": H,
        "user_prompt": text,
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "authority_effect": "None",
    }
    base.update(over)
    return base


def test_prompt_yaml_schema_parity():
    model_schema = P.PfpPrompt.model_json_schema()
    assert set(PROMPT_SCHEMA["required"]) == set(model_schema["required"])
    assert set(PROMPT_SCHEMA["properties"]) == set(model_schema["properties"])


def test_valid_prompt_and_optional_system_prompt():
    assert P.PfpPrompt.model_validate(_prompt(), strict=False).system_prompt is None
    assert P.PfpPrompt.model_validate(_prompt(system_prompt="sys"), strict=False)


@pytest.mark.parametrize(
    "over",
    [
        {"user_prompt": ""},
        {"user_prompt": "   ", "content_sha256": hashlib.sha256(b"   ").hexdigest()},
        {"content_sha256": "0" * 64},  # digest of other bytes
        {"prompt_id": "short"},
        {"authority_effect": "Grant"},
        {"schema_version": "core.pfp.prompt.v0"},
        {"system_prompt": 5},
        {"extra": 1},
    ],
)
def test_malformed_prompt_rejected(over):
    with pytest.raises(ValidationError):
        P.PfpPrompt.model_validate(_prompt(**over), strict=False)


def _node(cardinality=1, children=(), kind="decompose") -> dict:
    return {
        "mutation_kind": kind,
        "prompt_ref": "p",
        "cardinality": cardinality,
        "children": list(children),
        "authority_effect": "None",
    }


def test_containment_yaml_example_validates():
    node = C.ExpansionNode.model_validate(CATALOG["example"], strict=False)
    assert node.cardinality == 3
    assert [m.value for m in C.MutationKind] == CATALOG["mutation_kinds"]
    assert [s.value for s in C.PipelineStage] == CATALOG["pipeline_order"]
    assert C.MAX_DEPTH == CATALOG["max_depth"]


def _chain(depth: int) -> dict:
    node = _node()
    for _ in range(depth):
        node = _node(cardinality=node["cardinality"] + 1, children=[node])
    return node


def test_depth_bound():
    assert C.ExpansionNode.model_validate(_chain(5), strict=False).depth() == 5
    with pytest.raises(ValidationError, match="max_depth"):
        C.ExpansionNode.model_validate(_chain(6), strict=False)


@pytest.mark.parametrize(
    "data",
    [
        _node(cardinality=2),
        _node(cardinality=1, children=[_node()]),
        _node(cardinality=True),
        _node(kind="invented"),
        {**_node(), "authority_effect": "Grant"},
        {**_node(), "prompt_ref": ""},
    ],
)
def test_malformed_node_rejected(data):
    with pytest.raises(ValidationError):
        C.ExpansionNode.model_validate(data, strict=False)
