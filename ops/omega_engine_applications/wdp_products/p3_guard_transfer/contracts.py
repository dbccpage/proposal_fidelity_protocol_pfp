"""P3 transferable guard library: typed break-even skeleton.

Exact arithmetic of WDP Appendix Q.4: T_bare = N*v, T_guard = C_0 + N*g + (N - h)*v,
saving = h*v - N*g - C_0, strict benefit iff saving > 0. AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Literal, Protocol

from pydantic import Field, field_validator, model_validator

from omega_engine_applications.wdp_products.base import FrozenModel
from omega_engine_applications.wdp_products.kernel.contracts import TypedRefusal, is_rational_text


class GuardRule(FrozenModel):
    """A learned rejection rule and the instance shape it was proved sound on."""

    rule_id: str = Field(min_length=1)
    source_instance_digest: str = Field(min_length=1)
    soundness_claim: str = Field(min_length=1)
    authority_effect: Literal["None"] = "None"


class BreakEven(FrozenModel):
    """Costs as exact rational strings; counts as integers."""

    candidates: int = Field(ge=0)
    hits: int = Field(ge=0)
    verify_cost: str
    guard_cost: str
    setup_cost: str

    @field_validator("verify_cost", "guard_cost", "setup_cost")
    @classmethod
    def _rational(cls, value: str) -> str:
        if not is_rational_text(value) or Fraction(value) < 0:
            raise ValueError("cost must be a nonnegative exact rational string")
        return value

    @model_validator(mode="after")
    def _hits_bounded(self) -> BreakEven:
        if self.hits > self.candidates:
            raise ValueError("hits cannot exceed candidates")
        return self

    def bare_total(self) -> Fraction:
        return self.candidates * Fraction(self.verify_cost)

    def guarded_total(self) -> Fraction:
        v, g, c0 = Fraction(self.verify_cost), Fraction(self.guard_cost), Fraction(self.setup_cost)
        return c0 + self.candidates * g + (self.candidates - self.hits) * v

    def saving(self) -> Fraction:
        return self.bare_total() - self.guarded_total()

    def strict_benefit(self) -> bool:
        return self.saving() > 0


class GuardTransferChecker(Protocol):
    """Checks that a rule transfers soundly to a target instance and prices it."""

    def transfer(self, rule: GuardRule, target: object) -> GuardRule | TypedRefusal: ...

    def price(self, rule: GuardRule, ledger: BreakEven) -> Fraction: ...


for _model in (GuardRule, BreakEven):
    _model.model_rebuild()
