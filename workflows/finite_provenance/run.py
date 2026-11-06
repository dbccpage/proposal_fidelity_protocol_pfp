"""Quiz01: finite successors, declared observations and supplied provenance.

Offline teaching model. No automatic carrier admission or external authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000036"
MAX_BYTES = 65536
FACETS = ("current", "previous", "history", "supplied", "mentioned_only", "internal")
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID


class InvalidInput(ValueError):
    """Input does not satisfy this finite pilot's declared contract."""


def require(condition, reason):
    if not condition:
        raise InvalidInput(reason)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Unexpected fields")


def bounded_text(value, limit=256):
    require(type(value) is str and 0 < len(value) <= limit, "Bounded nonempty text required")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise InvalidInput("Text must have a UTF-8 representation") from error


def identifier(value):
    require(type(value) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,47}", value) is not None, "Invalid record ID")


def sequence(value, maximum, minimum=0):
    require(type(value) is list and minimum <= len(value) <= maximum, "Invalid bounded list")


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
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, "Bounded input bytes required")
    def bad_constant(_):
        raise InvalidInput("Non-finite JSON number")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs, parse_constant=bad_constant)


def event_prefix(task, index):
    return digest({"task_id": task["task_id"], "presentations": task["presentations"], "events": task["events"][:index]})


def validate_task(task):
    fields(task, ("task_id", "presentations", "events", "transitions", "observations", "interpretations"))
    identifier(task["task_id"])
    sequence(task["presentations"], 16, 1)
    texts = {}
    for record in task["presentations"]:
        fields(record, ("id", "text"))
        identifier(record["id"])
        bounded_text(record["text"])
        require(record["id"] not in texts, "Repeated presentation ID")
        texts[record["id"]] = record["text"]
    def known(value):
        identifier(value)
        require(value in texts, "Unknown presentation ID")
    sequence(task["events"], 64, 2)
    supplies, supplied, mentioned, internal, receipt_ids = {}, set(), set(), set(), set()
    event_ids, designations = set(), []
    regime = None
    for index, event in enumerate(task["events"]):
        require(type(event) is dict, "Event object required")
        kind = event.get("kind")
        extra = ("supply_event", "regime_event", "basis", "receipt_id", "prefix_sha256", "inscription_sha256") if kind == "admit" else ()
        fields(event, ("kind", "event_id", "presentation", *extra))
        identifier(event["event_id"])
        require(event["event_id"] not in event_ids, "Repeated event ID")
        event_ids.add(event["event_id"])
        mark = event["presentation"]
        known(mark)
        if kind == "supply":
            require(mark not in supplied, "Repeated supply")
            supplies[event["event_id"]] = mark
            supplied.add(mark)
        elif kind == "mention":
            mentioned.add(mark)
        elif kind == "designate":
            require(mark in supplied, "Designation before supply")
            designations.append(mark)
            regime = event["event_id"]
            internal = set()
        elif kind == "admit":
            identifier(event["supply_event"])
            identifier(event["receipt_id"])
            require(supplies.get(event["supply_event"]) == mark, "Admission lacks prior matching supply")
            require(regime is not None and event["regime_event"] == regime, "Wrong admission regime")
            require(event["basis"] in ("consumer", "retention"), "Undeclared admission basis")
            require(event["receipt_id"] not in receipt_ids and mark not in internal, "Repeated admission")
            require(event["prefix_sha256"] == event_prefix(task, index), "Admission prefix/task changed")
            require(event["inscription_sha256"] == sha(texts[mark].encode("utf-8")), "Admission inscription changed")
            receipt_ids.add(event["receipt_id"])
            internal.add(mark)
        else:
            raise InvalidInput("Unknown event kind")
    require(designations, "Current designation required")
    sequence(task["transitions"], 64)
    edges = set()
    for edge in task["transitions"]:
        sequence(edge, 2, 2)
        for mark in edge:
            known(mark)
        require(tuple(edge) not in edges, "Repeated transition")
        edges.add(tuple(edge))
    sequence(task["observations"], 8)
    test_ids = set()
    for table in task["observations"]:
        fields(table, ("test_id", "domain", "values"))
        identifier(table["test_id"])
        require(table["test_id"] not in test_ids, "Repeated test ID")
        test_ids.add(table["test_id"])
        sequence(table["domain"], 16)
        for mark in table["domain"]:
            known(mark)
        require(len(set(table["domain"])) == len(table["domain"]) and set(table["domain"]) == internal, "Observation domain differs from admitted carrier")
        require(type(table["values"]) is dict and set(table["values"]) == internal, "Incomplete observation table")
        for value in table["values"].values():
            bounded_text(value, 32)
    sequence(task["interpretations"], 16)
    declaration_ids = set()
    for declaration in task["interpretations"]:
        fields(declaration, ("declaration_id", "presentation", "meaning"))
        identifier(declaration["declaration_id"])
        require(declaration["declaration_id"] not in declaration_ids, "Repeated interpretation declaration")
        declaration_ids.add(declaration["declaration_id"])
        known(declaration["presentation"])
        bounded_text(declaration["meaning"])
    return {"texts": texts, "current": designations[-1], "regime": regime, "history": designations[:-1],
            "supplied": supplied, "mentioned": mentioned, "internal": internal}


