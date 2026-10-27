from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Any


class MergeMutexStatus(str, Enum):
    UNLOCKED = "UNLOCKED"
    LOCKED = "LOCKED"
    STALE_RECOVERED = "STALE_RECOVERED"


class MergeMutexHeldError(Exception):
    """Raised when an acquire attempt is made while another merge is already in flight."""
    pass


class MergeMutexInvalidTokenError(Exception):
    """Raised when releasing an invalid, expired, or non-matching mutex token."""
    pass


@dataclass(frozen=True, slots=True)
class MergeMutexToken:
    token_id: str
    holder_id: str
    acquired_at_epoch: float
    expires_at_epoch: float
    status: MergeMutexStatus

    def is_expired(self, current_epoch: float) -> bool:
        return current_epoch >= self.expires_at_epoch

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, MergeMutexToken)
        return (
            self.token_id == other.token_id
            and self.holder_id == other.holder_id
            and self.acquired_at_epoch == other.acquired_at_epoch
            and self.expires_at_epoch == other.expires_at_epoch
            and self.status == other.status
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "token_id": self.token_id,
            "holder_id": self.holder_id,
            "acquired_at_epoch": self.acquired_at_epoch,
            "expires_at_epoch": self.expires_at_epoch,
            "status": self.status.value,
        }


class MergeMutexState:
    """Deterministic, fail-closed state manager for repository merge mutex."""

    def __init__(self) -> None:
        self._current_token: MergeMutexToken | None = None

    @property
    def current_token(self) -> MergeMutexToken | None:
        return self._current_token

    def is_locked(self, current_epoch: float) -> bool:
        if self._current_token is None:
            return False
        return not self._current_token.is_expired(current_epoch)

    def acquire(
        self,
        holder_id: str,
        current_epoch: float,
        ttl_seconds: float = 300.0,
    ) -> MergeMutexToken:
        if self._current_token is not None:
            if not self._current_token.is_expired(current_epoch):
                raise MergeMutexHeldError(
                    f"Merge mutex currently held by '{self._current_token.holder_id}' "
                    f"until epoch {self._current_token.expires_at_epoch} (token {self._current_token.token_id})"
                )
            # An expired lease was silently taken over here, with no audit
            # record and no check that the previous holder's merge had actually
            # finished. A lease lapsing is not the same as a merge completing:
            # a holder whose merge overran kept running while a second holder
            # was granted the lock, so two merges proceeded on the rail this
            # module exists to serialise.
            #
            # Recovery is a deliberate act. `recover_stale_mutex` records
            # STALE_RECOVERED; acquire refuses and points at it.
            raise MergeMutexHeldError(
                f"Merge mutex lease from '{self._current_token.holder_id}' expired at epoch "
                f"{self._current_token.expires_at_epoch} and has not been recovered. Call "
                f"recover_stale_mutex to record the takeover before acquiring "
                f"(token {self._current_token.token_id})."
            )

        token_raw = f"{holder_id}:{current_epoch}:{current_epoch + ttl_seconds}"
        token_id = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()

        token = MergeMutexToken(
            token_id=token_id,
            holder_id=holder_id,
            acquired_at_epoch=current_epoch,
            expires_at_epoch=current_epoch + ttl_seconds,
            status=MergeMutexStatus.LOCKED,
        )
        self._current_token = token
        return token

    def release(self, token: MergeMutexToken, current_epoch: float) -> bool:
        if self._current_token is None:
            raise MergeMutexInvalidTokenError("No merge mutex is currently held")
        if self._current_token.token_id != token.token_id:
            raise MergeMutexInvalidTokenError(
                f"Supplied token '{token.token_id}' does not match active mutex token '{self._current_token.token_id}'"
            )
        # `current_epoch` was accepted and never read, which implied a lease
        # check the code did not perform: a holder whose lease had already
        # lapsed still released successfully, so the rail could not tell an
        # orderly finish from one that ran past its window.
        if self._current_token.is_expired(current_epoch):
            raise MergeMutexInvalidTokenError(
                f"Token '{token.token_id}' expired at epoch "
                f"{self._current_token.expires_at_epoch}; it cannot release at {current_epoch}. "
                f"An overrunning merge must be resolved through recover_stale_mutex."
            )

        self._current_token = None
        return True

    def recover_stale_mutex(self, current_epoch: float) -> MergeMutexToken | None:
        if self._current_token is not None and self._current_token.is_expired(current_epoch):
            stale_token = self._current_token
            self._current_token = None
            return MergeMutexToken(
                token_id=stale_token.token_id,
                holder_id=stale_token.holder_id,
                acquired_at_epoch=stale_token.acquired_at_epoch,
                expires_at_epoch=stale_token.expires_at_epoch,
                status=MergeMutexStatus.STALE_RECOVERED,
            )
        return None
