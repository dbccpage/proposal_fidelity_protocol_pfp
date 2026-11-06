"""Quiz13: bounded clique complexes and exact rational simplicial homology."""
import argparse
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000044"
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID
MAX_BYTES = 131072
MAX_VERTICES = 6
SOURCE_VOCABULARY = ("graph<edges>", "f_vec<f0,f1,f2,f3,f4>", "euler<chi_int>",
                     "betti<b0,b1,b2,b3,b4>", "z<euler_defect,0>", "ref<1>", "ref<2>", "ref<4>")


class InvalidInput(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Exact object fields required")


def json_value(value, depth=0):
    require(depth <= 16, "JSON depth bound")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        require(abs(value) <= 10**18, "JSON integer bound")
    elif type(value) is str:
        require(len(value) <= 2048 and all(32 <= ord(c) < 127 for c in value), "Bounded printable ASCII required")
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



def integer(value, lower, upper, label):
    require(type(value) is int and lower <= value <= upper, label)
    return value


def vertex(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-z]", value), "Single glyph vertex required")
    return value


def vertex_list(value):
    require(type(value) is list and len(value) <= MAX_VERTICES, "At most six vertices")
    nodes = tuple(vertex(v) for v in value)
    require(len(set(nodes)) == len(nodes), "Repeated vertex")
    return nodes


def graph_input(value):
    require(type(value) is dict, "Graph object required")
    encoding = value.get("encoding")
    require(encoding in ("edges", "glyph"), "Graph encoding")
    cutoff = integer(value.get("max_dimension"), 0, 4, "Dimension cutoff is 0..4")
    if encoding == "edges":
        fields(value, ("encoding", "vertices", "edges", "max_dimension"))
        nodes = vertex_list(value["vertices"])
        require(type(value["edges"]) is list and len(value["edges"]) <= 15, "At most fifteen edges")
        pairs = []
        for edge in value["edges"]:
            require(type(edge) is list and len(edge) == 2, "Edge pair required")
            a, b = (vertex(v) for v in edge)
            require(a in nodes and b in nodes, "Undeclared endpoint")
            pairs.append((a, b))
    else:
        fields(value, ("encoding", "text", "max_dimension"))
        raw = value["text"]
        require(type(raw) is str and 0 < len(raw) <= 128, "Bounded nonempty glyph graph")
        pairs, declared, inferred = [], set(), set()
        for item in raw.split("<>"):
            require(re.fullmatch(r"[0-9a-z]([<>][0-9a-z])?", item), "Unweighted glyph subset required")
            if len(item) == 1:
                require(item not in declared, "Repeated vertex declaration")
                declared.add(item)
                inferred.add(item)
            else:
                pairs.append((item[0], item[2]))
                inferred.update((item[0], item[2]))
        nodes = vertex_list(sorted(inferred))
    edges = set()
    for a, b in pairs:
        require(a != b, "Loops not allowed")
        edge = tuple(sorted((a, b)))
        require(edge not in edges, "Repeated undirected edge")
        edges.add(edge)
    return tuple(sorted(nodes)), frozenset(edges), cutoff


def simplex_bases(nodes, edges, cutoff):
    all_cliques = [tuple(c for c in combinations(nodes, size)
                         if all(pair in edges for pair in combinations(c, 2)))
                   for size in range(1, len(nodes) + 1)]
    full_dimension = max((i for i, basis in enumerate(all_cliques) if basis), default=-1)
    bases = [all_cliques[k] if k <= cutoff and k < len(all_cliques) else () for k in range(5)]
    return bases, full_dimension


def boundary(rows, columns):
    matrix = [[0 for _ in columns] for _ in rows]
    lookup = {simplex: i for i, simplex in enumerate(rows)}
    for j, simplex in enumerate(columns):
        for i in range(len(simplex)):
            face = simplex[:i] + simplex[i + 1:]
            if face in lookup:
                matrix[lookup[face]][j] = (-1) ** i
    return {"rows": len(rows), "cols": len(columns), "entries": matrix}


def reduction(matrix):
    rows, cols = matrix["rows"], matrix["cols"]
    reduced = [[Fraction(x) for x in row] for row in matrix["entries"]]
    transform = [[Fraction(i == j) for j in range(rows)] for i in range(rows)]
    pivots = []
    for col in range(cols):
        pivot = next((i for i in range(len(pivots), rows) if reduced[i][col]), None)
        if pivot is None:
            continue
        row = len(pivots)
        reduced[row], reduced[pivot] = reduced[pivot], reduced[row]
        transform[row], transform[pivot] = transform[pivot], transform[row]
        divisor = reduced[row][col]
        reduced[row] = [x / divisor for x in reduced[row]]
        transform[row] = [x / divisor for x in transform[row]]
        for i in range(rows):
            if i != row and reduced[i][col]:
                factor = reduced[i][col]
                reduced[i] = [a - factor * b for a, b in zip(reduced[i], reduced[row], strict=True)]
                transform[i] = [a - factor * b for a, b in zip(transform[i], transform[row], strict=True)]
        pivots.append(col)
    return {"rank": len(pivots), "pivot_columns": pivots,
            "rref": [[str(v) for v in row] for row in reduced],
            "row_transform": [[str(v) for v in row] for row in transform]}


def product(left, right):
    require(left["cols"] == right["rows"], "Matrix shape mismatch")
    return {"rows": left["rows"], "cols": right["cols"],
            "entries": [[sum(left["entries"][i][k] * right["entries"][k][j]
                             for k in range(left["cols"])) for j in range(right["cols"])]
                        for i in range(left["rows"])]}


def analyse(nodes, edges, cutoff):
    bases, full_dimension = simplex_bases(nodes, edges, cutoff)
    maps = [boundary((), bases[0])] + [boundary(bases[k - 1], bases[k]) for k in range(1, 5)]
    maps.append(boundary(bases[4], ()))
    reductions = [reduction(matrix) for matrix in maps]
    ranks = [r["rank"] for r in reductions]
    counts = [len(b) for b in bases]
    betti = [counts[k] - ranks[k] - ranks[k + 1] for k in range(5)]
    composites = [product(maps[k - 1], maps[k]) for k in range(1, 6)]
    nilpotent = all(v == 0 for matrix in composites for row in matrix["entries"] for v in row)
    require(nilpotent and all(b >= 0 for b in betti), "Invalid chain complex")
    chi = sum((-1) ** k * f for k, f in enumerate(counts))
    betti_sum = sum((-1) ** k * b for k, b in enumerate(betti))
    return {"vertices": list(nodes), "edges": [list(e) for e in sorted(edges)],
            "max_dimension": cutoff, "full_clique_dimension": full_dimension,
            "selected_dimension": max((k for k, b in enumerate(bases) if b), default=-1),
            "truncated": full_dimension > cutoff,
            "coefficient_field": "Q", "homology": "ordinary_unreduced",
            "bases": [[list(s) for s in b] for b in bases], "f_vector": counts,
            "boundaries": maps, "rank_witnesses": reductions, "boundary_ranks": ranks,
            "boundary_composites": composites, "boundary_squared_zero": nilpotent,
            "betti": betti, "euler": chi, "betti_sum": betti_sum, "euler_defect": chi - betti_sum}


def answer_for(request):
    json_value(request)
    require(len(encoded(request)) <= MAX_BYTES, "Input byte limit")
    require(type(request) is dict, "Request object required")
    kinds = {"analyse": ("graph",), "clique": ("graph", "vertices"),
             "check_betti": ("graph", "betti"), "claim": ("claim",)}
    kind = request.get("kind")
    require(type(kind) is str and kind in kinds, "Unknown query kind")
    fields(request, ("case_id", "kind") + kinds[kind])
    require(type(request["case_id"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", request["case_id"]),
            "Bounded case identifier required")
    if kind == "claim":
        require(request["claim"] in ("infinite_dimensional_complex", "nonfinite_cw_complex"), "Unknown typed claim")
        data = {"status": "REFUSED", "refusal": "ref<4>", "claim": request["claim"], "adapter": "UNBOUND"}
    else:
        nodes, edges, cutoff = graph_input(request["graph"])
        if kind == "clique":
            vertices = tuple(sorted(vertex_list(request["vertices"])))
            require(len(vertices) >= 1, "Nonempty simplex query")
            missing_vertices = [v for v in vertices if v not in nodes]
            missing_edges = [list(pair) for pair in combinations(vertices, 2) if pair not in edges]
            complete = not missing_vertices and not missing_edges
            above = len(vertices) - 1 > cutoff
            included = complete and not above
            data = {"status": "COMPUTED" if included else "REFUSED",
                    "complete_in_graph": complete, "included_in_complex": included, "above_cutoff": above,
                    "missing_vertices": missing_vertices, "missing_edges": missing_edges, "vertices": list(vertices)}
            if not included:
                data["refusal"] = "ref<1>"
                data["reason"] = "Missing graph data" if not complete else "Outside declared dimension cutoff"
        else:
            result = analyse(nodes, edges, cutoff)
            if kind == "analyse":
                data = {"status": "COMPUTED", "complex": result}
            else:
                proposed = request["betti"]
                require(type(proposed) is list and len(proposed) == 5, "Five Betti entries required")
                proposed = [integer(b, 0, 64, "Betti entry is 0..64") for b in proposed]
                equal = proposed == result["betti"]
                data = {"status": "COMPUTED" if equal else "REFUSED", "actual_betti": result["betti"],
                        "proposed_betti": proposed, "euler": result["euler"],
                        "proposed_euler": sum((-1) ** k * b for k, b in enumerate(proposed)),
                        "matches_betti": equal, "coefficient_field": "Q"}
                if not equal:
                    data["refusal"] = "ref<2>"
    return {"case_id": request["case_id"], "kind": kind, "data": data,
            "authority_effect": "None", "genesis_effect": "None", "realizes": None}


def submission(request, answer):
    request = clone(request)
    return {"request": request, "proposal": {"input_sha256": digest(request), "answer": clone(answer)}}


def evaluate(document):
    json_value(document)
    require(len(encoded(document)) <= MAX_BYTES, "Input byte limit")
    document = clone(document)
    fields(document, ("request", "proposal"))
    proposal = document["proposal"]
    fields(proposal, ("input_sha256", "answer"))
    canonical = answer_for(document["request"])
    binding_ok = type(proposal["input_sha256"]) is str and proposal["input_sha256"] == digest(document["request"])
    matches = binding_ok and encoded(proposal["answer"]) == encoded(canonical)
    return {"verdict": "MATCH" if matches else "MISMATCH", "binding_ok": binding_ok,
            "request": document["request"], "proposal": proposal, "canonical": canonical}



def graph_request(case="complex", n=4, cutoff=4, edges=None):
    vertices = [str(i) for i in range(n)]
    pairs = list(combinations(vertices, 2)) if edges is None else edges
    return {"case_id": case, "kind": "analyse",
            "graph": {"encoding": "edges", "vertices": vertices, "edges": [list(p) for p in pairs],
                      "max_dimension": cutoff}}


def exercise_report():
    tetra = "0>1<>0>2<>0>3<>1>2<>1>3<>2>3"
    octa = [p for p in combinations("012345", 2) if p not in (("0", "1"), ("2", "3"), ("4", "5"))]
    missing = graph_request("P13.3", 3, edges=[("0", "1"), ("1", "2")])
    missing.update(kind="clique", vertices=["0", "1", "2"])
    fixtures = [
        ("P13.1", "ask<f_vector<0>1<>0>2<>0>3<>1>2<>1>3<>2>3>>",
         "ans<f_vec<4,6,4,1,0>,euler<1>,betti<1,0,0,0,0>>",
         {"case_id": "P13.1", "kind": "analyse", "graph": {"encoding": "glyph", "text": tetra, "max_dimension": 4}}),
        ("P13.2", "ask<eval<euler_poincare,octahedron>>",
         "ans<euler<2>,betti_sum<2>,z<euler_defect,0>>", graph_request("P13.2", 6, edges=octa)),
        ("P13.3", "ask<clique_face<0,1,2>>", "ref<1>", missing),
        ("DRILL13.1", "ask<f_vec<0>1>>", "ans<f_vec<2,1,0,0,0>,euler<1>>", graph_request("DRILL13.1", 2)),
        ("DRILL13.2", "ask<f_vec<0>1<>0>2<>1>2>>", "ans<f_vec<3,3,1,0,0>,euler<1>>", graph_request("DRILL13.2", 3)),
        ("DRILL13.3", "ask<f_vec<tetrahedron>>", "ans<f_vec<4,6,4,1,0>,euler<1>>", graph_request("DRILL13.3")),
        ("DRILL13.4", "ask<f_vec<4_simplex>>", "ans<f_vec<5,10,10,5,1>,euler<1>>", graph_request("DRILL13.4", 5)),
        ("DRILL13.5", "ask<clique<incomplete_edge>>", "ref<1>", dict(missing, case_id="DRILL13.5")),
        ("DRILL13.6", "ask<eval<euler_poincare,tetrahedron>>", "ans<z<euler_defect,0>>", graph_request("DRILL13.6"))]
    false_betti = graph_request("false_betti")
    false_betti.update(kind="check_betti", betti=[1, 1, 1, 0, 0])
    controls = [graph_request("empty", 0), graph_request("isolates", 3, edges=[]),
                graph_request("hollow_triangle", 3, 1), graph_request("hollow_tetrahedron", 4, 2),
                graph_request("K6_cutoff4", 6), false_betti,
                {"case_id": "nonfinite", "kind": "claim", "claim": "nonfinite_cw_complex"}]
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM",
            "exercises": [{"id": name, "source_query": query, "source_answer": answer,
                           "request": request, "computed_answer": answer_for(request)}
                          for name, query, answer, request in fixtures],
            "controls": [answer_for(request) for request in controls],
            "source_vocabulary": list(SOURCE_VOCABULARY),
            "source_notation": "HISTORICAL_QUERY_LABELS_WITH_SEPARATE_UNWEIGHTED_GLYPH_GRAPH_ADAPTER",
            "authority_effect": "None", "genesis_effect": "None", "realizes": None}


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: exact finite rational clique-complex homology.\n"
                                "No integral torsion, nonfinite topology, formal or Genesis derivation claim.\n").encode()}
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
            raw, report, status = encoded({"kind": "built_in_exercises"}), exercise_report(), "DEMONSTRATED"
        folder = write_run(args.output_dir, report, raw, status)
    except (ValueError, TypeError, OSError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder.resolve())}, ensure_ascii=True))
    return 1 if status in ("MISMATCH", "REJECTED") else 0


if __name__ == "__main__":
    sys.exit(main())
