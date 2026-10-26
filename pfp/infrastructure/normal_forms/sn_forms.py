"""S(n) local-route evaluators. They ignore the route map.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any


def evaluate_sn_pdnf(
    fixture: dict[str, Any],
    route_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Witnessed irreflexive differences on a declared carrier."""
    del route_map
    carrier = fixture.get("carrier")
    if carrier is None or len(carrier) < 2:
        return {
            "local_terminal": "RequireCarrierDeclaration",
            "reason": "Carrier must be declared with at least two distinct elements.",
        }
    if not fixture.get("irreflexivity_declared", False):
        return {
            "local_terminal": "RequireIrreflexivityDeclaration",
            "reason": "Irreflexivity law must be declared before asserting differences.",
        }
    asserted = fixture.get("asserted_relation", [])
    witness_map = fixture.get("witness_map", {})
    for pair in asserted:
        x, y = pair[0], pair[1]
        if x == y:
            return {
                "local_terminal": "RejectSelfDifference",
                "reason": f"Term '{x}' asserted different from itself; violates irreflexivity.",
                "offending_pair": (x, y),
            }
    for pair in asserted:
        x, y = pair[0], pair[1]
        count = None
        keys = ((x, y), (y, x), f"{x},{y}", f"{y},{x}", f"({x}, {y})", f"({y}, {x})")
        for key in keys:
            if key in witness_map:
                count = witness_map[key]
                break
        if count is None or count <= 0:
            return {
                "local_terminal": "RejectUnwitnessedAssertion",
                "reason": f"Asserted difference ({x}, {y}) has no positive witness count.",
                "offending_pair": (x, y),
            }
    if not fixture.get("scope_declared", True):
        return {
            "local_terminal": "Undetermined",
            "reason": "Scope of search undeclared; minimality cannot be determined.",
        }
    return {
        "local_terminal": "AcceptWitnessedIrreflexive",
        "reason": "Asserted differences are witnessed and irreflexive on declared carrier.",
        "carrier_size": len(carrier),
        "asserted_pairs_count": len(asserted),
    }


