"""C006 bounded sessions through PFP and the existing weighted native checker.

The host measures proposed cochains; it never puts its optimal repair in a
participant prompt. A checked move is not a completed scientific experiment.
Native and independent certificates establish finite admission only.
"""
from __future__ import annotations

import base64
import json
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256

from pfp.domain.cohomology.certificate_checker import check_certificate
from pfp.domain.cohomology.validation import exact_fraction, parse_c011_case
from pfp.domain.solvers.simplicial_cochain import CochainCarrier
from pfp.infrastructure.adapters.rust_cohomology_adapter import (
    RustCohomologySolverAdapter,
)
from pfp.infrastructure.mechanism_scratch_space import (
    HostScratchLedger,
    StationaryCutBinding,
    stationary_cut_binding,
    stationary_repeat,
)
from pfp.infrastructure.task_turn import prepare_task_turn


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _digest(value):
    return sha256(_bytes(value)).hexdigest()


def _seal(state):
    state["state_sha256"] = _digest({k: v for k, v in state.items() if k != "state_sha256"})
    return state


def _validate_state(state):
    if state.get("state_sha256") != _digest({k: v for k, v in state.items() if k != "state_sha256"}):
        raise ValueError("SESSION_STATE_MISMATCH")


def _integer(value):
    parsed = exact_fraction(value)
    if parsed.denominator != 1:
        raise ValueError("EXACT_INTEGER_REQUIRED")
    return int(parsed)


def _case(state, claims=None):
    return dict(state["board"], challenge="c011", claims=claims if claims is not None else state["claims"])


def _measure(case, native):
    result = (native or RustCohomologySolverAdapter()).solve(case)
    if result.get("status") != "SOLVED":
        raise ValueError("C006_NATIVE_UNAVAILABLE: " + str(result.get("refusal", result.get("status"))))
    if not check_certificate(case, result).passed:
        raise ValueError("C006_INDEPENDENT_CERTIFICATE_REFUSED")
    _integer(result["phi1"])
    return result


def _structure(board, claims):
    carrier = CochainCarrier("C006", tuple(board["nodes"]), tuple(map(tuple, board["edges"])), ())
    if "spanning_tree" in board:
        tree = tuple(map(tuple, board["spanning_tree"]))
        if len(tree) != len(board["nodes"]) - 1 or len(set(tree)) != len(tree) or not set(tree) <= set(carrier.edges):
            raise ValueError("C006_SPANNING_TREE_INVALID")
        CochainCarrier("C006-tree", carrier.vertices, tree, ()).find_spanning_tree()
        chords = tuple(edge for edge in carrier.edges if edge not in set(tree))
    else:
        tree, chords = carrier.find_spanning_tree()
    cycles = carrier.find_fundamental_cycles(tree, chords)
    residuals = {f"{u}->{v}": sum(sign * claims[f"{a}->{b}"] for a, b, sign in cycle)
                 for (u, v), cycle in zip(chords, cycles)}
    return {"tree_edges": list(map(list, tree)), "chords": list(map(list, chords)),
            "cycles": [[list(term) for term in cycle] for cycle in cycles],
            "cycle_residuals": residuals,
            "closed_chords": sorted(key for key, value in residuals.items() if value == 0)}


