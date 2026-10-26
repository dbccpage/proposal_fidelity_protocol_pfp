"""Load the task families catalog. AuthorityEffect: None."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from omega_engine_pfp.infrastructure.yaml_loading import strict_yaml_load
from omega_engine_pfp.domain.task_families.task_family_types import (
    TaskFamilyDefinition,
    GroundTruthProvider,
)


class TaskFamilyRegistry:
    """Thread-safe catalog of bedrock and dynamically registered task families."""

    _instance: TaskFamilyRegistry | None = None

    def __init__(self, register_path: Path | None = None) -> None:
        self._families: dict[str, TaskFamilyDefinition] = {}
        self._ground_truth_providers: dict[str, GroundTruthProvider] = {}
        self._register_path = register_path
        self._load_canonical_register()

    @classmethod
    def get_instance(cls, register_path: Path | None = None) -> TaskFamilyRegistry:
        if cls._instance is None:
            cls._instance = TaskFamilyRegistry(register_path=register_path)
            from omega_engine_pfp.domain.value_objects.taxonomy import (
                register_task_family_provider,
            )

            register_task_family_provider(
                lambda: cls._instance.all_family_ids() if cls._instance is not None else ()
            )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def _load_canonical_register(self) -> None:
        reg_file = self._register_path
        if reg_file is None:
            reg_file = (
                Path(__file__).resolve().parents[1]
                / "yaml"
                / "task_families/task_family_register.yaml"
            )
        if reg_file and reg_file.is_file():
            data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "families" in data:
                for fam in data["families"]:
                    try:
                        defn = TaskFamilyDefinition.model_validate(fam)
                        self._families[defn.family_id] = defn
                    except Exception:
                        pass

    def register(self, definition: TaskFamilyDefinition) -> None:
        self._families[definition.family_id] = definition

    def register_simple(
        self,
        family_id: str,
        display_name: str,
        domain_category: str = "extensional_prompt_domain",
        checker_contract_id: str | None = None,
        supports_refusal: bool = False,
        description: str = "",
        ground_truth_provider: GroundTruthProvider | None = None,
    ) -> TaskFamilyDefinition:
        checker_id = checker_contract_id or f"PFP-EXT-{family_id.upper()}"
        defn = TaskFamilyDefinition(
            family_id=family_id,
            display_name=display_name,
            domain_category=domain_category,
            checker_contract_id=checker_id,
            supports_refusal=supports_refusal,
            is_extensional=True,
            description=description,
        )
        self.register(defn)
        if ground_truth_provider is not None:
            self.register_ground_truth_provider(family_id, ground_truth_provider)
        return defn

    def register_ground_truth_provider(
        self,
        family_id: str,
        provider: GroundTruthProvider,
    ) -> None:
        self._ground_truth_providers[family_id] = provider

    def get_ground_truth(self, family_id: str, difficulty_rung: int = 1) -> dict[str, Any] | None:
        provider = self._ground_truth_providers.get(family_id)
        if provider is not None:
            return provider(difficulty_rung)
        return None

    def get(self, family_id: str) -> TaskFamilyDefinition | None:
        return self._families.get(family_id)

    def is_valid_family(self, family_id: str) -> bool:
        return family_id in self._families

    def all_family_ids(self) -> frozenset[str]:
        return frozenset(self._families.keys())

    def list_families(self) -> list[TaskFamilyDefinition]:
        return list(self._families.values())
