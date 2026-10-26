"""The reading ladder and its lift certifier, on record_reading's two steps.

Every condition is also refused on a mutated proposal with its own code
(the unit-level twin of injections I18 to I34).

AuthorityEffect: None
"""

from __future__ import annotations

import copy
import shutil
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

import omega_engine_operations.use_cases.level_engine.research_engine.ladder as L
import omega_engine_operations.use_cases.level_engine.research_engine.ladder_cert as C
from omega_engine_operations.domain.level_engine_context import (
    current_context,
)
from omega_engine_operations.use_cases.level_engine.research_engine.canon import (
    dumps,
    load_path,
    sha256_tag,
)
from omega_engine_operations.use_cases.level_engine.research_engine.errors import (
    NonDescent,
    Refusal,
)
from omega_engine_pfp.infrastructure.tower_research.level_engine.outward.lift import ladder_document

ROOT = current_context().runtime_root
Props = dict[str, object]


def props() -> Props:
    return copy.deepcopy(C.load_proposals())


def step(p: Props, k: int) -> dict[str, object]:
    steps = p["steps"]
    assert isinstance(steps, list)
    out = steps[k]
    assert isinstance(out, dict)
    return out


def expected() -> dict[str, object]:
    doc = load_path(ROOT / "lifts" / "record_reading" / "expect.json")
    assert isinstance(doc, dict)
    return doc


def drift_of(p: Props, root: Path = ROOT) -> tuple[str, ...]:
    return C.drift(C.certify_ladder(p, root), expected())


def codes(rows: tuple[str, ...]) -> set[str]:
    return {r.rsplit("(", 1)[-1].rstrip(")") for r in rows}


# ---------------------------------------------------------------- the mirror


def test_mirror_reproduces_the_carriers_census() -> None:
    pinned = C.load_pinned(C.load_proposals())
    assert C.census_agrees(pinned.evidence)


def test_key_padding_follows_the_carrier() -> None:
    assert L.key_at([0], 0, 3) == (0, 0, 0)
    assert L.key_at([0, 1], 1, 3) == (0, 0, 1)
    assert L.key_at([0, 1, 2, 0, 1], 4, 3) == (2, 0, 1)
    with pytest.raises(Refusal):
        L.key_at([0], 0, 0)


def test_setting_refusals() -> None:
    with pytest.raises(Refusal):
        L.Setting(0, ((0,),))
    with pytest.raises(Refusal):
        L.Setting(2, ((0, 2),))
    assert L.Setting(1, ((0,),)).to_json() == {"n": 1, "ops": [[0]]}


def test_explore_covers_the_universe_and_minima_are_tied() -> None:
    s = C.load_pinned(C.load_proposals()).setting
    for w in (1, 2):
        leaves = L.explore(w, s, 0, 3)
        assert sum(lf.weight for lf in leaves) == L.universe_size(w, s)
    assert len(L.minima(2, s, (0, 1, 0, 0))) == 2
    assert len(L.minima(3, s, (0, 1, 2, 0, 1, 0))) == 16
    assert L.minima(1, s, (0, 1, 0, 0)) == ()


def test_runner_strictness_and_maps() -> None:
    s = L.Setting(2, ((1, 0), (0, 1)))
    with pytest.raises(Refusal):
        L.run({}, 1, s, 0, 2, strict=True)
    assert L.run({}, 1, s, 0, 2) == (0,)
    with pytest.raises(Refusal):
        L.lift_table({(0,): 0}, 2, 1, s)
    t: dict[L.Key, int | None] = {(0,): 0, (1,): None}
    assert L.carrier_forget(L.lift_table(t, 1, 2, s), s) == t
    assert L.harness_restrict(L.lift_table(t, 1, 2, s), 1, s) == t
    with pytest.raises(NonDescent):
        L.harness_restrict({(0, 0): 0, (1, 0): 1}, 1, s)
    with pytest.raises(Refusal):
        L.full_tables(3, L.Setting(3, ((0, 0, 0),)))
    assert len(L.full_tables(1, s)) == 9


