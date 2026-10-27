"""Acceptance and contract tests verifying the 6 review findings for DDD Grammar and Packets.

Enforces:
1. Admission Fails Closed: Reject out-of-alphabet characters, unregistered opcodes, and nested higher-stage lifts.
2. Honest Outcomes & Authority Boundaries: Reject node/wire mismatch in validate(); decouple <1101> from terminal.
3. Opcode Table Parity: <100101> is Stage 13; <11010> is Stage 7; unknown opcodes fail closed.
4. Per-Candidate Conditioning & Frontier Hygiene: Unique token IDs, bounds checks, exact Bayes conditioning.
5. Mathematical Check Preconditions: QuantifierMask switches = 2 for '010'; Gram matrix enforces vertex distinctness.
6. Raw Syntax vs Typed Application & Recursion Depth: Reject untyped op<>; fail-stop on nesting depth > 32.
"""

from __future__ import annotations

from fractions import Fraction
import os
import sys
import unittest

# Ensure research directory is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_RESEARCH_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))
if _RESEARCH_DIR not in sys.path:
    sys.path.insert(0, _RESEARCH_DIR)

from pfp.domain.mssn_research.grammar.entities import TokenFrontier, TowerGrammar
from pfp.domain.mssn_research.grammar.errors import FrontierInconsistencyError, GrammarDomainError
from pfp.domain.mssn_research.grammar.lexical import (
    Alphabet,
    FrontierCandidate,
    ParserStateId,
    ProbabilityMass,
    QuantifierMask,
)
from pfp.domain.mssn_research.packets.entities import App, Atom, Diff, Packet
from pfp.domain.mssn_research.packets.errors import MalformedWireError, PacketDomainError, StageFloorViolationError
from pfp.domain.mssn_research.packets.invariants import (
    check_gram_matrix_positive_definiteness,
    check_opcode_stage_floor,
    check_simplex_distinctness,
)
from pfp.domain.mssn_research.packets.value_objects import (
    Opcode,
    RefusalCode,
    ValidationDisposition,
    WireBytes,
)
from pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal
from pfp.domain.mssn_research.shared_kernel.value_objects import Rational, StageLevel


class TestReviewFinding1AdmissionFailsClosed(unittest.TestCase):
    """Critical Finding 1: Admission fails closed across all AST nodes."""

    def test_stage_1_rejects_out_of_alphabet_atom(self) -> None:
        """Stage 1 admits only binary symbols ('0', '1'). Wire containing <2> must be refused."""
        g1 = TowerGrammar.for_stage(StageLevel(1))
        # Atom <2> directly
        res_atom = g1.parse_packet("<2>")
        self.assertTrue(res_atom.is_refusal(), f"Expected refusal for <2> at stage 1, got {res_atom}")
        self.assertEqual(res_atom.refusal.code, RefusalCode.INACTIVE_SYMBOL)

        # Atom <2> inside lift argument op<<0><2>>
        res_app = g1.parse_packet("op<<0><2>>")
        self.assertTrue(res_app.is_refusal(), f"Expected refusal for op<<0><2>> at stage 1, got {res_app}")
        self.assertEqual(res_app.refusal.code, RefusalCode.INACTIVE_SYMBOL)

    def test_stage_1_rejects_unregistered_opcode(self) -> None:
        """An unregistered opcode (e.g. <11111111>) must fail closed with UNKNOWN_OPCODE."""
        g1 = TowerGrammar.for_stage(StageLevel(1))
        res = g1.parse_packet("op<<11111111><0>>")
        self.assertTrue(res.is_refusal(), f"Expected refusal for unregistered opcode, got {res}")
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)

    def test_stage_1_rejects_nested_higher_stage_opcode(self) -> None:
        """Nested lift op<<0>op<<101><0><0>>> contains opcode <101> (Stage 3). Must be refused at Stage 1."""
        g1 = TowerGrammar.for_stage(StageLevel(1))
        res = g1.parse_packet("op<<0>op<<101><0><0>>>")
        self.assertTrue(res.is_refusal(), f"Expected refusal for nested stage 3 opcode at stage 1, got {res}")
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


