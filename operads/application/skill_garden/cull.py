"""Evaluate observed garden usage through the injected nomination policy port."""

from __future__ import annotations

from typing import Protocol

from operations.domain.rop.result import Refusal, Result
from operads.domain.skill_garden.cull import (
    CullPolicy,
    CullReport,
    GardenSnapshot,
)


class CullPolicyPort(Protocol):
    def nominate(
        self, policy: CullPolicy, snapshot: GardenSnapshot
    ) -> Result[CullReport, Refusal]: ...


def nominate(
    policy: CullPolicy, snapshot: GardenSnapshot, *, port: CullPolicyPort
) -> Result[CullReport, Refusal]:
    return port.nominate(policy, snapshot)
