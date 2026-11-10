import copy
import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from types import ModuleType

import pytest

CODE = Path(__file__).resolve().parents[2] / "run.py"
SPEC = importlib.util.spec_from_file_location("typed_engine_candidate", CODE)
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def graph(module=M):
    dep, _ = module.dependency()
    return module.build_graph(dep.demo_request())


def job(module=M):
    return module.demo_job().model_dump()


def check_query_change(module=M):
    left = graph(module)
    req = left.request.payload.model_dump()
    req["cochain"] = ["1", "2", "4"]
    right = module.build_graph(req)
    assert left.document.summary == right.document.summary
    assert left.result.answer_json != right.result.answer_json
    with pytest.raises(ValueError, match="query changed"):
        module.checked_transport(module.proposal(left, right))


def test_demo_actual_query_and_typed_edges():
    value = job()
    result = M.evaluate(value)
    assert result["status"] == "PRESERVED"
    assert result["authority_effect"] == "None"
    assert result["general_semantic_equivalence_claim"] is False
    left = value["transport"]["domain"]
    answer = json.loads(left["result"]["answer_json"])
    assert answer["data"]["value"] == [{"coefficient": "3", "radicand": 1}, {"coefficient": "-2/3", "radicand": 1}, {"coefficient": "1/2", "radicand": 1}]
    assert {x["subject"] for x in left["edges"]} == {"source_span", "request_span", "request", "checker", "test", "result"}
    assert value["transport"]["domain_sha256"] != value["transport"]["codomain_sha256"]
    raw = left["document"]["text"].encode("utf-8")
    span = left["request_span"]
    assert M.decode(raw[span["start"]:span["end"]]) == left["request"]["payload"]


def test_identity_and_associative_composition_exact_records():
    start = graph()
    # Three frames include a multibyte prefix and CRLF; offsets are bytes, not characters.
    first = M.reframe(start, "\u03a9\n", "\nA", 1)
    second = M.reframe(first.codomain, "\r\n\u00e9 request\r\n", "B", 2)
    third = M.reframe(second.codomain, "Third:\n", "\nC", 0)
    assert M.encoded(M.compose(M.identity(start), first)) == M.encoded(first)
    assert M.encoded(M.compose(first, M.identity(first.codomain))) == M.encoded(first)
    lhs = M.compose(M.compose(first, second), third)
    rhs = M.compose(first, M.compose(second, third))
    assert M.encoded(lhs) == M.encoded(rhs) == M.encoded(M.proposal(start, third.codomain))
    assert lhs.request_map.before == start.request_span
    assert lhs.request_map.after == third.codomain.request_span
    assert first.codomain.request_span.start == 3
    assert M.encoded(M.identity(start).domain) == M.encoded(start)


@pytest.mark.parametrize("x", [["0", "0", "0"], ["-2/3", "5/7", "3"], ["1000000", "1/1000000", "-1"]])
def test_request_variants_and_unweighted_reuse(x):
    for kind, cutoff in (("complement", 2), ("unweighted", 1), ("unweighted", 2)):
        req = graph().request.payload.model_dump()
        req.update(kind=kind, cutoff=cutoff, cochain=x)
        base = M.build_graph(req)
        assert M.checked_transport(M.reframe(base, "", "", None)).domain.result.answer_sha256 == base.result.answer_sha256


def test_summary_preserving_answer_change_is_not_preservation():
    check_query_change()


def test_different_intermediate_version_and_wrong_type():
    base = graph()
    first = M.reframe(base, "one", "", None)
    other = M.reframe(base, "two", "", None)
    with pytest.raises(ValueError, match="intermediate"):
        M.compose(first, other)
    for field in ("domain_type", "codomain_type"):
        raw = first.model_dump()
        raw[field] = "pilot21_request"
        with pytest.raises(ValueError):
            M.checked_transport(raw)


