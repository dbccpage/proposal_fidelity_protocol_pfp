"""Finite quotient, explicit extension and survivor checks for Quiz02.

Offline teaching model; a supplied admission is a premise, not authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000037"
MAX_BYTES = 65536
ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
OPERATIONS = ("decl", "del", "ins", "subst")
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID


class InvalidInput(ValueError):
    """The supplied object does not satisfy this pilot's finite contract."""


def require(condition, reason):
    if not condition:
        raise InvalidInput(reason)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Unexpected fields")


def identifier(value):
    require(type(value) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,47}", value) is not None, "Invalid ID")


def sequence(value, maximum, minimum=0):
    require(type(value) is list and minimum <= len(value) <= maximum, "Invalid bounded list")


def text_value(value):
    require(type(value) is str and len(value) <= 64, "Bounded text required")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise InvalidInput("Text must have a UTF-8 representation") from error


def table(value, domain, validator=identifier):
    require(type(value) is dict and set(value) == set(domain), "Incomplete or extra table keys")
    for item in value.values():
        validator(item)


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


def validate_task(task):
    fields(task, ("task_id", "records", "quotient", "downstream", "demands", "candidates"))
    identifier(task["task_id"])
    sequence(task["records"], 16, 1)
    payloads = {}
    for record in task["records"]:
        fields(record, ("id", "payload"))
        identifier(record["id"])
        payload = record["payload"]
        require(type(payload) is str and re.fullmatch(r"[a-z0-9]{0,32}", payload) is not None, "Original payload outside declared alphabet/length")
        require(record["id"] not in payloads, "Repeated record ID")
        payloads[record["id"]] = payload
    table(task["quotient"], payloads)
    table(task["downstream"], set(task["quotient"].values()), text_value)
    sequence(task["demands"], 64)
    demands = set()
    for pair in task["demands"]:
        sequence(pair, 2, 2)
        for name in pair:
            identifier(name)
            require(name in payloads, "Unknown demand endpoint")
        require(pair[0] != pair[1], "Self-demand is not admitted")
        canonical = tuple(sorted(pair))
        require(canonical not in demands, "Repeated unordered demand")
        demands.add(canonical)
    sequence(task["candidates"], 16)
    candidate_ids = set()
    for candidate in task["candidates"]:
        fields(candidate, ("id", "operation", "selector", "output_alphabet", "observer", "cost"))
        identifier(candidate["id"])
        require(candidate["id"] not in candidate_ids, "Repeated candidate ID")
        candidate_ids.add(candidate["id"])
        require(candidate["operation"] in OPERATIONS, "Unknown operation")
        sequence(candidate["selector"], 16)
        for name in candidate["selector"]:
            identifier(name)
            require(name in payloads, "Unknown selector member")
        require(len(set(candidate["selector"])) == len(candidate["selector"]), "Repeated selector member")
        alphabet = candidate["output_alphabet"]
        require(type(alphabet) is str and 1 <= len(alphabet) <= 64 and all(32 <= ord(c) <= 126 for c in alphabet), "Invalid output alphabet")
        require(len(set(alphabet)) == len(alphabet), "Repeated alphabet symbol")
        require(candidate["observer"] in ("opaque", "literal", "selected"), "Unknown output observer")
        require(type(candidate["cost"]) is int and 0 <= candidate["cost"] <= 1000000, "Bounded nonnegative integer cost required")
    return payloads


def factor_map(quotient, values):
    """Find a total factor on the image, or a concrete conflicting fibre pair."""
    witnesses, factor = {}, {}
    for name in sorted(quotient):
        label, value = quotient[name], values[name]
        if label in factor and factor[label] != value:
            return {"factors": False, "factor": None, "conflict": [witnesses[label], name]}
        factor[label], witnesses[label] = value, name
    return {"factors": True, "factor": dict(sorted(factor.items())), "conflict": None}


def unresolved(quotient, demands):
    return sorted([list(sorted(pair)) for pair in demands if quotient[pair[0]] == quotient[pair[1]]])


def refinement_check(old, new, forget):
    table(new, old)
    table(forget, set(new.values()))
    require(all(value in set(old.values()) for value in forget.values()), "Unknown old quotient label")
    violations = sorted(name for name in old if forget[new[name]] != old[name])
    return {"preserves_old": not violations, "violations": violations}


