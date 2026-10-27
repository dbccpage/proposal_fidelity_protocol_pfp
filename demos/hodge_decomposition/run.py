"""Quiz11: exact finite unweighted Hodge decomposition and a complement-face map."""
import argparse
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

PILOT_ID = "pilot_0000042"
OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID
# Facts each computed answer must show, transcribed from the original worksheet's row table and source answers.
SOURCE_FACTS = {
    "P11.1": {"data": {"boundary_squared_zero": True}},
    "P11.2": {"data": {"harmonic": ["1", "-1", "1"], "harmonic_dimension": 1}},
    "P11.3": {"data": {"coexact": ["0", "0", "0", "0", "0", "0"], "harmonic_dimension": 1}},
    "P11.4": {"data": {"refusal": "ref<4>"}},
    **{f"DRILL11.{n + 1}": {"data": {"status": "COMPUTED", "boundary_squared_zero": True,
                                     "boundary": {"shape": [n + 1 if n else 0, 1]}}} for n in range(5)},
    "DRILL11.6": {"data": {"boundary_squared_zero": True}},
    "DRILL11.7": {"data": {"harmonic": ["1", "-1", "1"], "harmonic_dimension": 1}},
    "DRILL11.8": {"data": {"refusal": "ref<4>"}}}
MAX_BYTES = 131072
SOURCE_VOCABULARY = ("k_simplex<k,edges>", "bound<k,sigma_k>", "z<bound2_bound1,0>",
                     "laplacian<k,form_k>", "harmonic<form_k,0>",
                     "decomp<form_k,exact,coexact,harmonic>", "ref<1>", "ref<2>", "ref<4>")


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


def degree(value, lower=0):
    require(type(value) is int and lower <= value <= 4, "Degree outside declared range")
    return value


def rational(value):
    require(type(value) is str and re.fullmatch(r"-?(0|[1-9][0-9]{0,6})(/[1-9][0-9]{0,6})?", value) is not None,
            "Canonical rational string required")
    result = Fraction(value)
    require(abs(result.numerator) <= 1000000 and result.denominator <= 1000000, "Rational bound")
    require(str(result) == value, "Unreduced or noncanonical rational")
    return result


def vector(value, size):
    require(type(value) is list and len(value) == size, "Cochain dimension mismatch")
    return tuple(rational(item) for item in value)


def complex_data(raw):
    require(type(raw) is dict and raw.get("mode") in ("facets", "cliques"), "Declared complex mode required")
    mode = raw["mode"]
    fields(raw, ("mode", "vertices", "facets") if mode == "facets"
           else ("mode", "vertices", "edges", "max_dimension"))
    vertices = raw["vertices"]
    require(type(vertices) is list and len(vertices) <= 6, "At most six vertices")
    require(all(type(v) is str and re.fullmatch(r"[a-zA-Z0-9]{1,16}", v) for v in vertices),
            "Bounded alphanumeric vertex labels required")
    require(len(set(vertices)) == len(vertices), "Duplicate vertex")
    index = {v: i for i, v in enumerate(vertices)}
    cells = {(i,) for i in range(len(vertices))}
    declared = raw["facets"] if mode == "facets" else raw["edges"]
    require(type(declared) is list and len(declared) <= 64, "Bounded cell list required")
    entries = []
    for cell in declared:
        require(type(cell) is list and 1 <= len(cell) <= 5, "Nonempty cell of dimension at most four required")
        require(all(type(v) is str and v in index for v in cell), "Unknown cell vertex")
        item = tuple(index[v] for v in cell)
        require(tuple(sorted(set(item))) == item, "Cells must follow the declared vertex order")
        require(item not in entries, "Duplicate declared cell")
        if mode == "cliques":
            require(len(item) == 2, "Graph edges need two endpoints")
        entries.append(item)
    graph_dimension = None
    cutoff = None
    if mode == "facets":
        for cell in entries:
            for size in range(1, len(cell) + 1):
                cells.update(combinations(cell, size))
    else:
        cutoff = degree(raw["max_dimension"])
        edges = set(entries)
        graph_dimension = -1
        for size in range(1, len(vertices) + 1):
            for cell in combinations(range(len(vertices)), size):
                if all(edge in edges for edge in combinations(cell, 2)):
                    graph_dimension = size - 1
                    if size <= cutoff + 1:
                        cells.add(cell)
    bases = tuple(tuple(sorted(cell for cell in cells if len(cell) == k + 1)) for k in range(5))
    metadata = {"mode": mode, "max_dimension": max((k for k, basis in enumerate(bases) if basis), default=-1),
                "clique_dimension": graph_dimension, "declared_cutoff": cutoff,
                "truncated": graph_dimension is not None and graph_dimension > cutoff}
    return tuple(vertices), bases, metadata


def boundary(bases, k):
    """Columns of B_k, including B_0: Q^vertices -> the zero space."""
    source = bases[k] if k < 5 else ()
    target = bases[k - 1] if k else ()
    positions = {face: i for i, face in enumerate(target)}
    columns = []
    for simplex in source:
        col = [Fraction(0)] * len(target)
        if k:
            for omitted in range(k + 1):
                face = simplex[:omitted] + simplex[omitted + 1:]
                require(face in positions, "Missing declared boundary face")
                col[positions[face]] = Fraction((-1) ** omitted)
        columns.append(tuple(col))
    return tuple(columns)


