"""Scoped exact-minor, signed-boundary, CLI and compiled-mutation tests for Quiz13."""
from fractions import Fraction as F
import hashlib
import importlib.util
from itertools import combinations
import json
from math import comb
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

CODE = Path(os.environ.get("PFP_PILOT_RUN_FILE", Path(__file__).resolve().parents[2] / "run.py")).resolve()
spec = importlib.util.spec_from_file_location("quiz13_exact_clique_homology", CODE)
pilot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot
spec.loader.exec_module(pilot)


def determinant(matrix):
    if not matrix:
        return F(1)
    return sum((-1) ** j * matrix[0][j] *
               determinant([row[:j] + row[j + 1:] for row in matrix[1:]]) for j in range(len(matrix)))


def minor_rank(matrix):
    for size in range(min(matrix["rows"], matrix["cols"]), 0, -1):
        for rows in combinations(range(matrix["rows"]), size):
            for columns in combinations(range(matrix["cols"]), size):
                if determinant([[F(matrix["entries"][i][j]) for j in columns] for i in rows]):
                    return size
    return 0


def orthogonal_rank(rows):
    independent = []
    for row in rows:
        residual = [F(x) for x in row]
        for basis in independent:
            factor = sum(a * b for a, b in zip(residual, basis, strict=True)) / sum(b * b for b in basis)
            residual = [a - factor * b for a, b in zip(residual, basis, strict=True)]
        if any(residual):
            independent.append(residual)
    return len(independent)


def components(nodes, edges):
    pending, count = set(nodes), 0
    while pending:
        reached = {pending.pop()}
        while True:
            added = {v for a, b in edges for u, v in ((a, b), (b, a)) if u in reached and v not in reached}
            if not added:
                break
            reached.update(added)
        pending.difference_update(reached)
        count += 1
    return count


def check_witnesses(result, use_minors=False):
    counts = result["f_vector"]
    for degree, (matrix, witness) in enumerate(zip(result["boundaries"], result["rank_witnesses"], strict=True)):
        rows = counts[degree - 1] if degree > 0 else 0
        cols = counts[degree] if degree < 5 else 0
        assert (matrix["rows"], matrix["cols"]) == (rows, cols)
        assert len(matrix["entries"]) == rows and all(len(r) == cols for r in matrix["entries"])
        original = matrix["entries"]
        for i in range(rows):
            for j in range(cols):
                face, simplex = result["bases"][degree - 1][i], result["bases"][degree][j]
                expected = sum((-1) ** k for k in range(len(simplex)) if simplex[:k] + simplex[k + 1:] == face)
                assert original[i][j] == expected
        transform = [[F(x) for x in row] for row in witness["row_transform"]]
        reduced = [[F(x) for x in row] for row in witness["rref"]]
        assert len(transform) == rows and all(len(r) == rows for r in transform)
        assert orthogonal_rank(transform) == rows
        assert len(reduced) == rows and all(len(r) == cols for r in reduced)
        assert [[sum(transform[i][k] * original[k][j] for k in range(rows))
                 for j in range(cols)] for i in range(rows)] == reduced
        pivots = witness["pivot_columns"]
        assert pivots == sorted(set(pivots))
        assert witness["rank"] == len(pivots) == sum(any(row) for row in reduced)
        for i, pivot in enumerate(pivots):
            assert all(v == 0 for v in reduced[i][:pivot])
            assert [row[pivot] for row in reduced] == [int(j == i) for j in range(rows)]
        assert all(not any(row) for row in reduced[len(pivots):])
        if use_minors:
            assert witness["rank"] == minor_rank(matrix)
        else:
            assert witness["rank"] == orthogonal_rank(original)
    for k, composite in enumerate(result["boundary_composites"], 1):
        left, right = result["boundaries"][k - 1:k + 1]
        assert composite["rows"] == left["rows"] and composite["cols"] == right["cols"]
        expected = [[sum(left["entries"][i][h] * right["entries"][h][j] for h in range(left["cols"]))
                     for j in range(right["cols"])] for i in range(left["rows"])]
        assert composite["entries"] == expected and all(v == 0 for row in expected for v in row)
    assert result["boundary_squared_zero"] is True
    ranks = [w["rank"] for w in result["rank_witnesses"]]
    assert result["boundary_ranks"] == ranks
    assert result["betti"] == [counts[k] - ranks[k] - ranks[k + 1] for k in range(5)]
    assert result["euler"] == sum((-1) ** k * c for k, c in enumerate(counts))
    assert result["euler"] == result["betti_sum"] and result["euler_defect"] == 0