def analyse_extension(task, candidate):
    selected = set(candidate["selector"])
    outputs = {}
    for record in task["records"]:
        name, payload = record["id"], record["payload"]
        output = payload
        if name in selected:
            if candidate["operation"] == "del":
                output = ""
            elif candidate["operation"] == "ins":
                output = payload + "a"
            elif candidate["operation"] == "subst":
                output = payload.replace("a", ">")
        outputs[name] = output
    invalid = sorted(name for name, value in outputs.items() if not set(value) <= set(candidate["output_alphabet"]))
    base = {"candidate_id": candidate["id"], "outputs": outputs, "cost": candidate["cost"],
            "selector_factors_through_old": factor_map(task["quotient"], {name: name in selected for name in task["quotient"]})["factors"]}
    if invalid:
        return {**base, "status": "INVALID_OUTPUT_ALPHABET", "invalid_records": invalid, "survivors": None}
    observations = {}
    for name, value in outputs.items():
        if candidate["observer"] == "opaque":
            observations[name] = "payload" if value else "empty"
        elif candidate["observer"] == "literal":
            observations[name] = value
        else:
            observations[name] = "selected" if name in selected else "other"
    profiles = {name: (task["quotient"][name], observations[name]) for name in outputs}
    labels = {pair: "c" + str(i) for i, pair in enumerate(sorted(set(profiles.values())))}
    new = {name: labels[profile] for name, profile in profiles.items()}
    forget = {label: pair[0] for pair, label in labels.items()}
    return {**base, "status": "CHECKED", "observations": observations, "new_quotient": new, "forget": forget,
            "refinement": refinement_check(task["quotient"], new, forget),
            "raw_observer_preserves_old": factor_map(observations, task["quotient"])["factors"],
            "survivors": unresolved(new, task["demands"])}


def find_candidate(task, candidate_id):
    identifier(candidate_id)
    matches = [candidate for candidate in task["candidates"] if candidate["id"] == candidate_id]
    require(len(matches) == 1, "Unknown candidate")
    return matches[0]


def admission_record(task, candidate_id, receipt_id="admission1"):
    candidate = find_candidate(task, candidate_id)
    return {"receipt_id": receipt_id, "decision": "ADMIT", "scope": "LOCAL_TEACHING_MODEL",
            "task_sha256": digest(task), "candidate_sha256": digest(candidate)}


def admitted(task, candidate, receipt):
    fields(receipt, ("receipt_id", "decision", "scope", "task_sha256", "candidate_sha256"))
    identifier(receipt["receipt_id"])
    require(receipt["decision"] == "ADMIT" and receipt["scope"] == "LOCAL_TEACHING_MODEL", "No local admission")
    require(receipt["task_sha256"] == digest(task), "Admission belongs to another task/baseline")
    require(receipt["candidate_sha256"] == digest(candidate), "Admission belongs to another candidate")


def family_costs(task):
    eligible = []
    partitions = {}
    for candidate in sorted(task["candidates"], key=lambda value: value["id"]):
        result = analyse_extension(task, candidate)
        if result["status"] != "CHECKED" or result["survivors"]:
            continue
        eligible.append(candidate)
        names = sorted(task["quotient"])
        partition = tuple(tuple(other for other in names if result["new_quotient"][name] == result["new_quotient"][other]) for name in names)
        partitions.setdefault(partition, []).append(candidate["id"])
    minimum = min((candidate["cost"] for candidate in eligible), default=None)
    return {"scope": "DECLARED_FAMILY_AND_COSTS", "eligible": [candidate["id"] for candidate in eligible],
            "minimum_cost": minimum, "minimum_ids": [candidate["id"] for candidate in eligible if candidate["cost"] == minimum],
            "equivalence": "SAME_PARTITION_ON_ORIGINAL_DOMAIN", "partition_classes": sorted(partitions.values())}


