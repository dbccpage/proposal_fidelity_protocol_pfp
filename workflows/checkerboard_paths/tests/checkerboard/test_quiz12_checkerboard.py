"""Scoped unit, direct-enumeration, CLI and compiled-mutation checks for Quiz12."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import importlib.util
from itertools import product
import json
import math
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

CODE = Path(os.environ.get("PFP_PILOT_000018_UNDER_TEST", Path(__file__).resolve().parents[2] / "run.py")).resolve()
spec = importlib.util.spec_from_file_location("quiz12_exact_checkerboard", CODE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def oracle(n, x, a=F(1), first=None, last=None):
    hist = [0] * max(1, n)
    real = imaginary = F(0)
    for path in product(("R", "L"), repeat=n):
        if sum(1 if step == "R" else -1 for step in path) != x:
            continue
        if first is not None and (not path or path[0] != first):
            continue
        if last is not None and (not path or path[-1] != last):
            continue
        c = sum(path[i] != path[i - 1] for i in range(1, n))
        hist[c] += 1
        power = a**c
        if c % 4 == 0:
            real += power
        elif c % 4 == 1:
            imaginary += power
        elif c % 4 == 2:
            real -= power
        else:
            imaginary -= power
    return hist, [str(real), str(imaginary)]


@pytest.mark.parametrize("n", range(10))
def test_complete_small_binary_path_oracle(n):
    for x in range(-n - 1, n + 2):
        for first, last in product((None, "R", "L"), repeat=2):
            request = pilot.kernel_request(steps=n, x=x, mass="-2/3", epsilon="3/2", first=first, last=last)
            answer = pilot.answer_for(request)["data"]
            expected_hist, expected_amplitude = oracle(n, x, F(-1), first, last)
            assert answer["corner_histogram"] == expected_hist
            assert answer["total_paths"] == sum(expected_hist)
            assert answer["amplitude"] == expected_amplitude
            for key, hist in answer["direction_histograms"].items():
                h, amp = oracle(n, x, F(-1), *key)
                assert hist == h
                assert answer["direction_amplitudes"][key] == amp
                assert all(c % 2 == int(key[0] != key[1]) for c, count in enumerate(hist) if count)


@pytest.mark.parametrize("a", ["0", "1", "-1", "2/3", "-3/2", "1000000", "1/1000000"])
def test_rational_complex_powers_and_weighted_kernel(a):
    for c in range(32):
        req = {"case_id": "amp", "kind": "amplitude", "corners": c, "epsilon": "1", "mass": a}
        actual = pilot.answer_for(req)["data"]["amplitude"]
        factor = F(a)**c
        expected = [str(factor if c % 4 == 0 else -factor if c % 4 == 2 else F(0)),
                    str(factor if c % 4 == 1 else -factor if c % 4 == 3 else F(0))]
        assert actual == expected
    for n, x in ((2, 0), (3, 1), (4, 0), (5, -1)):
        actual = pilot.answer_for(pilot.kernel_request(steps=n, x=x, mass=a))["data"]
        assert (actual["corner_histogram"], actual["amplitude"]) == oracle(n, x, F(a))



def positive_compositions(total, runs):
    if runs == 0:
        return int(total == 0)
    return math.comb(total - 1, runs - 1) if total >= runs else 0


@pytest.mark.parametrize("n", [16, 31, 32])
def test_large_histograms_by_positive_run_compositions(n):
    for x in (-n, -n + 2, n % 2, n - 2, n):
        right, left = (n + x) // 2, (n - x) // 2
        expected = {}
        for start, end in product("RL", repeat=2):
            values = []
            for c in range(n):
                if (c % 2 == 0) != (start == end):
                    values.append(0)
                    continue
                r_runs = c // 2 + 1 if start == "R" else (c + 1) // 2
                l_runs = c // 2 + 1 if start == "L" else (c + 1) // 2
                values.append(positive_compositions(right, r_runs) * positive_compositions(left, l_runs))
            expected[start + end] = values
        for first, last in product((None, "R", "L"), repeat=2):
            result = pilot.answer_for(pilot.kernel_request(steps=n, x=x, first=first, last=last))["data"]
            assert result["direction_histograms"] == expected
            selected = [sum(h[c] for key, h in expected.items()
                            if (first is None or key[0] == first) and (last is None or key[1] == last))
                        for c in range(n)]
            assert result["corner_histogram"] == selected
        reflected = pilot.answer_for(pilot.kernel_request(steps=n, x=-x))["data"]
        for key, hist in expected.items():
            opposite = "".join("L" if step == "R" else "R" for step in key)
            assert reflected["direction_histograms"][opposite] == hist
        assert expected["RL"] == expected["LR"]


def test_closed_counts_at_full_bound_and_translations():
    for n, x in ((32, 0), (32, 32), (32, -32), (31, 3), (0, 0)):
        request = pilot.kernel_request(steps=n, x=x)
        baseline = pilot.answer_for(request)["data"]
        assert baseline["total_paths"] == math.comb(n, (n + x) // 2)
        for t0, x0 in ((-50, -60), (60, 73), (999900, -999900)):
            shifted = deepcopy(request)
            shifted["start"] = [t0, x0]
            shifted["end"] = [t0 + n, x0 + x]
            assert pilot.answer_for(shifted)["data"] == baseline


def test_direction_cancellation_empty_and_massless_not_absent():
    directed = pilot.answer_for(pilot.kernel_request(first="R", last="L"))["data"]
    assert directed["corner_histogram"] == [0, 1, 0, 1]
    assert directed["total_paths"] == 2 and directed["amplitude"] == ["0", "0"]
    scalar = pilot.answer_for(pilot.kernel_request())["data"]
    assert scalar["corner_histogram"] == [0, 2, 2, 2]
    assert scalar["amplitude"] == ["-2", "0"]
    massless = pilot.answer_for(pilot.kernel_request(steps=2, mass="0"))["data"]
    assert massless["total_paths"] == 2 and massless["amplitude"] == ["0", "0"]
    empty = pilot.answer_for(pilot.kernel_request(steps=0))["data"]
    assert empty["total_paths"] == empty["empty_path_count"] == 1
    assert empty["amplitude"] == ["1", "0"]
    assert empty["direction_histograms"] == dict.fromkeys(("RR", "RL", "LR", "LL"), [0])
    conditioned = pilot.answer_for(pilot.kernel_request(steps=0, first="R"))["data"]
    assert conditioned["total_paths"] == conditioned["empty_path_count"] == 0
    single = pilot.answer_for(pilot.kernel_request(steps=1, x=1, mass="7", first="R", last="R"))["data"]
    assert single["corner_histogram"] == [1] and single["amplitude"] == ["1", "0"]
    assert single["initial_corner_counted"] is False


@pytest.mark.parametrize("n,x", [(0, 1), (3, 0), (3, 4), (3, -4)])
def test_unreachable_endpoint_is_computed_zero(n, x):
    result = pilot.answer_for(pilot.kernel_request(steps=n, x=x))["data"]
    assert result["status"] == "COMPUTED"
    assert result["total_paths"] == 0 and result["amplitude"] == ["0", "0"]


@pytest.mark.parametrize("end,expected", [([1, 1], "R"), ([1, -1], "L"), ([1, 2], None),
                                        ([1, 0], None), ([2, 2], None), ([-1, 1], None), ([0, 0], None)])
def test_actual_steps(end, expected):
    result = pilot.answer_for({"case_id": "step", "kind": "step", "start": [0, 0], "end": end})["data"]
    if expected:
        assert result == {"status": "COMPUTED", "direction": expected}
    else:
        assert result["status"] == "REFUSED" and result["refusal"] == "ref<1>"


def test_paths_and_full_upfront_coordinate_validation():
    request = {"case_id": "path", "kind": "path", "points": [[7, 8], [8, 9], [9, 8], [10, 9]]}
    assert pilot.answer_for(request)["data"] == {"status": "COMPUTED", "directions": ["R", "L", "R"],
                                               "corners": 2, "first": "R", "last": "R"}
    request["points"] = [[0, 0]]
    assert pilot.answer_for(request)["data"]["first"] is None
    request["points"] = [[0, 0], [1, 2], [3, 2]]
    assert pilot.answer_for(request)["data"]["invalid_step_indices"] == [0, 1]
    request["points"] = [[0, 0], [1, 2], [3, True]]
    with pytest.raises(pilot.InvalidInput, match="Coordinate"):
        pilot.answer_for(request)
    for points in ([], "R", [[0, 0]] * 34):
        request["points"] = points
        with pytest.raises(pilot.InvalidInput):
            pilot.answer_for(request)


@pytest.mark.parametrize("moves", [[], ["R"], ["L"], ["R", "L", "R"], ["L", "R", "R", "L"]])
def test_explicit_corner_operation(moves):
    result = pilot.answer_for({"case_id": "corner", "kind": "corners", "directions": moves})["data"]
    assert result["corners"] == sum(moves[i] != moves[i - 1] for i in range(1, len(moves)))
    assert result["first"] == (moves[0] if moves else None)
    assert result["last"] == (moves[-1] if moves else None)


@pytest.mark.parametrize("bad", [True, 1, "2/2", "-0", "00", "01", "1.0", "1/0", "1000001",
                                "1/1000001", "12345678", "1/-2", " 1", "1/1"])
def test_rational_input_refuses_noncanonical_or_unbounded(bad):
    req = pilot.kernel_request()
    req["mass"] = bad
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(req)


@pytest.mark.parametrize("change", [{"end": [-1, 0]}, {"end": [33, 0]}, {"epsilon": "0"},
                                    {"epsilon": "-1"}, {"first": "x"}, {"last": True},
                                    {"start": [0]}, {"start": [0, 1000001]}, {"start": [False, 0]},
                                    {"kind": []}, {"kind": "unknown"}, {"extra": None},
                                    {"case_id": ""}, {"case_id": True}, {"case_id": "x" * 65}])
def test_bad_kernel_inputs(change):
    req = pilot.kernel_request()
    req.update(change)
    with pytest.raises(pilot.InvalidInput):
        pilot.answer_for(req)


def test_other_bad_queries():
    for raw in (None, [], {"case_id": "x", "kind": "corners", "directions": "RL"},
                {"case_id": "x", "kind": "corners", "directions": ["R"] * 33},
                {"case_id": "x", "kind": "corners", "directions": ["r"]},
                {"case_id": "x", "kind": "amplitude", "corners": 32, "epsilon": "1", "mass": "1"},
                {"case_id": "x", "kind": "amplitude", "corners": True, "epsilon": "1", "mass": "1"},
                {"case_id": "x", "kind": "claim", "claim": "natural language"}):
        with pytest.raises(pilot.InvalidInput):
            pilot.answer_for(raw)


def test_claims_are_typed_and_have_no_semantic_classifier():
    for claim, ref in (("continuous_dirac_spinor_invariance", "ref<4>"),
                       ("continuous_spinor_field", "ref<4>"), ("physical_mass_or_spin", "ref<3>")):
        result = pilot.answer_for({"case_id": "claim", "kind": "claim", "claim": claim})
        assert result["data"] == {"status": "REFUSED", "refusal": ref, "claim": claim, "adapter": "UNBOUND"}
        assert result["authority_effect"] == result["genesis_effect"] == "None" and result["realizes"] is None


def test_fixture_accounting():
    report = pilot.exercise_report()
    assert [r["id"] for r in report["exercises"]] == [f"P12.{i}" for i in range(1, 5)] + [f"DRILL12.{i}" for i in range(1, 8)]
    assert len(report["source_vocabulary"]) == 10
    assert len(report["controls"]) == 7
    assert report["exercises"][0]["computed_answer"]["data"]["amplitude"] == ["1", "0"]
    assert report["exercises"][1]["computed_answer"]["data"]["corner_histogram"] == [0, 2]
    assert report["exercises"][8]["computed_answer"]["data"]["corners"] == 2
    assert report["exercises"][9]["computed_answer"]["data"]["total_paths"] == 2
    for row in report["exercises"]:
        assert row["computed_answer"] == pilot.answer_for(row["request"])


def valid_document():
    request = pilot.kernel_request()
    return pilot.submission(request, pilot.answer_for(request))


@pytest.mark.parametrize("target", ["digest", "histogram", "amplitude", "directions", "empty",
                                    "count", "authority", "request", "bool_count", "extra"])
def test_full_request_and_answer_binding(target):
    document = valid_document()
    data = document["proposal"]["answer"]["data"]
    if target == "digest":
        document["proposal"]["input_sha256"] = "0" * 64
    elif target == "histogram":
        data["corner_histogram"][1] += 1
    elif target == "amplitude":
        data["amplitude"][0] = "2"
    elif target == "directions":
        data["direction_histograms"]["RL"][1] = 7
    elif target == "empty":
        data["empty_path_count"] = 1
    elif target == "count":
        data["total_paths"] = 7
    elif target == "authority":
        document["proposal"]["answer"]["authority_effect"] = "Promoted"
    elif target == "request":
        document["request"]["case_id"] = "changed"
    elif target == "bool_count":
        data["empty_path_count"] = False
    else:
        data["extra"] = 0
    assert pilot.evaluate(document)["verdict"] == "MISMATCH"


def test_binding_snapshot_and_strict_envelopes():
    document = valid_document()
    result = pilot.evaluate(document)
    assert result["verdict"] == "MATCH" and result["binding_ok"] is True
    document["request"]["mass"] = "0"
    assert result["request"]["mass"] == "1"
    for bad in (None, [], {"request": {}}, {"request": {}, "proposal": {}}):
        with pytest.raises(pilot.InvalidInput):
            pilot.evaluate(bad)
    clone = pilot.submission(result["request"], result["canonical"])
    result["request"]["mass"] = "9"
    assert clone["request"]["mass"] == "1"


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


@pytest.mark.parametrize("mode", ["default", "match", "mismatch", "invalid", "claim", "path", "empty"])
def test_real_cli(tmp_path, mode):
    document = valid_document()
    if mode == "mismatch":
        document["proposal"]["answer"]["data"]["total_paths"] = 99
    elif mode == "invalid":
        document["request"]["mass"] = "2/2"
    elif mode in ("claim", "path", "empty"):
        req = {"case_id": "claim", "kind": "claim", "claim": "physical_mass_or_spin"} if mode == "claim" else (
            {"case_id": "path", "kind": "path", "points": [[0, 0], [1, 1]]} if mode == "path" else pilot.kernel_request(steps=0))
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
    document["request"]["mass"] = "2/2"
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
    ("lose_corner", "count + (new != last)", "count", "math"),
    ("wrong_displacement", "x + delta, first", "x - delta, first", "asymmetric"),
    ("lose_multiplicity", "buckets[first + last][count] += ways", "buckets[first + last][count] += 1", "math"),
    ("imaginary_sign", "-power_imaginary * a, power_real * a", "power_imaginary * a, power_real * a", "math"),
    ("mass_discarded", "return epsilon * mass", "return epsilon", "weight"),
    ("first_ignored", "first is None or key[0] == first", "True", "direction"),
    ("last_ignored", "last is None or key[1] == last", "True", "direction"),
    ("empty_path_lost", "selected[0] += empty", "selected[0] += 0", "empty"),
    ("conditioned_empty_invented", "and first is None and last is None)", ")", "empty_condition"),
    ("spurious_entry_corner", "count + (new != last)", "count + (new == last)", "straight"),
    ("wrong_path_corners", "sum(a != b for a, b", "sum(a == b for a, b", "path"),
    ("nonunit_step", "end[0] - start[0] != 1", "end[0] - start[0] < 1", "step"),
    ("accept_physics", '"status": "REFUSED", "refusal": "ref<4>" if claim', '"status": "COMPUTED", "refusal": "ref<4>" if claim', "claim"),
    ("ignore_binding", 'matches = binding_ok and encoded(proposal', 'matches = encoded(proposal', "binding"),
    ("ignore_answer", 'matches = binding_ok and encoded(proposal["answer"]) == encoded(canonical)', 'matches = binding_ok', "answer"),
    ("rational_canonical", 'require(str(result) == value, "Unreduced or noncanonical rational")',
     'require(True, "Unreduced or noncanonical rational")', "noncanonical"),
)


def mutation_document(mode):
    req = pilot.kernel_request(steps=6)
    if mode == "asymmetric":
        req = pilot.kernel_request(steps=4, x=2, first="R", last="L")
    elif mode == "weight":
        req = pilot.kernel_request(steps=3, x=1, mass="-2/3", epsilon="3/2")
    elif mode == "direction":
        req = pilot.kernel_request(first="R", last="L")
    elif mode in ("empty", "empty_condition"):
        req = pilot.kernel_request(steps=0, first="R" if mode == "empty_condition" else None)
    elif mode == "straight":
        req = pilot.kernel_request(steps=3, x=3)
    elif mode == "path":
        req = {"case_id": "path", "kind": "path", "points": [[0, 0], [1, 1], [2, 0]]}
    elif mode == "step":
        req = {"case_id": "step", "kind": "step", "start": [0, 0], "end": [2, 1]}
    elif mode == "claim":
        req = {"case_id": "claim", "kind": "claim", "claim": "physical_mass_or_spin"}
    document = pilot.submission(req, pilot.answer_for(req))
    if mode == "binding":
        document["proposal"]["input_sha256"] = "0" * 64
    elif mode == "answer":
        document["proposal"]["answer"]["data"]["total_paths"] += 1
    elif mode == "noncanonical":
        document["request"]["mass"] = "2/2"
        document["proposal"]["input_sha256"] = pilot.digest(document["request"])
    return document


def test_compiled_cli_mutations(tmp_path):
    source = CODE.read_text(encoding="utf-8")
    records = []
    for name, old, new, mode in MUTATIONS:
        assert source.count(old) == 1, (name, source.count(old))
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
    destination = os.environ.get("PFP_PILOT_000018_MUTATION_OUTPUT")
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
    monkeypatch.setitem(pilot.SOURCE_FACTS, "DRILL12.5", {"data": {"corners": 3}})
    mismatched = pilot.exercise_report()
    assert [row["id"] for row in mismatched["exercises"] if row["verdict"] == "MISMATCH"] == ["DRILL12.5"]
    assert pilot.main(["--output-dir", str(tmp_path / "mismatch")]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "MISMATCH"
    assert json.loads((Path(output["output"]) / "receipt.json").read_bytes())["status"] == "MISMATCH"