def start_session(board, *, run_id, protocol_sha256, arm="ledger", detector_firing_share="1/3", native=None):
    """Validate the original integer-board scope and measure its actual Phi1."""
    if type(run_id) is not str or not run_id.strip():
        raise ValueError("RUN_ID_REQUIRED")
    if (type(protocol_sha256) is not str or len(protocol_sha256) != 64
            or any(c not in "0123456789abcdef" for c in protocol_sha256)):
        raise ValueError("PROTOCOL_DIGEST_REQUIRED")
    if arm not in ("ledger", "history", "prose"):
        raise ValueError("C006_ARM_UNAVAILABLE")
    share = exact_fraction(detector_firing_share)
    if not 0 <= share <= 1:
        raise ValueError("DETECTOR_FIRING_SHARE_REQUIRED")
    nodes, edges, claims, weights = parse_c011_case(board)
    keys = {f"{u}->{v}" for u, v in edges}
    if set(claims) != keys or set(weights) != keys:
        raise ValueError("COMPLETE_BOARD_COORDINATES_REQUIRED")
    claims, weights = ({key: _integer(value) for key, value in vector.items()} for vector in (claims, weights))
    if any(value <= 0 for value in weights.values()):
        raise ValueError("POSITIVE_INTEGER_WEIGHTS_REQUIRED")
    if any(u == v or u not in nodes or v not in nodes for u, v in edges):
        raise ValueError("INVALID_BOARD_EDGE")
    normalized = dict(case_id=str(board.get("case_id", run_id)), nodes=nodes,
                      edges=list(map(list, edges)), claims=claims, weights=weights)
    if "spanning_tree" in board:
        normalized["spanning_tree"] = deepcopy(board["spanning_tree"])
    _structure(normalized, claims)  # Also rejects disconnected boards.
    rank = len(edges) - len(nodes) + 1
    if not 3 <= rank <= 8:
        raise ValueError("C006_CYCLE_RANK_OUT_OF_SCOPE")
    state = dict(schema_version="c006.session.v1", run_id=run_id, protocol_sha256=protocol_sha256,
                 arm=arm, detector_firing_share=str(share), board=normalized, cycle_rank=rank,
                 fuel=len(edges) + 3 * rank, claims=claims, asserted_edges=[], transcript=[],
                 terminal=None, detector_firings=0, detector_suspended=False,
                 stationary_binding=None, stationary_counter=0)
    if "spanning_tree" in normalized:
        state["schema_version"] = "c006.session.v2"
    state["measurement"] = _measure(_case(state), native)
    return _seal(state)


def _ledger(state):
    structure = _structure(state["board"], state["claims"])
    recent = [json.dumps({"answer": row["pfp"].get("answer"),
                          "reason": row["outcome"]["reason"]}, sort_keys=True)
              for row in state["transcript"]]
    return HostScratchLedger.from_host(board_bytes=_bytes(state["board"]), claims=state["claims"],
        asserted_edges=state["asserted_edges"], phi1=_integer(state["measurement"]["phi1"]),
        cycle_residuals=structure["cycle_residuals"], closed_chords=structure["closed_chords"],
        last_move_sha256=state["transcript"][-1]["pfp"]["raw_reply_sha256"] if recent else None,
        stationary_counter=state["stationary_counter"], last_two_turns=recent)


def _object(properties):
    return dict(type="object", properties=properties, required=list(properties), additionalProperties=False)


def prepare_session_turn(state):
    """A/B/C get identical current facts, with different history presentation."""
    _validate_state(state)
    if state["terminal"] is not None:
        raise ValueError("SESSION_TERMINAL")
    ledger = _ledger(state)
    structure = _structure(state["board"], state["claims"])
    scalar = {"type": "string", "pattern": r"^(0|[1-9][0-9]*|-[1-9][0-9]*)$"}
    moves = [
        _object(dict(move={"const": "ASSERT"}, edge={"enum": sorted(state["claims"])}, value=scalar)),
        _object(dict(move={"const": "CUT"}, claims=_object({k: scalar for k in state["claims"]}))),
        _object(dict(move={"const": "LIFT_REQUEST"})),
        _object(dict(move={"const": "VERIFY"}, potential=_object({k: scalar for k in state["board"]["nodes"]}))),
    ]
    facts = {"nodes": state["board"]["nodes"], "edges": state["board"]["edges"],
             "weights": state["board"]["weights"], "current_claims": state["claims"],
             "phi1": state["measurement"]["phi1"], "asserted_edges": state["asserted_edges"],
             **structure, "fuel_remaining": state["fuel"] - len(state["transcript"])}
    context = dict(protocol="C006", protocol_sha256=state["protocol_sha256"], host_facts=facts,
                   host_state_sha256=ledger.state_sha256, arm=state["arm"])
    if state["arm"] == "history":
        context["history"] = [dict(host_facts=row["host_facts"],
                                   answer=row["pfp"].get("answer"), reason=row["outcome"]["reason"])
                              for row in state["transcript"]]
    elif state["arm"] == "prose":
        context["scratch_prose"] = "; ".join(f"{key}: {json.dumps(value)}" for key, value in ledger.public_context().items())
    else:
        context["scratch_ledger"] = ledger.public_context()
    context["last_outcome"] = ({key: state["transcript"][-1]["outcome"].get(key)
                                for key in ("reason", "am4", "suggested_action")}
                               if state["transcript"] else None)
    return prepare_task_turn(system="Play one bounded Symbol Game move using the supplied public host facts.",
        user="ASSERT records an existing edge and its current value; it does not change the board. "
             "CUT proposes a complete integer cochain and is admitted only when exact weighted Phi1 "
             "strictly decreases or reaches zero. LIFT_REQUEST returns cycle structure, never proposed values. "
             "At Phi1 zero, submit VERIFY with a potential explaining every current edge to finish. "
             "A zero CUT alone does not finish. Every reply spends one turn. "
             "Your objective is a repaired cochain, not recording edges. ASSERT is optional bookkeeping. "
             "Do not repeat an already asserted edge: that leaves every claim and Phi1 unchanged and "
             "still spends fuel. Use CUT to propose progress or LIFT_REQUEST to inspect the structure. "
             "Use the declared response envelope and move grammar.",
        task_id="C006:" + state["run_id"], attempt_id=str(len(state["transcript"]) + 1),
        answer_schema={"oneOf": moves}, checker_id="c006-native-weighted-session-v1", context=context)


