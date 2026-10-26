"""Bounded DPO rewriting of one fixed attributed directed-graph schema.

Explicit injective matches and identity-key monic interface inclusions only.
There is no match search, arbitrary schema interpreter or semantic judge.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

MAX_PARTS = 128
MAX_LINKS = 256
MAX_ATTRS = 32
MAX_ATTRIBUTE_BYTES = 65536
MAX_FUEL = 1024
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9.-]{0,95}\Z")


class RewriteRefusal(ValueError):
    """Typed, non-mutating refusal of a finite rewrite."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _identifier(value: str) -> None:
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
        raise RewriteRefusal("INVALID_IDENTIFIER")


def _attributes(value: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple or len(value) > MAX_ATTRS:
        raise RewriteRefusal("ATTRIBUTE_BOUND")
    keys: set[str] = set()
    byte_count = 0
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise RewriteRefusal("ATTRIBUTE_TYPE")
        key, text = item
        _identifier(key)
        if type(text) is not str or key in keys:
            raise RewriteRefusal("ATTRIBUTE_TYPE_OR_DUPLICATE")
        try:
            byte_count += len(key.encode("utf-8")) + len(text.encode("utf-8"))
        except UnicodeEncodeError as exc:
            raise RewriteRefusal("ATTRIBUTE_UTF8") from exc
        keys.add(key)
    if byte_count > MAX_ATTRIBUTE_BYTES:
        raise RewriteRefusal("ATTRIBUTE_BYTE_BOUND")
    return tuple(sorted(value))


@dataclass(frozen=True)
class Part:
    id: str
    kind: str
    attrs: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _identifier(self.id)
        _identifier(self.kind)
        object.__setattr__(self, "attrs", _attributes(self.attrs))


@dataclass(frozen=True)
class Link:
    id: str
    kind: str
    source: str
    target: str
    attrs: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for value in (self.id, self.kind, self.source, self.target):
            _identifier(value)
        object.__setattr__(self, "attrs", _attributes(self.attrs))


@dataclass(frozen=True)
class FiniteACSet:
    parts: tuple[Part, ...] = ()
    links: tuple[Link, ...] = ()

    def __post_init__(self) -> None:
        if type(self.parts) is not tuple or type(self.links) is not tuple:
            raise RewriteRefusal("GRAPH_TYPE")
        if len(self.parts) > MAX_PARTS or len(self.links) > MAX_LINKS:
            raise RewriteRefusal("GRAPH_BOUND")
        if any(type(part) is not Part for part in self.parts) or any(
            type(link) is not Link for link in self.links
        ):
            raise RewriteRefusal("GRAPH_ELEMENT_TYPE")
        part_ids = {part.id for part in self.parts}
        link_ids = {link.id for link in self.links}
        if len(part_ids) != len(self.parts) or len(link_ids) != len(self.links):
            raise RewriteRefusal("DUPLICATE_ID")
        if any(link.source not in part_ids or link.target not in part_ids for link in self.links):
            raise RewriteRefusal("MISSING_ENDPOINT")
        byte_count = sum(
            len(key.encode("utf-8")) + len(value.encode("utf-8"))
            for element in self.parts + self.links
            for key, value in element.attrs
        )
        if byte_count > MAX_ATTRIBUTE_BYTES:
            raise RewriteRefusal("GRAPH_ATTRIBUTE_BYTE_BOUND")
        object.__setattr__(self, "parts", tuple(sorted(self.parts, key=lambda item: item.id)))
        object.__setattr__(self, "links", tuple(sorted(self.links, key=lambda item: item.id)))


@dataclass(frozen=True)
class DpoRule:
    rule_id: str
    left: FiniteACSet
    interface: FiniteACSet
    right: FiniteACSet

    def __post_init__(self) -> None:
        _identifier(self.rule_id)
        if any(type(graph) is not FiniteACSet for graph in (self.left, self.interface, self.right)):
            raise RewriteRefusal("RULE_GRAPH_TYPE")
        for side in (self.left, self.right):
            parts = {part.id: part for part in side.parts}
            links = {link.id: link for link in side.links}
            if any(parts.get(part.id) != part for part in self.interface.parts) or any(
                links.get(link.id) != link for link in self.interface.links
            ):
                raise RewriteRefusal("INTERFACE_NOT_MONIC_SUBGRAPH")


def graph_digest(state: FiniteACSet) -> str:
    """Named Python canonical JSON profile, not RFC 8785 or a semantic digest."""
    if type(state) is not FiniteACSet:
        raise RewriteRefusal("GRAPH_TYPE")
    value = {
        "schema": "pfp.finite-attributed-graph.v1",
        "parts": [[part.id, part.kind, part.attrs] for part in state.parts],
        "links": [
            [link.id, link.kind, link.source, link.target, link.attrs] for link in state.links
        ],
    }
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(raw).hexdigest()


def rule_digest(rule: DpoRule) -> str:
    """Bind all three graphs and the registered rule identity."""
    if type(rule) is not DpoRule:
        raise RewriteRefusal("RULE_TYPE")
    value = [
        rule.rule_id,
        graph_digest(rule.left),
        graph_digest(rule.interface),
        graph_digest(rule.right),
    ]
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode("ascii")).hexdigest()


