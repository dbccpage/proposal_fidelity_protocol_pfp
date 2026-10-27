from copy import deepcopy

import pytest

from pfp.domain.prompts.compression import (
    compress_prompt_tree, expand_prompt_tree, prompt_tree_storage_metrics,
)
from pfp.infrastructure.compressed_task_turn import prepare_compressed_turn
from pfp.infrastructure.task_turn import prepare_task_turn
from pfp.use_cases.pfp_proposal import REPAIR_RULES
from pfp.domain.prompt_representations.common import canonical_json_bytes, sha256_digest


def reseal(raw):
    raw["content_sha256"] = sha256_digest(canonical_json_bytes(
        {key: value for key, value in raw.items() if key != "content_sha256"}))
    return raw


def nodes():
    return [dict(node_id="root", parent_id=None, slot=None, system="Shared instruction. " * 200,
        user="α🙂 source", task_id="task", attempt_id="0", answer_schema={"type": "string"}),
        dict(node_id="child", parent_id="root", slot=0, system="Shared instruction. " * 200,
        user="second", task_id="task", attempt_id="1", answer_schema={"type": "integer"},
        context={"previous": "observed"}, feedback=REPAIR_RULES["TASK_ENVELOPE"])]


def test_compressed_nodes_prepare_identical_provider_and_checker_inputs():
    original = nodes()
    tree = compress_prompt_tree(original)
    assert len(tree.environments) == 1
    assert tree.nodes[1].overrides.answer_schema == {"type": "integer"}
    for node in original:
        kwargs = {k: v for k, v in node.items() if k not in {"node_id", "parent_id", "slot"}}
        plain = prepare_task_turn(**kwargs)
        compact = prepare_compressed_turn(tree, node["node_id"])
        assert compact == plain
        assert compact.binding == plain.binding
    metrics = prompt_tree_storage_metrics(tree)
    assert metrics["compact_bytes"] < metrics["expanded_bytes"]
    assert metrics["provider_token_savings"] is None


def test_empty_and_unicode_sources_roundtrip_after_json_storage():
    original = nodes()
    original[1]["user"] = ""
    tree = compress_prompt_tree(original)
    restored = type(tree).model_validate_json(tree.model_dump_json())
    assert [n["user"] for n in expand_prompt_tree(restored)] == ["α🙂 source", ""]


def test_explicit_optional_schema_uses_existing_preparation_default():
    original = nodes()[:1]
    original[0]["answer_schema"] = None
    tree = compress_prompt_tree(original)
    kwargs = {key: value for key, value in original[0].items()
        if key not in {"node_id", "parent_id", "slot"}}
    assert prepare_compressed_turn(tree, "root") == prepare_task_turn(**kwargs)


def test_changed_source_or_environment_is_refused_before_preparation():
    tree = compress_prompt_tree(nodes())
    raw = tree.model_dump(mode="json")
    raw["sources"][0]["text"] = "different source"
    with pytest.raises(ValueError):
        expand_prompt_tree(reseal(raw))
    tree.environments[next(iter(tree.environments))].answer_schema["type"] = "boolean"
    with pytest.raises(ValueError):
        prepare_compressed_turn(tree, "root")


@pytest.mark.parametrize("edit", ["unicode_boundary", "outside", "missing_parent", "duplicate_slot"])
def test_invalid_spans_and_tree_references_refused(edit):
    raw = compress_prompt_tree(nodes()).model_dump(mode="json")
    if edit == "unicode_boundary":
        raw["nodes"][0]["span"]["start"] = 1
    elif edit == "outside":
        raw["nodes"][0]["span"]["end"] = 999999
    elif edit == "missing_parent":
        raw["nodes"][1]["parent_id"] = "absent"
    else:
        other = deepcopy(raw["nodes"][1])
        other["node_id"] = "other"
        raw["nodes"].append(other)
    with pytest.raises(ValueError):
        expand_prompt_tree(reseal(raw))


def test_expansion_limit_and_unknown_node_refused():
    tree = compress_prompt_tree(nodes())
    with pytest.raises(ValueError, match="EXPANSION_LIMIT"):
        expand_prompt_tree(tree, max_expanded_bytes=100)
    with pytest.raises(ValueError, match="UNKNOWN_PROMPT_NODE"):
        prepare_compressed_turn(tree, "missing")


@pytest.mark.parametrize("change", [
    {"slot": True}, {"parent_id": "child"}, {"slot": 1}, {"user": "x" * 65537},
])
def test_compressor_rejects_invalid_tree_input(change):
    original = nodes()
    original[1].update(change)
    with pytest.raises(ValueError):
        compress_prompt_tree(original)
