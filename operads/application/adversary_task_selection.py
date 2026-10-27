"""Deterministic, non-authorizing task-to-candidate-plan selection for Adversary.

The caller supplies an exact task shape and an explicit bounded route set. No
objective-text inference, model tie-break, source-declared admission, or live
dispatch occurs here. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from ..domain.entities.operation_v3 import PortSpecV3
from ..domain.entities.skill_document_v3 import SkillDocumentV3
from .adversary_candidate_plan import (
    _CAPABILITY_NAME,
    _MAX_INSTRUCTION_BYTES,
    _MAX_TREE_NODES,
    CandidateInstructionPlanV01,
    PlanNodeV01,
    PlanRefusal,
    _bound_port,
    compile_candidate_plan,
    port_contract,
)

_ID = re.compile(r"[a-z][a-z0-9_.-]{0,127}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_MAX_ROUTES = 64


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "ascii"
    )


@dataclass(frozen=True, slots=True)
class AdversaryTaskShapeV01:
    """Candidate task contract; its claimed domain/profile need external binding."""

    request_digest: str
    workload_profile_id: str
    workload_profile_digest: str
    domain_id: str
    inputs: tuple[PortSpecV3, ...]
    output: PortSpecV3
    required_operation_ids: frozenset[str] = frozenset()
    allowed_effects: frozenset[str] = frozenset()
    allowed_tool_refs: frozenset[str] = frozenset()
    max_nodes: int = 128
    max_instruction_bytes: int = 65536

    def __post_init__(self) -> None:
        if type(self.request_digest) is not str or _DIGEST.fullmatch(self.request_digest) is None:
            raise PlanRefusal("TASK_SHAPE_INVALID", "request digest")
        if (
            type(self.workload_profile_digest) is not str
            or _DIGEST.fullmatch(self.workload_profile_digest) is None
        ):
            raise PlanRefusal("TASK_SHAPE_INVALID", "workload profile digest")
        for name in ("workload_profile_id", "domain_id"):
            value = getattr(self, name)
            if type(value) is not str or _ID.fullmatch(value) is None:
                raise PlanRefusal("TASK_SHAPE_INVALID", name)
        if (
            type(self.inputs) is not tuple
            or any(type(port) is not PortSpecV3 or not _bound_port(port) for port in self.inputs)
            or type(self.output) is not PortSpecV3
            or not _bound_port(self.output)
        ):
            raise PlanRefusal("TASK_SHAPE_INVALID", "input/output contracts")
        if type(self.required_operation_ids) is not frozenset or any(
            type(value) is not str or _ID.fullmatch(value) is None
            for value in self.required_operation_ids
        ):
            raise PlanRefusal("TASK_SHAPE_INVALID", "required_operation_ids")
        for name in ("allowed_effects", "allowed_tool_refs"):
            values = getattr(self, name)
            if type(values) is not frozenset or any(
                type(value) is not str or _CAPABILITY_NAME.fullmatch(value) is None
                for value in values
            ):
                raise PlanRefusal("TASK_SHAPE_INVALID", name)
        if (
            type(self.max_nodes) is not int or not 1 <= self.max_nodes <= _MAX_TREE_NODES
            or type(self.max_instruction_bytes) is not int
            or not 1 <= self.max_instruction_bytes <= _MAX_INSTRUCTION_BYTES
        ):
            raise PlanRefusal("TASK_SHAPE_INVALID", "node and text budgets")


@dataclass(frozen=True, slots=True)
class AdversaryCandidateRouteV01:
    route_id: str
    workload_profile_id: str
    workload_profile_digest: str
    domain_id: str
    documents: tuple[SkillDocumentV3, ...]
    root: PlanNodeV01
    projection: dict | None = None
    projection_path: str | None = None

    def __post_init__(self) -> None:
        for name in ("route_id", "workload_profile_id", "domain_id"):
            value = getattr(self, name)
            if type(value) is not str or _ID.fullmatch(value) is None:
                raise PlanRefusal("ROUTE_INVALID", name)
        if (
            type(self.workload_profile_digest) is not str
            or _DIGEST.fullmatch(self.workload_profile_digest) is None
        ):
            raise PlanRefusal("ROUTE_INVALID", "workload profile digest")
        if (
            type(self.documents) is not tuple
            or not self.documents
            or type(self.root) is not PlanNodeV01
        ):
            raise PlanRefusal("ROUTE_INVALID", self.route_id)


@dataclass(frozen=True, slots=True)
class SelectedCandidatePlanV01:
    task_shape_digest: str
    route_id: str
    plan: CandidateInstructionPlanV01
    considered_routes: tuple[tuple[str, str, bool], ...]
    applicable_routes: tuple[tuple[str, str], ...]
    selection_digest: str
    admission: str = "Unadmitted"


def task_shape_digest(task: AdversaryTaskShapeV01) -> str:
    """Bind the actual ordered task contract using the historical wire profile."""
    if type(task) is not AdversaryTaskShapeV01:
        raise PlanRefusal("TASK_SHAPE_INVALID", "exact task shape required")
    task_record = {
        "schema": "oewas.adversary.task_shape.v0.1",
        "request_digest": task.request_digest,
        "workload_profile_id": task.workload_profile_id,
        "workload_profile_digest": task.workload_profile_digest,
        "domain_id": task.domain_id,
        "inputs": [port_contract(port) for port in task.inputs],
        "output": port_contract(task.output),
        "required_operation_ids": sorted(task.required_operation_ids),
        "allowed_effects": sorted(task.allowed_effects),
        "allowed_tool_refs": sorted(task.allowed_tool_refs),
        "max_nodes": task.max_nodes,
        "max_instruction_bytes": task.max_instruction_bytes,
    }
    return "sha256:" + hashlib.sha256(_canonical(task_record)).hexdigest()


def select_candidate_plan(
    task: AdversaryTaskShapeV01,
    routes: tuple[AdversaryCandidateRouteV01, ...],
) -> SelectedCandidatePlanV01:
    """Choose the unique least-node plan satisfying all task obligations.

    A malformed matching route refuses the entire selection. A narrower plan
    wins only after exact profile/domain/boundary and required-operation checks;
    equal minima are ambiguous, never
    settled by route order, prose, or a model.
    """
    if (
        type(task) is not AdversaryTaskShapeV01
        or type(routes) is not tuple
        or not 1 <= len(routes) <= _MAX_ROUTES
    ):
        raise PlanRefusal("SELECTION_INPUT_INVALID", "task and bounded route tuple required")
    if any(type(route) is not AdversaryCandidateRouteV01 for route in routes):
        raise PlanRefusal("SELECTION_INPUT_INVALID", "route type")
    route_ids = [route.route_id for route in routes]
    if len(route_ids) != len(set(route_ids)):
        raise PlanRefusal("DUPLICATE_ROUTE_ID", "route ids must be unique")

    considered: list[tuple[AdversaryCandidateRouteV01, CandidateInstructionPlanV01, bool]] = []
    applicable: list[tuple[AdversaryCandidateRouteV01, CandidateInstructionPlanV01]] = []
    for route in sorted(routes, key=lambda item: item.route_id):
        if (
            route.workload_profile_id,
            route.workload_profile_digest,
            route.domain_id,
        ) != (
            task.workload_profile_id,
            task.workload_profile_digest,
            task.domain_id,
        ):
            continue
        plan = compile_candidate_plan(
            route.documents, route.root,
            allowed_effects=task.allowed_effects,
            allowed_tool_refs=task.allowed_tool_refs,
            max_nodes=task.max_nodes,
            max_instruction_bytes=task.max_instruction_bytes,
            projection=route.projection,
            projection_path=route.projection_path,
        )
        matches = (
            tuple(port_contract(port) for port in plan.inputs)
            == tuple(port_contract(port) for port in task.inputs)
            and port_contract(plan.output) == port_contract(task.output)
            and task.required_operation_ids <= set(plan.operation_ids)
        )
        considered.append((route, plan, matches))
        if matches:
            applicable.append((route, plan))
    if not applicable:
        raise PlanRefusal("NO_APPLICABLE_PLAN", f"{task.workload_profile_id}:{task.domain_id}")

    least_nodes = min(plan.operation_count for _, plan in applicable)
    minima = [(route, plan) for route, plan in applicable if plan.operation_count == least_nodes]
    if len(minima) != 1:
        raise PlanRefusal(
            "AMBIGUOUS_APPLICABILITY", ",".join(route.route_id for route, _ in minima)
        )
    route, plan = minima[0]
    task_digest = task_shape_digest(task)
    eligible = tuple((item.route_id, candidate.plan_digest) for item, candidate in applicable)
    considered_rows = tuple(
        (item.route_id, candidate.plan_digest, matches)
        for item, candidate, matches in considered
    )
    selection_record = {
        "schema": "oewas.adversary.candidate_selection.v0.1",
        "task_shape_digest": task_digest,
        "applicable_routes": eligible,
        "considered_routes": considered_rows,
        "selected_route_id": route.route_id,
        "selected_plan_digest": plan.plan_digest,
    }
    return SelectedCandidatePlanV01(
        task_shape_digest=task_digest,
        route_id=route.route_id,
        plan=plan,
        considered_routes=considered_rows,
        applicable_routes=eligible,
        selection_digest="sha256:" + hashlib.sha256(_canonical(selection_record)).hexdigest(),
    )


__all__ = [
    "SelectedCandidatePlanV01", "AdversaryCandidateRouteV01", "AdversaryTaskShapeV01",
    "select_candidate_plan", "task_shape_digest",
]
