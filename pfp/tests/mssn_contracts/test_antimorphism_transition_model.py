"""Targeted verification tests for Antimorphism Transition Model, Reversal Maps,
and Protected Distinction Invariants under Domain-Driven Design (DDD).

Enforces:
1. Involution Law: ((e)^dag)^dag == e for all reversible transitions.
2. Contravariant Composition: (e1 . e2)^dag == e2^dag . e1^dag in reversed order.
3. Conservative Retraction across Lift and Down Map: d_n o u_n == id.
4. Fail-Stop Refusal on Protected Distinction Erasure (Zero Data-Loss Invariant).
5. Exact-Type Value Object & Entity Equality (RULE_VO_EXACT_TYPE_EQUALITY_001).
"""

from __future__ import annotations

import os
import sys
import unittest

# Ensure research directory is in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_RESEARCH_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))
if _RESEARCH_DIR not in sys.path:
    sys.path.insert(0, _RESEARCH_DIR)

from omega_engine_pfp.domain.mssn_research.grammar.entities import (
    AntimorphismTransitionModel,
    DownMapQuarantineRequest,
    EpistemicQuarantineLedger,
    QuarantinedObstruction,
)
from omega_engine_pfp.domain.mssn_research.grammar.errors import ScopeBoundaryViolationError
from omega_engine_pfp.domain.mssn_research.grammar.exact_structures import (
    DownMapObstruction,
    EdgeInvolution,
    PontryaginKillFlags,
    ProtectedDistinction,
    QuarantinedShadowPacket,
    ReversalMap,
)
from omega_engine_pfp.domain.mssn_research.grammar.foundational_policies import (
    check_permanent_quarantine_isolation,
)
from omega_engine_pfp.domain.mssn_research.packets.value_objects import RefusalCode
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel


