"""Quiz06: finite oriented cochains and a declared rational edge Hodge adapter."""
import argparse
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000040"
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID
# Facts each computed answer must show, transcribed from the original worksheet's source-row table.
SOURCE_FACTS = {
    "P6.1": {"nilpotent": True, "d1d0": {"values": [[0, 0, 0]]}},
    "P6.2A": {"potential": [0, 2, 5], "classification": "EXACT", "closed": True},
    "P6.2B": {"classification": "NONCLOSED", "coboundary": [1]},
    "P6.3": {"status": "PAIRED", "dual_cochain": ["1/2", "0/1", "0/1", "0/1", "0/1", "0/1"]},
    "P6.4": {"refusal": "ref<4>"},
    "DRILL6.1": {"nilpotent": True},
    "DRILL6.2": {"operator": "d0", "value": [2, 5, 3]},
    "DRILL6.3": {"operator": "d1", "value": [1]},
    "DRILL6.4": {"classification": "NONCLOSED", "coboundary": [-1]},
    "DRILL6.5": {"refusal": "ref<4>"}}
MAX_BYTES = 131072
SOURCE_VOCABULARY = ["c0<a>", "d0<c0,c1>", "d1<c1,c2>", "z<d1d0,0>",
                     "hodge<c1,dual1>", "open<c1,r1>", "ref<4>"]


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
    require(type(value) is str and re.fullmatch(r"-?(0|[1-9][0-9]{0,6})/[1-9][0-9]{0,6}", value) is not None,
            "Canonical rational string required")
    parsed = Fraction(value)
    require(abs(parsed.numerator) <= 1000000 and parsed.denominator <= 1000000, "Rational bound")
    require(qtext(parsed) == value, "Unreduced or noncanonical rational")
    return parsed


def vector(value, size):
    require(type(value) is list and len(value) == size, "Complete cochain vector required")
    return [integer(item) for item in value]


def matrix(rows, cols, values):
    require(type(rows) is int and type(cols) is int and 0 <= rows <= 96 and 0 <= cols <= 96,
            "Explicit bounded matrix dimensions required")
    require(type(values) is list and len(values) == rows, "Matrix row count")
    require(all(type(row) is list and len(row) == cols for row in values), "Rectangular matrix required")
    for row in values:
        for value in row:
            integer(value)
    return {"rows": rows, "cols": cols, "values": values}


def mv(mat, values):
    require(len(values) == mat["cols"], "Matrix-vector shape mismatch")
    return [sum(a*b for a, b in zip(row, values, strict=True)) for row in mat["values"]]


def mm(left, right):
    require(left["cols"] == right["rows"], "Matrix-product shape mismatch")
    return matrix(left["rows"], right["cols"],
                  [[sum(left["values"][i][k]*right["values"][k][j] for k in range(left["cols"]))
                    for j in range(right["cols"])] for i in range(left["rows"])])


def transpose(mat):
    return matrix(mat["cols"], mat["rows"],
                  [[mat["values"][i][j] for i in range(mat["rows"])] for j in range(mat["cols"])])


def complex_data(task):
    fields(task, ("task_id", "vertices", "edges", "faces"))
    identifier(task["task_id"])
    vertices, edges, faces = task["vertices"], task["edges"], task["faces"]
    for value, bound in ((vertices, 24), (edges, 72), (faces, 48)):
        require(type(value) is list and len(value) <= bound, "Bounded simplex list required")
    for vertex in vertices:
        identifier(vertex)
    require(len(set(vertices)) == len(vertices), "Duplicate vertex")
    for simplices, arity in ((edges, 2), (faces, 3)):
        seen = set()
        for cell in simplices:
            require(type(cell) is list and len(cell) == arity, "Simplex arity")
            for vertex in cell:
                identifier(vertex)
            require(len(set(cell)) == arity, "Repeated simplex vertex")
            require(set(cell) <= set(vertices), "Undeclared simplex vertex")
            key = tuple(sorted(cell))
            require(key not in seen, "Duplicate unoriented simplex")
            seen.add(key)
    index = {tuple(sorted(edge)): i for i, edge in enumerate(edges)}
    d0 = matrix(len(edges), len(vertices),
                [[int(v == b) - int(v == a) for v in vertices] for a, b in edges])
    rows = []
    for a, b, c in faces:
        row = [0] * len(edges)
        for u, v in ((a, b), (b, c), (c, a)):
            key = tuple(sorted((u, v)))
            require(key in index, "Declared face is missing a boundary edge")
            j = index[key]
            row[j] = 1 if edges[j] == [u, v] else -1
        rows.append(row)
    d1 = matrix(len(faces), len(edges), rows)
    product = mm(d1, d0)
    return {"d0": d0, "d1": d1, "d1d0": product,
            "nilpotent": all(value == 0 for row in product["values"] for value in row),
            "basis": {"vertices": clone(vertices), "edges": clone(edges), "faces": clone(faces)}}