def test_pointer_and_shape_refusals() -> None:
    with pytest.raises(Refusal):
        C.pointer({"a": [1]}, ["a", 3])
    with pytest.raises(Refusal):
        C._ints([1, True])
    with pytest.raises(Refusal):
        C._list({"a": 1})
    assert C.pointer({"a": [1, {"b": 2}]}, ["a", 1, "b"]) == 2


# ---------------------------------------------------------------- the verdicts


def test_verdicts_match_the_frozen_expectations() -> None:
    result = C.certify_ladder(C.load_proposals())
    assert C.drift(result, expected()) == ()
    assert result.depth == 0 and result.chain.passed
    s0, s1 = result.steps
    assert s0.failed() == ("RR-NON-DESCENT",)
    assert s1.failed() == ("RR-ROLLBACK", "RR-NON-DESCENT")
    assert all(r.licensed for r in result.diagnostics)


def test_facts_are_the_predicted_ones() -> None:
    s0, s1 = C.certify_ladder(C.load_proposals()).steps
    search = s0.facts["same_level_search"]
    assert isinstance(search, dict)
    assert (search["covered"], search["realizers"], search["closed"]) == (64, 0, True)
    assert s0.facts["dual_witnesses"] == [[0, 2]] and s1.facts["dual_witnesses"] == [[1, 4]]
    mx0, mx1 = s0.facts["minimal_extension"], s1.facts["minimal_extension"]
    assert isinstance(mx0, dict) and isinstance(mx1, dict)
    assert (mx0["cost"], mx0["tied_minima"], mx1["cost"], mx1["tied_minima"]) == (3, 2, 5, 16)
    d0 = s0.facts["down_rule"]
    assert isinstance(d0, dict) and d0["defaulted"] == 3 and d0["non_descent_refusals"] == 0


def test_the_document_records_and_does_not_count() -> None:
    p = C.load_proposals()
    doc = ladder_document(C.certify_ladder(p), p, "0" * 40)
    assert doc["computed_depth"] == 0
    certs = doc["certificates"]
    assert isinstance(certs, list) and [c["licensed"] for c in certs] == [False, False]
    assert certs[0]["new_pair"] == [[0, 0], [1, 0]]
    dumps(doc)


def test_a_partial_carrier_map_would_give_depth_two(monkeypatch: pytest.MonkeyPatch) -> None:
    """A test only: were the carrier to define a partial retraction on both
    steps, every condition would hold and the depth would be two."""
    def partial(ws: int, wt: int) -> tuple[int, int, Callable[[Mapping[L.Key, int | None], L.Setting],
                                                             dict[L.Key, int | None]]]:
        return (ws, wt, lambda t, s: L.harness_restrict(t, ws, s))

    monkeypatch.setitem(C.CARRIER_DOWN, "forget", partial(1, 2))
    monkeypatch.setitem(C.CARRIER_DOWN, "partial2", partial(2, 3))
    p = props()
    step(p, 1)["down_map"] = "partial2"
    result = C.certify_ladder(p)
    assert [r.licensed for r in result.steps] == [True, True] and result.depth == 2


def test_a_chain_break_stops_the_depth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(C.CARRIER_DOWN, "forget", (1, 2, lambda t, s: L.harness_restrict(t, 1, s)))
    p = props()
    step(p, 1)["budget_before"] = 2
    result = C.certify_ladder(p)
    assert not result.chain.passed and result.depth == 0


# ---------------------------------------------------------------- one mutation per condition


def _mut(fn: Callable[[Props], None]) -> set[str]:
    p = props()
    fn(p)
    return codes(drift_of(p))


def test_survivor() -> None:
    assert _mut(lambda p: step(p, 0).__setitem__("dual_witness", [0, 1])) == {"NO_CERTIFIED_SURVIVOR"}


def test_claims_fixed() -> None:
    assert _mut(lambda p: step(p, 1).__setitem__("demand", [0, 1, 2, 0, 1, 2])) == {"CLAIM_FROZEN"}

    def setting(p: Props) -> None:
        st = p["setting"]
        assert isinstance(st, dict)
        st["ops"] = [[1, 2, 0], [0, 0, 0], [1, 2, 0]]

    assert _mut(setting) == {"CLAIM_FROZEN"}