@pytest.mark.parametrize("n", range(5))
def test_exhaustive_small_graphs_exact_minors(n):
    nodes = [str(i) for i in range(n)]
    possible = list(combinations(nodes, 2))
    for mask in range(1 << len(possible)):
        edges = [e for i, e in enumerate(possible) if mask & (1 << i)]
        for cutoff in range(5):
            request = pilot.graph_request(n=n, cutoff=cutoff, edges=edges)
            result = pilot.answer_for(request)["data"]["complex"]
            expected = []
            for degree in range(5):
                expected.append([list(s) for s in combinations(nodes, degree + 1)
                                 if degree <= cutoff and all(tuple(p) in edges for p in combinations(s, 2))])
            assert result["bases"] == expected
            assert result["f_vector"] == [len(b) for b in expected]
            assert result["betti"][0] == (n if cutoff == 0 else components(nodes, edges))
            assert result["coefficient_field"] == "Q" and result["homology"] == "ordinary_unreduced"
            check_witnesses(result, use_minors=True)


@pytest.mark.parametrize("n", range(7))
def test_complete_graphs_all_cutoffs_binomial_oracle(n):
    for cutoff in range(5):
        result = pilot.answer_for(pilot.graph_request(n=n, cutoff=cutoff))["data"]["complex"]
        counts = [comb(n, k + 1) if k <= cutoff and k < n else 0 for k in range(5)]
        ranks = [0] + [comb(n - 1, k) if k <= cutoff and k < n else 0 for k in range(1, 5)] + [0]
        assert result["f_vector"] == counts and result["boundary_ranks"] == ranks
        assert result["betti"] == [counts[k] - ranks[k] - ranks[k + 1] for k in range(5)]
        assert result["full_clique_dimension"] == n - 1
        assert result["selected_dimension"] == min(n - 1, cutoff)
        assert result["truncated"] == (n - 1 > cutoff)
        check_witnesses(result)


@pytest.mark.parametrize("missing", list(combinations("012345", 2)))
def test_K6_edge_deletions(missing):
    edges = [e for e in combinations("012345", 2) if e != missing]
    result = pilot.answer_for(pilot.graph_request(n=6, edges=edges))["data"]["complex"]
    assert result["f_vector"] == [6, 14, 16, 9, 2]
    assert result["boundary_ranks"] == [0, 5, 9, 7, 2, 0]
    assert result["betti"] == [1, 0, 0, 0, 0] and result["euler"] == 1
    assert result["full_clique_dimension"] == 4 and result["truncated"] is False
    check_witnesses(result)


def test_octahedron_cycle_isolates_and_relabelling():
    octa = [e for e in combinations("012345", 2) if e not in (("0", "1"), ("2", "3"), ("4", "5"))]
    fixtures = [(6, octa, [6, 12, 8, 0, 0], [1, 0, 1, 0, 0]),
                (4, [("0", "1"), ("1", "2"), ("2", "3"), ("0", "3")], [4, 4, 0, 0, 0], [1, 1, 0, 0, 0]),
                (3, [("0", "1")], [3, 1, 0, 0, 0], [2, 0, 0, 0, 0])]
    for n, edges, counts, betti in fixtures:
        req = pilot.graph_request(n=n, edges=edges)
        result = pilot.answer_for(req)["data"]["complex"]
        assert result["f_vector"] == counts and result["betti"] == betti
        check_witnesses(result)
        labels = dict(zip("012345", "zyxwvu", strict=True))
        req["graph"]["vertices"] = [labels[v] for v in req["graph"]["vertices"]][::-1]
        req["graph"]["edges"] = [[labels[b], labels[a]] for a, b in edges][::-1]
        other = pilot.answer_for(req)["data"]["complex"]
        assert other["betti"] == betti and other["f_vector"] == counts
        check_witnesses(other)


