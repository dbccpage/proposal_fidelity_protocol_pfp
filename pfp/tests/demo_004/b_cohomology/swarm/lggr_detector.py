"""Compatibility result for the unbound LGGR cohomology execution path."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class LggrVerdict:
    is_local_green: bool | None = None
    is_global_red: bool | None = None
    gamma2: Fraction | None = None
    phi1: Fraction | None = None
    cycle_rank: int | None = None
    native_gluing_defect: str | None = None
    ddc_rune: str | None = None
    diagnosis: str = "WOLAND_EXECUTION_UNAVAILABLE"
    status: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_local_green": self.is_local_green,
            "is_global_red": self.is_global_red,
            "gamma2": None,
            "phi1": None,
            "cycle_rank": None,
            "native_gluing_defect": None,
            "ddc_rune": None,
            "diagnosis": self.diagnosis,
            "status": self.status,
        }


class LggrDetector:
    """Do not infer LGGR from guessed cycle rank or substitute solver failures."""

    def __init__(self, host: Any = None) -> None:
        pass

    def evaluate(
        self,
        nodes: Sequence[str],
        edges: Sequence[tuple[str, str]],
        claims: Mapping[tuple[str, str], Fraction],
        faces: Sequence[tuple[str, str, str]] | None = None,
        phi1: Fraction | None = None,
    ) -> LggrVerdict:
        return LggrVerdict()
