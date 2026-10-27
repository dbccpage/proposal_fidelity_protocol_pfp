"""Quiz05: finite intrinsic triangle metrics and local vertex angle defects.

Offline, standard-library teaching model; no higher-dimensional or physics claim.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000039"
MAX_BYTES = 131072
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID
# Facts each computed answer must show, transcribed from the original worksheet's source-row table.
SOURCE_FACTS = {
    "P5.1": {"status": "INCOMPLETE_DECLARATION"},
    "P5.2": {"classification": "ZERO", "pi_multiple": "0/1"},
    "P5.3": {"classification": "POSITIVE", "pi_multiple": "1/3"},
    "P5.4": {"refusal": "ref<3>", "claim": "einstein_field_equations"},
    "DRILL5.1": {"status": "VALID_EDGE_ONLY", "length_squared": "2/1"},
    "DRILL5.2": {"label": "r0", "status": "SUPPLIED_LABEL_GEOMETRY_UNVERIFIED"},
    "DRILL5.3": {"label": "r1", "status": "SUPPLIED_LABEL_GEOMETRY_UNVERIFIED"},
    "DRILL5.4": {"refusal": "ref<3>", "claim": "general_relativity"},
    "DRILL5.5": {"refusal": "ref<3>", "claim": "spacetime_emergence"}}
SOURCE_VOCABULARY = ["s0<a>", "edge<ab,l2>", "face<abc,a1>", "def<hinge<ab>,r1>",
                     "flat<r0>", "curv<r1>", "oracle<phys,ae0>", "ref<3>"]


class InvalidInput(ValueError):
    """The bounded teaching input contract was not met."""


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
        require(len(value) <= 128, "List bound")
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
    require(type(value) is str and re.fullmatch(r"-?(0|[1-9][0-9]{0,6})/[1-9][0-9]{0,6}", value) is not None, "Canonical rational string required")
    parsed = Fraction(value)
    require(abs(parsed.numerator) <= 1000000 and parsed.denominator <= 1000000, "Rational bound")
    require(qtext(parsed) == value, "Unreduced or noncanonical rational")
    return parsed


def simplex(value, size):
    require(type(value) is list and len(value) == size, "Simplex arity")
    for vertex in value:
        identifier(vertex)
    require(len(set(value)) == size, "Repeated simplex vertex")
    return tuple(sorted(value))


def presentation(task):
    fields(task, ("task_id", "vertices", "edges", "faces"))
    identifier(task["task_id"])
    vertices = task["vertices"]
    require(type(vertices) is list and len(vertices) <= 32, "Vertex list bound")
    for vertex in vertices:
        identifier(vertex)
    require(len(set(vertices)) == len(vertices), "Duplicate vertex")
    require(type(task["edges"]) is list and len(task["edges"]) <= 96, "Edge list bound")
    require(type(task["faces"]) is list and len(task["faces"]) <= 64, "Face list bound")
    edges, faces = {}, {}
    for row in task["edges"]:
        fields(row, ("vertices", "length_squared"))
        key = simplex(row["vertices"], 2)
        require(key not in edges, "Duplicate unoriented edge")
        length = rational(row["length_squared"])
        require(length > 0, "Squared edge length must be positive")
        edges[key] = length
    for row in task["faces"]:
        fields(row, ("vertices", "area_squared"))
        key = simplex(row["vertices"], 3)
        require(key not in faces, "Duplicate unoriented face")
        area = None if row["area_squared"] is None else rational(row["area_squared"])
        require(area is None or area > 0, "Supplied squared area must be positive")
        faces[key] = area
    return set(vertices), edges, faces


def angle(x, y, z):
    """Exact unsigned corner angle from adjacent squared lengths x,y."""
    require(x > 0 and y > 0 and z > 0, "Positive corner metric required")
    numerator = x + y - z
    radicand = 4 * x * y
    require(numerator * numerator < radicand, "Nondegenerate corner required")
    cosine_squared = numerator * numerator / radicand
    elementary = {Fraction(0): Fraction(1, 2), Fraction(1, 4): Fraction(1, 3),
                  Fraction(1, 2): Fraction(1, 4), Fraction(3, 4): Fraction(1, 6)}
    multiple = elementary.get(cosine_squared)
    if multiple is not None and numerator < 0:
        multiple = 1 - multiple
    return {"cosine_sign": 0 if numerator == 0 else 1 if numerator > 0 else -1,
            "cosine_squared": qtext(cosine_squared),
            "pi_multiple": None if multiple is None else qtext(multiple),
            "meaning": "arccos(sign*sqrt(cosine_squared)) in (0,pi)"}


def triangle(x, y, z):
    require(x > 0 and y > 0 and z > 0, "Positive triangle metric required")
    discriminant = 4 * x * y - (x + y - z) ** 2
    if discriminant <= 0:
        return {"status": "DEGENERATE" if discriminant == 0 else "INVALID_TRIANGLE",
                "area_squared": None, "angles": None}
    return {"status": "VALID_TRIANGLE", "area_squared": qtext(discriminant / 16),
            "angles": [angle(x, y, z), angle(x, z, y), angle(y, z, x)]}


def geometry(task):
    vertices, edges, faces = presentation(task)
    missing_vertices = sorted(set().union(*map(set, edges), *map(set, faces)) - vertices)
    needed_edges = set(pair for face in faces for pair in combinations(face, 2))
    missing_edges = sorted(needed_edges - set(edges))
    triangles, invalid = [], []
    for face, supplied in sorted(faces.items()):
        if any(pair not in edges for pair in combinations(face, 2)):
            continue
        a, b, c = face
        result = triangle(edges[(a, b)], edges[(a, c)], edges[(b, c)])
        consistent = supplied is None or (result["area_squared"] is not None and supplied == Fraction(result["area_squared"]))
        if result["status"] != "VALID_TRIANGLE" or not consistent:
            invalid.append(list(face))
        triangles.append({"vertices": list(face), **result, "supplied_area_consistent": consistent})
    status = "INCOMPLETE_DECLARATION" if missing_vertices or missing_edges else "INVALID_METRIC" if invalid else "COMPLETE_METRIC_COMPLEX"
    return {"status": status, "missing_vertices": missing_vertices, "missing_edges": [list(e) for e in missing_edges],
            "invalid_faces": invalid, "triangles": triangles, "surface_topology": "NOT_CHECKED",
            "global_embedding": "NOT_CHECKED"}


def vertex_link(vertices, edges, faces, vertex):
    require(vertex in vertices, "Queried vertex is not declared")
    neighbors = {other for edge in edges if vertex in edge for other in edge if other != vertex}
    adjacency = {other: set() for other in neighbors}
    for face in faces:
        if vertex in face:
            a, b = (other for other in face if other != vertex)
            adjacency[a].add(b)
            adjacency[b].add(a)
    seen, pending = set(), list(neighbors)[:1]
    while pending:
        current = pending.pop()
        if current not in seen:
            seen.add(current)
            pending.extend(adjacency[current] - seen)
    connected = bool(neighbors) and seen == neighbors
    degrees = [len(adjacency[v]) for v in sorted(neighbors)]
    kind = "NON_SURFACE"
    if connected and len(neighbors) >= 3 and all(degree == 2 for degree in degrees):
        kind = "INTERIOR_CYCLE"
    elif connected and len(neighbors) >= 2 and degrees.count(1) == 2 and all(degree in (1, 2) for degree in degrees):
        kind = "BOUNDARY_PATH"
    return {"kind": kind, "connected": connected, "degrees": {v: len(adjacency[v]) for v in sorted(neighbors)}}


def vertex_defect(task, vertex):
    identifier(vertex)
    report = geometry(task)
    require(report["status"] == "COMPLETE_METRIC_COMPLEX", "Complete valid metric required for vertex query")
    vertices, edges, faces = presentation(task)
    link = vertex_link(vertices, edges, faces, vertex)
    base = {"vertex": vertex, "link": link, "quantity": None, "classification": "UNDEFINED",
            "pi_multiple": None, "expression": None, "global_flatness": "NOT_INFERRED"}
    if link["kind"] == "NON_SURFACE":
        return {**base, "status": "NON_SURFACE_VERTEX", "refusal": "ref<2>"}
    angles = []
    for face in sorted(faces):
        if vertex in face:
            a, b = (other for other in face if other != vertex)
            angles.append(angle(edges[tuple(sorted((vertex, a)))], edges[tuple(sorted((vertex, b)))], edges[tuple(sorted((a, b)))]))
    turns = 2 if link["kind"] == "INTERIOR_CYCLE" else 1
    quantity = "INTERIOR_ANGLE_DEFECT" if turns == 2 else "BOUNDARY_TURNING"
    known = all(value["pi_multiple"] is not None for value in angles)
    deficit = Fraction(turns) - sum(Fraction(value["pi_multiple"]) for value in angles) if known else None
    classification = "UNKNOWN" if deficit is None else "ZERO" if deficit == 0 else "POSITIVE" if deficit > 0 else "NEGATIVE"
    return {**base, "status": "COMPUTED_LOCAL" if known else "EXACT_EXPRESSION_UNRESOLVED", "refusal": None,
            "quantity": quantity, "classification": classification,
            "pi_multiple": None if deficit is None else qtext(deficit),
            "expression": {"pi_coefficient": turns, "subtract_angles": angles}}


def completion(task, proposed, original_sha256):
    old_vertices, old_edges, old_faces = presentation(task)
    new_vertices, new_edges, new_faces = presentation(proposed)
    bound = original_sha256 == digest(task)
    preserves = old_vertices <= new_vertices and all(new_edges.get(e) == value for e, value in old_edges.items())
    preserves = preserves and all(face in new_faces and (value is None or new_faces[face] == value) for face, value in old_faces.items())
    report = geometry(proposed)
    accepted = bound and preserves and task["task_id"] != proposed["task_id"] and report["status"] == "COMPLETE_METRIC_COMPLEX"
    return {"accepted": accepted, "refusal": None if accepted else "ref<5>",
            "original_sha256": digest(task), "completion_sha256": digest(proposed),
            "binding_checked": bound, "supplied_data_preserved": preserves,
            "completion_geometry": report, "meaning": "SUPPLIED_COMPLETION_WITNESS_NOT_AUTOMATIC_ADMISSION",
            "authority_effect": "None", "genesis_effect": "None"}


def answer_for(task, query):
    vertices, edges, faces = presentation(task)
    require(type(query) is dict, "Query object required")
    kind = query.get("kind")
    shapes = {"geometry": (), "vertex": ("vertex",), "edge": ("vertices",), "label": ("hinge", "label"),
              "complete": ("completion", "original_sha256"), "physics": ("claim",), "global_from_vertex": ("vertex",)}
    require(type(kind) is str and kind in shapes, "Unknown query")
    fields(query, ("kind", *shapes[kind]))
    if kind == "geometry":
        return geometry(task)
    if kind in ("vertex", "global_from_vertex"):
        local = vertex_defect(task, query["vertex"])
        return local if kind == "vertex" else {"refusal": "ref<2>", "reason": "LOCAL_RESULT_NOT_GLOBAL_CERTIFICATE", "local": local}
    if kind == "edge":
        key = simplex(query["vertices"], 2)
        require(key in edges and set(key) <= vertices, "Complete queried edge required")
        return {"status": "VALID_EDGE_ONLY", "vertices": list(key), "length_squared": qtext(edges[key]), "surface_geometry": "NOT_INFERRED"}
    if kind == "label":
        hinge = simplex(query["hinge"], 2)
        require(query["label"] in ("r0", "r1"), "Unknown historical deficit label")
        return {"status": "SUPPLIED_LABEL_GEOMETRY_UNVERIFIED", "hinge": list(hinge), "label": query["label"],
                "curvature": "NOT_MEASURED", "hinge_note": "EDGE_HINGE_NOT_A_COMPUTED_2D_VERTEX"}
    if kind == "complete":
        return completion(task, query["completion"], query["original_sha256"])
    require(query["claim"] in ("einstein_field_equations", "general_relativity", "spacetime_emergence"), "Unknown typed physics claim")
    return {"refusal": "ref<3>", "reason": "PHYSICAL_DERIVATION_NOT_SUPPLIED", "claim": query["claim"], "authority_effect": "None"}


def submission(task, query, answer):
    return {"task": task, "query": query, "proposal": {"problem_sha256": digest({"task": task, "query": query}), "answer": answer}}


def evaluate(document):
    fields(document, ("task", "query", "proposal"))
    json_value(document)
    require(len(encoded(document)) <= MAX_BYTES, "Submission exceeds byte limit")
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


def fan(count, rim_squared="1/1", boundary=False):
    require(type(count) is int and 1 <= count <= 12 and (boundary or count >= 3), "Bounded fan count")
    require(type(boundary) is bool, "Boundary flag must be boolean")
    rational(rim_squared)
    neighbors = [f"v{i}" for i in range(count + int(boundary))]
    edges = [{"vertices": ["v", n], "length_squared": "1/1"} for n in neighbors]
    faces = []
    for index in range(count):
        a, b = neighbors[index], neighbors[(index + 1) % len(neighbors)]
        edges.append({"vertices": [a, b], "length_squared": rim_squared})
        faces.append({"vertices": ["v", a, b], "area_squared": None})
    return {"task_id": "fan1", "vertices": ["v", *neighbors], "edges": edges, "faces": faces}


def declaration(complete=False):
    return {"task_id": "completion1" if complete else "partial1", "vertices": ["a", "b", "c"] if complete else ["a"],
            "edges": [{"vertices": ["a", "b"], "length_squared": "4/1"}] + ([
                {"vertices": ["a", "c"], "length_squared": "4/1"}, {"vertices": ["b", "c"], "length_squared": "8/1"}] if complete else []),
            "faces": [{"vertices": ["a", "b", "c"], "area_squared": "4/1"}]}


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
    partial, complete = declaration(), declaration(True)
    segment = {"task_id": "segment1", "vertices": ["a", "b"], "edges": [{"vertices": ["a", "b"], "length_squared": "2/1"}], "faces": []}
    fixtures = [
        ("P5.1", "ask<regge<s0<a>,edge<ab,l4>,face<abc,a2>>>", "ans<regge<s0<a>,edge<ab,l4>,face<abc,a2>,valid>>", partial, {"kind": "geometry"}),
        ("P5.2", "ask<def<hinge<v>,angles<6_times_pi_over_3>>>", "ans<def<hinge<v>,r0>,flat<r0>>", fan(6), {"kind": "vertex", "vertex": "v"}),
        ("P5.3", "ask<def<hinge<v>,angles<5_times_pi_over_3>>>", "ans<def<hinge<v>,r1>,curv<r1>>", fan(5), {"kind": "vertex", "vertex": "v"}),
        ("P5.4", "ask<prove<einstein_field_equations,from<def<hinge<ab>,r1>>>>", "ref<3>", partial, {"kind": "physics", "claim": "einstein_field_equations"}),
        ("DRILL5.1", "ask<edge<ab,l2>>", "ans<edge<ab,l2>>", segment, {"kind": "edge", "vertices": ["a", "b"]}),
        ("DRILL5.2", "ask<def<hinge<ab>,r0>>", "ans<flat<r0>>", partial, {"kind": "label", "hinge": ["a", "b"], "label": "r0"}),
        ("DRILL5.3", "ask<def<hinge<ab>,r1>>", "ans<curv<r1>>", partial, {"kind": "label", "hinge": ["a", "b"], "label": "r1"}),
        ("DRILL5.4", "ask<claim<general_relativity>>", "ref<3>", partial, {"kind": "physics", "claim": "general_relativity"}),
        ("DRILL5.5", "ask<claim<spacetime_emergence>>", "ref<3>", partial, {"kind": "physics", "claim": "spacetime_emergence"})]
    rows = [{"id": name, "source_query": printed_query, "source_answer": printed_answer,
             "task": task, "query": query, "computed_answer": answer_for(task, query)}
            for name, printed_query, printed_answer, task, query in fixtures]
    for row in rows:
        row.update(fact_check(row["id"], row["computed_answer"]))
    symbolic = fan(4)
    for index, edge in enumerate(symbolic["edges"][4:]):
        edge["length_squared"] = "1/2" if index % 2 == 0 else "7/2"
    positive = fan(5)
    query = {"kind": "vertex", "vertex": "v"}
    forged = clone(vertex_defect(positive, "v"))
    forged["classification"], forged["pi_multiple"] = "ZERO", "0/1"
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "exercises": rows,
            "source_vocabulary": SOURCE_VOCABULARY, "source_notation": "HISTORICAL_NOT_A_GENERAL_WIRE_PARSER",
            "completion_witness": completion(partial, complete, digest(partial)),
            "controls": {"negative": vertex_defect(fan(7), "v"), "boundary": vertex_defect(fan(3, boundary=True), "v"),
                         "symbolic": vertex_defect(symbolic, "v"), "local_not_global": answer_for(fan(6), {"kind": "global_from_vertex", "vertex": "v"}),
                         "forged_flat": evaluate(submission(positive, query, forged))},
            "authority_effect": "None", "genesis_effect": "None"}


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: finite triangle metrics and local vertex defects.\nNo higher-dimensional, physical, formal-theorem or global-authority claim.\n").encode()}
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

