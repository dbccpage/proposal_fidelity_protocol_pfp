"""Original C007 host compaction sessions over immutable constraint identities.

The host supplies the release schedule and independent native measurement. Model
turns use the existing PFP boundary. This implements text arms, not local KV hooks
or an empirical claim about any model. AuthorityEffect: None.
"""

from __future__ import annotations

import base64
import json
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256

from pfp.domain.cohomology.certificate_checker import check_certificate
from pfp.domain.cohomology.validation import exact_fraction
from pfp.domain.solvers.simplicial_cochain import CochainCarrier
from pfp.infrastructure.adapters.rust_cohomology_adapter import (
    RustCohomologySolverAdapter,
)
from pfp.infrastructure.task_turn import prepare_task_turn


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _seal(state):
    state["state_sha256"] = sha256(_bytes({k: v for k, v in state.items() if k != "state_sha256"})).hexdigest()
    return state


def _validate(state):
    expected = sha256(_bytes({k: v for k, v in state.items() if k != "state_sha256"})).hexdigest()
    if state.get("state_sha256") != expected:
        raise ValueError("COMPACTION_STATE_MISMATCH")


def _name(value):
    return type(value) is str and 0 < len(value) <= 128 and "->" not in value and not any(ord(c) < 32 for c in value)


def _constraint(value):
    if type(value) is not dict or set(value) != {"id", "u", "v", "claim", "repairable"}:
        raise ValueError("CONSTRAINT_SHAPE_REQUIRED")
    if not all(_name(value[k]) for k in ("id", "u", "v")) or value["u"] == value["v"]:
        raise ValueError("CONSTRAINT_IDENTITY_REQUIRED")
    if type(value["claim"]) is not int or abs(value["claim"]) > 999 or type(value["repairable"]) is not bool:
        raise ValueError("CONSTRAINT_EXACT_TYPES_REQUIRED")


def _schedule(events):
    if type(events) is not list or not 30 <= len(events) <= 48:
        raise ValueError("C007_REQUIRES_30_TO_48_TURNS")
    declared, edges, nodes = {}, set(), set()
    stage, status_turns = 0, 0
    for event in events:
        if type(event) is not dict or event.get("kind") not in {"release", "status", "continue"}:
            raise ValueError("HOST_EVENT_REQUIRED")
        if event["kind"] == "release":
            if set(event) != {"kind", "stage", "constraints"} or type(event["stage"]) is not int or event["stage"] != stage + 1:
                raise ValueError("STAGE_RELEASE_ORDER_REQUIRED")
            if not 1 <= event["stage"] <= 6 or type(event["constraints"]) is not list or not event["constraints"]:
                raise ValueError("STAGE_CONSTRAINTS_REQUIRED")
            previous_nodes, fragment_nodes = set(nodes), set()
            for row in event["constraints"]:
                _constraint(row)
                edge = row["u"], row["v"]
                if row["id"] in declared or edge in edges:
                    raise ValueError("CONSTRAINT_REDECLARATION_REFUSED")
                declared[row["id"]] = deepcopy(row)
                edges.add(edge)
                fragment_nodes.update(edge)
            if previous_nodes and not previous_nodes.intersection(fragment_nodes):
                raise ValueError("STAGE_MUST_SHARE_VERTICES")
            nodes.update(fragment_nodes)
            stage += 1
        elif event["kind"] == "status":
            if set(event) != {"kind", "restatements"} or type(event["restatements"]) is not list:
                raise ValueError("STATUS_RESTATEMENTS_REQUIRED")
            for row in event["restatements"]:
                _constraint(row)
                if row["id"] not in declared:
                    raise ValueError("UNKNOWN_RESTATEMENT_ID")
            status_turns += 1
        elif set(event) != {"kind"}:
            raise ValueError("CONTINUE_EVENT_FIELDS_REFUSED")
        if stage == 0:
            raise ValueError("FIRST_TURN_MUST_RELEASE_STAGE_ONE")
        if len(nodes) > 40 or len(edges) > 70 or len(edges) - len(nodes) + 1 > 10:
            raise ValueError("C007_UNION_BOUND_EXCEEDED")
        CochainCarrier("C007", tuple(sorted(nodes)), tuple(sorted(edges)), ()).find_spanning_tree()
    if stage != 6:
        raise ValueError("C007_REQUIRES_SIX_STAGES")
    if not 6 <= status_turns <= 10:
        raise ValueError("C007_REQUIRES_6_TO_10_STATUS_TURNS")
    return deepcopy(events)


