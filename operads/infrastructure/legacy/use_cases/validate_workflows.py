"""Validates workflow definitions against operad signatures and agent licenses."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from omega_engine_operads.domain.capability_catalog_v1 import (
    decode_capability_catalog,
)

from ..catalog_v2 import NodeAssignmentV1
from ..models import AgentSpecV1, WorkflowSpecV1


@dataclass(frozen=True)
class WorkflowFinding:
    workflow_id: str
    finding_kind: str
    operation: str
    message: str


@dataclass(frozen=True)
class WorkflowValidationReport:
    total_workflows: int
    valid_workflows: int
    findings: tuple[WorkflowFinding, ...]
    unlicensed_workflow_nodes: tuple[dict[str, object], ...] = ()
    authority_effect: str = "None"


class ValidateWorkflowsUseCase:
    """Validates workflows against the operad signature and agent capability slices."""

    def __init__(
        self,
        signature_path: Path | None = None,
        slices_path: Path | None = None,
        catalog_path: Path | None = None,
    ) -> None:
        self.signature_path = signature_path
        self.slices_path = slices_path
        self.catalog_path = catalog_path

    def _load_signature_ops(self) -> dict[str, set[str]]:
        if self.catalog_path is not None:
            catalog = decode_capability_catalog(self.catalog_path.read_bytes())
            return {
                skill.skill_id: set(skill.source_colours) | {skill.target_colour}
                for skill in catalog.skills
            }
        if not self.signature_path or not self.signature_path.exists():
            return {}
        data = json.loads(self.signature_path.read_text(encoding="utf-8"))
        raw_ops = data.get("operations", [])
        if isinstance(raw_ops, list):
            operations: dict[str, set[str]] = {}
            for operation in raw_ops:
                if not isinstance(operation, dict):
                    continue
                key = operation.get("skill_id", operation.get("name", ""))
                if isinstance(key, str) and key:
                    sources = operation.get("source_colours", [])
                    target = operation.get("target_colour", "")
                    if not isinstance(sources, list) or not all(
                        type(item) is str for item in sources
                    ):
                        continue
                    if type(target) is not str:
                        continue
                    operations[key] = set(sources) | ({target} if target else set())
            return operations
        if isinstance(raw_ops, dict):
            return {key: set() for key in raw_ops}
        return {}

    def _load_agent_slices(self) -> dict[str, tuple[set[str], set[str]]]:
        if self.catalog_path is not None:
            catalog = decode_capability_catalog(self.catalog_path.read_bytes())
            return {
                agent.agent_id: (
                    set(agent.licensed_skill_ids),
                    set(agent.licensed_colour_ids),
                )
                for agent in catalog.agents
            }
        if not self.slices_path or not self.slices_path.exists():
            return {}
        data = json.loads(self.slices_path.read_text(encoding="utf-8"))
        raw_agents = data.get("agents", data.get("slices", {}))
        if not isinstance(raw_agents, dict):
            return {}
        agent_slices: dict[str, tuple[set[str], set[str]]] = {}
        for agent_name, slice_info in raw_agents.items():
            if not isinstance(slice_info, dict):
                continue
            licensed = set(slice_info.get("licensed_skills", []))
            colours = set(slice_info.get("sub_operad", []))
            agent_slices[agent_name] = (licensed, colours)
        return agent_slices

    def execute(
        self,
        workflows: Mapping[str, WorkflowSpecV1],
        agents: Mapping[str, AgentSpecV1] | None = None,
        node_assignments: Mapping[str, NodeAssignmentV1] | None = None,
    ) -> WorkflowValidationReport:
        signature_ops = self._load_signature_ops()
        agent_slices = self._load_agent_slices()
        license_validation_requested = (
            self.catalog_path is not None
            or self.slices_path is not None
            or agents is not None
        )

        if agents:
            for name, agent in agents.items():
                declared = (
                    set(agent.licensed_skills),
                    set(agent.licensed_colours),
                )
                projected = agent_slices.get(name)
                if projected is not None and projected != declared:
                    raise ValueError(
                        f"agent capability projection drift for {name!r}"
                    )
                agent_slices[name] = declared

        findings: list[WorkflowFinding] = []
        unlicensed_nodes: list[dict[str, object]] = []
        valid_count = 0

        for wf_id, wf in workflows.items():
            wf_has_errors = False

            for node in wf.pipeline:
                op = node.operation_id
                required_colours = signature_ops.get(op, set())
                if signature_ops and op not in signature_ops:
                    wf_has_errors = True
                    findings.append(
                        WorkflowFinding(
                            workflow_id=wf_id,
                            finding_kind="MISSING_OPERAD_OPERATION",
                            operation=op,
                            message=(
                                f"Operation '{op}' is not registered in "
                                "operad_signature.json"
                            ),
                        )
                    )

                    continue

                if not license_validation_requested:
                    continue

                assignment_key = f"{wf_id}:{node.node_id}"
                assignment = (
                    node_assignments.get(assignment_key)
                    if node_assignments is not None
                    else None
                )
                if node_assignments is not None and assignment is None:
                    wf_has_errors = True
                    findings.append(
                        WorkflowFinding(
                            workflow_id=wf_id,
                            finding_kind="MISSING_NODE_ASSIGNMENT",
                            operation=op,
                            message=f"Node '{node.node_id}' has no explicit agent assignment.",
                        )
                    )
                    unlicensed_nodes.append(
                        {
                            "workflow_id": wf_id,
                            "node_id": node.node_id,
                            "operation": op,
                            "reason": "Missing explicit node assignment.",
                        }
                    )
                    continue

                candidate_agents = (
                    assignment.agent_ids
                    if assignment is not None
                    else tuple(agent_slices)
                )
                if assignment is not None:
                    if assignment.operation_id != op:
                        wf_has_errors = True
                        findings.append(
                            WorkflowFinding(
                                workflow_id=wf_id,
                                finding_kind="ASSIGNMENT_OPERATION_MISMATCH",
                                operation=op,
                                message=(
                                    f"Assignment for node '{node.node_id}' binds "
                                    f"'{assignment.operation_id}', not '{op}'."
                                ),
                            )
                        )
                        continue
                    if set(assignment.required_colours) != required_colours:
                        wf_has_errors = True
                        findings.append(
                            WorkflowFinding(
                                workflow_id=wf_id,
                                finding_kind="ASSIGNMENT_COLOUR_MISMATCH",
                                operation=op,
                                message=(
                                    "Assignment colours do not equal the registered "
                                    "operation boundary."
                                ),
                            )
                        )
                        continue

                covered: list[str] = []
                invalid: list[str] = []
                for agent_name in candidate_agents:
                    if agent_name not in agent_slices:
                        invalid.append(agent_name)
                        continue
                    licensed_ops, colours = agent_slices[agent_name]
                    colour_ok = not colours or required_colours.issubset(colours)
                    if op in licensed_ops and colour_ok:
                        covered.append(agent_name)
                    else:
                        invalid.append(agent_name)

                if assignment is not None and invalid:
                    covered = []
                if not covered:
                    wf_has_errors = True
                    findings.append(
                        WorkflowFinding(
                            workflow_id=wf_id,
                            finding_kind="UNLICENSED_WORKFLOW_NODE",
                            operation=op,
                            message=(
                                f"No declared agent independently covers node '{node.node_id}' "
                                "with the operation and registered colours."
                            ),
                        )
                    )
                    unlicensed_nodes.append(
                        {
                            "workflow_id": wf_id,
                            "node_id": node.node_id,
                            "operation": op,
                            "agents": list(candidate_agents),
                            "reason": "Operation or colour capability is absent.",
                        }
                    )

            if not wf_has_errors:
                valid_count += 1

        return WorkflowValidationReport(
            total_workflows=len(workflows),
            valid_workflows=valid_count,
            findings=tuple(findings),
            unlicensed_workflow_nodes=tuple(unlicensed_nodes),
            authority_effect="None",
        )