def evaluate_sn_rpnf(
    fixture: dict[str, Any],
    route_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Certified regime fold along an admitted history."""
    del route_map
    if not fixture.get("history_declared", True) or fixture.get("history") is None:
        return {
            "local_terminal": "RequireHistoryDeclaration",
            "reason": "History declaration missing or external state dependence detected.",
        }
    history = fixture.get("history", [])
    if len(history) == 0 and not fixture.get("genesis_quiescent", True):
        return {
            "local_terminal": "Recompute",
            "reason": "Non-quiescent genesis produced nonempty regime without history; must recompute.",
        }
    presentation = fixture.get("presentation_only", False) or fixture.get(
        "presentation_without_admission", False
    )
    if presentation:
        return {
            "local_terminal": "RejectPresentationAsChange",
            "reason": "Datum presented without an admission event cannot alter state.",
        }
    target_regime = fixture.get("target_regime")
    recomputed_regime = fixture.get("recomputed_regime", target_regime)
    if not fixture.get("certified_fold", True) or target_regime != recomputed_regime:
        return {
            "local_terminal": "RejectUncertifiedRegime",
            "reason": "Regime assertion uncertified by historical fold.",
            "target_regime": target_regime,
            "recomputed_regime": recomputed_regime,
        }
    return {
        "local_terminal": "AcceptCertifiedRegime",
        "reason": "Regime certified by deterministic fold along admitted history.",
        "history_length": len(history),
        "certified_regime": target_regime,
    }


def evaluate_sn_scnf(
    fixture: dict[str, Any],
    route_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Unique minimizer under a declared cost measure."""
    del route_map
    if not fixture.get("measure_declared", True) or not fixture.get("measure_name"):
        return {
            "local_terminal": "RejectUnmeasuredMinimum",
            "reason": "Cheapest separation asserted without declaring order or cost measure.",
        }
    ambiguous = fixture.get("isomorphism_undeclared", False) or fixture.get(
        "grammar_restatement_ambiguous", False
    )
    if ambiguous:
        return {
            "local_terminal": "RequireMeasureDeclaration",
            "reason": "Measure declaration ambiguous under grammar restatement; isomorphism undeclared.",
        }
    ratio = fixture.get("contraction_ratio")
    obstructed = fixture.get("obstruction_present", False) or (
        ratio is not None and float(ratio) >= 1.0
    )
    if obstructed:
        return {
            "local_terminal": "Escalate",
            "reason": f"Contraction ratio k={ratio} >= 1 or structural obstruction detected; escalated.",
        }
    tied = (
        fixture.get("tie_resolved_arbitrarily", False)
        or fixture.get("tied_candidates_count", 0) > 1
    )
    if tied:
        return {
            "local_terminal": "RecordTie",
            "reason": "Multiple minimizers achieve equal minimal cost; tie recorded.",
        }
    return {
        "local_terminal": "AcceptUniqueMinimizer",
        "reason": "Unique minimizer certified under declared measure.",
        "measure": fixture.get("measure_name"),
    }


def evaluate_sn_state(
    fixture: dict[str, Any],
    route_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Epistemic state: value, authority, cause, freshness, and confidence."""
    del route_map
    if fixture.get("malformed", False) or "value" not in fixture:
        return {
            "local_terminal": "Refuse",
            "reason": "Malformed epistemic state claim; missing value.",
        }
    authority = fixture.get("authority_source")
    if not authority or authority == "unknown":
        return {
            "local_terminal": "AuthorityUnknown",
            "reason": "State claim lacks explicit authority source.",
        }
    versioned = fixture.get("version") is not None and (
        fixture.get("causal_context") is None or fixture.get("has_causal_gap", False)
    )
    if versioned:
        return {
            "local_terminal": "CausalGap",
            "reason": "Version served without causal context; scalar state flattening detected.",
        }
    freshness = fixture.get("freshness")
    stale = fixture.get("is_stale", False) or (
        isinstance(freshness, dict) and freshness.get("is_stale", False)
    )
    if stale:
        return {
            "local_terminal": "Stale",
            "reason": "State claim freshness expired; labeled as stale.",
        }
    confidence = fixture.get("confidence")
    threshold = fixture.get("confidence_threshold", 0.8)
    if confidence is not None and confidence < threshold:
        return {
            "local_terminal": "ConfidenceBelowThreshold",
            "reason": f"State confidence {confidence} below threshold {threshold}.",
        }
    return {
        "local_terminal": "Accept",
        "reason": "Epistemic state carries complete value, version, causal context, freshness, and authority.",
        "authority_source": authority,
    }


def evaluate_sn_pvnf(
    fixture: dict[str, Any],
    route_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Provenance traced to source facts, or a typed refusal."""
    del route_map
    if fixture.get("refusal_requested", False) or "model_version" not in fixture:
        return {
            "local_terminal": "Refuse",
            "reason": "Untyped or uncertified provenance data product.",
        }
    source_facts = fixture.get("source_facts")
    if not source_facts or len(source_facts) == 0:
        return {
            "local_terminal": "AuthorityHallucinationViolation",
            "reason": "Generated answer carries no traceable source facts; authority hallucination.",
        }
    if fixture.get("has_lineage_break", False) or fixture.get("lineage_parent_ids") is None:
        return {
            "local_terminal": "LineageLost",
            "reason": "Lineage chain broken or parent references missing.",
        }
    non_replayable = fixture.get("non_replayable_steps")
    if non_replayable and len(non_replayable) > 0:
        return {
            "local_terminal": "NonReplayableFlagged",
            "reason": f"Non-replayable steps present ({len(non_replayable)} steps); flagged for escalation.",
            "non_replayable_count": len(non_replayable),
        }
    return {
        "local_terminal": "ProvenanceTraced",
        "reason": "Complete provenance chain traced to source facts with deterministic replayability.",
        "facts_count": len(source_facts),
    }
