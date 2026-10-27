"""PFP Infrastructure - Task Family Taxonomy.

AuthorityEffect: None.
Bedrock task family tokens are read from infrastructure/yaml/taxonomy/task_families.yaml.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


TASK_FAMILIES_PATH = (
    Path(__file__).resolve().parent.parent / "yaml" / "taxonomy" / "task_families.yaml"
)


def load_task_family_records() -> list[dict[str, Any]]:
    """Load the maintained catalog from its one declared resource home."""
    path = TASK_FAMILIES_PATH
    data = strict_yaml_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("categories"), list):
        raise ValueError(f"task family catalog {path} has no categories list")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in data["categories"]:
        if not isinstance(item, dict) or type(item.get("id")) is not str or not item["id"]:
            raise ValueError(f"task family catalog {path} has a category without a string id")
        token = item["id"]
        if token in seen:
            raise ValueError(f"duplicate task family token {token!r} in {path}")
        seen.add(token)
        records.append(item)
    if not records:
        raise ValueError(f"task family catalog {path} is empty")
    return records


def _enum_members() -> dict[str, str]:
    return {str(item["id"]): str(item["id"]) for item in load_task_family_records()}


TaskFamilyEnum: type[Enum] = Enum(
    "TaskFamilyEnum",
    _enum_members(),
    type=str,
    module=__name__,
)
TaskFamilyEnum.__doc__ = "Bedrock task family tokens loaded from task_families.yaml."


class TaskFamilyDefinition(BaseModel):
    """One bedrock task family category."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Task family token")
    display_name: str = Field(default="", description="Human-readable title")
    description: str = Field(default="", description="Catalog description")


class TaskFamilyRegistry:
    """Catalog of bedrock task families loaded from YAML."""

    _instance: TaskFamilyRegistry | None = None

    def __init__(self) -> None:
        self._families: dict[str, TaskFamilyDefinition] = {}
        for item in load_task_family_records():
            defn = TaskFamilyDefinition.model_validate(item)
            self._families[defn.id] = defn

    @classmethod
    def get_instance(cls) -> TaskFamilyRegistry:
        if cls._instance is None:
            cls._instance = TaskFamilyRegistry()
        return cls._instance

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._families.keys())


VALID_TASK_FAMILIES = TaskFamilyRegistry.get_instance().all_ids()


def get_valid_task_families() -> frozenset[str]:
    return TaskFamilyRegistry.get_instance().all_ids()
