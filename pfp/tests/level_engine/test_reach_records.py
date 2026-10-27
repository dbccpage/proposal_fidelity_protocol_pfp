"""Level records in the receiving side's shape: the committed stubs, the
replay's waiting states, and the whole pipeline run through the receiving
side's own ``check_record`` against a test-only draft checker (never of
record, so the terminal is capped at SELF_CONSISTENT_ONLY).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from operations.domain.level_engine_context import (
    current_context,
)
from operations.infrastructure.level_engine_ports import ports
from operations.use_cases.level_engine import reach_replay as RR
from operations.use_cases.level_engine.bind import LEVELS, TREE_REPLAYS, records
from operations.use_cases.level_engine.research_engine.canon import dumps, load_path
from operations.use_cases.level_engine.research_engine.level import run_level
from pfp.infrastructure.tower_research.level_engine.outward import bundles as B
from pfp.infrastructure.tower_research.level_engine.outward import reach as R

ROOT = current_context().runtime_root
DRAFT = Path(str(__import__("importlib.resources", fromlist=["files"]).files("pfp.tests.level_engine"))) / "reach_draft"
CHECKER_REL = "pfp/tests/level_engine/reach_draft/checker_L002.py"
CHECKER_COMMIT = "a" * 40
HARNESS_COMMIT = "c" * 40
WORKING_COMMIT = "d" * 40


def test_every_level_has_a_stub_with_the_standing_entries_booked() -> None:
    for tag, level, spec in records():
        # A level added after the relocation has its stub only among the
        # active v2 records; every earlier one is read from the v1 archive.
        old = current_context().historical_path("bindings") / "generated" / "reach" / f"{tag}.stub.json"
        st = load_path(old if old.is_file() else current_context().current_path(f"bindings/generated/reach/{tag}.stub.json"))
        assert isinstance(st, dict)
        assert st["framing"] == ("AP" if spec["answer_type"] == "A" or R.apparatus_level(level) else "SC")
        booked = {f["field_or_law"] for f in st["loss_ledger"]["fields"]}
        assert set(R.STANDING) <= booked
        assert st["receipt_schema"] == "reach-receipt/1" and st["provenance"]["source_blindness"] == "NOT_BLIND"
    five = load_path(current_context().historical_path("bindings") / "generated" / "reach" / "L005.stub.json")
    assert isinstance(five, dict) and len(five["lean_theorems"]) == 3


def test_the_restated_axiom_report_keeps_every_line() -> None:
    lines = R.axioms_report_bytes().decode("ascii").splitlines()
    assert len(lines) == len((current_context().lean_path("axioms.txt")).read_text(encoding="utf-8").splitlines())
    assert all(line.startswith("'") and ("depends on axioms: [" in line or "does not depend on any axioms" in line)
               for line in lines)
    assert not any("(none)" in line for line in lines)
    assert "'CycleWords.pos_one_class' does not depend on any axioms" in lines


def test_no_checker_of_record_means_every_level_waits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(R, "checkers_of_record", lambda: {})
    for level in sorted(LEVELS):
        assert RR.replay_level(level, None, store=False, ports=ports())[0] == "AWAITING_CHECKER"


def test_a_tree_off_origin_is_not_replayed() -> None:
    for level in sorted(LEVELS):
        found = R.checker_for(level)
        assert found is not None and found[0] == f"stage_{level:03d}"
        assert RR.replay_level(level, None, store=False, ports=ports())[0] == "NOT_REPLAYED"


def test_a_checker_without_an_adapter_waits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(R, "checker_for", lambda level, checkers=None: ("draft_edge_endpoints", {"level": level}))
    assert RR.replay_level(2, None, store=False, ports=ports())[0] == "AWAITING_ADAPTER"
    monkeypatch.setattr(R, "adapter_path", lambda level, tag=None: DRAFT / "adapter_L002.py")
    assert RR.replay_level(2, None, store=False, ports=ports())[0] == "NOT_REPLAYED"


def test_an_adapter_for_another_checker_waits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(R, "checker_for", lambda level, checkers=None: ("stage_999", {"level": level}))
    status, detail = RR.replay_level(0, None, store=False, ports=ports())
    assert status == "AWAITING_ADAPTER" and "stage_000" in detail


RECORDS = [(tag, level) for tag, level, _ in records()]


def _cid(tag: str, level: int) -> str:
    return str((TREE_REPLAYS if tag.startswith("T") else LEVELS)[level]["challenge_id"])


@pytest.mark.parametrize(("tag", "level"), RECORDS)
def test_committed_adapters_agree_with_the_engine(tag: str, level: int) -> None:
    """Every adapted fixture keeps the engine's own verdict (the positive is
    accepted natively, every other fixture refused), every mutation is a
    single edit of the positive, and the committed positive is the adapter's."""
    adapter = R.load_adapter(R.adapter_path(level, tag))
    assert adapter is not None
    cid = _cid(tag, level)
    result = run_level(cid)
    native = {v.fid: v.satisfied for v in result.verdicts}
    fx = adapter.fixtures(result, B.fixture_inputs(cid))
    pos = next(f for f in fx if f["kind"] == "positive")
    assert native[pos["id"]]
    edit = R.reach("targets").edit_count
    for f in fx:
        if f["kind"] == "decisive_mutation":
            assert edit(f["payload"], pos["payload"]) == 1
            assert f["clause"] in {c for c, _ in adapter.CLAUSES}
        if f["kind"] != "positive" and f["id"] in native:
            assert not native[f["id"]]
    assert load_path(current_context().require_repository() / R.positive_rel(level, tag)) == pos["payload"]