class TestAntimorphismTransitionModel(unittest.TestCase):
    """Test suite evaluating antimorphic reversal, composition, lift/down-map, and obstruction barriers."""

    def setUp(self) -> None:
        self.stage8 = StageLevel(8)
        self.stage9 = StageLevel(9)

        # Standard 3-state reversible transition triangle
        # a -(e1)-> b -(e2)-> c -(e3)-> a
        self.inv_e1 = EdgeInvolution(source_edge="a->b", reversed_edge="b->a")
        self.inv_e1_rev = EdgeInvolution(source_edge="b->a", reversed_edge="a->b")
        self.inv_e2 = EdgeInvolution(source_edge="b->c", reversed_edge="c->b")
        self.inv_e2_rev = EdgeInvolution(source_edge="c->b", reversed_edge="b->c")
        self.inv_e3 = EdgeInvolution(source_edge="c->a", reversed_edge="a->c")
        self.inv_e3_rev = EdgeInvolution(source_edge="a->c", reversed_edge="c->a")

        self.reversal_map_clean = ReversalMap((
            self.inv_e1, self.inv_e1_rev,
            self.inv_e2, self.inv_e2_rev,
            self.inv_e3, self.inv_e3_rev,
        ))

        self.distinction_parity = ProtectedDistinction(
            state_a="sector_plus",
            state_b="sector_minus",
            label="fermion_sign_parity",
        )

        self.model8 = AntimorphismTransitionModel(
            model_id="model/triangle_parity",
            stage_level=self.stage8,
            states=frozenset({"a", "b", "c", "sector_plus", "sector_minus"}),
            edges=frozenset({"a->b", "b->a", "b->c", "c->b", "c->a", "a->c"}),
            reversal_map=self.reversal_map_clean,
            protected_distinctions=frozenset({self.distinction_parity}),
        )

    def test_involution_law_for_reversible_edges(self) -> None:
        """Verify the involution law ((e)^dag)^dag == e for all non-obstructed edges."""
        self.assertTrue(self.model8.satisfies_involution())
        for e in ("a->b", "b->c", "c->a"):
            rev1_res = self.model8.reverse_edge(e)
            self.assertTrue(rev1_res.is_ok())
            rev1 = rev1_res.unwrap()

            rev2_res = self.model8.reverse_edge(rev1)
            self.assertTrue(rev2_res.is_ok())
            rev2 = rev2_res.unwrap()

            self.assertEqual(rev2, e, f"Involution failed for edge {e}: ({e}^dag)^dag == {rev2}")

    def test_irreversible_edge_obstruction(self) -> None:
        """Verify that an edge mapped to <bot> reports as obstructed and returns a typed obstruction."""
        dissipative_inv = EdgeInvolution(source_edge="a->drain", reversed_edge="bot")
        self.assertTrue(dissipative_inv.is_obstructed())

        rmap_dissipative = ReversalMap((dissipative_inv,))
        model_diss = AntimorphismTransitionModel(
            model_id="model/dissipative",
            stage_level=self.stage8,
            states=frozenset({"a", "drain"}),
            edges=frozenset({"a->drain"}),
            reversal_map=rmap_dissipative,
            protected_distinctions=frozenset(),
        )

        res = model_diss.reverse_edge("a->drain")
        self.assertTrue(res.is_err())
        self.assertIsInstance(res.error, DownMapObstruction)
        self.assertIn("irreversible", res.error.message)

    def test_contravariant_composition_in_reversed_order(self) -> None:
        """Verify that path reversal satisfies (e1 . e2)^dag == e2^dag . e1^dag."""
        path = ["a->b", "b->c"]
        rev_res = self.model8.reverse_path(path)
        self.assertTrue(rev_res.is_ok())
        reversed_path = rev_res.unwrap()

        # Expected: ["c->b", "b->a"]
        self.assertEqual(reversed_path, ("c->b", "b->a"))

        # Three-step composition
        path3 = ["a->b", "b->c", "c->a"]
        rev3_res = self.model8.reverse_path(path3)
        self.assertTrue(rev3_res.is_ok())
        self.assertEqual(rev3_res.unwrap(), ("a->c", "c->b", "b->a"))

    def test_conservative_retraction_identity(self) -> None:
        """Verify conservative retraction d_n o u_n == id across a lift and down map."""
        # 1. Lift model from Stage 8 to Stage 9
        model9 = self.model8.lift(self.stage9)
        self.assertEqual(model9.stage_level, self.stage9)
        self.assertEqual(model9.states, self.model8.states)
        self.assertEqual(model9.edges, self.model8.edges)

        # 2. Retract back to Stage 8 via canonical identity projection
        identity_state_proj = {s: s for s in model9.states}
        identity_edge_proj = {e: e for e in model9.edges}
        down_res = model9.down_map(
            target_stage=self.stage8,
            state_projection=identity_state_proj,
            edge_projection=identity_edge_proj,
        )
        self.assertTrue(down_res.is_ok(), f"Retraction failed: {down_res}")
        retracted_model8 = down_res.unwrap()

        # 3. Exact equality assertion d_8(u_8(M_8)) == M_8
        self.assertEqual(retracted_model8, self.model8)

    def test_descent_refusal_when_erasing_protected_distinction(self) -> None:
        """Counterexample: down map that collapses protected sector_plus and sector_minus must fail-stop."""
        model9 = self.model8.lift(self.stage9)

        # Collapsing projection attempting to quotient sector_plus and sector_minus to sector_trivial
        illicit_projection = {
            "a": "a",
            "b": "b",
            "c": "c",
            "sector_plus": "sector_trivial",
            "sector_minus": "sector_trivial",  # Collapses protected distinction!
        }

        down_res = model9.down_map(
            target_stage=self.stage8,
            state_projection=illicit_projection,
        )

        self.assertTrue(down_res.is_err(), "Expected down map to refuse when erasing protected distinction")
        obstruction = down_res.error
        self.assertIsInstance(obstruction, DownMapObstruction)
        self.assertEqual(obstruction.source_stage, self.stage9)
        self.assertEqual(obstruction.target_stage, self.stage8)
        self.assertEqual(obstruction.collapsed_target_state, "sector_trivial")
        self.assertEqual(obstruction.obstructed_distinction, self.distinction_parity)
        self.assertIn("erases protected distinction", obstruction.message)

    def test_descent_succeeds_when_protected_distinction_preserved(self) -> None:
        """Down map that collapses un-protected peripheral states (b and c -> bc) succeeds."""
        model9 = self.model8.lift(self.stage9)

        valid_projection = {
            "a": "a",
            "b": "bc",
            "c": "bc",  # Collapses b and c (un-protected)
            "sector_plus": "sector_plus",
            "sector_minus": "sector_minus",  # Preserved!
        }
        edge_projection = {
            "a->b": "a->bc",
            "b->a": "bc->a",
            "b->c": "bc->bc",
            "c->b": "bc->bc",
            "c->a": "bc->a",
            "a->c": "a->bc",
        }

        down_res = model9.down_map(
            target_stage=self.stage8,
            state_projection=valid_projection,
            edge_projection=edge_projection,
        )

        self.assertTrue(down_res.is_ok(), f"Expected valid projection to succeed: {down_res}")
        contracted_model = down_res.unwrap()
        self.assertEqual(contracted_model.stage_level, self.stage8)
        self.assertIn("bc", contracted_model.states)
        self.assertIn(self.distinction_parity, contracted_model.protected_distinctions)

    def test_exact_type_equality_guards(self) -> None:
        """Verify exact-type equality guards across all antimorphism domain value objects."""
        # EdgeInvolution
        self.assertFalse(self.inv_e1 == ("a->b", "b->a"))
        self.assertFalse(self.inv_e1 == "a->b")

        # ProtectedDistinction
        pd1 = ProtectedDistinction("s1", "s2", "test")
        pd2 = ProtectedDistinction("s2", "s1", "test")  # Symmetric set equality
        self.assertEqual(pd1, pd2)
        self.assertFalse(pd1 == ("s1", "s2"))
        self.assertFalse(pd1 == frozenset({"s1", "s2"}))

        # Distinct states guard
        with self.assertRaises(ValueError):
            ProtectedDistinction("same", "same")

        # DownMapObstruction
        obs1 = DownMapObstruction(self.stage9, self.stage8, self.distinction_parity, "triv", "msg")
        obs2 = DownMapObstruction(self.stage9, self.stage8, self.distinction_parity, "triv", "msg")
        self.assertEqual(obs1, obs2)
        self.assertFalse(obs1 == "DownMapObstruction")

    def test_down_map_obstruction_to_quarantined_shadow_packet(self) -> None:
        """Verify that DownMapObstruction converts into a valid Stage 10 QuarantinedShadowPacket."""
        obs = DownMapObstruction(
            source_stage=self.stage9,
            target_stage=self.stage8,
            obstructed_distinction=self.distinction_parity,
            collapsed_target_state="sector_trivial",
            message="Erased parity distinction",
        )
        shadow_pkt = obs.to_quarantined_shadow_packet(target_theorem="parity_obstruction_S9_to_S8")

        self.assertIsInstance(shadow_pkt, QuarantinedShadowPacket)
        self.assertEqual(shadow_pkt.target_theorem, "parity_obstruction_S9_to_S8")
        self.assertEqual(shadow_pkt.assertion_flags, PontryaginKillFlags())
        self.assertTrue(shadow_pkt.fence_audit.quarantine_verdict)
        self.assertTrue(shadow_pkt.is_permanent_quarantine)
        self.assertFalse(shadow_pkt.can_promote_to_core())
        self.assertEqual(shadow_pkt.shadow_type, "antimorphic_down_map_obstruction")
        self.assertEqual(shadow_pkt.evidence_bound, "S9->S8")
        self.assertTrue(any("sector_plus" in line for line in shadow_pkt.raw_transcript))
        self.assertTrue(any("sector_trivial" in line for line in shadow_pkt.raw_transcript))

    def test_epistemic_quarantine_ledger_lifecycle(self) -> None:
        """Verify append-only EpistemicQuarantineLedger lifecycle at Stage 10."""
        ledger = EpistemicQuarantineLedger(ledger_id="ledger/test_quarantine")
        self.assertEqual(ledger.entry_count, 0)
        self.assertEqual(ledger.stage_level, StageLevel(10))

        obs = DownMapObstruction(
            source_stage=self.stage9,
            target_stage=self.stage8,
            obstructed_distinction=self.distinction_parity,
            collapsed_target_state="sector_trivial",
            message="Erased parity distinction",
        )
        updated_ledger, shadow_pkt = ledger.commit_obstruction(obs, target_theorem="thm_parity_collapse")
        self.assertEqual(updated_ledger.entry_count, 1)
        self.assertEqual(updated_ledger.entries[0], shadow_pkt)
        self.assertEqual(updated_ledger.find_by_theorem("thm_parity_collapse"), shadow_pkt)
        self.assertIsNone(updated_ledger.find_by_theorem("nonexistent"))

        # Stage floor enforcement: EpistemicQuarantineLedger requires Stage 10+
        with self.assertRaises(ValueError):
            EpistemicQuarantineLedger(ledger_id="bad_stage", stage_level=StageLevel(9))

        # Rejects non-QuarantinedShadowPacket
        with self.assertRaises(TypeError):
            ledger.commit("not_a_packet")  # type: ignore

    def test_antimorphism_down_map_with_quarantine_integration(self) -> None:
        """Verify that down_map_with_quarantine automatically commits obstructions to Stage 10 ledger."""
        model9 = self.model8.lift(self.stage9)
        illicit_projection = {
            "a": "a",
            "b": "b",
            "c": "c",
            "sector_plus": "sector_trivial",
            "sector_minus": "sector_trivial",
        }

        res = model9.down_map_with_quarantine(DownMapQuarantineRequest(
            target_stage=self.stage8,
            state_projection=illicit_projection,
            target_theorem="thm_down_map_parity_obstruction",
        ))

        self.assertTrue(res.is_err(), "Expected projection with collapsed distinction to return Err")
        quarantined_obs = res.error
        self.assertIsInstance(quarantined_obs, QuarantinedObstruction)
        self.assertIsInstance(quarantined_obs.obstruction, DownMapObstruction)
        self.assertIsInstance(quarantined_obs.packet, QuarantinedShadowPacket)
        self.assertIsInstance(quarantined_obs.ledger, EpistemicQuarantineLedger)

        self.assertEqual(quarantined_obs.packet.target_theorem, "thm_down_map_parity_obstruction")
        self.assertEqual(quarantined_obs.ledger.entry_count, 1)
        self.assertEqual(quarantined_obs.ledger.entries[0], quarantined_obs.packet)
        self.assertEqual(quarantined_obs.obstruction.collapsed_target_state, "sector_trivial")

    def test_permanent_quarantine_fw_scope_isolation(self) -> None:
        """Verify Permanent Quarantine Law (Invariant 11): quarantined shadow packets cannot enter core stages <= 9."""
        model9 = self.model8.lift(self.stage9)
        illicit_projection = {
            "a": "a",
            "b": "b",
            "c": "c",
            "sector_plus": "sector_trivial",
            "sector_minus": "sector_trivial",
        }
        res = model9.down_map_with_quarantine(DownMapQuarantineRequest(
            target_stage=self.stage8,
            state_projection=illicit_projection,
            target_theorem="thm_isolated_obstruction",
        ))
        self.assertTrue(res.is_err())
        shadow_pkt = res.error.packet
        ledger = res.error.ledger

        # 1. Direct packet isolation check against core stages <= 9 raises FW-SCOPE
        for core_stage in range(10):
            check_res = check_permanent_quarantine_isolation(shadow_pkt, target_stage=StageLevel(core_stage))
            self.assertTrue(check_res.is_refusal())
            self.assertIsInstance(check_res.refusal, ScopeBoundaryViolationError)
            self.assertEqual(check_res.refusal.code, RefusalCode.NONCONSERVATIVE_LIFT)
            self.assertIn("FW-SCOPE", check_res.refusal.message)
            self.assertIn("Permanent Quarantine Law violation", check_res.refusal.message)

        # 2. Ledger isolation check against core stage 8 raises FW-SCOPE
        ledger_check = ledger.verify_isolation_against_stage(self.stage8)
        self.assertTrue(ledger_check.is_refusal())
        self.assertIsInstance(ledger_check.refusal, ScopeBoundaryViolationError)

        # 3. Isolation check against Stage 10 (epistemic quarantine domain) passes
        stage10_check = check_permanent_quarantine_isolation(shadow_pkt, target_stage=StageLevel(10))
        self.assertTrue(stage10_check.is_ok())
        self.assertTrue(stage10_check.unwrap())

        ledger_s10_check = ledger.verify_isolation_against_stage(StageLevel(10))
        self.assertTrue(ledger_s10_check.is_ok())
        self.assertTrue(ledger_s10_check.unwrap())

    def test_down_map_with_quarantine_success_preserves_model(self) -> None:
        """Verify that down_map_with_quarantine returns Ok(contracted_model) when distinctions are preserved."""
        model9 = self.model8.lift(self.stage9)
        identity_state_proj = {s: s for s in model9.states}
        identity_edge_proj = {e: e for e in model9.edges}

        res = model9.down_map_with_quarantine(DownMapQuarantineRequest(
            target_stage=self.stage8,
            state_projection=identity_state_proj,
            edge_projection=identity_edge_proj,
        ))
        self.assertTrue(res.is_ok())
        contracted_model = res.unwrap()
        self.assertEqual(contracted_model, self.model8)

    def test_quarantined_obstruction_and_ledger_exact_type_equality(self) -> None:
        """Verify exact-type equality guards on QuarantinedObstruction and EpistemicQuarantineLedger."""
        ledger1 = EpistemicQuarantineLedger(ledger_id="ledger/test")
        ledger2 = EpistemicQuarantineLedger(ledger_id="ledger/test")
        self.assertEqual(ledger1, ledger2)
        self.assertFalse(ledger1 == "ledger/test")
        self.assertFalse(ledger1 == {"ledger_id": "ledger/test"})

        obs = DownMapObstruction(self.stage9, self.stage8, self.distinction_parity, "triv", "msg")
        shadow_pkt = obs.to_quarantined_shadow_packet("thm_test")
        l_updated = ledger1.commit(shadow_pkt)

        qo1 = QuarantinedObstruction(obs, shadow_pkt, l_updated)
        qo2 = QuarantinedObstruction(obs, shadow_pkt, l_updated)
        self.assertEqual(qo1, qo2)
        self.assertFalse(qo1 == (obs, shadow_pkt, l_updated))
        self.assertFalse(qo1 == obs)


if __name__ == "__main__":
    unittest.main()
