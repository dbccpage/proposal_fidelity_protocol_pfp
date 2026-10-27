"""Custody replay classes and the leakage lint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from adversary.tests.pilots.judge_packet_audit import canonical, custody, leakage


def test_lf_crlf_classification() -> None:
    data = b'{\n  "a": 1\n}\n'
    lf = hashlib.sha256(data).hexdigest()
    crlf = hashlib.sha256(data.replace(b"\n", b"\r\n")).hexdigest()
    assert custody.classify(lf, data) == "LF"
    assert custody.classify(crlf, data) == "CRLF"
    # the working tree may hold CRLF bytes; the class is about the digest, not the checkout
    assert custody.classify(lf, data.replace(b"\n", b"\r\n")) == "LF"
    assert custody.classify("0" * 64, data) == "NEITHER"
    assert custody.classify(lf, None) == "FILE_MISSING"
    no_newline = b"abc"
    both = hashlib.sha256(no_newline).hexdigest()
    assert custody.classify(both, no_newline) == "LF_AND_CRLF"


@pytest.mark.parametrize(
    "shape",
    ["list_manifest", "dict_of_digests", "dict_of_records"],
)
def test_manifest_formats_are_all_read(tmp_path: Path, shape: str) -> None:
    pkg = tmp_path / "pkg"
    (pkg / "judge_packet" / "cases").mkdir(parents=True)
    case = pkg / "judge_packet" / "cases" / "a.json"
    case.write_bytes(b'{"id": "a"}\n')
    digest = hashlib.sha256(case.read_bytes()).hexdigest()
    rel = "judge_packet/cases/a.json"
    body = {
        "list_manifest": {"manifest": [{"path": rel, "sha256": digest}]},
        "dict_of_digests": {"files": {rel: digest}},
        "dict_of_records": {"files": {"cases/a.json": {"sha256": digest, "size_bytes": 12}}},
    }[shape]
    (pkg / "judge_packet" / "manifest.json").write_text(json.dumps(body), encoding="utf-8")
    replay = custody.manifest_replay(pkg)
    assert replay["entries"] == 1 and replay["counts"]["LF"] == 1
    assert replay["judge_files_not_listed"] == []


def test_case_id_naming_its_own_answer_is_flagged_but_input_tokens_are_not() -> None:
    case = {"case_id": "w10_base_01_removable_gauge", "type": "REMOVABLE_GAUGE", "edges": []}
    answer_tokens = ["gauge", "removable", "solved"]
    leak = leakage.case_id_leak(case["case_id"], case, answer_tokens)
    # 'removable' and 'gauge' also occur in the input's type field, which is itself the leak
    assert leak["names_own_answer"] == []
    fields = leakage.flagged_fields(case, answer_tokens)
    assert fields == [
        {
            "field": "type",
            "value_shares_answer_tokens": ["gauge", "removable"],
            "named_answer_field": False,
        }
    ]
    bare = {"case_id": "w10_base_01_removable_gauge", "edges": []}
    assert leakage.case_id_leak(bare["case_id"], bare, answer_tokens)["names_own_answer"] == [
        "gauge",
        "removable",
    ]


def test_example_duplicates_ignore_identifier_and_description() -> None:
    cases = [
        ("cases/a.json", {"id": "judge_a", "description": "x", "n": 3}),
        ("cases/b.json", {"id": "b", "n": 4}),
    ]
    examples = [("ex/1.json", {"id": "ex1", "n": 3}, True)]
    assert leakage.example_duplicates(cases, examples) == [
        {"case": "cases/a.json", "examples": ["ex/1.json"], "example_ships_answer": True}
    ]


def test_runner_lint_finds_case_id_note_and_expected_interpolations(tmp_path: Path) -> None:
    runner = tmp_path / "run_x_matrix.py"
    runner.write_text(
        "import json\n"
        "CASES = [{'case_id': 'c1_m02_trefoil_refusal', 'note': 'Quaternion group Q8', 'expected_kind': 'UNSAT'}]\n"
        "def prompt(case):\n"
        "    return f\"Case ID: {case['case_id']}\\n{json.dumps(case)}\\nHint: {case['note']} {case.get('expected_kind')}\"\n",
        encoding="utf-8",
    )
    lint = leakage.runner_lint(runner, {"trefoil"})
    kinds = lint["prompt_interpolations"][0]["kinds"]
    assert kinds == ["case_id", "case_json", "expected_field", "note"]
    inline = lint["inline_cases"][0]
    assert inline["verdict_words"] == ["refusal"]
    assert inline["answer_vocabulary_words"] == ["trefoil"]
    assert inline["answer_bearing_fields"] == ["expected_kind", "note"]


def test_canonical_output_refuses_floats_and_is_stable(tmp_path: Path) -> None:
    with pytest.raises(canonical.FloatInRecordError):
        canonical.dumps({"rate": 0.5})
    assert (
        canonical.ratio(68, 68) == "1/1"
        and canonical.ratio(6, 10) == "3/5"
        and canonical.ratio(0, 0) == "0/0"
    )
    with pytest.raises(TypeError):
        canonical.ratio(True, 2)
    first = canonical.write_jsonl_gz(tmp_path / "a.jsonl.gz", [{"b": 1, "a": [1, 2]}])
    second = canonical.write_jsonl_gz(tmp_path / "b.jsonl.gz", [{"a": [1, 2], "b": 1}])
    assert first == second
    assert canonical.read_jsonl_gz(tmp_path / "a.jsonl.gz") == [{"a": [1, 2], "b": 1}]
