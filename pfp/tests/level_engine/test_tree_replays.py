"""Research-tree replays (the author's ruling of 2026-09-25): custody, the
provenance mark in every record's loss ledger, the registry's checks, and the
read-only loading of tree modules.

AuthorityEffect: None
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from omega_engine_operations.domain.level_engine_context import (
    current_context,
)
from omega_engine_operations.infrastructure.level_engine_ports import ports
from omega_engine_operations.use_cases.level_engine import bind
from omega_engine_operations.use_cases.level_engine.bind import LEVELS, TREE_REPLAYS, records
from omega_engine_operations.use_cases.level_engine.research_engine.canon import dumps, load_path
from omega_engine_operations.use_cases.level_engine.research_engine.errors import (
    EmbargoRefusal,
    Refusal,
)
from omega_engine_operations.use_cases.level_engine.research_engine.level import (
    load_spec,
    run_level,
)
from omega_engine_operations.use_cases.level_engine.research_engine.replay import (
    Row,
    result,
    tree_json,
    tree_module,
    tree_rel,
)
from omega_engine_operations.use_cases.level_engine.research_engine.sealed import VENDOR
from omega_engine_pfp.infrastructure.tower_research.level_engine.outward import bundles as B
from omega_engine_pfp.infrastructure.tower_research.level_engine.outward import reach as R
from omega_engine_pfp.infrastructure.tower_research.level_engine.outward.qlevels import (
    REGISTRY,
    registrations,
)

ROOT = current_context().runtime_root
TREE_RECORDS = sorted((level, str(meta["challenge_id"])) for level, meta in TREE_REPLAYS.items())


def test_a_tree_name_is_one_plain_segment_and_the_second_derivation_is_refused() -> None:
    for bad in ("", "a/b", "a\\b", ".hidden", "../code"):
        with pytest.raises(Refusal) as err:
            tree_rel(bad, "x.py")
        assert err.value.code == "RR-TREE"
    with pytest.raises(EmbargoRefusal) as emb:
        tree_module("second_iso", "anything")
    assert emb.value.code == "GUARD_EMBARGO"
    with pytest.raises(Refusal) as missing:
        tree_module("g014_observer_descent", "no_such_module")
    assert missing.value.code == "RR-TREE"
    assert isinstance(tree_json("native_structure", "input.json"), dict)


def test_loading_a_tree_module_writes_no_bytecode_into_the_clone() -> None:
    tree_module("g014_observer_descent", "observer_descent")
    assert not (VENDOR / "research" / "g014_observer_descent" / "__pycache__").exists()


def test_a_tree_replay_reads_only_its_trees_and_cites_no_sealed_lean() -> None:
    def decide(pk: dict[str, object]) -> tuple[str, ...]:
        return ()

    rows: list[Row] = [("pos", "positive", {"a": 1}, None)]
    for lean, sources in (((), ("code/derivation/model.py",)), (("Derivation.mark_progress",), ("research/t/x.py",)),
                          ((), ())):
        with pytest.raises(Refusal) as err:
            result("x", "M", rows, decide, ("c",), lean, sources, {}, trees=("t",))
        assert err.value.code == "RR-TREE"
    ok = result("x", "M", rows, decide, ("c",), (), ("research/t/x.py",), {}, trees=("t",))
    assert ok.extra["witness_custody"] == {"custody": "research_tree", "trees": ["t"]}


def test_a_record_that_does_not_book_its_custody_is_refused() -> None:
    level, cid = TREE_RECORDS[0]
    res = run_level(cid)
    inputs = B.fixture_inputs(cid)
    stub = R.stub(level, res, inputs, f"T{level:03d}")
    assert any(f["field_or_law"] == "source.witness_custody" for f in stub["loss_ledger"]["fields"])
    with pytest.raises(Refusal) as err:
        R.custody_checked(res, f"T{level:03d}", {"fields": []})
    assert err.value.code == "UNBOOKED_CUSTODY"
    harness = run_level(str(LEVELS[level]["challenge_id"]))
    with pytest.raises(Refusal) as err2:
        R.stub(level, harness, B.fixture_inputs(str(LEVELS[level]["challenge_id"])), f"T{level:03d}")
    assert err2.value.code == "UNBOOKED_CUSTODY"


@pytest.mark.parametrize(("level", "cid"), TREE_RECORDS)
def test_every_tree_record_books_its_custody_and_its_findings(level: int, cid: str) -> None:
    stub = load_path(current_context().historical_path("bindings") / "generated" / "reach" / f"T{level:03d}.stub.json")
    assert isinstance(stub, dict) and stub["carrier_part"] == "repo_content" and stub["framing"] == "SC"
    rows = {f["field_or_law"]: f for f in stub["loss_ledger"]["fields"]}
    trees = TREE_REPLAYS[level]["trees"]
    assert isinstance(trees, list)
    assert rows["source.witness_custody"]["classification"] == "WEAKENED"
    assert all(f"research/{t}" in rows["source.witness_custody"]["source_value"] for t in trees)
    assert any("research-tree evidence" in n and "not sealed" in n for n in stub["non_claims"])
    raw: Any = load_path(REGISTRY)
    entry = next(e for e in raw["levels"] if e["level"] == level)
    booked = [f["source_value"] for k, f in sorted(rows.items()) if k.startswith("source.finding.")]
    assert booked == list(entry.get("findings", []))
    assert entry["witness_custody"] == "research_tree"
    assert sorted(entry["tree_sources"]) == sorted(load_spec(cid).SOURCES)  # type: ignore[attr-defined]
    binding = load_path(current_context().historical_path("bindings") / f"T{level:03d}.json")
    assert isinstance(binding, dict) and binding["custody"] == "research_tree" and binding["trees"] == trees


def test_a_tree_replay_never_shares_a_key_with_a_replay_of_sealed_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(bind.TREE_REPLAYS, 29, {"challenge_id": "boundary_chain", "trees": ["x"]})
    with pytest.raises(ValueError):
        records()


def _refused(tmp_path: Path, level: int, edit: Any) -> str:
    raw: Any = load_path(REGISTRY)
    doc = copy.deepcopy(raw)
    edit(next(e for e in doc["levels"] if e["level"] == level))
    (tmp_path / "q.json").write_bytes(dumps(doc))
    with pytest.raises(Refusal) as err:
        registrations(LEVELS, TREE_REPLAYS, tmp_path / "q.json")
    return err.value.code


def test_the_registry_refuses_a_retired_blocker_and_mixed_custody(tmp_path: Path) -> None:
    level = TREE_RECORDS[0][0]
    assert _refused(tmp_path, level, lambda e: e["blocked_by"].append("witness_not_sealed")) == "RULED_ADMISSIBLE"
    assert _refused(tmp_path, level, lambda e: e.__setitem__("witness_custody", "hearsay")) == "UNKNOWN_CUSTODY"
    assert _refused(tmp_path, level, lambda e: e.__setitem__("tree_sources", [])) == "MIXED_CUSTODY"
    assert _refused(tmp_path, level, lambda e: e["sealed_sources"].append("code/derivation/model.py")) == \
        "MIXED_CUSTODY"
    assert _refused(tmp_path, level, lambda e: e.__setitem__("tree_sources", ["code/derivation/model.py"])) == \
        "MIXED_CUSTODY"
    assert _refused(tmp_path, 29, lambda e: e.__setitem__("witness_custody", "research_tree")) == "MIXED_CUSTODY"

    def sealed(e: dict[str, Any]) -> None:
        e["witness_custody"] = "sealed"
        e["tree_sources"] = []

    assert _refused(tmp_path, level, sealed) == "MIXED_CUSTODY"


def test_a_tree_path_cannot_climb_out_of_its_tree() -> None:
    with pytest.raises(Refusal) as e:
        tree_rel("natural_sections", "../second/SEED.md")
    assert e.value.code == "RR-TREE"


def test_a_module_that_fails_to_load_is_not_cached(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed load leaves nothing in ``sys.modules``, so the next call fails
    for the real reason instead of returning a half-built module."""
    import sys

    from omega_engine_operations.use_cases.level_engine.research_engine import replay

    tree = tmp_path / "research" / "broken_tree"
    tree.mkdir(parents=True)
    (tree / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tree / "entry.py").write_text("import helper\nraise RuntimeError('boom')\n", encoding="utf-8")
    monkeypatch.setattr(replay, "vendored", lambda rel: tmp_path / rel)
    for _ in range(2):
        with pytest.raises(RuntimeError, match="boom"):
            tree_module("broken_tree", "entry")
    assert "_tree_broken_tree_entry" not in sys.modules
    assert "helper" not in sys.modules



def test_the_packaged_checker_is_the_checker_of_record() -> None:
    """``bind.target`` holds the installed checker to the historical checker of
    record, byte for byte, before any binding names it (a tree replay's
    level included)."""
    out = bind.target(23, ports())
    assert out["status"] == "CHECKER_OF_RECORD"
    checker = out["checker"]
    assert isinstance(checker, dict) and checker["id"] == "stage_023"
