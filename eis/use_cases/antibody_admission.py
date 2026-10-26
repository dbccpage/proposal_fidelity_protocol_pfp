"""Assess a farmed antibody for external review (`EPIC-OE-PHARMACY-001`).

Parses the admission request (refusing any missing binding), reads the
antibody's observations from a ledger port, and reports whether the distinct
observations reach the caller's threshold. The antibody stays `CANDIDATE`:
this use case computes eligibility for an external review and has no path to
admission.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping, Protocol

from omega_engine_epistemic_immune_system.domain.external_admission import (
    AdmissionError,
    AntibodyObservationV1,
)
from omega_engine_epistemic_immune_system.infrastructure.native_domain import native_admission


class ObservationLedgerPort(Protocol):
    """Recorded sightings of the defect an antibody guards."""

    def observations_for(self, candidate_digest: str) -> tuple[AntibodyObservationV1, ...]: ...


def assess_antibody(
    payload: Mapping[str, Any],
    *,
    ledger: ObservationLedgerPort,
    required_distinct: int,
) -> dict[str, Any]:
    """Eligibility of one antibody for external review; never an admission."""
    request = native_admission(
        "parse_request", payload=dict(payload) if isinstance(payload, Mapping) else payload
    )
    # Authenticated ledgers bind the entire request, including source and both
    # fixture digests. The legacy port remains count-only evidence.
    bound_reader = getattr(ledger, "observations_for_request", None)
    observations = (
        bound_reader(request)
        if callable(bound_reader)
        else ledger.observations_for(request["candidate_digest"])
    )
    if type(observations) is not tuple:
        raise AdmissionError("BAD_OBSERVATIONS", "observations must be an exact tuple")
    if any(type(item) is not AntibodyObservationV1 for item in observations):
        raise AdmissionError(
            "BAD_OBSERVATIONS", "each observation must be an exact AntibodyObservationV1"
        )
    return native_admission(
        "assess",
        payload=request,
        observations=[asdict(item) for item in observations],
        required_distinct=required_distinct,
    )


__all__ = ["ObservationLedgerPort", "assess_antibody"]
