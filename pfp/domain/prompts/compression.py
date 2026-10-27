"""Bounded storage codec for PFP turn trees; expansion preserves provider inputs.

This removes duplicate stored environments. It does not shorten the expanded
provider prompt or authenticate an author. Digests use python-sorted-json-v1.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from pfp.domain.prompt_representations.common import (
    BaseRepresentationRecord, Digest, MAX_PROMPT_BYTES, MAX_SEGMENTS,
    canonical_json_bytes, sha256_digest,
)

MAX_EXPANDED_BYTES = MAX_PROMPT_BYTES * MAX_SEGMENTS


class PromptEnvironment(BaseRepresentationRecord):
    system: str
    answer_schema: dict
    checker_id: str = Field(default="shape-only-v1", min_length=1)


class PromptSource(BaseRepresentationRecord):
    text: str
    sha256: Digest


class PromptSpan(BaseRepresentationRecord):
    source_sha256: Digest
    start: StrictInt = Field(ge=0)
    end: StrictInt = Field(ge=0)


class PromptOverrides(BaseRepresentationRecord):
    answer_schema: dict | None = None


class PromptTreeNode(BaseRepresentationRecord):
    node_id: str = Field(min_length=1)
    parent_id: str | None
    slot: StrictInt | None = Field(default=None, ge=0)
    environment: Digest
    span: PromptSpan
    task_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    context: dict | None = None
    feedback: str | None = None
    overrides: PromptOverrides = Field(default_factory=PromptOverrides)


class _TurnSpec(BaseRepresentationRecord):
    node_id: str = Field(min_length=1)
    parent_id: str | None
    slot: StrictInt | None = Field(default=None, ge=0)
    system: str
    user: str
    task_id: str = Field(min_length=1)
    attempt_id: str = Field(min_length=1)
    answer_schema: dict | None = None
    checker_id: str = Field(default="shape-only-v1", min_length=1)
    context: dict | None = None
    feedback: str | None = None


class CompressedPromptTree(BaseRepresentationRecord):
    version: Literal["pfp-environment-tree-v1"] = "pfp-environment-tree-v1"
    canonicalization_profile: Literal["python-sorted-json-v1"] = "python-sorted-json-v1"
    authority_effect: Literal["None"] = "None"
    environments: dict[str, PromptEnvironment]
    sources: list[PromptSource]
    nodes: list[PromptTreeNode] = Field(min_length=1, max_length=MAX_SEGMENTS)
    content_sha256: Digest

    @model_validator(mode="after")
    def validate_content(self):
        raw = self.model_dump(mode="json", exclude={"content_sha256"})
        if sha256_digest(canonical_json_bytes(raw)) != self.content_sha256:
            raise ValueError("PROMPT_TREE_DIGEST_MISMATCH")
        _expand(self, MAX_EXPANDED_BYTES)
        return self


def _expand(tree: CompressedPromptTree, limit: int) -> list[dict]:
    if len(tree.sources) > MAX_SEGMENTS or len(tree.environments) > MAX_SEGMENTS:
        raise ValueError("PROMPT_RESOURCE_COUNT_LIMIT")
    sources = {}
    for source in tree.sources:
        data = source.text.encode("utf-8")
        if sha256_digest(data) != source.sha256 or source.sha256 in sources:
            raise ValueError("PROMPT_SOURCE_DIGEST_MISMATCH")
        sources[source.sha256] = data
    if sum(map(len, sources.values())) > MAX_EXPANDED_BYTES:
        raise ValueError("PROMPT_SOURCE_LIMIT")
    for key, env in tree.environments.items():
        if len(canonical_json_bytes(env.model_dump())) > MAX_PROMPT_BYTES * 2:
            raise ValueError("PROMPT_ENVIRONMENT_LIMIT")
        if sha256_digest(canonical_json_bytes(env.model_dump())) != key:
            raise ValueError("PROMPT_ENVIRONMENT_DIGEST_MISMATCH")
    seen, slots, result, expanded = set(), defaultdict(int), [], 0
    for node in tree.nodes:
        if node.node_id in seen:
            raise ValueError("DUPLICATE_PROMPT_NODE")
        if not seen:
            if node.parent_id is not None or node.slot is not None:
                raise ValueError("PROMPT_ROOT_REQUIRED")
        else:
            if node.parent_id not in seen or node.slot != slots[node.parent_id]:
                raise ValueError("INVALID_PROMPT_PARENT_OR_SLOT")
            slots[node.parent_id] += 1
        seen.add(node.node_id)
        env = tree.environments.get(node.environment)
        data = sources.get(node.span.source_sha256)
        if env is None or data is None:
            raise ValueError("MISSING_PROMPT_SOURCE_OR_ENVIRONMENT")
        start, end = node.span.start, node.span.end
        if start > end or end > len(data):
            raise ValueError("INVALID_PROMPT_SPAN")
        try:
            # Decode both prefix and selected bytes: even an empty span must lie
            # on a UTF-8 boundary, not in the middle of a retained code point.
            data[:start].decode("utf-8")
            user = data[start:end].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("INVALID_PROMPT_UTF8_BOUNDARY") from exc
        schema = node.overrides.answer_schema
        item = dict(node_id=node.node_id, parent_id=node.parent_id, slot=node.slot,
            system=env.system, user=user, answer_schema=env.answer_schema if schema is None else schema,
            checker_id=env.checker_id, task_id=node.task_id, attempt_id=node.attempt_id,
            context=node.context, feedback=node.feedback)
        if len(user.encode("utf-8")) > MAX_PROMPT_BYTES or len(env.system.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ValueError("PROMPT_NODE_LIMIT")
        expanded += len(canonical_json_bytes(item))
        if expanded > limit:
            raise ValueError("PROMPT_EXPANSION_LIMIT")
        result.append(item)
    return result


def compress_prompt_tree(nodes: list[dict]) -> CompressedPromptTree:
    """Store shared system/schema once; retain per-node schema overrides explicitly."""
    if not 1 <= len(nodes) <= MAX_SEGMENTS:
        raise ValueError("PROMPT_NODE_COUNT_LIMIT")
    turns = [_TurnSpec.model_validate(node) for node in nodes]
    source = "".join(turn.user for turn in turns)
    source_digest = sha256_digest(source)
    envs, groups, compact, offset = {}, {}, [], 0
    for turn in turns:
        schema = turn.answer_schema if turn.answer_schema is not None else {"type": "string", "minLength": 1}
        group = (turn.system, turn.checker_id)
        if group not in groups:
            env = PromptEnvironment(system=turn.system, answer_schema=schema,
                checker_id=turn.checker_id)
            key = sha256_digest(canonical_json_bytes(env.model_dump()))
            groups[group], envs[key] = key, env
        key = groups[group]
        override = schema if schema != envs[key].answer_schema else None
        end = offset + len(turn.user.encode("utf-8"))
        compact.append(PromptTreeNode(node_id=turn.node_id, parent_id=turn.parent_id, slot=turn.slot,
            environment=key, span=PromptSpan(source_sha256=source_digest, start=offset, end=end),
            task_id=turn.task_id, attempt_id=turn.attempt_id, context=turn.context, feedback=turn.feedback,
            overrides=PromptOverrides(answer_schema=override)).model_dump(mode="json"))
        offset = end
    raw = dict(version="pfp-environment-tree-v1", canonicalization_profile="python-sorted-json-v1",
        authority_effect="None", environments={k: v.model_dump(mode="json") for k, v in envs.items()},
        sources=[dict(text=source, sha256=source_digest)], nodes=compact)
    return CompressedPromptTree.model_validate({**raw,
        "content_sha256": sha256_digest(canonical_json_bytes(raw))})


def expand_prompt_tree(tree: CompressedPromptTree | dict, *,
    max_expanded_bytes: int = MAX_EXPANDED_BYTES) -> list[dict]:
    if type(max_expanded_bytes) is not int or not 0 < max_expanded_bytes <= MAX_EXPANDED_BYTES:
        raise ValueError("PROMPT_EXPANSION_LIMIT")
    # Frozen models can contain mutable dictionaries. Revalidate the serialized
    # envelope at use time instead of trusting construction-time validation.
    raw = tree.model_dump(mode="json") if isinstance(tree, CompressedPromptTree) else tree
    checked = CompressedPromptTree.model_validate(raw)
    return _expand(checked, max_expanded_bytes)


def prompt_tree_storage_metrics(tree: CompressedPromptTree) -> dict:
    expanded = expand_prompt_tree(tree)
    return dict(compact_bytes=len(canonical_json_bytes(tree.model_dump(mode="json"))),
        expanded_bytes=len(canonical_json_bytes(expanded)), provider_token_savings=None,
        interpretation="Storage bytes only; expanded provider requests are unchanged.")
