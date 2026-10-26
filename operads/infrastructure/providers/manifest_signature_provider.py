"""Cryptographic manifest signing and signature verification provider."""

from __future__ import annotations

import hashlib
import hmac

from omega_engine_operations.domain.rop.result import Err, Ok, Result
from ...application.dtos.success_dtos import SignedManifestEnvelopeDTO
from ...domain.errors.domain_errors import DomainInvariantError, OeopDomainError


class ManifestSignatureProvider:
    """Signs and verifies cryptographic envelopes for exported skill catalogs and projection manifests."""

    @staticmethod
    def compute_payload_digest(payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _compute_signable_bytes(
        catalog_id: str,
        epoch: int,
        target_format: str,
        content_digest: str,
        signer_id: str,
        payload: str,
    ) -> bytes:
        canonical_str = f"{catalog_id}:{epoch}:{target_format}:{content_digest}:{signer_id}:{payload}"
        return canonical_str.encode("utf-8")

    def sign_manifest(
        self,
        manifest_id: str,
        catalog_id: str,
        epoch: int,
        target_format: str,
        payload: str,
        signer_id: str,
        secret_key: bytes,
    ) -> SignedManifestEnvelopeDTO:
        """Create a cryptographically signed manifest envelope."""
        content_digest = self.compute_payload_digest(payload)
        signable_bytes = self._compute_signable_bytes(
            catalog_id=catalog_id,
            epoch=epoch,
            target_format=target_format,
            content_digest=content_digest,
            signer_id=signer_id,
            payload=payload,
        )
        signature_hex = hmac.new(secret_key, signable_bytes, hashlib.sha256).hexdigest()

        return SignedManifestEnvelopeDTO(
            manifest_id=manifest_id,
            catalog_id=catalog_id,
            epoch=epoch,
            target_format=target_format,
            content_digest=content_digest,
            signer_id=signer_id,
            signature_algorithm="HMAC-SHA256",
            signature_hex=signature_hex,
            payload=payload,
        )

    def verify_envelope(
        self,
        envelope: SignedManifestEnvelopeDTO,
        secret_key: bytes,
    ) -> Result[bool, OeopDomainError]:
        """Verify that the envelope signature is valid and untampered."""
        # 1. Verify content digest matches payload
        computed_digest = self.compute_payload_digest(envelope.payload)
        if not hmac.compare_digest(computed_digest, envelope.content_digest):
            return Err(DomainInvariantError(
                code="PAYLOAD_DIGEST_MISMATCH",
                message=f"Declared digest {envelope.content_digest} does not match computed payload digest {computed_digest}",
            ))

        # 2. Compute expected HMAC signature
        signable_bytes = self._compute_signable_bytes(
            catalog_id=envelope.catalog_id,
            epoch=envelope.epoch,
            target_format=envelope.target_format,
            content_digest=envelope.content_digest,
            signer_id=envelope.signer_id,
            payload=envelope.payload,
        )
        expected_sig = hmac.new(secret_key, signable_bytes, hashlib.sha256).hexdigest()

        # 3. Constant-time comparison
        if not hmac.compare_digest(expected_sig, envelope.signature_hex):
            return Err(DomainInvariantError(
                code="SIGNATURE_VERIFICATION_FAILED",
                message=f"Cryptographic signature verification failed for manifest {envelope.manifest_id} signed by {envelope.signer_id}",
            ))

        return Ok(True)
