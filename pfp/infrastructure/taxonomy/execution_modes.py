"""PFP Infrastructure - Execution Modes Taxonomy.

AuthorityEffect: None.
Canonical specification of dispatch modes across the Proposal Fidelity Protocol.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pfp.infrastructure.yaml_loading import strict_yaml_load
from pydantic import BaseModel, ConfigDict, Field


def _load_execution_mode_enum_members() -> dict[str, str]:
    """Load canonical execution mode category identifiers directly from YAML."""
    for candidate_root in [
        Path(__file__).parent.parent / "yaml" / "taxonomy",
    ]:
        reg_file = candidate_root / "execution_modes.yaml"
        if reg_file.is_file():
            try:
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    members: dict[str, str] = {}
                    for item in data["categories"]:
                        if isinstance(item, dict) and "id" in item:
                            val = str(item["id"])
                            name = val.upper()
                            members[name] = val
                    if members:
                        return members
            except Exception:
                pass
    return {
        "OFFLINE_FIXTURE": "offline_fixture",
        "LIVE_MANUAL_DISPATCH": "live_manual_dispatch",
        "LIVE_GATEWAY_DISPATCH": "live_gateway_dispatch",
    }


ExecutionModeEnum: type[Enum] = Enum(
    "ExecutionModeEnum",
    _load_execution_mode_enum_members(),
    type=str,
    module=__name__,
)
ExecutionModeEnum.__doc__ = (
    "Canonical enum of supported execution dispatch modes loaded directly from YAML."
)


class ExecutionModeDefinition(BaseModel):
    """Strongly typed specification of an execution dispatch mode."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(description="Unique slug for the execution mode")
    display_name: str = Field(description="Human-readable title")
    is_live: bool = Field(
        default=False, description="Whether mode dispatches outside the local process"
    )
    spend_usd: float = Field(default=0.0, description="Baseline cost in USD")
    description: str = Field(default="", description="Operational description")


class ExecutionModeRegistry:
    """Catalog of execution dispatch modes loaded from canonical YAML with dynamic extension."""

    _instance: ExecutionModeRegistry | None = None

    def __init__(self) -> None:
        self._modes: dict[str, ExecutionModeDefinition] = {}
        self._load_canonical()

    @classmethod
    def get_instance(cls) -> ExecutionModeRegistry:
        if cls._instance is None:
            cls._instance = ExecutionModeRegistry()
        return cls._instance

    def _load_canonical(self) -> None:
        for candidate_root in [
            Path(__file__).parent.parent / "yaml" / "taxonomy",
        ]:
            reg_file = candidate_root / "execution_modes.yaml"
            if reg_file.is_file():
                data = strict_yaml_load(reg_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "categories" in data:
                    for item in data["categories"]:
                        try:
                            defn = ExecutionModeDefinition.model_validate(item)
                            self._modes[defn.id] = defn
                        except Exception:
                            pass
                    break

        # Fallback guarantee if YAML is missing
        if not self._modes:
            for mode_val in ExecutionModeEnum:
                self._modes[mode_val.value] = ExecutionModeDefinition(
                    id=mode_val.value,
                    display_name=mode_val.value.replace("_", " ").title(),
                )

    def register(self, defn: ExecutionModeDefinition) -> None:
        self._modes[defn.id] = defn

    def is_valid(self, mode_id: str) -> bool:
        return mode_id in self._modes

    def all_ids(self) -> frozenset[str]:
        return frozenset(self._modes.keys())

    def get(self, mode_id: str) -> ExecutionModeDefinition | None:
        return self._modes.get(mode_id)


# Pre-resolved constants
VALID_EXECUTION_MODES = ExecutionModeRegistry.get_instance().all_ids()


def get_valid_execution_modes() -> frozenset[str]:
    return ExecutionModeRegistry.get_instance().all_ids()
