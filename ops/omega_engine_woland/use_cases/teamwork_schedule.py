"""Declared Retinue schedules: which seats contribute, when, and what they see.

A schedule keeps the closed 22-role roster and names one policy per seat. The
coordinator decides each skip deterministically from the run's own history, so a
replay reproduces it exactly, and every skip is reported with its reason. With
no schedule the run is today's full scene-by-scene Retinue.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEDULE_SCHEMA = "omega.woland.retinue-schedule.v1"
# Seats a schedule cannot switch off or blind: the deterministic intake checker, the first
# intake seat (the native intake checkpoint follows it), the builder, the learning reviewer,
# the terminal gate and the learner.
REQUIRED_SEATS = ("hella", "azazello", "jeremy", "koroviev", "woland", "bezdomny")
Activation = Literal["always", "until_quorum", "on_findings", "off"]
View = Literal["chain", "blind"]


class SeatPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    role_id: str = Field(min_length=1)
    activation: Activation = "always"
    view: View = "chain"


class RetinueSchedule(BaseModel):
    """One policy per seat in roster order; the roster itself stays closed."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["omega.woland.retinue-schedule.v1"] = SCHEDULE_SCHEMA
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    seats: tuple[SeatPolicy, ...]
    quorum_clean_reviews: int = Field(default=3, ge=1, le=15)
    repair_cohort: Literal["full", "always_and_finders"] = "full"

    @model_validator(mode="after")
    def validate_required_seats(self):
        roles = [seat.role_id for seat in self.seats]
        if len(set(roles)) != len(roles):
            raise ValueError("SCHEDULE_DUPLICATE_SEAT")
        for seat in self.seats:
            if seat.role_id in REQUIRED_SEATS and (seat.activation != "always" or seat.view != "chain"):
                raise ValueError(f"SCHEDULE_REQUIRED_SEAT: {seat.role_id} must stay always-on with chain view")
        if not set(REQUIRED_SEATS) <= set(roles):
            raise ValueError("SCHEDULE_REQUIRED_SEAT_MISSING")
        return self

    def policy(self, role_id: str) -> SeatPolicy:
        for seat in self.seats:
            if seat.role_id == role_id:
                return seat
        raise ValueError("SCHEDULE_SEAT_UNKNOWN: " + role_id)


def seat_decision(schedule: RetinueSchedule, role_id: str, *, clean_streak: int,
                  cohort_has_findings: bool, repair_cohort: bool,
                  prior_finders: frozenset[str]) -> str | None:
    """Return None when the seat runs, or the reason it is skipped.

    ``clean_streak`` counts consecutive reviews without findings in the current cohort.
    ``prior_finders`` are the seats that raised findings in the cohort the repair answered.
    """
    policy = schedule.policy(role_id)
    if policy.activation == "always":
        return None
    if (repair_cohort and schedule.repair_cohort == "always_and_finders"
            and role_id not in prior_finders):
        return "REPAIR_COHORT_SCOPE"
    if policy.activation == "off":
        return "SCHEDULE_OFF"
    if policy.activation == "until_quorum":
        return "QUORUM_REACHED" if clean_streak >= schedule.quorum_clean_reviews else None
    return None if cohort_has_findings else "NO_COHORT_FINDINGS"


def compile_schedule(name: str, spec: dict, role_order: tuple[str, ...],
                     intake_roles: tuple[str, ...]) -> RetinueSchedule:
    """Build a schedule from declared YAML data; unknown keys and roles are refused."""
    allowed = {"description", "quorum_clean_reviews", "repair_cohort", "intake_activation",
               "review_activation", "review_view", "seats"}
    if type(spec) is not dict or set(spec) - allowed:
        raise ValueError("SCHEDULE_SPEC_INVALID: " + name)
    overrides = spec.get("seats") or {}
    if type(overrides) is not dict or set(overrides) - set(role_order):
        raise ValueError("SCHEDULE_SEAT_UNKNOWN: " + name)
    seats = []
    for role_id in role_order:
        if role_id in REQUIRED_SEATS:
            default = {"activation": "always", "view": "chain"}
        elif role_id in intake_roles:
            default = {"activation": spec.get("intake_activation", "always"), "view": "chain"}
        else:
            default = {"activation": spec.get("review_activation", "always"),
                       "view": spec.get("review_view", "chain")}
        override = overrides.get(role_id, {})
        if type(override) is str:
            override = {"activation": override}
        if type(override) is not dict:
            raise ValueError("SCHEDULE_SEAT_INVALID: " + role_id)
        seats.append(SeatPolicy(role_id=role_id, **{**default, **override}))
    return RetinueSchedule(name=name, seats=tuple(seats),
        quorum_clean_reviews=spec.get("quorum_clean_reviews", 3),
        repair_cohort=spec.get("repair_cohort", "full"))


def select_schedule_thompson(
    schedules: list[str] | tuple[str, ...],
    arm_history: dict[str, dict[str, int | float]],
    random_seed: int = 42,
) -> str:
    """Delegate Thompson sampling schedule selection over measured arm history (L2)."""
    from omega_engine_woland.use_cases.yardstick import thompson_sampling_schedule

    return thompson_sampling_schedule(schedules, arm_history, random_seed=random_seed)

