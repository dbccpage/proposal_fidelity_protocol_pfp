"""Operator-held live deployment using existing OEWAS signatures and native gates."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from contextlib import contextmanager
from dataclasses import asdict, replace
from pathlib import Path

from operations.domain.rop.result import Err
from operads.application.adversary_candidate_plan import (
    CandidateInstructionPlanV01,
    PlanNodeV01,
    compile_candidate_plan,
)
from operads.application.adversary_instruction_admission import (
    SCHEMA,
    SIGNATURE_NAMESPACE,
    source_snapshot_digest,
)
from operads.application.adversary_task_selection import (
    AdversaryCandidateRouteV01,
    AdversaryTaskShapeV01,
    select_candidate_plan,
)
from operads.domain.entities.operation_v3 import PortSpecV3
from operads.domain.value_objects.content_digest import ContentDigest
from operads.domain.value_objects.identifier import ColourId, SchemaRef

from ..domain.instruction_ingress import instruction_request_digest
from ..domain.models import SymbolGameRequestV1, AdversaryBoutRequestV1
from ..use_cases.base_swarm.specializations import resolve_swarm_type_profile
from .estates.oewas_native_anti_skill import load_native_anti_skill_gate
from .oewas_instruction_ingress import (
    OeopSourceRouteV01,
    SignedOeopInstructionIngress,
    read_route_documents,
    workload_profile_digest,
)

SCHEMA_VERSION = "core.adversary.live-config.v1"
SCENE_SCHEMA = "core.adversary.scene-orchestration.v1"
TRANSITION_EDGES = frozenset(
    (
        "PRE_DISPATCH->ACT_I",
        "ACT_I->ACT_II",
        "ACT_II->ACT_III",
        "ACT_III->ACT_IV",
        "ACT_IV->SANDBOX",
        "SANDBOX->ACT_V",
        "ACT_V->CHECKER",
        "CHECKER->ACT_VI",
        "ACT_VI->ACT_VII",
    )
)


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate configuration key: {key}")
        result[key] = value
    return result


# The core panel (five seats) is the default; the full panel is kept as an option.
PANEL_MODES = ("core", "full")


def _closed(value: object, fields: set[str], name: str) -> dict:
    if type(value) is not dict or set(value) != fields:
        raise ValueError(f"{name} has missing or unknown fields")
    return value


def load_live_configuration(path: Path) -> dict:
    if path.is_symlink() or not 0 < path.stat().st_size <= 131072:
        raise ValueError("bounded regular live configuration required")
    raw = path.read_bytes()
    if len(raw) > 131072:
        raise ValueError("live configuration exceeds size ceiling")
    value = json.loads(raw, object_pairs_hook=_unique)
    _closed(
        value,
        {"schema_version", "repo_root", "request", "native_host", "instructions", "execution"},
        "live configuration",
    )
    if value["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported live configuration schema")
    host = _closed(value["native_host"], {"path", "sha256"}, "native host")
    if type(host["sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", host["sha256"]) is None:
        raise ValueError("explicit native binary SHA256 required")
    _closed(
        value["execution"],
        {
            "provider",
            "model",
            "routing_config",
            "env_file",
            "output_dir",
            "max_cost_microusd",
            "max_output_tokens",
            "selected_characters",
            "panel_mode",
            "case_json",
        },
        "execution",
    )
    settings = value["execution"]
    if settings["provider"] != "openrouter":
        raise ValueError("live panel uses the existing OpenRouter seat gateway")
    for name, minimum, maximum in (
        ("max_cost_microusd", 1, 2**63 - 1),
        ("max_output_tokens", 1, 65536),
    ):
        if type(settings[name]) is not int or not minimum <= settings[name] <= maximum:
            raise ValueError(f"invalid {name}")
    roles = settings["selected_characters"]
    if (
        type(roles) is not list
        or any(type(v) is not str or not v for v in roles)
        or len(roles) != len(set(roles))
        or not {"gauge_breaker", "defect_hunter", "primal_dual"}.issubset(roles)
    ):
        raise ValueError("distinct runtime roles must include gauge_breaker, defect_hunter and primal_dual")
    if settings["panel_mode"] not in PANEL_MODES:
        raise ValueError("panel_mode must be core or full")
    for name in ("repo_root",):
        if type(value[name]) is not str or not Path(value[name]).is_absolute():
            raise ValueError(f"absolute {name} required")
    for field in ("path",):
        if type(host[field]) is not str or not Path(host[field]).is_absolute():
            raise ValueError("absolute native host path required")
    return value


def request_from_configuration(config: dict) -> AdversaryBoutRequestV1:
    wire = dict(config["request"])
    if wire.pop("schema_version", None) != "core.adversary.bout-request.v1":
        raise ValueError("exact Adversary request schema required")
    request = AdversaryBoutRequestV1(**wire)
    if request.fixture_mode:
        raise ValueError("live configuration must bind a non-fixture request")
    if request.carrier_context.get("live_execution") != execution_binding(config):
        raise ValueError("execution settings differ from the signed request binding")
    return request


def execution_binding(config: dict) -> dict:
    settings = config["execution"]
    routing = Path(settings["routing_config"])
    if routing.is_symlink() or not routing.is_file():
        raise ValueError("regular routing configuration required")
    case = SymbolGameRequestV1(settings["case_json"]) if settings["case_json"] is not None else None
    return {
        "provider": settings["provider"],
        "model": settings["model"],
        "routing_config_sha256": "sha256:" + hashlib.sha256(routing.read_bytes()).hexdigest(),
        "max_cost_microusd": settings["max_cost_microusd"],
        "max_output_tokens": settings["max_output_tokens"],
        "selected_characters": settings["selected_characters"],
        "panel_mode": settings["panel_mode"],
        "output_dir": settings["output_dir"],
        "case_sha256": "sha256:" + hashlib.sha256(case.case_json.encode()).hexdigest()
        if case
        else None,
        "native_host_sha256": config["native_host"]["sha256"],
    }


def _port(value: dict) -> PortSpecV3:
    _closed(
        value,
        {"name", "colour_id", "schema_ref", "schema_digest", "validator_ref", "validator_digest"},
        "task port",
    )
    return PortSpecV3(
        value["name"],
        ColourId(value["colour_id"]),
        SchemaRef(value["schema_ref"]),
        ContentDigest.sha256(value["schema_digest"]),
        value["validator_ref"],
        ContentDigest.sha256(value["validator_digest"]),
    )


def _port_wire(port: PortSpecV3) -> dict:
    return {
        "name": port.name,
        "colour_id": str(port.colour_id),
        "schema_ref": str(port.schema_ref),
        "schema_digest": port.schema_digest.hex_digest,
        "validator_ref": port.validator_ref,
        "validator_digest": port.validator_digest.hex_digest,
    }


def _node(value: dict, depth: int = 0) -> PlanNodeV01:
    if depth > 16:
        raise ValueError("route depth ceiling exceeded")
    _closed(value, {"operation_id", "children"}, "route node")
    if type(value["children"]) is not list or len(value["children"]) > 128:
        raise ValueError("bounded child list required")
    children = []
    for child in value["children"]:
        _closed(child, {"slot", "node"}, "route binding")
        if type(child["slot"]) is not int:
            raise ValueError("exact integer slot required")
        children.append((child["slot"], _node(child["node"], depth + 1)))
    return PlanNodeV01(value["operation_id"], tuple(children))


def configured_ingress(config: dict) -> SignedOeopInstructionIngress:
    request = request_from_configuration(config)
    profile = resolve_swarm_type_profile(request.swarm_type)
    instruction = _closed(
        config["instructions"],
        {
            "domain_id",
            "routes",
            "task_shape",
            "manifest_path",
            "signature_path",
            "allowed_signers_path",
            "ssh_keygen",
        },
        "instructions",
    )
    shape = _closed(
        instruction["task_shape"],
        {
            "request_digest",
            "workload_profile_id",
            "workload_profile_digest",
            "domain_id",
            "inputs",
            "output",
            "required_operation_ids",
            "allowed_effects",
            "allowed_tool_refs",
            "max_nodes",
            "max_instruction_bytes",
        },
        "task shape",
    )
    task = AdversaryTaskShapeV01(
        shape["request_digest"],
        shape["workload_profile_id"],
        shape["workload_profile_digest"],
        shape["domain_id"],
        tuple(_port(v) for v in shape["inputs"]),
        _port(shape["output"]),
        frozenset(shape["required_operation_ids"]),
        frozenset(shape["allowed_effects"]),
        frozenset(shape["allowed_tool_refs"]),
        shape["max_nodes"],
        shape["max_instruction_bytes"],
    )
    routes = []
    for row in instruction["routes"]:
        _closed(row, {"route_id", "source_kind", "source_paths", "root"}, "route")
        routes.append(
            OeopSourceRouteV01(
                row["route_id"],
                profile.specialization_id,
                workload_profile_digest(profile),
                instruction["domain_id"],
                tuple(row["source_paths"]),
                _node(row["root"]),
                row["source_kind"],
            )
        )
    return SignedOeopInstructionIngress(
        repo_root=Path(config["repo_root"]),
        workload_profile=profile,
        domain_id=instruction["domain_id"],
        route_specs=tuple(routes),
        task_shape=task,
        manifest_path=Path(instruction["manifest_path"]),
        signature_path=Path(instruction["signature_path"]),
        allowed_signers_path=Path(instruction["allowed_signers_path"]),
        ssh_keygen=instruction["ssh_keygen"],
    )


@contextmanager
def configured_native_gate(config: dict):
    host = config["native_host"]
    gate = load_native_anti_skill_gate(Path(host["path"]), host["sha256"])
    if isinstance(gate, Err):
        raise ValueError(f"{gate.error.code}: {gate.error.message}")
    previous = os.environ.get("CORE_SYMBOL_GAME_HOST")
    os.environ["CORE_SYMBOL_GAME_HOST"] = host["path"]
    try:
        yield gate.value
    finally:
        if previous is None:
            os.environ.pop("CORE_SYMBOL_GAME_HOST", None)
        else:
            os.environ["CORE_SYMBOL_GAME_HOST"] = previous


def prepare_live_configuration(
    *,
    repo_root: Path,
    destination: Path,
    request: AdversaryBoutRequestV1,
    native_host: Path,
    native_host_sha256: str,
    execution: dict,
    reviewer: str,
    allowed_signers: Path,
    signing_key: Path | None = None,
    ssh_keygen: str = "ssh-keygen",
) -> Path:
    """Create a reviewable exact-task draft; sign only with an explicit existing key."""
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._@+-]{0,127}", reviewer) is None:
        raise ValueError("explicit reviewer identity required")
    if (
        re.fullmatch(r"[0-9a-f]{64}", native_host_sha256) is None
        or hashlib.sha256(native_host.read_bytes()).hexdigest() != native_host_sha256
    ):
        raise ValueError("native executable differs from its explicit expected SHA256")
    if execution["provider"] != "openrouter":
        raise ValueError("live panel uses the existing OpenRouter seat gateway")
    for name, maximum in (("max_cost_microusd", 2**63 - 1), ("max_output_tokens", 65536)):
        if type(execution[name]) is not int or not 1 <= execution[name] <= maximum:
            raise ValueError(f"positive bounded {name} required")
    roles = execution["selected_characters"]
    if (
        type(roles) is not list
        or any(type(role) is not str or not role for role in roles)
        or len(set(roles)) != len(roles)
        or not {"gauge_breaker", "defect_hunter", "primal_dual"}.issubset(roles)
    ):
        raise ValueError("distinct runtime roles must include gauge_breaker, defect_hunter and primal_dual")
    if execution.get("panel_mode") not in PANEL_MODES:
        raise ValueError("panel_mode must be core or full")
    canonical_output = repo_root.absolute() / "_ic" / "darpa" / "adversary"
    if Path(execution["output_dir"]).absolute() != canonical_output:
        raise ValueError("live output directory must be the canonical repository Adversary custody")
    if (
        allowed_signers.resolve().is_relative_to(repo_root.resolve())
        or allowed_signers.is_symlink()
    ):
        raise ValueError("operator signer trust must be external to the repository")
    if signing_key is not None and not allowed_signers.is_file():
        raise ValueError("signing requires an existing operator allowed_signers file")
    if signing_key is not None and (
        not signing_key.is_file() or signing_key.resolve().is_relative_to(repo_root.resolve())
    ):
        raise ValueError("existing external signing key required")
    config = {
        "schema_version": SCHEMA_VERSION,
        "repo_root": str(repo_root.absolute()),
        "native_host": {"path": str(native_host.absolute()), "sha256": native_host_sha256},
        "execution": execution,
    }
    request = AdversaryBoutRequestV1(
        **{
            key: value
            for key, value in asdict(request).items()
            if key not in ("schema_version", "carrier_context")
        },
        carrier_context={**request.carrier_context, "live_execution": execution_binding(config)},
    )
    config["request"] = asdict(request)
    profile = resolve_swarm_type_profile(request.swarm_type)
    if (
        request.max_rounds > profile.budget.max_rounds
        or request.compute_budget > profile.budget.compute_budget
        or execution["max_cost_microusd"] > profile.budget.max_cost_microusd
    ):
        raise ValueError("live round, compute and cost budgets must narrow the selected profile")
    profile_digest = workload_profile_digest(profile)
    root_node = PlanNodeV01("adversary-claim-audit", ((0, PlanNodeV01("adversary-scope-falsifier")),))
    paths = (
        "operads/catalog/contracts/v1/adversary_claim_audit.json",
        "operads/catalog/contracts/v1/adversary_scope_falsifier.json",
    )
    route = OeopSourceRouteV01(
        "route.adversary_claim_audit",
        profile.specialization_id,
        profile_digest,
        "claims",
        paths,
        root_node,
        "typed_contracts",
    )
    documents = read_route_documents(repo_root, route)
    effects = frozenset(("read_subject", "emit_finding"))
    plan = compile_candidate_plan(documents, root_node, allowed_effects=effects)
    scene_config = request.carrier_context.get("scene_orchestration")
    if "scene_orchestration" in request.carrier_context:
        scenes = compile_scene_orchestration(
            repo_root,
            scene_config,
            plan,
            routing_path=Path(execution["routing_config"]),
            compute_budget=request.compute_budget,
        )
        request = replace(
            request, carrier_context={**request.carrier_context, "scene_orchestration": scenes}
        )
        config["request"] = asdict(request)
    task = AdversaryTaskShapeV01(
        instruction_request_digest(request),
        profile.specialization_id,
        profile_digest,
        "claims",
        plan.inputs,
        plan.output,
        frozenset(plan.operation_ids),
        effects,
    )
    candidate = AdversaryCandidateRouteV01(
        route.route_id,
        route.workload_profile_id,
        route.workload_profile_digest,
        route.domain_id,
        documents,
        root_node,
    )
    selected = select_candidate_plan(task, (candidate,))
    manifest = {
        "schema_version": SCHEMA,
        "decision": "APPROVE",
        "reviewer_identity": reviewer,
        "authority_effect": "None",
        "request_digest": task.request_digest,
        "task_shape_digest": selected.task_shape_digest,
        "workload_profile_id": task.workload_profile_id,
        "workload_profile_digest": task.workload_profile_digest,
        "domain_id": task.domain_id,
        "selection_digest": selected.selection_digest,
        "route_id": selected.route_id,
        "plan_digest": plan.plan_digest,
        "source_snapshot_digest": source_snapshot_digest(selected),
    }
    destination = destination.absolute()
    config["instructions"] = {
        "domain_id": task.domain_id,
        "routes": [
            {
                "route_id": route.route_id,
                "source_kind": "typed_contracts",
                "source_paths": list(paths),
                "root": {
                    "operation_id": root_node.operation_id,
                    "children": [
                        {
                            "slot": 0,
                            "node": {"operation_id": "adversary-scope-falsifier", "children": []},
                        }
                    ],
                },
            }
        ],
        "task_shape": {
            "request_digest": task.request_digest,
            "workload_profile_id": task.workload_profile_id,
            "workload_profile_digest": task.workload_profile_digest,
            "domain_id": task.domain_id,
            "inputs": [_port_wire(v) for v in task.inputs],
            "output": _port_wire(task.output),
            "required_operation_ids": sorted(task.required_operation_ids),
            "allowed_effects": sorted(task.allowed_effects),
            "allowed_tool_refs": [],
            "max_nodes": task.max_nodes,
            "max_instruction_bytes": task.max_instruction_bytes,
        },
        "manifest_path": str(destination / "instruction_manifest.json"),
        "signature_path": str(destination / "instruction_manifest.json.sig"),
        "allowed_signers_path": str(allowed_signers.absolute()),
        "ssh_keygen": ssh_keygen,
    }
    outputs = (
        ("request.json", canonical(config["request"])),
        ("instruction_manifest.json", canonical(manifest)),
        ("live_config.json", canonical(config)),
    )
    if len(outputs[2][1]) > 131072:
        raise ValueError("prepared configuration exceeds the live 128KiB ceiling")
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in outputs:
        with (destination / name).open("xb") as stream:
            stream.write(raw)
    if signing_key is not None:
        try:
            subprocess.run(
                [
                    ssh_keygen,
                    "-Y",
                    "sign",
                    "-f",
                    str(signing_key),
                    "-n",
                    SIGNATURE_NAMESPACE,
                    str(destination / "instruction_manifest.json"),
                ],
                check=True,
                capture_output=True,
                timeout=30,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(
                "OpenSSH signing failed; deployment remains an unsigned draft"
            ) from exc
    return destination / "live_config.json"


def _scene_catalog(repo_root: Path, routing_path: Path) -> tuple[set[str], set[str], set[str]]:
    import yaml

    from .scenes.repository import YamlSceneRepository

    scenes = {scene.id for scene in YamlSceneRepository(repo_root).load_scenes()}
    gate_path = (
        repo_root / "pfp/infrastructure/yaml/gates/gate_register.yaml"
    )
    register = yaml.safe_load(gate_path.read_text(encoding="utf-8"))
    gates = {
        row["gate_id"] for kind in ("primary_gates", "empirical_gates") for row in register[kind]
    }
    routing = yaml.safe_load(routing_path.read_text(encoding="utf-8"))
    # Existing routing names are ASCII display names; native routing remains the
    # authoritative canonical-key/seat validator before any provider dispatch.
    seats = {
        "seat_" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        for name in routing["seats"]
        if type(name) is str and name.isascii()
    }
    return scenes, gates, seats


def _scene_attachment(value: dict, gate_id: str, plan: CandidateInstructionPlanV01) -> dict:
    references = {"gate_id", "skill_id"}
    bound_fields = {"plan_digest", "source_digests", "ordered_operand_bodies"}
    if type(value) is not dict or set(value) not in (references, references | bound_fields):
        raise ValueError("scene attachment requires an exact typed skill reference")
    if value["gate_id"] != gate_id or value["skill_id"] not in plan.operation_ids:
        raise ValueError("scene attachment must bind its stage gate and a selected typed operation")
    bound = {
        "gate_id": gate_id,
        "skill_id": value["skill_id"],
        "plan_digest": plan.plan_digest,
        "source_digests": [list(pair) for pair in plan.source_digests],
        "ordered_operand_bodies": list(plan.ordered_operand_bodies),
    }
    if set(value) != references and value != bound:
        raise ValueError("scene attachment differs from the compiled signed instruction plan")
    return bound


def _scene_stage(
    value: dict, catalog: tuple[set[str], set[str], set[str]], plan: CandidateInstructionPlanV01
) -> dict:
    scenes, gates, seats = catalog
    _closed(
        value,
        {"scene_id", "seat_ids", "gate_id", "gate_payload", "attachments", "fallback_scene_id"},
        "scene stage",
    )
    if value["scene_id"] not in scenes or value["gate_id"] not in gates:
        raise ValueError("scene or gate is absent from its canonical catalog")
    chosen = value["seat_ids"]
    if (
        type(chosen) is not list
        or not 1 <= len(chosen) <= 22
        or any(type(seat) is not str or seat not in seats for seat in chosen)
        or len(chosen) != len(set(chosen))
    ):
        raise ValueError("scene seats must be distinct exact native routing IDs")
    if type(value["gate_payload"]) is not dict:
        raise ValueError("scene gate requires an explicit witness object")
    attachments = value["attachments"]
    if type(attachments) is not list or len(attachments) > len(set(plan.operation_ids)):
        raise ValueError("scene attachments exceed selected typed operations")
    bound = [_scene_attachment(row, value["gate_id"], plan) for row in attachments]
    if len({row["skill_id"] for row in bound}) != len(bound):
        raise ValueError("scene typed attachment references must be unique")
    return {**value, "attachments": bound}


def _scene_adjacency(stages: list[dict], edges: list[dict]) -> dict[str, set[str]]:
    stage_ids = {stage["scene_id"] for stage in stages}
    adjacency = {scene: set() for scene in stage_ids}
    for stage in stages:
        fallback = stage["fallback_scene_id"]
        if fallback is not None:
            if type(fallback) is not str or fallback not in stage_ids:
                raise ValueError("fallback must identify a declared scene stage")
            adjacency[stage["scene_id"]].add(fallback)
    if type(edges) is not list or len(edges) > 64:
        raise ValueError("scene outcome edges must be a bounded list")
    seen = set()
    for edge in edges:
        _closed(edge, {"from_scene_id", "to_scene_id", "on_status"}, "scene outcome edge")
        if (
            edge["from_scene_id"] not in stage_ids
            or edge["to_scene_id"] not in stage_ids
            or edge["on_status"] not in ("PASS", "HOLD", "REFUSE", "ERROR")
        ):
            raise ValueError("scene edge endpoint or gate outcome is invalid")
        key = (edge["from_scene_id"], edge["on_status"])
        if key in seen:
            raise ValueError("scene outcome routing must be deterministic")
        seen.add(key)
        adjacency[edge["from_scene_id"]].add(edge["to_scene_id"])
    return adjacency


def _scene_routes(record: dict, stages: list[dict]) -> None:
    stage_ids = {stage["scene_id"] for stage in stages}
    if len(stage_ids) != len(stages):
        raise ValueError("scene stage IDs must be unique")
    entries = record["entry_scenes"]
    if (
        type(entries) is not dict
        or not entries
        or not set(entries) <= TRANSITION_EDGES
        or any(type(scene) is not str or scene not in stage_ids for scene in entries.values())
    ):
        raise ValueError("scene entries must bind actual phase edges to declared stages")
    adjacency = _scene_adjacency(stages, record["edges"])
    reachable, pending = set(), list(entries.values())
    while pending:
        scene = pending.pop()
        if scene not in reachable:
            reachable.add(scene)
            pending.extend(adjacency[scene] - reachable)
    if reachable != stage_ids:
        raise ValueError("scene plan contains unreachable stages")


def compile_scene_orchestration(
    repo_root: Path,
    value: dict,
    plan: CandidateInstructionPlanV01,
    *,
    routing_path: Path,
    compute_budget: int,
) -> dict:
    """Compile catalog refs into the same signed plan; no provider or gate is executed."""
    _closed(
        value,
        {"schema_version", "max_steps", "max_visits_per_scene", "entry_scenes", "stages", "edges"},
        "scene orchestration",
    )
    if value["schema_version"] != SCENE_SCHEMA:
        raise ValueError("unsupported scene orchestration schema")
    for field, maximum in (("max_steps", min(64, compute_budget - 7)), ("max_visits_per_scene", 8)):
        if type(value[field]) is not int or not 1 <= value[field] <= maximum:
            raise ValueError(f"scene {field} must fit the shared compute budget")
    if type(value["stages"]) is not list or not 1 <= len(value["stages"]) <= 10:
        raise ValueError("scene orchestration requires one to ten canonical stages")
    catalog = _scene_catalog(repo_root, routing_path)
    stages = [_scene_stage(stage, catalog, plan) for stage in value["stages"]]
    _scene_routes(value, stages)
    return json.loads(canonical({**value, "stages": stages}))


def _scene_plan(path: Path | None) -> dict | None:
    if path is None:
        return None
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 65536:
        raise ValueError("scene plan must be a regular JSON object of at most 64KiB")
    raw = path.read_bytes()
    if len(raw) > 65536:
        raise ValueError("scene plan exceeds 64KiB")

    def reject_float(value):
        raise ValueError(
            "scene numbers require exact integers or rational strings, not floating-point tokens"
        )

    value = json.loads(raw, object_pairs_hook=_unique, parse_float=reject_float)
    if type(value) is not dict:
        raise ValueError("scene plan must be an object")
    canonical(value)  # Refuse nonfinite numbers before preparing any deployment.
    return value


def _case(path: Path | None, checker: str | None):
    if path is None:
        if checker is not None:
            raise ValueError("--checker requires --case or a prepared case")
        return None
    if not 0 < path.stat().st_size <= 16384:
        raise ValueError("finite case must fit the existing 16KiB request ceiling")
    return SymbolGameRequestV1(path.read_text(encoding="utf-8"))


def _carrier_context(path: Path | None) -> dict:
    if path is None:
        return {}
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 65536:
        raise ValueError("carrier context must be a regular JSON file of at most 64KiB")
    raw = path.read_bytes()
    if len(raw) > 65536:
        raise ValueError("carrier context exceeds 64KiB")

    def refuse_constant(value):
        raise ValueError(f"nonfinite carrier JSON value: {value}")

    context = json.loads(raw, object_pairs_hook=_unique, parse_constant=refuse_constant)
    if type(context) is not dict or "live_execution" in context:
        raise ValueError(
            "carrier context must be an object without the reserved live_execution field"
        )
    return context


def prepare_cli_configuration(parsed, *, task_key: str) -> Path:
    from operating_system.adapters.intelligence_custody.intelligence_root import (
        try_resolve_intelligence_repo_root,
    )

    from .seat_routing_loader import DEFAULT_CONFIG_PATH

    if not parsed.objective or not parsed.native_host or not parsed.native_host_sha256:
        raise ValueError("--objective, --native-host and --native-host-sha256 are required")
    if parsed.max_cost_microusd is None or parsed.max_cost_microusd <= 0:
        raise ValueError("explicit positive --max-cost-microusd required")
    root = (
        parsed.repo_root.absolute()
        if parsed.repo_root
        else try_resolve_intelligence_repo_root().unwrap()
    )
    case = _case(parsed.case, parsed.checker)
    execution = {
        "provider": parsed.provider,
        "model": parsed.model,
        "routing_config": str((parsed.routing_config or DEFAULT_CONFIG_PATH).absolute()),
        "env_file": str(parsed.env_file.absolute()) if parsed.env_file else None,
        "output_dir": str(
            parsed.output_dir.absolute() if parsed.output_dir else root / "_ic" / "darpa" / "adversary"
        ),
        "max_cost_microusd": parsed.max_cost_microusd,
        "max_output_tokens": parsed.max_output_tokens
        if parsed.max_output_tokens is not None
        else 1024,
        "selected_characters": [v.strip() for v in parsed.selected_characters.split(",")]
        if parsed.selected_characters
        else ["gauge_breaker", "defect_hunter", "primal_dual"],
        "panel_mode": parsed.panel_mode,
        "case_json": case.case_json if case else None,
    }
    carrier = _carrier_context(parsed.carrier_context)
    scene_config = _scene_plan(parsed.scene_plan)
    if scene_config is not None:
        if "scene_orchestration" in carrier:
            raise ValueError("choose --scene-plan or carrier scene_orchestration, not both")
        carrier["scene_orchestration"] = scene_config
    request = AdversaryBoutRequestV1(
        parsed.objective,
        task_key,
        max_rounds=parsed.max_rounds,
        fixture_mode=False,
        request_external_admission=parsed.request_admission,
        compute_budget=parsed.compute_budget,
        swarm_type=parsed.swarm_type,
        carrier_context=carrier,
    )
    return prepare_live_configuration(
        repo_root=root,
        destination=parsed.config_dir,
        request=request,
        native_host=parsed.native_host,
        native_host_sha256=parsed.native_host_sha256,
        execution=execution,
        reviewer=parsed.reviewer,
        allowed_signers=parsed.allowed_signers.absolute(),
        signing_key=parsed.signing_key.absolute() if parsed.signing_key else None,
        ssh_keygen=parsed.ssh_keygen,
    )


def prepare_template_configuration(parsed) -> Path:
    """Sign a fresh task using only an existing deployment's operator settings."""
    template = load_live_configuration(parsed.template)
    wire = dict(template["request"])
    if wire.pop("schema_version", None) != "core.adversary.bout-request.v1":
        raise ValueError("exact template request schema required")
    previous = AdversaryBoutRequestV1(**wire)
    if previous.fixture_mode:
        raise ValueError("run-live requires a live deployment template")
    if previous.task_key == parsed.task_key:
        raise ValueError("run-live requires a fresh task key")
    root = (parsed.repo_root or Path(template["repo_root"])).absolute()
    execution = dict(template["execution"])
    execution["max_cost_microusd"] = parsed.max_cost_microusd
    if parsed.max_output_tokens is not None:
        execution["max_output_tokens"] = parsed.max_output_tokens
    if parsed.panel_mode is not None:
        execution["panel_mode"] = parsed.panel_mode
    execution["output_dir"] = str(root / "_ic" / "darpa" / "adversary")
    carrier = {
        key: value for key, value in previous.carrier_context.items() if key != "live_execution"
    }
    scene = _scene_plan(parsed.scene_plan)
    if scene is not None:
        # Raw catalog references replace the prior task's compiled attachment bindings.
        carrier["scene_orchestration"] = scene
    request = replace(
        previous,
        objective=parsed.objective,
        task_key=parsed.task_key,
        max_rounds=parsed.max_rounds if parsed.max_rounds is not None else previous.max_rounds,
        compute_budget=parsed.compute_budget
        if parsed.compute_budget is not None
        else previous.compute_budget,
        fixture_mode=False,
        carrier_context=carrier,
    )
    instruction = template["instructions"]
    if type(instruction) is not dict:
        raise ValueError("template instruction settings must be an object")
    # A request identifier is never interpreted as a directory path.
    task_slug = re.sub(r"[^A-Za-z0-9_.-]", "_", request.task_key)[:64]
    task_digest = hashlib.sha256(request.task_key.encode("ascii")).hexdigest()[:12]
    deployment_root = (
        parsed.deployment_root or parsed.template.absolute().parent.parent
    ).absolute()
    return prepare_live_configuration(
        repo_root=root,
        destination=deployment_root / f"deployment-{task_slug}-{task_digest}",
        request=request,
        native_host=(parsed.native_host or Path(template["native_host"]["path"])).absolute(),
        native_host_sha256=parsed.native_host_sha256,
        execution=execution,
        reviewer=parsed.reviewer,
        allowed_signers=Path(instruction["allowed_signers_path"]).absolute(),
        signing_key=parsed.signing_key.absolute(),
        ssh_keygen=instruction["ssh_keygen"],
    )


