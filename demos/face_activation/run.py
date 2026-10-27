"""Quiz08: declared finite face activation, signed filling and toy observables."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000041"
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID
# Facts each computed answer must show, transcribed from the original worksheet's tables and source rows.
SOURCE_FACTS = {
    "P8.1": {"data": {"observables": {"toy_drag": "0/1", "toy_massless_no_drag": True}}},
    "P8.2": {"data": {"status": "EXECUTED", "state": {"face_weight": 1}}},
    "P8.3": {"data": {"right_mass_vs_left": 1, "transition_executed": False}},
    "P8.4": {"data": dict(refusal="ref<3>", claim="cern_higgs_boson_125_gev")},
    "DRILL8.1": {"data": {"observables": {"toy_massless_no_drag": True}}},
    "DRILL8.2": {"data": {"status": "EXECUTED", "state": {"face_weight": 1}}},
    "DRILL8.3": {"data": {"observables": {"toy_drag": "0/1"}}},
    "DRILL8.4": {"data": {"observables": {"toy_drag": "1/1"}}},
    "DRILL8.5": {"data": dict(refusal="ref<3>", claim="standard_model")}}
MAX_BYTES = 131072
SOURCE_VOCABULARY = ("<a,b,c,0>", "<a,b,c,1>", "pop<f0,f1>", "lock<l,f1,d>",
                     "mass<area<d>>", "oracle<phys,ae0>", "ref<3>")


class InvalidInput(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Exact object fields required")


def identifier(value):
    require(type(value) is str and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_.-]{0,31}", value) is not None,
            "Bounded identifier required")


def integer(value):
    require(type(value) is int and abs(value) <= 1000000, "Bounded integer required")
    return value


def json_value(value, depth=0):
    require(depth <= 16, "JSON depth bound")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        require(abs(value) <= 10**18, "JSON integer bound")
    elif type(value) is str:
        require(len(value) <= 2048, "String bound")
        require(all(32 <= ord(c) < 127 for c in value), "Printable ASCII required")
    elif type(value) is list:
        require(len(value) <= 256, "List bound")
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


def clone(value):
    return json.loads(encoded(value))


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


def qtext(value):
    return f"{value.numerator}/{value.denominator}"


def rational(value):
    require(type(value) is str and re.fullmatch(r"(0|[1-9][0-9]{0,6})/[1-9][0-9]{0,6}", value) is not None,
            "Nonnegative canonical rational string required")
    parsed = Fraction(value)
    require(parsed.numerator <= 1000000 and parsed.denominator <= 1000000, "Rational bound")
    require(qtext(parsed) == value, "Unreduced or noncanonical rational")
    return parsed


def state_data(state):
    fields(state, ("revision", "face_weight", "payload"))
    require(integer(state["revision"]) >= 0, "Nonnegative revision required")
    require(type(state["face_weight"]) is int and state["face_weight"] in (0, 1), "Integer activity bit required")
    require(type(state["payload"]) is dict, "Payload object required")
    json_value(state["payload"])


def vector(value, size):
    require(type(value) is list and len(value) == size, "Complete edge-chain vector required")
    return [integer(item) for item in value]


def mat(values, cols):
    return {"rows": len(values), "cols": cols, "values": values}


def mv(matrix, values):
    require(len(values) == matrix["cols"], "Matrix-vector shape mismatch")
    return [sum(a*b for a, b in zip(row, values, strict=True)) for row in matrix["values"]]


def complex_data(task):
    fields(task, ("task_id", "vertices", "edges", "potential_face", "activity_encoding", "state", "adapter"))
    identifier(task["task_id"])
    require(task["activity_encoding"] == "one_potential_face_binary_activity_v1", "Explicit activity encoding required")
    vertices, edges = task["vertices"], task["edges"]
    require(type(vertices) is list and 3 <= len(vertices) <= 16, "Bounded vertex list required")
    require(type(edges) is list and 3 <= len(edges) <= 48, "Bounded edge list required")
    for vertex in vertices:
        identifier(vertex)
    require(len(set(vertices)) == len(vertices), "Duplicate vertex")
    seen = set()
    for edge in edges:
        require(type(edge) is list and len(edge) == 2, "Edge arity")
        for vertex in edge:
            identifier(vertex)
        require(len(set(edge)) == 2 and set(edge) <= set(vertices), "Edge endpoints")
        key = tuple(sorted(edge))
        require(key not in seen, "Duplicate unoriented edge")
        seen.add(key)
    face = task["potential_face"]
    fields(face, ("face_id", "vertices"))
    identifier(face["face_id"])
    cycle = face["vertices"]
    require(type(cycle) is list and len(cycle) == 3, "Potential triangle arity")
    for vertex in cycle:
        identifier(vertex)
    require(len(set(cycle)) == 3 and set(cycle) <= set(vertices), "Potential triangle vertices")
    state_data(task["state"])
    adapter = task["adapter"]
    if adapter is not None:
        fields(adapter, ("scheme", "mass_scale", "drag_scale"))
        require(adapter["scheme"] == "linear_activity_observables_v1", "Unknown observable adapter")
        for name in ("mass_scale", "drag_scale"):
            if adapter[name] is not None:
                rational(adapter[name])
    b1 = mat([[int(v == b) - int(v == a) for a, b in edges] for v in vertices], len(edges))
    boundary = [0] * len(edges)
    a, b, c = cycle
    for u, v in ((a, b), (b, c), (c, a)):
        matches = [j for j, edge in enumerate(edges) if set(edge) == {u, v}]
        require(len(matches) == 1, "Potential face is missing a boundary edge")
        j = matches[0]
        boundary[j] = 1 if edges[j] == [u, v] else -1
    active = task["state"]["face_weight"] == 1
    b2 = mat([[value] if active else [] for value in boundary], int(active))
    product = mat([[sum(row[k]*b2["values"][k][j] for k in range(len(edges)))
                    for j in range(b2["cols"])] for row in b1["values"]], b2["cols"])
    return {"B1": b1, "B2": b2, "B1B2": product, "face_boundary": boundary,
            "boundary_of_face_boundary": mv(b1, boundary),
            "active_faces": [face["face_id"]] if active else [],
            "basis": {"vertices": clone(vertices), "edges": clone(edges)}}


def classify(task, chain):
    topology = complex_data(task)
    chain = vector(chain, len(task["edges"]))
    boundary = mv(topology["B1"], chain)
    face_boundary = topology["face_boundary"]
    if task["state"]["face_weight"] == 0:
        witness = [] if not any(chain) else None
    else:
        pivot = next(i for i, value in enumerate(face_boundary) if value)
        k = chain[pivot] * face_boundary[pivot]
        witness = [k] if chain == [k*value for value in face_boundary] else None
    return {"chain": chain, "boundary": boundary, "closed": not any(boundary),
            "exact": witness is not None, "filling": witness}


def observations(task):
    complex_data(task)
    adapter, weight = task["adapter"], task["state"]["face_weight"]
    values = {}
    for name in ("mass", "drag"):
        scale = adapter[name + "_scale"] if adapter is not None else None
        values["toy_" + name] = None if scale is None else qtext(rational(scale)*weight)
    values["toy_massless_no_drag"] = None if None in values.values() else all(v == "0/1" for v in values.values())
    return values


def permission_for(task, query, admitted=True):
    return {"permit_id": "local_permission1", "admitted": admitted,
            "problem_sha256": digest({"task": task, "query": query})}


def permission_shape(permission):
    if permission is None:
        return
    fields(permission, ("permit_id", "admitted", "problem_sha256"))
    identifier(permission["permit_id"])
    require(type(permission["admitted"]) is bool, "Boolean permission disposition required")
    require(type(permission["problem_sha256"]) is str and re.fullmatch("[0-9a-f]{64}", permission["problem_sha256"]) is not None,
            "Permission digest format")

def permission_valid(task, query, permission):
    permission_shape(permission)
    return permission is not None and permission["admitted"] and permission["problem_sha256"] == digest({"task": task, "query": query})


def validate_pop(task, query):
    fields(query, ("case_id", "kind", "event_id", "face_id", "before_state_sha256", "after", "lock"))
    require(query["kind"] == "pop", "Pop event required")
    for key in ("case_id", "event_id", "face_id"):
        identifier(query[key])
    require(type(query["before_state_sha256"]) is str and re.fullmatch("[0-9a-f]{64}", query["before_state_sha256"]) is not None,
            "Before-state digest format")
    state_data(query["after"])
    vector(query["lock"], len(task["edges"]))


def pop_data(task, query, permission):
    validate_pop(task, query)
    topology = complex_data(task)
    allowed = permission_valid(task, query, permission)
    expected_after = clone(task["state"])
    expected_after.update(face_weight=1, revision=task["state"]["revision"] + 1)
    checks = {"permission": allowed, "target": query["face_id"] == task["potential_face"]["face_id"],
              "before": query["before_state_sha256"] == digest(task["state"]),
              "inactive": task["state"]["face_weight"] == 0,
              "after": encoded(query["after"]) == encoded(expected_after),
              "unit_signed_lock": query["lock"] == topology["face_boundary"]}
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return {"status": "REFUSED", "failed": failed, "state": clone(task["state"]), "actual_after": None}
    after_task = clone(task)
    after_task["state"] = clone(query["after"])
    return {"status": "EXECUTED", "failed": [], "state": clone(after_task["state"]),
            "before_lock": classify(task, query["lock"]), "after_lock": classify(after_task, query["lock"]),
            "actual_after": {"topology": complex_data(after_task), "observables": observations(after_task)}}


def answer_for(task, query, permission=None):
    for value in (task, query, permission):
        json_value(value)
    task, query, permission = clone(task), clone(query), clone(permission)
    topology = complex_data(task)
    require(type(query) is dict and "kind" in query and "case_id" in query, "Query identity required")
    identifier(query["case_id"])
    kind = query["kind"]
    require(type(kind) is str, "Query kind required")
    if kind == "pop":
        data = pop_data(task, query, permission)
    elif kind == "replay":
        fields(query, ("case_id", "kind", "events"))
        events = query["events"]
        require(type(events) is list and 1 <= len(events) <= 8, "Bounded nonempty event list required")
        require(type(permission) is list and len(permission) == len(events), "Parallel permission list required")
        for event, grant in zip(events, permission, strict=True):
            validate_pop(task, event)
            permission_shape(grant)
        history = []
        for event, grant in zip(events, permission, strict=True):
            step = pop_data(task, event, grant)
            history.append(step)
            if step["status"] != "EXECUTED":
                break
            task["state"] = clone(step["state"])
        data = {"status": "EXECUTED" if len(history) == len(events) and history[-1]["status"] == "EXECUTED" else "REFUSED",
                "steps": history, "state": clone(task["state"])}
    else:
        require(permission is None, "Permission belongs only to transition queries")
        if kind == "observe":
            fields(query, ("case_id", "kind"))
            data = {"topology": topology, "face_cycle": classify(task, topology["face_boundary"]), "observables": observations(task)}
        elif kind == "chain":
            fields(query, ("case_id", "kind", "chain"))
            data = classify(task, query["chain"])
        elif kind == "compare":
            fields(query, ("case_id", "kind", "other_state"))
            state_data(query["other_state"])
            other = clone(task)
            other["state"] = clone(query["other_state"])
            left, right = observations(task), observations(other)
            comparison = None if left["toy_mass"] is None or right["toy_mass"] is None else (
                (Fraction(right["toy_mass"]) > Fraction(left["toy_mass"])) -
                (Fraction(right["toy_mass"]) < Fraction(left["toy_mass"])))
            data = {"left": left, "right": right, "right_mass_vs_left": comparison,
                    "transition_executed": False, "state": clone(task["state"])}
        elif kind == "physics":
            fields(query, ("case_id", "kind", "claim"))
            require(query["claim"] in ("cern_higgs_boson_125_gev", "standard_model", "origin_of_inertial_mass_in_qft"),
                    "Unknown physical claim identifier")
            data = {"status": "REFUSED", "refusal": "ref<3>", "claim": query["claim"]}
        else:
            raise InvalidInput("Unknown query kind")
    return {"case_id": query["case_id"], "kind": kind, "data": data,
            "authority_effect": "None", "genesis_effect": "None", "realizes": None}


def submission(task, query, answer, permission=None):
    inputs = {"task": clone(task), "query": clone(query), "permission": clone(permission)}
    return {**inputs, "proposal": {"input_sha256": digest(inputs), "answer": clone(answer)}}


def evaluate(document):
    json_value(document)
    require(len(encoded(document)) <= MAX_BYTES, "Input byte limit")
    document = clone(document)
    fields(document, ("task", "query", "permission", "proposal"))
    proposal = document["proposal"]
    fields(proposal, ("input_sha256", "answer"))
    inputs = {key: document[key] for key in ("task", "query", "permission")}
    canonical = answer_for(**inputs)
    binding_ok = type(proposal["input_sha256"]) is str and proposal["input_sha256"] == digest(inputs)
    matches = binding_ok and encoded(proposal["answer"]) == encoded(canonical)
    return {"verdict": "MATCH" if matches else "MISMATCH", "binding_ok": binding_ok,
            "inputs": inputs, "proposal": proposal, "canonical": canonical}


def triangle_task(weight=0):
    return {"task_id": "triangle1", "vertices": ["a", "b", "c"], "edges": [["a", "b"], ["a", "c"], ["b", "c"]],
            "potential_face": {"face_id": "face1", "vertices": ["a", "b", "c"]},
            "activity_encoding": "one_potential_face_binary_activity_v1",
            "state": {"revision": 0, "face_weight": weight, "payload": {"note": "retained"}},
            "adapter": {"scheme": "linear_activity_observables_v1", "mass_scale": "1/1", "drag_scale": "1/1"}}


def pop_query(task, case_id="pop1"):
    after = clone(task["state"])
    after.update(face_weight=1, revision=after["revision"] + 1)
    return {"case_id": case_id, "kind": "pop", "event_id": "event1", "face_id": task["potential_face"]["face_id"],
            "before_state_sha256": digest(task["state"]), "after": after, "lock": complex_data(task)["face_boundary"]}


def holds(expected, actual):
    """Every expected field occurs in ``actual`` with the same canonical value."""
    if type(expected) is dict:
        return type(actual) is dict and all(key in actual and holds(value, actual[key]) for key, value in expected.items())
    return encoded(expected) == encoded(actual)


def fact_check(case_id, answer):
    facts = SOURCE_FACTS[case_id]
    return {"source_facts": facts, "verdict": "MATCH" if holds(facts, answer) else "MISMATCH"}


def demonstration_status(report):
    """DEMONSTRATED only when every exercise row shows its stated source facts."""
    return "DEMONSTRATED" if all(row["verdict"] == "MATCH" for row in report["exercises"]) else "MISMATCH"


def exercise_report():
    fixtures = [
        ("P8.1", "ask<flow<a,b,c,0>>", "ans<flow<massless,drag<0>>>", 0, {"kind": "observe"}),
        ("P8.2", "ask<pop<f0,f1>>", "ans<lock<l,f1,d>,mass<area<d>>>", 0, {"kind": "pop"}),
        ("P8.3", "ask<mass<area<d0>>,mass<area<d1>>>", "ans<comp<area<d0,0>,area<d1,1>,mass<d1_gt_d0>>>", 0,
         {"kind": "compare", "other_state": triangle_task(1)["state"]}),
        ("P8.4", "ask<prove<cern_higgs_boson_125_gev,from<pop<f0,f1>>>>", "ref<3>", 0,
         {"kind": "physics", "claim": "cern_higgs_boson_125_gev"}),
        ("DRILL8.1", "ask<simplex<a,b,c,0>>", "ans<flow<massless>>", 0, {"kind": "observe"}),
        ("DRILL8.2", "ask<pop<f0,f1>>", "ans<lock<l,f1,d>,mass<area<d>>>", 0, {"kind": "pop"}),
        ("DRILL8.3", "ask<drag<area<0>>>", "ans<drag<0>>", 0, {"kind": "observe"}),
        ("DRILL8.4", "ask<drag<area<1>>>", "ans<drag<1>>", 1, {"kind": "observe"}),
        ("DRILL8.5", "ask<claim<standard_model>>", "ref<3>", 0, {"kind": "physics", "claim": "standard_model"})]
    rows = []
    for name, source_query, source_answer, weight, partial in fixtures:
        task = triangle_task(weight)
        query = pop_query(task, name) if partial["kind"] == "pop" else {"case_id": name, **partial}
        permission = permission_for(task, query) if query["kind"] == "pop" else None
        rows.append({"id": name, "source_query": source_query, "source_answer": source_answer,
                     "task": task, "query": query, "permission": permission,
                     "computed_answer": answer_for(task, query, permission)})
    for row in rows:
        row.update(fact_check(row["id"], row["computed_answer"]))
    task = triangle_task()
    query = pop_query(task)
    unassigned = triangle_task(1)
    unassigned["adapter"] = None
    zero_mass = triangle_task(1)
    zero_mass["adapter"]["mass_scale"] = "0/1"
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "exercises": rows, "source_vocabulary": list(SOURCE_VOCABULARY),
            "source_notation": "HISTORICAL_LABELS_NOT_A_GENERAL_WIRE_PARSER",
            "controls": {"missing_permission": answer_for(task, query),
                         "repeated_pop": answer_for(task, {"case_id": "replay1", "kind": "replay", "events": [query, query]},
                                                    [permission_for(task, query), permission_for(task, query)]),
                         "missing_assignment": observations(unassigned), "active_zero_mass": observations(zero_mass)},
            "authority_effect": "None", "genesis_effect": "None", "realizes": None}


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: declared face activation and assigned toy observables.\nNo physical, metric, authenticated-authorization or Genesis derivation claim.\n").encode()}
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
