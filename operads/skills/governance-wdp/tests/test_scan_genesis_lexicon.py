"""Primitive Difference lexicon scanner — behavior preserved under rename."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "scan_genesis_lexicon.py"
SPEC = importlib.util.spec_from_file_location("scan_genesis_lexicon", SCRIPT)
assert SPEC and SPEC.loader
scan = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scan
SPEC.loader.exec_module(scan)


def test_high_ofn_and_primdiff_hits(tmp_path: Path) -> None:
    paper = tmp_path / "sample.md"
    paper.write_text(
        "A view from nowhere audit fails.\n"
        "Difference cannot float in nothing.\n"
        "Ordinary prose about categories.\n",
        encoding="utf-8",
        newline="\n",
    )
    hits = scan.scan_file(paper)
    severities = {h[1] for h in hits}
    tags = {h[2] for h in hits}
    assert "HIGH" in severities
    assert "OFN" in tags
    assert "PRIMDIFF" in tags


def test_cli_marker_renamed_and_exit_zero(tmp_path: Path) -> None:
    paper = tmp_path / "sample.md"
    paper.write_text("the world offers all cuts\n", encoding="utf-8", newline="\n")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(paper)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "PRIMDIFF_OBSERVER_AUDIT: CANDIDATES_ONLY" in proc.stdout
    assert "PRIMDIFF_OFN_LEXSCAN" not in proc.stdout
    assert "AuthorityEffect: None" in proc.stdout
    assert "HIGH" in proc.stdout


def test_clean_file_no_hits(tmp_path: Path) -> None:
    paper = tmp_path / "clean.md"
    paper.write_text(
        "On carrier K under family J the admitted cut presents non-sameness.\n",
        encoding="utf-8",
        newline="\n",
    )
    hits = scan.scan_file(paper)
    assert hits == []
