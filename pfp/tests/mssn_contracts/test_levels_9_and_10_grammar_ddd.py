"""Targeted verification test suite for Level 9 Dagger Categories / Adjoint Involution
and Level 10 Epistemic Quarantine Adapter Firewall under Domain-Driven Design (DDD).

Enforces:
- Exact-Type Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Clean Architecture Inward Dependencies
- Railway-Oriented Programming (Result Monad)
- Claim Discipline & Scoped Verification
"""

from __future__ import annotations

import os
import sys
import unittest

# Ensure ddd package is importable without collisions
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_RESEARCH_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))
if _RESEARCH_DIR not in sys.path:
    sys.path.insert(0, _RESEARCH_DIR)

from pfp.domain.mssn_research.grammar.entities import TowerGrammar
from pfp.domain.mssn_research.grammar.errors import (
    DaggerInvolutionError,
    QuarantineViolationError,
    ScopeBoundaryViolationError,
)
from pfp.domain.mssn_research.grammar.foundational_policies import (
    check_dagger_involution_law,
    check_dagger_trace_invariance,
    check_permanent_quarantine_isolation,
    check_pontryagin_firewall,
)
from pfp.domain.mssn_research.grammar.exact_structures import (
    DaggerProfunctor,
    EdgeInvolution,
    HostFenceAudit,
    PontryaginKillFlags,
    QuarantinedShadowPacket,
    ReversalMap,
    TraceInvarianceDisposition,
)
from pfp.domain.mssn_research.packets.entities import Packet
from pfp.domain.mssn_research.packets.value_objects import Opcode, RefusalCode
from pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal
from pfp.domain.mssn_research.shared_kernel.value_objects import Rational, StageLevel


class TestLevel9DaggerCategoriesAndInvolution(unittest.TestCase):
    """Level 9: Dagger monads, profunctor reversals, and adjoint involution checks."""

    def setUp(self) -> None:
        self.stage = StageLevel(9)
        self.grammar = TowerGrammar.for_stage(self.stage)

    def test_dagger_opcode_stage_floor(self) -> None:
        op20 = Opcode.from_int(20)  # binary 10100
        self.assertEqual(op20.binary_str, "10100")
        self.assertEqual(op20.stage_floor, StageLevel(9))

        # Parsing Level 9 opcode at Stage 8 must be refused
        g8 = TowerGrammar.for_stage(StageLevel(8))
        res8 = g8.parse_packet("op<<10100><1>op<<0>>op<<10><0><0>>op<<11><0><0>>>")
        self.assertTrue(res8.is_refusal(), "Expected stage floor refusal at stage 8")

    def test_valid_dagger_packet_parsing_at_stage_9(self) -> None:
        # Valid wire with binary opcodes (<10> for 2, <11> for 3):
        # op<<10100><1>op<<0>op<<1><0><1>>op<<1><1><0>>>op<<10><10><1>>op<<11><10><1>>>
        wire = "op<<10100><1>op<<0>op<<1><0><1>>op<<1><1><0>>>op<<10><10><1>>op<<11><10><1>>>"
        res = self.grammar.parse_packet(wire)
        self.assertTrue(res.is_ok(), f"Failed parsing valid dagger packet: {res}")
        pkt = res.unwrap()
        self.assertEqual(pkt.wire.raw, wire)
        self.assertEqual(pkt.opcode(), Opcode("10100"))

    def test_edge_involution_value_object_exact_type_equality(self) -> None:
        e1 = EdgeInvolution(source_edge="0->1", reversed_edge="1->0")
        e2 = EdgeInvolution(source_edge="0->1", reversed_edge="1->0")
        self.assertEqual(e1, e2)
        self.assertFalse(e1 == ("0->1", "1->0"))

    def test_involution_law_satisfaction(self) -> None:
        # Symmetric reversal map: (0->1) <-> (1->0), (1->2) <-> (2->1)
        r_map = ReversalMap((
            EdgeInvolution("0->1", "1->0"),
            EdgeInvolution("1->0", "0->1"),
            EdgeInvolution("1->2", "2->1"),
            EdgeInvolution("2->1", "1->2"),
        ))
        res = check_dagger_involution_law(r_map)
        self.assertTrue(res.is_ok())

    def test_involution_law_violation_rejection(self) -> None:
        # Asymmetric 3-cycle: (0->1) -> (1->2), but (1->2) -> (2->0) != (0->1)
        r_map_bad = ReversalMap((
            EdgeInvolution("0->1", "1->2"),
            EdgeInvolution("1->2", "2->0"),
            EdgeInvolution("2->0", "0->1"),
        ))
        res = check_dagger_involution_law(r_map_bad)
        self.assertTrue(res.is_refusal(), "Expected refusal on involution law violation")
        self.assertIsInstance(res.refusal, DaggerInvolutionError)
        self.assertIn("involution law violation", res.refusal.message)

    def test_obstructed_missing_reverse_edge_rule(self) -> None:
        # Missing reverse edge assigned 'bot' (zero support) does not break involution
        r_map_bot = ReversalMap((
            EdgeInvolution("0->1", "1->0"),
            EdgeInvolution("1->0", "0->1"),
            EdgeInvolution("0->2", "bot"),
        ))
        res = check_dagger_involution_law(r_map_bot)
        self.assertTrue(res.is_ok(), "Obstructed missing edge should pass involution check")

    def test_trace_invariance_verification_and_claim_discipline(self) -> None:
        # Case 1: Independently confirmed invariance
        t_claimed = Rational(5, 1)
        t_computed = Rational(5, 1)
        res_ok = check_dagger_trace_invariance(t_claimed, t_computed, asserted_invariance=True)
        self.assertTrue(res_ok.is_ok())
        self.assertEqual(res_ok.unwrap(), TraceInvarianceDisposition.INVARIANT_VERIFIED)

        # Case 2: Candidate falsely asserts invariance (<1>) on asymmetric trace
        t_asym_comp = Rational(3, 1)
        res_fail = check_dagger_trace_invariance(t_claimed, t_asym_comp, asserted_invariance=True)
        self.assertTrue(res_fail.is_refusal(), "Expected refusal on false invariance assertion")
        self.assertIsInstance(res_fail.refusal, DaggerInvolutionError)
        self.assertIn("claimed trace invariance", res_fail.refusal.message)

        # Case 3: Honest declaration of asymmetry (<0>) emits ASYMMETRIC receipt without refusal
        res_honest = check_dagger_trace_invariance(t_claimed, t_asym_comp, asserted_invariance=False)
        self.assertTrue(res_honest.is_ok())
        self.assertEqual(res_honest.unwrap(), TraceInvarianceDisposition.ASYMMETRIC)