def dot(a, b):
    return sum((x * y for x, y in zip(a, b, strict=True)), Fraction(0))


def linear(columns, coefficients, rows):
    require(len(columns) == len(coefficients), "Linear combination shape mismatch")
    return tuple(sum((col[i] * coeff for col, coeff in zip(columns, coefficients, strict=True)), Fraction(0))
                 for i in range(rows))


def projection(columns, x):
    """Exact Gram-Schmidt image projection with an explicit preimage witness."""
    orthogonal = []
    for j, col in enumerate(columns):
        u = tuple(col)
        witness = tuple(Fraction(int(i == j)) for i in range(len(columns)))
        for prior, preimage in orthogonal:
            factor = dot(prior, u) / dot(prior, prior)
            u = tuple(a - factor * b for a, b in zip(u, prior, strict=True))
            witness = tuple(a - factor * b for a, b in zip(witness, preimage, strict=True))
        if any(u):
            orthogonal.append((u, witness))
    parts = []
    preimages = []
    for u, witness in orthogonal:
        factor = dot(u, x) / dot(u, u)
        parts.append(tuple(factor * a for a in u))
        preimages.append(tuple(factor * a for a in witness))
    projected = tuple(sum((part[i] for part in parts), Fraction(0)) for i in range(len(x)))
    coefficients = tuple(sum((part[i] for part in preimages), Fraction(0)) for i in range(len(columns)))
    return projected, coefficients, len(orthogonal)


def operator_columns(bases, k):
    down = boundary(bases, k)
    previous = len(bases[k - 1]) if k else 0
    exact_columns = tuple(tuple(col[i] for col in down) for i in range(previous))
    coexact_columns = boundary(bases, k + 1)
    return down, exact_columns, coexact_columns


def laplacian(exact_columns, coexact_columns, size):
    return tuple(tuple(sum((col[i] * col[j] for col in exact_columns + coexact_columns), Fraction(0))
                       for j in range(size)) for i in range(size))


def texts(values):
    return [str(value) for value in values]


def matrix_record(columns, rows):
    return {"shape": [rows, len(columns)], "columns": [texts(col) for col in columns]}


def analyse(bases, k, x):
    down, exact_columns, coexact_columns = operator_columns(bases, k)
    exact, alpha, exact_rank = projection(exact_columns, x)
    coexact, beta, coexact_rank = projection(coexact_columns, x)
    harmonic = tuple(a - b - c for a, b, c in zip(x, exact, coexact, strict=True))
    lap = laplacian(exact_columns, coexact_columns, len(x))
    nilpotent = all(not any(linear(boundary(bases, j - 1), col, len(bases[j - 2])))
                     for j in range(2, 6) for col in boundary(bases, j))
    return {"status": "COMPUTED", "dimension": len(x), "exact": texts(exact), "coexact": texts(coexact),
            "harmonic": texts(harmonic), "alpha": texts(alpha), "beta": texts(beta),
            "exact_rank": exact_rank, "coexact_rank": coexact_rank,
            "harmonic_dimension": len(x) - exact_rank - coexact_rank,
            "boundary": matrix_record(down, len(bases[k - 1]) if k else 0),
            "next_boundary": matrix_record(coexact_columns, len(x)),
            "laplacian": [texts(row) for row in lap], "boundary_squared_zero": nilpotent,
            "harmonic_residual": texts(tuple(dot(row, harmonic) for row in lap)),
            "orthogonality": texts((dot(exact, coexact), dot(exact, harmonic), dot(coexact, harmonic)))}


def complement(bases, vertices, k, x):
    n = len(vertices) - 1
    expected = tuple(tuple(combinations(range(n + 1), j + 1)) for j in range(5))
    require(0 <= n <= 4 and bases == expected, "Complement map requires one full simplex")
    require(-1 <= k <= n, "Complement degree outside simplex")
    source = ((),) if k == -1 else bases[k]
    require(len(x) == len(source), "Complement input dimension mismatch")
    target_degree = n - k - 1
    target = ((),) if target_degree == -1 else bases[target_degree]
    positions = {cell: i for i, cell in enumerate(target)}
    output = [Fraction(0)] * len(target)
    for cell, value in zip(source, x, strict=True):
        other = tuple(i for i in range(n + 1) if i not in cell)
        sequence = cell + other
        inversions = sum(sequence[i] > sequence[j] for i in range(n + 1) for j in range(i + 1, n + 1))
        output[positions[other]] = (-1) ** inversions * value
    return {"status": "COMPUTED", "map": "unit_complement_face", "target_degree": target_degree,
            "target_basis": [[vertices[i] for i in cell] for cell in target], "value": texts(output),
            "double_sign": (-1) ** ((k + 1) * (n - k)),
            "geometric_dual_claim": False}


