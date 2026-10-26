"""Edges of the evidence and metrics tools that the mutation campaigns showed were unpinned.

AuthorityEffect: None.
Contract: urn:pfp-governance:tests:tool-pins:v1

Expected values come from SCORING.md's metric ceilings table and from the
documented record format, not from the tools under test.
"""

from __future__ import annotations

import ast
import io
import json
import sys
from pathlib import Path

import pytest

from governance.tools import evidence, metrics
from governance.tools.checker import Repository


@pytest.mark.parametrize(
    ("metric", "value", "grade"),
    [
        ("cognitive", 20, "B"),
        ("cognitive", 21, "C"),
        ("cognitive", 25, "C"),
        ("cognitive", 26, "D"),
        ("cognitive", 40, "D"),
        ("nesting", 5, "C"),
        ("nesting", 6, "D"),
        ("ccn", 0, "A+"),
    ],
)
def test_more_band_edges(metric: str, value: int, grade: str) -> None:
    assert metrics.band(metric, value) == grade


def test_nested_if_counts_but_elif_does_not() -> None:
    nested = ast.parse("def f(a, b):\n    if a:\n        if b:\n            pass\n").body[0]
    assert metrics.nesting_depth(nested) == 2
    chain = ast.parse("def f(a, b, c):\n    if a:\n        pass\n    elif b:\n        if c:\n            pass\n").body[
        0
    ]
    assert metrics.nesting_depth(chain) == 2


def test_module_without_functions(tmp_path: Path) -> None:
    source = tmp_path / "plain.py"
    source.write_text("X = 1\n", encoding="utf-8")
    measured = metrics.file_metrics(source)
    assert (measured["ccn_max"], measured["cognitive_max"], measured["nesting_max"]) == (0, 0, 0)


def test_csharp_nesting_resets_between_members(tmp_path: Path) -> None:
    source = tmp_path / "Two.cs"
    source.write_text(
        "namespace N;\nclass T\n{\n    void A() { if (x) { y(); } }\n    void B() { if (x) { if (y) { z(); } } }\n}\n",
        encoding="utf-8",
    )
    assert metrics.csharp_nesting(source) == 2


def test_metrics_report_format_and_single_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "plain.py"
    source.write_text("def f():\n    return 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    out = io.StringIO()
    assert metrics.main(["r.json", "plain.py"], out) == 0
    text = (tmp_path / "r.json").read_text(encoding="utf-8")
    assert text.startswith('{\n  "plain.py": {\n    "ccn_max"')
    monkeypatch.setattr(sys, "argv", ["metrics", "s.json", "plain.py"])
    assert metrics.main(None, io.StringIO()) == 0
    assert json.loads((tmp_path / "s.json").read_text(encoding="utf-8"))["plain.py"]["functions"] == 1


def test_documented_evidence_constants() -> None:
    assert (evidence.DEFAULT_TIMEOUT, evidence.NOT_STARTED) == (3600, 127)


def test_run_record_format_and_partial_output_on_timeout(repo: Path) -> None:
    command = [sys.executable, "-c", "import sys, time; print('partial'); sys.stdout.flush(); time.sleep(5)"]
    record = evidence.capture(Repository(repo), "slow", command, [], timeout=2)
    assert record.exit_status == -1
    assert b"partial" in (repo / "governance" / "evidence" / "slow.log").read_bytes()
    text = (repo / "governance" / "evidence" / "slow.run.json").read_text(encoding="utf-8")
    assert text.startswith('{\n  "schema_version": "pfp.evidence-run.v1",\n  "AuthorityEffect": "None"')


def test_evidence_main_reads_sys_argv(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(evidence, "ROOT", repo)
    monkeypatch.setattr(sys, "argv", ["evidence", "argv-run", "--", sys.executable, "-c", "pass"])
    out = io.StringIO()
    assert evidence.main(None, out) == 0
    assert out.getvalue().startswith("argv-run: exit 0")
