"""Executable Demonstration of Antimorphic Reversal and Epistemic Quarantine.

Demonstrates:
1. Reversible transition models and the Involution Law:
       ((e)^dag)^dag == e
2. Contravariant path composition:
       (e1 . e2 . ... . ek)^dag == ek^dag . ... . e2^dag . e1^dag
3. Irreversible dissipative edges yielding typed DownMapObstruction.
4. Stage lift u_n and down-map d_n conservative retraction:
       d_n(u_n(x)) == x
5. Protected distinctions and fail-stop refusal on distinction erasure:
       Collapse(state_a, state_b) -> Refusal(DownMapObstruction)
6. Epistemic quarantine ledger isolation (Zero Data-Loss Invariant).
7. RFC 8785 canonical execution receipt.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pfp.domain.mssn_research.grammar.exact_structures import (
    DownMapObstruction,
    EdgeInvolution,
    ProtectedDistinction,
    ReversalMap,
)
from pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel
from pfp.domain.mssn_research.grammar.entities import (
    AntimorphismTransitionModel,
    EpistemicQuarantineLedger,
)


def _canonical_json(data: Any) -> str:
    """RFC 8785 canonical JSON serialization (sorted keys, compact whitespace)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_triangle_parity_model(stage: int = 8) -> AntimorphismTransitionModel:
    """Construct a canonical 3-state reversible triangle with fermion sign parity protection."""
    inv_e1 = EdgeInvolution(source_edge="a->b", reversed_edge="b->a")
    inv_e1_rev = EdgeInvolution(source_edge="b->a", reversed_edge="a->b")
    inv_e2 = EdgeInvolution(source_edge="b->c", reversed_edge="c->b")
    inv_e2_rev = EdgeInvolution(source_edge="c->b", reversed_edge="b->c")
    inv_e3 = EdgeInvolution(source_edge="c->a", reversed_edge="a->c")
    inv_e3_rev = EdgeInvolution(source_edge="a->c", reversed_edge="c->a")

    reversal_map = ReversalMap((
        inv_e1, inv_e1_rev,
        inv_e2, inv_e2_rev,
        inv_e3, inv_e3_rev,
    ))

    distinction_parity = ProtectedDistinction(
        state_a="sector_plus",
        state_b="sector_minus",
        label="fermion_sign_parity",
    )

    return AntimorphismTransitionModel(
        model_id="model/triangle_parity",
        stage_level=StageLevel(stage),
        states=frozenset({"a", "b", "c", "sector_plus", "sector_minus"}),
        edges=frozenset({"a->b", "b->a", "b->c", "c->b", "c->a", "a->c"}),
        reversal_map=reversal_map,
        protected_distinctions=frozenset({distinction_parity}),
    )