GRAPH_EDITS = [
    ("source", "sha256", "0" * 64), ("checker", "source_sha256", "0" * 64),
    ("checker", "core_sha256", "0" * 64), ("source_span", "parent", "document"),
    ("source_span", "parent_sha256", "0" * 64), ("source_span", "sha256", "0" * 64),
    ("request_span", "start", True), ("request_span", "start", -1), ("request_span", "end", 65537),
    ("request_span", "end", 0), ("request_span", "parent_sha256", "0" * 64),
    ("request_span", "sha256", "0" * 64), ("document", "sha256", "0" * 64),
    ("request", "sha256", "0" * 64), ("result", "request_sha256", "0" * 64),
    ("result", "answer_json", "{}"), ("result", "answer_sha256", "0" * 64),
    ("test", "expected_sha256", "0" * 64), ("source", "path", "../../unbound.py"),
    ("checker", "entrypoint", "eval"), ("test", "query", "summary"),
]


@pytest.mark.parametrize("edit", GRAPH_EDITS, ids=[f"graph_{i}" for i in range(len(GRAPH_EDITS))])
def test_graph_binding_controls(edit):
    data = graph().model_dump()
    section, key, value = edit
    data[section][key] = value
    with pytest.raises(ValueError):
        M.checked_graph(data)


def test_span_boundaries_source_locator_and_request_substitution():
    data = graph().model_dump()
    dep, raw = M.dependency()
    data["source_span"] = M.make_span(raw, 0, 5, "source_span", "source")
    with pytest.raises(ValueError, match="source passage"):
        M.checked_graph(data)
    data = M.reframe(graph(), "\u03a9", "", None).codomain.model_dump()
    raw = data["document"]["text"].encode("utf-8")
    data["request_span"] = M.make_span(raw, 1, data["request_span"]["end"], "request_span", "document")
    with pytest.raises(UnicodeError):
        M.checked_graph(data)
    data = graph().model_dump()
    data["request"]["payload"]["cochain"][0] = "0"
    with pytest.raises(ValueError, match="Document/request"):
        M.checked_graph(data)
    data = graph().model_dump()
    data["request_span"]["end"] = len(data["document"]["text"].encode()) + 1
    with pytest.raises(ValueError, match="interval"):
        M.checked_graph(data)


@pytest.mark.parametrize("mode", ["missing_edge", "extra_edge", "wrong_edge", "missing_obligation", "extra_field", "payload_boolean", "wrong_node_id"])
def test_complete_dependency_graph_and_strict_schema(mode):
    data = graph().model_dump()
    if mode == "missing_edge":
        data["edges"].pop()
    elif mode == "extra_edge":
        data["edges"].append(data["edges"][0])
    elif mode == "wrong_edge":
        data["edges"][0]["dependency"] = "result"
    elif mode == "missing_obligation":
        data["obligations"].pop()
    elif mode == "extra_field":
        data["document"]["truth"] = True
    elif mode == "payload_boolean":
        data["request"]["payload"]["degree"] = True
    else:
        data["request_span"]["id"] = "source_span"
    with pytest.raises(ValueError):
        M.checked_graph(data)


@pytest.mark.parametrize("field", ["domain_sha256", "codomain_sha256", "source_map", "request_map", "obligations"])
def test_transport_custody(field):
    arrow = job()["transport"]
    if field.endswith("sha256"):
        arrow[field] = "0" * 64
    elif field.endswith("map"):
        arrow[field]["after"]["sha256"] = "0" * 64
    else:
        arrow[field].pop()
    with pytest.raises(ValueError):
        M.checked_transport(arrow)


def test_output_snapshots_are_not_input_aliases():
    data = job()
    arrow = M.checked_transport(data["transport"])
    before = M.encoded(arrow)
    data["transport"]["domain"]["request"]["payload"]["cochain"][0] = "99"
    assert M.encoded(arrow) == before
    fields = dict(graph())
    fields["obligations"] = list(fields["obligations"])
    bypass = M.Graph.model_construct(**fields)
    assert M.checked_graph(bypass)[0].kind == "engine_graph_v1"
    bypass.obligations.clear()
    with pytest.raises(ValueError):
        M.checked_graph(bypass)


