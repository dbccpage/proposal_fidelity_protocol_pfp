"""Prompt Hierarchy Parser.

Parses prompt URIs and already-decoded companion binding mappings.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

from .models import (
    AntiOpBinding,
    AntibodyBinding,
    ImmuneFenceBinding,
    OperadPromptBinding,
    PromptTreeNode,
    PromptUri,
)


def parse_prompt_uri(uri_str: str) -> PromptUri:
    """Validate and parse a canonical prompt URI string."""
    return PromptUri.parse(uri_str)


def load_prompt_node_from_binding_dict(data: Mapping[str, Any], *, source_file: str | None = None) -> PromptTreeNode:
    """Build a PromptTreeNode from a raw binding mapping."""
    raw_uri = str(data["prompt_uri"])
    uri = parse_prompt_uri(raw_uri)
    title = str(data.get("title", uri.prompt_id))
    description = str(data.get("description", ""))

    anti_ops: list[AntiOpBinding] = []
    for item in data.get("oewas_anti_ops", ()):
        anti_ops.append(
            AntiOpBinding(
                op_id=str(item["op_id"]),
                inspects_slot=str(item.get("inspects_slot", "candidate_text")),
                refusal_code=str(item.get("refusal_code", "ANTI_OP_VIOLATION")),
                description=str(item.get("description", "")),
            )
        )

    antibodies: list[AntibodyBinding] = []
    for item in data.get("oeeis_antibodies", ()):
        antibodies.append(
            AntibodyBinding(
                antibody_id=str(item["antibody_id"]),
                signal1_epitope=str(item.get("signal1_epitope", "")),
                signal2_required_danger=str(item.get("signal2_required_danger", "")),
                minimum_status=str(item.get("minimum_status", "admitted")),
                description=str(item.get("description", "")),
            )
        )

    operad_raw = data.get("operad_binding")
    operad_binding: OperadPromptBinding | None = None
    if isinstance(operad_raw, Mapping):
        operad_binding = OperadPromptBinding(
            operation_id=str(operad_raw["operation_id"]),
            source_colours=tuple(str(c) for c in operad_raw.get("source_colours", ())),
            target_colour=str(operad_raw["target_colour"]),
            slot_to_colour=dict(operad_raw.get("slot_to_colour", {})),
            required_slot_pins=tuple(str(s) for s in operad_raw.get("required_slot_pins", ())),
            cross_slot_equality_groups=tuple(
                tuple(str(s) for s in grp) for grp in operad_raw.get("cross_slot_equality_groups", ())
            ),
            required_boundary_witness_slots=tuple(
                str(s) for s in operad_raw.get("required_boundary_witness_slots", ())
            ),
            equivariant=bool(operad_raw.get("equivariant", False)),
            residual_effect=str(operad_raw.get("residual_effect", "contractive")),
        )

    return PromptTreeNode(
        uri=uri,
        title=title,
        description=description,
        anti_ops=tuple(anti_ops),
        antibodies=tuple(antibodies),
        source_file=source_file,
        immune_fence=ImmuneFenceBinding(**data["immune_fence"]) if data.get("immune_fence") is not None else None,
        operad_binding=operad_binding,
    )