def check_cli_overrides(parsed, config: dict, request: AdversaryBoutRequestV1) -> None:
    settings = config["execution"]
    comparisons = {
        "--objective": (parsed.objective, request.objective),
        "--task-key": (parsed.task_key, request.task_key),
        "--max-rounds": (parsed.max_rounds, request.max_rounds),
        "--compute-budget": (parsed.compute_budget, request.compute_budget),
        "--swarm-type": (parsed.swarm_type, request.swarm_type.value),
        "--provider": (parsed.provider, settings["provider"]),
        "--model": (parsed.model, settings["model"]),
        "--max-cost-microusd": (parsed.max_cost_microusd, settings["max_cost_microusd"]),
        "--max-output-tokens": (parsed.max_output_tokens, settings["max_output_tokens"]),
        "--panel": (parsed.panel_mode, settings["panel_mode"]),
        "--native-host-sha256": (parsed.native_host_sha256, config["native_host"]["sha256"]),
        "--request-admission": (parsed.request_admission, request.request_external_admission),
    }
    for option, (given, signed) in comparisons.items():
        if option in parsed.provided_options and given != signed:
            raise ValueError(f"{option} differs from signed request; prepare again")
    for option, given, signed in (
        ("--native-host", parsed.native_host, config["native_host"]["path"]),
        ("--repo-root", parsed.repo_root, config["repo_root"]),
        ("--routing-config", parsed.routing_config, settings["routing_config"]),
        ("--output-dir", parsed.output_dir, settings["output_dir"]),
        ("--env-file", parsed.env_file, settings["env_file"]),
    ):
        if option in parsed.provided_options and (
            signed is None or given.absolute() != Path(signed).absolute()
        ):
            raise ValueError(f"{option} differs from prepared configuration")
    if (
        parsed.selected_characters is not None
        and [v.strip() for v in parsed.selected_characters.split(",")]
        != settings["selected_characters"]
    ):
        raise ValueError("--roles differs from the prepared signed request")
    if (
        parsed.case is not None
        and _case(parsed.case, parsed.checker).case_json != settings["case_json"]
    ):
        raise ValueError("--case differs from signed finite challenge")
    if parsed.checker and settings["case_json"] is None:
        raise ValueError("--checker requires a prepared finite case")


