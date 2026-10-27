"""Review worktree exact-head pin (STORY-033-004).

AuthorityEffect: None.
"""

from __future__ import annotations

from .pin_check import PinCheck
from .review_pin import ReviewPin


def pin_review_head(pr_number: int, head_sha: str) -> ReviewPin:
    if not head_sha:
        raise ValueError("MISSING_HEAD")
    return ReviewPin(pr_number=pr_number, pin_sha=head_sha)


def check_pin(pin: ReviewPin, live_head_sha: str) -> PinCheck:
    if live_head_sha != pin.pin_sha:
        return PinCheck(False, "STALE_AFTER_HEAD_CHANGE", pin.pin_sha)
    return PinCheck(True, None, pin.pin_sha)
