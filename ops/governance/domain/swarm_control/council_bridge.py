"""Legacy council vote assessment; its records cannot verify configured decisions.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

from .council_resolution_status import CouncilResolutionStatus
from .council_resolution_v1 import CouncilResolutionV1
from .council_resolution_verification_result import CouncilResolutionVerificationResult
from .council_vote_choice import CouncilVoteChoice
from .council_vote_record import CouncilVoteRecord
from .quorum_threshold import QuorumThreshold


def _require_sha256(val: str) -> None:
    if (
        not isinstance(val, str)
        or len(val) != 64
        or not all(c in "0123456789abcdefABCDEF" for c in val)
    ):
        raise ValueError(f"Invalid SHA256 hex digest: {val!r}")


def canonical_council_json_bytes(data: Mapping[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_council_resolution(
    council_or_resolution: CouncilResolutionV1 | str,
    resolution_id: str | None = None,
    motion: str | None = None,
    threshold: QuorumThreshold | None = None,
    votes: Sequence[CouncilVoteRecord] = (),
    eligible_members: frozenset[str] | None = None,
    signature_verifier: Any = None,
) -> bool:
    """Legacy records lack bound policy and authenticated ballots and never verify."""
    if isinstance(council_or_resolution, CouncilResolutionV1):
        if council_or_resolution.authority_effect != "None":
            raise ValueError("Council resolution must have authority_effect='None'")
        return False
    raise ValueError(
        "LEGACY_COUNCIL_VERIFICATION_UNSUPPORTED: use assess_advisory_council_votes "
        "for advisory arithmetic; a configured decision requires bound verification"
    )


def _validated_threshold(threshold: QuorumThreshold | None) -> QuorumThreshold:
    t = QuorumThreshold() if threshold is None else threshold
    if type(t) is not QuorumThreshold:
        raise ValueError("threshold must be a QuorumThreshold")
    for value in (t.total_eligible_members, t.min_participating_members):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("threshold member counts must be integers")
    if not 1 <= t.min_participating_members <= t.total_eligible_members:
        raise ValueError("threshold participation must fit the eligible member count")
    fraction = t.required_aye_fraction
    if (
        not isinstance(fraction, (int, float, Fraction))
        or isinstance(fraction, bool)
        or (isinstance(fraction, float) and not math.isfinite(fraction))
        or not 0.5 < fraction <= 1
    ):
        raise ValueError("required_aye_fraction must be finite and greater than 0.5 up to 1")
    return t


def _require_member_id(member_id: str) -> None:
    if type(member_id) is not str or not member_id or member_id != member_id.strip():
        raise ValueError("council member ID must be a nonempty normalized string")


def _snapshot_votes(votes: Sequence[CouncilVoteRecord]) -> tuple[CouncilVoteRecord, ...]:
    if not isinstance(votes, Sequence) or isinstance(votes, (str, bytes, bytearray)):
        raise ValueError("votes must be a sequence of CouncilVoteRecord values")
    return tuple(votes)


def _validate_electorate(eligible_members: frozenset[str] | None, total: int) -> None:
    if eligible_members is not None:
        if type(eligible_members) is not frozenset or len(eligible_members) != total:
            raise ValueError("eligible members must match the threshold electorate")
        for member_id in eligible_members:
            _require_member_id(member_id)


def _validate_vote_records(
    votes: tuple[CouncilVoteRecord, ...],
    eligible_members: frozenset[str] | None,
) -> None:
    seen_members: set[str] = set()
    for v in votes:
        if type(v) is not CouncilVoteRecord or type(v.vote) is not CouncilVoteChoice:
            raise ValueError("invalid council vote record or choice")
        _require_member_id(v.member_id)
        if any(type(value) is not str for value in (v.rationale, v.signature, v.timestamp_utc)):
            raise ValueError("council vote metadata must be strings")
        if v.member_id in seen_members:
            raise ValueError(f"duplicate council member: {v.member_id}")
        seen_members.add(v.member_id)
        if eligible_members is not None and v.member_id not in eligible_members:
            raise ValueError(f"ineligible council member: {v.member_id}")


def _meets_aye_threshold(aye: int, total: int, required: int | float | Fraction) -> bool:
    share = Fraction(aye, total) if isinstance(required, Fraction) else aye / total
    return share >= required


def assess_advisory_council_votes(
    council_id: str,
    resolution_id: str | None = None,
    motion: str | None = None,
    threshold: QuorumThreshold | None = None,
    votes: Sequence[CouncilVoteRecord] = (),
    eligible_members: frozenset[str] | None = None,
    signature_verifier: Callable[[CouncilVoteRecord, str, str, str], bool] | None = None,
) -> CouncilResolutionVerificationResult:
    """Assess a legacy threshold; even RATIFIED is advisory, not admission.

    Fraction thresholds use exact rational comparison. Float thresholds retain
    the historical float-ratio comparison, including equality at 0.8 or 5 / 7;
    they are not reinterpreted as decimal strings or configured decision policy.
    """
    t = _validated_threshold(threshold)
    votes = _snapshot_votes(votes)
    if len(votes) > t.total_eligible_members:
        raise ValueError("votes exceed total eligible members")
    _validate_electorate(eligible_members, t.total_eligible_members)
    _validate_vote_records(votes, eligible_members)
    if signature_verifier is not None and not callable(signature_verifier):
        raise ValueError("signature_verifier must be callable")
    for v in votes:
        if signature_verifier is not None:
            if signature_verifier(v, council_id, resolution_id or "", motion or "") is not True:
                raise ValueError(f"unverified council vote signature: {v.member_id}")

    total = len(votes)
    aye = sum(1 for v in votes if v.vote in (CouncilVoteChoice.AYE, CouncilVoteChoice.YES))
    nay = sum(1 for v in votes if v.vote in (CouncilVoteChoice.NAY, CouncilVoteChoice.NO))
    abstain = sum(1 for v in votes if v.vote == CouncilVoteChoice.ABSTAIN)

    if total < t.min_participating_members:
        status = CouncilResolutionStatus.QUORUM_NOT_MET
    elif _meets_aye_threshold(aye, total, t.required_aye_fraction):
        status = CouncilResolutionStatus.RATIFIED
    else:
        status = CouncilResolutionStatus.REJECTED

    return CouncilResolutionVerificationResult(
        council_id=council_id,
        resolution_id=resolution_id or "",
        motion=motion or "",
        status=status,
        aye_count=aye,
        nay_count=nay,
        abstain_count=abstain,
        total_votes=total,
    )


def tally_council_votes(
    *,
    resolution_id: str,
    council_id: str,
    proposal_id: str,
    candidate_id: str,
    votes: Sequence[CouncilVoteRecord],
    threshold: QuorumThreshold | None = None,
    timestamp_utc: str | None = None,
) -> CouncilResolutionV1:
    """Build a legacy advisory record from the same participation-based assessment."""
    votes = _snapshot_votes(votes)
    assessment = assess_advisory_council_votes(
        council_id,
        resolution_id,
        threshold=threshold,
        votes=votes,
    )
    ts = timestamp_utc or datetime.now(timezone.utc).isoformat()
    status = (
        CouncilResolutionStatus.APPROVED
        if assessment.status is CouncilResolutionStatus.RATIFIED
        else assessment.status
    )

    return CouncilResolutionV1(
        resolution_id=resolution_id,
        council_id=council_id,
        proposal_id=proposal_id,
        candidate_id=candidate_id,
        status=status,
        votes=tuple(votes),
        yes_count=assessment.aye_count,
        no_count=assessment.nay_count,
        abstain_count=assessment.abstain_count,
        total_votes=assessment.total_votes,
        resolution_timestamp_utc=ts,
    )