def _apply(state, answer, native):
    outcome = dict(accepted=False, reason="TASK_ENVELOPE", am4=None)
    move = answer["move"]
    if move == "ASSERT":
        if _integer(answer["value"]) != state["claims"][answer["edge"]]:
            outcome["reason"] = "ASSERT_VALUE_MISMATCH"
        else:
            reason = "ASSERT_ALREADY_RECORDED" if answer["edge"] in state["asserted_edges"] else "ASSERT_RECORDED"
            state["asserted_edges"] = sorted(set(state["asserted_edges"]) | {answer["edge"]})
            outcome.update(accepted=True, reason=reason)
    elif move == "LIFT_REQUEST":
        outcome.update(accepted=True, reason="STRUCTURE_RETURNED", **_structure(state["board"], state["claims"]))
    elif move == "CUT":
        candidate = {key: _integer(value) for key, value in answer["claims"].items()}
        measured = _measure(_case(state, candidate), native)
        before, after = _integer(state["measurement"]["phi1"]), _integer(measured["phi1"])
        outcome["candidate_measurement"] = measured
        if after < before or after == 0:
            state.update(claims=candidate, measurement=measured, stationary_binding=None, stationary_counter=0)
            outcome.update(accepted=True, reason="CUT_ADMITTED")
        else:
            outcome["reason"] = "NO_STRICT_DESCENT"
            if after == before and before > 0:
                ledger = _ledger(state)
                previous = (StationaryCutBinding(**state["stationary_binding"])
                            if state["stationary_binding"] is not None else None)
                if stationary_repeat(ledger, candidate, previous) and not state["detector_suspended"]:
                    state["detector_firings"] += 1
                    outcome.update(am4="AM-4-STATIONARY-REPEAT", suggested_action="REQUEST_DIFFERENT_CANDIDATE_OR_LIFT")
                    if Fraction(state["detector_firings"], len(state["transcript"]) + 1) > Fraction(state["detector_firing_share"]):
                        state["detector_suspended"] = True
                        outcome["detector_suspended"] = True
                binding = stationary_cut_binding(ledger, candidate, observed_phi1=after)
                state["stationary_binding"] = dict(host_state_sha256=binding.host_state_sha256, cut_sha256=binding.cut_sha256)
                state["stationary_counter"] += 1
    elif move == "VERIFY":
        state["measurement"] = _measure(_case(state), native)
        if _integer(state["measurement"]["phi1"]) != 0:
            outcome["reason"] = "NONZERO_DEFECT"
        elif not check_certificate(_case(state), dict(status="SOLVED", phi1="0",
                potential=answer["potential"], repair={}, dual={})).passed:
            outcome["reason"] = "INVALID_POTENTIAL"
        else:
            state["terminal"] = "ACCEPTED_ZERO_DEFECT"
            outcome.update(accepted=True, reason="VERIFIED_ZERO_DEFECT")
    return outcome