class TestReviewFinding2HonestOutcomesAndAuthority(unittest.TestCase):
    """Critical Finding 2: Validate node/wire correspondence and decouple <1101> from terminal."""

    def test_packet_validation_rejects_node_wire_mismatch(self) -> None:
        """A packet constructed with node=Diff() but wire='<1>' must be rejected by validate()."""
        corrupted_pkt = Packet(node=Diff(), wire=WireBytes("<1>"), stage_level=StageLevel(1))
        val_res = corrupted_pkt.validate(StageLevel(1))
        self.assertTrue(val_res.is_err(), f"Expected validation error on node/wire mismatch, got {val_res}")
        self.assertIsInstance(val_res.error, MalformedWireError)

    def test_opcode_1101_is_not_terminal(self) -> None:
        """Opcode <1101> (13 decimal) is assigned to Level 7 PeriodicOrbitTable, NOT terminal."""
        g7 = TowerGrammar.for_stage(StageLevel(7))
        pkt_res = g7.parse_packet("op<<1101><0>>")
        self.assertTrue(pkt_res.is_ok(), f"Expected valid parse at stage 7, got {pkt_res}")
        pkt = pkt_res.unwrap()
        self.assertFalse(pkt.is_terminal(), "Opcode <1101> must not be classified as terminal")

    def test_validation_disposition_includes_stage_admitted(self) -> None:
        """ValidationDisposition must expose STAGE_ADMITTED for representation gating."""
        self.assertTrue(hasattr(ValidationDisposition, "STAGE_ADMITTED"))
        self.assertEqual(ValidationDisposition.STAGE_ADMITTED.value, "StageAdmitted")