def classify(task, cochain):
    data = complex_data(task)
    values = vector(cochain, len(task["edges"]))
    coboundary = mv(data["d1"], values)
    adjacency = {v: [] for v in task["vertices"]}
    for i, (a, b) in enumerate(task["edges"]):
        adjacency[a].append((b, i, 1))
        adjacency[b].append((a, i, -1))
    potentials, paths = {}, {}
    for root in task["vertices"]:
        if root in potentials:
            continue
        potentials[root], paths[root] = 0, [0] * len(values)
        pending = [root]
        while pending:
            current = pending.pop()
            for neighbor, edge, sign in adjacency[current]:
                if neighbor not in potentials:
                    potentials[neighbor] = potentials[current] + sign * values[edge]
                    paths[neighbor] = paths[current].copy()
                    paths[neighbor][edge] += sign
                    pending.append(neighbor)
    cycle = None
    for i, (a, b) in enumerate(task["edges"]):
        if potentials[b] - potentials[a] != values[i]:
            coefficients = [x-y+int(j == i) for j, (x, y) in enumerate(zip(paths[a], paths[b], strict=True))]
            cycle = {"coefficients": coefficients,
                     "boundary": mv(transpose(data["d0"]), coefficients),
                     "circulation": sum(x*y for x, y in zip(coefficients, values, strict=True))}
            break
    closed, exact = not any(coboundary), cycle is None
    return {"closed": closed, "exact": exact, "coboundary": coboundary,
            "classification": "EXACT" if exact else "CLOSED_NOT_EXACT" if closed else "NONCLOSED",
            "potential": [potentials[v] for v in task["vertices"]] if exact else None,
            "cycle_witness": cycle,
            "cohomology_obstruction": closed and not exact}


def surface_links(task):
    reports = []
    for vertex in task["vertices"]:
        neighbors = {w for edge in task["edges"] if vertex in edge for w in edge if w != vertex}
        adjacency = {w: set() for w in neighbors}
        for face in task["faces"]:
            if vertex in face:
                a, b = [w for w in face if w != vertex]
                adjacency[a].add(b)
                adjacency[b].add(a)
        seen, pending = set(), sorted(neighbors)[:1]
        while pending:
            current = pending.pop()
            if current not in seen:
                seen.add(current)
                pending.extend(adjacency[current] - seen)
        valid = len(neighbors) >= 3 and seen == neighbors and all(len(x) == 2 for x in adjacency.values())
        reports.append({"vertex": vertex, "connected_cycle": valid,
                        "degrees": {v: len(adjacency[v]) for v in sorted(neighbors)}})
    return reports


