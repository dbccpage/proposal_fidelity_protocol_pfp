"""Fenced example discriminators stay types in the user seed.

AuthorityEffect: None. Host fixtures only; schema shape is not task acceptance.
"""

import json

import pytest

from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
from omega_engine_pfp.use_cases.pfp_prompt import AssemblePfpPromptUseCase, task_contract

DISCRIMINATORS = ("code", "verdict", "status", "kind", "refusal_code")


def user_seed(task_text: str) -> str:
    prompt = AssemblePfpPromptUseCase().execute(
        PfpPromptTemplate(
            "SPK-001",
            "[USER PROMPT]",
            {"properties": {"answer": {"type": "object"}}},
        ),
        PfpTaskPrompt("fixture", task_text, {"n": 3}, {"type": "object"}),
    )
    return prompt.user


def embedded_schema(redacted: str) -> dict:
    marker = "Wire field shape (values withheld):\n"
    start = redacted.index(marker) + len(marker)
    return json.loads(redacted[start:].split("\n", 1)[0])


def consts(node) -> list:
    found = []
    if type(node) is dict:
        if "const" in node:
            found.append(node["const"])
        for value in node.values():
            found.extend(consts(value))
    elif type(node) is list:
        for value in node:
            found.extend(consts(value))
    return found


@pytest.mark.parametrize("key", DISCRIMINATORS)
def test_fenced_discriminator_value_does_not_become_a_schema_const(key):
    task_text = "keep-this-heading\n```json\n" + json.dumps(
        {key: "938456", "phi1": "1/2", "width": 7}
    ) + "\n```\n"
    redacted = task_contract(task_text)
    schema = embedded_schema(redacted)
    assert consts(schema) == []
    assert schema["properties"][key] == {"type": "string"}
    assert schema["properties"]["phi1"] == {"type": "string"}
    assert schema["properties"]["width"] == {"type": "integer"}
    assert "938456" not in redacted
    assert "1/2" not in redacted
    assert "keep-this-heading" in redacted
    assert "Example block withheld" not in redacted

    user = user_seed(task_text)
    seeded = json.loads(user)
    assert "938456" not in user
    assert '"const"' not in user
    assert consts(embedded_schema(seeded["task_contract"])) == []
    assert key in seeded["task_contract"]
    assert "phi1" in seeded["task_contract"]
    assert "width" in seeded["task_contract"]
    assert "keep-this-heading" in seeded["task_contract"]


def test_code_fence_938456_is_not_a_user_seed_const():
    task_text = "```json\n" + json.dumps({"code": "938456"}) + "\n```"
    user = user_seed(task_text)
    seeded = json.loads(user)
    schema = embedded_schema(seeded["task_contract"])
    assert schema["properties"]["code"] == {"type": "string"}
    assert consts(schema) == []
    assert "938456" not in user


def test_phi1_fence_still_withholds_938456():
    task_text = 'Contract\n```json\n{"answer": {"phi1": "938456"}}\n```'
    redacted = task_contract(task_text)
    assert "938456" not in redacted
    assert "phi1" in redacted
    assert embedded_schema(redacted)["properties"]["answer"]["properties"]["phi1"] == {
        "type": "string"
    }
    user = user_seed(task_text)
    assert "938456" not in user
    assert "phi1" in user
