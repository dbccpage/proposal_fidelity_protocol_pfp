"""Integration tests for HigherOperadAdapter anti-corruption layer."""

import unittest
from dataclasses import asdict, replace

import pytest

from operads.domain.entities import (
    OperationV3,
    PortSpecV3,
)
from operads.domain.value_objects import (
    AdmissionFacet,
    AuthorityEffect,
    ColourId,
    ContentDigest,
    DeclarationFacet,
    ExecutorBindingFacet,
    OperationId,
    SchemaBindingFacet,
    SchemaRef,
    SkillLifecycleV3,
    ValidationFacet,
)
from operads.infrastructure.operad.higher_operad_adapter import (
    HigherOperadAdapter,
)


class HigherOperadAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = HigherOperadAdapter()
        self.digest = ContentDigest.sha256("0" * 64)
        self.lifecycle = SkillLifecycleV3(
            declaration=DeclarationFacet.DECLARED,
            schema_binding=SchemaBindingFacet.BOUND,
            executor_binding=ExecutorBindingFacet.BOUND,
            validation=ValidationFacet.VALIDATED,
            admission=AdmissionFacet.ADMITTED,
            schema_digest=self.digest,
            executor_digest=self.digest,
        )

    def test_verify_composition_and_refuse_term_without_license_witness(self) -> None:
        op = OperationV3(
            operation_id=OperationId("my_skill:audit"),
            inputs=(
                PortSpecV3("in", ColourId("Code"), SchemaRef("schema:code:v1"), self.digest, "", self.digest),
            ),
            output=PortSpecV3("out", ColourId("Audit"), SchemaRef("schema:audit:v1"), self.digest, "", self.digest),
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )
        res = self.adapter.verify_composition(
            root_op=op,
            child_ops=(),
            slot_bindings=(),
        )
        self.assertTrue(res.is_ok)
        self.assertTrue(res.unwrap())

        auth_res = self.adapter.authorize_term(
            agent_id="agent_adversary",
            term_expr="my_skill:audit(Code)",
        )
        self.assertTrue(auth_res.is_err)
        self.assertEqual(auth_res.unwrap_err().code, "LICENSE_WITNESS_REQUIRED")

    def test_reject_composition_on_schema_digest_mismatch(self) -> None:
        """Assert that operations with identical colour but divergent schema digests are rejected."""
        digest_v1 = ContentDigest.sha256("1" * 64)
        digest_v2 = ContentDigest.sha256("2" * 64)

        root_op = OperationV3(
            operation_id=OperationId("root:op"),
            inputs=(
                PortSpecV3("in", ColourId("Code"), SchemaRef("schema:code:v1"), digest_v1, "", self.digest),
            ),
            output=PortSpecV3("out", ColourId("Receipt"), SchemaRef("schema:receipt:v1"), self.digest, "", self.digest),
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )

        child_op = OperationV3(
            operation_id=OperationId("child:op"),
            inputs=(),
            output=PortSpecV3("out", ColourId("Code"), SchemaRef("schema:code:v2"), digest_v2, "", self.digest),
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )

        # Attempt to bind child_op into slot 0 of root_op
        res = self.adapter.verify_composition(
            root_op=root_op,
            child_ops=(child_op,),
            slot_bindings=((0, child_op),),
        )

        self.assertTrue(res.is_err, "Composition must fail on schema digest divergence")
        err = res.unwrap_err()
        self.assertEqual(err.code, "SCHEMA_DIGEST_MISMATCH")
        self.assertIn("Child output schema digest", err.message)


    # --- slot index bounds --------------------------------------------------
    #
    # The bound was one-sided: `if slot_idx >= len(root_op.inputs)`. A NEGATIVE
    # index passed it, and `root_op.inputs[slot_idx]` then counted from the end.
    # Slot -1 bound silently to the LAST input, so a composition was verified
    # against a slot the caller never named and reported Ok.

    def _two_slot_root(self) -> OperationV3:
        """A root whose two inputs differ in colour.

        They must differ, or binding to the wrong slot would still pass the
        colour check and the defect would be invisible.
        """
        return OperationV3(
            operation_id=OperationId("root:two_slot"),
            inputs=(
                PortSpecV3("first", ColourId("Code"), SchemaRef("s:code"), self.digest, "", self.digest),
                PortSpecV3("second", ColourId("Prompt"), SchemaRef("s:prompt"), self.digest, "", self.digest),
            ),
            output=PortSpecV3("out", ColourId("Receipt"), SchemaRef("s:r"), self.digest, "", self.digest),
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
        )

    def _child_with_output(self, colour: str) -> OperationV3:
        return OperationV3(
            operation_id=OperationId(f"child:{colour.lower()}"),
            inputs=(),
            output=PortSpecV3("out", ColourId(colour), SchemaRef(f"s:{colour.lower()}"), self.digest, "", self.digest),
            operand_refs=(),
            lifecycle=self.lifecycle,
            residual_status="verified",
        )

    def test_a_negative_slot_index_is_refused(self) -> None:
        """The headline.

        Mutation: restore the one-sided bound and slot -1 binds to the last
        input, whose colour this child happens to match, so the call returns Ok.
        """
        root = self._two_slot_root()
        child = self._child_with_output("Prompt")   # matches inputs[-1], not inputs[0]

        res = self.adapter.verify_composition(
            root_op=root, child_ops=(child,), slot_bindings=((-1, child),)
        )

        self.assertTrue(res.is_err, "slot -1 was accepted and bound to the last input")
        self.assertEqual(res.unwrap_err().code, "SLOT_INDEX_OUT_OF_BOUNDS")

    def test_an_out_of_range_slot_index_is_still_refused(self) -> None:
        root = self._two_slot_root()
        child = self._child_with_output("Code")

        res = self.adapter.verify_composition(
            root_op=root, child_ops=(child,), slot_bindings=((2, child),)
        )

        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, "SLOT_INDEX_OUT_OF_BOUNDS")

    def test_a_boolean_slot_index_is_refused(self) -> None:
        """`bool` is an `int` subclass, so True would index inputs[1].

        A flag is not a slot. Mutation: drop the bool guard and True silently
        binds to the second input.
        """
        root = self._two_slot_root()
        child = self._child_with_output("Prompt")

        res = self.adapter.verify_composition(
            root_op=root, child_ops=(child,), slot_bindings=((True, child),)
        )

        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, "SLOT_INDEX_NOT_AN_INTEGER")

    def test_duplicate_slot_bindings_are_refused(self) -> None:
        """A root input can receive one child, not two competing children."""
        root = self._two_slot_root()
        child = self._child_with_output("Code")

        res = self.adapter.verify_composition(
            root_op=root,
            child_ops=(child,),
            slot_bindings=((0, child), (0, child)),
        )

        self.assertTrue(res.is_err, "two children were accepted for one root slot")
        self.assertEqual(res.unwrap_err().code, "DUPLICATE_SLOT_BINDING")

    def test_a_valid_slot_index_still_verifies(self) -> None:
        """Negative control.

        Without it, an adapter that refused every binding would pass all three
        tests above and look correct while blocking every composition.
        """
        root = self._two_slot_root()
        child = self._child_with_output("Code")

        res = self.adapter.verify_composition(
            root_op=root, child_ops=(child,), slot_bindings=((0, child),)
        )

        self.assertTrue(res.is_ok, res)
        self.assertTrue(res.unwrap())

    def test_the_second_slot_also_verifies(self) -> None:
        """Confirms the two slots really are distinguishable, so the negative
        test above is testing the bound and not a colour accident."""
        root = self._two_slot_root()
        child = self._child_with_output("Prompt")

        res = self.adapter.verify_composition(
            root_op=root, child_ops=(child,), slot_bindings=((1, child),)
        )

        self.assertTrue(res.is_ok, res)

    def test_actual_native_operation_keeps_optional_retirement_metadata(self) -> None:
        from operating_system.adapters.rust_host.ffi import RustSymbolGameHost

        operation = self._two_slot_root()
        legacy = asdict(operation)
        assert legacy.pop("replacement_operation_id") is None
        current = asdict(operation)

        def native(payload):
            response = RustSymbolGameHost().invoke_runtime(
                "workflow_operation_v3", {"operation": payload}
            ).unwrap()
            assert response["success"], response
            assert response["result"]["refusal"] is None, response
            return response["result"]["outcome"]

        assert native(current) == native(legacy)
        retired = replace(
            operation,
            lifecycle=replace(operation.lifecycle, admission=AdmissionFacet.RETIRED),
            replacement_operation_id=OperationId("replacement:review"),
        )
        outcome = native(asdict(retired))
        assert outcome["is_executable"] is False
        assert outcome["operation"]["replacement_operation_id"] == {
            "value": "replacement:review"
        }

        invalid = asdict(retired)
        invalid["lifecycle"]["admission"] = "Admitted"
        refused = RustSymbolGameHost().invoke_runtime(
            "workflow_operation_v3", {"operation": invalid}
        ).unwrap()
        assert refused["success"] is True
        assert refused["result"]["refusal"]["code"] == "OEWAS_VALUE_ERROR"
        assert refused["result"]["outcome"] is None

