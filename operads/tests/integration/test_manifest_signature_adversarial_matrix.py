"""Examiner Class 2: Adversarial Attack Matrix for HMAC-SHA256 Manifest Signatures.

Theoretical Minimum:
1. INVARIANT: Every cryptographic manifest envelope must be non-malleable across all header facets
   (signer_id, epoch, catalog_id, target_format, payload) and reject forged/truncated/bit-flipped keys.
2. BREAK: Envelope ignores header field tamper, accepts prefix/truncated signatures, or leaks timing.
3. WITNESS: ManifestSignatureProvider.verify_envelope returns Err with SIGNATURE_VERIFICATION_FAILED
   or PAYLOAD_DIGEST_MISMATCH.
4. MUTATION: In manifest_signature_provider.py, replace 'hmac.compare_digest' with 'return Ok(True)'.
"""

from __future__ import annotations

import unittest

from operads.application.dtos.success_dtos import (
    SignedManifestEnvelopeDTO,
)
from operads.infrastructure.providers.manifest_signature_provider import (
    ManifestSignatureProvider,
)


class TestManifestSignatureAdversarialMatrix(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = ManifestSignatureProvider()
        self.secret_key = b"secret_master_key_12345"
        self.wrong_key = b"attacker_forged_key_99999"

        self.valid_envelope = self.provider.sign_manifest(
            manifest_id="manifest_alpha",
            catalog_id="catalog_canonical_v3",
            epoch=42,
            target_format="operad_v1",
            payload='{"skills": ["skill_1", "skill_2"]}',
            signer_id="signer:panepistimion:primary",
            secret_key=self.secret_key,
        )

    def test_wrong_key_rejection(self) -> None:
        """Class 2: Asserts that envelope verified with a different secret key fails."""
        res = self.provider.verify_envelope(self.valid_envelope, secret_key=self.wrong_key)
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, "SIGNATURE_VERIFICATION_FAILED")

    def test_epoch_tamper_rejection(self) -> None:
        """Class 2: Asserts that altering the epoch number invalidates the signature."""
        tampered_envelope = SignedManifestEnvelopeDTO(
            manifest_id=self.valid_envelope.manifest_id,
            catalog_id=self.valid_envelope.catalog_id,
            epoch=999,  # altered epoch
            target_format=self.valid_envelope.target_format,
            content_digest=self.valid_envelope.content_digest,
            signer_id=self.valid_envelope.signer_id,
            signature_algorithm=self.valid_envelope.signature_algorithm,
            signature_hex=self.valid_envelope.signature_hex,
            payload=self.valid_envelope.payload,
        )
        res = self.provider.verify_envelope(tampered_envelope, secret_key=self.secret_key)
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, "SIGNATURE_VERIFICATION_FAILED")

    def test_signer_id_tamper_rejection(self) -> None:
        """Class 2: Asserts that altering the signer ID invalidates the signature."""
        tampered_envelope = SignedManifestEnvelopeDTO(
            manifest_id=self.valid_envelope.manifest_id,
            catalog_id=self.valid_envelope.catalog_id,
            epoch=self.valid_envelope.epoch,
            target_format=self.valid_envelope.target_format,
            content_digest=self.valid_envelope.content_digest,
            signer_id="attacker:unauthorized",  # altered signer
            signature_algorithm=self.valid_envelope.signature_algorithm,
            signature_hex=self.valid_envelope.signature_hex,
            payload=self.valid_envelope.payload,
        )
        res = self.provider.verify_envelope(tampered_envelope, secret_key=self.secret_key)
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, "SIGNATURE_VERIFICATION_FAILED")

    def test_truncated_signature_rejection(self) -> None:
        """Class 2: Asserts that truncated or partial signature hex strings are rejected."""
        tampered_envelope = SignedManifestEnvelopeDTO(
            manifest_id=self.valid_envelope.manifest_id,
            catalog_id=self.valid_envelope.catalog_id,
            epoch=self.valid_envelope.epoch,
            target_format=self.valid_envelope.target_format,
            content_digest=self.valid_envelope.content_digest,
            signer_id=self.valid_envelope.signer_id,
            signature_algorithm=self.valid_envelope.signature_algorithm,
            signature_hex=self.valid_envelope.signature_hex[:32],  # truncated signature
            payload=self.valid_envelope.payload,
        )
        res = self.provider.verify_envelope(tampered_envelope, secret_key=self.secret_key)
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, "SIGNATURE_VERIFICATION_FAILED")


if __name__ == "__main__":
    unittest.main()
