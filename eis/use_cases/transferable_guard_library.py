"""P3 Transferable Guard Library Use Case (PROD-P3).

Zero infrastructure imports; depends strictly on epistemic_immune_system domain
contracts and pure protocols. Evaluates parent-digest-bound rejection guard mining
(REV-SMRM-P3-MINE), zero false positives on valid candidates, cross-level adapter
pullback, and multi-episode transfer savings (PROD-P3-NEXT-1, PROD-P3-NEXT-2).

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class GuardTransferRefusal(Exception):
    """Typed refusal raised when a guard bundle fails parent binding, soundness, or trace verification."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.clause = code
        self.message = message


@dataclass(frozen=True, slots=True)
class GuardTransferEvaluationRequest:
    task_id: int = 1
    level: int = 1
    episode_budget: int = 18
    override_parent_digest: str | None = None


class TransferableGuardLibraryPort(Protocol):
    """Port for mining rejections into typed guards and verifying cross-level transfer."""

    def evaluate_transfer(
        self, request: GuardTransferEvaluationRequest
    ) -> Mapping[str, Any]: ...


def evaluate_guard_transfer(
    request: GuardTransferEvaluationRequest,
    library: TransferableGuardLibraryPort,
) -> dict[str, Any]:
    """Run the P3 transferable guard library evaluation and enforce soundness + parent binding."""
    if request.episode_budget <= 0:
        raise GuardTransferRefusal("INVALID_BUDGET", "episode_budget must be strictly positive")
    verdict = dict(library.evaluate_transfer(request))
    if not verdict.get("bundle_matches_parent", False):
        raise GuardTransferRefusal(
            "PARENT_DIGEST_MISMATCH",
            "guard bundle parent_sha256 does not match the parent packet digest",
        )
    if not verdict.get("sound_on_valid", False):
        raise GuardTransferRefusal(
            "UNSOUND_GUARD",
            "mined guard rejected a valid candidate on the carrier",
        )
    if not verdict.get("trace_verified", False):
        raise GuardTransferRefusal(
            "TRACE_REJECTED",
            "multi-episode guard transfer trace failed independent trace_checker",
        )
    return verdict