@dataclass(frozen=True)
class RewriteResult:
    state: FiniteACSet
    fuel_remaining: int
    before_digest: str
    after_digest: str
    rule_id: str
    part_match: tuple[tuple[str, str], ...]
    link_match: tuple[tuple[str, str], ...]


def _match(value: dict[str, str], required: set[str]) -> None:
    if type(value) is not dict or set(value) != required:
        raise RewriteRefusal("MATCH_DOMAIN")
    for key, target in value.items():
        _identifier(key)
        _identifier(target)
    if len(set(value.values())) != len(value):
        raise RewriteRefusal("NON_INJECTIVE_MATCH")


def _fresh(rule_id: str, local_id: str, occupied: set[str]) -> str:
    prefix = "dpo_" + hashlib.sha256((rule_id + "\0" + local_id).encode("utf-8")).hexdigest()[:16]
    serial = 0
    while f"{prefix}_{serial}" in occupied:
        serial += 1
    result = f"{prefix}_{serial}"
    occupied.add(result)
    return result


def apply_registered_rule(
    state: FiniteACSet,
    registry: tuple[DpoRule, ...],
    rule_id: str,
    part_match: dict[str, str],
    link_match: dict[str, str],
    *,
    fuel: int,
    protected_parts: frozenset[str] = frozenset(),
    protected_links: frozenset[str] = frozenset(),
) -> RewriteResult:
    """Execute a restricted DPO step; independent judges own task semantics."""
    if type(state) is not FiniteACSet:
        raise RewriteRefusal("GRAPH_TYPE")
    if type(fuel) is not int or not 1 <= fuel <= MAX_FUEL:
        raise RewriteRefusal("FUEL_BOUND")
    if type(registry) is not tuple or any(type(rule) is not DpoRule for rule in registry):
        raise RewriteRefusal("REGISTRY_TYPE")
    if len(registry) > 128:
        raise RewriteRefusal("REGISTRY_BOUND")
    rules = {rule.rule_id: rule for rule in registry}
    if len(rules) != len(registry):
        raise RewriteRefusal("DUPLICATE_RULE_ID")
    _identifier(rule_id)
    if rule_id not in rules:
        raise RewriteRefusal("UNREGISTERED_RULE")
    rule = rules[rule_id]
    state_parts = {part.id: part for part in state.parts}
    state_links = {link.id: link for link in state.links}
    for protected, actual in ((protected_parts, state_parts), (protected_links, state_links)):
        if type(protected) is not frozenset:
            raise RewriteRefusal("PROTECTION_TYPE")
        for item in protected:
            _identifier(item)
        if not protected.issubset(actual):
            raise RewriteRefusal("MISSING_PROTECTED_ELEMENT")
    _match(part_match, {part.id for part in rule.left.parts})
    _match(link_match, {link.id for link in rule.left.links})
    for part in rule.left.parts:
        found = state_parts.get(part_match[part.id])
        if found is None or (found.kind, found.attrs) != (part.kind, part.attrs):
            raise RewriteRefusal("PART_MATCH_MISMATCH")
    for link in rule.left.links:
        found = state_links.get(link_match[link.id])
        if found is None or (found.kind, found.attrs) != (link.kind, link.attrs):
            raise RewriteRefusal("LINK_MATCH_MISMATCH")
        if (found.source, found.target) != (part_match[link.source], part_match[link.target]):
            raise RewriteRefusal("MATCH_NOT_NATURAL")
    interface_parts = {part.id for part in rule.interface.parts}
    interface_links = {link.id for link in rule.interface.links}
    removed_parts = {
        part_match[part.id] for part in rule.left.parts if part.id not in interface_parts
    }
    removed_links = {
        link_match[link.id] for link in rule.left.links if link.id not in interface_links
    }
    if removed_parts & protected_parts or removed_links & protected_links:
        raise RewriteRefusal("PROTECTED_ELEMENT_DELETION")
    if any(
        link.id not in removed_links
        and (link.source in removed_parts or link.target in removed_parts)
        for link in state.links
    ):
        raise RewriteRefusal("DANGLING_CONDITION")
    parts = {key: part for key, part in state_parts.items() if key not in removed_parts}
    links = {key: link for key, link in state_links.items() if key not in removed_links}
    occupied_parts = set(state_parts)
    occupied_links = set(state_links)
    right_parts = {key: part_match[key] for key in interface_parts}
    for part in rule.right.parts:
        if part.id not in interface_parts:
            fresh = _fresh(rule_id, part.id, occupied_parts)
            right_parts[part.id] = fresh
            parts[fresh] = Part(fresh, part.kind, part.attrs)
    for link in rule.right.links:
        if link.id not in interface_links:
            fresh = _fresh(rule_id, link.id, occupied_links)
            links[fresh] = Link(
                fresh, link.kind, right_parts[link.source], right_parts[link.target], link.attrs
            )
    result = FiniteACSet(tuple(parts.values()), tuple(links.values()))
    if any(parts.get(key) != state_parts[key] for key in protected_parts) or any(
        links.get(key) != state_links[key] for key in protected_links
    ):
        raise RewriteRefusal("PROTECTED_ELEMENT_CHANGED")
    return RewriteResult(
        result,
        fuel - 1,
        graph_digest(state),
        graph_digest(result),
        rule_id,
        tuple(sorted(part_match.items())),
        tuple(sorted(link_match.items())),
    )