@pytest.mark.parametrize("raw", ["0>1<>1<2<>0<2<>a", "a<>2>0<>1>2<>1<0"])
def test_glyph_adapter_equivalence_direction_and_isolates(raw):
    glyph = {"encoding": "glyph", "text": raw, "max_dimension": 4}
    req = {"case_id": "glyph", "kind": "analyse", "graph": glyph}
    result = pilot.answer_for(req)["data"]["complex"]
    assert result["f_vector"] == [4, 3, 1, 0, 0] and result["betti"] == [2, 0, 0, 0, 0]
    assert pilot.graph_input({"encoding": "glyph", "text": "z", "max_dimension": 0}) == (("z",), frozenset(), 0)


@pytest.mark.parametrize("raw", ["", " ", "0>1 ", "0>1<>", "<>0", "0>1>2", "0>1w2", "01", "A", "0\n",
                                 "0<>0", "0>0", "0>1<>1>0", "0>1<>0<1", "0<>1<>2<>3<>4<>5<>6",
                                 "a" * 129, "ask<0>1>", 7, None])
def test_invalid_glyphs(raw):
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for({"case_id": "g", "kind": "analyse",
                          "graph": {"encoding": "glyph", "text": raw, "max_dimension": 4}})


@pytest.mark.parametrize("change", [{"encoding": "unknown"}, {"max_dimension": True}, {"max_dimension": -1},
                                  {"max_dimension": 5}, {"vertices": ["0", "0"]}, {"vertices": list("0123456")},
                                  {"vertices": [1]}, {"vertices": ["aa"]}, {"vertices": "0123"},
                                  {"edges": [["0"]]}, {"edges": ["01"]}, {"edges": [[0, "1"]]},
                                  {"edges": [["0", "z"]]}, {"edges": [["0", "0"]]},
                                  {"edges": [["0", "1"], ["1", "0"]]}, {"edges": [] * 0 + [["0", "1"]] * 16},
                                  {"edges": None}, {"extra": None}])
def test_invalid_edge_inputs(change):
    req = pilot.graph_request()
    req["graph"].update(change)
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(req)


def test_clique_membership_and_cutoff_refusals():
    req = pilot.graph_request(n=3, cutoff=1)
    req.update(kind="clique", vertices=["2", "0", "1"])
    result = pilot.answer_for(req)["data"]
    assert result["complete_in_graph"] is True and result["included_in_complex"] is False
    assert result["above_cutoff"] is True and result["missing_edges"] == []
    assert result["refusal"] == "ref<1>" and result["reason"] == "Outside declared dimension cutoff"
    req["graph"]["max_dimension"] = 2
    assert pilot.answer_for(req)["data"]["included_in_complex"] is True
    req["graph"]["edges"] = [["0", "1"], ["1", "2"]]
    result = pilot.answer_for(req)["data"]
    assert result["missing_edges"] == [["0", "2"]] and result["above_cutoff"] is False
    assert result["refusal"] == "ref<1>" and result["reason"] == "Missing graph data"
    req["vertices"] = ["a"]
    assert pilot.answer_for(req)["data"]["missing_vertices"] == ["a"]
    for bad in ([], ["0", "0"], [True]):
        req["vertices"] = bad
        with pytest.raises(pilot.InvalidInput):
            pilot.answer_for(req)


def test_false_betti_with_same_euler_is_rejected():
    req = pilot.graph_request()
    req.update(kind="check_betti", betti=[1, 1, 1, 0, 0])
    result = pilot.answer_for(req)["data"]
    assert result["euler"] == result["proposed_euler"] == 1
    assert result["actual_betti"] == [1, 0, 0, 0, 0]
    assert result["refusal"] == "ref<2>" and result["matches_betti"] is False
    req["betti"] = [1, 0, 0, 0, 0]
    assert pilot.answer_for(req)["data"]["status"] == "COMPUTED"
    for bad in ([], [1] * 6, [True, 0, 0, 0, 0], [-1, 0, 0, 0, 0], [65, 0, 0, 0, 0], "1"):
        req["betti"] = bad
        with pytest.raises(pilot.InvalidInput):
            pilot.answer_for(req)


