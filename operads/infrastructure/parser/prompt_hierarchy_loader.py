"""Read PFP prompt packets and sidecars at the OEWAS filesystem boundary."""

from __future__ import annotations

from pathlib import Path

import yaml

from omega_engine_operads.domain.prompt_hierarchy.models import (
    AntiOpBinding, AntibodyBinding, PromptTreeNode,
)
from omega_engine_operads.domain.prompt_hierarchy.parser import (
    load_prompt_node_from_binding_dict, parse_prompt_uri,
)


def load_prompt_node_from_pfp_yaml(pfp_yaml_path: Path) -> PromptTreeNode:
    """Construct a PromptTreeNode directly from a PFP PromptPacket YAML (e.g. p_research_04.yaml).

    Extracts declared constraints (forbidden interpretations, import boundaries) and merges any
    sibling binding definition (e.g. `<stem>.binding.yaml`).
    """
    raw_text = pfp_yaml_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw_text)

    lineage = data.get("lineage", {})
    prompt_id = lineage.get("prompt_id", pfp_yaml_path.stem.upper())

    # Map filename stage or prompt_id to canonical URI
    stage_match = re_stage(pfp_yaml_path.name)
    stage = stage_match if stage_match else "stage_04"
    canonical_uri = f"prompt://education/pfp/workflows/research/{stage}/{prompt_id}"
    uri = parse_prompt_uri(canonical_uri)

    anti_ops: list[AntiOpBinding] = []

    # 1. Parse op_semantics.forbidden_unlicensed_interpretations
    sys_prompt = data.get("system_prompt", {})
    op_semantics = sys_prompt.get("op_semantics", {})
    forbidden = op_semantics.get("forbidden_unlicensed_interpretations", [])
    for interp in forbidden:
        anti_ops.append(
            AntiOpBinding(
                op_id=f"pfp.refuse_unlicensed_{interp}",
                inspects_slot="candidate_text",
                refusal_code=f"ANTI_UNLICENSED_{interp.upper()}",
                description=f"Refuses candidate importing unlicensed {interp} semantics into SYM SYS.",
            )
        )

    # 2. Parse import_boundary
    if "import_boundary" in sys_prompt:
        anti_ops.append(
            AntiOpBinding(
                op_id="pfp.refuse_unmapped_continuum_import",
                inspects_slot="candidate_text",
                refusal_code="ANTI_UNMAPPED_CONTINUUM_IMPORT",
                description="Refuses continuous physics or Lie algebras without explicit primitive derivation mapping.",
            )
        )

    # 3. Check for companion binding sidecar (e.g. p_research_04.binding.yaml)
    sidecar = pfp_yaml_path.with_name(f"{pfp_yaml_path.stem}.binding.yaml")
    antibodies: list[AntibodyBinding] = []
    immune_fence = None
    operad_binding = None
    if sidecar.is_file():
        sidecar_data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
        bound = load_prompt_node_from_binding_dict(
            {"prompt_uri": str(uri), **sidecar_data}, source_file=str(sidecar))
        uri = bound.uri
        immune_fence = bound.immune_fence
        operad_binding = bound.operad_binding
        for item in sidecar_data.get("oewas_anti_ops", ()):
            anti_ops.append(
                AntiOpBinding(
                    op_id=str(item["op_id"]),
                    inspects_slot=str(item.get("inspects_slot", "candidate_text")),
                    refusal_code=str(item.get("refusal_code", "ANTI_OP_VIOLATION")),
                    description=str(item.get("description", "")),
                )
            )
        for item in sidecar_data.get("oeeis_antibodies", ()):
            antibodies.append(
                AntibodyBinding(
                    antibody_id=str(item["antibody_id"]),
                    signal1_epitope=str(item.get("signal1_epitope", "")),
                    signal2_required_danger=str(item.get("signal2_required_danger", "")),
                    minimum_status=str(item.get("minimum_status", "admitted")),
                    description=str(item.get("description", "")),
                )
            )

    return PromptTreeNode(
        uri=uri,
        title=f"PFP Research Prompt {prompt_id}",
        description=str(data.get("packet_type", "PromptPacketV0_1")),
        anti_ops=tuple(anti_ops),
        antibodies=tuple(antibodies),
        source_file=str(pfp_yaml_path),
        immune_fence=immune_fence,
        operad_binding=operad_binding,
    )


def re_stage(filename: str) -> str | None:
    import re
    m = re.search(r"p_research_(\d+)", filename)
    if m:
        return f"stage_{m.group(1)}"
    return None
