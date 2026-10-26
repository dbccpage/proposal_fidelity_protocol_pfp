"""Bounded Complement Cascade Recruitment (U16).

Effector recruitment cascade capped by an explicit integer budget.
AuthorityEffect: None.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ComplementStage(str, Enum):
    C1_INITIATION = "C1_INITIATION"
    C3_AMPLIFICATION = "C3_AMPLIFICATION"
    MAC_TERMINAL = "MAC_TERMINAL"


@dataclass(frozen=True, slots=True)
class ComplementCascadeReceipt:
    initial_triggers: int
    recruited_effectors: int
    max_recruitment_budget: int
    reached_terminal_mac: bool
    budget_exhausted: bool
    stage: ComplementStage
    authority_effect: str = "None"


@dataclass(frozen=True, slots=True)
class ComplementCascade:
    max_recruitment_budget: int = 10
    amplification_factor: int = 4

    def __post_init__(self) -> None:
        if not isinstance(self.max_recruitment_budget, int) or self.max_recruitment_budget < 1:
            raise ValueError("max_recruitment_budget must be integer >= 1")
        if not isinstance(self.amplification_factor, int) or self.amplification_factor < 1:
            raise ValueError("amplification_factor must be integer >= 1")

    def execute(self, initial_triggers: int) -> ComplementCascadeReceipt:
        if initial_triggers <= 0:
            return ComplementCascadeReceipt(
                initial_triggers=0,
                recruited_effectors=0,
                max_recruitment_budget=self.max_recruitment_budget,
                reached_terminal_mac=False,
                budget_exhausted=False,
                stage=ComplementStage.C1_INITIATION,
            )

        potential = initial_triggers * self.amplification_factor
        recruited = min(potential, self.max_recruitment_budget)
        budget_exhausted = potential >= self.max_recruitment_budget
        reached_mac = recruited >= 3

        if reached_mac:
            stage = ComplementStage.MAC_TERMINAL
        elif recruited > initial_triggers:
            stage = ComplementStage.C3_AMPLIFICATION
        else:
            stage = ComplementStage.C1_INITIATION

        return ComplementCascadeReceipt(
            initial_triggers=initial_triggers,
            recruited_effectors=recruited,
            max_recruitment_budget=self.max_recruitment_budget,
            reached_terminal_mac=reached_mac,
            budget_exhausted=budget_exhausted,
            stage=stage,
        )