def execute_cli_configuration(parsed):
    from ..runtime import build_adversary_swarm
    from ..use_cases.base_swarm.adversary_swarm import AdversarySwarm

    if parsed.live_config is None:
        raise ValueError("--live requires --live-config; use prepare-live first")
    config = load_live_configuration(parsed.live_config)
    request = request_from_configuration(config)
    check_cli_overrides(parsed, config, request)
    settings = config["execution"]
    with configured_native_gate(config) as gate:
        ingress = configured_ingress(config)
        verified = ingress.pre_dispatch(request)
        if isinstance(verified, Err):
            return config, request, verified
        swarm = build_adversary_swarm(
            AdversarySwarm,
            repo_root=Path(config["repo_root"]),
            swarm_type=request.swarm_type,
            provider=settings["provider"],
            model=settings["model"],
            instruction_ingress=ingress,
            anti_skill_gate=gate,
            routing_config=Path(settings["routing_config"]),
            env_file=Path(settings["env_file"]) if settings["env_file"] else None,
            output_dir=Path(settings["output_dir"]) if settings["output_dir"] else None,
            max_cost_microusd=settings["max_cost_microusd"],
            max_output_tokens=settings["max_output_tokens"],
            selected_characters=tuple(settings["selected_characters"]) or None,
            panel_mode=settings["panel_mode"],
            symbol_game_request=SymbolGameRequestV1(settings["case_json"])
            if settings["case_json"]
            else None,
        )
        result = swarm.run_bout(
            request.objective,
            request.task_key,
            fixture_mode=False,
            carrier_context=request.carrier_context,
            request_external_admission=request.request_external_admission,
            max_rounds=request.max_rounds,
            compute_budget=request.compute_budget,
        )
    return config, request, result