def answer_for(task, query):
    context = validate_task(task)
    require(type(query) is dict, "Query object required")
    kind = query.get("kind")
    shapes = {"presentation": (), "successors": ("seed",), "permitted_next": ("seed", "target"),
              "forced_next": ("seed", "target"), "profiles": ("left", "right"),
              "claim_discrimination": ("left", "right"), "provenance": ("facets",),
              "interpretation": ("presentation", "meaning"), "authority": ()}
    require(type(kind) is str and kind in shapes, "Unknown query")
    fields(query, ("kind", *shapes[kind]))
    for name in ("seed", "target", "left", "right", "presentation"):
        if name in query:
            identifier(query[name])
            require(query[name] in context["texts"], "Unknown query operand")
    if kind == "presentation":
        current = context["current"]
        return {"id": current, "text": context["texts"][current], "internally_admitted": current in context["internal"], "semantics": "NOT_INFERRED"}
    if kind in ("successors", "permitted_next", "forced_next"):
        successors = sorted(post for pre, post in task["transitions"] if pre == query["seed"])
        if kind == "forced_next":
            return {"refusal": "ref<2>", "reason": "NO_FORCING_CONTRACT", "permitted": query["target"] in successors}
        if kind == "permitted_next":
            return {"permitted": query["target"] in successors, "scope": "DECLARED_RELATION_ONLY"}
        return {"successors": successors, "quiescent": not successors, "sole_successor": successors[0] if len(successors) == 1 else None, "inevitability": "NOT_ESTABLISHED"}
    if kind in ("profiles", "claim_discrimination"):
        left, right = query["left"], query["right"]
        admitted = left in context["internal"] and right in context["internal"]
        witnesses = sorted(table["test_id"] for table in task["observations"] if admitted and table["values"][left] != table["values"][right])
        if kind == "claim_discrimination":
            return {"separating_tests": witnesses} if witnesses else {"refusal": "ref<2>", "reason": "NO_DECLARED_SEPARATING_WITNESS"}
        return {"external_text_equal": context["texts"][left] == context["texts"][right],
                "operands_admitted": admitted, "separating_tests": witnesses,
                "comparison_status": "UNADMITTED_OPERAND" if not admitted else ("CHECKED_DECLARED_TABLES" if task["observations"] else "NO_DECLARED_TESTS"),
                "object_equality": "NOT_INFERRED", "expressive_power": "NOT_MEASURED"}
    if kind == "provenance":
        selected = query["facets"]
        sequence(selected, len(FACETS), 1)
        require(all(type(x) is str and x in FACETS for x in selected) and len(set(selected)) == len(selected), "Invalid provenance facets")
        facets = {"current": context["current"], "previous": context["history"][-1] if context["history"] else None,
                  "history": list(context["history"]), "supplied": sorted(context["supplied"]),
                  "mentioned_only": sorted(context["mentioned"] - context["supplied"]), "internal": sorted(context["internal"])}
        return {key: facets[key] for key in sorted(selected)}
    if kind == "interpretation":
        bounded_text(query["meaning"])
        matches = sorted(x["declaration_id"] for x in task["interpretations"] if x["presentation"] == query["presentation"] and x["meaning"] == query["meaning"])
        return {"status": "DECLARED_NOT_VALIDATED", "declarations": matches} if matches else {"refusal": "ref<1>", "reason": "UNDECLARED_INTERPRETATION"}
    return {"refusal": "ref<2>", "reason": "NO_ACTION_AUTHORITY"}


def problem_digest(task, query):
    return digest({"task": task, "query": query})