def test_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _mut(lambda p: step(p, 0).__setitem__("move_universe_size", 63)) == {"EXHAUSTION_NOT_CLOSED"}
    real = L.explore
    monkeypatch.setattr(C, "explore", lambda w, s, st, f: real(w, s, st, f)[1:])
    assert "EXHAUSTION_NOT_CLOSED" in codes(drift_of(props()))


def test_context_witness() -> None:
    def ctx(p: Props) -> None:
        cw = step(p, 0)["context_witness"]
        assert isinstance(cw, dict)
        cw["positions"] = [0, 1]

    assert _mut(ctx) == {"NO_CONTEXT_WITNESS"}
    assert _mut(lambda p: step(p, 1).__setitem__("context_witness", None)) >= {"NO_CONTEXT_WITNESS"}


def test_class_preregistered(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "lifts", tmp_path / "lifts")
    (tmp_path / "predictions").mkdir()
    shutil.copy(current_context().historical_path("predictions") / "FROZEN_P2.json", tmp_path / "predictions" / "FROZEN_P2.json")
    assert drift_of(C.load_proposals(), tmp_path) == ()
    cls = tmp_path / "lifts" / "record_reading" / "CLASS.json"
    cls.write_bytes(cls.read_bytes().replace(b"strictly shorter", b"shorter"))
    assert codes(drift_of(C.load_proposals(), tmp_path)) == {"CLASS_NOT_PREREGISTERED"}


def test_minimal() -> None:
    assert _mut(lambda p: step(p, 0).__setitem__("tied_minima", 1)) == {"NOT_MINIMAL_OVER_A_CLASS"}

    def extra(p: Props) -> None:
        ans = step(p, 0)["answer"]
        assert isinstance(ans, list)
        ans.append([[1, 1], 0])
        step(p, 0)["price"] = {"enablements": 4, "key_width_added": 1}

    assert _mut(extra) == {"NOT_MINIMAL_OVER_A_CLASS"}


def test_a_skipped_rung_is_not_minimal() -> None:
    p = props()
    step(p, 0)["target"] = "rung2"
    r = C.certify_step(p, 0, C.load_pinned(p))
    assert "NOT_MINIMAL_OVER_A_CLASS" in r.failed() and "UNTRACEABLE" in r.failed()


def test_traceable() -> None:
    assert _mut(lambda p: step(p, 0).__setitem__("new_entry_offset", 0)) == {"UNTRACEABLE"}


def test_resolved() -> None:
    """The next step's survival accounting sees the earlier demand no longer
    written, so it drifts too."""
    assert _mut(lambda p: step(p, 0).__setitem__("answer", [[[0, 0], 0], [[0, 1], 2], [[1, 0], 1]])) == {
        "NOT_RESOLVED", "SILENT_DRIFT"}
    assert _mut(lambda p: step(p, 1).__setitem__(
        "answer", [[[0, 0, 0], 0], [[0, 0, 1], 0], [[0, 1, 2], 0], [[1, 2, 0], 0], [[2, 0, 1], 0]])) >= {
        "NOT_RESOLVED"}


def test_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    def wrong(table: Mapping[L.Key, int | None], ws: int, wt: int, s: L.Setting) -> dict[L.Key, int | None]:
        return {k: table[k[:ws]] for k in L.keys(wt, s) if k[:ws] in table}

    monkeypatch.setattr(C, "lift_table", wrong)
    assert "NOT_PRESERVED" in codes(drift_of(props()))


def test_rollback(monkeypatch: pytest.MonkeyPatch) -> None:
    def shifted(t: Mapping[L.Key, int | None], s: L.Setting) -> dict[L.Key, int | None]:
        return {(x,): t.get((x, (x + 1) % s.n)) for x in range(s.n)}

    monkeypatch.setitem(C.CARRIER_DOWN, "forget", (1, 2, shifted))
    assert codes(drift_of(props())) == {"RR-ROLLBACK"}


def test_non_descent(monkeypatch: pytest.MonkeyPatch) -> None:
    def defaulting(t: Mapping[L.Key, int | None], ws: int, s: L.Setting) -> dict[L.Key, int | None]:
        out: dict[L.Key, int | None] = {}
        for k, v in sorted(t.items()):
            out.setdefault(k[len(k) - ws:], v)
        return out

    monkeypatch.setattr(C, "harness_restrict", defaulting)
    assert "RR-NON-DESCENT" in codes(drift_of(props()))