def submit_session_turn(state, raw_reply, *, native=None):
    """Check the actual PFP reply bytes; each attempt spends exactly one turn."""
    turn = prepare_session_turn(state)
    result = deepcopy(state)
    outcome = dict(accepted=False, reason="TASK_ENVELOPE", am4=None)

    def judge(_case_value, answer):
        nonlocal outcome
        try:
            outcome = _apply(result, answer, native)
        except ValueError as exc:
            if str(exc).startswith(("C006_NATIVE_", "C006_INDEPENDENT_")):
                result["terminal"] = "EXECUTION_UNAVAILABLE"
                outcome = dict(accepted=False, reason=str(exc), am4=None)
            else:
                raise
        return outcome["accepted"], outcome["reason"]

    checked = turn.check(raw_reply, judges=(("c006-native-weighted-session", judge),), require_checker=True)
    result["transcript"].append(dict(host_facts=turn.task.case["context"]["host_facts"],
                                     pfp=checked, outcome=outcome))
    if result["terminal"] is None and len(result["transcript"]) >= result["fuel"]:
        result["terminal"] = "SURVIVOR_OBSTRUCTION"
    return _seal(result)


def _stable(value):
    if type(value) is dict:
        return {key: _stable(item) for key, item in value.items() if key not in ("native_outcome", "state_sha256")}
    if type(value) in (list, tuple):
        return [_stable(item) for item in value]
    return value


def replay_session(state, *, native=None):
    """Rebuild from the original board and raw turns, with zero model calls."""
    # Raw corruption gets its own reason even if it also invalidates the seal.
    for row in state["transcript"]:
        try:
            raw = base64.b64decode(row["pfp"]["raw_reply_base64"], validate=True)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("REPLAY_RAW_MISMATCH") from exc
        if sha256(raw).hexdigest() != row["pfp"].get("raw_reply_sha256"):
            raise ValueError("REPLAY_RAW_MISMATCH")
    _validate_state(state)
    replayed = start_session(state["board"], run_id=state["run_id"], protocol_sha256=state["protocol_sha256"],
                             arm=state["arm"], detector_firing_share=state["detector_firing_share"], native=native)
    for row in state["transcript"]:
        turn = prepare_session_turn(replayed)
        if row["pfp"].get("binding") != turn.binding:
            raise ValueError("REPLAY_BINDING_MISMATCH")
        replayed = submit_session_turn(replayed, base64.b64decode(row["pfp"]["raw_reply_base64"], validate=True), native=native)
    if _stable(replayed) != _stable(state):
        raise ValueError("SESSION_STATE_MISMATCH")
    return dict(terminal=replayed["terminal"], provider_calls=0, turns=len(replayed["transcript"]),
                phi1_final=replayed["measurement"]["phi1"])


def session_result(state):
    """Original C006 deliverable projection; only a checked VERIFY is SOLVED."""
    _validate_state(state)
    result = dict(status="UNKNOWN", refusal=state["terminal"] or "SESSION_IN_PROGRESS",
                  phi1_final=state["measurement"]["phi1"], turns=str(len(state["transcript"])),
                  transcript=deepcopy(state["transcript"]))
    if state["terminal"] == "ACCEPTED_ZERO_DEFECT":
        result.update(status="SOLVED", final_cochain={key: str(value) for key, value in state["claims"].items()},
                      potential=deepcopy(state["transcript"][-1]["pfp"]["answer"]["potential"]))
        del result["refusal"]
    return result


def exact_baseline(board, *, protocol_sha256, native=None):
    """Original arm E: actual exact nearest coboundary, explicitly NO_LLM.

    This host-only control deliberately uses the solver's potential. It does not
    fabricate model turns or feed that potential to another arm's prompt.
    """
    state = start_session(board, run_id="C006-exact-baseline", protocol_sha256=protocol_sha256, native=native)
    potential = state["measurement"]["potential"]
    claims = {f"{u}->{v}": str(_integer(exact_fraction(potential[v]) - exact_fraction(potential[u])))
              for u, v in state["board"]["edges"]}
    measured = _measure(_case(state, claims), native)
    if measured["phi1"] != "0" or not check_certificate(_case(state, claims), dict(
            status="SOLVED", phi1="0", potential=potential, repair={}, dual={})).passed:
        raise ValueError("C006_BASELINE_VERIFICATION_FAILED")
    return dict(executor="NO_LLM", status="SOLVED", final_cochain=claims, potential=potential,
                original_phi1=state["measurement"]["phi1"], phi1_final="0", provider_calls=0,
                turns="0", original_measurement=state["measurement"], final_measurement=measured)