def _case(state, claims=None):
    values = state["claims"] if claims is None else claims
    rows = state["constraints"].values()
    return dict(challenge="c011", case_id="C007:" + state["run_id"],
                nodes=sorted({r[k] for r in rows for k in ("u", "v")}),
                edges=[[r["u"], r["v"]] for r in rows],
                claims={r["u"] + "->" + r["v"]: values[r["id"]] for r in rows},
                weights={r["u"] + "->" + r["v"]: 1 for r in rows})


def _measure(case, native):
    result = (native or RustCohomologySolverAdapter()).solve(case)
    if result.get("status") != "SOLVED" or not check_certificate(case, result).passed:
        raise ValueError("C007_MEASUREMENT_UNAVAILABLE")
    return result


def _release(state, native):
    event = state["schedule"][len(state["transcript"])]
    refusal = None
    if event["kind"] == "release":
        for row in event["constraints"]:
            state["constraints"][row["id"]] = deepcopy(row)
            state["claims"][row["id"]] = row["claim"]
    elif event["kind"] == "status":
        if any(row != state["constraints"][row["id"]] for row in event["restatements"]):
            refusal = "FALSE_RESTATEMENT_REFUSED"
    state["host_event"] = dict(message=deepcopy(event), refusal=refusal)
    state["measurement"] = _measure(_case(state), native)


def start_compaction_session(events, *, run_id, protocol_sha256, arm="ledger", native=None):
    """Freeze the original long-horizon host schedule before the first model turn."""
    if not _name(run_id) or type(protocol_sha256) is not str or len(protocol_sha256) != 64 or any(c not in "0123456789abcdef" for c in protocol_sha256):
        raise ValueError("RUN_AND_PROTOCOL_BINDING_REQUIRED")
    if arm not in {"ledger", "history", "prose"}:
        raise ValueError("C007_KV_EXECUTION_UNAVAILABLE")
    state = dict(schema_version="c007.session.v1", run_id=run_id, protocol_sha256=protocol_sha256,
                 arm=arm, schedule=_schedule(events), constraints={}, claims={}, transcript=[],
                 violations=0, terminal=None)
    _release(state, native)
    return _seal(state)


def _object(properties):
    return dict(type="object", properties=properties, required=list(properties), additionalProperties=False)


def prepare_compaction_turn(state):
    _validate(state)
    if state["terminal"] is not None:
        raise ValueError("SESSION_TERMINAL")
    rows = list(state["constraints"].values())
    context = dict(protocol="C007", protocol_sha256=state["protocol_sha256"],
                   turn=len(state["transcript"]) + 1, total_turns=len(state["schedule"]),
                   constraints=rows, current_claims=state["claims"], phi1=state["measurement"]["phi1"],
                   host_event=state["host_event"], violations=state["violations"])
    previous = [dict(host_event=row["host_event"], answer=row["pfp"].get("answer"), outcome=row["outcome"])
                for row in state["transcript"]]
    if state["arm"] == "history":
        context["history"] = previous
    elif state["arm"] == "prose":
        context["constraint_prose"] = _bytes(rows).decode()
        context["last_two_turns"] = previous[-2:]
        del context["constraints"]
    else:
        context["last_two_turns"] = previous[-2:]
    scalar = dict(type="string", pattern=r"^(0|[1-9][0-9]*|-[1-9][0-9]*)$")
    moves = [_object(dict(move={"const": "CUT"}, claims=_object({r["id"]: scalar for r in rows}))),
             _object(dict(move={"const": "VERIFY"}, potential=_object({n: scalar for n in _case(state)["nodes"]})))]
    return prepare_task_turn(system="Play the original bounded C007 context-retention task.",
        user="Preserve every declared constraint identity and every non-repairable claim. "
             "A refused restatement does not replace the host ledger. CUT proposes all current claims; "
             "only exact strict descent or zero is admitted. VERIFY supplies a potential, not a claim of success. "
             "Completion requires the final union after every scheduled turn and zero constraint violations.",
        task_id="C007:" + state["run_id"], attempt_id=str(len(state["transcript"]) + 1),
        answer_schema={"oneOf": moves}, checker_id="c007-protected-constraints-v1", context=context)


