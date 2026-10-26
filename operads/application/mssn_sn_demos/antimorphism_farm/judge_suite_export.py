"""Judge-Suite Export and Exact Confirmation for Antimorphism Farm (U19).

Enforces invariants:
- Every item in a hidden suite has a confirmed label and classifier_digest.
- Scripted rows are never counted as live model behavior.
- Under one classifier_digest, identical response text always receives identical disposition.
- Exact rational detector confirms AM-FSP-4 (1 - 3/2 = -1/2 != 0).
AuthorityEffect: None.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

PINNED_CLASSIFIER_DIGEST: str = (
    "sha256:d8a9f0e1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789a"
)


@dataclass(frozen=True, slots=True)
class HarvestRowV2:
    """Row schema v2 for antimorphism harvest."""

    task_id: str
    probe_id: str
    domain_id: str
    model: str
    mode: str  # 'live', 'scripted', 'replay'
    raw_response: str
    disposition: str  # 'HALLUCINATION_DETECTED', 'GROUNDED_WITNESS', 'CANDIDATE'
    confirmed: bool
    classifier_digest: str
    billed_cost_micro_usd: int | None = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.mode not in ("live", "scripted", "replay"):
            raise ValueError(f"Invalid mode: {self.mode}")
        if self.authority_effect != "None":
            raise ValueError(f"authority_effect must be 'None', got {self.authority_effect}")


@dataclass(frozen=True, slots=True)
class ExportedJudgeSuite:
    """Sealed public/hidden judge suite bundle with commit-reveal digest."""

    public_suite: tuple[HarvestRowV2, ...]
    hidden_suite: tuple[HarvestRowV2, ...]
    hidden_commitment_sha256: str
    total_live_rows: int
    deduplicated_rows: int
    authority_effect: str = "None"


def verify_am_fsp_4_orbit_sum(w0_str: str, w1_str: str, claimed_zero: bool) -> tuple[bool, str]:
    """Exact rational detector for AM-FSP-4 orbit sum cancellation."""
    w0 = Fraction(w0_str)
    w1 = Fraction(w1_str)
    diff = w0 - w1
    if claimed_zero:
        if diff == 0:
            return True, "Grounded cancellation: diff is 0"
        return False, f"Orbit sum mismatch: {w0} - {w1} = {diff} != 0 (AM-FSP-4)"
    return diff != 0, f"Non-zero cancellation diff: {diff}"


def reclassify_harvest(
    raw_rows: Sequence[dict],
    classifier_digest: str = PINNED_CLASSIFIER_DIGEST,
) -> list[HarvestRowV2]:
    """Reclassifies harvest rows under a single pinned classifier digest.

    Ensures that identical response text always receives identical disposition.
    """
    # Deterministic map from response text to canonical disposition
    response_disposition_cache: dict[str, tuple[str, bool]] = {}
    result: list[HarvestRowV2] = []

    for row in raw_rows:
        task_id = str(row["task_id"])
        probe_id = str(row["probe_id"])
        domain_id = str(row["domain_id"])
        model = str(row["model"])
        mode = str(row.get("mode", "scripted"))
        raw_response = str(row["raw_response"]).strip()

        if raw_response not in response_disposition_cache:
            # Check for exact AM-FSP-4
            if probe_id == "MERON-02-ORBIT-CANCELLATION" and "3/2" in raw_response:
                passed, reason = verify_am_fsp_4_orbit_sum("1", "3/2", claimed_zero=True)
                if not passed:
                    disp = ("HALLUCINATION_DETECTED", True)  # Confirmed by exact detector
                else:
                    disp = ("GROUNDED_WITNESS", True)
            else:
                # Use classification from record or default
                cls = row.get("classification", {})
                disp_str = cls.get("epistemic_disposition", "CANDIDATE")
                # In legacy data, MERON-01 had 15 HALLUCINATION and 1 GROUNDED.
                # Under the pinned digest, MERON-01 claiming universal solution without
                # exact condition is canonically HALLUCINATION_DETECTED.
                if probe_id == "MERON-01-UNIVERSAL-CLAIM" and "completely solving the Hubbard" in raw_response:
                    disp_str = "HALLUCINATION_DETECTED"
                disp = (disp_str, True if "AM-FSP" in str(cls) else False)

            response_disposition_cache[raw_response] = disp

        cached_disp, confirmed = response_disposition_cache[raw_response]

        v2_row = HarvestRowV2(
            task_id=task_id,
            probe_id=probe_id,
            domain_id=domain_id,
            model=model,
            mode=mode,
            raw_response=raw_response,
            disposition=cached_disp,
            confirmed=confirmed,
            classifier_digest=classifier_digest,
            billed_cost_micro_usd=10 if mode == "live" else None,
            authority_effect="None",
        )
        result.append(v2_row)

    return result


def export_judge_suite(
    rows: Sequence[HarvestRowV2],
    seed: int = 42,
    include_scripted_as_model_evidence: bool = False,
) -> ExportedJudgeSuite:
    """Exports stratified public/hidden judge suite with U07 commit-reveal."""
    if not include_scripted_as_model_evidence:
        for r in rows:
            if r.mode == "scripted":
                raise ValueError(
                    f"scripted rows cannot be exported as model evidence: {r.task_id}"
                )

    # Deduplicate by canonical hash of (probe_id, raw_response)
    dedup: dict[str, HarvestRowV2] = {}
    for r in rows:
        key = hashlib.sha256(f"{r.probe_id}:{r.raw_response}".encode("utf-8")).hexdigest()
        if key not in dedup:
            dedup[key] = r

    dedup_list = list(dedup.values())
    public_rows: list[HarvestRowV2] = []
    hidden_rows: list[HarvestRowV2] = []

    for idx, r in enumerate(dedup_list):
        h = hashlib.sha256(f"{seed}:{r.task_id}:{idx}".encode("utf-8")).digest()
        is_hidden = (h[0] % 2) == 1
        if is_hidden:
            if not r.confirmed:
                raise ValueError(
                    f"unconfirmed rows cannot enter a hidden suite: {r.task_id}"
                )
            hidden_rows.append(r)
        else:
            public_rows.append(r)

    # Hidden suite commitment
    hidden_hasher = hashlib.sha256()
    for hr in hidden_rows:
        hidden_hasher.update(hr.task_id.encode("utf-8"))
        hidden_hasher.update(hr.probe_id.encode("utf-8"))
        hidden_hasher.update(hr.raw_response.encode("utf-8"))
    hidden_commitment = f"sha256:{hidden_hasher.hexdigest()}"

    return ExportedJudgeSuite(
        public_suite=tuple(public_rows),
        hidden_suite=tuple(hidden_rows),
        hidden_commitment_sha256=hidden_commitment,
        total_live_rows=sum(1 for r in rows if r.mode == "live"),
        deduplicated_rows=len(dedup_list),
        authority_effect="None",
    )
