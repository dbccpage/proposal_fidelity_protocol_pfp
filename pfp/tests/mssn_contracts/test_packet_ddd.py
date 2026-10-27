"""Unit and fitness tests for the Packet Aggregate Root and Packets Bounded Context.

Enforces:
- Exact-Type Value Object Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Pure Monadic Result Handling (RULE_ROP_RESULT_MONAD_001)
- Domain Invariant Verification
"""

import sys
from pathlib import Path
import unittest

# Ensure research directory is in sys.path so ddd package is importable
RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

from pfp.domain.mssn_research.packets.entities import App, Atom, Diff, Packet
from pfp.domain.mssn_research.packets.invariants import (
    check_delimiter_balance,
    check_gram_matrix_positive_definiteness,
    check_opcode_stage_floor,
    check_refusal_code_bounds,
    check_simplex_distinctness,
)
from pfp.domain.mssn_research.packets.value_objects import (
    Opcode,
    RefusalCode,
    RuntimeProofStatus,
    ValidationDisposition,
    WireBytes,
)
from pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal
from pfp.domain.mssn_research.shared_kernel.value_objects import (
    AuthorityEffect,
    ContentDigest,
    Rational,
    StageLevel,
)


class TestSharedKernelValueObjects(unittest.TestCase):
    def test_stage_level_exact_type_equality(self):
        s1 = StageLevel(1)
        s2 = StageLevel(1)
        s3 = StageLevel(2)

        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        # Exact-type equality guard: comparison to primitive int returns False
        self.assertFalse(s1 == 1)
        self.assertFalse(s1 == "1")
        self.assertFalse(1 == s1)

    def test_rational_exact_type_equality_and_reduction(self):
        r1 = Rational(2, 4)  # Reduces to 1/2
        r2 = Rational(1, 2)
        r3 = Rational(3, 4)

        self.assertEqual(r1.numerator, 1)
        self.assertEqual(r1.denominator, 2)
        self.assertEqual(r1, r2)
        self.assertNotEqual(r1, r3)
        self.assertFalse(r1 == 0.5)
        self.assertFalse(r1 == "1/2")

    def test_content_digest_validation(self):
        valid_hex = "a" * 64
        d = ContentDigest(valid_hex)
        self.assertEqual(d.value, valid_hex)
        self.assertFalse(d == valid_hex)

        with self.assertRaises(ValueError):
            ContentDigest("short_hex")
        with self.assertRaises(ValueError):
            ContentDigest("g" * 64)  # Non-hex


class TestPacketValueObjects(unittest.TestCase):
    def test_opcode_exact_type_equality_and_stage_floor(self):
        op0 = Opcode("0")
        op10 = Opcode("10")

        self.assertEqual(op0.decimal_value, 0)
        self.assertEqual(op10.decimal_value, 2)
        self.assertEqual(op0.stage_floor, StageLevel(1))
        self.assertEqual(op10.stage_floor, StageLevel(2))

        # Exact-type equality
        self.assertFalse(op0 == "0")
        self.assertFalse(op0 == 0)

    def test_wire_bytes_immutability(self):
        wb1 = WireBytes("<0>")
        wb2 = WireBytes("<0>")
        self.assertEqual(wb1, wb2)
        self.assertEqual(wb1.byte_length, 3)
        self.assertFalse(wb1 == "<0>")


