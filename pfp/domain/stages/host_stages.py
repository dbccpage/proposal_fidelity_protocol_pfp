"""Host stage rules of the staged PFP pipeline: admit, selection, receipt and hand-off.

Pure functions over earlier stage data. They compute a record from host facts; none reads a
model field as a verdict, and none authorizes anything. AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple

from pydantic import ValidationError

from ..contracts.pfp_runtime import PfpPipelineFailure
from ..kernel.result import TerminalStatus
from .stages import OBLIGATION_CODES, ChallengeReplay, ReplayOutcome, Stage8Response

DECLARATION_KEYS: Tuple[str, ...] = ("grammar", "equality_test", "coefficient_profile")

Responses = Mapping[int, Mapping[str, Any]]


def _bound(stage: int, demo_id: str) -> Dict[str, Any]:
    return {"stage": stage, "demo_id": demo_id, "authority_effect": "None", "derived_under_policy": "SPK-001"}


def host_passed(responses: Responses) -> bool:
    host = responses.get(5, {})
    return host.get("host_verdict") == "PASS" and host.get("exact_checks_passed") is True


def challenge_replay(responses: Responses) -> Optional[ChallengeReplay]:
    """The stage 7 replay record, validated again on read; None when stage 7 has not run."""
    data = responses.get(7)
    if type(data) is not dict or "host_replay" not in data:
        return None
    try:
        return ChallengeReplay.model_validate(data["host_replay"])
    except ValueError as exc:
        raise PfpPipelineFailure("HOST_CHECK_FAILED", f"Invalid host replay record: {exc}", 7) from exc


def declaration_problems(declaration: Any) -> list[str]:
    """What keeps a seed declaration from admission; empty when it admits."""
    if type(declaration) is not dict:
        return list(DECLARATION_KEYS)
    problems = [key for key in DECLARATION_KEYS
                if type(declaration.get(key)) is not str or not declaration[key].strip()]
    problems += [f"UNKNOWN_DECLARATION_KEY:{key}" for key in sorted(set(declaration) - set(DECLARATION_KEYS))]
    return problems


def admit_record(demo_id: str, declaration: Any, repair: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Stage 1. Admit exactly when the declaration names a grammar, an equality test and a profile.

    With no `repair`, `declaration` is the seed's own. With a `repair` (a validated stage 1 model
    turn), the declaration is the one the model proposed, and the model must also have proposed
    admission with nothing missing. A repaired declaration is admitted as a remaining obligation,
    not as a seed fact.
    """
    if repair is None:
        source, proposal = "seed", declaration
        missing = declaration_problems(declaration)
        refused = False
    else:
        source, proposal = "model_repair", repair["admission_proposal"]
        fields = {key: proposal[key] for key in DECLARATION_KEYS}
        missing = declaration_problems(fields) + list(proposal["missing_declarations"])
        refused = proposal["status"] == "refuse"
    values = proposal if type(proposal) is dict else {}
    status = "refuse" if refused else ("admit" if not missing and (
        repair is None or proposal["status"] == "admit") else "needs_declaration")
    return {
        **_bound(1, demo_id),
        "status": status,
        **{key: values.get(key) if type(values.get(key)) is str else None for key in DECLARATION_KEYS},
        "missing_declarations": missing,
        "declaration_source": source,
        "repair": None if repair is None else dict(repair),
    }


def selection_record(demo_id: str, responses: Responses) -> Dict[str, Any]:
    """Stage 8. Survivors are the stage 5 survivors less every candidate with an open obstruction.

    One survivor is selected and none is a rejection. More than one needs a selector model turn,
    which this version refuses rather than choosing by position.
    """
    if not host_passed(responses):
        raise PfpPipelineFailure("HOST_CHECK_FAILED", "SELECTION_WITHOUT_HOST_PASS", 8)
    replay = challenge_replay(responses)
    obstructed = set() if replay is None else {
        w.candidate_id for w in replay.witnesses if w.outcome is ReplayOutcome.OPEN_OBSTRUCTION}
    passed = list(responses[5].get("surviving_candidates", []))
    survivors = [cid for cid in passed if cid not in obstructed]
    if len(survivors) > 1:
        raise PfpPipelineFailure("HOST_CHECK_FAILED", "SELECTION_NEEDS_MASTER_TURN", 8)
    if not survivors and not obstructed:
        raise PfpPipelineFailure("HOST_CHECK_FAILED", "SELECTION_WITHOUT_SURVIVOR", 8)
    try:
        return Stage8Response(
            demo_id=demo_id,
            disposition="SELECT" if survivors else "REJECT",
            selected_candidate_id=survivors[0] if survivors else None,
            survivors=survivors,
            rule="STAGE5_SURVIVORS_LESS_STAGE7_OBSTRUCTIONS",
        ).model_dump(mode="json")
    except ValidationError as exc:
        raise PfpPipelineFailure("SCHEMA_VIOLATION", f"Selection record refused: {exc}", 8) from exc


def receipt_terminal(responses: Responses) -> Tuple[str, Tuple[str, ...]]:
    """Stage 9. The terminal and the remaining obligation codes, from host facts only."""
    replay = challenge_replay(responses)
    codes = []
    if replay is None or replay.checked_count == 0:
        codes.append("ADVERSARY_CHECKED_NOTHING")
    if responses.get(1, {}).get("declaration_source") != "seed":
        codes.append("DECLARATION_FROM_MODEL_REPAIR")
    obligations = tuple(code for code in OBLIGATION_CODES if code in codes)
    if not host_passed(responses):
        return "BLOCKED_BY_EVIDENCE", obligations
    if replay is not None and replay.obstruction_indices:
        return "OPEN_OBSTRUCTION", obligations
    return ("VERIFIED_WITH_RESIDUALS" if obligations else "VERIFIED"), obligations


def receipt_record(demo_id: str, responses: Responses, obligation_rules: Mapping[str, str]) -> Dict[str, Any]:
    """Stage 9 record; each obligation carries its kill-condition refusal-map key."""
    terminal, codes = receipt_terminal(responses)
    missing = sorted(set(codes) - set(obligation_rules))
    if missing:
        raise PfpPipelineFailure("SCHEMA_VIOLATION", f"RECEIPT_OBLIGATION_RULE_MISSING: {missing}", 9)
    return {
        **_bound(9, demo_id),
        "terminal": terminal,
        "remaining_obligations": [{"code": code, "refusal_map_key": obligation_rules[code]} for code in codes],
        "diagnostic_only": terminal != "VERIFIED",
    }


def hand_off_record(demo_id: str, receipt: Mapping[str, Any], routing: Mapping[str, str]) -> Dict[str, Any]:
    """Stage 10. The packet a later consumer reads: terminal, routing terminal, obligations, no token."""
    terminal = receipt["terminal"]
    status = TerminalStatus.__members__.get(terminal)
    if status is None or status.value not in routing:
        raise PfpPipelineFailure("SCHEMA_VIOLATION", f"HAND_OFF_TERMINAL_UNROUTED: {terminal}", 10)
    return {
        **_bound(10, demo_id),
        "terminal": terminal,
        "routing_terminal": routing[status.value],
        "remaining_obligations": [dict(item) for item in receipt["remaining_obligations"]],
        "authorized_by": None,
    }
