"""Scoped tests for Quiz11's finite rational Hodge pilot."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import importlib.util
from itertools import combinations, permutations, product
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "run.py"
SPEC = importlib.util.spec_from_file_location("quiz11_hodge_pilot", CODE)
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


def ref_rank(matrix):
    a = [[F(x) for x in row] for row in matrix]
    if not a:
        return 0
    rank = 0
    for col in range(len(a[0])):
        pivot = next((i for i in range(rank, len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        scalar = a[rank][col]
        a[rank] = [x / scalar for x in a[rank]]
        for i in range(len(a)):
            if i != rank:
                scalar = a[i][col]
                a[i] = [x - scalar * y for x, y in zip(a[i], a[rank], strict=True)]
        rank += 1
        if rank == len(a):
            break
    return rank


def ref_solve(matrix, rhs):
    size = len(rhs)
    a = [[F(v) for v in row] + [F(b)] for row, b in zip(matrix, rhs, strict=True)]
    row = 0
    pivots = []
    for col in range(size):
        pivot = next((i for i in range(row, size) if a[i][col]), None)
        if pivot is None:
            continue
        a[row], a[pivot] = a[pivot], a[row]
        scalar = a[row][col]
        a[row] = [v / scalar for v in a[row]]
        for i in range(size):
            if i != row:
                scalar = a[i][col]
                a[i] = [v - scalar * w for v, w in zip(a[i], a[row], strict=True)]
        pivots.append(col)
        row += 1
    assert all(any(r[:size]) or r[size] == 0 for r in a)
    result = [F(0)] * size
    for row, col in enumerate(pivots):
        result[col] = a[row][size]
    return result


def ref_cells(carrier):
    verts = carrier["vertices"]
    if carrier["mode"] == "facets":
        generators = [set(cell) for cell in carrier["facets"]] + [{v} for v in verts]

        def included(cell):
            return any(set(cell) <= gen for gen in generators)

        ceiling = 4
    else:
        edges = {frozenset(edge) for edge in carrier["edges"]}

        def included(cell):
            return all(frozenset(edge) in edges for edge in combinations(cell, 2))

        ceiling = carrier["max_dimension"]
    return [[cell for cell in combinations(verts, k + 1) if k <= ceiling and included(cell)]
            for k in range(5)]


def ref_boundary(cells, k):
    if k == 0:
        return []
    cols = cells[k] if k < 5 else []
    rows = cells[k - 1]
    return [[sum((-1) ** j for j in range(len(simplex)) if simplex[:j] + simplex[j + 1:] == face)
             for simplex in cols] for face in rows]


def ref_project(matrix, x, columns):
    normal = [[sum(F(row[i]) * row[j] for row in matrix) for j in range(columns)] for i in range(columns)]
    rhs = [sum(F(row[i]) * v for row, v in zip(matrix, x, strict=True)) for i in range(columns)]
    coeffs = ref_solve(normal, rhs)
    return [sum((F(a) * b for a, b in zip(row, coeffs, strict=True)), F(0)) for row in matrix]


def assert_math(carrier, k, x):
    request = pilot.request_for("oracle", carrier, k, x)
    report = pilot.answer_for(request)
    actual = report["data"]
    cells = ref_cells(carrier)
    assert report["bases"] == [[list(cell) for cell in group] for group in cells]
    size = len(cells[k])
    down = ref_boundary(cells, k)
    up = ref_boundary(cells, k + 1)
    exact_matrix = [[down[j][i] for j in range(len(down))] for i in range(size)]
    exact = ref_project(exact_matrix, list(map(F, x)), len(down))
    coexact = ref_project(up, list(map(F, x)), len(cells[k + 1]) if k < 4 else 0)
    harmonic = [F(v) - a - b for v, a, b in zip(x, exact, coexact, strict=True)]
    assert list(map(F, actual["exact"])) == exact
    assert list(map(F, actual["coexact"])) == coexact
    assert list(map(F, actual["harmonic"])) == harmonic
    assert [sum((F(a) * F(b) for a, b in zip(row, actual["alpha"], strict=True)), F(0))
            for row in exact_matrix] == exact
    assert [sum((F(a) * F(b) for a, b in zip(row, actual["beta"], strict=True)), F(0))
            for row in up] == coexact
    expected_lap = [[sum(F(row[i]) * row[j] for row in down)
                     + sum(F(a) * b for a, b in zip(up[i], up[j], strict=True))
                     for j in range(size)] for i in range(size)]
    assert [[F(v) for v in row] for row in actual["laplacian"]] == expected_lap
    assert actual["exact_rank"] == ref_rank(down)
    assert actual["coexact_rank"] == ref_rank(up)
    assert actual["harmonic_dimension"] == size - ref_rank(down) - ref_rank(up)
    assert actual["boundary_squared_zero"] is True
    assert actual["harmonic_residual"] == ["0"] * size
    assert actual["orthogonality"] == ["0", "0", "0"]
    assert actual["boundary"]["shape"] == [len(down), size]
    assert actual["boundary"]["columns"] == [[str(row[j]) for row in down] for j in range(size)]
    assert actual["next_boundary"]["shape"] == [size, len(cells[k + 1]) if k < 4 else 0]
    energy = sum(F(x[i]) * expected_lap[i][j] * F(x[j]) for i in range(size) for j in range(size))
    norm_down = sum(sum(F(v) * F(w) for v, w in zip(row, x, strict=True)) ** 2 for row in down)
    norm_up = sum(sum(F(up[i][j]) * F(x[i]) for i in range(size)) ** 2
                  for j in range(len(cells[k + 1]) if k < 4 else 0))
    assert energy == norm_down + norm_up >= 0
    return actual


@pytest.mark.parametrize("n,k", [(n, k) for n in range(5) for k in range(5)])
def test_full_simplices_every_degree(n, k):
    carrier = pilot.simplex(n)
    size = len(list(combinations(range(n + 1), k + 1)))
    x = [F((-1) ** i * (i + 1), i + 2) for i in range(size)]
    actual = assert_math(carrier, k, x)
    assert actual["harmonic_dimension"] == int(k == 0)


def test_all_four_vertex_graphs_and_declared_skeletons():
    edges = list(combinations("abcd", 2))
    for mask in range(64):
        present = [list(e) for i, e in enumerate(edges) if mask & (1 << i)]
        for cutoff in range(5):
            carrier = {"mode": "cliques", "vertices": list("abcd"), "edges": present, "max_dimension": cutoff}
            for k in range(3):
                size = len(ref_cells(carrier)[k])
                assert_math(carrier, k, [F(i - 2, 3) for i in range(size)])


def test_hollow_filled_and_disjoint_source_repair():
    cycle = [1, -1, 1]
    hollow = assert_math(pilot.triangle(False), 1, cycle)
    filled = assert_math(pilot.triangle(), 1, cycle)
    assert hollow["harmonic"] == ["1", "-1", "1"]
    assert hollow["coexact"] == ["0"] * 3
    assert filled["harmonic"] == ["0"] * 3
    assert filled["coexact"] == ["1", "-1", "1"]
    assert filled["laplacian"] == [["3", "0", "0"], ["0", "3", "0"], ["0", "0", "3"]]
    row = next(row for row in pilot.exercise_report()["exercises"] if row["id"] == "P11.3")
    actual = assert_math(row["request"]["complex"], 1, [1, 3, 2, 1, -1, 1])
    assert actual["exact"] == ["1", "3", "2", "0", "0", "0"]
    assert actual["harmonic"] == ["0", "0", "0", "1", "-1", "1"]
    assert actual["coexact"] == ["0"] * 6
    assert actual["coexact_rank"] == 1
    assert any(F(x) for col in actual["next_boundary"]["columns"] for x in col)


def test_triangle_grid_and_zero_harmonic_on_nontrivial_topology():
    cycle = (F(1), F(-1), F(1))
    for x in product((-1, 0, 1), repeat=3):
        factor = sum(a * b for a, b in zip(cycle, x, strict=True)) / 3
        circulation = [factor * a for a in cycle]
        for filled in (False, True):
            actual = assert_math(pilot.triangle(filled), 1, x)
            assert list(map(F, actual["coexact" if filled else "harmonic"])) == circulation
    actual = assert_math(pilot.triangle(False), 1, [1, 0, -1])
    assert actual["harmonic_dimension"] == 1
    assert actual["harmonic"] == ["0"] * 3


def test_all_114_explicit_complexes_on_four_vertices():
    edges = list(combinations("abcd", 2))
    checked = 0
    for mask in range(64):
        present = [e for i, e in enumerate(edges) if mask & (1 << i)]
        possible_faces = [f for f in combinations("abcd", 3) if all(e in present for e in combinations(f, 2))]
        for face_mask in range(1 << len(possible_faces)):
            faces = [f for i, f in enumerate(possible_faces) if face_mask & (1 << i)]
            carrier = {"mode": "facets", "vertices": list("abcd"), "facets": [list(c) for c in present + faces]}
            for k in range(5):
                size = len(ref_cells(carrier)[k])
                assert_math(carrier, k, [F(i - 1, i + 2) for i in range(size)])
            checked += 1
    assert checked == 113
    for k in range(5):
        size = len(ref_cells(pilot.simplex(3))[k])
        assert_math(pilot.simplex(3), k, [1] * size)


def test_six_vertex_four_skeleton_is_not_full_clique_complex():
    carrier = {"mode": "cliques", "vertices": list("abcdef"),
               "edges": [list(e) for e in combinations("abcdef", 2)], "max_dimension": 4}
    result = pilot.answer_for(pilot.request_for("skeleton", carrier, 4, [1] * 6))
    assert result["complex"] == {"mode": "cliques", "max_dimension": 4, "clique_dimension": 5,
                                 "declared_cutoff": 4, "truncated": True}
    assert [len(b) for b in result["bases"]] == [6, 15, 20, 15, 6]
    assert assert_math(carrier, 4, [1] * 6)["harmonic_dimension"] == 1


def test_nonorientable_projective_plane_local_boundaries():
    facets = [list(s) for s in ("012", "013", "024", "035", "045", "125", "134", "145", "234", "235")]
    carrier = {"mode": "facets", "vertices": list("012345"), "facets": facets}
    cells = ref_cells(carrier)
    assert [len(c) for c in cells[:3]] == [6, 15, 10]
    assert all(sum(set(edge) <= set(face) for face in facets) == 2 for edge in cells[1])
    for v in carrier["vertices"]:
        link = [set(face) - {v} for face in facets if v in face]
        neighbors = set().union(*link)
        assert all(sum(w in edge for edge in link) == 2 for w in neighbors)
        reached = {next(iter(neighbors))}
        for _ in neighbors:
            reached |= set().union(*(edge for edge in link if edge & reached))
        assert reached == neighbors
    # The closed connected surface has no nonzero rational top cycle; local d^2 remains zero.
    assert [assert_math(carrier, k, [1] * len(cells[k]))["harmonic_dimension"] for k in range(3)] == [1, 0, 0]
    assert ref_rank(ref_boundary(cells, 2)) == 10


def test_nonorientable_mobius_fixture():
    facets = [sorted(s) for s in ("023", "031", "245", "253", "410", "405")]
    carrier = {"mode": "facets", "vertices": list("012345"), "facets": facets}
    cells = ref_cells(carrier)
    assert [len(c) for c in cells[:3]] == [6, 12, 6]
    assert [assert_math(carrier, k, [F(i + 1, 3) for i in range(len(cells[k]))])["harmonic_dimension"]
            for k in range(3)] == [1, 1, 0]


def test_orientation_reordering_with_transported_cochains():
    original = pilot.triangle(False)
    baseline = pilot.answer_for(pilot.request_for("base", original, 1, [1, -1, 1]))["data"]
    for order in permutations(["0", "1", "2"]):
        facets = [list(e) for e in combinations(order, 2)]
        carrier = {"mode": "facets", "vertices": list(order), "facets": facets}
        old = {("0", "1"): F(1), ("0", "2"): F(-1), ("1", "2"): F(1)}
        transported = [old.get(e, -old.get(e[::-1], F(0))) for e in combinations(order, 2)]
        actual = assert_math(carrier, 1, transported)
        assert actual["harmonic_dimension"] == baseline["harmonic_dimension"] == 1
        assert actual["exact"] == ["0"] * 3


@pytest.mark.parametrize("k", range(5))
def test_empty_complex_spaces(k):
    actual = assert_math({"mode": "facets", "vertices": [], "facets": []}, k, [])
    assert actual["dimension"] == actual["harmonic_dimension"] == 0
    assert actual["laplacian"] == []


@pytest.mark.parametrize("n,k", [(n, k) for n in range(5) for k in range(-1, n + 1)])
def test_complement_map_all_degrees(n, k):
    carrier = pilot.simplex(n)
    cells = ref_cells(carrier)
    source = [()] if k == -1 else cells[k]
    x = [F(i + 1, i + 2) for i in range(len(source))]
    request = {"case_id": "star", "kind": "complement", "complex": carrier, "degree": k, "cochain": list(map(str, x))}
    first = pilot.answer_for(request)["data"]
    target = n - k - 1
    assert first["target_degree"] == target
    assert first["geometric_dual_claim"] is False
    target_cells = [()] if target == -1 else cells[target]
    expected = []
    for other in target_cells:
        cell = tuple(v for v in carrier["vertices"] if v not in other)
        sequence = tuple(map(int, cell + other))
        sign = (-1) ** sum(a > b for i, a in enumerate(sequence) for b in sequence[i + 1:])
        expected.append(sign * x[source.index(cell)])
    assert list(map(F, first["value"])) == expected
    request.update(degree=target, cochain=first["value"])
    second = pilot.answer_for(request)["data"]
    sign = (-1) ** ((k + 1) * (n - k))
    assert first["double_sign"] == sign
    assert list(map(F, second["value"])) == [sign * v for v in x]


def test_complement_source_sign_counterexample_and_incomplete_refusal():
    request = {"case_id": "star", "kind": "complement", "complex": pilot.triangle(),
               "degree": 1, "cochain": ["1", "0", "0"]}
    first = pilot.answer_for(request)["data"]
    assert first["value"] == ["0", "0", "1"]
    assert first["double_sign"] == 1 != (-1) ** (1 * (2 - 1))
    request["complex"] = pilot.triangle(False)
    with pytest.raises(pilot.InvalidInput, match="full simplex"):
        pilot.answer_for(request)
    request.update(complex=pilot.simplex(0), degree=1, cochain=[])
    with pytest.raises(pilot.InvalidInput, match="Complement degree"):
        pilot.answer_for(request)
    with pytest.raises(pilot.InvalidInput, match="dimension"):
        pilot.complement(pilot.complex_data(pilot.simplex(0))[1], ("0",), -1, ())


@pytest.mark.parametrize("bad", ["-0", "1/1", "2/4", "1/0", "+1", "01", "1.0", "", "1000001", "1/1000001", "a", True, 1])
def test_rational_boundaries(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.rational(bad)


@pytest.mark.parametrize("value", ["0", "-1", "2/3", "-5/7", "1000000", "1/1000000"])
def test_valid_rationals(value):
    assert str(pilot.rational(value)) == value


@pytest.mark.parametrize("change", [
    {"mode": "implicit"}, {"vertices": "012"}, {"vertices": list("0123456")},
    {"vertices": ["0", "0"]}, {"vertices": ["$"]}, {"vertices": [True]}, {"vertices": ["a" * 17]},
    {"facets": "012"}, {"facets": [[]]}, {"facets": [["0", "0"]]},
    {"facets": [["1", "0"]]}, {"facets": [["0", "z"]]}, {"facets": [[[]]]},
    {"facets": [["0", "1"], ["0", "1"]]}, {"facets": [["0"]] * 65},
    {"facets": [["0", "1", "2", "3", "4", "5"]]}, {"weight": 1},
])
def test_invalid_complexes(change):
    carrier = pilot.triangle()
    carrier.update(change)
    with pytest.raises(pilot.InvalidInput):
        pilot.complex_data(carrier)


@pytest.mark.parametrize("change", [{"edges": [["0"]]}, {"edges": [["0", "1", "2"]]},
                                     {"max_dimension": True}, {"max_dimension": -1}, {"max_dimension": 5}])
def test_invalid_clique_complexes(change):
    carrier = {"mode": "cliques", "vertices": list("012"), "edges": [["0", "1"]], "max_dimension": 2}
    carrier.update(change)
    with pytest.raises(pilot.InvalidInput):
        pilot.complex_data(carrier)


def test_clique_cutoff_zero_and_boundary_missing_face_fail_closed():
    carrier = {"mode": "cliques", "vertices": list("012"), "edges": [["0", "1"]], "max_dimension": 0}
    result = pilot.answer_for(pilot.request_for("zero", carrier, 0, [1, 2, 3]))
    assert result["data"]["harmonic"] == ["1", "2", "3"]
    assert result["complex"]["truncated"] is True
    assert result["bases"][1] == []
    vertices, bases, _ = pilot.complex_data(pilot.triangle())
    incomplete = list(bases)
    incomplete[1] = ()
    with pytest.raises(pilot.InvalidInput, match="Missing declared boundary"):
        pilot.boundary(tuple(incomplete), 2)
    with pytest.raises(pilot.InvalidInput, match="shape"):
        pilot.linear(((F(1),),), (), 1)
    with pytest.raises(ValueError):
        pilot.dot((F(1),), ())


@pytest.mark.parametrize("change", [{"kind": "unknown"}, {"case_id": ""}, {"case_id": True},
                                    {"degree": True}, {"degree": -1}, {"degree": 5},
                                    {"cochain": [1, 2, 3]}, {"cochain": []},
                                    {"cochain": "123"}, {"extra": None}])
def test_invalid_requests(change):
    request = pilot.request_for("valid", pilot.triangle(), 1, [1, 2, 3])
    request.update(change)
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(request)


def test_continuum_refusal_is_typed_not_language_detection():
    for claim in ("smooth_differential_form_wedge_product_manifold", "riemannian_metric_tensor"):
        result = pilot.answer_for({"case_id": "import", "kind": "continuum", "claim": claim})
        assert result["data"] == {"status": "REFUSED", "refusal": "ref<4>", "claim": claim, "adapter": "UNBOUND"}
        assert result["authority_effect"] == result["genesis_effect"] == "None"
        assert result["realizes"] is None
    with pytest.raises(pilot.InvalidInput, match="Unknown continuum"):
        pilot.answer_for({"case_id": "import", "kind": "continuum", "claim": "arbitrary language"})


def test_fixture_accounting_and_companion_exact_values():
    report = pilot.exercise_report()
    assert [r["id"] for r in report["exercises"]] == [f"P11.{i}" for i in range(1, 5)] + [f"DRILL11.{i}" for i in range(1, 9)]
    assert len(report["exercises"]) == 12
    assert len(report["source_vocabulary"]) == 9
    assert "z<bound2_bound1,0>" in report["source_vocabulary"]
    for row in report["exercises"]:
        assert row["computed_answer"] == pilot.answer_for(row["request"])
    full = report["controls"]["companion_filled"]["data"]
    hollow = report["controls"]["companion_hollow"]["data"]
    assert full["exact"] == hollow["exact"] == ["1/3", "8/3", "7/3"]
    assert full["coexact"] == hollow["harmonic"] == ["2/3", "-2/3", "2/3"]
    assert full["harmonic"] == hollow["coexact"] == ["0"] * 3


def valid_document():
    req = pilot.request_for("check", pilot.triangle(), 1, [1, 2, 3])
    return pilot.submission(req, pilot.answer_for(req))


@pytest.mark.parametrize("target", ["digest", "exact", "coexact", "harmonic", "alpha", "beta", "laplacian",
                                    "rank", "basis", "authority", "type"])
def test_proposal_corruption(target):
    document = valid_document()
    answer = document["proposal"]["answer"]
    if target == "digest":
        document["proposal"]["input_sha256"] = "0" * 64
    elif target in ("exact", "coexact", "harmonic", "alpha", "beta"):
        answer["data"][target][0] = "123"
    elif target == "laplacian":
        answer["data"]["laplacian"][0][0] = "4"
    elif target == "rank":
        answer["data"]["harmonic_dimension"] = 1
    elif target == "basis":
        answer["bases"][1][0].reverse()
    elif target == "authority":
        answer["authority_effect"] = "Promoted"
    else:
        answer["data"]["dimension"] = True
    assert pilot.evaluate(document)["verdict"] == "MISMATCH"


def test_request_binding_snapshot_and_success():
    document = valid_document()
    frozen = deepcopy(document)
    result = pilot.evaluate(document)
    assert result["verdict"] == "MATCH" and result["binding_ok"] is True
    document["request"]["cochain"][0] = "9"
    assert result["request"] == frozen["request"]
    assert pilot.evaluate(document)["verdict"] == "MISMATCH"
    for obj in (None, [], {"request": {}}, {"request": frozen["request"], "proposal": {}}):
        with pytest.raises(pilot.InvalidInput):
            pilot.evaluate(obj)


@pytest.mark.parametrize("bad", [1.5, float("nan"), float("inf"), (1,), {1: "x"}, "\u00e9", "\n",
                                 "x" * 2049, [0] * 257, {str(i): 0 for i in range(65)}, 10**19])
def test_json_value_boundaries(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.json_value(bad)


def test_depth_bytes_and_decoder():
    deep = 0
    for _ in range(17):
        deep = [deep]
    with pytest.raises(pilot.InvalidInput, match="depth"):
        pilot.json_value(deep)
    for raw in (b"", b" " * (pilot.MAX_BYTES + 1), b'{"x":1,"x":2}', b"NaN", b"Infinity", b"not_json", b"\xff"):
        with pytest.raises((ValueError, UnicodeError)):
            pilot.decode(raw)
    assert pilot.decode(b'{"x":[null,true,false,1,"a"]}') == {"x": [None, True, False, 1, "a"]}
    with pytest.raises(pilot.InvalidInput, match="Request object"):
        pilot.answer_for([])
    huge = {str(i): ["a" * 2048] * 2 for i in range(40)}
    with pytest.raises(pilot.InvalidInput, match="byte limit"):
        pilot.answer_for(huge)
    with pytest.raises(pilot.InvalidInput, match="byte limit"):
        pilot.evaluate(huge)


def cli(tmp_path, raw=None, code=CODE):
    output = tmp_path / "output"
    args = [sys.executable, str(code), "--output-dir", str(output)]
    if raw is not None:
        source = tmp_path / "input.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(raw)
        args.extend(["--input", str(source)])
    result = subprocess.run(args, text=True, capture_output=True, timeout=30, check=False,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert not result.stderr, result.stderr
    return result.returncode, json.loads(result.stdout)


def inspect_run(reply, raw, code=CODE):
    folder = Path(reply["output"])
    assert (folder / "input.bin").read_bytes() == raw
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert receipt["code_sha256"] == hashlib.sha256(code.read_bytes()).hexdigest()
    assert receipt["model_calls"] == 0 and receipt["cost_usd"] == "0"
    for name, digest in receipt["artifact_sha256"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
    return json.loads((folder / "result.json").read_bytes())


@pytest.mark.parametrize("mode", ["default", "match", "mismatch", "invalid", "continuum", "complement", "empty"])
def test_real_cli(tmp_path, mode):
    document = valid_document()
    if mode == "mismatch":
        document["proposal"]["answer"]["data"]["exact"][0] = "99"
    elif mode == "invalid":
        document["request"]["degree"] = True
    elif mode == "continuum":
        req = {"case_id": "refusal", "kind": "continuum", "claim": "riemannian_metric_tensor"}
        document = pilot.submission(req, pilot.answer_for(req))
    elif mode == "complement":
        req = {"case_id": "star", "kind": "complement", "complex": pilot.simplex(1), "degree": 0, "cochain": ["1", "2"]}
        document = pilot.submission(req, pilot.answer_for(req))
    elif mode == "empty":
        req = pilot.request_for("empty", {"mode": "facets", "vertices": [], "facets": []}, 4, [])
        document = pilot.submission(req, pilot.answer_for(req))
    raw = None if mode == "default" else b" \n" + json.dumps(document, indent=2).encode() + b"\n"
    status, reply = cli(tmp_path, raw)
    assert status == (1 if mode in ("mismatch", "invalid") else 0)
    assert reply["status"] == {"default": "DEMONSTRATED", "mismatch": "MISMATCH", "invalid": "REJECTED"}.get(mode, "MATCH")
    inspect_run(reply, raw if raw is not None else pilot.encoded({"kind": "built_in_exercises"}))


@pytest.mark.parametrize("raw", [b"{", b'{"x":1,"x":2}', b"NaN", b"\xff", b"x" * (131072 + 1)],
                         ids=["syntax", "duplicate", "nonfinite", "utf8", "oversize"])
def test_real_cli_malformed_bytes(tmp_path, raw):
    code, reply = cli(tmp_path, raw)
    assert code == 2 and reply["status"] == "REFUSED"
    assert not (tmp_path / "output").exists()


def test_main_in_process_and_io_failures(tmp_path, capsys):
    assert pilot.main(["--output-dir", str(tmp_path / "runs")]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"
    document = valid_document()
    file = tmp_path / "input.json"
    file.write_bytes(pilot.encoded(document))
    assert pilot.main(["--input", str(file), "--output-dir", str(tmp_path / "runs")]) == 0
    capsys.readouterr()
    document["request"]["degree"] = -1
    file.write_bytes(pilot.encoded(document))
    assert pilot.main(["--input", str(file), "--output-dir", str(tmp_path / "runs")]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "REJECTED"
    assert pilot.main(["--input", str(tmp_path / "missing")]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    blocked = tmp_path / "not_a_directory"
    blocked.write_text("preserve", encoding="utf-8")
    assert pilot.main(["--output-dir", str(blocked)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert blocked.read_text() == "preserve"


MUTATIONS = (
    ("boundary_sign", "Fraction((-1) ** omitted)", "Fraction(1)", "math"),
    ("lose_coexact", "coexact_columns = boundary(bases, k + 1)", "coexact_columns = ()", "math"),
    ("bad_harmonic", "a - b - c for a, b, c", "a - b + c for a, b, c", "math"),
    ("bad_projection", "factor = dot(u, x) / dot(u, u)", "factor = dot(u, x)", "math"),
    ("lose_preimage", "preimages.append(tuple(factor * a for a in witness))", "preimages.append(tuple(Fraction(0) for a in witness))", "math"),
    ("bad_rank", '"harmonic_dimension": len(x) - exact_rank - coexact_rank', '"harmonic_dimension": len(x) - exact_rank', "math"),
    ("lose_laplacian_term", "for col in exact_columns + coexact_columns", "for col in exact_columns", "math"),
    ("dependent_columns", "if any(u):", "if False:", "math"),
    ("fill_hollow", "for cell in entries:\n            for size", "for cell in [tuple(range(len(vertices)))]:\n            for size", "hollow"),
    ("ignore_cutoff", "if size <= cutoff + 1:", "if size <= 5:", "cutoff"),
    ("star_sign", "(-1) ** inversions * value", "value", "star"),
    ("star_degree", '"target_degree": target_degree,', '"target_degree": target_degree + 1,', "star"),
    ("star_double_sign", '"double_sign": (-1) ** ((k + 1) * (n - k))', '"double_sign": (-1) ** (k * (n - k))', "star"),
    ("ignore_binding", "matches = binding_ok and encoded(proposal", "matches = encoded(proposal", "binding"),
    ("ignore_answer", 'matches = binding_ok and encoded(proposal["answer"]) == encoded(canonical)', "matches = binding_ok", "answer"),
    ("authority_promotion", '"authority_effect": "None", "genesis_effect": "None", "realizes": None}', '"authority_effect": "Promoted", "genesis_effect": "None", "realizes": None}', "authority"),
    ("continuum_accept", '"status": "REFUSED", "refusal": "ref<4>"', '"status": "COMPUTED", "refusal": None', "continuum"),
    ("rational_canonical", 'require(str(result) == value, "Unreduced or noncanonical rational")',
     'require(True, "Unreduced or noncanonical rational")', "noncanonical"),
)


def mutation_document(mode):
    document = valid_document()
    if mode == "hollow":
        req = pilot.request_for("hollow", pilot.triangle(False), 1, [1, -1, 1])
        document = pilot.submission(req, pilot.answer_for(req))
    elif mode == "cutoff":
        carrier = {"mode": "cliques", "vertices": list("012"), "edges": [["0", "1"], ["0", "2"], ["1", "2"]], "max_dimension": 1}
        req = pilot.request_for("cutoff", carrier, 1, [1, -1, 1])
        document = pilot.submission(req, pilot.answer_for(req))
    elif mode == "star":
        req = {"case_id": "star", "kind": "complement", "complex": pilot.triangle(), "degree": 1, "cochain": ["1", "2", "3"]}
        document = pilot.submission(req, pilot.answer_for(req))
    elif mode == "binding":
        document["proposal"]["input_sha256"] = "0" * 64
    elif mode == "answer":
        document["proposal"]["answer"]["data"]["exact"][0] = "99"
    elif mode == "continuum":
        req = {"case_id": "import", "kind": "continuum", "claim": "riemannian_metric_tensor"}
        document = pilot.submission(req, pilot.answer_for(req))
    elif mode == "noncanonical":
        document["request"]["cochain"][0] = "2/2"
        document["proposal"]["input_sha256"] = pilot.digest(document["request"])
    return document


def test_compiled_cli_mutations(tmp_path):
    source = CODE.read_text(encoding="utf-8")
    records = []
    for name, old, new, mode in MUTATIONS:
        # One selected authority field is mutated; the second belongs only to the default report.
        count = source.count(old)
        assert count == (2 if name == "authority_promotion" else 1), (name, count)
        altered = source.replace(old, new, 1)
        compile(altered, name, "exec")
        folder = tmp_path / name
        folder.mkdir()
        code = folder / "run.py"
        code.write_text(altered, encoding="utf-8")
        document = mutation_document(mode)
        if mode == "noncanonical":
            with pytest.raises(pilot.InvalidInput):
                pilot.evaluate(document)
            baseline_status = "REJECTED"
        else:
            baseline_status = pilot.evaluate(document)["verdict"]
        exit_code, reply = cli(folder, pilot.encoded(document), code)
        assert reply["status"] != baseline_status, (name, reply)
        assert reply["status"] in ("MATCH", "MISMATCH", "REJECTED"), (name, reply)
        inspect_run(reply, pilot.encoded(document), code)
        records.append({"mutation": name, "compiled": True, "caught": True, "old": old, "new": new,
                        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                        "mutant_sha256": hashlib.sha256(altered.encode()).hexdigest(),
                        "baseline_status": baseline_status, "mutant_status": reply["status"],
                        "exit_code": exit_code, "document": document})
    assert CODE.read_text(encoding="utf-8") == source
    destination = os.environ.get("PFP_MUTATION_REPORT")
    if destination:
        Path(destination).write_text(json.dumps({"count": len(records), "mutations": records}, indent=2), encoding="utf-8")


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(CODE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(CODE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"


def test_default_output_root_is_beside_the_pilot():
    assert pilot.OUTPUT_ROOT == CODE.resolve().parent.parent / "pilot_output" / pilot.PILOT_ID


def test_fact_subset_comparison_is_exact():
    assert pilot.holds({"a": {"b": 1}}, {"a": {"b": 1, "c": 2}, "d": 3})
    assert not pilot.holds({"a": {"b": 1}}, {"a": 1})
    assert not pilot.holds({"a": 1}, {})
    assert not pilot.holds({"a": True}, {"a": 1})


def test_demonstration_fails_when_a_row_mismatches(tmp_path, monkeypatch, capsys):
    report = pilot.exercise_report()
    assert pilot.demonstration_status(report) == "DEMONSTRATED"
    monkeypatch.setitem(pilot.SOURCE_FACTS, "P11.2", {"data": {"harmonic_dimension": 0}})
    mismatched = pilot.exercise_report()
    assert [row["id"] for row in mismatched["exercises"] if row["verdict"] == "MISMATCH"] == ["P11.2"]
    assert pilot.main(["--output-dir", str(tmp_path / "mismatch")]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "MISMATCH"
    assert json.loads((Path(output["output"]) / "receipt.json").read_bytes())["status"] == "MISMATCH"
