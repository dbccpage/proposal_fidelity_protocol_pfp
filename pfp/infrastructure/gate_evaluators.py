"""Concrete evaluators for the 13 Woland Tribunal Gates.

Implements PfpGateEvaluatorPort.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

from ..domain.contracts.gates import GateReceipt, GateSpec, GateVerdict
from ..domain.kernel.ports import PfpGateEvaluatorPort
from ..domain.kernel.result import RefusalCode

FORBIDDEN_HYPE_WORDS = (
    "proves",
    "guarantees",
    "mathematically verifies",
    "fundamentally",
    "true intelligence",
    "impossible",
    "universal",
    "flawless",
    "perfectly",
    "clearly",
    "obviously",
    "simply",
    "merely",
    "weaponized",
)

CONVERSATIONAL_FILLER = (
    "certainly!",
    "i would be happy to help",
    "as an ai language model",
    "sure thing",
    "of course!",
)


# Each gate reads caller-supplied attestations; it does not re-execute anything.
# Every attestation a gate reads is required. A missing or mistyped one fails
# the gate, so silence about a defect never counts as its absence.
REQUIRED_ATTESTATIONS: Dict[str, Dict[str, Tuple[type, ...]]] = {
    "HELLA": {"text": (str,), "is_admitted": (bool,)},
    "KOROVIEV": {"masks_contradiction": (bool,)},
    "BEGEMOT": {"is_trivial_fixpoint": (bool,)},
    "AZAZELLO": {"round_number": (int,)},
    "ABADONNA": {"nilpotency_verified": (bool,)},
    "MARGARITA": {"duality_gap": (int, Fraction), "requires_exact_zero": (bool,)},
    "MASTER": {"has_coerced_witness": (bool,)},
    "BEZDOMNY": {"unhealed_defect_count": (int,), "defect_budget": (int,)},
    "BENGALSKY": {"text": (str,)},
    "ANNUSHKA": {"fails_perturbation": (bool,)},
    "STRAVINSKY": {"regress_depth": (int,)},
    "PILATE": {"is_timid_refusal": (bool,)},
    "WOLAND": {"prior_failures_count": (int,)},
}


def _gate_key(gate_id: str) -> Optional[str]:
    return next((k for k in REQUIRED_ATTESTATIONS if k in gate_id), None)


def _missing_attestations(gate_key: str, state: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for field, kinds in REQUIRED_ATTESTATIONS[gate_key].items():
        value = state.get(field)
        # bool is a subclass of int; an int-typed attestation must not accept True/False.
        if field not in state:
            missing.append(field)
        elif type(value) is float:
            missing.append(f"{field} (float rejected: exact int or Fraction required)")
        elif type(value) not in kinds:
            missing.append(field)
    return missing


class WolandTribunalGateEvaluator(PfpGateEvaluatorPort):
    """Evaluates caller-supplied attestations against the 13 Woland Tribunal gates.

    A pass means every attestation the gate reads was present, well typed and
    acceptable. It does not mean the gate re-ran the underlying check.
    """

    def evaluate_gate(self, gate_spec: GateSpec, candidate_state: Dict[str, Any]) -> GateVerdict:
        gate_id = gate_spec.gate_id
        passed = True
        refusal_code: Optional[str] = None
        fences_violated: List[str] = []
        obs = "Attestations accepted; underlying check not re-executed."
        counter_route: Optional[str] = None

        gate_key = _gate_key(gate_id)
        missing = [] if gate_key is None else _missing_attestations(gate_key, candidate_state)
        if gate_key is None or missing:
            return GateVerdict(
                gate_id=gate_id,
                character=gate_spec.character,
                passed=False,
                refusal_code=RefusalCode.MISSING_ATTESTATION.value,
                observation=(
                    f"Unknown gate {gate_id}."
                    if gate_key is None
                    else f"Missing or mistyped attestations: {missing}."
                ),
                fences_violated=["Fail closed: a gate never passes on absent evidence."],
                counter_route="ROUTE_REFUSE",
                authority_effect="None",
            )

        # 01. Hella Cold Syntax Pre-Filter
        if "HELLA" in gate_id:
            raw_text = candidate_state["text"].lower()
            if any(filler in raw_text for filler in CONVERSATIONAL_FILLER):
                passed = False
                refusal_code = "POLICY_VIOLATION"
                fences_violated.append("Conversational filler detected.")
                obs = "Candidate contains conversational fluff or politeness."
            if not candidate_state["is_admitted"]:
                passed = False
                refusal_code = "UNADMITTED_PACKET"
                fences_violated.append("Prime 000: Unadmitted packets cannot be measured.")
                obs = "Candidate not admitted prior to measurement."

        # 02. Koroviev Nocebo Plunge
        elif "KOROVIEV" in gate_id:
            if candidate_state["masks_contradiction"]:
                passed = False
                refusal_code = "CONTRADICTION_MASKING"
                fences_violated.append("Detected contradiction masking or whitewashed defects.")
                obs = "Candidate attempted to suppress structural defects."

        # 03. Begemot 9-Dot Gauge Break
        elif "BEGEMOT" in gate_id:
            if candidate_state["is_trivial_fixpoint"]:
                passed = False
                refusal_code = "TRIVIAL_FIXPOINT"
                fences_violated.append("Trivial local fixpoint violates 9-dot gauge break requirement.")
                obs = "Zero entropy proposal without genuine structural difference."

        # 04. Azazello Scope Assassin
        elif "AZAZELLO" in gate_id:
            round_num = candidate_state["round_number"]
            if round_num > 10:
                passed = False
                refusal_code = "ROUND_CAP_EXCEEDED"
                fences_violated.append("Exceeded 10-round execution cap.")
                obs = f"Round {round_num} exceeds hard cap of 10."

        # 05. Abadonna Terminal Gaze (Nilpotency d^2 = 0)
        elif "ABADONNA" in gate_id:
            if not candidate_state["nilpotency_verified"]:
                passed = False
                refusal_code = "NILPOTENCY_BROKEN"
                fences_violated.append("Nilpotency d^2 = 0 broken; nonzero boundary square.")
                obs = "Nonzero boundary composition detected."

        # 06. Margarita Primal-Dual Balance
        elif "MARGARITA" in gate_id:
            duality_gap = candidate_state["duality_gap"]
            if duality_gap != 0 and candidate_state["requires_exact_zero"]:
                passed = False
                refusal_code = "DUALITY_GAP_NONZERO"
                fences_violated.append("Duality gap nonzero under exact zero requirement.")
                obs = f"Nonzero duality gap: {duality_gap}."

        # 07. The Master Manuscript Truth
        elif "MASTER" in gate_id:
            if candidate_state["has_coerced_witness"]:
                passed = False
                refusal_code = "WITNESS_COERCION"
                fences_violated.append("Witness values must be exact integers or rationals, not coerced.")
                obs = "Witness coercion detected."

        # 08. Bezdomny Scar Chronicler
        elif "BEZDOMNY" in gate_id:
            if candidate_state["unhealed_defect_count"] > candidate_state["defect_budget"]:
                passed = False
                refusal_code = "DEFECT_BUDGET_EXCEEDED"
                fences_violated.append("Unhealed defect count exceeds declared budget.")
                obs = "Scar chronicler recorded defect inflation."

        # 09. Bengalsky Anti-Hype
        elif "BENGALSKY" in gate_id:
            raw_text = candidate_state["text"].lower()
            found_hype = [w for w in FORBIDDEN_HYPE_WORDS if w in raw_text]
            if found_hype:
                passed = False
                refusal_code = "POLICY_VIOLATION"
                fences_violated.append(f"Forbidden hype verbs detected: {found_hype}")
                obs = f"Bengalsky severed claim: contains unearned hype {found_hype}."

        # 10. Annushka Oil Spill
        elif "ANNUSHKA" in gate_id:
            if candidate_state["fails_perturbation"]:
                passed = False
                refusal_code = "PERTURBATION_FAILURE"
                fences_violated.append("Failed under stochastic boundary perturbation.")
                obs = "Turnstile oil spill triggered instability."

        # 11. Stravinsky Epistemic Sanatorium
        elif "STRAVINSKY" in gate_id:
            if candidate_state["regress_depth"] > 12:
                passed = False
                refusal_code = "CARRIER_REGRESS"
                fences_violated.append("Alternation depth exceeds 12; unbounded regress.")
                obs = "Quarantine triggered for unbounded regress."

        # 12. Pilate Anti-Cowardice
        elif "PILATE" in gate_id:
            if candidate_state["is_timid_refusal"]:
                passed = False
                refusal_code = "COWARDICE_DETECTED"
                fences_violated.append("Timid non-assertion where constructive action is admissible.")
                obs = "Unearned refusal without witness obstruction."

        # 13. Woland Terminal Reality
        elif "WOLAND" in gate_id:
            if candidate_state["prior_failures_count"] > 0:
                passed = False
                refusal_code = "TRIBUNAL_BLOCKED"
                fences_violated.append("Candidate carries unaddressed tribunal gate failures.")
                obs = "Woland dissolved candidate: prior gate failures remain."
                counter_route = "ROUTE_REFUSE"
            else:
                obs = "All twelve attested gates passed; their checks were not re-executed here."

        return GateVerdict(
            gate_id=gate_id,
            character=gate_spec.character,
            passed=passed,
            refusal_code=refusal_code,
            observation=obs,
            fences_violated=fences_violated,
            counter_route=counter_route,
            authority_effect="None",
        )

    def evaluate_tribunal(self, candidate_id: str, candidate_state: Dict[str, Any]) -> GateReceipt:
        from .storage import PfpFileSystemStorageAdapter

        storage = PfpFileSystemStorageAdapter()
        specs = [s for s in storage.list_gate_specs() if _gate_key(s.gate_id) is not None]
        verdicts: List[GateVerdict] = []
        prior_fails = 0

        for spec in specs:
            state = dict(candidate_state)
            state["prior_failures_count"] = prior_fails
            verdict = self.evaluate_gate(spec, state)
            verdicts.append(verdict)
            if not verdict.passed:
                prior_fails += 1

        all_passed = all(v.passed for v in verdicts)
        status = "AttestedPass" if all_passed else "Refused"
        raw_receipt = {
            "candidate_id": candidate_id,
            "all_passed": all_passed,
            "status": status,
            "verdict_count": len(verdicts),
            "authority_effect": "None",
        }
        r_hash = hashlib.sha256(json.dumps(raw_receipt, sort_keys=True).encode("utf-8")).hexdigest()

        return GateReceipt(
            candidate_id=candidate_id,
            verdicts=verdicts,
            all_passed=all_passed,
            terminal_disposition=status,
            receipt_sha256=r_hash,
            authority_effect="None",
        )
