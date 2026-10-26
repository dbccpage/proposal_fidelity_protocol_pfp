"""Comprehensive Unit Tests for PFP Domain Value Objects.

AuthorityEffect: None.
Verifies:
1. Input validation upon instantiation (rejects malformed inputs, wrong types, illegal ranges).
2. Value Object exact-type equality invariant: type(self) is type(other) in __eq__.
3. Subclass and cross-class type confusion guards.
4. Composite hashing consistency.
"""

from __future__ import annotations

from dataclasses import dataclass
import unittest

from omega_engine_pfp.domain.value_objects.numerics import BoundedTemperature
from omega_engine_pfp.domain.value_objects.topology import ByteSpanVO
from omega_engine_pfp.domain.value_objects.identifiers import CheckerIdVO
from omega_engine_pfp.domain.value_objects.numerics import DifficultyRung
from omega_engine_pfp.domain.value_objects.topology import EdgeVO
from omega_engine_pfp.domain.value_objects.taxonomy import EvaluationStatusVO
from omega_engine_pfp.domain.value_objects.taxonomy import ExecutionModeVO
from omega_engine_pfp.domain.value_objects.topology import MatrixShape
from omega_engine_pfp.domain.value_objects.numerics import MicroUsdSpend
from omega_engine_pfp.domain.value_objects.identifiers import NormalFormId
from omega_engine_pfp.domain.value_objects.identifiers import PilotId
from omega_engine_pfp.domain.value_objects.identifiers import PromptId
from omega_engine_pfp.domain.value_objects.identifiers import RequestId
from omega_engine_pfp.domain.value_objects.identifiers import Sha256Digest
from omega_engine_pfp.domain.value_objects.taxonomy import SpanRoleVO
from omega_engine_pfp.domain.value_objects.numerics import StageNumber
from omega_engine_pfp.domain.value_objects.numerics import StratumLevel
from omega_engine_pfp.domain.value_objects.taxonomy import TaskFamilyVO
from omega_engine_pfp.domain.value_objects.taxonomy import TrialStatusVO
from omega_engine_pfp.domain.value_objects.topology import VertexId