def test_nontrivial() -> None:
    assert _mut(lambda p: step(p, 1).__setitem__("price", {"enablements": 0, "key_width_added": 1})) == {
        "RR-TRIVIAL-LIFT"}


def test_survival() -> None:
    assert _mut(lambda p: step(p, 0).__setitem__(
        "old_certificates", [{"class": "preserved", "id": "ceiling_rung0"},
                             {"class": "preserved", "id": "tapes_rung0"}])) == {"SILENT_DRIFT"}
    assert _mut(lambda p: step(p, 1).__setitem__(
        "old_certificates", [{"class": "refined", "id": "ceiling_rung1"},
                             {"class": "preserved", "id": "tapes_rung1"}])) == {"SILENT_DRIFT"}


def test_authority() -> None:
    assert _mut(lambda p: step(p, 1).__setitem__("activation", "granted")) == {"AUTHORITY_FIELD"}
    assert _mut(lambda p: p.__setitem__("authority_effect", "Some")) == {"AUTHORITY_FIELD"}


def test_budget() -> None:
    assert _mut(lambda p: step(p, 1).__setitem__("budget_after", 1)) == {"BUDGET_NOT_DECREASING"}
    assert _mut(lambda p: step(p, 1).__setitem__("stop", "finished")) == {"BUDGET_NOT_DECREASING"}


def test_replay() -> None:
    assert _mut(lambda p: step(p, 0).__setitem__("exhibit_pointer", ["record_runs", 4, "enablements"])) == {
        "REPLAY_MISMATCH"}


def test_chain() -> None:
    assert _mut(lambda p: step(p, 1).__setitem__("budget_before", 2)) == {"CHAIN_BROKEN"}
    assert _mut(lambda p: p.__setitem__("budget_initial", 3)) == {"CHAIN_BROKEN"}
    assert _mut(lambda p: step(p, 0).__setitem__("stop", "saturated")) == {"CHAIN_BROKEN"}

    def reuse(p: Props) -> None:
        step(p, 1)["demand_pointer"] = ["record_runs", 0, "tape"]

    assert "CHAIN_BROKEN" in _mut(reuse)


def test_chain_source_mismatch() -> None:
    p = props()
    step(p, 1)["source"] = "rung0"
    assert not C.chain(p, C.load_pinned(p)).passed


def test_drift_names_depth_and_missing_rows() -> None:
    result = C.certify_ladder(C.load_proposals())
    exp = expected()
    exp2 = copy.deepcopy(exp)
    exp2["depth"] = 1
    steps = exp2["steps"]
    assert isinstance(steps, dict)
    del steps["step1"]
    rows = C.drift(result, exp2)
    assert any("depth" in r for r in rows) and any("steps:step1:" in r for r in rows)


def test_unknown_stage_names_fail_closed() -> None:
    p = props()
    step(p, 0)["source"] = "nowhere"
    r = C.certify_step(p, 0, C.load_pinned(p))
    assert {"NO_CERTIFIED_SURVIVOR", "EXHAUSTION_NOT_CLOSED", "CLASS_NOT_PREREGISTERED"} <= set(r.failed())


def test_certificate_digest_is_stable() -> None:
    p = C.load_proposals()
    a = dumps(ladder_document(C.certify_ladder(p), p, "0" * 40))
    b = dumps(ladder_document(C.certify_ladder(p), p, "0" * 40))
    assert sha256_tag(a) == sha256_tag(b)


def test_revealed_predictions_match_their_frozen_digests() -> None:
    for frozen in sorted((current_context().historical_path("predictions")).glob("FROZEN_*.json")):
        doc = load_path(frozen)
        assert isinstance(doc, dict)
        plain = ROOT / str(doc["plaintext"]).split(" ", 1)[0]
        if plain.exists():
            data = plain.read_bytes()
            assert sha256_tag(data) == doc["sha256"] and len(data) == doc["bytes"], frozen.name
