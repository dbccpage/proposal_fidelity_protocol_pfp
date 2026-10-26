"""The Lean layer as the Python side sees it: the committed axiom report,
the component registry, and the generated sources."""

from __future__ import annotations

from pathlib import Path

import pytest

import engine.components as C
from engine.level import run_level
from outward import bundles as B
from tools import lean_audit, lean_gen


def test_generated_sources_are_current() -> None:
    assert lean_gen.main(["--check"]) == 0
    assert len(lean_gen.certificates()) == 15
    assert [fid for fid, _ in lean_gen.tables()] == ["pos", "own_neg", "near_degenerate", "near_diagonal", "mut"]
    assert set(lean_gen.reported()) >= set(lean_gen.LIBRARY_THEOREMS)


def test_the_committed_report_is_within_policy_and_complete() -> None:
    report = C.lean_report()
    assert set(report) == set(lean_gen.reported())
    assert all(set(ax) <= C.POLICY for ax in report.values())
    assert lean_audit.parse(lean_audit.render(report)) == report
    assert "lean.exact.qn" in C.available()
    assert "lean.exact.induction" in C.available()
    assert set(report["ExactRat.QN.nonneg_from"]) == {"propext", "Quot.sound"}


def test_a_missing_or_classical_report_withdraws_the_component(tmp_path: Path) -> None:
    assert C.lean_report(tmp_path) == {}
    assert "lean.exact.qn" not in C.available(tmp_path)
    (tmp_path / "lean").mkdir()
    lines = [f"{n}: propext" for n in C.LEAN_COMPONENTS["lean.exact.qn"]]
    lines[0] = lines[0] + ", Classical.choice"
    (tmp_path / "lean" / "axioms.txt").write_bytes(("\n".join(lines) + "\n").encode("ascii"))
    report = C.lean_report(tmp_path)
    assert not C.within_policy(report, C.LEAN_COMPONENTS["lean.exact.qn"][0])
    assert "lean.exact.qn" not in C.available(tmp_path)
    (tmp_path / "lean" / "axioms.txt").write_bytes(b"x: (none)\n")
    assert C.lean_report(tmp_path) == {"x": ()}


def test_a_missing_certificate_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    import engine.level as L

    report = dict(C.lean_report())
    del report["DistanceForm.own_neg_form_positive"]
    monkeypatch.setattr(L, "lean_report", lambda: report)
    r = run_level("distance_form")
    assert r.missing_components == ("lean:DistanceForm.own_neg_form_positive",)
    assert B.status(r) == "UNRESOLVED"
    assert r.extra["clause_evidence"]["form_positive"] == "COMPUTED"  # type: ignore[index]
    assert r.extra["clause_evidence"]["diagonal_zero"] == "LEAN"  # type: ignore[index]
