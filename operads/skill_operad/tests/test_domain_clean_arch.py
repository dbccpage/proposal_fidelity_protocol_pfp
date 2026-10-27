"""Unit tests for skill-operad colours, composition grading, and the three use cases.

AuthorityEffect: None.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from operads.skill_operad.application.use_cases.dispatch_operation_use_case import (
    DispatchOperationUseCase,
)
from operads.skill_operad.application.use_cases.record_trace_use_case import (
    RecordTraceUseCase,
)
from operads.skill_operad.application.use_cases.validate_operad_use_case import (
    ValidateOperadUseCase,
    validate_composition_grading,
)
from operads.skill_operad.domain.colours import (
    ADMITTED_FINITE_COLOURS,
    Colour,
)
from operads.skill_operad.domain.errors import (
    Err,
    InvalidColourError,
    Ok,
)
from operads.domain.operad.errors import ArityMismatchError, IllTypedCompositionError, Ok as RegistryOk, Err as RegistryErr
from operads.skill_operad.domain.evidence import DiagnosticObservation
from operads.domain.operad.operad import ColouredOperad
from operads.domain.operad.operation import (
    OperationId,
    OperationSignature,
)
from operads.skill_operad.infrastructure.adapters.file_lock_adapter import (
    exclusive_file_lock,
)
from operads.skill_operad.infrastructure.repositories.json_operad_repository import (
    JsonOperadRepository,
)


class ValueObjectTests(unittest.TestCase):
    def test_colour_validation(self) -> None:
        c1 = Colour("Code")
        self.assertEqual(c1.name, "Code")
        self.assertEqual(str(c1), "Code")

        with self.assertRaises(InvalidColourError):
            Colour("NonExistentColour")

        with self.assertRaises(InvalidColourError):
            Colour("")

    def test_operation_id_validation(self) -> None:
        op_id = OperationId("techne-code-python-tester")
        self.assertEqual(str(op_id), "techne-code-python-tester")
        self.assertFalse(op_id.is_unit)

        unit_id = OperationId.unit_for(Colour("Code"))
        self.assertEqual(str(unit_id), "id_Code")
        self.assertTrue(unit_id.is_unit)

        with self.assertRaises(ValueError):
            OperationId("")

    def test_operation_signature_immutability_and_types(self) -> None:
        sig = OperationSignature.create(
            op_id="test_op",
            source=["Code", "Audit"],
            target="Receipt",
            equivariant=False,
            residual_effect="unknown",
        )
        self.assertEqual(sig.arity, 2)
        self.assertEqual(sig.source_colours, ("Code", "Audit"))
        self.assertEqual(sig.target.name, "Receipt")

        with self.assertRaises(ArityMismatchError):
            OperationSignature.create(
                op_id="bad_arity",
                source=["Code"],
                target="Receipt",
                arity=3,
            )


class ColouredOperadAggregateTests(unittest.TestCase):
    def test_operad_creation_and_units(self) -> None:
        operad = ColouredOperad()
        for colour_name in ADMITTED_FINITE_COLOURS:
            operad.add_colour(Colour(colour_name))

        self.assertEqual(len(operad.colours), len(ADMITTED_FINITE_COLOURS))
        added_units = operad.ensure_units()
        self.assertEqual(len(added_units), len(ADMITTED_FINITE_COLOURS))

    def test_operad_composition_typecheck(self) -> None:
        operad = ColouredOperad()
        for c in ADMITTED_FINITE_COLOURS:
            operad.add_colour(Colour(c))

        op1 = OperationSignature.create("op1", ["Code"], "State")
        op2 = OperationSignature.create("op2", ["State"], "Receipt")
        operad.add_operation(op1)
        operad.add_operation(op2)

        # Valid composition: op2 o_0 op1
        comp_res = operad.compose(op2.op_id, 0, op1.op_id, OperationId("op2_o0_op1"))
        self.assertTrue(isinstance(comp_res, RegistryOk))

        # Invalid composition (type mismatch): op1 o_0 op2
        bad_res = operad.compose(op1.op_id, 0, op2.op_id, OperationId("bad_comp"))
        self.assertTrue(isinstance(bad_res, RegistryErr))
        self.assertTrue(isinstance(bad_res.error, IllTypedCompositionError))


class CompositionGradingTests(unittest.TestCase):
    def test_entry_outer_may_invoke_discipline(self) -> None:
        errors, terminal = validate_composition_grading(
            [
                {
                    "outer": "entry",
                    "slot": 0,
                    "inner": "discipline",
                    "composite_id": "entry-after-discipline",
                }
            ],
            {"entry"},
        )
        self.assertEqual(errors, [])
        self.assertIn("entry-after-discipline", terminal)

    def test_discipline_above_transitive_entry_is_refused_regardless_of_order(
        self,
    ) -> None:
        errors, terminal = validate_composition_grading(
            [
                {
                    "outer": "discipline-two",
                    "slot": 0,
                    "inner": "entry-after-discipline",
                    "composite_id": "illegal-result",
                },
                {
                    "outer": "entry",
                    "slot": 0,
                    "inner": "discipline-one",
                    "composite_id": "entry-after-discipline",
                },
            ],
            {"entry"},
        )
        self.assertIn("entry-after-discipline", terminal)
        self.assertEqual(len(errors), 1)
        self.assertIn("terminal entry operation 'entry-after-discipline'", errors[0])
        self.assertIn("outer='discipline-two'", errors[0])


class UseCaseIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.operad_dir = Path(__file__).resolve().parents[1]

    def test_validate_operad_use_case(self) -> None:
        repo = JsonOperadRepository(self.operad_dir)
        use_case = ValidateOperadUseCase(repo)
        result = use_case.execute()

        self.assertTrue(result.is_ok())
        report = result.unwrap()
        self.assertTrue(report.is_valid)
        self.assertEqual(report.colour_count, 10)
        self.assertGreater(report.operation_count, 20)
        self.assertEqual(report.slices_verified, 0)

    def test_dispatch_operation_use_case(self) -> None:
        repo = JsonOperadRepository(self.operad_dir)
        use_case = DispatchOperationUseCase(repo)

        # Valid registered operation
        res = use_case.resolve_operation("id_Code")
        self.assertTrue(res.is_ok())
        dto = res.unwrap()
        self.assertEqual(dto.op_id, "id_Code")
        self.assertEqual(dto.target_colour, "Code")

        # Unknown operation
        bad_res = use_case.resolve_operation("non_existent_op_12345")
        self.assertTrue(bad_res.is_err())

    def test_record_trace_use_case_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "evidence_trace.json"
            lock_path = Path(tmpdir) / "trace.lock"

            use_case = RecordTraceUseCase(trace_path, lock_path, lock_port=exclusive_file_lock)
            obs = DiagnosticObservation(
                skill_id="test-skill",
                run_id="run-001",
                phi_before=1.0,
                phi_after=0.5,
                delta_phi=0.5,
            )
            use_case.record(obs)

            self.assertTrue(trace_path.exists())
            self.assertFalse(lock_path.exists())


if __name__ == "__main__":
    unittest.main()
