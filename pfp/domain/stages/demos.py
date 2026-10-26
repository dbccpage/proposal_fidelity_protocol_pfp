"""Pydantic v2 models for Demos and Demo Catalogs.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr


class CheckResult(BaseModel):
    """Result of an individual demo check assertion."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: StrictStr = Field(min_length=1)
    passed: StrictBool
    observed: Optional[StrictStr] = None
    expected: Optional[StrictStr] = None
    error_message: Optional[StrictStr] = None


class DemoSpec(BaseModel):
    """Specification of an SG-xx or numbered demo task."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: StrictStr = Field(min_length=1)
    title: StrictStr = Field(min_length=1)
    profile: StrictStr = Field(default="standard")
    seed: StrictStr = Field(min_length=1)
    model_seed: StrictStr = Field(default="")
    expectations: Dict[str, str] = Field(default_factory=dict)
    gates: List[StrictStr] = Field(default_factory=list)
    modes: List[StrictStr] = Field(default_factory=list)
    source_sha256: StrictStr = ""
    seed_sha256: StrictStr = ""
    source_path: StrictStr = ""
    sealed_second_task: Optional[StrictStr] = None

    @property
    def demo_id(self) -> str:
        return self.id


class DemoRunReceipt(BaseModel):
    """Machine receipt summarizing the execution of a demo."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    demo_id: StrictStr = Field(min_length=1)
    runner_id: StrictStr = Field(min_length=1)
    all_passed: StrictBool
    checks: List[CheckResult] = Field(default_factory=list)
    duration_sec: float = Field(ge=0.0)
    terminal_status: StrictStr = Field(default="Exact")
    receipt_sha256: StrictStr = Field(default="")
    authority_effect: StrictStr = Field(default="None")


class DemoCatalog(BaseModel):
    """Catalog of available demos."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    version: StrictStr = Field(default="1.0.0")
    demos: List[DemoSpec] = Field(default_factory=list)

    def get_by_id(self, demo_id: str) -> Optional[DemoSpec]:
        for d in self.demos:
            if d.id == demo_id:
                return d
        return None
