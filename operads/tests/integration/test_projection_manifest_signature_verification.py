"""Integration test for Projection Manifest cryptographic signing and signature verification."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from operads.application.commands.compile_projection import (
    CompileProjectionCommand,
)
from operads.domain.entities.catalog_v3 import EstateCatalogV3
from operads.domain.entities.operation_v3 import (
    OperationV3,
    PortSpecV3,
)
from operads.domain.value_objects.authority import AuthorityEffect
from operads.domain.value_objects.content_digest import ContentDigest
from operads.domain.value_objects.identifier import (
    CausationId,
    ColourId,
    CorrelationId,
    EstateRef,
    OperandId,
    OperationId,
    SchemaRef,
)
from operads.domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)
from operads.infrastructure.bootstrap import OeopContainer
from operads.infrastructure.providers.manifest_signature_provider import (
    ManifestSignatureProvider,
)


class TestProjectionManifestSignatureVerification(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "manifest_sig_test.db")
        self.container = OeopContainer(
            workspace_root=self.workspace_root,
            db_path=self.db_path,
        )
        self.uow = self.container.uow
        self.sig_provider = ManifestSignatureProvider()
        self.author_key = b"author_secret_signing_key_primary_99"
        self.attacker_key = b"malicious_impostor_secret_key_00"

    def tearDown(self) -> None:
        self.container.uow.close()
        self._temp_dir.cleanup()

    def _seed_catalog(self) -> EstateCatalogV3:
        now = datetime.now(timezone.utc)
        empty_digest = ContentDigest.empty_sha256()
        in_port = PortSpecV3(
            name="manifest",
            colour_id=ColourId("Manifest"),
            schema_ref=SchemaRef("schemas/manifest.json"),
            schema_digest=empty_digest,
            validator_ref="default",
            validator_digest=empty_digest,
        )
        out_port = PortSpecV3(
            name="envelope",
            colour_id=ColourId("SignedEnvelope"),
            schema_ref=SchemaRef("schemas/envelope.json"),
            schema_digest=empty_digest,
            validator_ref="default",
            validator_digest=empty_digest,
        )
        lifecycle = SkillLifecycleV3(
            declaration=DeclarationFacet.DECLARED,
            schema_binding=SchemaBindingFacet.BOUND,
            executor_binding=ExecutorBindingFacet.BOUND,
            validation=ValidationFacet.VALIDATED,
            admission=AdmissionFacet.ADMITTED,
        )
        op = OperationV3(
            operation_id=OperationId("agent-signer:sign"),
            inputs=(in_port,),
            output=out_port,
            operand_refs=(OperandId("opnd_sign_01"),),
            lifecycle=lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )
        catalog = EstateCatalogV3(
            catalog_id="cat_manifest_01",
            estate_ref=EstateRef("canonical"),
            epoch=1,
            compiled_at=now,
            skills={},
            operations={op.operation_id: op},
            capability_slices={},
            aliases={},
            catalog_digest=ContentDigest.sha256("fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"),
        )
        self.uow.save_catalog(catalog, ())
        return catalog

    def test_e2e_projection_compilation_and_valid_signature_verification(self) -> None:
        """Verifies end-to-end projection generation, cryptographic signing, and verification."""
        self._seed_catalog()

        # 1. Compile Projection
        cmd = CompileProjectionCommand(
            catalog_id="cat_manifest_01",
            target_format="yaml",
            correlation_id=CorrelationId("corr-proj-01"),
            causation_id=CausationId("cause-proj-01"),
        )
        proj_res = self.container.compile_projection_handler.handle(cmd)
        self.assertTrue(proj_res.is_ok)
        proj = proj_res.unwrap()

        # 2. Sign Manifest
        envelope = self.sig_provider.sign_manifest(
            manifest_id="man_01",
            catalog_id=proj.catalog_id,
            epoch=1,
            target_format=proj.target_format,
            payload=proj.payload,
            signer_id="author:sentinel:primary",
            secret_key=self.author_key,
        )

        self.assertEqual(envelope.manifest_id, "man_01")
        self.assertEqual(envelope.signature_algorithm, "HMAC-SHA256")
        self.assertEqual(len(envelope.signature_hex), 64)

        # 3. Verify Signature
        verify_res = self.sig_provider.verify_envelope(envelope, secret_key=self.author_key)
        self.assertTrue(verify_res.is_ok)
        self.assertTrue(verify_res.unwrap())

    def test_payload_tampering_is_rejected(self) -> None:
        """Modifying 1 character of the manifest payload must cause verification failure."""
        self._seed_catalog()
        raw_payload = json.dumps({"catalog_id": "cat_manifest_01", "skills": ["skill_a"]})

        envelope = self.sig_provider.sign_manifest(
            manifest_id="man_tamper_01",
            catalog_id="cat_manifest_01",
            epoch=1,
            target_format="json",
            payload=raw_payload,
            signer_id="author:sentinel:primary",
            secret_key=self.author_key,
        )

        # Tamper with payload (injecting unauthorized skill)
        tampered_envelope = type(envelope)(
            manifest_id=envelope.manifest_id,
            catalog_id=envelope.catalog_id,
            epoch=envelope.epoch,
            target_format=envelope.target_format,
            content_digest=envelope.content_digest,  # unchanged digest
            signer_id=envelope.signer_id,
            signature_algorithm=envelope.signature_algorithm,
            signature_hex=envelope.signature_hex,
            payload=json.dumps({"catalog_id": "cat_manifest_01", "skills": ["skill_a", "injected_malicious_skill"]}),
        )

        verify_res = self.sig_provider.verify_envelope(tampered_envelope, secret_key=self.author_key)
        self.assertTrue(verify_res.is_err)
        self.assertEqual(verify_res.unwrap_err().code, "PAYLOAD_DIGEST_MISMATCH")

    def test_signature_corruption_is_rejected(self) -> None:
        """Modifying signature hex digits must fail verification."""
        self._seed_catalog()
        raw_payload = json.dumps({"catalog_id": "cat_manifest_01"})

        envelope = self.sig_provider.sign_manifest(
            manifest_id="man_corrupt_sig_01",
            catalog_id="cat_manifest_01",
            epoch=1,
            target_format="json",
            payload=raw_payload,
            signer_id="author:sentinel:primary",
            secret_key=self.author_key,
        )

        corrupt_sig = "0" * 64 if envelope.signature_hex != "0" * 64 else "1" * 64
        corrupted_envelope = type(envelope)(
            manifest_id=envelope.manifest_id,
            catalog_id=envelope.catalog_id,
            epoch=envelope.epoch,
            target_format=envelope.target_format,
            content_digest=envelope.content_digest,
            signer_id=envelope.signer_id,
            signature_algorithm=envelope.signature_algorithm,
            signature_hex=corrupt_sig,
            payload=envelope.payload,
        )

        verify_res = self.sig_provider.verify_envelope(corrupted_envelope, secret_key=self.author_key)
        self.assertTrue(verify_res.is_err)
        self.assertEqual(verify_res.unwrap_err().code, "SIGNATURE_VERIFICATION_FAILED")

    def test_wrong_key_verification_fails(self) -> None:
        """Verifying signature with an incorrect key fails."""
        self._seed_catalog()
        envelope = self.sig_provider.sign_manifest(
            manifest_id="man_wrong_key_01",
            catalog_id="cat_manifest_01",
            epoch=1,
            target_format="json",
            payload='{"status": "ok"}',
            signer_id="author:sentinel:primary",
            secret_key=self.author_key,
        )

        verify_res = self.sig_provider.verify_envelope(envelope, secret_key=self.attacker_key)
        self.assertTrue(verify_res.is_err)
        self.assertEqual(verify_res.unwrap_err().code, "SIGNATURE_VERIFICATION_FAILED")


if __name__ == "__main__":
    unittest.main()
