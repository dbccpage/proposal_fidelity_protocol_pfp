"""Strict read-only filesystem and in-memory readers for the legacy WAS estate."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

import yaml  # type: ignore[import-untyped]

from operads.domain.capability_catalog_v1 import (
    CapabilityCatalogV1,
    decode_capability_catalog,
)

from .legacy.models import (
    ADMITTED_RESIDUAL,
    DECLARATION_COMPATIBILITY_DEFAULTED,
    DECLARATION_STRICT_EXPLICIT,
    AgentSpecV1,
    LegacyEstateSnapshotV1,
    SkillOperationV1,
    SkillSpecV1,
    WorkflowEdgeV1,
    WorkflowNodeV1,
    WorkflowSpecV1,
    normalize_estate_path,
)

# The closing fence may end the file. Requiring a newline after it made a
# document's meaning depend on an invisible trailing byte: a file whose last
# byte is `---` parsed its full frontmatter in Rust and read as having none
# here, giving the same file two different arities. Both readers now accept
# end-of-input as a closing fence.
# `[ \t\r]*` rather than `\s*`, matching the Rust reader's
# `trim_start_matches([' ', '\t', '\r'])`. `\s` would swallow newlines and let
# the fence match across a blank line.
FRONTMATTER_REGEX = re.compile(r"^---[ \t\r]*\n(.*?)\n---[ \t\r]*(?:\n|\Z)", re.DOTALL)
_EXPLICIT_OPERATION_FIELDS = (
    "operad_source_colours",
    "operad_target_colour",
    "operad_arity",
    "operad_residual",
)


def _canonical_source_digest(text: str) -> str:
    """Hash UTF-8 text after platform-independent LF normalization."""
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


class MissingFrontmatterError(ValueError):
    """A skill document carries no frontmatter block at all."""


def parse_skill_frontmatter(text: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a skill document.

    A document with no frontmatter is refused rather than treated as empty.
    Returning ``{}`` meant every declared field fell to a default, so a skill
    that declared no signature was silently handed a fabricated one -- the same
    silent-defaulting failure that let operad colours drift. The Rust reader
    (`core_oewas::estate`) already refused it; Python now agrees.

    None of the 133 tracked shipped skills is affected: all carry frontmatter.
    """

    match = FRONTMATTER_REGEX.match(text)
    if not match:
        raise MissingFrontmatterError(
            "skill document has no frontmatter block; a skill that declares no "
            "signature must not be given a defaulted one"
        )
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"malformed skill frontmatter: {exc}") from exc
    return data if isinstance(data, dict) else {}


def parse_skill_operation(
    content: str,
    *,
    operation_id: str,
    require_explicit: bool,
) -> SkillOperationV1:
    """Parse one SkillOperationV1. Strict mode refuses defaults and non-unknown residuals."""

    meta = parse_skill_frontmatter(content)
    if require_explicit:
        missing = [field for field in _EXPLICIT_OPERATION_FIELDS if field not in meta]
        if missing:
            raise ValueError(f"missing explicit operation field: {missing[0]}")
        if "authority_effect" in meta and meta["authority_effect"] != "None":
            raise ValueError("authority_effect must be None when declared")
        residual = meta["operad_residual"]
        if residual != ADMITTED_RESIDUAL:
            raise ValueError(
                f"operad_residual must be {ADMITTED_RESIDUAL!r}, got {residual!r}"
            )
        raw_source_colours = meta["operad_source_colours"]
        target_colour = meta["operad_target_colour"]
        arity = meta["operad_arity"]
        declaration_status = DECLARATION_STRICT_EXPLICIT
    else:
        raw_source_colours = meta.get("operad_source_colours", ("State",))
        target_colour = meta.get("operad_target_colour", "State")
        residual = meta.get("operad_residual", ADMITTED_RESIDUAL)
        arity = meta.get("operad_arity")
        if arity is None:
            if not isinstance(raw_source_colours, (list, tuple)):
                raise TypeError("operad_source_colours must be a list or tuple")
            arity = len(tuple(raw_source_colours))
        declaration_status = (
            DECLARATION_STRICT_EXPLICIT
            if all(field in meta for field in _EXPLICIT_OPERATION_FIELDS)
            and residual == ADMITTED_RESIDUAL
            and (
                "authority_effect" not in meta or meta["authority_effect"] == "None"
            )
            else DECLARATION_COMPATIBILITY_DEFAULTED
        )
    if not isinstance(raw_source_colours, (list, tuple)):
        raise TypeError("operad_source_colours must be a list or tuple")
    if type(arity) is not int:
        raise TypeError("operad_arity must be an exact int")
    return SkillOperationV1(
        operation_id=operation_id,
        source_colours=tuple(raw_source_colours),
        target_colour=target_colour,
        arity=arity,
        residual_effect=residual,
        declaration_status=declaration_status,
        authority_effect="None",
    )


