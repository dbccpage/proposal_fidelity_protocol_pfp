"""Executable Demonstration of Level 11 Polygraph 2-Cell Term Rewriting and Peak Join Confluence.

Demonstrates:
1. Representation of higher-dimensional term rewriting using Polygraph packets.
2. Step continuity verification across sequences of rewrite steps.
3. Divergent peak joins: resolving divergence s <- u and s -> v to a common join term w.
4. Fail-closed refusal on discontinuous chains, non-confluent peaks, and mismatched join terms.
5. RFC 8785 canonical JSON execution receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pfp.domain.mssn_research.grammar.rewriting import (
    PeakClaim,
    PolygraphPacket,
    RewriteStep,
)
from pfp.domain.mssn_research.shared_kernel.value_objects import (
    ContentDigest,
    StageLevel,
)

# Setup research package imports
from pfp.domain.mssn_research.grammar.entities import (
    TowerGrammar,
)
from pfp.domain.mssn_research.grammar.errors import (
    PolygraphConfluenceError,
)
from pfp.domain.mssn_research.grammar.rewriting_policies import (
    check_peak_claim_confluence,
    check_step_continuity,
)
from pfp.domain.mssn_research.packets.value_objects import (
    RefusalCode,
)


def _canonical_json(data: Any) -> str:
    """Serialize data into RFC 8785 canonical JSON (sorted keys, compact whitespace)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _compute_sha256(data: str) -> str:
    """Compute SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def run_polygraph_confluence_demo(verbose: bool = True) -> dict[str, Any]:
    """Execute complete Level 11 polygraph 2-cell rewriting and peak join demo."""
    if verbose:
        print("=" * 70)
        print("DEMO: Level 11 Polygraphs & Confluent 2-Cell Rewriting")
        print("=" * 70)

    grammar11 = TowerGrammar.for_stage(StageLevel(11))
    ruleset_digest = ContentDigest("a" * 64)

    # -------------------------------------------------------------
    # Scenario 1: Valid Confluent Divergent Peak Join
    # -------------------------------------------------------------
    if verbose:
        print("\n[Scenario 1] Valid Confluent Divergent Peak Join")
        print("  Apex: term_s")
        print("  Left branch : term_s -> term_u -> term_w")
        print("  Right branch: term_s -> term_v -> term_w")
        print("  Join term   : term_w (confluent!)")

    step_s_u = RewriteStep("r_left_branch", "<0>", "term_s", "term_u")
    step_u_w = RewriteStep("r_left_join", "<0>", "term_u", "term_w")
    step_v_w = RewriteStep("r_right_join", "<1>", "term_v", "term_w")

    claim_valid = PeakClaim(
        peak_apex="term_s",
        target_left="term_u",
        target_right="term_v",
        left_path=(step_u_w,),
        right_path=(step_v_w,),
        join_term="term_w",
    )

    packet_valid = PolygraphPacket(
        presentation_id="confluent_system_v1",
        ruleset_digest=ruleset_digest,
        step_list=(step_s_u, step_u_w),
        peak_claim=claim_valid,
    )

    res_valid = grammar11.validate_polygraph(packet_valid)
    if not (res_valid.is_ok()):
        raise ValueError(f"Expected Ok, got {res_valid}")

    if verbose:
        print("  ==> VALIDATION: PASS (Admitted into Level 11 grammar)")

    # -------------------------------------------------------------
    # Scenario 2: Refused Discontinuous Reduction Sequence
    # -------------------------------------------------------------
    if verbose:
        print("\n[Scenario 2] Discontinuous Rewrite Sequence")
        print("  Step 1: term_s -> term_u")
        print("  Step 2: unrelated_term -> term_w (broken continuity)")

    broken_step = RewriteStep("r_broken", "<0>", "unrelated_term", "term_w")
    res_discont = check_step_continuity([step_s_u, broken_step])
    if not (res_discont.is_refusal()):
        raise ValueError('scenario invariant failed')
    if not (isinstance(res_discont.refusal, PolygraphConfluenceError)):
        raise ValueError('scenario invariant failed')

    if verbose:
        print(f"  ==> REFUSAL: {res_discont.refusal.code.name} - {res_discont.refusal.message}")

    # -------------------------------------------------------------
    # Scenario 3: Refused Non-Confluent Divergent Peak (Mismatched Ends)
    # -------------------------------------------------------------
    if verbose:
        print("\n[Scenario 3] Non-Confluent Divergent Peak")
        print("  Left path  ends at: term_w1")
        print("  Right path ends at: term_w2 != term_w1")

    step_left_mismatch = RewriteStep("r_left", "<0>", "term_u", "term_w1")
    step_right_mismatch = RewriteStep("r_right", "<1>", "term_v", "term_w2")

    claim_mismatch = PeakClaim(
        peak_apex="term_s",
        target_left="term_u",
        target_right="term_v",
        left_path=(step_left_mismatch,),
        right_path=(step_right_mismatch,),
        join_term="term_w1",
    )

    res_mismatch = check_peak_claim_confluence(claim_mismatch)
    if not (res_mismatch.is_refusal()):
        raise ValueError('scenario invariant failed')
    if not (isinstance(res_mismatch.refusal, PolygraphConfluenceError)):
        raise ValueError('scenario invariant failed')

    if verbose:
        print(f"  ==> REFUSAL: {res_mismatch.refusal.code.name} - {res_mismatch.refusal.message}")

    # -------------------------------------------------------------
    # Scenario 4: Stage Floor Enforcement (Level 10 Refusal)
    # -------------------------------------------------------------
    if verbose:
        print("\n[Scenario 4] Stage Floor Enforcement")
        print("  Attempting polygraph validation at Stage 10 (< Level 11)")

    grammar10 = TowerGrammar.for_stage(StageLevel(10))
    res_floor = grammar10.validate_polygraph(packet_valid)
    if not (res_floor.is_refusal()):
        raise ValueError('scenario invariant failed')
    if not (res_floor.refusal.code == RefusalCode.UNKNOWN_OPCODE):
        raise ValueError('scenario invariant failed')

    if verbose:
        print(f"  ==> REFUSAL: {res_floor.refusal.code.name} - {res_floor.refusal.message}")

    # -------------------------------------------------------------
    # Build and Return RFC 8785 Execution Receipt
    # -------------------------------------------------------------
    receipt_payload = {
        "schema": "receipt_polygraph_confluence_v1",
        "authority_effect": "None",
        "stage_floor": 11,
        "scenarios_evaluated": 4,
        "admitted_packets": 1,
        "refused_mutations": 3,
        "refusal_codes_observed": [
            res_discont.refusal.code.name,
            res_mismatch.refusal.code.name,
            res_floor.refusal.code.name,
        ],
        "status": "PASS",
    }
    canon_bytes = _canonical_json(receipt_payload)
    digest = _compute_sha256(canon_bytes)
    receipt_payload["receipt_sha256"] = digest

    if verbose:
        print("\n" + "=" * 70)
        print("RECEIPT DIGEST:", digest)
        print("DEMO STATUS: PASS")
        print("=" * 70)

    return receipt_payload