def test_checker_lookup_by_level() -> None:
    reg = {"b": {"level": 2}, "a": {"level": 2}, "c": {"level": 3}}
    found = R.checker_for(2, reg)
    assert found is not None and found[0] == "a"
    assert R.checker_for(9, reg) is None
    assert R.load_adapter(current_context().historical_path("bindings") / "adapters" / "L999.py") is None


# ---------------------------------------------------------------- the pipeline, against a draft checker


def _historical_sources(challenge_id: str) -> list[dict[str, str]]:
    """Legacy schema fixtures retain their engine/payload closure, including K13.

    The active v2 manifest also includes its receipt serializer; those full bytes
    are never presented as new reach-receipt/1 evidence.
    """
    return [entry for entry in B.harness_sources(challenge_id)
            if entry["path"].startswith(("engine/", "payload/"))]


def _pipeline(mutate: Callable[[dict[str, Any]], None] | None = None,
              checkers: dict[str, Any] | None = None) -> Any:
    level, cid = 2, "edge_endpoints"
    adapter = R.load_adapter(DRAFT / "adapter_L002.py")
    assert adapter is not None
    result = run_level(cid)
    inputs = B.fixture_inputs(cid)
    st = R.stub(level, result, inputs)
    positive = next(f["payload"] for f in adapter.fixtures(result, inputs) if f["kind"] == "positive")
    canonical = R.reach("canonical")
    files: dict[tuple[str, str, str], bytes] = {}
    for e in _historical_sources(cid):
        files[(R.CARRIER, HARNESS_COMMIT, f"{R.ENGINE_REL}/{e['path']}")] = (ROOT / e["path"]).read_bytes()
    files[(R.CARRIER, HARNESS_COMMIT, f"{R.ENGINE_REL}/adapters/L002.py")] = (
        DRAFT / "adapter_L002.py").read_bytes()
    files[(R.CARRIER, HARNESS_COMMIT, R.positive_rel(level))] = canonical.canonical_bytes(positive)
    checker_bytes = (DRAFT / "checker_L002.py").read_bytes()
    files[("the_symbol_game", CHECKER_COMMIT, CHECKER_REL)] = checker_bytes
    sources = [{"path": p, "sha256": canonical.digest(b)} for (repo, _, p), b in sorted(files.items())
               if repo == R.CARRIER]
    entry = {"commit": CHECKER_COMMIT, "level": 2, "path": CHECKER_REL, "sha256": canonical.digest(checker_bytes)}
    record = R.complete(st, result, inputs, adapter, "draft_edge_endpoints", entry, checker_bytes, HARNESS_COMMIT,
                        sources, None)
    if mutate is not None:
        mutate(record)
    pins = R.reach("pins")
    return R.preflight(record, pins.MapResolver(files), checkers={} if checkers is None else checkers)


def test_a_completed_record_passes_every_check_up_to_the_cap() -> None:
    out = _pipeline()
    assert out.codes == (), out.receipt["computed"]["refusals"]
    assert out.terminal == "SELF_CONSISTENT_ONLY"
    assert out.grades["P"] == "supplied" and out.grades["B"] == "named" and out.grades["R"] == "-"
    fixtures = out.receipt["computed"]["fixtures"]
    assert [f["observed"] for f in fixtures if f["kind"] == "positive"] == ["PASS"]
    assert all(f["observed"] == "REFUSED" for f in fixtures if f["kind"] != "positive")


def test_the_same_record_would_reach_r1_under_a_checker_of_record() -> None:
    """A test only: were the draft registered and gated, the record would
    replay at R1.  It is not registered anywhere."""
    canonical = R.reach("canonical")
    sha = canonical.digest((DRAFT / "checker_L002.py").read_bytes())
    reg = {"draft_edge_endpoints": {"commit": CHECKER_COMMIT, "gated_step": "reach-tests", "id": "draft_edge_endpoints",
                                    "level": 2, "path": CHECKER_REL, "sha256": sha}}
    out = _pipeline(checkers=reg)
    assert out.codes == () and out.terminal == "EVIDENCE_ONLY" and out.grades["R"] == "R1"