def test_invalid_envelopes_claims_and_internal_guards(monkeypatch):
    for raw in (None, [], {"kind": []}, {"kind": "unknown"}, dict(pilot.graph_request(), extra=None),
                dict(pilot.graph_request(), case_id=""), dict(pilot.graph_request(), case_id=True),
                dict(pilot.graph_request(), case_id="a" * 65), dict(pilot.graph_request(), graph=[]),
                {"case_id": "x", "kind": "claim", "claim": "unspecified natural language"}):
        with pytest.raises(pilot.InvalidInput):
            pilot.answer_for(raw)
    for claim in ("infinite_dimensional_complex", "nonfinite_cw_complex"):
        answer = pilot.answer_for({"case_id": "x", "kind": "claim", "claim": claim})
        assert answer["data"] == {"status": "REFUSED", "refusal": "ref<4>", "claim": claim, "adapter": "UNBOUND"}
        assert answer["authority_effect"] == answer["genesis_effect"] == "None" and answer["realizes"] is None
    with pytest.raises(pilot.InvalidInput, match="shape"):
        pilot.product({"rows": 0, "cols": 2, "entries": []}, {"rows": 1, "cols": 0, "entries": [[]]})
    actual = pilot.reduction
    def wrong(matrix):
        result = actual(matrix)
        result["rank"] = 100
        return result
    monkeypatch.setattr(pilot, "reduction", wrong)
    with pytest.raises(pilot.InvalidInput, match="chain complex"):
        pilot.answer_for(pilot.graph_request())


def test_fixture_accounting():
    report = pilot.exercise_report()
    assert [r["id"] for r in report["exercises"]] == [f"P13.{i}" for i in range(1, 4)] + [f"DRILL13.{i}" for i in range(1, 7)]
    assert len(report["source_vocabulary"]) == 8 and len(report["controls"]) == 7
    assert report["exercises"][0]["computed_answer"]["data"]["complex"]["betti"] == [1, 0, 0, 0, 0]
    assert report["exercises"][1]["computed_answer"]["data"]["complex"]["betti"] == [1, 0, 1, 0, 0]
    assert report["exercises"][2]["computed_answer"]["data"]["refusal"] == "ref<1>"
    assert report["controls"][5]["data"]["refusal"] == "ref<2>"
    for row in report["exercises"]:
        assert row["computed_answer"] == pilot.answer_for(row["request"])


def valid_document():
    request = pilot.graph_request()
    return pilot.submission(request, pilot.answer_for(request))


@pytest.mark.parametrize("target", ["digest", "matrix", "rank", "betti", "boolean", "authority", "request", "cutoff", "extra", "transform"])
def test_full_request_and_answer_binding(target):
    document = valid_document()
    data = document["proposal"]["answer"]["data"]["complex"]
    if target == "digest":
        document["proposal"]["input_sha256"] = "0" * 64
    elif target == "matrix":
        data["boundaries"][1]["entries"][0][0] = 1
    elif target == "rank":
        data["boundary_ranks"][2] -= 1
    elif target == "betti":
        data["betti"] = [1, 1, 1, 0, 0]
    elif target == "boolean":
        data["betti"][0] = True
    elif target == "authority":
        document["proposal"]["answer"]["authority_effect"] = "Promoted"
    elif target == "request":
        document["request"]["case_id"] = "changed"
    elif target == "cutoff":
        document["request"]["graph"]["max_dimension"] = 2
    elif target == "transform":
        data["rank_witnesses"][1]["row_transform"][0][0] = "777"
    else:
        data["extra"] = 0
    assert pilot.evaluate(document)["verdict"] == "MISMATCH"


def test_binding_snapshots_and_envelopes():
    document = valid_document()
    result = pilot.evaluate(document)
    assert result["verdict"] == "MATCH" and result["binding_ok"] is True
    document["request"]["graph"]["max_dimension"] = 1
    assert result["request"]["graph"]["max_dimension"] == 4
    copy = pilot.submission(result["request"], result["canonical"])
    result["request"]["graph"]["max_dimension"] = 0
    assert copy["request"]["graph"]["max_dimension"] == 4
    for bad in (None, [], {"request": {}}, {"request": {}, "proposal": {}}):
        with pytest.raises(pilot.InvalidInput):
            pilot.evaluate(bad)


@pytest.mark.parametrize("bad", [1.5, float("nan"), float("inf"), (1,), {1: "x"}, "\u00e9", "\n",
                                 "x" * 2049, [0] * 257, {str(i): 0 for i in range(65)}, 10**19])
