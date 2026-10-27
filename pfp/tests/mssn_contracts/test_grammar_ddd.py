"""Unit and fitness tests for the Grammar Bounded Context and TowerGrammar Aggregate Root.

Enforces:
- Alphabet Gating and Symbol Invariants
- Zero Probability Mass Fail-Stop Boundary Refusal
- Exact-Type Equality
"""

import sys
from pathlib import Path
import unittest

# Ensure research directory is in sys.path so ddd package is importable
RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

from pfp.domain.mssn_research.grammar.entities import TokenFrontier, TowerGrammar
from pfp.domain.mssn_research.grammar.foundational_policies import (
    check_alphabet_conformance,
    check_quantifier_mask_depth,
    check_wire_round_trip,
    check_zero_mass_fence,
)
from pfp.domain.mssn_research.grammar.lexical import (
    Alphabet,
    FrontierCandidate,
    ParserStateId,
    ProbabilityMass,
    QuantifierMask,
)
from pfp.domain.mssn_research.packets.value_objects import RefusalCode
from pfp.domain.mssn_research.shared_kernel.value_objects import Rational, StageLevel


class TestGrammarValueObjects(unittest.TestCase):
    def test_alphabet_exact_type_equality_and_scoping(self):
        a1 = Alphabet.level_1()
        a2 = Alphabet.level_1()
        a3 = Alphabet.level_2_plus(StageLevel(2))

        self.assertEqual(a1, a2)
        self.assertNotEqual(a1, a3)
        self.assertFalse(a1 == frozenset("01"))

        # Level 1 admits only 0 and 1
        self.assertTrue(a1.contains("0"))
        self.assertTrue(a1.contains("1"))
        self.assertFalse(a1.contains("2"))
        self.assertFalse(a1.contains("a"))

        # Level 2 admits 0..9 and a..z
        self.assertTrue(a3.contains("2"))
        self.assertTrue(a3.contains("z"))
        self.assertFalse(a3.contains("_"))

    def test_quantifier_mask_depth_computation(self):
        qm1 = QuantifierMask("0")       # 1 block, depth = 1
        qm2 = QuantifierMask("010")     # 3 alternations, depth = 3
        qm3 = QuantifierMask("0011")    # 2 blocks, depth = 2

        self.assertEqual(qm1.alternation_depth, 1)
        self.assertEqual(qm2.alternation_depth, 3)
        self.assertEqual(qm3.alternation_depth, 2)
        self.assertFalse(qm1 == "0")

    def test_probability_mass_bounds(self):
        pm_zero = ProbabilityMass.zero()
        pm_half = ProbabilityMass(Rational(1, 2))
        pm_one = ProbabilityMass.one()

        self.assertTrue(pm_zero.is_zero())
        self.assertFalse(pm_half.is_zero())
        self.assertTrue(pm_one.is_one())

        with self.assertRaises(ValueError):
            ProbabilityMass(Rational(3, 2))  # Mass > 1


class TestTokenFrontierEntity(unittest.TestCase):
    def test_valid_three_candidate_frontier(self):
        # Matches 1_packets.md test vector (support_width: 3, retained_mass: 1/2)
        c1 = FrontierCandidate(
            token_id=1042,
            emitted_bytes=b"SELECT",
            parser_state_after=ParserStateId("state/21"),
            base_probability=Rational(31, 100),
            constrained_probability=Rational(31, 50),
        )
        c2 = FrontierCandidate(
            token_id=1043,
            emitted_bytes=b"FROM",
            parser_state_after=ParserStateId("state/22"),
            base_probability=Rational(15, 100),
            constrained_probability=Rational(15, 50),
        )
        c3 = FrontierCandidate(
            token_id=1044,
            emitted_bytes=b"WHERE",
            parser_state_after=ParserStateId("state/23"),
            base_probability=Rational(4, 100),
            constrained_probability=Rational(4, 50),
        )

        res = TokenFrontier.create(
            vocabulary_size=32000,
            candidates=[c1, c2, c3],
            retained_mass=ProbabilityMass(Rational(1, 2)),
        )
        self.assertTrue(res.is_ok())
        frontier = res.unwrap()
        self.assertEqual(frontier.support_width, 3)
        self.assertEqual(frontier.masked_token_count, 31997)

    def test_zero_retained_mass_refusal(self):
        # Zero retained mass must emit Refusal, never smooth or unwrap
        res = TokenFrontier.create(
            vocabulary_size=32000,
            candidates=[],
            retained_mass=ProbabilityMass.zero(),
        )
        self.assertTrue(res.is_err())
        err = res.error if hasattr(res, "error") else res.refusal
        self.assertEqual(err.code, RefusalCode.ZERO_RETAINED_MASS)


class TestTowerGrammarAggregateRoot(unittest.TestCase):
    def test_level_1_grammar_validation(self):
        g1 = TowerGrammar.for_stage(StageLevel(1))

        # Admissible atoms under Level 1
        self.assertTrue(g1.validate_atom_characters("0").is_ok())
        self.assertTrue(g1.validate_atom_characters("101").is_ok())

        # Inactive symbol '2' triggers Refusal
        res = g1.validate_atom_characters("102")
        self.assertTrue(res.is_err())

    def test_level_1_wire_compilation(self):
        g1 = TowerGrammar.for_stage(StageLevel(1))

        # Up-Lift is admissible at Level 1
        res = g1.parse_packet("op<<0><><0><1>>")
        self.assertTrue(res.is_ok())
        pkt = res.unwrap()
        self.assertEqual(pkt.arity(), 3)

        # Level 2 Edge op<<10>...> is refused by Level 1 grammar
        edge_res = g1.parse_packet("op<<10><0><1>>")
        self.assertTrue(edge_res.is_err())

    def test_round_trip_invariant(self):
        g2 = TowerGrammar.for_stage(StageLevel(2))
        res = g2.parse_packet("op<<10><0><1>>")
        self.assertTrue(res.is_ok())
        pkt = res.unwrap()
        rt_res = check_wire_round_trip(pkt)
        self.assertTrue(rt_res.is_ok())


if __name__ == "__main__":
    unittest.main()
