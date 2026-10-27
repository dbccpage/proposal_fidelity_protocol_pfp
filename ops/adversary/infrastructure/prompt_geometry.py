"""Thin Adversary composition for native prompt geometry and bounded organization.

Observations are source-bound diagnostics, never task acceptance. The existing
PFP prompt and raw-response owners retain source bytes; this adapter does not
create another transcript store or change PFP's digest profile.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from adversary.domain import native
from adversary.domain.native_gate_check import native_digest
from adversary.infrastructure.native import DefaultNativeOperationPort
from operads.skill_operad.resolver.native_runtime import (
    native_validate,
)

from .operad_binding import forge_operation_inventory

PROFILE = "ordered-sha256-density-v1"
SCHEMA = "core.prompt-density.v1"
FORGE_OPERATION = "forge.organize-prompt.v1"


def _bytes(text: str | bytes) -> bytes:
    return text if isinstance(text, bytes) else text.encode("utf-8", errors="surrogatepass")


def observe_text(text: str | bytes, *, dimension: int, role_id: str,
                 field: str, trust_level: str) -> dict:
    """Observe actual bytes; host or numerical failure leaves an explicit status."""
    raw = _bytes(text)
    binding = dict(schema_version=SCHEMA, profile=PROFILE, dim=dimension,
        source_sha256="sha256:" + sha256(raw).hexdigest(), source_bytes=len(raw),
        role_id=role_id, field=field, trust_level=trust_level, authority_effect="None")
    try:
        report = native.value(DefaultNativeOperationPort(), "prompt_density_observe", bytes_hex=raw.hex(), dim=dimension,
            role_id=role_id, field=field, trust_level=trust_level, profile=PROFILE)
        if not isinstance(report, dict) or any(report.get(key) != value for key, value in binding.items()):
            raise ValueError("DENSITY_SOURCE_BINDING_MISMATCH")
        if report.get("status") not in {"OBSERVED", "EMPTY", "INVALID_UTF8", "LIMIT_EXCEEDED", "INVALID_INPUT", "UNAVAILABLE"}:
            raise ValueError("DENSITY_STATUS_INVALID")
        return report
    except (ValueError, TypeError, OSError) as exc:
        return {**binding, "status":"UNAVAILABLE", "reason":str(exc),
            "spans":[], "factors":[], "weights":[], "spectrum":[],
            "entropy_bits":None, "purity":None, "effective_rank":None, "numerical_rank":None,
            "spectrum_tolerance":1e-10}


def _dimension(action):
    return getattr(action.brief, "density_dimension", None) if action.brief is not None else None


def observe_teamwork_seed(action) -> dict | None:
    dimension = _dimension(action)
    if dimension is None:
        return None
    return observe_text(action.objective, dimension=dimension, role_id="syntax_prefilter",
        field="seed", trust_level="user-seed")


def observe_prepared_turn(action, turn):
    """Called after all rendering; measurements cannot alter the PFP input digest."""
    dimension = _dimension(action)
    if dimension is None:
        return turn
    reports = {
        "system":observe_text(turn.prompt.system, dimension=dimension, role_id=action.role_id,
            field="pfp.system", trust_level="host-assembled"),
        "user":observe_text(turn.prompt.user, dimension=dimension, role_id=action.role_id,
            field="pfp.user", trust_level="mixed-source"),
    }
    return replace(turn, observation_metadata={**turn.observation_metadata, "density":reports})


def observe_teamwork_reply(action, raw: bytes) -> dict | None:
    dimension = _dimension(action)
    if dimension is None:
        return None
    return observe_text(raw, dimension=dimension, role_id=action.role_id,
        field="pfp.raw_reply", trust_level="untrusted-model")


def _forge_request(objective, brief):
    return {"seed":objective, "task":brief.deliverable, "constraints":list(brief.constraints),
        "acceptance":list(brief.acceptance), "response_contract":brief.artifact_schema}


def _request_json(request):
    return json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def organize_initial_seed(objective: str, brief) -> dict:
    """Execute one checked operation; callers persist its result in the run brief."""
    if brief.forge_organization is not True:
        raise ValueError("FORGE_NOT_SELECTED")
    request = _forge_request(objective, brief)
    inventory, wire = forge_operation_inventory()
    # Values request kernel evaluation; this registered host operation is
    # executed by its native Forge owner after the term boundary is checked.
    checked = native_validate(inventory, wire)
    if checked.get("status") != "VALID" or checked.get("operation_ids") != [FORGE_OPERATION]:
        raise ValueError("FORGE_OPERATION_TERM_REFUSED")
    result = native.value(DefaultNativeOperationPort(), "forge_organize_prompt", request_json=_request_json(request))
    _verify_result_binding(request, result)
    root = Path(__file__).resolve().parents[2]
    sources = ("adversary/infrastructure/operad_binding.py",
        "adversary/infrastructure/prompt_geometry.py",
        "engine/crates_rs/core_prompt_civilization/src/forge.rs")
    result = {**result, "operation_validation":checked,
        "source_sha256":{name:sha256((root / name).read_bytes()).hexdigest() for name in sources},
        "executed_operation_ids":[FORGE_OPERATION]}
    if brief.density_dimension is not None:
        before = observe_text(objective, dimension=brief.density_dimension, role_id="syntax_prefilter",
            field="seed", trust_level="user-seed")
        after = observe_text(result["organized_text"], dimension=brief.density_dimension, role_id="syntax_prefilter",
            field="seed", trust_level="user-seed")
        result["observations"] = {"before":before, "after":after}
        try:
            result["comparison"] = native.value(DefaultNativeOperationPort(), "prompt_density_compare", left=before, right=after)
        except (ValueError, TypeError, OSError) as exc:
            result["comparison"] = {"status":"UNAVAILABLE", "reason":str(exc), "authority_effect":"None"}
    return result


def _verify_result_binding(request, preparation):
    seed = _bytes(request["seed"])
    if not isinstance(preparation, dict) or type(preparation.get("organized_text")) is not str:
        raise ValueError("FORGE_PREPARATION_REQUIRED")
    organized = _bytes(preparation["organized_text"])
    expected = {"schema_version":"core.forge.organize-prompt.v1", "operation_id":FORGE_OPERATION,
        "status":"ORGANIZED", "request_sha256":native_digest(request),
        "seed_sha256":sha256(seed).hexdigest(), "organized_sha256":sha256(organized).hexdigest(),
        "source_bytes":len(seed), "rendered_bytes":len(organized), "authority_effect":"None"}
    if any(preparation.get(key) != value for key, value in expected.items()) or not organized.startswith(seed):
        raise ValueError("FORGE_PREPARATION_MISMATCH")


def organized_teamwork_seed(action) -> str:
    """Verify stored organization before digesting a role's prepared turn."""
    brief = action.brief
    if brief is None or brief.forge_organization is not True:
        return action.objective
    request = _forge_request(action.objective, brief)
    preparation = brief.forge_preparation
    _verify_result_binding(request, preparation)
    # Large diagnostic factors and transcript references are not validation inputs.
    retained = {key:preparation[key] for key in ("schema_version", "operation_id", "status",
        "request_sha256", "seed_sha256", "organized_sha256", "organized_text", "protected_spans",
        "source_bytes", "rendered_bytes", "authority_effect")}
    verified = native.value(DefaultNativeOperationPort(), "forge_verify_preparation", request_json=_request_json(request), preparation=retained)
    if verified.get("status") != "VALID":
        raise ValueError("FORGE_PREPARATION_MISMATCH")
    return preparation["organized_text"]


