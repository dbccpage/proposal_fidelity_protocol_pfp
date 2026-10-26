"""Mutation-tool edges that its own campaign showed were unpinned.

AuthorityEffect: None.
Contract: urn:pfp-governance:tests:mutation-pins:v1
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from governance.tools import mutation

SAMPLE = "def check(x):\n    return x == 1\n"


def test_documented_defaults() -> None:
    assert (mutation.DEFAULT_TIMEOUT, mutation.PYTEST_FAILED, mutation.PYTEST_INTERRUPTED) == (300, 1, 2)
    assert mutation.build_parser().parse_args(["n"]).max == 10_000


def test_boolean_answers_are_booleans(tmp_path: Path) -> None:
    assert mutation.compiles("x = (\n") is False
    assert mutation.recover(tmp_path, "none") is False


def test_integer_mutant_adds_one() -> None:
    descriptions = [site.description for site in mutation.sites(SAMPLE)]
    index = descriptions.index("1 -> 2")
    assert "x == 2" in mutation.mutant(SAMPLE, index)


def test_mask_handles_a_comment_at_column_zero() -> None:
    assert mutation.mask("// a == b") == " " * 9
    assert mutation.lexical_sites("// a == b\n") == []


def test_campaign_defaults_and_journal_folder(tmp_path: Path) -> None:
    campaign = mutation.Campaign(tmp_path, "fresh", [], timeout=5)
    assert (campaign.killed, campaign.invalid) == (frozenset({1}), frozenset())
    assert (tmp_path / "governance" / "evidence").is_dir()


@pytest.fixture
def two_targets(repo: Path) -> Path:
    for name, body in (("one.py", "def one():\n    return 1\n"), ("two.py", "def two():\n    return 2\n")):
        (repo / "pfp_lab" / name).write_text(body, encoding="utf-8")
    (repo / "pfp_lab" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pfp_lab" / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "pfp_lab" / "tests" / "test_both.py").write_text(
        "from pfp_lab.one import one\nfrom pfp_lab.two import two\n\n\ndef test_both():\n"
        "    assert (one(), two()) == (1, 2)\n",
        encoding="utf-8",
    )
    return repo


def test_budget_spans_targets_and_report_format(two_targets: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    argv = [
        "span",
        "--target",
        "pfp_lab/one.py",
        "--target",
        "pfp_lab/two.py",
        "--max",
        "1",
        "--",
        "pfp_lab/tests/test_both.py",
    ]
    monkeypatch.setattr(sys, "argv", ["mutation", *argv])
    assert mutation.main(None, io.StringIO(), root=two_targets) == 0
    path = two_targets / "governance" / "evidence" / "span.mutation.json"
    text = path.read_text(encoding="utf-8")
    assert text.startswith('{\n  "schema_version": "pfp.mutation-report.v1"')
    report = json.loads(text)
    assert report["python"] == sys.version.split()[0]
    outcomes = [(item["path"], item["outcome"]) for item in report["mutants"]]
    assert outcomes == [
        ("pfp_lab/one.py", "killed"),
        ("pfp_lab/one.py", "unrun"),
        ("pfp_lab/two.py", "unrun"),
        ("pfp_lab/two.py", "unrun"),
    ]
    assert all(
        0 <= item["seconds"] < 600 and round(item["seconds"], 2) == item["seconds"] for item in report["mutants"]
    )
