"""Immutable application receipt value object (Pass 5 / Stage C / P3-07A).

AuthorityEffect: None.
Receipt derives from the exact old/new Git states, decision, manifest, fence, and timestamp.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .receipt_validation_error import ReceiptValidationError
from .value_objects import (
    DecisionId,
    DigestKind,
    DomainInvariantError,
    FenceToken,
    GitCommitOid,
    GitTreeOid,
    IdKind,
    ManifestDigest,
    OneUseToken,
    ReceiptId,
    Sha256Digest,
    UtcTimestamp,
)

APPLICATION_RECEIPT_SCHEMA_V1 = "omega.application_receipt.v1"
RECEIPT_SCHEMA_V1 = APPLICATION_RECEIPT_SCHEMA_V1


@dataclass(frozen=True, slots=True, eq=False)
class ApplicationReceiptV1:
    """Immutable proof of a completed single-effect Git mutation."""

    receipt_id: ReceiptId
    decision_id: DecisionId
    one_use_token: OneUseToken
    old_head_commit_oid: GitCommitOid
    new_head_commit_oid: GitCommitOid
    old_tree_oid: GitTreeOid
    new_tree_oid: GitTreeOid
    manifest_sha256: ManifestDigest
    fence_token: FenceToken
    applied_timestamp_utc: UtcTimestamp
    receipt_sha256: Sha256Digest
    authority_effect: str = "None"
    schema_version: str = RECEIPT_SCHEMA_V1

    def __init__(
        self,
        *,
        receipt_id: ReceiptId | str,
        decision_id: DecisionId | str,
        one_use_token: OneUseToken | str,
        old_head_commit_oid: GitCommitOid | str,
        new_head_commit_oid: GitCommitOid | str,
        old_tree_oid: GitTreeOid | str,
        new_tree_oid: GitTreeOid | str,
        manifest_sha256: ManifestDigest | str,
        fence_token: FenceToken | int,
        applied_timestamp_utc: UtcTimestamp | str | datetime,
        receipt_sha256: Sha256Digest | str,
        authority_effect: str = "None",
        schema_version: str = RECEIPT_SCHEMA_V1,
    ) -> None:
        if schema_version != RECEIPT_SCHEMA_V1:
            raise ReceiptValidationError(
                "RECEIPT_SCHEMA_VERSION_MISMATCH",
                f"expected {RECEIPT_SCHEMA_V1} got {schema_version}",
            )
        try:
            r_id = ReceiptId.from_str(receipt_id, kind=IdKind.RECEIPT)
            d_id = DecisionId.from_str(decision_id, kind=IdKind.DECISION)
            tok = OneUseToken.from_str(one_use_token, kind=IdKind.ONE_USE_TOKEN)
            old_head = GitCommitOid.from_str(
                old_head_commit_oid, kind=DigestKind.GIT_COMMIT
            )
            new_head = GitCommitOid.from_str(
                new_head_commit_oid, kind=DigestKind.GIT_COMMIT
            )
            old_tr = GitTreeOid.from_str(old_tree_oid, kind=DigestKind.GIT_TREE)
            new_tr = GitTreeOid.from_str(new_tree_oid, kind=DigestKind.GIT_TREE)
            m_sha = ManifestDigest.from_str(manifest_sha256, kind=DigestKind.MANIFEST)
            f_tok = (
                FenceToken.from_int(fence_token)
                if isinstance(fence_token, int)
                else fence_token
            )
            app_ts = UtcTimestamp.from_iso(applied_timestamp_utc)
            r_sha = Sha256Digest.from_str(receipt_sha256, kind=DigestKind.SHA256)
        except DomainInvariantError as exc:
            raise ReceiptValidationError("INVALID_RECEIPT_FIELD", str(exc)) from exc

        computed = compute_receipt_sha256(
            decision_id=str(d_id),
            one_use_token=str(tok),
            old_head_commit_oid=str(old_head),
            new_head_commit_oid=str(new_head),
            old_tree_oid=str(old_tr),
            new_tree_oid=str(new_tr),
            manifest_sha256=str(m_sha),
            fence_token=int(f_tok),
            applied_timestamp_utc=str(app_ts),
            authority_effect=authority_effect,
        )
        if str(r_sha) != computed:
            raise ReceiptValidationError(
                "RECEIPT_SHA256_MISMATCH",
                f"expected {computed} got {r_sha}",
            )

        object.__setattr__(self, "receipt_id", r_id)
        object.__setattr__(self, "decision_id", d_id)
        object.__setattr__(self, "one_use_token", tok)
        object.__setattr__(self, "old_head_commit_oid", old_head)
        object.__setattr__(self, "new_head_commit_oid", new_head)
        object.__setattr__(self, "old_tree_oid", old_tr)
        object.__setattr__(self, "new_tree_oid", new_tr)
        object.__setattr__(self, "manifest_sha256", m_sha)
        object.__setattr__(self, "fence_token", f_tok)
        object.__setattr__(self, "applied_timestamp_utc", app_ts)
        object.__setattr__(self, "receipt_sha256", r_sha)
        object.__setattr__(self, "authority_effect", authority_effect)
        object.__setattr__(self, "schema_version", schema_version)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.receipt_id == other.receipt_id

    def __hash__(self) -> int:
        return hash((type(self), self.receipt_id))

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": str(self.receipt_id),
            "decision_id": str(self.decision_id),
            "one_use_token": str(self.one_use_token),
            "old_head_commit_oid": str(self.old_head_commit_oid),
            "new_head_commit_oid": str(self.new_head_commit_oid),
            "old_tree_oid": str(self.old_tree_oid),
            "new_tree_oid": str(self.new_tree_oid),
            "manifest_sha256": str(self.manifest_sha256),
            "fence_token": int(self.fence_token),
            "applied_timestamp_utc": str(self.applied_timestamp_utc),
            "receipt_sha256": str(self.receipt_sha256),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }


def compute_receipt_sha256(
    *,
    decision_id: str,
    one_use_token: str,
    old_head_commit_oid: str,
    new_head_commit_oid: str,
    old_tree_oid: str,
    new_tree_oid: str,
    manifest_sha256: str,
    fence_token: int,
    applied_timestamp_utc: str,
    authority_effect: str = "None",
) -> str:
    hasher = hashlib.sha256()
    for field_val in (
        RECEIPT_SCHEMA_V1,
        str(decision_id),
        str(one_use_token),
        str(old_head_commit_oid),
        str(new_head_commit_oid),
        str(old_tree_oid),
        str(new_tree_oid),
        str(manifest_sha256),
        str(fence_token),
        str(applied_timestamp_utc),
        str(authority_effect),
    ):
        hasher.update(field_val.encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()