def discard_geometry_diagnostics(context: dict) -> None:
    """Project an owned wire dictionary in place; never pass retained model data."""
    brief = context.get("brief")
    if not isinstance(brief, dict) or brief.get("density_dimension") is None:
        return
    context.pop("pending_prompt", None)
    preparation = brief.get("forge_preparation") if isinstance(brief, dict) else None
    if isinstance(preparation, dict):
        preparation.pop("observations", None)
        preparation.pop("comparison", None)
    records = list(context.get("observations", ()))
    learning = context.get("learning_context")
    if isinstance(learning, dict):
        records.extend(learning.get(name) for name in ("learning", "digestion"))
    for record in records:
        metadata = record.get("metadata") if isinstance(record, dict) else None
        if isinstance(metadata, dict):
            metadata.pop("density", None)
            metadata.pop("pfp_prepared_prompts", None)
            attempts = metadata.get("pfp_attempts", ())
            if isinstance(attempts, (list, tuple)):
                for attempt in attempts:
                    if isinstance(attempt, dict):
                        attempt.pop("density", None)
                        attempt.pop("pfp_prepared_prompts", None)


def semantic_geometry_context(context: dict) -> dict:
    """Project task inputs without mutating the retained reporting history."""
    projected = deepcopy(context)
    discard_geometry_diagnostics(projected)
    return projected


def trim_geometry_context(context: dict) -> None:
    """Do not inject diagnostics or duplicate the persisted seed into model input."""
    discard_geometry_diagnostics(context)
    brief = context.get("brief")
    if isinstance(brief, dict) and "forge_preparation" in brief:
        preparation = brief.pop("forge_preparation")
        context["forge_binding"] = {key:preparation[key] for key in
            ("schema_version", "operation_id", "request_sha256", "seed_sha256", "organized_sha256")}