def test_json_value_boundaries(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.json_value(bad)


def test_decoder_and_depth_limits():
    deep = 0
    for _ in range(17):
        deep = [deep]
    with pytest.raises(pilot.InvalidInput, match="depth"):
        pilot.json_value(deep)
    for raw in (b"", b" " * (pilot.MAX_BYTES + 1), b'{"x":1,"x":2}', b"NaN", b"Infinity", b"not_json", b"\xff"):
        with pytest.raises((ValueError, UnicodeError)):
            pilot.decode(raw)
    assert pilot.decode(b'{"x":[null,true,false,1,"a"]}') == {"x": [None, True, False, 1, "a"]}
    huge = {str(i): ["a" * 2048] * 2 for i in range(40)}
    for operation in (pilot.answer_for, pilot.evaluate):
        with pytest.raises(pilot.InvalidInput, match="byte limit"):
            operation(huge)


def cli(tmp_path, raw=None, code=CODE):
    args = [sys.executable, str(code), "--output-dir", str(tmp_path / "output")]
    if raw is not None:
        source = tmp_path / "input.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(raw)
        args.extend(["--input", str(source)])
    result = subprocess.run(args, text=True, capture_output=True, timeout=30,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
    assert not result.stderr, result.stderr
    return result.returncode, json.loads(result.stdout)


def test_default_output_root_is_beside_the_pilot_not_the_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert pilot.OUTPUT_ROOT == CODE.parent.parent / "pilot_output" / pilot.PILOT_ID
    assert pilot.OUTPUT_ROOT.is_absolute()


def test_script_entry(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(CODE), "--output-dir", str(tmp_path / "runs")])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(CODE), run_name="__main__")
    assert caught.value.code == 0 and json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"


def inspect_run(reply, raw, code=CODE):
    folder = Path(reply["output"])
    assert (folder / "input.bin").read_bytes() == raw
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert receipt["code_sha256"] == hashlib.sha256(code.read_bytes()).hexdigest()
    assert receipt["model_calls"] == 0 and receipt["cost_usd"] == "0"
    for name, digest in receipt["artifact_sha256"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
    return json.loads((folder / "result.json").read_bytes())



@pytest.mark.parametrize("mode", ["default", "match", "mismatch", "invalid", "claim", "clique", "empty", "maximal"])
def test_real_cli(tmp_path, mode):
    document = valid_document()
    if mode == "mismatch":
        document["proposal"]["answer"]["data"]["complex"]["betti"] = [1, 1, 1, 0, 0]
    elif mode == "invalid":
        document["request"]["graph"]["max_dimension"] = True
    elif mode in ("claim", "clique", "empty", "maximal"):
        req = pilot.graph_request(n=0 if mode == "empty" else 6)
        if mode == "claim":
            req = {"case_id": "claim", "kind": "claim", "claim": "nonfinite_cw_complex"}
        elif mode == "clique":
            req.update(kind="clique", vertices=["0", "1"])
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
    document["request"]["graph"]["max_dimension"] = True
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
    ("unsigned_boundary", "(-1) ** i", "1", "math"),
    ("rank_error_cancels", 'ranks = [r["rank"] for r in reductions]', 'ranks = [r["rank"] for r in reductions]; ranks[2] = max(0, ranks[2] - 1)', "math"),
    ("ignore_cutoff", "k <= cutoff and k < len(all_cliques)", "k < len(all_cliques)", "cutoff"),
    ("lose_isolates", "return tuple(sorted(nodes)), frozenset(edges), cutoff",
     "return tuple(sorted({v for edge in edges for v in edge})), frozenset(edges), cutoff", "isolates"),
    ("force_connected", '"betti": betti, "euler"', '"betti": [1] + betti[1:], "euler"', "isolates"),
    ("Euler_only_Betti", 'equal = proposed == result["betti"]',
     'equal = sum((-1) ** k * b for k, b in enumerate(proposed)) == result["euler"]', "false_betti"),
    ("consecutive_clique_edges", "for pair in combinations(c, 2)", "for pair in zip(c, c[1:])", "missing"),
    ("clique_missing_edge_ignored", "complete = not missing_vertices and not missing_edges", "complete = not missing_vertices", "clique"),
    ("cutoff_membership_ignored", "included = complete and not above", "included = complete", "face_cutoff"),
    ("wrong_zero_shape", '"cols": len(columns), "entries": matrix', '"cols": len(columns) if rows else 0, "entries": matrix', "math"),
    ("wrong_row_transform", '"row_transform": [[str(v) for v in row] for row in transform]',
     '"row_transform": [[str(int(i == j)) for j in range(rows)] for i in range(rows)]', "math"),
    ("wrong_orientation", "(-1) ** i", "(-1) ** (i + 1)", "math"),
    ("no_skeleton_label", '"truncated": full_dimension > cutoff', '"truncated": False', "cutoff"),
    ("accept_nonfinite", '"status": "REFUSED", "refusal": "ref<4>"', '"status": "COMPUTED", "refusal": "ref<4>"', "claim"),
    ("ignore_binding", 'matches = binding_ok and encoded(proposal', 'matches = encoded(proposal', "binding"),
    ("ignore_answer", 'matches = binding_ok and encoded(proposal["answer"]) == encoded(canonical)', 'matches = binding_ok', "answer"),
    ("bool_integer", "type(value) is int and lower <= value <= upper", "isinstance(value, int) and lower <= value <= upper", "boolean"),
    ("authority_promotion", '"authority_effect": "None", "genesis_effect": "None", "realizes": None}',
     '"authority_effect": "Promoted", "genesis_effect": "None", "realizes": None}', "math"),
)