class TestValueObjectsInputTesting(unittest.TestCase):
    """Test input testing and validation across all Value Objects."""

    def test_pilot_id_validation(self) -> None:
        # Valid
        pid = PilotId("pilot_0000001")
        self.assertEqual(pid.value, "pilot_0000001")
        self.assertEqual(str(pid), "pilot_0000001")

        # Empty or whitespace
        with self.assertRaises(ValueError):
            PilotId("")
        with self.assertRaises(ValueError):
            PilotId("   ")
        with self.assertRaises(ValueError):
            PilotId(" pilot_001 ")
        with self.assertRaises(ValueError):
            PilotId("pilot with spaces")

        # Wrong type
        with self.assertRaises(TypeError):
            PilotId(123)  # type: ignore

    def test_request_id_validation(self) -> None:
        # Valid
        rid = RequestId("req-001_abc.1")
        self.assertEqual(rid.value, "req-001_abc.1")

        with self.assertRaises(ValueError):
            RequestId("")
        with self.assertRaises(ValueError):
            RequestId("bad request!")
        with self.assertRaises(TypeError):
            RequestId(None)  # type: ignore

    def test_checker_id_validation(self) -> None:
        checker = CheckerIdVO("PFP-01-EXACT-LINALG")
        self.assertTrue(checker.is_canonical)
        self.assertEqual(checker.value, "PFP-01-EXACT-LINALG")

        custom = CheckerIdVO("CUSTOM_CHECKER_01")
        self.assertFalse(custom.is_canonical)

        with self.assertRaises(ValueError):
            CheckerIdVO("")
        with self.assertRaises(ValueError):
            CheckerIdVO("invalid checker id!")

    def test_sha256_digest_validation(self) -> None:
        valid_hash = "a" * 64
        digest = Sha256Digest(valid_hash)
        self.assertEqual(digest.value, valid_hash)

        # Wrong length
        with self.assertRaises(ValueError):
            Sha256Digest("a" * 63)
        with self.assertRaises(ValueError):
            Sha256Digest("a" * 65)

        # Uppercase hex rejected
        with self.assertRaises(ValueError):
            Sha256Digest("A" * 64)

        # Non-hex characters
        with self.assertRaises(ValueError):
            Sha256Digest("g" * 64)

        # Wrong type
        with self.assertRaises(TypeError):
            Sha256Digest(12345)  # type: ignore

    def test_normal_form_id_validation(self) -> None:
        nf = NormalFormId("nf.coda.eqnf")
        self.assertEqual(nf.value, "nf.coda.eqnf")

        with self.assertRaises(ValueError):
            NormalFormId("eqnf")
        with self.assertRaises(ValueError):
            NormalFormId("nf.coda")
        with self.assertRaises(TypeError):
            NormalFormId(10)  # type: ignore

    def test_difficulty_rung_validation(self) -> None:
        # Valid: 1 to 5
        for r in range(1, 6):
            rung = DifficultyRung(r)
            self.assertEqual(int(rung), r)

        # Out of bounds
        with self.assertRaises(ValueError):
            DifficultyRung(0)
        with self.assertRaises(ValueError):
            DifficultyRung(6)

        # Rejects bools (True is not a pure int in domain sense)
        with self.assertRaises(TypeError):
            DifficultyRung(True)  # type: ignore

        # Rejects floats
        with self.assertRaises(TypeError):
            DifficultyRung(3.0)  # type: ignore

    def test_micro_usd_spend_validation(self) -> None:
        spend = MicroUsdSpend(500)
        self.assertEqual(int(spend), 500)
        self.assertEqual(spend.to_usd(), 0.0005)

        from_usd = MicroUsdSpend.from_usd(1.50)
        self.assertEqual(int(from_usd), 1_500_000)

        # Negative spend rejected
        with self.assertRaises(ValueError):
            MicroUsdSpend(-1)

        # Float direct instantiation rejected
        with self.assertRaises(TypeError):
            MicroUsdSpend(10.5)  # type: ignore

    def test_bounded_temperature_validation(self) -> None:
        t0 = BoundedTemperature(0.0)
        self.assertEqual(float(t0), 0.0)
        t2 = BoundedTemperature(2.0)
        self.assertEqual(float(t2), 2.0)
        t_int = BoundedTemperature(1)
        self.assertEqual(float(t_int), 1.0)

        # Out of bounds
        with self.assertRaises(ValueError):
            BoundedTemperature(-0.1)
        with self.assertRaises(ValueError):
            BoundedTemperature(2.01)

        # Wrong type
        with self.assertRaises(TypeError):
            BoundedTemperature("0.5")  # type: ignore

    def test_stage_number_and_stratum_level(self) -> None:
        s1 = StageNumber(1)
        s8 = StageNumber(11)
        self.assertEqual(int(s1), 1)
        self.assertEqual(int(s8), 11)

        with self.assertRaises(ValueError):
            StageNumber(0)
        with self.assertRaises(ValueError):
            StageNumber(12)

        lvl0 = StratumLevel(0)
        lvl6 = StratumLevel(6)
        self.assertEqual(int(lvl0), 0)
        self.assertEqual(int(lvl6), 6)

        with self.assertRaises(ValueError):
            StratumLevel(-1)
        with self.assertRaises(ValueError):
            StratumLevel(7)

    def test_topology_validation(self) -> None:
        v0 = VertexId(0)
        v10 = VertexId(10)
        self.assertEqual(int(v0), 0)
        with self.assertRaises(ValueError):
            VertexId(-1)

        edge = EdgeVO(v0, v10)
        self.assertEqual(edge.src, v0)
        self.assertEqual(edge.tgt, v10)

        # Auto-wrap integer vertex IDs
        edge2 = EdgeVO(0, 10)  # type: ignore
        self.assertEqual(edge2.src, v0)
        self.assertEqual(edge2.tgt, v10)

        # Byte span
        span = ByteSpanVO(10, 25)
        self.assertEqual(span.length, 15)
        self.assertTrue(span.contains(10))
        self.assertTrue(span.contains(24))
        self.assertFalse(span.contains(25))
        self.assertEqual(span.slice("0123456789abcdefghijklmnopqrstuvwxyz"), "abcdefghijklmno")

        with self.assertRaises(ValueError):
            ByteSpanVO(25, 10)  # start > end

        # Matrix shape
        shape = MatrixShape(3, 3)
        self.assertTrue(shape.is_square)
        self.assertEqual(shape.total_entries, 9)

    def test_taxonomy_validation(self) -> None:
        tf = TaskFamilyVO("linear_algebra")
        self.assertEqual(str(tf), "linear_algebra")
        with self.assertRaises(ValueError):
            TaskFamilyVO("unknown_family")

        em = ExecutionModeVO("offline_fixture")
        self.assertEqual(str(em), "offline_fixture")
        with self.assertRaises(ValueError):
            ExecutionModeVO("cloud_run")

        status = EvaluationStatusVO("ACCEPTED")
        self.assertTrue(status.is_accepted)
        with self.assertRaises(ValueError):
            EvaluationStatusVO("PASSED")


class TestValueObjectExactTypeEquality(unittest.TestCase):
    """Verify RULE_VO_EXACT_TYPE_EQUALITY_001: type(self) is type(other)."""

    def test_reject_primitive_equality(self) -> None:
        pid = PilotId("pilot_0000001")
        # Comparing Value Object to raw string MUST return False
        self.assertFalse(pid == "pilot_0000001")
        self.assertFalse("pilot_0000001" == pid)

        rung = DifficultyRung(3)
        # Comparing Value Object to raw int MUST return False
        self.assertFalse(rung == 3)
        self.assertFalse(3 == rung)

        spend = MicroUsdSpend(100)
        self.assertFalse(spend == 100)

    def test_reject_cross_class_confusion(self) -> None:
        pid = PilotId("common_key_001")
        req = RequestId("common_key_001")
        prompt = PromptId("common_key_001")

        # Different VO classes with same internal string value MUST NOT be equal
        self.assertFalse(pid == req)
        self.assertFalse(req == pid)
        self.assertFalse(pid == prompt)
        self.assertFalse(req == prompt)

    def test_reject_subclass_confusion(self) -> None:
        @dataclass(frozen=True)
        class SyntheticPilotIdSubclass(PilotId):
            pass

        parent = PilotId("pilot_0000001")
        subclass_instance = SyntheticPilotIdSubclass("pilot_0000001")

        # Exact-type equality guard must reject subclass confusion
        self.assertFalse(parent == subclass_instance)
        self.assertFalse(subclass_instance == parent)

    def test_equality_and_hashing_consistency(self) -> None:
        p1 = PilotId("pilot_0000001")
        p2 = PilotId("pilot_0000001")
        p3 = PilotId("pilot_0000002")

        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        self.assertEqual(hash(p1), hash(p2))

        # Usable in sets and dict keys
        vo_set = {p1, p2, p3}
        self.assertEqual(len(vo_set), 2)


if __name__ == "__main__":
    unittest.main()