@pytest.mark.parametrize("raw,format", [(b"", "json"), (b"{", "json"), (b"\xff", "json"),
    (b'{"x":1,"x":2}', "json"), (b"NaN", "json"), (b"1.5", "json"), (b'"\\ud800"', "json"),
    (b"x: 1\nx: 2\n", "yaml"), (b"x: &a [1]\ny: *a\n", "yaml"), (b"!!python/object:abc {}", "yaml"),
    (b"x: .nan", "yaml"), (b"2001-01-01", "yaml"), (b"1: hi", "yaml"), (b"{}", "unknown"),
    (b"a" * (M.MAX_BYTES + 1), "json")], ids=[f"wire_{i}" for i in range(15)])
def test_wire_rejections(raw, format):
    with pytest.raises((ValueError, TypeError, M.yaml.YAMLError)):
        M.decode(raw, format)


def test_json_and_yaml_twins_exact_replay():
    data = job()
    assert M.encoded(M.decode(M.yaml_bytes(data), "yaml")) == M.encoded(data)
    assert M.evaluate(M.decode(M.yaml_bytes(data), "yaml")) == M.evaluate(data)
    for value in (None, True, False, 3, "\u03a9", [1, "a"], {"one": 1}):
        assert M.decode(M.yaml_bytes(value), "yaml") == value


@pytest.mark.parametrize("value", [(1,), 1.5, 10**19, {1: "x"}, [0] * 257, {str(i): i for i in range(65)}, "x" * 65537], ids=[f"bound_{i}" for i in range(7)])
def test_recursive_bounds(value):
    with pytest.raises(ValueError):
        M.json_tree(value)


def test_depth_and_reframe_bounds(monkeypatch):
    value = []
    for _ in range(25):
        value = [value]
    with pytest.raises(ValueError):
        M.json_tree(value)
    for prefix, suffix, indent in ((3, "", None), ("", [], None), ("", "", True), ("", "", -1), ("", "", 5)):
        with pytest.raises(ValueError):
            M.reframe(graph(), prefix, suffix, indent)
    original = M.decode
    monkeypatch.setattr(M, "decode", lambda *args: {})
    with pytest.raises(ValueError, match="twin mismatch"):
        M.yaml_bytes({"not": "empty"})
    monkeypatch.setattr(M, "decode", original)


def test_dependency_pins_and_missing(monkeypatch):
    original = M.CHECKER_SHA
    monkeypatch.setattr(M, "CHECKER_SHA", "0" * 64)
    with pytest.raises(ValueError, match="pilot21 changed") as caught:
        M.dependency()
    assert "pilot_0000046" in str(caught.value) and f"expected sha256 {'0' * 64}, found {original}" in str(caught.value)
    monkeypatch.setattr(M, "CHECKER_SHA", original)
    core_sha = M.CORE_SHA
    monkeypatch.setattr(M, "CORE_SHA", "0" * 64)
    with pytest.raises(ValueError, match="pilot17 changed") as caught:
        M.dependency()
    assert "pilot_0000042" in str(caught.value) and f"found {core_sha}" in str(caught.value)
    monkeypatch.setattr(M, "CHECKER_PATH", "missing/pilot.py")
    with pytest.raises(ValueError, match="unavailable"):
        M.dependency()


