"""Gate, schema and mode catalog file loading outside their pure models."""

from __future__ import annotations

from pathlib import Path

from omega_engine_pfp.domain.stages.mode_catalog import ModeCatalog, ModeContractHeader

from .yaml_loading import strict_yaml_load

_PRIMARY_KEYS = ("gate_id", "name", "character", "authority_effect")
_INTER_KEYS = ("intergate_id", "transition_from", "transition_to", "cognitive_vector", "authority_effect")
_EMP_KEYS = ("gate_id", "kind", "suite_id", "comparison_operator", "authority_effect")


def _head(path: Path, keys: tuple[str, ...], relative: str) -> dict[str, object]:
    raw = strict_yaml_load(path.read_text(encoding="utf-8"))
    return {**{key: raw[key] for key in keys}, "file": relative}


def load_gate_register_from_files(gates_dir: Path) -> dict[str, list[dict[str, object]]]:
    return {
        "primary_gates": [_head(path, _PRIMARY_KEYS, path.name) for path in sorted(gates_dir.glob("[0-9][0-9]_*.yaml"))],
        "intergates": [_head(path, _INTER_KEYS, f"intergates/{path.name}") for path in sorted((gates_dir / "intergates").glob("*.yaml"))],
        "empirical_gates": [_head(path, _EMP_KEYS, f"empirical/{path.name}") for path in sorted((gates_dir / "empirical").glob("*.yaml"))],
    }


def load_schema_register_from_files(schemas_dir: Path) -> dict[str, list[dict[str, object]]]:
    envelopes: list[dict[str, object]] = []
    grammars: list[dict[str, object]] = []
    for path in sorted(schemas_dir.glob("*.yaml")):
        raw = strict_yaml_load(path.read_text(encoding="utf-8"))
        if "$schema" in raw:
            envelopes.append({"file": path.name, "dialect": raw["$schema"], "schema_dollar_id": raw.get("$id")})
        elif "schema_id" in raw:
            grammars.append({"file": path.name, "schema_id": raw["schema_id"]})
    return {"envelope_schemas": envelopes, "grammar_schemas": grammars}


def load_mode_contract_header(path: Path) -> ModeContractHeader:
    raw = strict_yaml_load(path.read_text(encoding="utf-8"))
    keys = ("mode_id", "name", "cluster", "authority_effect")
    return ModeContractHeader.model_validate({key: raw[key] for key in keys}, strict=False)


def load_mode_catalog(modes_dir: Path, yaml_path: Path) -> ModeCatalog:
    raw = strict_yaml_load(yaml_path.read_text(encoding="utf-8"))
    catalog = ModeCatalog.model_validate(raw, strict=False)
    for entry in catalog.entries:
        header = load_mode_contract_header(modes_dir / entry.contract_path)
        if (header.mode_id, header.cluster) != (entry.mode_id, entry.cluster):
            raise ValueError(f"catalog entry {entry.mode_id} disagrees with its contract.yaml")
    return catalog