def test_a_positive_that_is_not_the_committed_witness_is_refused() -> None:
    def edit(record: dict[str, Any]) -> None:
        pos = next(f for f in record["fixtures"] if f["kind"] == "positive")
        pos["payload"] = copy.deepcopy(pos["payload"])
        pos["payload"]["protected"] = [[0, 1]]

    assert "RR-PIN" in _pipeline(edit).codes


def test_a_producer_verdict_is_refused() -> None:
    assert _pipeline(lambda r: r.__setitem__("verdict", "PASS")).codes == ("RR-PRODUCER-VERDICT",)


def test_the_lean_block_cites_the_positive_certificates() -> None:
    names = ["DistanceForm.pos_form_positive"]

    def read(rel: str) -> bytes | None:
        path = current_context().require_repository() / rel
        return path.read_bytes() if path.exists() else None

    block = R.lean_block(read, names)
    assert block is not None and block["theorems"][0]["name"] == names[0]
    assert R.lean_block(read, []) is None
    assert R.lean_block(lambda rel: None, names) is None


def test_a_coefficient_change_is_booked() -> None:
    result = run_level("first_separation")
    ledger = R.loss_ledger_v2(result, ("token",), {"source": "a", "target": "b"})
    rows = {f["field_or_law"]: f for f in ledger["fields"]}
    assert rows["source.coefficient_domain"]["classification"] == "WEAKENED"
    assert rows["sort:token"]["classification"] == "DROPPED"
    assert rows["source.cost_measure"]["classification"] == "WEAKENED"
    dumps(ledger)


# ---------------------------------------------------------------- every bound level, on the working tree


def _working_tree_receipt(level: int, tag: str | None = None) -> Any:
    """The level's record, completed against its checker of record with the
    working tree standing in for the harness commit, and run through the
    receiving side's ``check_record`` in memory."""
    tag = tag or f"L{level:03d}"
    cid = _cid(tag, level)
    found = R.checker_for(level)
    assert found is not None
    checker_id, entry = found
    checker_bytes = subprocess.run(["git", "-C", str(R.REPO), "show", f"{entry['commit']}:{entry['path']}"],
                                   capture_output=True, check=True).stdout
    adapter = R.load_adapter(R.adapter_path(level, tag))
    assert adapter is not None
    result = run_level(cid)
    inputs = B.fixture_inputs(cid)
    st = R.stub(level, result, inputs, tag)
    canonical = R.reach("canonical")

    def read(rel: str) -> bytes | None:
        path = current_context().require_repository() / rel
        return path.read_bytes() if path.is_file() else None

    lean = R.lean_block(read, list(st["lean_theorems"]))
    historical_paths = [f"{R.ENGINE_REL}/{e['path']}" for e in _historical_sources(cid)]
    historical_paths += [R.adapter_path(level, tag).relative_to(current_context().require_repository()).as_posix(), R.positive_rel(level, tag)]
    rels = set(historical_paths)
    if lean is not None:
        rels |= {lean["report"]["path"]} | {s["path"] for s in lean["sources"]}
    files: dict[tuple[str, str, str], bytes] = {}
    for rel in sorted(rels):
        data = read(rel)
        assert data is not None, rel
        files[(R.CARRIER, WORKING_COMMIT, rel)] = data
    files[("the_symbol_game", str(entry["commit"]), str(entry["path"]))] = checker_bytes
    sources = [{"path": rel, "sha256": canonical.digest(files[(R.CARRIER, WORKING_COMMIT, rel)])}
               for rel in historical_paths]
    record = R.complete(st, result, inputs, adapter, checker_id, entry, checker_bytes, WORKING_COMMIT, sources, lean,
                        tag)
    return R.preflight(record, R.reach("pins").MapResolver(files))


@pytest.mark.parametrize(("tag", "level"), RECORDS)
def test_every_bound_level_refuses_new_historical_receipt_generation(tag: str, level: int) -> None:
    output = current_context().current_path("bindings/generated/reach")
    before = {path.name: path.read_bytes() for path in output.glob("*") if path.is_file()}
    status, detail = RR.replay_level(level, WORKING_COMMIT, store=True, tag=tag, ports=ports())
    assert status == "NOT_REPLAYED"
    assert detail == "REACH_V2_GENERATION_UNAVAILABLE: historical reach-receipt/1 is verification-only"
    assert {path.name: path.read_bytes() for path in output.glob("*") if path.is_file()} == before


