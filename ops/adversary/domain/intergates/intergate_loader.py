"""intergate_loader.py
===================

Deterministic loader and validator for the 10 on-disk PFP intergate YAML specifications.

Governing Epic: EPIC-OE-ADVERSARY-002
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Optional

import yaml

from adversary.domain.intergates.models import IntergateSpec


class _UniqueKeyLoader(yaml.SafeLoader):
    """Refuse a mapping that repeats a key."""

    def construct_mapping(self, node, deep=False):
        seen: set[str] = set()
        for key_node, _value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if type(key) is not str:
                raise ValueError(f"YAML key must be a string: {key!r}")
            if key in seen:
                raise ValueError(f"duplicate YAML key: {key!r}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def find_intergates_dir() -> Path:
    """Dynamically resolve the canonical gates/intergates directory."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            target = parent / "pfp/infrastructure/yaml/gates/intergates"
            if target.is_dir():
                return target
            raise FileNotFoundError(f"Canonical PFP intergates missing: {target}")
    raise FileNotFoundError("Repository root for canonical PFP intergates is unresolved")


def load_intergate_specs(intergates_dir: Optional[Path] = None) -> Dict[str, IntergateSpec]:
    """Load all 10 intergate specifications from YAML into typed IntergateSpec records."""
    target_dir = intergates_dir or find_intergates_dir()
    yaml_files = sorted(target_dir.glob("*.yaml"))

    specs: Dict[str, IntergateSpec] = {}
    for yf in yaml_files:
        source_bytes = yf.read_bytes()
        raw = yaml.load(source_bytes, Loader=_UniqueKeyLoader)
        if type(raw) is not dict:
            raise ValueError(f"intergate specification must be a mapping: {yf}")
        spec = IntergateSpec(
            intergate_id=str(raw["intergate_id"]),
            name=str(raw["name"]),
            transition_from=str(raw["transition_from"]),
            transition_to=str(raw["transition_to"]),
            cognitive_vector=str(raw["cognitive_vector"]),
            authority_effect=str(raw.get("authority_effect", "None")),
            version=str(raw.get("version", "0.1.0")),
            doctrine=str(raw.get("doctrine", "")).strip(),
            objective=str(raw.get("objective", "")).strip(),
            fences=tuple(str(f) for f in raw.get("fences", ())),
            input_schema=dict(raw.get("input_schema", {})),
            transition_rules=str(raw.get("transition_rules", "")).strip(),
            narrowest_defensible_claim=str(raw.get("narrowest_defensible_claim", "")).strip(),
            next_test_needed=str(raw.get("next_test_needed", "")).strip(),
            source_file=yf.name,
            source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        )
        if spec.intergate_id in specs:
            raise ValueError(f"duplicate intergate ID: {spec.intergate_id}")
        if spec.authority_effect != "None" or not spec.fences or not spec.objective:
            raise ValueError(f"invalid intergate specification: {yf}")
        specs[spec.intergate_id] = spec

    if intergates_dir is None:
        from adversary.domain.intergates.payload_contract import PAYLOAD_FIELDS

        if set(specs) != set(PAYLOAD_FIELDS):
            raise ValueError("Canonical PFP intergate inventory differs from implemented diagnostics")
    return specs
