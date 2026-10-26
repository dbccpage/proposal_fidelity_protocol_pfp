from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


class PostmergeMismatchError(Exception):
    """Raised when post-merge content identity verification fails on mainline."""
    pass


@dataclass(frozen=True, slots=True)
class PostmergeContentWitness:
    witness_id: str
    candidate_id: str
    landed_main_head: str
    expected_path_blobs: dict[str, str]
    observed_path_blobs: dict[str, str]
    is_verified: bool
    witness_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, PostmergeContentWitness)
        return (
            self.witness_id == other.witness_id
            and self.candidate_id == other.candidate_id
            and self.landed_main_head == other.landed_main_head
            and self.expected_path_blobs == other.expected_path_blobs
            and self.observed_path_blobs == other.observed_path_blobs
            and self.is_verified == other.is_verified
            and self.witness_digest == other.witness_digest
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "witness_id": self.witness_id,
            "candidate_id": self.candidate_id,
            "landed_main_head": self.landed_main_head,
            "expected_path_blobs": dict(sorted(self.expected_path_blobs.items(), key=lambda kv: kv[0].encode("utf-8"))),
            "observed_path_blobs": dict(sorted(self.observed_path_blobs.items(), key=lambda kv: kv[0].encode("utf-8"))),
            "is_verified": self.is_verified,
            "witness_digest": self.witness_digest,
        }


def create_postmerge_content_witness(
    candidate_id: str,
    landed_main_head: str,
    expected_path_blobs: Mapping[str, str],
    observed_path_blobs: Mapping[str, str],
) -> PostmergeContentWitness:
    """Verifies that landed mainline exact-blob content matches the candidate's promised state."""
    sorted_expected = dict(sorted(expected_path_blobs.items(), key=lambda kv: kv[0].encode("utf-8")))
    sorted_observed = dict(sorted(observed_path_blobs.items(), key=lambda kv: kv[0].encode("utf-8")))

    mismatches: list[str] = []
    for path, expected_oid in sorted_expected.items():
        observed_oid = sorted_observed.get(path)
        if observed_oid != expected_oid:
            mismatches.append(f"'{path}' expected {expected_oid}, got {observed_oid}")

    # Both directions. The loop above only walked the expected paths, so a
    # landing that ADDED blobs the candidate never promised verified clean --
    # which is the shape a tampered landing takes. "Matches the promised state"
    # has to mean the promised state and nothing besides.
    for path in sorted_observed:
        if path not in sorted_expected:
            mismatches.append(f"'{path}' observed on mainline but never promised")

    if mismatches:
        raise PostmergeMismatchError(
            f"Post-merge content verification failed on mainline {landed_main_head} for candidate "
            f"'{candidate_id}': {', '.join(mismatches)}"
        )

    # The digest must cover the observation, not only the promise. Hashing
    # `sorted_expected` alone meant two witnesses over wildly different observed
    # trees produced byte-identical witness_digest and witness_id, so the
    # receipt could not bind the thing it claims to witness and no after-the-fact
    # audit could tell them apart.
    raw_payload = json.dumps(
        {
            "candidate_id": candidate_id,
            "landed_main_head": landed_main_head,
            "expected_blobs": sorted_expected,
            "observed_blobs": sorted_observed,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    witness_id = f"witness:{digest[:16]}"

    return PostmergeContentWitness(
        witness_id=witness_id,
        candidate_id=candidate_id,
        landed_main_head=landed_main_head,
        expected_path_blobs=sorted_expected,
        observed_path_blobs=sorted_observed,
        is_verified=True,
        witness_digest=digest,
    )