def dual_complex(task):
    data = complex_data(task)
    d0, d1 = data["d0"], data["d1"]
    links = surface_links(task)
    endpoints, bad_edges = [], []
    for e in range(len(task["edges"])):
        negative = [f for f, row in enumerate(d1["values"]) if row[e] == -1]
        positive = [f for f, row in enumerate(d1["values"]) if row[e] == 1]
        if len(negative) != 1 or len(positive) != 1:
            bad_edges.append(e)
        else:
            endpoints.append({"primal_edge": e, "tail_face": negative[0], "head_face": positive[0]})
    if not task["faces"] or bad_edges or not all(row["connected_cycle"] for row in links):
        return {"status": "REFUSED", "refusal": "ref<4>", "reason": "NOT_A_CLOSED_COHERENTLY_ORIENTED_SURFACE",
                "bad_edges": bad_edges, "vertex_links": links}
    boundary2 = matrix(len(task["edges"]), len(task["vertices"]),
                       [[-value for value in row] for row in d0["values"]])
    dual_faces = []
    for v, vertex in enumerate(task["vertices"]):
        outgoing = {}
        for e, edge in enumerate(endpoints):
            sign = boundary2["values"][e][v]
            if sign:
                start, end = edge["tail_face"], edge["head_face"]
                if sign == -1:
                    start, end = end, start
                require(start not in outgoing, "Dual face has a branched boundary")
                outgoing[start] = (end, e, sign)
        start = min(outgoing)
        current, used, steps = start, set(), []
        for _ in range(len(outgoing)):
            require(current in outgoing and current not in used, "Dual boundary is not one cycle")
            used.add(current)
            end, edge, sign = outgoing[current]
            steps.append({"edge": edge, "sign": sign, "from": current, "to": end})
            current = end
        require(current == start and len(used) == len(outgoing), "Dual boundary does not close")
        dual_faces.append({"primal_vertex": vertex, "boundary_cycle": steps})
    return {"status": "CONSTRUCTED", "vertices": [{"primal_face": f} for f in range(len(task["faces"]))],
            "edges": endpoints, "faces": dual_faces, "boundary1": d1, "boundary2": boundary2,
            "boundary_product": mm(d1, boundary2),
            "convention": "B1_dual=d1;B2_dual=-d0;dual_faces_are_oriented_polygons"}


def hodge(task, cochain, adapter):
    data = complex_data(task)
    values = vector(cochain, len(task["edges"]))
    if adapter is None:
        return {"status": "REFUSED", "refusal": "ref<4>", "reason": "FINITE_METRIC_ADAPTER_MISSING"}
    fields(adapter, ("scheme", "edge_weights"))
    require(adapter["scheme"] == "positive_diagonal_edge_v1", "Unknown finite adapter scheme")
    weights = adapter["edge_weights"]
    require(type(weights) is list and len(weights) == len(values), "One weight per declared oriented edge required")
    weights = [rational(value) for value in weights]
    require(all(value > 0 for value in weights), "Strictly positive weights required")
    dual = dual_complex(task)
    if dual["status"] != "CONSTRUCTED":
        return dual
    image = [weight*value for weight, value in zip(weights, values, strict=True)]
    inverse = [value/weight for value, weight in zip(image, weights, strict=True)]
    dual_coboundary = mv(transpose(dual["boundary2"]), image)
    return {"status": "PAIRED", "scalar_extension": "Z_TO_Q", "dual_complex": dual,
            "primal_cochain": values, "dual_cochain": [qtext(value) for value in image],
            "inverse_recovery": [qtext(value) for value in inverse],
            "weighted_self_pairing": qtext(sum((v*w for v, w in zip(values, image, strict=True)), Fraction(0))),
            "primal_coboundary": mv(data["d1"], values),
            "dual_coboundary": [qtext(value) for value in dual_coboundary],
            "metric_origin": "DECLARED_POSITIVE_RATIONAL_WEIGHTS_NOT_DERIVED_GEOMETRY",
            "continuum_bridge": "NOT_SUPPLIED"}


def answer_for(task, query):
    data = complex_data(task)
    require(type(query) is dict, "Query object required")
    kind = query.get("kind")
    shapes = {"nilpotency": (), "d0": ("cochain",), "d1": ("cochain",), "classify": ("cochain",),
              "hodge": ("cochain", "adapter"), "import": ("claim",)}
    require(type(kind) is str and kind in shapes, "Unknown query")
    fields(query, ("case_id", "kind", *shapes[kind]))
    identifier(query["case_id"])
    if kind == "nilpotency":
        return data
    if kind in ("d0", "d1"):
        operator = data[kind]
        return {"operator": kind, "matrix": operator, "value": mv(operator, vector(query["cochain"], operator["cols"]))}
    if kind == "classify":
        return classify(task, query["cochain"])
    if kind == "hodge":
        return hodge(task, query["cochain"], query["adapter"])
    require(query["claim"] in ("smooth_de_rham_cohomology_and_differential_forms", "riemannian_manifold"),
            "Unknown typed continuum claim")
    return {"refusal": "ref<4>", "claim": query["claim"], "reason": "FINITE_TO_CONTINUUM_BRIDGE_NOT_SUPPLIED",
            "authority_effect": "None"}


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


