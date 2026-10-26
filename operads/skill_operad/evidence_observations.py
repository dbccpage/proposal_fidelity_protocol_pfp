"""Fail-closed classification for legacy operad residual observations.

Rows in ``evidence_trace.json`` are useful diagnostics, but neither the legacy
shape nor the current content-addressed recorder binds an artifact, executable,
metric, environment, and independent verifier.  Consequently no row parsed by
this compatibility module can certify contraction, equivalence, or promotion.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

RECORDED_SCHEMA = "omega.operad.execution_trace.v1"


class ResidualObservationError(ValueError):
    """A diagnostic row is malformed and cannot even be replayed as an observation."""


@dataclass(frozen=True)
class ResidualObservation:
    skill_id: str
    run_id: str
    phi_before: float
    phi_after: float
    classification: str
    source_index: int

    @property
    def observed_delta(self) -> float:
        return self.phi_after - self.phi_before

    @property
    def observed_decrease(self) -> bool:
        return self.phi_after < self.phi_before

    @property
    def supports_contractivity(self) -> bool:
        return False

    @property
    def supports_equivalence(self) -> bool:
        return False

    @property
    def supports_promotion(self) -> bool:
        return False


@dataclass(frozen=True)
class LegacyResidualObservation(ResidualObservation):
    """Unsigned pre-schema scalar observation retained for diagnostics only."""


@dataclass(frozen=True)
class RecordedResidualObservation(ResidualObservation):
    """Content-addressed scalar observation; still not an independent certificate."""


def classify_residual_observation(
    row: Mapping[str, Any], source_index: int = 0
) -> ResidualObservation:
    """Classify one ledger row without upgrading it to evidence."""

    if not isinstance(row, Mapping):
        raise ResidualObservationError("residual observation must be an object")
    skill_id = row.get("skill_id")
    run_id = row.get("run_id")
    if not isinstance(skill_id, str) or not skill_id.strip():
        raise ResidualObservationError("skill_id must be a non-empty string")
    if not isinstance(run_id, str) or not run_id.strip():
        raise ResidualObservationError("run_id must be a non-empty string")
    try:
        before = float(row["phi_before"])
        after = float(row["phi_after"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ResidualObservationError("phi values must be numeric") from exc
    if not math.isfinite(before) or not math.isfinite(after):
        raise ResidualObservationError("phi values must be finite")
    if before < 0.0 or after < 0.0:
        raise ResidualObservationError("phi values must be non-negative")

    schema = row.get("schema")
    if schema == RECORDED_SCHEMA and isinstance(row.get("entry_id"), str):
        cls = RecordedResidualObservation
        classification = "RecordedResidualObservation"
    else:
        cls = LegacyResidualObservation
        classification = "LegacyResidualObservation"
    return cls(
        skill_id=skill_id.strip(),
        run_id=run_id.strip(),
        phi_before=before,
        phi_after=after,
        classification=classification,
        source_index=source_index,
    )


def classify_residual_rows(rows: object) -> list[ResidualObservation]:
    if not isinstance(rows, list):
        raise ResidualObservationError("residual ledger must be a JSON array")
    return [classify_residual_observation(row, index) for index, row in enumerate(rows)]