class TestLevel10QuarantineAdapterFirewall(unittest.TestCase):
    """Level 10: Pontryagin boundary kill flags, epistemic quarantine, and zero scope leakage."""

    def setUp(self) -> None:
        self.stage = StageLevel(10)
        self.grammar = TowerGrammar.for_stage(self.stage)

    def test_quarantine_opcode_stage_floor(self) -> None:
        op21 = Opcode.from_int(21)  # binary 10101
        self.assertEqual(op21.binary_str, "10101")
        self.assertEqual(op21.stage_floor, StageLevel(10))

        # Parsing Level 10 opcode at Stage 9 must be refused
        g9 = TowerGrammar.for_stage(StageLevel(9))
        res9 = g9.parse_packet("op<<10101><1>op<<0><0><0><0><0>>op<<1><1><1><1><1><1>>op<<10><0><0><0>>>")
        self.assertTrue(res9.is_refusal(), "Expected stage floor refusal at stage 9")

    def test_valid_quarantined_packet_parsing_at_stage_10(self) -> None:
        # Valid wire with binary opcodes (<10> for body opcode 2):
        # op<<10101><100>op<<0><0><0><0><0>>op<<1><1><1><1><1><1>>op<<10><1><10><1><10><11>>>
        wire = "op<<10101><100>op<<0><0><0><0><0>>op<<1><1><1><1><1><1>>op<<10><1><10><1><10><11>>>"
        res = self.grammar.parse_packet(wire)
        self.assertTrue(res.is_ok(), f"Failed parsing valid quarantine packet: {res}")
        pkt = res.unwrap()
        self.assertEqual(pkt.wire.raw, wire)
        self.assertEqual(pkt.opcode(), Opcode("10101"))

    def test_pontryagin_kill_flag_pi_rejection(self) -> None:
        # Breach 1: PI_FROM_EXACT_Q
        flags = PontryaginKillFlags(flag_pi=True)
        res = check_pontryagin_firewall(flags)
        self.assertTrue(res.is_refusal(), "Expected refusal on PI_FROM_EXACT_Q breach")
        self.assertIsInstance(res.refusal, QuarantineViolationError)
        self.assertIn("PI_FROM_EXACT_Q", res.refusal.message)

    def test_pontryagin_kill_flag_u1_rejection(self) -> None:
        # Breach 2: U1_FROM_L1_MASS_ALONE
        flags = PontryaginKillFlags(flag_u1=True)
        res = check_pontryagin_firewall(flags)
        self.assertTrue(res.is_refusal(), "Expected refusal on U1_FROM_L1_MASS_ALONE breach")
        self.assertIn("U1_FROM_L1_MASS_ALONE", res.refusal.message)

    def test_pontryagin_kill_flag_zn_rejection(self) -> None:
        # Breach 3: ZN_SOLD_AS_FREE_U1_WITHOUT_UNBOUNDED_DECL
        flags = PontryaginKillFlags(flag_zn=True)
        res = check_pontryagin_firewall(flags)
        self.assertTrue(res.is_refusal(), "Expected refusal on ZN_SOLD_AS_FREE_U1 breach")
        self.assertIn("ZN_SOLD_AS_FREE_U1_WITHOUT_UNBOUNDED_DECL", res.refusal.message)

    def test_pontryagin_kill_flag_alpha_rejection(self) -> None:
        # Breach 4: ALPHA_AS_CERTIFIED_EXACT
        flags = PontryaginKillFlags(flag_alpha=True)
        res = check_pontryagin_firewall(flags)
        self.assertTrue(res.is_refusal(), "Expected refusal on ALPHA_AS_CERTIFIED_EXACT breach")
        self.assertIn("ALPHA_AS_CERTIFIED_EXACT", res.refusal.message)

    def test_clean_quarantine_fence_audit_passing(self) -> None:
        # All flags False (no illicit continuum promotion asserted)
        clean_flags = PontryaginKillFlags(flag_pi=False, flag_u1=False, flag_zn=False, flag_alpha=False)
        res = check_pontryagin_firewall(clean_flags)
        self.assertTrue(res.is_ok(), f"Clean flags should pass audit: {res}")
        audit = res.unwrap()
        self.assertTrue(audit.check_pi)
        self.assertTrue(audit.check_u1)
        self.assertTrue(audit.check_zn)
        self.assertTrue(audit.check_alpha)
        self.assertTrue(audit.quarantine_verdict)

    def test_permanent_quarantine_law_and_fw_scope_enforcement(self) -> None:
        """Even when clean, a quarantined packet can NEVER be promoted to core stages 0-9."""
        clean_flags = PontryaginKillFlags()
        audit = HostFenceAudit.evaluate(clean_flags)
        self.assertTrue(audit.quarantine_verdict)

        shadow_pkt = QuarantinedShadowPacket(
            target_theorem="spectral_shadow_thm",
            assertion_flags=clean_flags,
            fence_audit=audit,
            shadow_type="zeta_shadow",
            evidence_bound="bounded_k_10",
            raw_transcript=("token_1", "token_2"),
        )
        self.assertTrue(shadow_pkt.is_permanent_quarantine)
        self.assertFalse(shadow_pkt.can_promote_to_core())

        # Attempt to import into Level 8 core stage must raise FW-SCOPE refusal
        res_import_8 = check_permanent_quarantine_isolation(shadow_pkt, target_stage=StageLevel(8))
        self.assertTrue(res_import_8.is_refusal(), "Expected FW-SCOPE refusal when importing into Level 8")
        self.assertIsInstance(res_import_8.refusal, ScopeBoundaryViolationError)
        self.assertIn("Permanent Quarantine Law violation", res_import_8.refusal.message)
        self.assertIn("FW-SCOPE", res_import_8.refusal.message)

        # Attempt to import into Level 9 core stage must also raise FW-SCOPE refusal
        res_import_9 = check_permanent_quarantine_isolation(shadow_pkt, target_stage=StageLevel(9))
        self.assertTrue(res_import_9.is_refusal(), "Expected FW-SCOPE refusal when importing into Level 9")

        # Isolation preserved at Level 10
        res_ok_10 = check_permanent_quarantine_isolation(shadow_pkt, target_stage=StageLevel(10))
        self.assertTrue(res_ok_10.is_ok())

    def test_exact_type_equality_on_quarantine_value_objects(self) -> None:
        flags1 = PontryaginKillFlags()
        flags2 = PontryaginKillFlags()
        self.assertEqual(flags1, flags2)
        self.assertFalse(flags1 == {"pi": False})

        audit1 = HostFenceAudit.evaluate(flags1)
        audit2 = HostFenceAudit.evaluate(flags2)
        self.assertEqual(audit1, audit2)
        self.assertFalse(audit1 == True)


if __name__ == "__main__":
    unittest.main()
