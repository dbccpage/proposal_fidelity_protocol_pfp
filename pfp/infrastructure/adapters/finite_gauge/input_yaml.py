"""Strict YAML input adapter for finite-gauge requests."""

from __future__ import annotations

from typing import Any

import yaml

from omega_engine_pfp.domain.finite_gauge import RunConfig


class StrictFiniteGaugeLoader(yaml.SafeLoader):
    """Reject aliases, anchors, merge keys, and duplicate/non-string keys."""

    def compose_node(self, parent: Any, index: Any) -> Any:
        event = self.peek_event()
        if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None) is not None:
            raise ValueError("YAML aliases and anchors are not accepted")
        return super().compose_node(parent, index)

    def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            if key_node.value == "<<":
                raise ValueError("YAML merge keys are not accepted")
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in mapping:
                raise ValueError("YAML keys must be unique strings")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def parse_input_yaml(source: str) -> RunConfig:
    """Decode a bounded typed input packet."""
    if not isinstance(source, str) or not source.strip() or len(source) > 16_384:
        raise ValueError("input YAML must be nonempty and at most 16384 characters")
    try:
        packet = yaml.load(source, Loader=StrictFiniteGaugeLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid input YAML: {exc}") from exc
    return RunConfig.from_packet(packet)


__all__ = ["parse_input_yaml"]