def test_a_level_naming_a_structure_map_carries_its_square() -> None:
    out = _working_tree_receipt(8)
    squares = out.receipt["transport"]["c3_compatibility"]["squares"]
    assert [s["structure_map"] for s in squares] == ["adjunction_unit"]
    assert squares[0]["lhs_sha256"] == squares[0]["rhs_sha256"]


def test_a_theorem_with_no_single_certificate_module_is_named() -> None:
    with pytest.raises(KeyError):
        R.lean_source_rel("NoSuchModule.pos_vanishes")
    assert R.lean_source_rel("ScopeFence.pos_vanishes").endswith("lean4/research_programs/level_engine/ScopeFence.lean")


def test_a_record_at_a_d4_apparatus_level_is_framed_apparatus() -> None:
    """Ruling D4: 017's checker decides only digests, tag dispatch and decoding,
    so the replayed record counts in A, never in C."""
    result = run_level("tagged_digest")
    fresh = R.stub(17, result, B.fixture_inputs("tagged_digest"))
    assert fresh["framing"] == "AP", "D4_FRAMING: 017 is framed " + str(fresh["framing"])
    assert R.framing(29, run_level("boundary_chain")) == "SC"
    assert R.framing(17, result, {"stage_017": {"level": 17}}) == "SC"


def test_the_q_levels_are_registered_with_checked_citations(tmp_path: Path) -> None:
    from operations.use_cases.level_engine.research_engine.errors import Refusal
    from pfp.infrastructure.tower_research.level_engine.outward.qlevels import (
        REGISTRY,
        registrations,
    )

    doc = registrations(LEVELS, TREE_REPLAYS)
    rows: Any = {r["level"]: r for r in doc["levels"]}  # type: ignore[attr-defined]
    assert sorted(rows) == [6, 9, 11, 12, 13, 14, 15, 16, 17, 20, 22, 23, 27, 29, 32, 41, 43, 44,
                            55, 58, 59, 60, 61, 62, 65, 66, 71, 72]
    assert rows[27]["findings"] and "g013" in rows[27]["findings"][0]
    # Round P7A: research-tree witnesses are admissible (the author's ruling of 2026-09-25).
    trees = {23, 58, 59, 60, 61, 62, 65, 66, 72}
    assert {k for k, r in rows.items() if r["status"] == "BOUND"} == {6, 9, 11, 13, 14, 15, 16, 17, 29, 32, 43} | trees
    assert {k for k, r in rows.items() if r["status"] == "BLOCKED"} == {12, 20, 22, 27, 41, 44, 55, 71}
    assert {k for k, r in rows.items() if r["witness_custody"] == "research_tree"} == trees | {27, 41, 44, 55, 71}
    assert {k: r["blocked_by"] for k, r in rows.items() if r["witness_custody"] == "research_tree"
            and r["status"] == "BLOCKED"} == {k: ["tree_witness_off_class"] for k in (27, 41, 44, 55, 71)}
    assert all(r["challenge_id"] == TREE_REPLAYS[k]["challenge_id"] for k, r in rows.items() if k in trees)
    assert rows[22]["blocked_by"] == ["no_sealed_replay"]
    assert all(r["tree_sources"] for r in rows.values() if r["witness_custody"] == "research_tree")
    # A harness record at a blocked level leaves the registration's blocker standing.
    assert {k: r["harness_record"] for k, r in rows.items() if r["harness_record"]} == {
        22: "reindexed_fibres", 23: "glued_patches", 27: "associator_tables", 41: "use_once_terms",
        44: "witnessed_triples", 55: "far_blind", 58: "overlap_choices", 59: "two_party_bound",
        60: "commuting_checks", 61: "walk_transport", 62: "face_products", 65: "step_squares",
        66: "signed_totals", 71: "rated_limits", 72: "rim_cochains"}
    assert all(r["checker"] == f"stage_{k:03d}" for k, r in rows.items())
    raw: Any = load_path(REGISTRY)
    edits: list[tuple[Callable[[Any], object], str]] = [
        (lambda e: e["named_not_reported"].append("TraceAlgebra.rw_confluent"), "STALE_REGISTRATION"),
        (lambda e: e["blocked_by"].append("weather"), "UNKNOWN_BLOCKER"),
        (lambda e: e["sealed_theorems"].append("TraceAlgebra.no_such_theorem"), "RR-STATEMENT"),
        (lambda e: e.__setitem__("missing", "a gap"), "STALE_REGISTRATION"),
    ]
    for edit, code in edits:
        doc2 = copy.deepcopy(raw)
        edit(next(e for e in doc2["levels"] if e["level"] == 11))
        (tmp_path / "q.json").write_bytes(dumps(doc2))
        with pytest.raises(Refusal) as err:
            registrations(LEVELS, TREE_REPLAYS, tmp_path / "q.json")
        assert err.value.code == code