def answer_for(request):
    json_value(request)
    require(len(encoded(request)) <= MAX_BYTES, "Input byte limit")
    require(type(request) is dict, "Request object required")
    kind = request.get("kind")
    if kind == "continuum":
        fields(request, ("case_id", "kind", "claim"))
        require(request["claim"] in ("smooth_differential_form_wedge_product_manifold", "riemannian_metric_tensor"),
                "Unknown continuum claim")
        data = {"status": "REFUSED", "refusal": "ref<4>", "claim": request["claim"], "adapter": "UNBOUND"}
        extra = {}
    else:
        require(kind in ("analyse", "complement"), "Unknown query kind")
        fields(request, ("case_id", "kind", "complex", "degree", "cochain"))
        vertices, bases, metadata = complex_data(request["complex"])
        k = degree(request["degree"], -1 if kind == "complement" else 0)
        size = 1 if k == -1 else len(bases[k])
        x = vector(request["cochain"], size)
        data = analyse(bases, k, x) if kind == "analyse" else complement(bases, vertices, k, x)
        extra = {"complex": metadata, "bases": [[[vertices[i] for i in cell] for cell in basis] for basis in bases]}
    case_id = request["case_id"]
    require(type(case_id) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", case_id), "Bounded case identifier required")
    return {"case_id": case_id, "kind": kind, **extra, "data": data,
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


def simplex(n):
    vertices = [str(i) for i in range(n + 1)]
    return {"mode": "facets", "vertices": vertices, "facets": [vertices]}


def triangle(filled=True):
    return simplex(2) if filled else {"mode": "facets", "vertices": ["0", "1", "2"],
                                      "facets": [["0", "1"], ["0", "2"], ["1", "2"]]}


def request_for(case_id, carrier, k, x):
    return {"case_id": case_id, "kind": "analyse", "complex": carrier, "degree": k, "cochain": texts(x)}


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
    filled = triangle()
    hollow = triangle(False)
    disjoint = {"mode": "facets", "vertices": [str(i) for i in range(6)],
                "facets": [["0", "1", "2"], ["3", "4"], ["3", "5"], ["4", "5"]]}
    fixtures = [
        ("P11.1", "ask<eval<bound_sq,2_simplex<0>1<>0>2<>1>2>>>", "ans<z<bound1_bound2,0>>",
         request_for("P11.1", filled, 2, [1])),
        ("P11.2", "ask<eval<laplacian<1>,form<0>1+1>2-0>2>>>", "ans<harmonic<form,0>>",
         request_for("P11.2", hollow, 1, [1, -1, 1])),
        ("P11.3", "ask<decomp<1,form>>", "ans<decomp<1,exact<d0_alpha>,coexact<0>,harmonic<h>>>",
         request_for("P11.3", disjoint, 1, [1, 3, 2, 1, -1, 1])),
        ("P11.4", "ask<import<smooth_differential_form,wedge_product,manifold>>", "ref<4>",
         {"case_id": "P11.4", "kind": "continuum", "claim": "smooth_differential_form_wedge_product_manifold"})]
    for n in range(5):
        graph = "<>".join(f"{i}>{j}" for i, j in combinations(range(n + 1), 2))
        response = "ans<clique<0,verts<0>,edges<>>>" if n == 0 else f"ans<clique<{n},edges<{graph}>>>"
        case = f"DRILL11.{n + 1}"
        fixtures.append((case, f"ask<simplex<{n}>>", response, request_for(case, simplex(n), n, [1])))
    fixtures.extend([
        ("DRILL11.6", "ask<eval<bound_sq,simplex<2>>>", "ans<z<bound1_bound2,0>>",
         request_for("DRILL11.6", filled, 2, [1])),
        ("DRILL11.7", "ask<harmonic<cycle_1>>", "ans<harmonic<cycle_1,0>>",
         request_for("DRILL11.7", hollow, 1, [1, -1, 1])),
        ("DRILL11.8", "ask<import<riemannian_metric_tensor>>", "ref<4>",
         {"case_id": "DRILL11.8", "kind": "continuum", "claim": "riemannian_metric_tensor"})])
    rows = [{"id": name, "source_query": query, "source_answer": answer, "request": request,
             "computed_answer": answer_for(request)} for name, query, answer, request in fixtures]
    for row in rows:
        row.update(fact_check(row["id"], row["computed_answer"]))
    controls = {label: answer_for(request_for(label, carrier, 1, [1, 2, 3]))
                for label, carrier in (("companion_filled", filled), ("companion_hollow", hollow))}
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "exercises": rows, "controls": controls,
            "source_vocabulary": list(SOURCE_VOCABULARY),
            "source_notation": "HISTORICAL_LABELS_NOT_A_GENERAL_WIRE_PARSER",
            "authority_effect": "None", "genesis_effect": "None", "realizes": None}


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw), raw


def write_run(output, report, raw_input, status):
    folder = output / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    artifacts = {"input.bin": raw_input, "result.json": encoded(report),
                 "summary.md": (f"# {PILOT_ID}\n\n{status}: exact finite unweighted Hodge calculations.\n"
                                "No geometric dual, continuum, physical or Genesis derivation claim.\n").encode()}
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
