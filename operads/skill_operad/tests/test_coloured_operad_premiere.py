"""test_coloured_operad_premiere.py

Unit tests for premiere-level colored operad morphisms, anti-morphisms,
residuals, antibodies, evidence receipts, and HoTT-lite path semantics.

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

_SHARED_DIR = Path(__file__).resolve().parents[1]
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from coloured_operad import (
    AntiMorphism,
    ColoredOp,
    Residual,
    Term,
    Witness,
    identity,
    nullary,
)
from evidence_receipt import (
    CommandRecord,
    EvidenceReceipt,
    compute_normalized_source_sha256,
)
from antibodies import (
    ConcreteWitness,
    create_default_antibody_battery,
    make_ast_pattern_antibody,
    make_differential_replay_antibody,
    make_property_invariant_antibody,
    scan_source_for_pitfalls,
)
from hott import (
    HallucinationWitness,
    Path as HottPath,
    identity_path,
    transport,
)


class ResidualMonoidTests(unittest.TestCase):
    def test_claims_are_not_promoted_from_unverified_obligations(self) -> None:
        claims_only = Residual(claims=("verified-local",))
        open_only = Residual(obligations=("still-open",))
        self.assertEqual(claims_only.claims, ("verified-local",))
        self.assertEqual(claims_only.unverified, ())
        self.assertEqual(open_only.claims, ())
        self.assertEqual(open_only.unverified, ("still-open",))
        self.assertEqual(open_only.obligations, ("still-open",))

    def test_facades_preserve_domain_type_identity(self) -> None:
        from domain.evidence import Residual as DomainResidual, Witness as DomainWitness
        from domain.planar import ColoredOp as DomainColoredOp

        self.assertIs(Residual, DomainResidual)
        self.assertIs(Witness, DomainWitness)
        self.assertIs(ColoredOp, DomainColoredOp)

    def test_residual_absorption(self) -> None:
        r1 = Residual(claims=("claim_1",), unverified=("unv_1",), risk_score=0.2)
        r2 = Residual(claims=("claim_2",), unverified=("unv_2",), risk_score=0.8)
        absorbed = r1.absorb(r2)

        self.assertEqual(absorbed.claims, ("claim_1", "claim_2"))
        self.assertEqual(absorbed.unverified, ("unv_1", "unv_2"))
        self.assertEqual(absorbed.risk_score, 0.8)

    def test_residual_empty_identity(self) -> None:
        empty = Residual()
        r = Residual(claims=("c",), unverified=(), risk_score=0.1)
        self.assertEqual(empty.absorb(r), r)


class ColoredOpTests(unittest.TestCase):
    def test_identity_and_nullary_use_positional_body_contract(self) -> None:
        payload = {"zero": 0}
        self.assertEqual(identity("Code")(payload)[0], payload)
        self.assertEqual(nullary("Code", payload)()[0], payload)

    def test_body_type_error_is_not_retried_with_another_call_shape(self) -> None:
        calls = 0

        def broken(_: object) -> tuple[object, Residual]:
            nonlocal calls
            calls += 1
            raise TypeError("body defect")

        op = ColoredOp("broken", ("Code",), "Code", broken)
        with self.assertRaisesRegex(TypeError, "body defect"):
            op("input")
        self.assertEqual(calls, 1)

    def test_term_evaluation_uses_the_same_positional_contract(self) -> None:
        merge = ColoredOp(
            "merge",
            ("Code", "Code"),
            "Code",
            lambda left, right: ((left, right), Residual()),
        )
        term = Term(merge, (Term(nullary("Code", "a")), Term(nullary("Code", "b"))))
        self.assertEqual(term.evaluate()[0], ("a", "b"))

    def test_single_op_execution(self) -> None:
        op: ColoredOp[str, str] = ColoredOp(
            name="uppercase",
            source_colors=("Code",),
            target_color="Code",
            residual=Residual(claims=("declared_uppercase",), unverified=(), risk_score=0.0),
            body=lambda s: (s.upper(), Residual(claims=("executed_upper",), unverified=(), risk_score=0.1)),
        )

        result, r = op("hello")
        self.assertEqual(result, "HELLO")
        self.assertIn("declared_uppercase", r.claims)
        self.assertIn("executed_upper", r.claims)
        self.assertEqual(r.risk_score, 0.1)

    def test_op_composition_success(self) -> None:
        op1: ColoredOp[str, str] = ColoredOp(
            name="strip",
            source_colors=("Code",),
            target_color="Code",
            residual=Residual(claims=("strip_op",), unverified=(), risk_score=0.1),
            body=lambda s: (s.strip(), Residual()),
        )
        op2: ColoredOp[str, int] = ColoredOp(
            name="length",
            source_colors=("Code",),
            target_color="Evidence",
            residual=Residual(claims=("len_op",), unverified=(), risk_score=0.2),
            body=lambda s: (len(s), Residual()),
        )

        composed = op2.compose(op1)
        self.assertEqual(composed.name, "length∘strip")
        self.assertEqual(composed.source_colors, ("Code",))
        self.assertEqual(composed.target_color, "Evidence")

        res, r = composed("  hello  ")
        self.assertEqual(res, 5)
        self.assertEqual(r.risk_score, 0.2)
        self.assertIn("strip_op", r.claims)
        self.assertIn("len_op", r.claims)

    def test_op_composition_color_mismatch_raises(self) -> None:
        op1: ColoredOp[str, str] = ColoredOp(
            name="code_to_state",
            source_colors=("Code",),
            target_color="State",
            residual=Residual(),
            body=lambda s: (s, Residual()),
        )
        op2: ColoredOp[str, str] = ColoredOp(
            name="expects_audit",
            source_colors=("Audit",),
            target_color="Receipt",
            residual=Residual(),
            body=lambda s: (s, Residual()),
        )
        with self.assertRaises(TypeError):
            op2.compose(op1)

    def test_op_composition_arity_mismatch_raises(self) -> None:
        op: ColoredOp[str, str] = ColoredOp(
            name="binary_op",
            source_colors=("Code", "Code"),
            target_color="Code",
            residual=Residual(),
            body=lambda s: (s, Residual()),
        )
        op_inner: ColoredOp[str, str] = ColoredOp(
            name="unary_op",
            source_colors=("Code",),
            target_color="Code",
            residual=Residual(),
            body=lambda s: (s, Residual()),
        )
        with self.assertRaises(ValueError):
            op.compose(op_inner)  # Expected 2 inners, got 1


class AntibodyBatteryTests(unittest.TestCase):
    def test_ast_antibody_detects_mutable_default(self) -> None:
        bad_code = "def append_item(x: int, target: list[int] = []) -> list[int]:\n    target.append(x)\n    return target\n"
        witnesses = scan_source_for_pitfalls(bad_code)
        self.assertTrue(any(w.kind == "MUTABLE_DEFAULT_ARGUMENT" for w in witnesses))

    def test_ast_antibody_detects_bare_except(self) -> None:
        bad_code = "try:\n    x = 1\nexcept:\n    x = 0\n"
        witnesses = scan_source_for_pitfalls(bad_code)
        self.assertTrue(any(w.kind == "BARE_EXCEPT" for w in witnesses))

    def test_ast_antibody_detects_literal_is(self) -> None:
        bad_code = "def is_foo(val: str) -> bool:\n    return val is 'foo'\n"
        witnesses = scan_source_for_pitfalls(bad_code)
        self.assertTrue(any(w.kind == "LITERAL_IS_COMPARISON" for w in witnesses))

    def test_ast_antibody_detects_type_equality(self) -> None:
        bad_code = "def check(val: object) -> bool:\n    return type(val) == int\n"
        witnesses = scan_source_for_pitfalls(bad_code)
        self.assertTrue(any(w.kind == "TYPE_EQUALITY_CHECK" for w in witnesses))

    def test_ast_antibody_detects_any_on_public_surface(self) -> None:
        bad_code = "from typing import Any\ndef calculate(data: Any) -> int:\n    return len(data)\n"
        witnesses = scan_source_for_pitfalls(bad_code)
        self.assertTrue(any(w.kind == "ANY_ON_PUBLIC_SURFACE" for w in witnesses))

    def test_ast_antibody_passes_clean_code(self) -> None:
        clean_code = "from typing import Sequence\ndef calculate(data: Sequence[int]) -> int:\n    return len(data)\n"
        witnesses = scan_source_for_pitfalls(clean_code)
        self.assertEqual(witnesses, [])

    def test_anti_morphism_kill_vs_survive(self) -> None:
        ab = make_ast_pattern_antibody()
        bad_code = "def f(items: list = []): pass"
        clean_code = "def f(items: tuple[int, ...] = ()): pass"

        kill_witness, r_bad = ab.apply(bad_code)
        self.assertIsNotNone(kill_witness)
        self.assertEqual(r_bad.risk_score, 1.0)
        self.assertTrue(isinstance(kill_witness, Witness))

        no_witness, r_good = ab.apply(clean_code)
        self.assertIsNone(no_witness)
        self.assertEqual(r_good.risk_score, 0.1)
        self.assertIn("survived ASTStaticAntiPatternAntibody", r_good.claims)


class EvidenceReceiptTests(unittest.TestCase):
    def test_command_record_hashing(self) -> None:
        rec = CommandRecord.from_execution(
            cmd=["pytest", "-v"],
            cwd="/repo",
            exit_code=0,
            stdout="collected 10 items\n10 passed",
            duration_s=1.23,
        )
        self.assertEqual(rec.exit_code, 0)
        self.assertEqual(len(rec.stdout_sha256), 64)

    def test_evidence_receipt_clean_predicate(self) -> None:
        receipt = EvidenceReceipt(
            sys_executable="python",
            python_version="3.14.2",
            platform="win32",
            packaging_root=".",
            layout="src",
            git_head="abcd123",
            git_status_dirty=False,
            changed_paths=("src/mod.py",),
            change_sha256=compute_normalized_source_sha256("def add(a: int, b: int) -> int: return a + b"),
            commands=(),
            test_counts={"collected": 5, "passed": 5, "failed": 0},
            contract_discovery="Protocol",
            invariants=("add_commutative",),
            counterexample_level="property",
            antibodies_applied=("ASTStaticAntiPatternAntibody",),
            witnesses_found=(),
            residual=(),
            unverified_claims=(),
        )
        self.assertTrue(receipt.is_clean())
        self.assertEqual(receipt.authority_effect, "None")
        d = receipt.to_dict()
        self.assertEqual(d["python_version"], "3.14.2")


class HoTTLiteTests(unittest.TestCase):
    def test_identity_path(self) -> None:
        code = "def identity(x: int) -> int: return x"
        path = identity_path(code)
        self.assertTrue(path.is_valid)
        self.assertEqual(path.source, path.target)
        self.assertEqual(path.residual.risk_score, 0.0)

    def test_transport_clean_survives(self) -> None:
        code = "def add(x: int, y: int) -> int: return x + y"
        battery = create_default_antibody_battery()
        path = transport(code, battery, source_reference="contract_add")
        self.assertTrue(path.is_valid)
        self.assertIn("ASTStaticAntiPatternAntibody", path.antibodies_passed)

    def test_transport_falsified_detects_hallucination(self) -> None:
        broken_code = "def add(x: int, y: int = []) -> int: return x"
        battery = create_default_antibody_battery()
        path = transport(broken_code, battery, source_reference="contract_add")
        self.assertFalse(path.is_valid)
        self.assertIsNotNone(path.witness)
        self.assertTrue(isinstance(path.witness, HallucinationWitness))
        self.assertIn("Hallucination detected", path.witness.describe())


class HoTTGroupoidTests(unittest.TestCase):
    def test_refl_and_inv_symmetry(self) -> None:
        p = HottPath(source="state_A", target="state_B", steps=("step1",))
        inv_p = p.inv()
        self.assertEqual(inv_p.source, "state_B")
        self.assertEqual(inv_p.target, "state_A")
        self.assertEqual(inv_p.steps, ("inv(step1)",))

        # Double inversion gives back original endpoints
        inv_inv_p = inv_p.inv()
        self.assertEqual(inv_inv_p.source, p.source)
        self.assertEqual(inv_inv_p.target, p.target)

    def test_path_concat_associativity_and_unitors(self) -> None:
        p1 = HottPath(source="A", target="B", steps=("1",))
        p2 = HottPath(source="B", target="C", steps=("2",))
        p3 = HottPath(source="C", target="D", steps=("3",))

        # Associativity: (p1 @ p2) @ p3 == p1 @ (p2 @ p3)
        left = (p1 @ p2) @ p3
        right = p1 @ (p2 @ p3)
        self.assertEqual(left.source, right.source)
        self.assertEqual(left.target, right.target)
        self.assertEqual(left.steps, right.steps)

        # Left unitor: refl(A) @ p1 == p1
        from hott import refl
        left_unit = refl("A") @ p1
        self.assertEqual(left_unit.source, p1.source)
        self.assertEqual(left_unit.target, p1.target)

        # Right unitor: p1 @ refl(B) == p1
        right_unit = p1 @ refl("B")
        self.assertEqual(right_unit.source, p1.source)
        self.assertEqual(right_unit.target, p1.target)

    def test_path_concat_endpoint_mismatch_fails_closed(self) -> None:
        p1 = HottPath(source="A", target="B")
        p2 = HottPath(source="X", target="Y")
        broken = p1 @ p2
        self.assertFalse(broken.is_valid)
        self.assertIsNotNone(broken.witness)
        self.assertIn("EndpointMatching", broken.witness.describe())


class Homotopy2CellTests(unittest.TestCase):
    def test_homotopy_2cell_vertical_composition(self) -> None:
        from hott import Homotopy2Cell
        p1 = HottPath(source="A", target="B", steps=("p1",))
        p2 = HottPath(source="A", target="B", steps=("p2",))
        p3 = HottPath(source="A", target="B", steps=("p3",))

        alpha = Homotopy2Cell(name="alpha", source_path=p1, target_path=p2)
        beta = Homotopy2Cell(name="beta", source_path=p2, target_path=p3)
        composed_v = alpha.compose_vertical(beta)

        self.assertEqual(composed_v.source_path, p1)
        self.assertEqual(composed_v.target_path, p3)
        self.assertTrue(composed_v.is_valid)

    def test_homotopy_2cell_horizontal_composition(self) -> None:
        from hott import Homotopy2Cell
        p1 = HottPath(source="A", target="B", steps=("p1",))
        q1 = HottPath(source="A", target="B", steps=("q1",))
        p2 = HottPath(source="B", target="C", steps=("p2",))
        q2 = HottPath(source="B", target="C", steps=("q2",))

        alpha = Homotopy2Cell(name="alpha", source_path=p1, target_path=q1)
        beta = Homotopy2Cell(name="beta", source_path=p2, target_path=q2)
        composed_h = alpha.compose_horizontal(beta)

        self.assertEqual(composed_h.source_path.source, "A")
        self.assertEqual(composed_h.source_path.target, "C")
        self.assertEqual(composed_h.target_path.source, "A")
        self.assertEqual(composed_h.target_path.target, "C")


class PullbackAntibodyTests(unittest.TestCase):
    def test_pullback_antibody_detects_forward_violation(self) -> None:
        from antibodies import pullback_antibody
        from coloured_operad import ColoredOp, Residual

        # Forward op: generates code with mutable default
        bad_generator: ColoredOp[str, str] = ColoredOp(
            name="bad_generator",
            source_colors=("Code",),
            target_color="Code",
            residual=Residual(),
            body=lambda s: (f"def gen(x: int, buf: list = []):\n    pass\n", Residual()),
        )
        ast_ab = make_ast_pattern_antibody()
        pb_ab = pullback_antibody(bad_generator, ast_ab)

        witness, res = pb_ab.apply("dummy_spec")
        self.assertIsNotNone(witness)
        self.assertIn("MUTABLE_DEFAULT_ARGUMENT", witness.describe())

    def test_pullback_antibody_passes_clean_forward(self) -> None:
        from antibodies import pullback_antibody
        from coloured_operad import ColoredOp, Residual

        good_generator: ColoredOp[str, str] = ColoredOp(
            name="good_generator",
            source_colors=("Code",),
            target_color="Code",
            residual=Residual(),
            body=lambda s: (f"def gen(x: int, buf: tuple = ()):\n    pass\n", Residual()),
        )
        ast_ab = make_ast_pattern_antibody()
        pb_ab = pullback_antibody(good_generator, ast_ab)

        witness, res = pb_ab.apply("dummy_spec")
        self.assertIsNone(witness)
        self.assertEqual(res.unverified, ())
        self.assertIn("survived", res.claims[0])


if __name__ == "__main__":
    unittest.main()

