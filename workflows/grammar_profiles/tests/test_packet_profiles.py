import hashlib
import importlib.util
import json
import os
import runpy
import random
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PILOT_FILE = Path(os.environ.get("PFP_PARSE_UNDER_TEST", HERE.parent / "run.py"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pilot = load("pfp_parser_tested", PILOT_FILE)
reference = load("pfp_parser_reference", HERE / "ebnf_reference.py")
CASES = json.loads((HERE / "conformance_cases.json").read_text(encoding="utf-8"))
GRAMMARS = {
    "mss-boundary-v1": ("boundary.ebnf", "packet"),
    "historical-packet-v1": ("historical_packet.ebnf", "packet"),
    "quiz-packet-v1": ("quiz_packet.ebnf", "quiz_message"),
    "glyph-graph-v1": ("glyph_graph.ebnf", "glyph_graph"),
}
ORACLES = {profile: (reference.Grammar((HERE / "grammars" / file).read_text(encoding="utf-8")), start)
           for profile, (file, start) in GRAMMARS.items()}


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_retained_conformance_corpus(case):
    actual = pilot.inspect(case["text"].encode("utf-8"), case["profile"])
    assert (actual["status"] == "ACCEPTED") is case["accept"]
    grammar, start = ORACLES[case["profile"]]
    assert grammar.accepts(start, case["text"]) is case["accept"]
    assert actual["interpretation"] == "NOT_CHECKED"
    assert actual["authority_effect"] == "None"


NOVEL = [
    ("mss-boundary-v1", "<<>>", True),
    ("mss-boundary-v1", "<<a><a><>>", True),
    ("mss-boundary-v1", "<<><a>z>", False),
    ("mss-boundary-v1", "<<<><>>><a>", False),
    ("historical-packet-v1", "op<op<>>", True),
    ("historical-packet-v1", "op<<>op<><a>>", True),
    ("historical-packet-v1", "op<<<>>>", False),
    ("historical-packet-v1", "op<op<>>op<>", False),
    ("quiz-packet-v1", "ans<1<_,ref<7>>,<>,<a,a>>", True),
    ("quiz-packet-v1", "ask<ans<>>", True),
    ("quiz-packet-v1", "ans<<<>>>", True),
    ("quiz-packet-v1", "ans<>", False),
    ("quiz-packet-v1", "ref<01>", False),
    ("quiz-packet-v1", "ans<<a><b>>", False),
    ("glyph-graph-v1", "0<0a0<>0<>0>0a0", True),
    ("glyph-graph-v1", "a<>a", True),
    ("glyph-graph-v1", "a<bz9", True),
    ("glyph-graph-v1", "a<ba10", False),
    ("glyph-graph-v1", "ab", False),
    ("glyph-graph-v1", "a<><>b", False),
]


@pytest.mark.parametrize("profile,text,accept", NOVEL)
def test_independent_review_fixtures(profile, text, accept):
    assert (pilot.inspect(text.encode("ascii"), profile)["status"] == "ACCEPTED") is accept
    grammar, start = ORACLES[profile]
    assert grammar.accepts(start, text) is accept


def test_seeded_comparison_to_independent_ebnf():
    rng = random.Random(557)
    texts = {"".join(rng.choices("<>ab01_op,snrf", k=rng.randrange(16))) for _ in range(250)}
    texts.update({"<"+a+b+">" for a in ("a", "01", "<>", "<a>") for b in ("", "<>", "<b>", ",b")})
    for profile, (grammar, start) in ORACLES.items():
        for text in texts:
            assert (pilot.inspect(text.encode("ascii"), profile)["status"] == "ACCEPTED") == grammar.accepts(start, text), (profile, text)


def test_four_exercise_obligations():
    cases = pilot.exercise_report()["cases"]
    assert set(cases) == {f"quiz15.{i}" for i in range(1, 5)}
    classifications = cases["quiz15.1"]
    assert len(classifications) == 19
    assert [row["status"] == "ACCEPTED" for row in classifications[:18]] == [
        True,False,False, True,False,False, True,False,False,
        False,True,False, False,False,True, False,False,False,
    ]
    assert classifications[-1]["status"] == "REFUSED"
    for repair in cases["quiz15.2"]:
        assert repair["original"]["status"] == "REFUSED"
        assert repair["proposed"]["status"] == "ACCEPTED"
        assert repair["original"]["raw_sha256"] != repair["proposed"]["raw_sha256"]
        assert not repair["same_bytes"] and not repair["applied"]
    historical = cases["quiz15.3"]
    outer = historical["original"]["ast"]
    assert outer["kind"] == "application" and len(outer["children"]) == 3
    assert outer["children"][0] == {"kind": "atom", "value": "10"}
    assert [node["children"][1]["value"] for node in outer["children"][1:]] == ["a", "b"]
    assert historical["renamed_first_atom"]["status"] == "ACCEPTED"
    assert historical["renamed_first_atom"]["ast"]["children"][0]["value"] == "foo"
    assert historical["trailing_root"]["status"] == "REFUSED"
    seals = cases["quiz15.4"]
    assert seals["shape_only"]["lexical_shape_matches"]
    assert seals["shape_only"]["artifact_binding"] == "NOT_CHECKED"
    assert not seals["invalid_shape"]["lexical_shape_matches"]
    assert seals["bound_bytes"]["artifact_binding"] == "MATCH"
    assert seals["wrong_bytes"]["artifact_binding"] == "MISMATCH"


def test_ast_retains_duplicates_direction_and_word_spelling():
    boundary = pilot.parse(b"<<a><a><>>", "mss-boundary-v1")
    assert boundary["children"] == [{"kind": "atom", "value": "a"}]*2 + [{"kind": "difference"}]
    historical = pilot.parse(b"op<<>op<><01>>", "historical-packet-v1")
    assert historical["children"] == [{"kind": "difference"}, {"kind": "application", "children": []}, {"kind": "atom", "value": "01"}]
    graph = pilot.parse(b"a<>a<>b<az9<>a>bz9", "glyph-graph-v1")["items"]
    assert graph[:2] == [{"kind": "vertex", "value": "a"}]*2
    assert graph[2]["source"] == graph[3]["source"] == "a"
    assert graph[2]["direction"] == "<" and graph[3]["direction"] == ">"
    assert graph[2]["spelling"] == "b<az9" and graph[3]["spelling"] == "a>bz9"
    assert graph[2]["weight_suffix"] == "z9"


@pytest.mark.parametrize("raw", [b" <a>", b"<a>\n", b"<a>\r\n", b"<a>\x00", b"\xef\xbb\xbf<a>", b"\xff", "<\u0430>".encode("utf-8")])
def test_no_whitespace_or_unicode_repair(raw):
    result = pilot.inspect(raw, "mss-boundary-v1")
    assert result["status"] == "REFUSED"
    assert bytes.fromhex(result["raw_hex"]) == raw
    assert result["raw_sha256"] == hashlib.sha256(raw).hexdigest()


def test_limits_are_not_grammar_refutations():
    assert pilot.inspect(b"<" + b"a"*65534 + b">", "mss-boundary-v1")["status"] == "ACCEPTED"
    assert pilot.inspect(b"<" + b"a"*65535 + b">", "mss-boundary-v1")["status"] == "LIMIT_EXCEEDED"
    assert pilot.inspect(b"<"*65 + b">"*65, "mss-boundary-v1")["status"] == "ACCEPTED"
    assert pilot.inspect(b"<"*66 + b">"*66, "mss-boundary-v1")["status"] == "LIMIT_EXCEEDED"
    for profile, small, large in [
        ("mss-boundary-v1", b"<"+b"<>"*4095+b">", b"<"+b"<>"*4096+b">"),
        ("historical-packet-v1", b"op<"+b"<>"*4095+b">", b"op<"+b"<>"*4096+b">"),
        ("glyph-graph-v1", b"<>".join([b"a"]*4095), b"<>".join([b"a"]*4096)),
        ("quiz-packet-v1", b"ans<"+b",".join([b"a"]*4095)+b">", b"ans<"+b",".join([b"a"]*4096)+b">"),
    ]:
        assert pilot.inspect(small, profile)["status"] == "ACCEPTED"
        assert pilot.inspect(large, profile)["status"] == "LIMIT_EXCEEDED"
    assert pilot.repair_record(b"<a>", b"<a>", "mss-boundary-v1")["same_bytes"]


@pytest.mark.parametrize("value", ["0"*63, "0"*65, "G"+"0"*63, "g"+"0"*63, "0"*64+"\n", "0"*64+"\x00"])
def test_digest_full_match(value):
    assert not pilot.seal_record(value)["lexical_shape_matches"]


def test_contract_types_and_digest_binding():
    assert pilot.seal_record("0"*64)["artifact_binding"] == "NOT_CHECKED"
    assert pilot.seal_record("g"*64, b"")["artifact_binding"] == "MISMATCH"
    for raw in (None, "", bytearray(b"<>")):
        with pytest.raises(pilot.InvalidInput):
            pilot.parse(raw, "mss-boundary-v1")
        with pytest.raises(pilot.InvalidInput):
            pilot.inspect(raw, "mss-boundary-v1")
    with pytest.raises(pilot.InvalidInput):
        pilot.parse(b"<>", "not-a-profile")
    with pytest.raises(pilot.InvalidInput):
        pilot.seal_record(None)
    with pytest.raises(pilot.InvalidInput):
        pilot.seal_record("0"*64, "not-bytes")


def test_cli_routes_and_exact_custody(tmp_path, capsys):
    out = tmp_path / "runs"
    args = ["--output-dir", str(out)]
    assert pilot.main(args) == 0
    first = Path(json.loads(capsys.readouterr().out)["output"])
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    source = tmp_path / "raw.bin"
    source.write_bytes(b"a<bz9")
    custom = args + ["--input", str(source), "--profile", "glyph-graph-v1"]
    assert pilot.main(custom) == 0
    folder = Path(json.loads(capsys.readouterr().out)["output"])
    assert (folder / "input.bin").read_bytes() == b"a<bz9"
    report = json.loads((folder / "result.json").read_text())
    receipt = json.loads((folder / "receipt.json").read_text())
    assert receipt["input_sha256"] == pilot.sha(b"a<bz9")
    assert receipt["result_sha256"] == pilot.sha(pilot.canonical(report))
    assert receipt["code_sha256"] == pilot.sha(PILOT_FILE.read_bytes())
    assert receipt["network_calls"] == 0 and receipt["cost_usd"] == "0"
    assert receipt["result_sha256"] in (folder / "summary.md").read_text()
    source.write_bytes(b"a>b<>")
    assert pilot.main(custom) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    source.write_bytes(b"a"*65537)
    assert pilot.main(custom) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    source.unlink()
    assert pilot.main(custom) == 2
    capsys.readouterr()
    assert pilot.main(args + ["--profile", "glyph-graph-v1"]) == 2
    capsys.readouterr()
    assert pilot.main(args + ["--input", str(source)]) == 2
    capsys.readouterr()
    blocked = tmp_path / "file_not_dir"
    blocked.write_bytes(b"keep")
    assert pilot.main(["--output-dir", str(blocked)]) == 2
    capsys.readouterr()
    assert blocked.read_bytes() == b"keep"
    assert before == {p.name: p.read_bytes() for p in first.iterdir()}


def test_real_cli(tmp_path):
    completed = subprocess.run([sys.executable, str(PILOT_FILE), "--output-dir", str(tmp_path / "cli")],
                               capture_output=True, text=True, check=False, timeout=20)
    assert completed.returncode == 0, completed.stderr
    folder = Path(json.loads(completed.stdout)["output"])
    report = json.loads((folder / "result.json").read_text())
    assert report["cases"]["quiz15.4"]["shape_only"]["artifact_binding"] == "NOT_CHECKED"


def test_implementation_mutations_are_killed(tmp_path):
    original = PILOT_FILE.read_bytes()
    source = original.decode("utf-8")
    mutations = [
        ("trim_input", 'text = raw.decode("ascii")', 'text = raw.decode("ascii").strip()', "test_no_whitespace_or_unicode_repair"),
        ("accept_prefix", 'require(parser.pos == len(text), "Trailing bytes after the single root")', 'require(True, "Trailing bytes after the single root")', "test_four_exercise_obligations"),
        ("drop_empty_items", 'for item in self.text.split("<>"):', 'for item in filter(None, self.text.split("<>")):', "test_four_exercise_obligations"),
        ("digest_newline", 're.fullmatch(r"[0-9a-f]{64}", digest_text)', 're.match(r"[0-9a-f]{64}$", digest_text)', "test_digest_full_match"),
    ]
    observations = []
    for name, anchor, replacement, node in mutations:
        assert source.count(anchor) == 1, name
        mutant = tmp_path / (name + ".py")
        mutant.write_text(source.replace(anchor, replacement), encoding="utf-8")
        env = dict(os.environ, PFP_PARSE_UNDER_TEST=str(mutant), NO_COLOR="1")
        for variable in ("PFP_PARSE_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
            env.pop(variable, None)
        run = subprocess.run(
            [sys.executable, "-m", "pytest", str(Path(__file__).resolve())+"::"+node, "-q", "--color=no", "-o", "addopts=",
             "--import-mode=importlib", "--basetemp", str(tmp_path / name)],
            capture_output=True, text=True, env=env, check=False, timeout=40)
        assert run.returncode == 1, (name, run.stdout, run.stderr)
        failures = [line for line in run.stdout.splitlines() if line.startswith("FAILED ")]
        assert failures and all(node in line for line in failures)
        observations.append({
            "name": name, "target": str(PILOT_FILE), "anchor": anchor, "replacement": replacement,
            "applied": mutant.read_text(encoding="utf-8") == source.replace(anchor, replacement),
            "mutant_sha256": pilot.sha(mutant.read_bytes()), "failed_nodes": failures, "exit_code": run.returncode,
            "original_unchanged": PILOT_FILE.read_bytes() == original, "original_sha256": pilot.sha(original),
        })
    if output := os.environ.get("PFP_PARSE_MUTATION_OUTPUT"):
        Path(output).write_text(json.dumps(observations, indent=2)+"\n", encoding="utf-8")


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(PILOT_FILE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(PILOT_FILE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "COMPUTED"
