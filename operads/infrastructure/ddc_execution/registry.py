"""Read canonical signature and capability files without permissive fallbacks."""

import json
import re
from pathlib import Path

from operads.domain.ddc_execution.constants import (
    ADMITTED_FINITE_COLOURS,
)
from operads.domain.ddc_execution.errors import (
    PermissionDeniedError,
    Refusal,
    UnknownMorphismError,
)
from operads.domain.ddc_execution.value_objects import (
    ColourSignature,
    OperadOperation,
)


def safe_skill_id(skill_id: str) -> str:
    if not isinstance(skill_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", skill_id):
        raise UnknownMorphismError(str(skill_id))
    return skill_id


def read_object(path: Path) -> dict:
    try:
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("JSON file exceeds the 1 MiB limit")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON root must be an object")
        return data
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Refusal("OPERAD_REGISTRY_UNAVAILABLE", f"{path}: {exc}") from exc


class FileOperadRegistry:
    def __init__(self, repo_root: Path) -> None:
        canonical = repo_root / "operads"
        self.directory = canonical / "skill_operad/json" if (
            (canonical / "skills").is_dir() or (canonical / "skill_operad").is_dir()
        ) else repo_root / ".agents/skill_operads"

    def _agents(self) -> dict:
        agents = read_object(self.directory / "agent_capability_slices.json").get("agents")
        if not isinstance(agents, dict):
            raise Refusal("OPERAD_REGISTRY_INVALID", "Capability registry agents must be an object")
        for name, agent in agents.items():
            if not isinstance(name, str) or not isinstance(agent, dict):
                raise Refusal("OPERAD_REGISTRY_INVALID", "Invalid agent capability entry")
            licensed = agent.get("licensed_skills")
            if not isinstance(licensed, list) or any(
                not isinstance(item, str) for item in licensed
            ):
                raise Refusal("OPERAD_REGISTRY_INVALID", f"Invalid licensed skills for {name!r}")
        return agents

    def resolve_operation(self, skill_id: str) -> OperadOperation:
        clean_id = safe_skill_id(skill_id.strip())
        self._agents()
        data = read_object(self.directory / "operad_signature.json")
        entries = data.get("operations")
        if not isinstance(entries, list):
            raise Refusal("OPERAD_REGISTRY_INVALID", "operations must be a list")
        found = None
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("skill_id"), str):
                raise Refusal("OPERAD_REGISTRY_INVALID", "Invalid operation declaration")
            operation_id = entry["skill_id"]
            if operation_id in seen:
                raise Refusal("OPERAD_REGISTRY_INVALID", f"Duplicate operation {operation_id!r}")
            seen.add(operation_id)
            if operation_id == clean_id:
                found = entry
        if found is None:
            raise UnknownMorphismError(clean_id)
        sources = found.get("source_colours")
        target = found.get("target_colour")
        arity = found.get("arity")
        if (
            not isinstance(sources, list)
            or any(
                not isinstance(value, str) or value not in ADMITTED_FINITE_COLOURS
                for value in sources
            )
            or target not in ADMITTED_FINITE_COLOURS
            or type(arity) is not int
            or arity != len(sources)
        ):
            raise Refusal("OPERAD_REGISTRY_INVALID", f"Invalid colour signature for {clean_id!r}")
        return OperadOperation(
            clean_id,
            str(found.get("name", clean_id)),
            ColourSignature(tuple(sources), target),
            arity,
            str(found.get("residual_effect", "unknown")),
            bool(found.get("equivariant", False)),
        )

    def check_agent_license(self, agent_id: str | None, skill_id: str) -> None:
        agents = self._agents()
        if agent_id is None:
            return
        if agent_id not in agents or skill_id not in agents[agent_id]["licensed_skills"]:
            raise PermissionDeniedError(agent_id, f"Not licensed for skill {skill_id!r}")