class ReadOnlyEstateFSReader:
    """Read-only adapter parsing canonical estate files without mutating them."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir

    def _parse_frontmatter(self, text: str) -> dict[str, Any]:
        return parse_skill_frontmatter(text)

    def _capability_catalog(self, estate_root: Path) -> CapabilityCatalogV1:
        path = estate_root / "skill_operads" / "capability_catalog.v1.json"
        if not path.is_file():
            path = estate_root / "operad" / "capability_catalog.v1.json"
        if not path.is_file():
            raise FileNotFoundError(f"Capability catalog does not exist: {path}")
        return decode_capability_catalog(path.read_bytes())

    def _parse_skill_spec(
        self, *, skill_folder_name: str, file_path: str, content: str
    ) -> SkillSpecV1:
        meta = self._parse_frontmatter(content)
        name = meta.get("name", skill_folder_name)
        operation = parse_skill_operation(
            content, operation_id=name, require_explicit=False
        )
        return SkillSpecV1(
            skill_id=name,
            name=name,
            description=meta.get("description", ""),
            invocation=meta.get("invocation", "discipline"),
            operation=operation,
            family=name.split("-")[0] if "-" in name else "default",
            atoms=(),
            file_path=file_path,
            source_digest=_canonical_source_digest(content),
            authority_effect="None",
        )

    def _parse_agent_spec(
        self, *, agent_name: str, file_path: str, content: str
    ) -> AgentSpecV1:
        meta = self._parse_frontmatter(content)
        name = meta.get("name", agent_name)
        raw_licensed_skills = meta.get("licensed_skills")
        raw_licensed_colours = meta.get("licensed_colours")
        if not isinstance(raw_licensed_skills, list) or not raw_licensed_skills:
            raise TypeError("agent licensed_skills must be a non-empty list")
        if not all(type(item) is str and item for item in raw_licensed_skills):
            raise TypeError("agent licensed_skills must contain non-empty strings")
        if tuple(raw_licensed_skills) != tuple(sorted(set(raw_licensed_skills))):
            raise ValueError("agent licensed_skills must be sorted and unique")
        if not isinstance(raw_licensed_colours, list) or not raw_licensed_colours:
            raise TypeError("agent licensed_colours must be a non-empty list")
        if not all(type(item) is str and item for item in raw_licensed_colours):
            raise TypeError("agent licensed_colours must contain non-empty strings")
        if tuple(raw_licensed_colours) != tuple(sorted(set(raw_licensed_colours))):
            raise ValueError("agent licensed_colours must be sorted and unique")
        if "skills" in meta:
            raise ValueError("legacy agent frontmatter key 'skills' is forbidden")
        raw_tools = meta.get("tools", ())
        if not isinstance(raw_tools, (list, tuple)):
            raise TypeError("agent tools must be a list or tuple")
        return AgentSpecV1(
            agent_id=name,
            name=name,
            description=meta.get("description", ""),
            model=meta.get("model", "opus"),
            licensed_skills=tuple(raw_licensed_skills),
            licensed_colours=tuple(raw_licensed_colours),
            tools=tuple(raw_tools),
            standalone=bool(meta.get("standalone", True)),
            file_path=file_path,
            source_digest=_canonical_source_digest(content),
            authority_effect="None",
        )

    def _parse_workflow_spec(
        self, *, default_id: str, file_path: str, content: str
    ) -> WorkflowSpecV1:
        data = json.loads(content)
        if not isinstance(data, dict):
            raise TypeError("workflow JSON must contain an object")
        workflow_id = data.get("workflow_id", default_id)
        raw_pipeline = data.get("pipeline", [])
        if not isinstance(raw_pipeline, list):
            raise TypeError("workflow pipeline must be a list")
        nodes: list[WorkflowNodeV1] = []
        for index, node in enumerate(raw_pipeline):
            if not isinstance(node, dict):
                raise TypeError("workflow pipeline entries must be objects")
            nodes.append(
                WorkflowNodeV1(
                    node_id=node.get("node_id", f"node_{index}"),
                    slot=int(node.get("slot", index)),
                    operation_id=node.get("operation", ""),
                    authority_effect="None",
                )
            )
        raw_edges = data.get("edges", [])
        if not isinstance(raw_edges, list):
            raise TypeError("workflow edges must be a list")
        edges: list[WorkflowEdgeV1] = []
        for edge in raw_edges:
            if not isinstance(edge, dict):
                raise TypeError("workflow edges must be objects")
            edges.append(
                WorkflowEdgeV1(
                    from_node=edge["from_node"],
                    to_node=edge["to_node"],
                    colour=edge["colour"],
                )
            )
        raw_source_colours = data.get("source_colours", ())
        if not isinstance(raw_source_colours, (list, tuple)):
            raise TypeError("workflow source_colours must be a list or tuple")
        workflow_name = data.get("name", workflow_id)
        if type(workflow_name) is not str:
            raise TypeError("workflow name must be a str")
        return WorkflowSpecV1(
            workflow_id=workflow_id,
            name=workflow_name,
            source_colours=tuple(raw_source_colours),
            target_colour=data.get("target_colour", ""),
            nodes=tuple(nodes),
            edges=tuple(edges),
            file_path=file_path,
            source_digest=_canonical_source_digest(content),
            authority_effect="None",
        )

    def read_skill_frontmatters(self, skills_dir: Path) -> Mapping[str, SkillSpecV1]:
        """Read only the exact skill entrypoints named by the sealed catalog."""
        if not skills_dir.exists() or not skills_dir.is_dir():
            raise FileNotFoundError(f"Skills directory does not exist: {skills_dir}")
        skills: dict[str, SkillSpecV1] = {}
        catalog = self._capability_catalog(skills_dir.parent)
        for declaration in catalog.skills:
            skill_md = skills_dir.parent / declaration.source_path
            content = skill_md.read_bytes().decode("utf-8")
            digest = _canonical_source_digest(content).removeprefix("sha256:")
            if digest != declaration.source_digest:
                raise ValueError(f"catalog source digest drift: {declaration.source_path}")
            skill = self._parse_skill_spec(
                skill_folder_name=skill_md.parent.name,
                file_path=skill_md.relative_to(skills_dir.parent).as_posix(),
                content=content,
            )
            if skill.skill_id in skills:
                raise ValueError(f"duplicate parsed skill id: {skill.skill_id}")
            skills[skill.skill_id] = skill
        return skills

    def read_agent_specs(self, agents_dir: Path) -> Mapping[str, AgentSpecV1]:
        """Read only the exact agent entrypoints named by the sealed catalog."""
        if not agents_dir.exists() or not agents_dir.is_dir():
            raise FileNotFoundError(f"Agents directory does not exist: {agents_dir}")
        agents: dict[str, AgentSpecV1] = {}
        catalog = self._capability_catalog(agents_dir.parent)
        for declaration in catalog.agents:
            agent_md = agents_dir.parent / declaration.source_path
            content = agent_md.read_bytes().decode("utf-8")
            digest = _canonical_source_digest(content).removeprefix("sha256:")
            if digest != declaration.source_digest:
                raise ValueError(f"catalog source digest drift: {declaration.source_path}")
            agent = self._parse_agent_spec(
                agent_name=agent_md.stem,
                file_path=agent_md.relative_to(agents_dir.parent).as_posix(),
                content=content,
            )
            if agent.agent_id in agents:
                raise ValueError(f"duplicate parsed agent id: {agent.agent_id}")
            agents[agent.agent_id] = agent
        return agents

    def read_workflow_specs(self, workflows_dir: Path) -> Mapping[str, WorkflowSpecV1]:
        """Discover and parse direct JSON workflow specifications."""
        if not workflows_dir.exists() or not workflows_dir.is_dir():
            raise FileNotFoundError(
                f"Workflows directory does not exist: {workflows_dir}"
            )
        workflows: dict[str, WorkflowSpecV1] = {}
        for workflow_json in sorted(workflows_dir.glob("*.json")):
            workflow = self._parse_workflow_spec(
                default_id=workflow_json.stem,
                file_path=workflow_json.relative_to(workflows_dir.parent).as_posix(),
                content=workflow_json.read_bytes().decode("utf-8"),
            )
            if workflow.workflow_id in workflows:
                raise ValueError(
                    f"duplicate parsed workflow id: {workflow.workflow_id}"
                )
            workflows[workflow.workflow_id] = workflow
        return workflows

    def read_snapshot(
        self, snapshot: LegacyEstateSnapshotV1
    ) -> tuple[
        Mapping[str, SkillSpecV1],
        Mapping[str, AgentSpecV1],
        Mapping[str, WorkflowSpecV1],
    ]:
        """Parse canonical WAS entries from an immutable in-memory snapshot."""
        skills: dict[str, SkillSpecV1] = {}
        agents: dict[str, AgentSpecV1] = {}
        workflows: dict[str, WorkflowSpecV1] = {}
        for raw_path, raw_bytes in sorted(snapshot.raw_files.items()):
            normalized = normalize_estate_path(raw_path)
            path = PurePosixPath(normalized)
            content = raw_bytes.decode("utf-8")
            if (
                len(path.parts) >= 3
                and path.parts[-3] == "skills"
                and path.name == "SKILL.md"
            ):
                skill = self._parse_skill_spec(
                    skill_folder_name=path.parts[-2],
                    file_path=path.as_posix(),
                    content=content,
                )
                if skill.skill_id in skills:
                    raise ValueError(f"duplicate parsed skill id: {skill.skill_id}")
                skills[skill.skill_id] = skill
            elif (
                len(path.parts) >= 2
                and path.parts[-2] == "agents"
                and path.suffix == ".md"
            ):
                agent = self._parse_agent_spec(
                    agent_name=path.stem,
                    file_path=path.as_posix(),
                    content=content,
                )
                if agent.agent_id in agents:
                    raise ValueError(f"duplicate parsed agent id: {agent.agent_id}")
                agents[agent.agent_id] = agent
            elif (
                len(path.parts) >= 2
                and path.parts[-2] == "workflows"
                and path.suffix == ".json"
            ):
                workflow = self._parse_workflow_spec(
                    default_id=path.stem,
                    file_path=path.as_posix(),
                    content=content,
                )
                if workflow.workflow_id in workflows:
                    raise ValueError(
                        f"duplicate parsed workflow id: {workflow.workflow_id}"
                    )
                workflows[workflow.workflow_id] = workflow
        return skills, agents, workflows

    def write(self, *args: Any, **kwargs: Any) -> None:
        """Fail closed on all write attempts."""
        raise PermissionError(
            "WAS shadow package is strictly read-only: writing to estate is prohibited."
        )