def run_antimorphism_scenarios() -> dict[str, Any]:
    """Execute six core scenarios demonstrating antimorphic reversal and quarantine."""
    results: dict[str, Any] = {
        "schema": "symbol_game.demo_antimorphic_reversal.v1",
        "scenarios": {},
    }

    model = build_triangle_parity_model(8)

    # ---------------------------------------------------------
    # Scenario 1: Involution Law ((e)^dag)^dag == e
    # ---------------------------------------------------------
    if not (model.satisfies_involution()):
        raise ValueError("Model must satisfy involution law")
    test_edge = "a->b"
    rev1 = model.reverse_edge(test_edge).unwrap()
    rev2 = model.reverse_edge(rev1).unwrap()
    if not (rev2 == test_edge):
        raise ValueError(f"Involution failed: {test_edge} -> {rev1} -> {rev2}")

    results["scenarios"]["scenario_1_involution_law"] = {
        "status": "PASS",
        "tested_edge": test_edge,
        "reversed_once": rev1,
        "reversed_twice": rev2,
        "involution_satisfied": True,
    }

    # ---------------------------------------------------------
    # Scenario 2: Contravariant Path Composition (e1 . e2)^dag == e2^dag . e1^dag
    # ---------------------------------------------------------
    forward_path = ["a->b", "b->c"]
    rev_path_res = model.reverse_path(forward_path)
    if not (rev_path_res.is_ok()):
        raise ValueError(f"Path reversal failed: {rev_path_res}")
    rev_path = rev_path_res.unwrap()
    # Expected: c->b, then b->a
    if not (rev_path == ("c->b", "b->a")):
        raise ValueError(f"Contravariance failed: {rev_path}")

    results["scenarios"]["scenario_2_contravariant_composition"] = {
        "status": "PASS",
        "forward_path": forward_path,
        "reversed_path": list(rev_path),
        "contravariant_order_verified": True,
    }

    # ---------------------------------------------------------
    # Scenario 3: Irreversible Dissipative Transition Obstruction
    # ---------------------------------------------------------
    dissipative_inv = EdgeInvolution(source_edge="a->drain", reversed_edge="bot")
    diss_model = AntimorphismTransitionModel(
        model_id="model/dissipative",
        stage_level=StageLevel(8),
        states=frozenset({"a", "drain"}),
        edges=frozenset({"a->drain"}),
        reversal_map=ReversalMap((dissipative_inv,)),
        protected_distinctions=frozenset(),
    )
    diss_res = diss_model.reverse_edge("a->drain")
    if not (diss_res.is_err()):
        raise ValueError("Expected DownMapObstruction for irreversible edge")
    err_diss = diss_res.error
    if not (isinstance(err_diss, DownMapObstruction)):
        raise ValueError('scenario invariant failed')

    results["scenarios"]["scenario_3_irreversible_dissipation"] = {
        "status": "PASS_OBSTRUCTED_TYPED",
        "edge": "a->drain",
        "target": err_diss.collapsed_target_state,
        "message": err_diss.message,
    }

    # ---------------------------------------------------------
    # Scenario 4: Retraction Across Lift and Down Map: d_n(u_n(x)) == x
    # ---------------------------------------------------------
    lifted_9 = model.lift(StageLevel(9))
    identity_proj = {s: s for s in model.states}
    down_mapped_res = lifted_9.down_map(StageLevel(8), identity_proj)
    if not (down_mapped_res.is_ok()):
        raise ValueError(f"Down-map failed: {down_mapped_res}")
    down_mapped = down_mapped_res.unwrap()
    if not (down_mapped.stage_level == StageLevel(8)):
        raise ValueError('scenario invariant failed')
    if not (down_mapped.states == model.states):
        raise ValueError('scenario invariant failed')
    if not (down_mapped.edges == model.edges):
        raise ValueError('scenario invariant failed')

    results["scenarios"]["scenario_4_retraction_lift_down"] = {
        "status": "PASS",
        "initial_stage": 8,
        "lifted_stage": 9,
        "retracted_stage": 8,
        "retraction_law_verified": True,
    }

    # ---------------------------------------------------------
    # Scenario 5: Protected Distinction Erasure Fail-Stop Refusal
    # ---------------------------------------------------------
    # Attempt to collapse sector_plus and sector_minus into 'sector_neutral'
    erasure_projection = {
        "a": "a", "b": "b", "c": "c",
        "sector_plus": "sector_neutral",
        "sector_minus": "sector_neutral",  # ERASURE ATTEMPT!
    }
    erasure_res = model.down_map(StageLevel(7), erasure_projection)
    if not (erasure_res.is_err()):
        raise ValueError("Erasure of protected distinction must fail")
    err_erasure = erasure_res.error
    if not (isinstance(err_erasure, DownMapObstruction)):
        raise ValueError('scenario invariant failed')
    if not (err_erasure.obstructed_distinction.label == "fermion_sign_parity"):
        raise ValueError('scenario invariant failed')

    results["scenarios"]["scenario_5_protected_distinction_refusal"] = {
        "status": "REFUSED_EXPECTED",
        "erasure_label": err_erasure.obstructed_distinction.label,
        "states_collapsed": [err_erasure.obstructed_distinction.state_a, err_erasure.obstructed_distinction.state_b],
        "refusal_message": err_erasure.message,
    }

    # ---------------------------------------------------------
    # Scenario 6: Epistemic Quarantine Ledger Isolation
    # ---------------------------------------------------------
    ledger = EpistemicQuarantineLedger(ledger_id="ledger/demo_antimorphism")
    updated_ledger, shadow_pkt = ledger.commit_obstruction(err_erasure, target_theorem="thm_parity_collapse")
    if not (updated_ledger.entry_count == 1):
        raise ValueError('scenario invariant failed')
    if not (updated_ledger.find_by_theorem("thm_parity_collapse") == shadow_pkt):
        raise ValueError('scenario invariant failed')
    if not (shadow_pkt.is_permanent_quarantine):
        raise ValueError('scenario invariant failed')
    if not (not shadow_pkt.can_promote_to_core()):
        raise ValueError('scenario invariant failed')

    results["scenarios"]["scenario_6_epistemic_quarantine"] = {
        "status": "PASS",
        "ledger_id": updated_ledger.ledger_id,
        "entry_count": updated_ledger.entry_count,
        "is_quarantined": True,
        "target_theorem": shadow_pkt.target_theorem,
        "quarantine_verdict": shadow_pkt.fence_audit.quarantine_verdict,
    }

    # Cryptographic Hash of the Entire Demo Receipt
    canonical_bytes = _canonical_json(results)
    results["receipt_sha256"] = _sha256(canonical_bytes)
    return results
