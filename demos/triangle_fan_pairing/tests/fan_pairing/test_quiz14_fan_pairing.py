"""Scoped exact fan/pairing, custody, CLI and compiled-mutation tests for Quiz14."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import importlib.util
from itertools import product
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

CODE = Path(os.environ.get("PFP_PILOT_RUN_FILE", Path(__file__).resolve().parents[2] / "run.py")).resolve()
spec = importlib.util.spec_from_file_location("quiz14_fans_and_pairings", CODE)
pilot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot
spec.loader.exec_module(pilot)


@pytest.mark.parametrize("n", range(3, 13))
def test_all_fan_sizes_and_independent_boundary_turn(n):
    req = pilot.fan_request(size=n)
    result = pilot.answer_for(req)["data"]["fan"]
    assert result["triangle_count"] == n
    assert result["f_vector"] == [n + 1, 2 * n, n] and result["euler"] == 1
    assert result["angle_units"] == "2*pi" and result["metric"] == "intrinsic_equilateral_unit_edges"
    assert result["center_angles"] == ["1/6"] * n
    assert F(result["angle_sum"]) == F(n, 6)
    assert F(result["deficit"]) == F(6 - n, 6)
    assert F(result["deficit_pi_multiple"]) == F(6 - n, 3)
    assert result["classification"] == ("flat" if n == 6 else "curved")
    assert result["deficit_sign"] == ("positive" if n < 6 else "zero" if n == 6 else "negative")
    assert result["boundary_turns"] == {f"v{i}": "1/6" for i in range(n)}
    assert F(result["deficit"]) + sum(map(F, result["boundary_turns"].values())) == 1
    assert result["total_normalized_turn"] == "1" and result["gauss_bonnet_residual"] == "0"
    rim = [f"v{i}" for i in range(n)]
    rim_edges = {tuple(sorted((rim[i], rim[(i + 1) % n]))) for i in range(n)}
    expected_edges = rim_edges | {tuple(sorted(("c", v))) for v in rim}
    assert result["edges"] == [list(e) for e in sorted(expected_edges)]
    assert result["center_link_edges"] == [list(e) for e in sorted(rim_edges)]
    for reverse_faces, reverse_vertices, reverse_orientation in product((False, True), repeat=3):
        changed = deepcopy(req)
        if reverse_faces:
            changed["fan"]["triangles"].reverse()
        if reverse_vertices:
            changed["fan"]["vertices"].reverse()
        if reverse_orientation:
            changed["fan"]["triangles"] = [face[::-1] for face in changed["fan"]["triangles"]]
        assert pilot.answer_for(changed)["data"]["fan"] == result


def test_relabelled_fan_is_intrinsic_not_a_clique_fill():
    req = pilot.fan_request(size=3)
    labels = dict(zip(req["fan"]["vertices"], ("Z", "a-1", "b_2", "x.3"), strict=True))
    req["fan"]["vertices"] = list(labels.values())
    req["fan"]["center"] = labels["c"]
    req["fan"]["triangles"] = [[labels[v] for v in triangle] for triangle in req["fan"]["triangles"]]
    result = pilot.answer_for(req)["data"]["fan"]
    assert result["f_vector"] == [4, 6, 3] and result["euler"] == 1
    assert F(result["deficit"]) == F(1, 2)
    assert all("Z" in triangle for triangle in result["triangles"])
    # The missing outer triangle is not inferred from its three graph edges.
    assert ["a-1", "b_2", "x.3"] not in result["triangles"]


@pytest.mark.parametrize("mode", ["open", "disconnected", "duplicate", "unrelated", "wrong_center", "missing_vertex",
                                   "isolated_vertex", "repeated_vertex", "short_face", "long_face", "repeated_face_vertex",
                                   "bad_label", "bad_center", "missing_field", "extra_field", "too_small", "too_large",
                                   "vertices_not_list", "triangles_not_list", "no_center", "empty"])
def test_invalid_fan_carriers(mode):
    req = pilot.fan_request()
    fan = req["fan"]
    if mode == "open":
        fan["triangles"].pop()
    elif mode == "disconnected":
        fan["triangles"] = [["c", f"v{a}", f"v{b}"] for a, b in ((0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3))]
    elif mode == "duplicate":
        fan["triangles"].append(fan["triangles"][0][::-1])
    elif mode == "unrelated":
        fan["triangles"][0] = ["v0", "v1", "v2"]
    elif mode == "wrong_center":
        fan["center"] = "other"
    elif mode == "missing_vertex":
        fan["triangles"][0][1] = "other"
    elif mode == "isolated_vertex":
        fan["vertices"].append("other")
    elif mode == "repeated_vertex":
        fan["vertices"].append("v0")
    elif mode == "short_face":
        fan["triangles"][0] = ["c", "v0"]
    elif mode == "long_face":
        fan["triangles"][0] = ["c", "v0", "v1", "v2"]
    elif mode == "repeated_face_vertex":
        fan["triangles"][0] = ["c", "v0", "v0"]
    elif mode == "bad_label":
        fan["vertices"][0] = "bad label"
    elif mode == "bad_center":
        fan["center"] = True
    elif mode == "missing_field":
        fan.pop("vertices")
    elif mode == "extra_field":
        fan["count"] = 6
    elif mode == "too_small":
        req = pilot.fan_request(size=2)
    elif mode == "too_large":
        req = pilot.fan_request(size=13)
    elif mode == "vertices_not_list":
        fan["vertices"] = "cv0"
    elif mode == "triangles_not_list":
        fan["triangles"] = {}
    elif mode == "no_center":
        fan["vertices"].remove("c")
    else:
        req["fan"] = {}
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(req)


@pytest.mark.parametrize("n", range(13))
def test_pair_counts_and_weighted_changes_derive_from_records(n):
    req = pilot.pairing_request(size=n)
    result = pilot.answer_for(req)["data"]["pairing"]
    assert result["pair_count"] == result["positive_count"] == result["negative_count"] == n
    assert result["member_count"] == 2 * n and result["signed_count"] == 0
    assert result["positive_weight_total"] == result["negative_weight_total"] == str(n)
    assert result["weighted_total"] == "0" and result["all_pairwise_weights_equal"] is True
    for i in range(n):
        for role, expected in (("positive", "1"), ("negative", "-1")):
            changed = deepcopy(req)
            changed["pairs"][i][role]["weight"] = "2"
            actual = pilot.answer_for(changed)["data"]["pairing"]
            assert actual["pair_count"] == n and actual["signed_count"] == 0
            assert actual["weighted_total"] == expected and actual["all_pairwise_weights_equal"] is False
            assert sum(F(row["contribution"]) for row in actual["pairs"]) == F(expected)
    req["pairs"].reverse()
    assert pilot.answer_for(req)["data"]["pairing"] == result


def test_exhaustive_two_pair_weights_against_flat_dot_product():
    for weights in product(("0", "1/2", "1", "2"), repeat=4):
        req = pilot.pairing_request(size=2)
        for i, row in enumerate(req["pairs"]):
            row["positive"]["weight"], row["negative"]["weight"] = weights[2 * i:2 * i + 2]
        expected = sum(sign * F(weight) for sign, weight in zip((1, -1, 1, -1), weights, strict=True))
        actual = pilot.answer_for(req)["data"]["pairing"]
        assert F(actual["weighted_total"]) == expected and actual["signed_count"] == 0
        assert actual["all_pairwise_weights_equal"] == (weights[0] == weights[1] and weights[2] == weights[3])
        assert [F(row["contribution"]) for row in actual["pairs"]] == [F(weights[0]) - F(weights[1]), F(weights[2]) - F(weights[3])]


def test_fractional_cross_cancellation_and_large_canonical_weights():
    req = pilot.pairing_request(size=2)
    for pair, a, b in zip(req["pairs"], ("1/3", "1/2"), ("1/4", "2/3"), strict=True):
        pair["positive"]["weight"], pair["negative"]["weight"] = a, b
    assert pilot.answer_for(req)["data"]["pairing"]["weighted_total"] == "-1/12"
    req = pilot.pairing_request(size=2)
    req["pairs"][0]["positive"]["weight"] = req["pairs"][1]["negative"]["weight"] = "2"
    result = pilot.answer_for(req)["data"]["pairing"]
    assert result["weighted_total"] == "0" and result["all_pairwise_weights_equal"] is False
    req = pilot.pairing_request(size=12, last_negative="1/1000000")
    req["pairs"][0]["positive"]["weight"] = "1000000"
    assert F(pilot.answer_for(req)["data"]["pairing"]["weighted_total"]) == F(1000000) - F(1, 1000000)


@pytest.mark.parametrize("bad", [True, 1, "-1", "2/2", "-0", "00", "01", "1.0", "1/0", "1000001",
                                "1/1000001", "12345678", "1/-2", " 1", "1/1"])
def test_invalid_weights(bad):
    req = pilot.pairing_request()
    req["pairs"][-1]["negative"]["weight"] = bad
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(req)


@pytest.mark.parametrize("mode", ["not_list", "too_many", "duplicate_pair", "duplicate_member", "same_members",
                                   "positive_wrong", "negative_wrong", "zero_sign", "bool_sign", "missing_weight",
                                   "extra_field", "missing_member", "bad_id", "long_id", "empty_id", "not_object"])
def test_invalid_pairs(mode):
    req = pilot.pairing_request(size=2)
    pairs = req["pairs"]
    if mode == "not_list":
        req["pairs"] = {}
    elif mode == "too_many":
        req = pilot.pairing_request(size=13)
    elif mode == "duplicate_pair":
        pairs[1]["pair_id"] = pairs[0]["pair_id"]
    elif mode == "duplicate_member":
        pairs[1]["positive"]["member_id"] = pairs[0]["negative"]["member_id"]
    elif mode == "same_members":
        pairs[0]["negative"]["member_id"] = pairs[0]["positive"]["member_id"]
    elif mode == "positive_wrong":
        pairs[0]["positive"]["sign"] = -1
    elif mode == "negative_wrong":
        pairs[0]["negative"]["sign"] = 1
    elif mode == "zero_sign":
        pairs[0]["positive"]["sign"] = 0
    elif mode == "bool_sign":
        pairs[0]["positive"]["sign"] = True
    elif mode == "missing_weight":
        pairs[0]["positive"].pop("weight")
    elif mode == "extra_field":
        pairs[0]["positive"]["physical"] = True
    elif mode == "missing_member":
        pairs[0].pop("negative")
    elif mode == "bad_id":
        pairs[0]["pair_id"] = False
    elif mode == "long_id":
        pairs[0]["pair_id"] = "p" * 33
    elif mode == "empty_id":
        pairs[0]["pair_id"] = ""
    else:
        pairs[0] = None
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(req)


def test_physical_refusal_retains_finite_computation_and_validates_all_inputs():
    req = pilot.pairing_request(last_negative="2")
    req.update(kind="physical_claim", claim="regge4d_susy_from_pairs")
    result = pilot.answer_for(req)
    data = result["data"]
    assert data["status"] == "REFUSED" and data["refusal"] == "ref<3>" and data["adapter"] == "UNBOUND"
    assert data["finite_pairing"]["pair_count"] == 11 and data["finite_pairing"]["weighted_total"] == "-1"
    assert len(data["missing_witnesses"]) == 3
    assert result["authority_effect"] == result["genesis_effect"] == "None" and result["realizes"] is None
    req["pairs"][-1]["negative"].pop("weight")
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(req)
    req = pilot.pairing_request()
    req.update(kind="physical_claim", claim="any physical theory")
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(req)


@pytest.mark.parametrize("bad", [None, [], {"kind": []}, {"kind": "unknown"},
                                {"case_id": "x", "kind": "fan", "fan": {}, "extra": None},
                                {"case_id": "", "kind": "fan", "fan": {}},
                                {"case_id": True, "kind": "fan", "fan": {}},
                                {"case_id": "a" * 65, "kind": "fan", "fan": {}}])
def test_other_invalid_requests(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(bad)


def test_exact_source_accounting():
    report = pilot.exercise_report()
    assert [r["id"] for r in report["exercises"]] == [f"P14.{i}" for i in range(1, 5)]
    assert report["source_drills"] == 0 and report["source_registry"] is None
    assert [r["source_prompt_kind"] for r in report["exercises"]] == ["packet_label", "packet_label", "prose", "packet_label"]
    assert len(report["controls"]) == 7
    assert report["exercises"][0]["computed_answer"]["data"]["fan"]["deficit"] == "0"
    assert report["exercises"][1]["computed_answer"]["data"]["fan"]["deficit"] == "1/6"
    assert report["exercises"][2]["computed_answer"]["data"]["pairing"]["weighted_total"] == "-1"
    assert report["exercises"][3]["computed_answer"]["data"]["refusal"] == "ref<3>"
    for row in report["exercises"]:
        assert row["computed_answer"] == pilot.answer_for(row["request"])


def valid_document():
    req = pilot.fan_request()
    return pilot.submission(req, pilot.answer_for(req))


@pytest.mark.parametrize("target", ["digest", "case", "orientation", "angles", "deficit", "boundary", "classification",
                                    "bool_count", "authority", "extra"])
def test_full_binding_and_answer_comparison(target):
    document = valid_document()
    result = document["proposal"]["answer"]["data"]["fan"]
    if target == "digest":
        document["proposal"]["input_sha256"] = "0" * 64
    elif target == "case":
        document["request"]["case_id"] = "new"
    elif target == "orientation":
        document["request"]["fan"]["triangles"][0].reverse()
    elif target == "angles":
        result["center_angles"][0] = "0"
    elif target == "deficit":
        result["deficit"] = "1"
    elif target == "boundary":
        result["boundary_turns"]["v0"] = "0"
    elif target == "classification":
        result["classification"] = "curved"
    elif target == "bool_count":
        result["center_is_interior"] = 1
    elif target == "authority":
        document["proposal"]["answer"]["authority_effect"] = "Promoted"
    else:
        result["extra"] = 0
    assert pilot.evaluate(document)["verdict"] == "MISMATCH"


def test_pairing_custody_and_snapshots():
    req = pilot.pairing_request(last_negative="2")
    document = pilot.submission(req, pilot.answer_for(req))
    result = pilot.evaluate(document)
    assert result["verdict"] == "MATCH"
    req["pairs"][-1]["negative"]["weight"] = "3"
    assert document["request"]["pairs"][-1]["negative"]["weight"] == "2"
    document["request"]["pairs"][-1]["negative"]["weight"] = "4"
    assert result["request"]["pairs"][-1]["negative"]["weight"] == "2"
    assert pilot.evaluate(document)["verdict"] == "MISMATCH"
    document = pilot.submission(result["request"], result["canonical"])
    document["proposal"]["answer"]["data"]["pairing"]["weighted_total"] = "0"
    assert pilot.evaluate(document)["verdict"] == "MISMATCH"
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



@pytest.mark.parametrize("mode", ["default", "match", "mismatch", "invalid", "claim", "pairing", "empty", "maximal"])
def test_real_cli(tmp_path, mode):
    document = valid_document()
    if mode == "mismatch":
        document["proposal"]["answer"]["data"]["fan"]["deficit"] = "1"
    elif mode == "invalid":
        document["request"]["fan"]["triangles"].pop()
    elif mode in ("claim", "pairing", "empty", "maximal"):
        req = pilot.fan_request(size=12) if mode == "maximal" else pilot.pairing_request(size=0 if mode == "empty" else 11)
        if mode == "claim":
            req.update(kind="physical_claim", claim="regge4d_susy_from_pairs")
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
    document["request"]["fan"]["triangles"].pop()
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
    ("wrong_angle", "angles = [Fraction(1, 6)] * count", "angles = [Fraction(1, 3)] * count", "fan5"),
    ("boundary_normalization", "deficit = Fraction(1) - angle_sum", "deficit = Fraction(1, 2) - angle_sum", "fan5"),
    ("clamp_negative", "deficit = Fraction(1) - angle_sum", "deficit = max(Fraction(0), Fraction(1) - angle_sum)", "fan7"),
    ("integer_angle_sum", "angle_sum = sum(angles, Fraction(0))", "angle_sum = Fraction(int(sum(angles, Fraction(0))))", "fan5"),
    ("constant_face_count", "count = len(triangles)", "count = 6", "fan5"),
    ("duplicate_triangle", 'require(triangle not in triangles, "Repeated triangle")', 'require(True, "Repeated triangle")', "duplicate_triangle"),
    ("open_link", 'require(all(len(neighbors) == 2 for neighbors in link.values()), "Interior link must have degree two")',
     'require(True, "Interior link must have degree two")', "open"),
    ("disconnected_link", 'require(reached == set(link), "Interior link must be one connected cycle")',
     'require(True, "Interior link must be one connected cycle")', "disconnected"),
    ("discard_weights", 'weight = rational(member["weight"])', 'weight = Fraction(1)', "weighted"),
    ("negative_sign", 'str(positive_total - negative_total)', 'str(positive_total + negative_total)', "weighted"),
    ("unsigned_count", "signed_count += sign", "signed_count += 1", "weighted"),
    ("constant_pair_count", '"pair_count": len(rows)', '"pair_count": 11', "empty"),
    ("duplicate_pair_id", 'require(pair_id not in pair_ids, "Repeated pair identifier")',
     'require(True, "Repeated pair identifier")', "duplicate_pair"),
    ("duplicate_member_id", 'require(member_id not in member_ids, "Repeated member identifier")',
     'require(True, "Repeated member identifier")', "duplicate_member"),
    ("bool_integer", "type(value) is int and lower <= value <= upper", "isinstance(value, int) and lower <= value <= upper", "boolean"),
    ("noncanonical_weight", 'require(str(result) == value, "Unreduced or noncanonical rational")',
     'require(True, "Unreduced or noncanonical rational")', "noncanonical"),
    ("total_not_pairwise", 'all(row["positive_weight"] == row["negative_weight"] for row in rows)',
     'positive_total == negative_total', "cross"),
    ("accept_physics", '"status": "REFUSED", "refusal": "ref<3>"', '"status": "COMPUTED", "refusal": "ref<3>"', "claim"),
    ("ignore_binding", 'matches = binding_ok and encoded(proposal', 'matches = encoded(proposal', "binding"),
    ("ignore_answer", 'matches = binding_ok and encoded(proposal["answer"]) == encoded(canonical)', 'matches = binding_ok', "answer"),
    ("authority_promotion", '"authority_effect": "None", "genesis_effect": "None", "realizes": None}',
     '"authority_effect": "Promoted", "genesis_effect": "None", "realizes": None}', "fan5"),
)
INVALID_MODES = ("duplicate_triangle", "open", "disconnected", "duplicate_pair", "duplicate_member", "boolean", "noncanonical")


def mutation_document(mode):
    if mode.startswith("fan") or mode in ("duplicate_triangle", "open", "disconnected", "binding", "answer"):
        req = pilot.fan_request(size=int(mode[3:]) if mode.startswith("fan") else 6)
    else:
        req = pilot.pairing_request(size=0 if mode == "empty" else 2, last_negative="2" if mode == "weighted" else "1")
    if mode == "claim":
        req.update(kind="physical_claim", claim="regge4d_susy_from_pairs")
    if mode == "cross":
        req["pairs"][0]["positive"]["weight"] = req["pairs"][1]["negative"]["weight"] = "2"
    document = pilot.submission(req, pilot.answer_for(req))
    request = document["request"]
    if mode == "duplicate_triangle":
        request["fan"]["triangles"].append(request["fan"]["triangles"][0][::-1])
    elif mode == "open":
        request["fan"]["triangles"].pop()
    elif mode == "disconnected":
        request["fan"]["triangles"] = [["c", f"v{a}", f"v{b}"] for a, b in ((0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3))]
    elif mode == "duplicate_pair":
        request["pairs"][1]["pair_id"] = request["pairs"][0]["pair_id"]
    elif mode == "duplicate_member":
        request["pairs"][1]["positive"]["member_id"] = request["pairs"][0]["positive"]["member_id"]
    elif mode == "boolean":
        request["pairs"][0]["positive"]["sign"] = True
    elif mode == "noncanonical":
        request["pairs"][0]["positive"]["weight"] = "2/2"
    if mode in INVALID_MODES:
        document["proposal"]["input_sha256"] = pilot.digest(request)
    elif mode == "binding":
        document["proposal"]["input_sha256"] = "0" * 64
    elif mode == "answer":
        document["proposal"]["answer"]["data"]["fan"]["deficit"] = "1"
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
        if mode in INVALID_MODES:
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
