"""Post-await TOCTOU revalidation (SWARM-L11 / STORY-031-002).

AuthorityEffect: None.
"""

from __future__ import annotations

from .await_boundary import AwaitBoundary
from .candidate_binding import (
    CandidateBinding,
    bindings_equal,
    build_candidate_binding,
)
from .revalidate_result import RevalidateResult


def record_await(binding: CandidateBinding) -> AwaitBoundary:
    return AwaitBoundary(pre_await=binding)


def resume_and_revalidate(
    boundary: AwaitBoundary,
    *,
    live_head_sha: str,
    live_base_sha: str,
    live_merge_base_sha: str,
    live_tree_sha: str | None = None,
    live_blob_manifest: dict[str, str] | None = None,
    other_residuals_clear: bool = True,
) -> RevalidateResult:
    pre = boundary.pre_await
    live = build_candidate_binding(
        repository=pre.repository,
        pr_number=pre.pr_number,
        base_sha=live_base_sha,
        head_sha=live_head_sha,
        merge_base_sha=live_merge_base_sha,
        tree_sha=live_tree_sha if live_tree_sha is not None else pre.tree_sha,
        blob_manifest=live_blob_manifest
        if live_blob_manifest is not None
        else pre.blob_manifest,
        path_set=list((live_blob_manifest or pre.blob_manifest or {}).keys())
        if (live_blob_manifest or pre.blob_manifest)
        else None,
        policy_digest=pre.policy_digest,
        evaluator_digest=pre.evaluator_digest,
    )
    if not bindings_equal(pre, live):
        residual = (
            "STALE_AFTER_HEAD_CHANGE"
            if pre.head_sha != live.head_sha
            else "STALE_BINDING"
        )
        return RevalidateResult(ok=False, residual=residual, live=live)
    if not other_residuals_clear:
        return RevalidateResult(ok=False, residual="OTHER_RESIDUALS_OPEN", live=live)
    return RevalidateResult(ok=True, residual=None, live=live)