class TestReviewFinding3OpcodeTableParity(unittest.TestCase):
    """High Finding 3: Opcode registry parity against MSS papers and fail-closed resolution."""

    def test_opcode_100101_is_level_13(self) -> None:
        """Opcode <100101> (37 decimal) is assigned to Level 13 (BQNF / Alternation view)."""
        op = Opcode("100101")
        self.assertEqual(op.decimal_value, 37)
        self.assertEqual(op.stage_floor, StageLevel(13))

    def test_opcode_11010_is_level_7(self) -> None:
        """Opcode <11010> (26 decimal) is assigned to Level 7 (ShiftSpec)."""
        op = Opcode("11010")
        self.assertEqual(op.decimal_value, 26)
        self.assertEqual(op.stage_floor, StageLevel(7))

    def test_unknown_opcode_fails_closed(self) -> None:
        """Unknown opcodes must report is_registered=False and raise ValueError on stage_floor access."""
        unknown_op = Opcode("11111111")
        self.assertFalse(unknown_op.is_registered)
        with self.assertRaises(ValueError):
            _ = unknown_op.stage_floor

        # Invariant check must refuse unknown opcode
        check_res = check_opcode_stage_floor(unknown_op, StageLevel(1))
        self.assertTrue(check_res.is_refusal())
        self.assertEqual(check_res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


class TestReviewFinding4FrontierConditioning(unittest.TestCase):
    """High Finding 4: Enforce unique IDs, bounds, and exact per-candidate Bayes conditioning."""

    def setUp(self) -> None:
        self.retained_mass = ProbabilityMass(Rational(1, 2))

    def test_frontier_rejects_duplicate_token_ids(self) -> None:
        """Frontier with duplicate token IDs must be rejected."""
        c1 = FrontierCandidate(
            token_id=10,
            emitted_bytes=b"A",
            parser_state_after=ParserStateId("s/1"),
            base_probability=Rational(1, 4),
            constrained_probability=Rational(1, 2),
        )
        c2 = FrontierCandidate(
            token_id=10,  # Duplicate ID
            emitted_bytes=b"B",
            parser_state_after=ParserStateId("s/2"),
            base_probability=Rational(1, 4),
            constrained_probability=Rational(1, 2),
        )
        res = TokenFrontier.create(vocabulary_size=100, candidates=[c1, c2], retained_mass=self.retained_mass)
        self.assertTrue(res.is_err(), f"Expected error on duplicate token ID, got {res}")
        self.assertIn("Duplicate", res.error.message)

    def test_frontier_rejects_out_of_range_token_ids(self) -> None:
        """Frontier with candidate token ID >= vocabulary size must be rejected."""
        c = FrontierCandidate(
            token_id=100,  # >= vocab size 100
            emitted_bytes=b"A",
            parser_state_after=ParserStateId("s/1"),
            base_probability=Rational(1, 2),
            constrained_probability=Rational(1, 1),
        )
        res = TokenFrontier.create(vocabulary_size=100, candidates=[c], retained_mass=self.retained_mass)
        self.assertTrue(res.is_err(), f"Expected error on out-of-range token ID, got {res}")
        self.assertIn("out of bounds", res.error.message)

    def test_frontier_rejects_unconditioned_probabilities(self) -> None:
        """Frontier where base sums to 1/2 and constrained sums to 1, but per-candidate ratio violates Bayes."""
        # Candidate 1: base = 1/4, expected constrained = (1/4)/(1/2) = 1/2. Given: 3/4.
        # Candidate 2: base = 1/4, expected constrained = (1/4)/(1/2) = 1/2. Given: 1/4.
        # Both sums match: base sum = 1/2, constrained sum = 1. But ratios are wrong!
        c1 = FrontierCandidate(
            token_id=1,
            emitted_bytes=b"A",
            parser_state_after=ParserStateId("s/1"),
            base_probability=Rational(1, 4),
            constrained_probability=Rational(3, 4),
        )
        c2 = FrontierCandidate(
            token_id=2,
            emitted_bytes=b"B",
            parser_state_after=ParserStateId("s/2"),
            base_probability=Rational(1, 4),
            constrained_probability=Rational(1, 4),
        )
        res = TokenFrontier.create(vocabulary_size=100, candidates=[c1, c2], retained_mass=self.retained_mass)
        self.assertTrue(res.is_err(), f"Expected error on unconditioned probabilities, got {res}")
        self.assertIn("does not match conditioned value", res.error.message)


class TestReviewFinding5MathematicalPreconditions(unittest.TestCase):
    """Medium Finding 5: Quantifier switches vs blocks and Gram simplex distinctness precondition."""

    def test_quantifier_mask_reports_two_switches_for_010(self) -> None:
        """Level 14 paper specifies switches: QuantifierMask('010') has exactly 2 switches."""
        qm = QuantifierMask("010")
        self.assertEqual(qm.switch_count, 2)
        self.assertEqual(qm.switches, 2)
        self.assertEqual(qm.block_count, 3)

    def test_gram_checker_rejects_repeated_vertices_upfront(self) -> None:
        """check_gram_matrix_positive_definiteness must compose check_simplex_distinctness as a precondition."""
        degenerate_vertices = ["v0", "v0"]
        lengths = {frozenset({"v0"}): 1}
        res = check_gram_matrix_positive_definiteness(degenerate_vertices, lengths)
        self.assertTrue(res.is_refusal(), f"Expected refusal on repeated vertices in Gram check, got {res}")
        self.assertIn("repeated vertex", res.refusal.message)


class TestReviewFinding6RawSyntaxAndRecursionLimits(unittest.TestCase):
    """Medium Finding 6: Reject untyped op<> in typed packets and fail-stop on nesting depth > 32."""

    def test_typed_parser_rejects_untyped_op_empty(self) -> None:
        """Typed applications require an opcode child; op<> must be rejected."""
        res = Packet.from_wire("op<>", StageLevel(1))
        self.assertTrue(res.is_err(), f"Expected error for untyped op<>, got {res}")
        self.assertEqual(res.error.code, RefusalCode.UNKNOWN_OPCODE)

    def test_deeply_nested_wire_rejects_gracefully_without_recursion_error(self) -> None:
        """Deeply nested wire (depth > 32) must be caught by depth limit without raising RecursionError."""
        # Build 40 levels of nesting: op<<0>op<<0> ... <> ... >>
        nested = "<>"
        for _ in range(40):
            nested = f"op<<0>{nested}>"
        res = Packet.from_wire(nested, StageLevel(1))
        self.assertTrue(res.is_err(), f"Expected Err on exceeding depth limit, got {res}")
        self.assertIn("depth exceeds maximum nesting limit", res.error.message)


if __name__ == "__main__":
    unittest.main()