def answer_for(task, query):
    payloads = validate_task(task)
    require(type(query) is dict, "Query object required")
    kind = query.get("kind")
    shapes = {"collision": ("left", "right"), "recovery": ("left", "right"), "factor": ("values",),
              "refinement": ("new_quotient", "forget"), "family": (), "unique": (), "costs": (),
              "baseline": (), "effect": ("candidate_id",), "survivors": ("candidate_id", "admission"), "authority": ()}
    require(type(kind) is str and kind in shapes, "Unknown query")
    fields(query, ("kind", *shapes[kind]))
    if kind in ("collision", "recovery"):
        for key in ("left", "right"):
            identifier(query[key])
            require(query[key] in payloads, "Unknown query operand")
        left, right = (task["quotient"][query[key]] for key in ("left", "right"))
        equal = left == right
        if kind == "collision":
            return {"left_class": left, "right_class": right, "collision": equal}
        values = [task["downstream"][left], task["downstream"][right]]
        return {"quotient_equal": equal, "outputs": values, "output_equal": values[0] == values[1],
                "status": "NO_RECOVERY_ON_COLLAPSED_PAIR" if equal else "NO_COLLISION_PREMISE"}
    if kind == "factor":
        table(query["values"], payloads, text_value)
        return factor_map(task["quotient"], query["values"])
    if kind == "refinement":
        return refinement_check(task["quotient"], query["new_quotient"], query["forget"])
    if kind == "family":
        return {"candidate_ids": sorted(candidate["id"] for candidate in task["candidates"]),
                "count": len(task["candidates"]), "classification": "SUPPLIED_NOT_EXHAUSTIVE"}
    if kind == "unique":
        return {"refusal": "ref<2>", "reason": "NO_UNCONDITIONAL_SELECTION"}
    if kind == "costs":
        return family_costs(task)
    before = unresolved(task["quotient"], task["demands"])
    if kind == "baseline":
        return {"survivors": before, "count": len(before)}
    if kind in ("effect", "survivors"):
        candidate = find_candidate(task, query["candidate_id"])
        result = analyse_extension(task, candidate)
        if kind == "effect":
            return result
        has_admission = query["admission"] is not None
        if has_admission:
            admitted(task, candidate, query["admission"])
        if result["status"] != "CHECKED":
            return {"refusal": "ref<5>", "reason": "ILL_TYPED_EXTENSION", "current": before, "current_count": len(before), "applied": False}
        after = result["survivors"]
        current = after if has_admission else before
        return {"before": before, "projected_after": after, "current": current, "before_count": len(before),
                "projected_count": len(after), "current_count": len(current),
                "projected_delta": len(before) - len(after), "delta": len(before) - len(current),
                "applied": has_admission, "admission_authenticity": "NOT_CHECKED"}
    return {"refusal": "ref<2>", "reason": "NO_ACTION_AUTHORITY"}


def submission(task, query, answer):
    return {"task": task, "query": query, "proposal": {"problem_sha256": digest({"task": task, "query": query}), "answer": answer}}


def evaluate(document):
    fields(document, ("task", "query", "proposal"))
    computed = answer_for(document["task"], document["query"])
    fields(document["proposal"], ("problem_sha256", "answer"))
    require(type(document["proposal"]["answer"]) is dict, "Structured answer required")
    problem = digest({"task": document["task"], "query": document["query"]})
    require(document["proposal"]["problem_sha256"] == problem, "Proposal belongs to another task/query")
    raw = encoded(document)
    require(len(raw) <= MAX_BYTES, "Proposal exceeds byte limit")
    snapshot = decode(raw)
    matches = encoded(snapshot["proposal"]["answer"]) == encoded(computed)
    return {"pilot_id": PILOT_ID, "verdict": "MATCH" if matches else "MISMATCH", "original": snapshot,
            "computed_answer": computed, "problem_sha256": problem, "authority_effect": "None", "genesis_effect": "None"}


def example_task():
    return {"task_id": "quiz02", "records": [{"id": "blank", "payload": ""}, {"id": "a", "payload": "a"}, {"id": "ab", "payload": "ab"}],
            "quotient": {"blank": "empty", "a": "payload", "ab": "payload"},
            "downstream": {"empty": "0", "payload": "1"}, "demands": [["a", "ab"]],
            "candidates": [{"id": operation, "operation": operation, "selector": ["a"], "output_alphabet": ALPHABET,
                            "observer": "selected" if operation == "decl" else "opaque", "cost": 1} for operation in OPERATIONS]}


def survivor_answer(adoption, separates=True):
    """Handwritten expected answer for the single-demand source fixture."""
    before, after = [["a", "ab"]], ([] if separates else [["a", "ab"]])
    return {"before": before, "projected_after": after, "current": after if adoption else before, "before_count": 1,
            "projected_count": 0 if separates else 1, "current_count": 0 if adoption and separates else 1,
            "projected_delta": 1 if separates else 0, "delta": 1 if adoption and separates else 0,
            "applied": adoption, "admission_authenticity": "NOT_CHECKED"}


