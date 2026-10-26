"""Nomination values; no filesystem or execution authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, NamedTuple


class CullPolicy(NamedTuple):
    window_days: int
    sensor_epoch: datetime
    minimum_ledger_days: int
    new_skill_grace_days: int
    max_candidate_fraction: float
    exempt: dict[str, str]
    approved_by: str
    approved_at: str


class CullReport(NamedTuple):
    refusals: tuple[str, ...]
    candidates: tuple[dict[str, Any], ...]
    exempt: tuple[dict[str, Any], ...]
    in_grace: tuple[dict[str, Any], ...]
    used_recently: tuple[dict[str, Any], ...]
    roster_size: int
    span_days: float

    @property
    def refused(self) -> bool:
        return bool(self.refusals)


class CullPolicyError(RuntimeError):
    """A malformed or unavailable policy boundary, distinct from refusing nomination."""


@dataclass(frozen=True, slots=True)
class SkillObservation:
    skill_id: str
    at_us: int
    date: str


@dataclass(frozen=True, slots=True)
class GardenSnapshot:
    now_us: int
    first_us: int | None
    last_us: int | None
    roster: tuple[str, ...]
    last_used: tuple[SkillObservation, ...]
    births: tuple[SkillObservation, ...]
    parity_green: bool | None
