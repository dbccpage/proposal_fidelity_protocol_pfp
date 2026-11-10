"""Quiz04: declared simple-pole calculations and typed state replay.

An offline teaching model. Supplied admission is not external authorization.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000038"
MAX_BYTES = 65536
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID


class InvalidInput(ValueError):
    """The bounded JSON teaching contract is not satisfied."""


def require(condition, reason):
    if not condition:
        raise InvalidInput(reason)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Unexpected fields")


def identifier(value):
    require(type(value) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,47}", value) is not None, "Invalid ID")


def json_value(value, depth=0):
    require(depth <= 12, "JSON nesting limit")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        require(abs(value) <= 10**12, "Integer bound")
    elif type(value) is str:
        require(len(value) <= 512, "String bound")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise InvalidInput("Text must have a UTF-8 representation") from error
    elif type(value) is list:
        require(len(value) <= 64, "List bound")
        for item in value:
            json_value(item, depth + 1)
    elif type(value) is dict:
        require(len(value) <= 64, "Object bound")
        for key, item in value.items():
            require(type(key) is str, "String keys required")
            json_value(key, depth + 1)
            json_value(item, depth + 1)
    else:
        raise InvalidInput("Unsupported JSON value; no floating-point numbers")


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(encoded(value))


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, "Bounded bytes required")
    def bad_constant(_):
        raise InvalidInput("Non-finite JSON number")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs, parse_constant=bad_constant)


def clone(value):
    return json.loads(encoded(value))


def qtext(value):
    return f"{value.numerator}/{value.denominator}"


def rational(value):
    require(type(value) is str and re.fullmatch(r"-?(0|[1-9][0-9]{0,6})/[1-9][0-9]{0,6}", value) is not None, "Canonical rational string required")
    parsed = Fraction(value)
    require(abs(parsed.numerator) <= 1000000 and parsed.denominator <= 1000000, "Rational bound")
    require(qtext(parsed) == value, "Unreduced or noncanonical rational")
    return parsed


def task_values(task):
    fields(task, ("task_id", "integrand", "interval", "carrier", "prescription"))
    identifier(task["task_id"])
    fields(task["integrand"], ("family", "residue", "pole"))
    require(task["integrand"]["family"] == "simple_pole", "Unknown integrand family")
    coefficient, pole = rational(task["integrand"]["residue"]), rational(task["integrand"]["pole"])
    require(coefficient != 0, "Zero residue is outside this simple-pole family")
    fields(task["interval"], ("lo", "hi"))
    lo, hi = rational(task["interval"]["lo"]), rational(task["interval"]["hi"])
    require(lo < hi, "Strictly ordered finite bounds required")
    require(task["carrier"] in ("interval", "punctured"), "Unknown carrier")
    prescription = task["prescription"]
    require(type(prescription) is dict, "Prescription object required")
    kind = prescription.get("kind")
    require(type(kind) is str and kind in ("ordinary", "unspecified", "symmetric_pv", "paired_limit"), "Unknown prescription")
    fields(prescription, ("kind", "left_scale", "right_scale") if kind == "paired_limit" else ("kind",))
    if kind == "paired_limit":
        require(rational(prescription["left_scale"]) > 0 and rational(prescription["right_scale"]) > 0, "Positive cutoff scales required")
    return coefficient, pole, lo, hi


def log_term(coefficient, argument):
    """The declared coefficient/log-ratio format, not a general log normal form."""
    require(argument > 0, "Positive log argument required")
    if coefficient == 0 or argument == 1:
        return {"coefficient": "0/1", "log_argument": "1/1"}
    if argument < 1:
        coefficient, argument = -coefficient, 1 / argument
    return {"coefficient": qtext(coefficient), "log_argument": qtext(argument)}


def integral(task):
    coefficient, pole, lo, hi = task_values(task)
    kind = task["prescription"]["kind"]
    inside = lo < pole < hi
    location = "interior" if inside else "left_endpoint" if pole == lo else "right_endpoint" if pole == hi else "outside"
    base = {"pole_location": location, "value": None, "left_limit": None, "right_limit": None,
            "defect_functional": "NOT_MEASURED", "authority_effect": "None"}
    if kind == "unspecified":
        return {**base, "status": "UNSPECIFIED_PRESCRIPTION", "refusal": "ref<5>", "terminal": "REFUSED"}
    if kind != "ordinary":
        if not inside or task["carrier"] != "punctured":
            return {**base, "status": "INVALID_LIMIT_DECLARATION", "refusal": "ref<5>", "terminal": "REFUSED"}
        ratio = (hi - pole) / (pole - lo)
        if kind == "paired_limit":
            ratio *= rational(task["prescription"]["left_scale"]) / rational(task["prescription"]["right_scale"])
        return {**base, "status": "CAUCHY_PRINCIPAL_VALUE" if kind == "symmetric_pv" else "PAIRED_CUTOFF_LIMIT",
                "value": log_term(coefficient, ratio), "refusal": None, "terminal": "LOCAL_GREEN_FOR_SCOPE"}
    if location == "outside":
        return {**base, "status": "PROPER_INTEGRAL", "value": log_term(coefficient, abs((hi - pole) / (lo - pole))),
                "refusal": None, "terminal": "LOCAL_GREEN_FOR_SCOPE"}
    positive = "+infinity" if coefficient > 0 else "-infinity"
    negative = "-infinity" if coefficient > 0 else "+infinity"
    return {**base, "status": "ORDINARY_DIVERGENCE", "left_limit": negative if lo < pole else None,
            "right_limit": positive if pole < hi else None, "refusal": "M", "terminal": "REFUSED_SINGULAR_OBSERVED"}


def cutoff_integral(task, left_cutoff, right_cutoff):
    coefficient, pole, lo, hi = task_values(task)
    left, right = rational(left_cutoff), rational(right_cutoff)
    require(lo < pole < hi, "Cutoff query requires an interior pole")
    require(0 < left < pole - lo and 0 < right < hi - pole, "Cutoffs must retain both nonempty intervals")
    kind = task["prescription"]["kind"]
    follows = None
    if kind == "symmetric_pv":
        follows = left == right
    elif kind == "paired_limit":
        follows = left / right == rational(task["prescription"]["left_scale"]) / rational(task["prescription"]["right_scale"])
    return {"status": "FINITE_TRUNCATION_ONLY", "left": log_term(coefficient, left / (pole - lo)),
            "right": log_term(coefficient, (hi - pole) / right),
            "sum": log_term(coefficient, left * (hi - pole) / (right * (pole - lo))),
            "matches_declared_pairing": follows}


def admission_record(task, replacement, receipt_id="admission1"):
    return {"receipt_id": receipt_id, "decision": "ADMIT_NEW_PROBLEM", "scope": "LOCAL_TEACHING_MODEL",
            "original_sha256": digest(task), "replacement_sha256": digest(replacement)}


def fork_problem(task, replacement, admission):
    task_values(task)
    task_values(replacement)
    refused = {"accepted": False, "refusal": "ref<5>", "original_sha256": digest(task),
               "replacement": None, "admission_authenticity": "NOT_CHECKED"}
    if admission is None:
        return {**refused, "reason": "NO_SUPPLIED_ADMISSION"}
    fields(admission, ("receipt_id", "decision", "scope", "original_sha256", "replacement_sha256"))
    identifier(admission["receipt_id"])
    if not (admission["decision"] == "ADMIT_NEW_PROBLEM" and admission["scope"] == "LOCAL_TEACHING_MODEL"
            and admission["original_sha256"] == digest(task) and admission["replacement_sha256"] == digest(replacement)):
        return {**refused, "reason": "ADMISSION_BINDING"}
    same_integrand = encoded(task["integrand"]) == encoded(replacement["integrand"])
    same_bounds = encoded(task["interval"]) == encoded(replacement["interval"])
    changed_id = task["task_id"] != replacement["task_id"]
    permitted_modes = task["prescription"]["kind"] == "ordinary" and replacement["prescription"]["kind"] in ("symmetric_pv", "paired_limit")
    calculated = integral(replacement)
    if not (same_integrand and same_bounds and changed_id and permitted_modes
            and replacement["carrier"] == "punctured" and calculated["value"] is not None):
        return {**refused, "reason": "NEW_PROBLEM_CONTRACT"}
    return {"accepted": True, "refusal": None, "reason": "DECLARED_LOCAL_NEW_PROBLEM",
            "original_sha256": digest(task), "replacement": clone(replacement), "admission_authenticity": "NOT_CHECKED"}


def state(task, result=None):
    return {"task": clone(task), "result": clone(result)}


def validate_state(value):
    fields(value, ("task", "result"))
    task_values(value["task"])
    require(value["result"] is None or type(value["result"]) is dict, "State result must be an object or null")
    json_value(value)


def event(label, before, after):
    return {"label": label, "task_sha256": digest(before["task"]), "before": clone(before), "after": clone(after)}


def validate_event(value):
    fields(value, ("label", "task_sha256", "before", "after"))
    require(value["label"] in ("C", "R", "M", "T", "D", "E", "I"), "Unknown event label")
    require(type(value["task_sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", value["task_sha256"]) is not None, "Event digest required")
    for name in ("before", "after"):
        if value[name] is not None:
            validate_state(value[name])


def stationary_refusal(task, value):
    validate_event(value)
    require(value["label"] == "M", "Stationarity query requires M")
    before, after = value["before"], value["after"]
    present = before is not None and after is not None
    equal = encoded(before) == encoded(after) if present else None
    bindings = value["task_sha256"] == digest(task) and all(encoded(s["task"]) == encoded(task) for s in (before, after) if s is not None)
    return {"state_equality": "UNVERIFIED" if not present else "EQUAL" if equal else "DIFFERENT",
            "task_binding": "MISMATCH" if not bindings else "CHECKED" if present else "UNVERIFIED",
            "stationary_refusal_verified": present and bindings and equal, "semantic_replay": "NOT_CHECKED"}


def expected_trace(task, replacement=None, admission=None):
    start = state(task)
    if replacement is None:
        require(admission is None and integral(task)["status"] == "ORDINARY_DIVERGENCE", "Refusal route requires ordinary divergence")
        diagnosed = state(task, integral(task))
        return [event("C", start, start), event("R", start, diagnosed),
                event("M", diagnosed, diagnosed), event("T", diagnosed, diagnosed)]
    change = fork_problem(task, replacement, admission)
    require(change["accepted"], "New-problem route lacks a valid declared local fork")
    fresh = state(replacement)
    evaluated = state(replacement, integral(replacement))
    return [event("C", start, start), event("D", start, fresh), event("E", fresh, evaluated),
            event("I", evaluated, evaluated), event("T", evaluated, evaluated)]


def replay_trace(task, events, replacement, admission):
    require(type(events) is list and 1 <= len(events) <= 8, "Bounded nonempty event list required")
    for value in events:
        validate_event(value)
    labels = [value["label"] for value in events]
    refused = {"accepted": False, "refusal": "ref<1>", "bad_events": [], "final_state": None,
               "authority_effect": "None", "admission_authenticity": "NOT_CHECKED"}
    if labels not in (["C", "R", "M", "T"], ["C", "D", "E", "I", "T"]):
        return {**refused, "reason": "ROUTE_SHAPE"}
    if (labels[1] == "R") != (replacement is None):
        return {**refused, "reason": "ROUTE_DECLARATION"}
    try:
        expected = expected_trace(task, replacement, admission)
    except InvalidInput:
        return {**refused, "reason": "ROUTE_PRECONDITION"}
    wrong = [index for index, (actual, wanted) in enumerate(zip(events, expected, strict=True)) if encoded(actual) != encoded(wanted)]
    if wrong:
        return {**refused, "reason": "EVENT_REPLAY", "bad_events": wrong}
    return {**refused, "accepted": True, "refusal": None, "reason": "DECLARED_EVENT_REPLAY",
            "final_state": clone(events[-1]["after"])}


def answer_for(task, query):
    task_values(task)
    require(type(query) is dict, "Query object required")
    kind = query.get("kind")
    shapes = {"integral": (), "cutoffs": ("left_cutoff", "right_cutoff"), "claim_zero": (),
              "stationarity": ("event",), "change": ("replacement", "admission"),
              "trace": ("events", "replacement", "admission"), "authority": ()}
    require(type(kind) is str and kind in shapes, "Unknown query")
    fields(query, ("kind", *shapes[kind]))
    if kind == "integral":
        return integral(task)
    if kind == "cutoffs":
        return cutoff_integral(task, query["left_cutoff"], query["right_cutoff"])
    if kind == "claim_zero":
        result = integral(task)
        supported = result["value"] == {"coefficient": "0/1", "log_argument": "1/1"}
        return {"zero_supported": supported, "refusal": None if supported else "ref<5>", "prescription": task["prescription"]["kind"]}
    if kind == "stationarity":
        return stationary_refusal(task, query["event"])
    if kind == "change":
        return fork_problem(task, query["replacement"], query["admission"])
    if kind == "trace":
        return replay_trace(task, query["events"], query["replacement"], query["admission"])
    return {"refusal": "ref<2>", "reason": "NO_GLOBAL_AUTHORITY"}


def submission(task, query, answer):
    return {"task": task, "query": query, "proposal": {"problem_sha256": digest({"task": task, "query": query}), "answer": answer}}


def evaluate(document):
    fields(document, ("task", "query", "proposal"))
    json_value(document)
    raw = encoded(document)
    require(len(raw) <= MAX_BYTES, "Submission exceeds byte limit")
    snapshot = clone(document)
    fields(snapshot["proposal"], ("problem_sha256", "answer"))
    require(type(snapshot["proposal"]["answer"]) is dict, "Structured answer required")
    problem = digest({"task": snapshot["task"], "query": snapshot["query"]})
    require(snapshot["proposal"]["problem_sha256"] == problem, "Proposal belongs to another task/query")
    computed = answer_for(snapshot["task"], snapshot["query"])
    matches = encoded(snapshot["proposal"]["answer"]) == encoded(computed)
    return {"pilot_id": PILOT_ID, "verdict": "MATCH" if matches else "MISMATCH", "original": snapshot,
            "computed_answer": clone(computed), "problem_sha256": problem,
            "comparison": "DECLARED_STRUCTURED_FORMAT_NOT_GENERAL_SYMBOLIC_EQUIVALENCE",
            "authority_effect": "None", "genesis_effect": "None"}


def example_task(mode="ordinary"):
    return {"task_id": "ordinary1" if mode == "ordinary" else "newproblem1",
            "integrand": {"family": "simple_pole", "residue": "1/1", "pole": "5/1"},
            "interval": {"lo": "0/1", "hi": "10/1"}, "carrier": "interval" if mode == "ordinary" else "punctured",
            "prescription": {"kind": mode}}


def source_answers():
    base = {"pole_location": "interior", "left_limit": None, "right_limit": None,
            "defect_functional": "NOT_MEASURED", "authority_effect": "None"}
    ordinary = {**base, "status": "ORDINARY_DIVERGENCE", "value": None, "left_limit": "-infinity",
                "right_limit": "+infinity", "refusal": "M", "terminal": "REFUSED_SINGULAR_OBSERVED"}
    pv = {**base, "status": "CAUCHY_PRINCIPAL_VALUE", "value": {"coefficient": "0/1", "log_argument": "1/1"},
          "refusal": None, "terminal": "LOCAL_GREEN_FOR_SCOPE"}
    return ordinary, pv


def exercise_report():
    original, replacement = example_task(), example_task("symmetric_pv")
    ordinary_answer, pv_answer = source_answers()
    admission = admission_record(original, replacement)
    trace1 = expected_trace(original)
    trace2 = expected_trace(original, replacement, admission)
    changed_trace = clone(trace1)
    changed_trace[-1]["label"] = "E"
    stationary = {"state_equality": "EQUAL", "task_binding": "CHECKED", "stationary_refusal_verified": True, "semantic_replay": "NOT_CHECKED"}
    refused_change = {"accepted": False, "refusal": "ref<5>", "original_sha256": digest(original),
                      "replacement": None, "admission_authenticity": "NOT_CHECKED", "reason": "NO_SUPPLIED_ADMISSION"}
    wrong_route = {"accepted": False, "refusal": "ref<1>", "bad_events": [], "final_state": None,
                   "authority_effect": "None", "admission_authenticity": "NOT_CHECKED", "reason": "ROUTE_SHAPE"}
    change_query = {"kind": "change", "replacement": replacement, "admission": None}
    fixtures = [
        ("P4.1", "ask<eval<f<1_over_x_minus_5>,c<0_10>,cont>>", "ans<refusal<M>,res<phi1<inf>>,locus<x5>,tape<c,r,m,t>>", original, {"kind": "integral"}, ordinary_answer),
        ("P4.2", "ask<check<state<before_m>,state<after_m>>>", "ans<eq<state<before_m>,state<after_m>>>", original, {"kind": "stationarity", "event": trace1[2]}, stationary),
        ("P4.3", "ask<op<auto_carrier_surgery>>", "ref<5>", original, change_query, refused_change),
        ("P4.4", "ask<eval<PV_integral,carrier<strat>>>", "ans<hit<0>,term<LOCAL_GREEN_FOR_SCOPE>>", replacement, {"kind": "integral"}, pv_answer),
        ("DRILL4.1", "ask<int<f<pole>,carrier<cont>>>", "ans<refusal<M>,tape<c,r,m,t>>", original, {"kind": "integral"}, ordinary_answer),
        ("DRILL4.2", "ask<claim<0,carrier<cont>>>", "ref<5>", original, {"kind": "claim_zero"}, {"zero_supported": False, "refusal": "ref<5>", "prescription": "ordinary"}),
        ("DRILL4.3", "ask<tape<c,r,m,e>>", "ref<1>", original, {"kind": "trace", "events": changed_trace, "replacement": None, "admission": None}, wrong_route),
        ("DRILL4.4", "ask<auto_excise<x5>>", "ref<5>", original, change_query, refused_change),
        ("DRILL4.5", "ask<int<PV,carrier<strat>>>", "ans<hit<0>,term<local_green>>", replacement, {"kind": "integral"}, pv_answer)]
    rows = [{"id": name, "source_query": printed_query, "source_answer": printed_answer,
             "result": evaluate(submission(task, query, answer))} for name, printed_query, printed_answer, task, query, answer in fixtures]
    routes = []
    for name, tape, events, new, permit, final in [
            ("ROUTE1", "C -> R -> M -> T", trace1, None, None, state(original, ordinary_answer)),
            ("ROUTE2", "C -> D -> E -> I -> T", trace2, replacement, admission, state(replacement, pv_answer))]:
        expected = {"accepted": True, "refusal": None, "bad_events": [], "final_state": final,
                    "authority_effect": "None", "admission_authenticity": "NOT_CHECKED", "reason": "DECLARED_EVENT_REPLAY"}
        routes.append({"id": name, "source_tape": tape, "result": evaluate(submission(original,
            {"kind": "trace", "events": events, "replacement": new, "admission": permit}, expected))})
    missing = {**trace1[2], "before": None, "after": None}
    missing_answer = {"state_equality": "UNVERIFIED", "task_binding": "UNVERIFIED", "stationary_refusal_verified": False, "semantic_replay": "NOT_CHECKED"}
    controls = {
        "missing_state": evaluate(submission(original, {"kind": "stationarity", "event": missing}, missing_answer)),
        "promotion": evaluate(submission(replacement, {"kind": "authority"}, {"refusal": "ref<2>", "reason": "NO_GLOBAL_AUTHORITY"})),
        "forged_zero": evaluate(submission(original, {"kind": "integral"}, pv_answer)),
        "forged_stationarity": evaluate(submission(original, {"kind": "stationarity", "event": missing}, stationary))}
    asymmetric = clone(replacement)
    asymmetric["integrand"]["pole"] = "4/1"
    paired = clone(replacement)
    paired["prescription"] = {"kind": "paired_limit", "left_scale": "2/1", "right_scale": "1/1"}
    punctured = clone(original)
    punctured["carrier"] = "punctured"
    unspecified = clone(punctured)
    unspecified["prescription"] = {"kind": "unspecified"}
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "exercises": rows, "routes": routes, "controls": controls,
            "counterexamples": {name: {"task": task, "result": integral(task)} for name, task in [
                ("asymmetric_pv", asymmetric), ("unequal_cutoffs", paired),
                ("excision_only", punctured), ("unspecified_limit", unspecified)]},
            "source_notation": "HISTORICAL_NOT_A_GENERAL_WIRE_PARSER", "authority_effect": "None", "genesis_effect": "None"}


def demonstration_status(report):
    """DEMONSTRATED only when every source row and both routes match their stated answers."""
    rows = report["exercises"] + report["routes"]
    return "DEMONSTRATED" if all(row["result"]["verdict"] == "MATCH" for row in rows) else "MISMATCH"


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: declared simple-pole calculation and state replay.\nNo general integration, authenticated permission, live-model or authority claim.\n").encode()}
    for name, raw in artifacts.items():
        (folder / name).write_bytes(raw)
    receipt = {"pilot_id": PILOT_ID, "status": status, "model_calls": 0, "cost_usd": "0",
               "code_sha256": sha(Path(__file__).read_bytes()), "artifact_sha256": {name: sha(raw) for name, raw in artifacts.items()}}
    (folder / "receipt.json").write_bytes(encoded(receipt))
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    try:
        if args.input:
            document, raw = read_document(args.input)
            try:
                report = evaluate(document)
                status = report["verdict"]
            except InvalidInput as error:
                report, status = {"reason": str(error)}, "REJECTED"
        else:
            raw, report = encoded({"kind": "built_in_exercises"}), exercise_report()
            status = demonstration_status(report)
        folder = write_run(args.output_dir, report, raw, status)
    except (ValueError, TypeError, OSError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder.resolve())}, ensure_ascii=True))
    return 1 if status in ("MISMATCH", "REJECTED") else 0


if __name__ == "__main__":
    sys.exit(main())