def exercise_report():
    task = example_task()
    collision = {"left_class": "payload", "right_class": "payload", "collision": True}
    recovery = {"quotient_equal": True, "outputs": ["1", "1"], "output_equal": True, "status": "NO_RECOVERY_ON_COLLAPSED_PAIR"}
    refusal = {"refusal": "ref<2>", "reason": "NO_UNCONDITIONAL_SELECTION"}
    family = {"candidate_ids": ["decl", "del", "ins", "subst"], "count": 4, "classification": "SUPPLIED_NOT_EXHAUSTIVE"}
    pair = {"left": "a", "right": "ab"}
    adopted = {"kind": "survivors", "candidate_id": "decl", "admission": admission_record(task, "decl")}
    fixtures = [
        ("P2.1", "ask<coll<a,ab>>", "ans<coll<q1<a>,q1<ab>,eq>>", {"kind": "collision", **pair}, collision),
        ("P2.2", "ask<recov<f,q1<a>,q1<ab>>>", "ans<norecov<eq<f<q1<a>>,f<q1<ab>>>>>", {"kind": "recovery", **pair}, recovery),
        ("P2.3", "ask<ext<unique,a,ab>>", "ref<2>", {"kind": "unique"}, refusal),
        ("P2.3_ENUM", "ask<ext<enum,a,ab>>", "ans<ext<decl,del,ins,subst>,cnt<4>>", {"kind": "family"}, family),
        ("P2.4", "ask<surv<s1,s2>>", "ans<surv<s1<1>,s2<0>,d<1>>>", adopted, survivor_answer(True)),
        ("DRILL2.1", "ask<coll<a,ab>>", "ans<coll<q1<a>,q1<ab>,eq>>", {"kind": "collision", **pair}, collision),
        ("DRILL2.2", "ask<recov<f,q1>>", "ans<norecov<q1>>", {"kind": "recovery", **pair}, recovery),
        ("DRILL2.3", "ask<ext<unique>>", "ref<2>", {"kind": "unique"}, refusal),
        ("DRILL2.4", "ask<ext<enum>>", "ans<ext<decl,del,ins,subst>,cnt<4>>", {"kind": "family"}, family),
        ("DRILL2.5", "ask<surv<s1>>", "ans<surv<s1<1>>>", {"kind": "baseline"}, {"survivors": [["a", "ab"]], "count": 1})]
    rows = [{"id": name, "source_query": source_query, "source_answer": source_answer,
             "result": evaluate(submission(task, query, answer))} for name, source_query, source_answer, query, answer in fixtures]
    controls = {
        "not_yet_adopted": evaluate(submission(task, {**adopted, "admission": None}, survivor_answer(False))),
        "ineffective_insertion": evaluate(submission(task, {"kind": "survivors", "candidate_id": "ins", "admission": admission_record(task, "ins")}, survivor_answer(True, False))),
        "forged_collision": evaluate(submission(task, {"kind": "collision", **pair}, {**collision, "collision": False})),
        "forged_survivor_reduction": evaluate(submission(task, {"kind": "survivors", "candidate_id": "ins", "admission": admission_record(task, "ins")}, survivor_answer(True))),
        "authority": evaluate(submission(task, {"kind": "authority"}, {"refusal": "ref<2>", "reason": "NO_ACTION_AUTHORITY"}))}
    enlarged = decode(encoded(task))
    enlarged["candidates"][3]["output_alphabet"] += ">"
    trace = decode(encoded(task))
    trace["candidates"][2]["observer"] = "selected"
    literal = decode(encoded(enlarged))
    literal["candidates"][3]["observer"] = "literal"
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "exercises": rows, "controls": controls,
            "candidate_checks": [answer_for(task, {"kind": "effect", "candidate_id": name}) for name in OPERATIONS],
            "additional_observers": {"substitution_extended_but_opaque": answer_for(enlarged, {"kind": "effect", "candidate_id": "subst"}),
                                    "insertion_with_trace": answer_for(trace, {"kind": "effect", "candidate_id": "ins"}),
                                    "substitution_with_literal_readout": answer_for(literal, {"kind": "effect", "candidate_id": "subst"})},
            "cost_comparison": answer_for(task, {"kind": "costs"}),
            "source_notation": "HISTORICAL_NOT_A_GENERAL_WIRE_PARSER", "authority_effect": "None", "genesis_effect": "None"}


def demonstration_status(report):
    """DEMONSTRATED only when every source row matches its stated answer."""
    return "DEMONSTRATED" if all(row["result"]["verdict"] == "MATCH" for row in report["exercises"]) else "MISMATCH"


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: finite quotient, explicit extension and survivor checks.\nNo live-model, authenticated-admission, global minimum or authority claim.\n").encode()}
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
