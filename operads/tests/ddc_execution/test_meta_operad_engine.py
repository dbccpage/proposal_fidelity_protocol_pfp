#!/usr/bin/env python3
"""Comprehensive unit and integration tests for the Operad Bounded Context and MetaOperadEngine.

Validates:
- Value Objects: Exact-type equality and immutability (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Domain Errors: Typed hierarchy rooted in OperadDomainError
- Entities: OperadMorphism lifecycle and arity checking
- Use Case: MetaOperadEngineUseCase deterministic execution & trace recording
- All 24 metaskill scripts/execute.py entrypoints: Clean import and dry-run execution

AuthorityEffect: None.
"""

from __future__ import annotations

import subprocess
import sys
import unittest

from operads.domain.ddc_execution import (
    ADMITTED_FINITE_COLOURS,
    ArityMismatchError,
    ArtifactOutput,
    ColourSignature,
    MorphismExecutionStatus,
    OperadDomainError,
    OperadMorphism,
    OperadOperation,
    PermissionDeniedError,
    UnknownMorphismError,
)
from operads.domain.ddc_execution.execution import ExecutionPlan
from operads.domain.ddc_execution.signatures import (
    METASKILL_SIGNATURES,
)
from operads.frontend.cli.meta_operad_cli import main
from operads.infrastructure.ddc_execution.runtime import (
    build_meta_operad_engine,
    find_repo_root,
)


class OperadValueObjectTests(unittest.TestCase):
    """Test suite for domain value objects enforcing exact-type equality."""

    def test_colour_signature_exact_type_equality(self) -> None:
        sig1 = ColourSignature(("Code",), "Audit")
        sig2 = ColourSignature(("Code",), "Audit")
        self.assertEqual(sig1, sig2)
        self.assertEqual(hash(sig1), hash(sig2))
        self.assertEqual(sig1.arity, 1)

        # Cross-class comparison must return False (RULE_VO_EXACT_TYPE_EQUALITY_001)
        class SubColourSignature(ColourSignature):
            pass

        sub_sig = SubColourSignature(("Code",), "Audit")
        self.assertFalse(sig1 == sub_sig)
        self.assertFalse(sub_sig == sig1)
        self.assertFalse(sig1 == ("Code", "Audit"))

    def test_artifact_output_exact_type_equality(self) -> None:
        out1 = ArtifactOutput("runs/test.json", "sha256:abc")
        out2 = ArtifactOutput("runs/test.json", "sha256:abc")
        self.assertEqual(out1, out2)
        self.assertEqual(hash(out1), hash(out2))

        class SubArtifactOutput(ArtifactOutput):
            pass

        sub_out = SubArtifactOutput("runs/test.json", "sha256:abc")
        self.assertFalse(out1 == sub_out)
        self.assertFalse(out1 == "runs/test.json")

    def test_operad_operation_exact_type_equality(self) -> None:
        sig = ColourSignature(("State",), "State")
        op1 = OperadOperation("meta-atlas", "Atlas", sig, 1)
        op2 = OperadOperation("meta-atlas", "Atlas", sig, 1)
        self.assertEqual(op1, op2)
        self.assertEqual(hash(op1), hash(op2))

        class SubOperadOperation(OperadOperation):
            pass

        sub_op = SubOperadOperation("meta-atlas", "Atlas", sig, 1)
        self.assertFalse(op1 == sub_op)


class OperadDomainErrorTests(unittest.TestCase):
    """Test suite for typed error hierarchy."""

    def test_domain_error_inheritance(self) -> None:
        err = UnknownMorphismError("test-morphism")
        self.assertIsInstance(err, OperadDomainError)
        self.assertIsInstance(err, ValueError)
        self.assertEqual(err.code, "UNKNOWN_MORPHISM")
        self.assertIn("test-morphism", err.detail)

    def test_arity_and_permission_errors(self) -> None:
        arity_err = ArityMismatchError("test-op", 2, 1)
        self.assertEqual(arity_err.code, "ARITY_MISMATCH")

        perm_err = PermissionDeniedError("agent-x", "Not licensed")
        self.assertEqual(perm_err.code, "PERMISSION_DENIED")


class OperadMorphismEntityTests(unittest.TestCase):
    """Test suite for OperadMorphism entity."""

    def test_morphism_lifecycle(self) -> None:
        sig = ColourSignature(("State",), "Receipt")
        op = OperadOperation("test-morph", "TestMorph", sig, 1)
        morphism = OperadMorphism(op)

        # Enforces arity when explicit inputs provided
        with self.assertRaises(ArityMismatchError):
            morphism.validate_inputs(["input1", "input2"])

        # Completes run with contractivity determination
        record = morphism.complete_run(
            inputs=["in1"],
            output_path="runs/out.json",
            output_sha256="abc123hash",
            residual_before=5.0,
            residual_after=0.0,
            findings_count=0,
            timestamp="2026-10-05T00:00:00+00:00",
        )
        self.assertTrue(record.contractive)
        self.assertEqual(record.residual_delta, -5.0)
        self.assertEqual(morphism.status, MorphismExecutionStatus.CONTRACTIVE_PASS)


class MetaOperadEngineUseCaseTests(unittest.TestCase):
    """Test suite for MetaOperadEngineUseCase and CLI entrypoint."""

    def setUp(self) -> None:
        self.engine = build_meta_operad_engine()

    def test_resolve_known_metaskills(self) -> None:
        op = self.engine.resolve_operation("meta-atlas-state-to-state-verifier")
        self.assertEqual(op.skill_id, "meta-atlas-state-to-state-verifier")
        self.assertEqual(op.signature.source_colours, ("State",))
        self.assertEqual(op.signature.target_colour, "State")

    def test_execute_morphism_dry_run(self) -> None:
        result = self.engine.execute_morphism(
            skill_id="meta-dda-dag-emitter",
            inputs=[],
            dry_run=True,
        )
        self.assertTrue(result.is_ok)
        plan = result.unwrap()
        self.assertIsInstance(plan, ExecutionPlan)
        self.assertEqual(plan.operation.skill_id, "meta-dda-dag-emitter")
        self.assertEqual(plan.status, "DRY_RUN_PLAN")
        self.assertFalse(hasattr(plan, "residual_before"))

    def test_main_cli_dry_run(self) -> None:
        exit_code = main(["meta-state--state--contractive", "--dry-run"])
        self.assertEqual(exit_code, 0)

    def test_all_24_metaskill_signatures_registered(self) -> None:
        self.assertEqual(len(METASKILL_SIGNATURES), 24)
        for skill_id, (sources, target, desc) in METASKILL_SIGNATURES.items():
            op = self.engine.resolve_operation(skill_id)
            self.assertEqual(op.signature.source_colours, sources)
            self.assertEqual(op.signature.target_colour, target)
            for c in sources + (target,):
                self.assertIn(c, ADMITTED_FINITE_COLOURS)

    def test_all_24_metaskill_runners_execute_dry_run(self) -> None:
        """Verify every single meta-*/scripts/execute.py executes cleanly."""
        repo_root = find_repo_root()
        for skill_id in sorted(METASKILL_SIGNATURES.keys()):
            script = repo_root / ".agents" / "skills" / skill_id / "scripts" / "execute.py"
            self.assertTrue(script.is_file(), f"Missing execute.py for {skill_id}")
            proc = subprocess.run(
                [sys.executable, str(script), "--dry-run"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"Runner failed for {skill_id}:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}",
            )
            self.assertIn("[DRY_RUN_PLAN]", proc.stdout)
            self.assertNotIn("CONTRACTIVE_PASS", proc.stdout)
            self.assertNotIn("NEUTRAL_PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