def mutation_document(mode):
    req = pilot.graph_request()
    if mode == "cutoff":
        req = pilot.graph_request(n=6, cutoff=2)
    elif mode == "isolates":
        req = pilot.graph_request(n=3, edges=[])
    elif mode == "false_betti":
        req.update(kind="check_betti", betti=[1, 1, 1, 0, 0])
    elif mode in ("missing", "clique"):
        req = pilot.graph_request(n=3, edges=[("0", "1"), ("1", "2")])
        if mode == "clique":
            req.update(kind="clique", vertices=["0", "1", "2"])
    elif mode == "face_cutoff":
        req = pilot.graph_request(n=3, cutoff=1)
        req.update(kind="clique", vertices=["0", "1", "2"])
    elif mode == "claim":
        req = {"case_id": "claim", "kind": "claim", "claim": "nonfinite_cw_complex"}
    document = pilot.submission(req, pilot.answer_for(req))
    if mode == "binding":
        document["proposal"]["input_sha256"] = "0" * 64
    elif mode == "answer":
        document["proposal"]["answer"]["data"]["complex"]["betti"] = [1, 1, 1, 0, 0]
    elif mode == "boolean":
        req["graph"]["max_dimension"] = 1
        canonical = pilot.answer_for(req)
        req["graph"]["max_dimension"] = True
        document = pilot.submission(req, canonical)
    return document


def test_compiled_cli_mutations(tmp_path):
    source = CODE.read_text(encoding="utf-8")
    records = []
    for name, old, new, mode in MUTATIONS:
        assert source.count(old) == (2 if name == "authority_promotion" else 1), (name, source.count(old))
        altered = source.replace(old, new, 1)
        compile(altered, name, "exec")
        folder = tmp_path / name
        folder.mkdir()
        code = folder / "run.py"
        code.write_text(altered, encoding="utf-8")
        document = mutation_document(mode)
        if mode == "boolean":
            with pytest.raises(pilot.InvalidInput):
                pilot.evaluate(document)
            baseline = "REJECTED"
        else:
            baseline = pilot.evaluate(document)["verdict"]
        exit_code, reply = cli(folder, pilot.encoded(document), code)
        assert reply["status"] in ("MATCH", "MISMATCH", "REJECTED"), (name, reply)
        assert reply["status"] != baseline, (name, reply)
        inspect_run(reply, pilot.encoded(document), code)
        records.append({"mutation": name, "compiled": True, "caught": True, "old": old, "new": new,
                        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                        "mutant_sha256": hashlib.sha256(altered.encode()).hexdigest(),
                        "baseline_status": baseline, "mutant_status": reply["status"],
                        "exit_code": exit_code, "document": document})
    assert CODE.read_text(encoding="utf-8") == source
    destination = os.environ.get("PFP_MUTATION_REPORT")
    if destination:
        Path(destination).write_text(json.dumps({"count": len(records), "mutations": records}, indent=2), encoding="utf-8")