def triangle_task(filled=True):
    return {"task_id": "triangle1", "vertices": ["a", "b", "c"],
            "edges": [["a", "b"], ["a", "c"], ["b", "c"]], "faces": [["a", "b", "c"]] if filled else []}


def tetrahedron():
    return {"task_id": "tetrahedron1", "vertices": ["a", "b", "c", "d"],
            "edges": [list(pair) for pair in combinations("abcd", 2)],
            "faces": [["b", "c", "d"], ["a", "d", "c"], ["a", "b", "d"], ["a", "c", "b"]]}


def metric():
    return {"scheme": "positive_diagonal_edge_v1", "edge_weights": ["1/2", "2/1", "3/1", "4/1", "5/1", "6/1"]}


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
    triangle, sphere = triangle_task(), tetrahedron()
    exact = mv(complex_data(triangle)["d0"], [0, 2, 5])
    fixtures = [
        ("P6.1", "ask<z<d1d0>>", "ans<z<d1d0,0>>", triangle, {"kind": "nilpotency"}),
        ("P6.2A", "ask<eval<d1,c1<exact>>>", "ans<closed<c1,0>>", triangle, {"kind": "classify", "cochain": exact}),
        ("P6.2B", "ask<eval<d1,c1<nonclosed>>>", "ans<open<c1,r1>>", triangle, {"kind": "classify", "cochain": [1, 0, 0]}),
        ("P6.3", "ask<hodge<c1<ab>>>", "ans<hodge<c1<ab>,dual1<ab_star>>>", sphere, {"kind": "hodge", "cochain": [1, 0, 0, 0, 0, 0], "adapter": metric()}),
        ("P6.4", "ask<import<smooth_de_rham_cohomology,differential_forms>>", "ref<4>", triangle, {"kind": "import", "claim": "smooth_de_rham_cohomology_and_differential_forms"}),
        ("DRILL6.1", "ask<z<d1d0>>", "ans<z<d1d0,0>>", sphere, {"kind": "nilpotency"}),
        ("DRILL6.2", "ask<d0<c0>>", "ans<d0<c0,c1>>", triangle, {"kind": "d0", "cochain": [0, 2, 5]}),
        ("DRILL6.3", "ask<d1<c1>>", "ans<d1<c1,c2>>", triangle, {"kind": "d1", "cochain": [1, 0, 0]}),
        ("DRILL6.4", "ask<open<c1>>", "ans<open<c1,r1>>", triangle, {"kind": "classify", "cochain": [0, 1, 0]}),
        ("DRILL6.5", "ask<import<riemannian_manifold>>", "ref<4>", triangle, {"kind": "import", "claim": "riemannian_manifold"})]
    rows = []
    for name, source_query, source_answer, task, partial_query in fixtures:
        query = {"case_id": name, **partial_query}
        rows.append({"id": name, "source_query": source_query, "source_answer": source_answer,
                     "task": task, "query": query, "computed_answer": answer_for(task, query)})
    for row in rows:
        row.update(fact_check(row["id"], row["computed_answer"]))
    query = {"case_id": "counterexample1", "kind": "classify", "cochain": [1, 0, 0]}
    wrong = clone(classify(triangle_task(False), query["cochain"]))
    wrong["exact"] = True
    bad_orientation = clone(sphere)
    bad_orientation["faces"][0].reverse()
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "exercises": rows,
            "source_vocabulary": SOURCE_VOCABULARY, "source_notation": "HISTORICAL_LABELS_NOT_A_GENERAL_WIRE_PARSER",
            "controls": {"closed_not_exact": classify(triangle_task(False), [1, 0, 0]),
                         "missing_adapter": hodge(sphere, [1, 0, 0, 0, 0, 0], None),
                         "incoherent_surface": dual_complex(bad_orientation),
                         "exact_primal_nonclosed_dual": hodge(sphere, [-1, -1, -1, 0, 0, 0], metric()),
                         "forged_exact": evaluate(submission(triangle_task(False), query, wrong))},
            "authority_effect": "None", "genesis_effect": "None"}


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: finite cochains and a declared rational edge Hodge adapter.\nNo smooth, physical, formal-theorem or general Hodge-decomposition claim.\n").encode()}
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