def test_typed_outputs_and_receipt_strictness(tmp_path):
    report = M.PreservedReport.model_validate(M.evaluate(job()))
    for invalid in (True, 0, "false"):
        row = report.model_dump()
        row["general_semantic_equivalence_claim"] = invalid
        with pytest.raises(ValueError):
            M.PreservedReport.model_validate(row)
    assert M.typed(M.PreservedReport, M.decode(M.yaml_bytes(report), "yaml")) == report
    for model, status in ((M.RejectedReport, "REJECTED"), (M.RefusedReport, "REFUSED")):
        value = M.rejection(ValueError("deliberate"))[0] if model is M.RejectedReport else model(status=status, reason="deliberate")
        assert M.typed(model, M.decode(M.yaml_bytes(value), "yaml")) == value
        with pytest.raises(ValueError):
            model.model_validate({"status": status, "reason": 3})
    status, stdout = M.run_file(None, tmp_path)
    folder = Path(json.loads(stdout)["output"])
    row = M.decode((folder / "receipt.json").read_bytes())
    for key, value in (("input_complete", False), ("input_complete", 1), ("model_calls", True), ("cost_usd", 0)):
        bad = copy.deepcopy(row)
        bad[key] = value
        with pytest.raises(ValueError):
            M.Receipt.model_validate(bad)
    del row["artifact_sha256"]["result.yaml"]
    with pytest.raises(ValueError):
        M.Receipt.model_validate(row)


def test_oversized_input_retained_without_whole_file_memory_read(tmp_path, monkeypatch):
    source = tmp_path / "oversize.bin"
    raw = b"x" * (M.MAX_BYTES + 100)
    source.write_bytes(raw)
    original = Path.read_bytes
    def guarded(path):
        assert path.name != "input.bin", "Oversized captured input read into memory"
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", guarded)
    status, stdout = M.run_file(source, tmp_path / "output")
    assert status == "REJECTED"
    folder = Path(json.loads(stdout)["output"])
    assert original(folder / "input.bin") == raw
    assert M.decode(original(folder / "receipt.json"))["input_sha256"] == M.sha(raw)


def inspect_bundle(reply, raw, stdout):
    folder = Path(reply["output"])
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert receipt["input_complete"] is True and receipt["input_bytes"] == len(raw)
    assert (folder / "input.bin").read_bytes() == raw
    assert (folder / "stdout.txt").read_bytes() == stdout
    assert (folder / "stderr.txt").read_bytes() == b""
    for name, sha in receipt["artifact_sha256"].items():
        assert M.sha((folder / name).read_bytes()) == sha
    assert M.decode((folder / "receipt.yaml").read_bytes(), "yaml") == receipt
    report = M.decode((folder / "result.json").read_bytes())
    assert M.decode((folder / "result.yaml").read_bytes(), "yaml") == report
    assert receipt["code_sha256"] == M.sha(CODE.read_bytes())
    assert receipt["checker_sha256"] == M.CHECKER_SHA and receipt["core_sha256"] == M.CORE_SHA
    assert receipt["model_calls"] == 0 and receipt["cost_usd"] == "0"
    return report


@pytest.mark.parametrize("mode", ["demo", "json", "yaml", "bad", "changed", "oversized"])
def test_fresh_cli_receipts(tmp_path, mode):
    args = [sys.executable, "-B", str(CODE), "--output-dir", str(tmp_path / "out")]
    data = job()
    raw = M.encoded(data)
    if mode == "changed":
        original = data["transport"]["domain"]
        req = copy.deepcopy(original["request"]["payload"])
        req["cochain"][0] = "9"
        data["transport"] = M.proposal(original, M.build_graph(req)).model_dump()
        raw = M.encoded(data)
    if mode == "bad":
        raw = b'{"surrogate":"\\ud800"}'
    elif mode == "yaml":
        raw = M.yaml_bytes(data)
        args.extend(["--format", "yaml"])
    elif mode == "oversized":
        raw = b"a" * (M.MAX_BYTES + 1)
    if mode != "demo":
        source = tmp_path / "input.bin"
        source.write_bytes(raw)
        args.extend(["--input", str(source)])
    result = subprocess.run(args, capture_output=True, check=False)
    assert result.returncode == int(mode in ("bad", "changed", "oversized"))
    assert result.stderr == b""
    report = inspect_bundle(json.loads(result.stdout), raw, result.stdout)
    assert report["status"] == ("REJECTED" if result.returncode else "PRESERVED")