def evaluate(document):
    fields(document, ("task", "query", "proposal"))
    computed = answer_for(document["task"], document["query"])
    fields(document["proposal"], ("problem_sha256", "answer"))
    require(type(document["proposal"]["answer"]) is dict, "Structured answer required")
    require(document["proposal"]["problem_sha256"] == problem_digest(document["task"], document["query"]), "Proposal belongs to another task/query")
    raw = encoded(document)
    require(len(raw) <= MAX_BYTES, "Proposal exceeds byte limit")
    snapshot = decode(raw)
    matches = encoded(snapshot["proposal"]["answer"]) == encoded(computed)
    return {"pilot_id": PILOT_ID, "verdict": "MATCH" if matches else "MISMATCH",
            "original": snapshot, "computed_answer": computed, "problem_sha256": problem_digest(snapshot["task"], snapshot["query"]),
            "authority_effect": "None", "genesis_effect": "None", "external_history_authentication": "NOT_PERFORMED"}


def ground_task():
    return {"task_id": "quiz01_ground", "presentations": [{"id": "ground", "text": "<>"}, {"id": "a", "text": "<a>"}, {"id": "ab", "text": "<ab>"}],
            "events": [{"kind": "supply", "event_id": "s0", "presentation": "ground"}, {"kind": "designate", "event_id": "d0", "presentation": "ground"}],
            "transitions": [], "observations": [], "interpretations": []}


def append_admission(task, mark, supply_event, regime_event, receipt_id):
    """Construct a declared local ledger entry; no issuer authentication."""
    texts = {x["id"]: x["text"] for x in task["presentations"]}
    task["events"].append({"kind": "admit", "event_id": "admit_" + receipt_id, "presentation": mark,
                           "supply_event": supply_event, "regime_event": regime_event, "basis": "retention",
                           "receipt_id": receipt_id, "prefix_sha256": event_prefix(task, len(task["events"])),
                           "inscription_sha256": sha(texts[mark].encode("utf-8"))})


def provenance_task():
    task = ground_task()
    task["task_id"] = "quiz01_provenance"
    task["events"].extend([{"kind": "supply", "event_id": "s1", "presentation": "a"},
                           {"kind": "designate", "event_id": "d1", "presentation": "a"},
                           {"kind": "mention", "event_id": "m1", "presentation": "ab"}])
    append_admission(task, "a", "s1", "d1", "r1")
    return task


def submission(task, query, answer):
    return {"task": task, "query": query, "proposal": {"problem_sha256": problem_digest(task, query), "answer": answer}}


def observation_task(same_text=False, separating=True):
    task = ground_task()
    task["task_id"] = "quiz01_observations"
    if same_text:
        task["presentations"][1]["text"] = "<>"
    task["events"].append({"kind": "supply", "event_id": "s1", "presentation": "a"})
    append_admission(task, "ground", "s0", "d0", "r0")
    append_admission(task, "a", "s1", "d0", "r1")
    task["observations"] = [{"test_id": "t1", "domain": ["ground", "a"], "values": {"ground": "0", "a": "1" if separating else "0"}}]
    return task


