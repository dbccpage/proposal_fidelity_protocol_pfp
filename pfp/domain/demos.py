"""Demo contracts. A completed experiment has no promotion authority."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Protocol


class DemoRefusal(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    version: str
    title: str
    kind: str
    scope: str
    level: int | None = None
    challenge_id: str | None = None
    front_end: str | None = None
    use_case: str | None = None
    test: str | None = None


class CheckerPort(Protocol):
    def check(self, payload: Any) -> tuple[str, str | None]: ...


class ProposalPort(Protocol):
    def propose(self, prompt: str, scripted_reply: str) -> str: ...


def exact_functional(value: object) -> Fraction:
    """Admit a native rational value; never compare serialized numerals."""
    if type(value) is Fraction:
        return value
    if type(value) not in (int, str):
        raise DemoRefusal("INEXACT_FUNCTIONAL_VALUE")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise DemoRefusal("INVALID_FUNCTIONAL_VALUE") from exc
    if type(value) is str and str(result) != value:
        raise DemoRefusal("NONCANONICAL_FUNCTIONAL_VALUE")
    return result


def strict_descent(before: object, after: object) -> bool:
    return exact_functional(after) < exact_functional(before)


def refuse_model_functionals(value: object) -> None:
    """Model-supplied functional or authority labels are never host evidence."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace("_", "")
            if normalized in {
                "phi",
                "phi1",
                "phi2",
                "phi3",
                "phi4",
                "gamma",
                "gamma2",
                "xi",
                "verified",
                "certified",
                "authorityeffect",
            }:
                raise DemoRefusal("MODEL_FUNCTIONAL_CLAIM", str(key))
            refuse_model_functionals(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            refuse_model_functionals(item)