def test_in_process_cli_and_operational_limits(tmp_path, capsys, monkeypatch):
    assert M.main(["--output-dir", str(tmp_path / "demo")]) == 0
    capsys.readouterr()
    file = tmp_path / "bad.json"
    file.write_bytes(b"{")
    assert M.main(["--input", str(file), "--output-dir", str(tmp_path / "bad")]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "REJECTED"
    assert M.main(["--input", str(tmp_path / "missing"), "--output-dir", str(tmp_path / "missing_run")]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"


def test_long_validation_diagnostic_real_cli_is_completed(tmp_path, monkeypatch, capsys):
    raw = M.encoded({"x" * 60000: None, "y" * 60000: None})
    assert len(raw) == 120017 and M.sha(raw) == "e963cac4f8d9d43c6affe71e57527060d636a67c60406242bc0f71307558d1a4"
    decoded = M.decode(raw)
    with pytest.raises(ValueError) as error:
        M.evaluate(decoded)
    expected_diagnostic = str(error.value).encode("utf-8", errors="backslashreplace")
    assert len(expected_diagnostic) > 65536
    for index, submitted in enumerate((M.encoded({"x": None, "y": None}), raw)):
        source = tmp_path / f"invalid_{index}.json"
        source.write_bytes(submitted)
        completed = subprocess.run([sys.executable, "-B", str(CODE), "--input", str(source),
                                    "--output-dir", str(tmp_path / f"runs_{index}")], capture_output=True, check=False)
        assert completed.returncode == 1 and completed.stderr == b""
        reply = json.loads(completed.stdout)
        report = inspect_bundle(reply, submitted, completed.stdout)
        assert report["status"] == "REJECTED" and len(report["reason"]) <= 1200
        folder = Path(reply["output"])
        diagnostic = (folder / "diagnostic.txt").read_bytes()
        assert report["diagnostic_bytes"] == len(diagnostic)
        assert report["diagnostic_sha256"] == M.sha(diagnostic)
        if index:
            assert diagnostic == expected_diagnostic
    def fail(*args):
        raise OSError("deliberate output failure")
    monkeypatch.setattr(M, "run_file", fail)
    assert M.main(["--output-dir", str(tmp_path / "fail")]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"


def mutation_guard(module, mode):
    if mode == "diagnostic":
        report, raw = module.rejection(ValueError("x" * 120788))
        assert len(report.reason) <= 1200 and raw == b"x" * 120788
        assert report.diagnostic_bytes == len(raw) and report.diagnostic_sha256 == module.sha(raw)
    elif mode == "query":
        check_query_change(module)
    elif mode in ("edges", "obligations", "result", "source", "request", "document"):
        g = graph(module).model_dump()
        if mode == "edges":
            g["edges"].pop()
        elif mode == "obligations":
            g["obligations"].pop()
        elif mode == "result":
            g["result"]["answer_json"] = "{}"
        elif mode == "source":
            g["source"]["sha256"] = "0" * 64
        elif mode == "request":
            g["request"]["sha256"] = "0" * 64
            g["result"]["request_sha256"] = "0" * 64
        else:
            g["document"]["sha256"] = "0" * 64
        with pytest.raises(ValueError):
            module.checked_graph(g)
    elif mode == "span":
        span = module.Span.model_validate(module.make_span(b"abc", 0, 1, "request_span", "document"))
        span = span.model_copy(update={"sha256": "0" * 64})
        with pytest.raises(ValueError):
            module.check_span(span, b"abc", "request_span", "document")
    elif mode == "composition":
        original = graph(module)
        first = module.identity(original)
        # Same byte spans, different intermediate graph summary/version: the
        # separate span-compatibility guard must not mask the version mutation.
        other = module.build_graph(original.request.payload, summary="Other summary")
        second = module.reframe(other, "two", "", None)
        with pytest.raises(ValueError):
            module.compose(first, second)
    elif mode in ("endpoint", "mapping", "arrow_obligations"):
        arrow = job(module)["transport"]
        if mode == "endpoint":
            arrow["domain_sha256"] = "0" * 64
        elif mode == "mapping":
            arrow["request_map"]["after"]["sha256"] = "0" * 64
        else:
            arrow["obligations"].pop()
        with pytest.raises(ValueError):
            module.checked_transport(arrow)
    elif mode == "pin":
        module.CHECKER_SHA = "0" * 64
        with pytest.raises(ValueError):
            module.dependency()
    else:
        raw = b'{"x":1,"x":2}' if mode == "duplicate" else b"x: &a 1\ny: *a"
        with pytest.raises(ValueError):
            module.decode(raw, "json" if mode == "duplicate" else "yaml")


MUTATIONS = [
    ("diagnostic", 'diagnostic.decode("utf-8")[:PUBLIC_REASON_CHARS]', 'diagnostic.decode("utf-8")'),
    ("query", 'require(before == after, "Protected executable query changed")', 'require(True, "Protected executable query changed")'),
    ("edges", 'require(edges == sorted(EDGE_ROWS),', 'require(True,'),
    ("obligations", 'require(graph.obligations == OBLIGATIONS,', 'require(True,'),
    ("result", 'require(graph.result.answer_json.encode("utf-8") == answer,', 'require(True,'),
    ("source", 'graph.source.sha256 == CHECKER_SHA and graph.checker.source_sha256', 'True and graph.checker.source_sha256'),
    ("request", 'and digest(request) == graph.request.sha256,', 'and True,'),
    ("document", 'require(sha(text) == graph.document.sha256,', 'require(True,'),
    ("span", 'require(sha(selected) == span.sha256,', 'require(True,'),
    ("composition", 'left.codomain_type == right.domain_type and encoded(left.codomain) == encoded(right.domain)', 'True'),
    ("endpoint", 'arrow.domain_sha256 == digest(left) and arrow.codomain_sha256 == digest(right)', 'True'),
    ("mapping", 'require(encoded(arrow.source_map) ==', 'require(True or encoded(arrow.source_map) =='),
    ("arrow_obligations", 'require(arrow.obligations == left.obligations == right.obligations,', 'require(True,'),
    ("pin", 'require(sha(raw) == CHECKER_SHA,', 'require(True,'),
    ("duplicate", 'type(key) is str and key not in out', 'type(key) is str'),
    ("alias", 'not isinstance(event, yaml.events.AliasEvent) and getattr(event, "anchor", None) is None', 'True'),
]


def test_compiled_semantic_mutations():
    source = CODE.read_text(encoding="utf-8")
    records = []
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, name
        baseline_name = "typed_baseline_" + name
        baseline = ModuleType(baseline_name)
        sys.modules[baseline_name] = baseline
        baseline.__file__ = str(CODE)
        exec(compile(source, "<baseline>", "exec"), baseline.__dict__)
        mutation_guard(baseline, name)
        altered = source.replace(old, new, 1)
        code = compile(altered, f"<mutant_{name}>", "exec")
        module_name = "typed_mutant_" + name
        module = ModuleType(module_name)
        sys.modules[module_name] = module
        module.__file__ = str(CODE)
        exec(code, module.__dict__)
        with pytest.raises((AssertionError, ValueError, pytest.fail.Exception)) as caught:
            mutation_guard(module, name)
        records.append({"name": name, "old": old, "new": new, "compiled": True, "baseline_passed": True,
                        "killed": True, "source_sha256": M.sha(CODE.read_bytes()),
                        "mutant_sha256": M.sha(altered.encode()), "failure": type(caught.value).__name__, "reason": str(caught.value)})
    destination = os.environ.get("TYPED_ENGINE_MUTATION_REPORT")
    if destination:
        Path(destination).write_text(json.dumps({"count": len(records), "mutations": records}, indent=2), encoding="utf-8")


def test_script_entry(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(CODE), "--output-dir", str(tmp_path / "runs")])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(CODE), run_name="__main__")
    assert caught.value.code == 0 and Path(json.loads(capsys.readouterr().out)["output"]).parent == tmp_path / "runs"