def exercise_report():
    ground, provenance = ground_task(), provenance_task()
    supplied = ground_task()
    supplied["events"].append({"kind": "supply", "event_id": "s1", "presentation": "a"})
    quiet = {"successors": [], "quiescent": True, "sole_successor": None, "inevitability": "NOT_ESTABLISHED"}
    profiles = {"external_text_equal": False, "operands_admitted": False, "separating_tests": [],
                "comparison_status": "UNADMITTED_OPERAND", "object_equality": "NOT_INFERRED", "expressive_power": "NOT_MEASURED"}
    full_facets = ["current", "previous", "history", "mentioned_only", "internal"]
    full_answer = {"current": "a", "previous": "ground", "history": ["ground"], "mentioned_only": ["ab"], "internal": ["a"]}
    fixtures = [
        ("P1.1", "ask<trans<pd<>>>", "ans<quiet<pd<>>>", ground, {"kind": "successors", "seed": "ground"}, quiet),
        ("P1.2", "ask<expr<pd<>,a>>", "ans<eqexpr<pd<>,a,0>>", supplied, {"kind": "profiles", "left": "ground", "right": "a"}, profiles),
        ("P1.3", "ask<audit<regime>>", "ans<audit<curr<a>,prev<pd<>>,hist<pd<>>,ment<ab>,intern<a>>>", provenance, {"kind": "provenance", "facets": full_facets}, full_answer),
        ("DRILL1.1", "ask<pd>", "ans<pd<>>", ground, {"kind": "presentation"}, {"id": "ground", "text": "<>", "internally_admitted": False, "semantics": "NOT_INFERRED"}),
        ("DRILL1.2", "ask<next<pd<>>>", "ans<quiet<pd<>>>", ground, {"kind": "successors", "seed": "ground"}, quiet),
        ("DRILL1.3", "ask<claim<forced<a>>>", "ref<2>", ground, {"kind": "forced_next", "seed": "ground", "target": "a"}, {"refusal": "ref<2>", "reason": "NO_FORCING_CONTRACT", "permitted": False}),
        ("DRILL1.4", "ask<sem<pd<>>>", "ref<1>", ground, {"kind": "interpretation", "presentation": "ground", "meaning": "void"}, {"refusal": "ref<1>", "reason": "UNDECLARED_INTERPRETATION"}),
        ("DRILL1.5", "ask<audit<regime>>", "ans<audit<curr<a>,prev<pd<>>,ment<ab>>>", provenance, {"kind": "provenance", "facets": ["current", "previous", "mentioned_only"]}, {"current": "a", "previous": "ground", "mentioned_only": ["ab"]})]
    rows = [{"id": name, "source_query": query_text, "source_answer": source_answer,
             "result": evaluate(submission(task, query, answer))} for name, query_text, source_answer, task, query, answer in fixtures]
    trap = evaluate(submission(supplied, {"kind": "claim_discrimination", "left": "ground", "right": "a"},
                               {"refusal": "ref<2>", "reason": "NO_DECLARED_SEPARATING_WITNESS"}))
    edge_task = ground_task()
    edge_task["transitions"] = [["ground", "a"]]
    controls = {
        "forged_successor": evaluate(submission(ground, {"kind": "permitted_next", "seed": "ground", "target": "a"}, {"permitted": True, "scope": "DECLARED_RELATION_ONLY"})),
        "permitted_successor": evaluate(submission(edge_task, {"kind": "permitted_next", "seed": "ground", "target": "a"}, {"permitted": True, "scope": "DECLARED_RELATION_ONLY"})),
        "singleton_not_inevitable": evaluate(submission(edge_task, {"kind": "forced_next", "seed": "ground", "target": "a"}, {"refusal": "ref<2>", "reason": "NO_FORCING_CONTRACT", "permitted": True})),
        "forged_internal": evaluate(submission(ground, {"kind": "provenance", "facets": ["internal"]}, {"internal": ["ground"]})),
        "authority": evaluate(submission(ground, {"kind": "authority"}, {"refusal": "ref<2>", "reason": "NO_ACTION_AUTHORITY"}))}
    for name, same_text, separating in (("separating_table", False, True), ("equal_profiles", False, False), ("same_text_distinct_records", True, True)):
        expected = {"external_text_equal": same_text, "operands_admitted": True,
                    "separating_tests": ["t1"] if separating else [], "comparison_status": "CHECKED_DECLARED_TABLES",
                    "object_equality": "NOT_INFERRED", "expressive_power": "NOT_MEASURED"}
        controls[name] = evaluate(submission(observation_task(same_text, separating), {"kind": "profiles", "left": "ground", "right": "a"}, expected))
    interpreted = ground_task()
    interpreted["interpretations"] = [{"declaration_id": "i1", "presentation": "ground", "meaning": "void"}]
    controls["declared_not_true"] = evaluate(submission(interpreted, {"kind": "interpretation", "presentation": "ground", "meaning": "void"},
                                                        {"status": "DECLARED_NOT_VALIDATED", "declarations": ["i1"]}))
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "exercises": rows, "P1.2_refusal_trap": trap, "controls": controls,
            "source_notation": "HISTORICAL_NOT_A_GENERAL_WIRE_PARSER", "authority_effect": "None", "genesis_effect": "None"}


def demonstration_status(report):
    """DEMONSTRATED only when every source row and the P1.2 trap match their stated answers."""
    results = [row["result"] for row in report["exercises"]] + [report["P1.2_refusal_trap"]]
    return "DEMONSTRATED" if all(result["verdict"] == "MATCH" for result in results) else "MISMATCH"


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: bounded relation, observation and supplied-event checks.\nNo external-history authenticity, live-model or action-authority claim.\n").encode()}
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
            raw = encoded({"kind": "built_in_exercises"})
            report = exercise_report()
            status = demonstration_status(report)
        folder = write_run(args.output_dir, report, raw, status)
    except (ValueError, TypeError, OSError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder.resolve())}, ensure_ascii=True))
    return 1 if status in ("MISMATCH", "REJECTED") else 0


if __name__ == "__main__":
    sys.exit(main())
