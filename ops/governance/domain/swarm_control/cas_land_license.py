from __future__ import annotations

from dataclasses import dataclass
import hashlib
import secrets
from typing import Any


class CasHeadDriftError(Exception):
    """Raised when observed mainline head differs from the license expected_head_sha."""
    pass


class CasLicenseExpiredError(Exception):
    """Raised when attempting to execute a land after the license TTL has elapsed."""
    pass


@dataclass(frozen=True, slots=True)
class CasLandLicense:
    license_id: str
    candidate_id: str
    expected_head_sha: str
    granted_at_epoch: float
    expires_at_epoch: float
    nonce: str

    def is_expired(self, current_epoch: float) -> bool:
        return current_epoch >= self.expires_at_epoch

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, CasLandLicense)
        return (
            self.license_id == other.license_id
            and self.candidate_id == other.candidate_id
            and self.expected_head_sha == other.expected_head_sha
            and self.granted_at_epoch == other.granted_at_epoch
            and self.expires_at_epoch == other.expires_at_epoch
            and self.nonce == other.nonce
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "license_id": self.license_id,
            "candidate_id": self.candidate_id,
            "expected_head_sha": self.expected_head_sha,
            "granted_at_epoch": self.granted_at_epoch,
            "expires_at_epoch": self.expires_at_epoch,
            "nonce": self.nonce,
        }


def issue_cas_land_license(
    candidate_id: str,
    expected_head_sha: str,
    current_epoch: float,
    ttl_seconds: float = 120.0,
    nonce: str | None = None,
) -> CasLandLicense:
    """Issue a compare-and-swap land license bound to an exact mainline head.

    The nonce defaulted to the empty string, which made `license_id` a pure
    deterministic hash of `(candidate_id, expected_head_sha, current_epoch)`.
    Two calls with the same arguments minted the identical id, so the ledger
    could not tell a re-issued license from a replayed one, nor a revoked one
    from a fresh one — and every call site in this package used the default,
    with `qualification_n1_engine` hard-coding the epoch as well.

    A fresh random nonce is now generated when none is supplied. Pass one
    explicitly only to reproduce a specific license in a test.
    """
    if nonce is None:
        nonce = secrets.token_hex(16)
    raw_payload = f"{candidate_id}:{expected_head_sha}:{current_epoch}:{nonce}"
    license_id = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    return CasLandLicense(
        license_id=license_id,
        candidate_id=candidate_id,
        expected_head_sha=expected_head_sha,
        granted_at_epoch=current_epoch,
        expires_at_epoch=current_epoch + ttl_seconds,
        nonce=nonce,
    )


def validate_cas_land_license(
    license: CasLandLicense,
    observed_head_sha: str,
    current_epoch: float,
) -> bool:
    """Validates that mainline has not drifted and the license is unexpired."""
    if license.is_expired(current_epoch):
        raise CasLicenseExpiredError(
            f"Land license '{license.license_id}' expired at epoch {license.expires_at_epoch} "
            f"(current epoch: {current_epoch})"
        )

    if license.expected_head_sha != observed_head_sha:
        raise CasHeadDriftError(
            f"Compare-and-swap failed for license '{license.license_id}': expected main HEAD "
            f"'{license.expected_head_sha}', but observed '{observed_head_sha}'"
        )

    return True