def constraint_retention(state):
    """Exact declared records present in the model-visible decoded public context."""
    turn = prepare_compaction_turn(state)
    context = turn.task.case["context"]
    raw = _bytes(context)
    if "constraint_prose" in context:
        raw += context["constraint_prose"].encode()
    found = sum(_bytes(row) in raw for row in state["constraints"].values())
    return Fraction(found, len(state["constraints"]))


def submit_compaction_turn(state, raw_reply, *, native=None):
    turn = prepare_compaction_turn(state)
    result = deepcopy(state)
    outcome = dict(accepted=False, reason="TASK_ENVELOPE")

    def judge(_public, answer):
        nonlocal outcome
        if answer["move"] == "CUT":
            proposed = {key: int(value) for key, value in answer["claims"].items()}
            changed = [key for key, row in result["constraints"].items()
                       if not row["repairable"] and proposed[key] != row["claim"]]
            if changed:
                result["violations"] += 1
                outcome = dict(accepted=False, reason="CONSTRAINT_EDIT", constraint_ids=changed)
            else:
                measured = _measure(_case(result, proposed), native)
                admitted = exact_fraction(measured["phi1"]) < exact_fraction(result["measurement"]["phi1"]) or measured["phi1"] == "0"
                if admitted:
                    result.update(claims=proposed, measurement=measured)
                outcome = dict(accepted=admitted, reason="CUT_ADMITTED" if admitted else "NO_STRICT_DESCENT")
        else:
            result["measurement"] = _measure(_case(result), native)
            valid = result["measurement"]["phi1"] == "0" and check_certificate(_case(result), dict(
                status="SOLVED", phi1="0", potential=answer["potential"], repair={}, dual={})).passed
            final = len(result["transcript"]) + 1 == len(result["schedule"])
            accepted = valid and final and result["violations"] == 0
            reason = "VERIFIED_UNION" if accepted else "FUTURE_CONSTRAINTS_PENDING" if valid and not final else "INVALID_UNION_OR_VIOLATION"
            outcome = dict(accepted=accepted, reason=reason)
            if accepted:
                result["terminal"] = "ACCEPTED_ZERO_DEFECT"
        return outcome["accepted"], outcome["reason"]

    checked = turn.check(raw_reply, judges=(("c007-native-and-independent", judge),), require_checker=True)
    result["transcript"].append(dict(host_event=deepcopy(state["host_event"]),
                                     prompt=dict(system=turn.prompt.system, user=turn.prompt.user), pfp=checked,
                                     retention=str(constraint_retention(state)), outcome=outcome))
    if result["terminal"] is None:
        if len(result["transcript"]) == len(result["schedule"]):
            result["terminal"] = "FUEL_EXHAUSTED"
        else:
            _release(result, native)
    return _seal(result)


def _stable(value):
    if type(value) is dict:
        return {k: _stable(v) for k, v in value.items() if k not in {"native_outcome", "state_sha256"}}
    if type(value) in (tuple, list):
        return [_stable(v) for v in value]
    return value


def replay_compaction_session(state, *, native=None):
    """Recompute every retained raw turn and protected-constraint decision."""
    _validate(state)
    replayed = start_compaction_session(state["schedule"], run_id=state["run_id"],
        protocol_sha256=state["protocol_sha256"], arm=state["arm"], native=native)
    for row in state["transcript"]:
        raw = base64.b64decode(row["pfp"]["raw_reply_base64"], validate=True)
        if sha256(raw).hexdigest() != row["pfp"]["raw_reply_sha256"]:
            raise ValueError("REPLAY_RAW_MISMATCH")
        replayed = submit_compaction_turn(replayed, raw, native=native)
    if _stable(replayed) != _stable(state):
        raise ValueError("COMPACTION_REPLAY_MISMATCH")
    return dict(terminal=replayed["terminal"], turns=len(replayed["transcript"]),
                violations=replayed["violations"], provider_calls=0)


def compaction_result(state):
    """Project the original deliverable only after final-union verification."""
    _validate(state)
    result = dict(status="UNKNOWN", refusal=state["terminal"] or "SESSION_IN_PROGRESS",
        violations=str(state["violations"]), turns=str(len(state["transcript"])),
        transcript=deepcopy(state["transcript"]))
    if state["terminal"] == "ACCEPTED_ZERO_DEFECT":
        result.update(status="SOLVED", final_cochain={key: str(value) for key, value in state["claims"].items()},
            potential=deepcopy(state["transcript"][-1]["pfp"]["answer"]["potential"]))
        del result["refusal"]
    return result
