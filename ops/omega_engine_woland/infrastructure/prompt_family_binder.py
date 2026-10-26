"""Woland composes OEEIS selection and PFP rendering before task preparation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping, Protocol

from omega_engine_pfp.domain.types.prompt_templates import AntibodySlot, GuidanceSlot
from omega_engine_pfp.infrastructure.immune_fence import NativeImmuneFenceRenderer
from omega_engine_operads.domain.prompt_hierarchy.models import PromptTreeNode


def attach_failure_to_prompt_family(
    family_store: dict[str, Any],
    failure_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Store a host-reproduced failure in the prompt-family binding store as a candidate antibody (F6).

    Invariants:
    - Refuses unreproduced failures with ValueError("UNREPRODUCED_FAILURE_CANNOT_ATTACH").
    - Emits CANDIDATE_ANTIBODY gated by existing human/thymus admission (human_thymus_admitted=False).
    """
    if failure_record.get("reproduced_by_host") is not True:
        raise ValueError("UNREPRODUCED_FAILURE_CANNOT_ATTACH")

    text = str(failure_record.get("text") or "").strip()
    if not text:
        raise ValueError("FAILURE_TEXT_REQUIRED")

    family_id = str(failure_record.get("family_id") or "default_family")
    candidates = family_store.setdefault(family_id, [])

    antibody_entry = {
        "candidate_id": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
        "seat_id": failure_record.get("seat_id"),
        "negative_example": text,
        "host_checker_witness": failure_record.get("witness"),
        "status": "CANDIDATE_ANTIBODY",
        "human_thymus_admitted": False,
    }
    candidates.append(antibody_entry)
    return antibody_entry


class PharmacySearchPort(Protocol):
    def search(self, query: Mapping[str, Any]) -> dict[str, Any]: ...


class FenceRenderPort(Protocol):
    def render(self, payload: Mapping[str, Any]) -> dict[str, Any]: ...


@dataclass(frozen=True)
class BoundPrompt:
    text: str
    metadata: dict[str, Any] | None
    exclusions: tuple[dict[str, Any], ...] = ()


class PromptFamilyBinder:
    def __init__(self, search_index: PharmacySearchPort, renderer: FenceRenderPort | None = None):
        self._search = search_index
        self._renderer = renderer if renderer is not None else NativeImmuneFenceRenderer()

    def bind(self, *, template_text: str, node: PromptTreeNode, operation_id: str,
             suspended_ids: tuple[str, ...] = ()) -> BoundPrompt:
        spec = node.immune_fence
        if spec is None:
            return BoundPrompt(template_text, None)
        if spec.domain != node.uri.domain or spec.stage != node.uri.stage:
            raise ValueError("IMMUNE_SCOPE_MISMATCH")
        found = self._search.search(dict(domain=spec.domain, tags=list(spec.tags), stage=spec.stage,
            prompt_field=spec.prompt_field, scope=str(node.uri), limit=spec.max_antibodies,
            suspended_ids=list(suspended_ids)))
        # Existing PFP guidance DTO carries the narrowed reviewed projection. Never
        # copy a catalog row, description, negative fixture or expected answer.
        guidance = GuidanceSlot(antibodies=[AntibodySlot(antibody_id=item["antibody_id"],
            pharmacy_status="admitted", evidence_sha256=item["rule_digest"],
            reviewed_guidance=item["guidance_text"], admission_reference=item["admission_reference"])
            for item in found["selected"]])
        rendered = self._renderer.render(dict(template_text=template_text,
            template_id=spec.template_id, template_version=spec.template_version,
            prompt_uri=str(node.uri), operation_id=operation_id, catalog_digest=found["catalog_digest"],
            required_ids=list(spec.required_antibody_ids), max_items=spec.max_antibodies,
            max_bytes=spec.max_bytes, guidance=[dict(antibody_id=item.antibody_id,
                rule_digest=item.evidence_sha256, guidance_text=item.reviewed_guidance,
                admission_reference=item.admission_reference) for item in guidance.antibodies
                if isinstance(item, AntibodySlot)]))
        return BoundPrompt(rendered["rendered_text"], rendered["binding"],
            tuple(found.get("exclusions", ())) + tuple(rendered["omissions"]))
