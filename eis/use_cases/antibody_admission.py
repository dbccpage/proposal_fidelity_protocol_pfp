"""Assess a farmed antibody for external review (`EPIC-OE-PHARMACY-001`).

Parses the admission request (refusing any missing binding), reads the
antibody's observations from a ledger port, and reports whether the distinct
observations reach the caller's threshold. The antibody stays `CANDIDATE`:
this use case computes eligibility for an external review and has no path to
admission.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any, Protocol

from eis.domain.external_admission import (
    AdmissionError,
    AntibodyObservationV1,
    HumanAdmissionApplierV1,
    HumanAntiSkillAdmissionDecisionV1,
)
from eis.domain.pharmacy_catalog import PharmacyCatalogRepository
from eis.domain.pharmacy_models import PharmacyStatus
from eis.infrastructure.native_domain import native_admission
from eis.infrastructure.pharmacy_writer import release_publication_marker


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


def admit_antibody_by_operator(
    antibody_id: str,
    decision: HumanAntiSkillAdmissionDecisionV1,
    *,
    catalog: PharmacyCatalogRepository,
    applier: HumanAdmissionApplierV1 | None = None,
    self_panel: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Screen an antibody via Thymus + fixture polarity, then persist operator admission."""
    from pfp_core.caller_feedback import screen_antibody_with_thymus  # noqa: PLC0415

    loaded = catalog.load_catalog()
    entries = loaded.get("antibodies", {})
    if antibody_id not in entries:
        raise KeyError(antibody_id)
    record = dict(entries[antibody_id])
    producer_actor = record.get("producer_actor", "")
    if isinstance(producer_actor, str) and producer_actor.strip() and decision.issuer == producer_actor:
        raise PermissionError("SELF_ADMISSION_REFUSED: issuer cannot equal producer_actor")

    thymus_receipt = screen_antibody_with_thymus(record, self_panel=self_panel)
    if not thymus_receipt.is_admitted:
        record["pharmacy_status"] = PharmacyStatus.RETIRED.value
        record["revoked"] = True
        catalog.upsert_managed_record(
            record,
            allowed_existing_statuses=frozenset({"candidate", "provisional", "admitted"}),
        )
        raise ValueError(f"AUTOIMMUNE_RULE_REFUSED: {thymus_receipt.rationale}")

    _result, marker_path = catalog.publish_admission(
        antibody_id,
        decision,
        applier=applier or HumanAdmissionApplierV1(),
        self_panel=None,
    )
    release_publication_marker(marker_path)
    admitted_record = dict(catalog.load_catalog()["antibodies"][antibody_id])
    admitted_record["thymus_receipt_sha256"] = thymus_receipt.receipt_sha256
    return catalog.upsert_managed_record(
        admitted_record,
        allowed_existing_statuses=frozenset({"admitted"}),
    )


__all__ = ["ObservationLedgerPort", "admit_antibody_by_operator", "assess_antibody"]
