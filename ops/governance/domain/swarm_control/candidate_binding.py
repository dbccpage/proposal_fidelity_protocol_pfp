"""Content-bound CandidateBinding (SWARM-L7 / STORY-031-001).

Binding id is re-derived in __post_init__; replace()/manual field forgery fails closed.
blob_manifest is always deep-copied into a private dict then wrapped in MappingProxyType
so a caller-supplied proxy cannot retain a live mutable backing map.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .binding_error import BindingError


def _digest(parts: Mapping[str, Any]) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _private_blob_proxy(
    blob_manifest: Mapping[str, str] | None,
) -> Mapping[str, str] | None:
    """Copy into a fresh private dict, then freeze. Never retain caller containers."""
    if blob_manifest is None:
        return None
    private = dict(blob_manifest)
    return MappingProxyType(private)


def _content_parts(
    *,
    repository: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
    merge_base_sha: str,
    tree_sha: str | None,
    blob_manifest: Mapping[str, str] | None,
    path_set_digest: str,
    policy_digest: str,
    evaluator_digest: str,
) -> dict[str, Any]:
    return {
        "repository": repository,
        "pr": pr_number,
        "base": base_sha,
        "head": head_sha,
        "merge_base": merge_base_sha,
        "tree": tree_sha,
        "blobs": dict(sorted((blob_manifest or {}).items())),
        "path_set_digest": path_set_digest,
        "policy": policy_digest,
        "evaluator": evaluator_digest,
    }


def compute_content_binding_id(
    *,
    repository: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
    merge_base_sha: str,
    tree_sha: str | None,
    blob_manifest: Mapping[str, str] | None,
    path_set_digest: str,
    policy_digest: str,
    evaluator_digest: str,
) -> str:
    return _digest(
        _content_parts(
            repository=repository,
            pr_number=pr_number,
            base_sha=base_sha,
            head_sha=head_sha,
            merge_base_sha=merge_base_sha,
            tree_sha=tree_sha,
            blob_manifest=blob_manifest,
            path_set_digest=path_set_digest,
            policy_digest=policy_digest,
            evaluator_digest=evaluator_digest,
        )
    )


def revalidate_binding(binding: CandidateBinding) -> None:
    """Custody boundary: re-derive id; raise if field set drifted from id."""
    expected = compute_content_binding_id(
        repository=binding.repository,
        pr_number=binding.pr_number,
        base_sha=binding.base_sha,
        head_sha=binding.head_sha,
        merge_base_sha=binding.merge_base_sha,
        tree_sha=binding.tree_sha,
        blob_manifest=binding.blob_manifest,
        path_set_digest=binding.path_set_digest,
        policy_digest=binding.policy_digest,
        evaluator_digest=binding.evaluator_digest,
    )
    if binding.content_binding_id != expected:
        raise BindingError("BINDING_ID_MISMATCH")


@dataclass(frozen=True)
class CandidateBinding:
    repository: str
    pr_number: int
    base_sha: str
    head_sha: str
    merge_base_sha: str
    tree_sha: str | None
    blob_manifest: Mapping[str, str] | None
    path_set_digest: str
    policy_digest: str
    evaluator_digest: str
    content_binding_id: str

    def __post_init__(self) -> None:
        if not self.head_sha or not self.base_sha:
            raise BindingError("MISSING_HEAD_OR_BASE")
        if not isinstance(self.pr_number, int):
            raise BindingError("INVALID_PR_NUMBER")
        if self.tree_sha is None and not self.blob_manifest:
            raise BindingError("CONTENT_IDENTITY_REQUIRED")

        frozen_blobs = _private_blob_proxy(self.blob_manifest)
        object.__setattr__(self, "blob_manifest", frozen_blobs)

        expected = compute_content_binding_id(
            repository=self.repository,
            pr_number=self.pr_number,
            base_sha=self.base_sha,
            head_sha=self.head_sha,
            merge_base_sha=self.merge_base_sha,
            tree_sha=self.tree_sha,
            blob_manifest=frozen_blobs,
            path_set_digest=self.path_set_digest,
            policy_digest=self.policy_digest,
            evaluator_digest=self.evaluator_digest,
        )
        if self.content_binding_id != expected:
            raise BindingError("BINDING_ID_MISMATCH")

    def review_valid_with_path_set_only(self) -> bool:
        """Path-set fingerprint alone is never enough for review continuity."""
        return False


def build_candidate_binding(
    *,
    repository: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
    merge_base_sha: str,
    tree_sha: str | None = None,
    blob_manifest: Mapping[str, str] | None = None,
    path_set: list[str] | None = None,
    policy_digest: str = "policy:unset",
    evaluator_digest: str = "eval:unset",
) -> CandidateBinding:
    if not head_sha or not base_sha:
        raise BindingError("MISSING_HEAD_OR_BASE")
    if not isinstance(pr_number, int):
        raise BindingError("INVALID_PR_NUMBER")
    if tree_sha is None and not blob_manifest:
        raise BindingError("CONTENT_IDENTITY_REQUIRED")

    paths = sorted(path_set or (list(blob_manifest.keys()) if blob_manifest else []))
    path_set_digest = _digest({"paths": paths})
    blobs = dict(blob_manifest) if blob_manifest is not None else None
    content_binding_id = compute_content_binding_id(
        repository=repository,
        pr_number=pr_number,
        base_sha=base_sha,
        head_sha=head_sha,
        merge_base_sha=merge_base_sha,
        tree_sha=tree_sha,
        blob_manifest=blobs,
        path_set_digest=path_set_digest,
        policy_digest=policy_digest,
        evaluator_digest=evaluator_digest,
    )
    return CandidateBinding(
        repository=repository,
        pr_number=pr_number,
        base_sha=base_sha,
        head_sha=head_sha,
        merge_base_sha=merge_base_sha,
        tree_sha=tree_sha,
        blob_manifest=blobs,
        path_set_digest=path_set_digest,
        policy_digest=policy_digest,
        evaluator_digest=evaluator_digest,
        content_binding_id=content_binding_id,
    )


def bindings_equal(a: CandidateBinding, b: CandidateBinding) -> bool:
    """Equality only after custody revalidation of both sides."""
    revalidate_binding(a)
    revalidate_binding(b)
    return a.content_binding_id == b.content_binding_id
