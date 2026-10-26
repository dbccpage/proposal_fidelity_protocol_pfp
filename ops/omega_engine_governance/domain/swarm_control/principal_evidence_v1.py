"""Principal Evidence V1 Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .decision_validation_error import DecisionValidationError
from .value_objects import (
    DigestKind,
    DomainInvariantError,
    IdKind,
    PrincipalId,
    PublicKeyRef,
    SignatureDigest,
)


@dataclass(frozen=True, slots=True, eq=False)
class PrincipalEvidenceV1:
    """Syntax-checked evidence references for an injected external verifier."""

    principal_id: PrincipalId
    public_key_ref: PublicKeyRef
    signature_digest: SignatureDigest
    auth_scheme: str = "ed25519"

    def __init__(
        self,
        *,
        principal_id: PrincipalId | str,
        public_key_ref: PublicKeyRef | str,
        signature_digest: SignatureDigest | str,
        auth_scheme: str = "ed25519",
    ) -> None:
        try:
            p_id = PrincipalId.from_str(principal_id, kind=IdKind.PRINCIPAL)
            k_ref = PublicKeyRef.from_str(public_key_ref, kind=IdKind.PUBLIC_KEY_REF)
            s_dig = SignatureDigest.from_str(
                signature_digest, kind=DigestKind.SIGNATURE
            )
        except DomainInvariantError as exc:
            raise DecisionValidationError("INVALID_PRINCIPAL_FIELD", str(exc)) from exc

        if auth_scheme not in ("ed25519", "ecdsa_p256", "rsa4096"):
            raise DecisionValidationError("UNSUPPORTED_AUTH_SCHEME", auth_scheme)

        object.__setattr__(self, "principal_id", p_id)
        object.__setattr__(self, "public_key_ref", k_ref)
        object.__setattr__(self, "signature_digest", s_dig)
        object.__setattr__(self, "auth_scheme", auth_scheme)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return (
            self.principal_id == other.principal_id
            and self.public_key_ref == other.public_key_ref
            and self.signature_digest == other.signature_digest
            and self.auth_scheme == other.auth_scheme
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.principal_id,
                self.public_key_ref,
                self.signature_digest,
                self.auth_scheme,
            )
        )