class TestPacketAggregateRoot(unittest.TestCase):
    def test_void_packet_level_0(self):
        pkt = Packet.void()
        self.assertTrue(pkt.is_diff())
        self.assertEqual(pkt.wire.raw, "<>")
        self.assertEqual(pkt.stage_level, StageLevel(0))
        self.assertEqual(pkt.arity(), 0)

        # Validate under Level 0
        val_res = pkt.validate(StageLevel(0))
        self.assertTrue(val_res.is_ok())
        self.assertEqual(val_res.unwrap(), ValidationDisposition.CERTIFICATE)

    def test_atom_packet_creation(self):
        res = Packet.atom("101", StageLevel(1))
        self.assertTrue(res.is_ok())
        pkt = res.unwrap()
        self.assertTrue(pkt.is_atom())
        self.assertEqual(pkt.wire.raw, "<101>")

        # Atom rejected at Level 0
        lvl0_res = Packet.atom("0", StageLevel(0))
        self.assertTrue(lvl0_res.is_err())

    def test_compound_application_parsing(self):
        wire = "op<<10><0><1>>"  # Edge from vertex 0 to 1
        res = Packet.from_wire(wire, StageLevel(2))
        self.assertTrue(res.is_ok())
        pkt = res.unwrap()
        self.assertTrue(pkt.is_app())
        self.assertEqual(pkt.opcode(), Opcode("10"))
        self.assertEqual(pkt.arity(), 2)

    def test_stage_floor_refusal(self):
        # Opcode 10 (Edge) requires StageLevel(2); parsing at StageLevel(1) emits Refusal
        wire = "op<<10><0><1>>"
        res = Packet.from_wire(wire, StageLevel(1))
        self.assertTrue(res.is_err())

    def test_base_refusal_packet(self):
        wire = "op<<1100><0>>"  # Refusal 0: MalformedPacket
        res = Packet.from_wire(wire, StageLevel(6))
        self.assertTrue(res.is_ok())
        pkt = res.unwrap()
        self.assertTrue(pkt.is_refusal())
        val_res = pkt.validate(StageLevel(6))
        self.assertTrue(val_res.is_ok())
        self.assertEqual(val_res.unwrap(), ValidationDisposition.REFUSAL)

    def test_extended_refusal_packet(self):
        wire = "op<<1100><1000><101><11>>"  # ZeroRetainedMass extended refusal
        res = Packet.from_wire(wire, StageLevel(6))
        self.assertTrue(res.is_ok())
        pkt = res.unwrap()
        self.assertTrue(pkt.is_refusal())
        self.assertEqual(pkt.arity(), 3)


class TestPacketInvariants(unittest.TestCase):
    def test_delimiter_balance(self):
        self.assertTrue(check_delimiter_balance("<>").is_ok())
        self.assertTrue(check_delimiter_balance("op<<0><><0><1>>").is_ok())
        self.assertTrue(check_delimiter_balance("<<>>").is_ok())
        self.assertTrue(check_delimiter_balance("><").is_err())
        self.assertTrue(check_delimiter_balance("<").is_err())

    def test_simplex_distinctness(self):
        self.assertTrue(check_simplex_distinctness(["0", "1", "10"]).is_ok())
        self.assertTrue(check_simplex_distinctness(["0", "0"]).is_err())

    def test_gram_matrix_sylvester_criterion(self):
        vertices = ["0", "1", "10", "11"]
        # Regular unit tetrahedron: all edge lengths squared = 1
        lengths = {
            frozenset(("0", "1")): 1,
            frozenset(("0", "10")): 1,
            frozenset(("0", "11")): 1,
            frozenset(("1", "10")): 1,
            frozenset(("1", "11")): 1,
            frozenset(("10", "11")): 1,
        }
        res = check_gram_matrix_positive_definiteness(vertices, lengths)
        self.assertTrue(res.is_ok())

        # Indefinite Gram counterexample from test_packets.py
        # Leading 2x2 Gram minor is -7; should be rejected
        edges = [("0", "1", 9), ("0", "10", 1), ("0", "11", 9),
                 ("1", "10", 2), ("1", "11", 38), ("10", "11", 18)]
        bad_lengths = {frozenset((a, b)): d for a, b, d in edges}
        bad_res = check_gram_matrix_positive_definiteness(vertices, bad_lengths)
        self.assertTrue(bad_res.is_err())


if __name__ == "__main__":
    unittest.main()