if __name__ == "__main__":
    unittest.main()


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("colour_id", ColourId("State"), "COLOUR_MISMATCH"),
        ("schema_ref", SchemaRef("schema:foreign:v1"), "SCHEMA_REFERENCE_MISMATCH"),
        ("schema_digest", ContentDigest.sha256("e" * 64), "SCHEMA_DIGEST_MISMATCH"),
        ("validator_ref", "validator:foreign:v1", "VALIDATOR_REFERENCE_MISMATCH"),
        ("validator_digest", ContentDigest.sha256("f" * 64), "VALIDATOR_DIGEST_MISMATCH"),
    ],
)
def test_full_typed_boundary_refuses_foreign_field_then_exact_restore_recovers(field, value, code):
    port = PortSpecV3(
        "parent-input", ColourId("Code"), SchemaRef("schema:code:v1"),
        ContentDigest.sha256("a" * 64), "validator:code:v1", ContentDigest.sha256("b" * 64),
    )
    life = SkillLifecycleV3(
        DeclarationFacet.DECLARED, SchemaBindingFacet.BOUND, ExecutorBindingFacet.BOUND,
        ValidationFacet.VALIDATED, AdmissionFacet.UNADMITTED,
        ContentDigest.sha256("c" * 64), ContentDigest.sha256("d" * 64),
    )
    parent = OperationV3(OperationId("parent"), (port,), port, (), life, "HOLD")
    output = replace(port, name="child-output")
    child = OperationV3(OperationId("child"), (), output, (), life, "HOLD")
    adapter = HigherOperadAdapter()
    assert adapter.verify_composition(parent, (child,), ((0, child),)).unwrap() is True
    changed = replace(child, output=replace(output, **{field: value}))
    refused = adapter.verify_composition(parent, (changed,), ((0, changed),))
    assert refused.is_err, f"A foreign {field} was accepted"
    assert refused.unwrap_err().code == code
    assert adapter.verify_composition(parent, (child,), ((0, child),)).unwrap() is True
