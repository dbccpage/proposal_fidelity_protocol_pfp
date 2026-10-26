"""Deterministic proposal harvesting after independent host replay.

No filesystem, provider, registry, or workflow effect occurs here.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from typing import Any

from omega_engine_woland.domain.evidence import (
    CheckerVerdict,
    is_sha256_ref,
    parse_checker_receipt,
    parse_exact_rational,
    sha256_ref,
)
from omega_engine_woland.domain.intelligence_mining import (
    IntelligenceHarvestV1,
    IntelligenceReplayPort,
    MinedCandidateV1,
    MiningObservationV1,
    MiningResidualV1,
    ReplayedMiningEvidenceV1,
)
from omega_engine_woland.domain.native import NativeOperationPort


def _reject_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate receipt key: {key}")
        result[key] = value
    return result


def _receipt(raw: bytes) -> dict[str, Any]:
    if not raw:
        raise ValueError("host replay receipt is unavailable")
    result = json.loads(
        raw.decode("utf-8"), parse_constant=_reject_constant, object_pairs_hook=_unique_keys
    )
    if type(result) is not dict:
        raise ValueError("host replay receipt must be an object")
    return result


def _bind(payload: dict[str, Any], observation: MiningObservationV1) -> None:
    for name, expected in (
        ("observation_ref", observation.observation_ref),
        ("candidate_content_sha256", observation.subject_ref),
        ("carrier_context_sha256", observation.carrier_ref),
        ("source_event_sha256", observation.source_event_ref),
    ):
        if payload.get(name) != expected:
            raise ValueError(f"host receipt {name} does not bind this observation")


def _witness(payload: dict[str, Any], prefix: str) -> str:
    text = payload.get(prefix + "_hex")
    reference = payload.get(prefix + "_sha256")
    if type(text) is not str or not is_sha256_ref(reference):
        raise ValueError(f"missing exact {prefix} bytes and digest")
    try:
        raw = bytes.fromhex(text)
    except ValueError as exc:
        raise ValueError(f"malformed {prefix} bytes") from exc
    if not raw or sha256_ref(raw) != reference:
        raise ValueError(f"{prefix} bytes do not match their digest")
    return reference


def _check_replay(
    observation: MiningObservationV1, evidence: ReplayedMiningEvidenceV1
, *, native_support: NativeOperationPort) -> tuple[str, ...]:
    if type(evidence) is not ReplayedMiningEvidenceV1:
        raise TypeError("host replay must return exact ReplayedMiningEvidenceV1")
    if evidence.observation_ref != observation.observation_ref:
        raise ValueError("host replay substituted the complete observation")
    check = evidence.candidate_check
    if (
        check.candidate_id != observation.candidate_id
        or check.candidate_content_sha256 != observation.subject_ref
    ):
        raise ValueError("host checker substituted the candidate")
    if check.verdict is CheckerVerdict.NOT_MEASURED:
        raise ValueError("host checker did not reproduce a verdict")
    parsed = parse_checker_receipt(check.checker_receipt_bytes, native_support=native_support)
    payload = _receipt(check.checker_receipt_bytes)
    _bind(payload, observation)
    if (
        parsed.candidate_id != observation.candidate_id
        or parsed.candidate_content_sha256 != observation.subject_ref
        or parsed.checker_id != check.checker_id
        or parsed.verdict is not check.verdict
    ):
        raise ValueError("host checker receipt contradicts its typed result")
    refs = {observation.source_event_ref, check.checker_receipt_sha256}
    if observation.trigger == "EXACT_REPAIR":
        if check.verdict is not CheckerVerdict.ACCEPTED:
            raise ValueError("exact-repair source was rejected by the host")
        measurement = evidence.measurement
        if measurement is None or not measurement.is_exact_joint_zero():
            raise ValueError("skill requires independently verified Phi1 = Gamma2 = 0")
        measured = _receipt(evidence.measurement_receipt_bytes)
        _bind(measured, observation)
        if (
            measured.get("status") != "MEASURED"
            or measured.get("certificate_verified") is not True
            or measured.get("backend") != measurement.backend
            or parse_exact_rational(measured.get("phi1")) != measurement.phi1
            or parse_exact_rational(measured.get("gamma2")) != measurement.gamma2
        ):
            raise ValueError("host measurement receipt contradicts the exact measurement")
        refs.add(_witness(measured, "certificate"))
        joint = _receipt(evidence.joint_kernel_receipt_bytes)
        _bind(joint, observation)
        if joint.get("status") != "CERTIFIED":
            raise ValueError("skill requires certified joint-kernel replay")
        refs.add(_witness(joint, "witness"))
        refs.add(sha256_ref(evidence.measurement_receipt_bytes))
        refs.add(sha256_ref(evidence.joint_kernel_receipt_bytes))
    else:
        if check.verdict is not CheckerVerdict.REJECTED:
            raise ValueError("defect was not reproduced by the exact host checker")
        if (
            payload.get("failure_class") != observation.failure_class
            or payload.get("target_pattern") != observation.target_pattern
            or payload.get("trigger") != observation.trigger
        ):
            raise ValueError("host refutation does not bind the declared typed defect")
    return tuple(sorted(refs))


def _candidate(
    kind: str, rows: list[tuple[MiningObservationV1, tuple[str, ...]]]
) -> MinedCandidateV1:
    observations = [observation for observation, _ in rows]
    return MinedCandidateV1(
        kind=kind,
        failure_class=observations[0].failure_class,
        target_pattern=observations[0].target_pattern,
        subject_refs=tuple(sorted({item.subject_ref for item in observations})),
        carrier_refs=tuple(sorted({item.carrier_ref for item in observations})),
        source_event_refs=tuple(sorted({item.source_event_ref for item in observations})),
        evidence_refs=tuple(sorted({ref for _, refs in rows for ref in refs})),
    )


def mine_intelligence(
    observations: tuple[MiningObservationV1, ...],
    *,
    replay_port: IntelligenceReplayPort | None,
    recurrence_threshold: int,
    native_support: NativeOperationPort,
) -> IntelligenceHarvestV1:
    """Replay a frozen finite batch, emit only inert candidates and residuals.

    Threshold selects review eligibility, never admission. Replays of one
    source event count once; distinctness is not an independence theorem.
    """
    if type(recurrence_threshold) is not int or recurrence_threshold < 2:
        raise ValueError("recurrence_threshold must be an exact int >= 2")
    if type(observations) is not tuple or any(
        type(item) is not MiningObservationV1 for item in observations
    ):
        raise TypeError("observations must be a frozen exact MiningObservationV1 tuple")
    distinct = {item.observation_ref: item for item in observations}
    residuals: list[MiningResidualV1] = []
    groups: dict[tuple[str, ...], list[tuple[MiningObservationV1, tuple[str, ...]]]] = {}
    for reference, observation in sorted(distinct.items()):
        if replay_port is None:
            residuals.append(
                MiningResidualV1(
                    reference,
                    "MINING_REPLAY_UNAVAILABLE",
                    "No independent host replay port is bound.",
                )
            )
            continue
        try:
            result = replay_port.replay(observation)
            if result.is_err:
                refusal = result.unwrap_err()
                residuals.append(MiningResidualV1(reference, refusal.code, refusal.message))
                continue
            refs = _check_replay(observation, result.unwrap(), native_support=native_support)
        except (TypeError, ValueError, UnicodeDecodeError) as exc:
            residuals.append(MiningResidualV1(reference, "MINING_EVIDENCE_REFUSED", str(exc)))
            continue
        if observation.trigger == "EXACT_REPAIR":
            key = ("SKILL", observation.subject_ref, observation.carrier_ref)
        elif observation.trigger in {"KOROVIEV_REFUTATION", "FALSE_GREEN"}:
            key = ("ANTIBODY", observation.failure_class, observation.target_pattern)
        else:
            key = ("INVARIANT_RULE", observation.failure_class, observation.target_pattern)
        groups.setdefault(key, []).append((observation, refs))
    candidates = []
    for key, rows in sorted(groups.items()):
        if key[0] == "INVARIANT_RULE":
            count = len({row.source_event_ref for row, _ in rows})
            if count < recurrence_threshold:
                for row, _ in rows:
                    residuals.append(
                        MiningResidualV1(
                            row.observation_ref,
                            "MINING_RECURRENCE_PENDING",
                            f"{count} distinct source events; {recurrence_threshold} required.",
                        )
                    )
                continue
        candidates.append(_candidate(key[0], rows))
    return IntelligenceHarvestV1(
        candidates=tuple(sorted(candidates, key=lambda item: item.candidate_ref)),
        residuals=tuple(sorted(residuals, key=lambda item: (item.observation_ref, item.code))),
        distinct_observations=len(distinct),
    )
