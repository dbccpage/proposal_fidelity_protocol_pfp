import hashlib
import importlib.util
import itertools
import json
import os
import runpy
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest

PILOT_FILE = Path(os.environ.get("PFP_REWRITE_UNDER_TEST", Path(__file__).resolve().parents[1] / "run.py"))
spec = importlib.util.spec_from_file_location("pfp_rewrite_under_test", PILOT_FILE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def test_four_exercise_obligations():
    report = pilot.exercise_report()
    cases = report["cases"]
    assert set(cases) == {f"quiz18.{i}" for i in range(1, 5)}
    original, extended = cases["quiz18.1"], cases["quiz18.2"]
    assert original["normal_forms"] == ["ae", "dc"] and original["complete"]
    assert not original["unique_normal_form"] and original["global_confluence"] == "DISPROVED"
    assert len(original["steps"]) == 2
    assert extended["normal_forms"] == ["e"] and extended["unique_normal_form"]
    assert len(extended["steps"]) == 4 and extended["rules_length_decreasing"]
    assert extended["global_confluence"] == "NOT_CHECKED"
    assert cases["quiz18.3"]["same_normal_form"] and cases["quiz18.3"]["different_protected_counts"]
    assert not cases["quiz18.3"]["protected_query_descends"]
    codec = cases["quiz18.4"]
    assert codec["decoded_hex"] == [b"abc".hex(), b"e".hex()]
    assert codec["records"][0]["normal_form"] == codec["records"][1]["normal_form"] == "e"
    assert codec["records"][0] != codec["records"][1]
    assert codec["retained_original_required"] and not codec["normal_form_alone_lossless"]


@pytest.mark.parametrize("presentation", ["original", "extended"])
def test_all_words_through_length_five_against_recursive_oracle(presentation):
    replacements = {"ab": "d", "bc": "e"}
    if presentation == "extended":
        replacements.update(dc="e", ae="e")

    @lru_cache(None)
    def normal_forms(value):
        descendants = {value[:i] + replacements[value[i:i+2]] + value[i+2:]
                       for i in range(len(value) - 1) if value[i:i+2] in replacements}
        return frozenset().union(*(normal_forms(v) for v in descendants)) if descendants else frozenset([value])

    for length in range(6):
        for letters in itertools.product("abcde", repeat=length):
            value = "".join(letters)
            result = pilot.explore(value.encode(), presentation)
            assert result["complete"]
            assert result["normal_forms"] == sorted(normal_forms(value)), value
            assert result["protected_a_count"] == value.count("a")
            assert result["input_sha256"] == hashlib.sha256(value.encode()).hexdigest()
            assert result["presentation_sha256"] == pilot.digest(pilot.rules(presentation))


@pytest.mark.parametrize("presentation,value,expected", [
    ("original", "ababc", ["dae", "ddc"]), ("extended", "ababc", ["de"]),
    ("original", "abcabc", ["aeae", "aedc", "dcae", "dcdc"]),
    ("extended", "abcabc", ["ee"]), ("original", "", [""]), ("extended", "e", ["e"]),
])
def test_known_branching_examples(presentation, value, expected):
    report = pilot.explore(value.encode(), presentation)
    assert report["normal_forms"] == expected and report["complete"]


def test_original_not_silently_extended_and_rule_tuple_immutable():
    assert isinstance(pilot.ORIGINAL, tuple) and all(isinstance(row, tuple) for row in pilot.ORIGINAL)
    assert pilot.explore(b"dc", "original")["normal_forms"] == ["dc"]
    assert pilot.explore(b"dc", "extended")["normal_forms"] == ["e"]
    assert pilot.explore(b"abc", "original")["presentation_sha256"] != pilot.explore(b"abc", "extended")["presentation_sha256"]


def test_every_redex_position_and_overlapping_choices():
    steps = pilot.steps("ababc", "original")
    actual = {(s["offset"], s["to"], s["rule"]) for s in steps}
    assert actual == {(0, "dabc", "ab_d"), (2, "abdc", "ab_d"), (3, "abae", "bc_e")}
    assert len(steps) == 3
    report = pilot.explore(b"abcabc", "original")
    for edge in report["steps"]:
        assert edge["from"] in report["states"] and edge["to"] in report["states"]
        assert len(edge["to"]) == len(edge["from"]) - 1
        assert pilot.replay(edge["from"].encode(), [edge], "original") == edge["to"].encode()


@pytest.mark.parametrize("bound", [1, 2, 3, 4, 1024])
def test_budget_cannot_establish_uniqueness(bound):
    result = pilot.explore(b"abc", "extended", bound)
    if bound < 4:
        assert not result["complete"] and result["unique_normal_form"] is None
        assert result["cut_step"] is not None
    else:
        assert result["complete"] and result["unique_normal_form"]
        assert result["normal_forms"] == ["e"] and result["cut_step"] is None
    # Complete even at bound one when the input itself is already irreducible.
    assert pilot.explore(b"e", "extended", 1)["complete"]


@pytest.mark.parametrize("bad", [True, False, 0, -1, 1025, 1.0, "1", None])
def test_invalid_state_budget(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.explore(b"abc", "original", bad)


@pytest.mark.parametrize("raw", [b" abc", b"abc ", b"abc\n", b"abc\r\n", b"f", b"\x00", b"\xff",
                                 "abc", bytearray(b"abc"), "\u0430bc".encode(), b"a" * 33])
def test_exact_word_domain(raw):
    with pytest.raises(pilot.InvalidInput):
        pilot.word(raw)


@pytest.mark.parametrize("presentation", ["Original", "", None, "complete", 1])
def test_unknown_presentation(presentation):
    with pytest.raises(pilot.InvalidInput):
        pilot.explore(b"abc", presentation)


def test_trace_replay_both_branches_and_stopped_prefix():
    graph = pilot.explore(b"abc", "extended")
    for first in [s for s in graph["steps"] if s["from"] == "abc"]:
        second = next(s for s in graph["steps"] if s["from"] == first["to"])
        assert pilot.replay(b"abc", [first, second], "extended") == b"e"
        assert pilot.replay(b"abc", [first], "extended") == first["to"].encode()
    assert pilot.replay(b"abc", [], "original") == b"abc"
    with pytest.raises(pilot.InvalidInput):
        pilot.replay(b"abc", {}, "original")


@pytest.mark.parametrize("mutation", [
    lambda e: e.update(offset=True), lambda e: e.update(offset=1), lambda e: e.update(rule="dc_e"),
    lambda e: e.update(**{"from": "bc"}), lambda e: e.update(to="e"), lambda e: e.update(extra=True),
])
def test_forged_trace_rejected(mutation):
    edge = pilot.steps("abc", "original")[0]
    mutation(edge)
    with pytest.raises(pilot.InvalidInput):
        pilot.replay(b"abc", [edge], "original")


@pytest.mark.parametrize("raw,presentation,nf", [(b"abc", "extended", "e"), (b"e", "extended", "e"),
                                                (b"abc", "original", "ae"), (b"abc", "original", "dc"),
                                                (b"", "original", ""), (b"a" * 32, "original", "a" * 32)])
def test_retained_original_codec(raw, presentation, nf):
    record = pilot.encode(raw, nf, presentation)
    assert pilot.decode(record) == raw
    assert record["original_hex"] == raw.hex()
    assert record["original_sha256"] == hashlib.sha256(raw).hexdigest()
    assert record["normal_form"] == nf


@pytest.mark.parametrize("nf", ["abc", "dc", "d", "ee", "", "e\n", 1, "\u0435"])
def test_fabricated_reducible_or_malformed_first_component(nf):
    with pytest.raises((pilot.InvalidInput, ValueError)):
        pilot.encode(b"abc", nf, "extended")


@pytest.mark.parametrize("mutate", [
    lambda r: r.pop("original_hex"), lambda r: r.update(original_sha256="0" * 64),
    lambda r: r.update(original_hex=" 616263"), lambda r: r.update(original_hex="GG"),
    lambda r: r.update(original_hex=0), lambda r: r.update(original_hex="61" * 33),
    lambda r: r.update(original_hex="65"), lambda r: r.update(normal_form="d"),
    lambda r: r.update(presentation="original"), lambda r: r.update(extra=True),
])
def test_lossy_or_tampered_record_rejected(mutate):
    record = pilot.encode(b"abc", "e", "extended")
    mutate(record)
    with pytest.raises((pilot.InvalidInput, ValueError)):
        pilot.decode(record)


def test_large_branching_refuses_codec_without_complete_search():
    raw = b"abc" * 10
    result = pilot.explore(raw, "extended")
    assert not result["complete"] and result["unique_normal_form"] is None
    assert len(result["states"]) <= pilot.MAX_STATES
    with pytest.raises(pilot.InvalidInput):
        pilot.encode(raw, "e" * 10, "extended")


def test_main_routes_custody_and_no_overwrite(tmp_path, capsys):
    out = tmp_path / "runs"
    args = ["--output-dir", str(out)]
    assert pilot.main(args) == 0
    first = Path(json.loads(capsys.readouterr().out)["output"])
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    receipt = json.loads(before["receipt.json"])
    assert receipt["result_sha256"] == pilot.digest(json.loads(before["result.json"]))
    assert receipt["code_sha256"] == hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest()
    assert receipt["cost_usd"] == "0" and receipt["network_calls"] == 0
    assert receipt["result_sha256"] in before["summary.md"].decode()
    source = tmp_path / "word.bin"
    source.write_bytes(b"abc")
    assert pilot.main(args + ["--input", str(source), "--presentation", "original"]) == 0
    folder = Path(json.loads(capsys.readouterr().out)["output"])
    assert (folder / "input.bin").read_bytes() == b"abc"
    assert json.loads((folder / "receipt.json").read_text())["input_sha256"] == hashlib.sha256(b"abc").hexdigest()
    assert pilot.main(args + ["--input", str(source), "--presentation", "extended", "--max-states", "1"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "INCOMPLETE"
    for extra in [["--input", str(source)], ["--presentation", "original"], ["--max-states", "2"]]:
        assert pilot.main(args + extra) == 2
        capsys.readouterr()
    source.write_bytes(b"a" * 33)
    assert pilot.main(args + ["--input", str(source), "--presentation", "original"]) == 2
    capsys.readouterr()
    source.unlink()
    assert pilot.main(args + ["--input", str(source), "--presentation", "original"]) == 2
    capsys.readouterr()
    blocked = tmp_path / "file"
    blocked.write_bytes(b"keep")
    assert pilot.main(["--output-dir", str(blocked)]) == 2
    capsys.readouterr()
    assert blocked.read_bytes() == b"keep"
    assert before == {p.name: p.read_bytes() for p in first.iterdir()}


def test_real_cli(tmp_path):
    run = subprocess.run([sys.executable, str(PILOT_FILE), "--output-dir", str(tmp_path / "cli")],
                         capture_output=True, text=True, check=False, timeout=20)
    assert run.returncode == 0, run.stderr
    folder = Path(json.loads(run.stdout)["output"])
    assert json.loads((folder / "result.json").read_text())["cases"]["quiz18.1"]["normal_forms"] == ["ae", "dc"]


def test_implementation_mutations_are_killed(tmp_path):
    original = PILOT_FILE.read_bytes()
    source = original.decode("utf-8")
    mutations = [
        ("first_redex_only", "outgoing = steps(current, presentation)", "outgoing = steps(current, presentation)[:1]", "test_four_exercise_obligations"),
        ("extend_silently", 'return ORIGINAL if presentation == "original" else EXTENDED', "return EXTENDED", "test_original_not_silently_extended_and_rule_tuple_immutable"),
        ("peak_as_confluence", '"DISPROVED" if len(normal) > 1 else "NOT_CHECKED"', '"DISPROVED" if len(normal) > 1 else "PROVED"', "test_four_exercise_obligations"),
        ("lost_protected_query", 'raw.count(b"a")', 'sum(w.count("a") for w in normal)', "test_four_exercise_obligations"),
        ("budget_as_complete", '"complete": complete,', '"complete": True,', "test_budget_cannot_establish_uniqueness"),
        ("fabricated_normal_form", 'require(normal_form in result["normal_forms"],', "require(True,", "test_fabricated_reducible_or_malformed_first_component"),
        ("decode_normal_form_only", "    return raw\n", '    return record["normal_form"].encode("ascii")\n', "test_retained_original_codec"),
    ]
    evidence = []
    for name, anchor, replacement, test_name in mutations:
        assert source.count(anchor) == 1, (name, "nonunique anchor")
        mutant = tmp_path / (name + ".py")
        mutant.write_text(source.replace(anchor, replacement), encoding="utf-8")
        env = dict(os.environ, PFP_REWRITE_UNDER_TEST=str(mutant), NO_COLOR="1")
        for variable in ("PFP_REWRITE_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
            env.pop(variable, None)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", str(Path(__file__).resolve()) + "::" + test_name,
             "-q", "--color=no", "-o", "addopts=", "--import-mode=importlib", "--basetemp", str(tmp_path / name)],
            env=env, capture_output=True, text=True, check=False, timeout=40)
        assert completed.returncode == 1, (name, completed.stdout, completed.stderr)
        failures = [line for line in completed.stdout.splitlines() if line.startswith("FAILED ")]
        assert failures and all(test_name in line for line in failures)
        evidence.append({
            "name": name, "target": str(PILOT_FILE), "anchor": anchor, "replacement": replacement,
            "applied": mutant.read_text(encoding="utf-8") == source.replace(anchor, replacement),
            "mutant_sha256": hashlib.sha256(mutant.read_bytes()).hexdigest(),
            "failed_nodes": failures, "exit_code": completed.returncode,
            "original_unchanged": PILOT_FILE.read_bytes() == original,
            "original_sha256": hashlib.sha256(original).hexdigest(),
        })
    assert len(evidence) == 7
    if output := os.environ.get("PFP_REWRITE_MUTATION_OUTPUT"):
        Path(output).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(PILOT_FILE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(PILOT_FILE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "COMPUTED"
