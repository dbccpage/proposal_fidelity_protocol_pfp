"""Typed requirement kinds, fixed claims, candidate classes, exhaustion and
the witness search."""

from __future__ import annotations

import pytest

from engine.encoding import encode
from engine.errors import ClaimFrozen, Refusal, StageRefusal
from engine.guards import ResourceBound
from engine.kinds import (
    Closure,
    ConstOracle,
    Denied,
    Forbid,
    Functional,
    Holds,
    RegimeOracle,
    Separate,
    Req,
    Total,
    forms_of,
    kind_of,
    matches,
    refutation,
    rename_req,
    req_json,
    satisfies,
)
from engine.level import ROOT, hosted, load_fixtures, load_spec
from engine.regimek import BASE, RegimeK, Stage, admit_response, check_witness_only, claims_unchanged, host
from engine.search import canonical_k, check_count, class_size_formula, decide_k, iter_class, pruning_sound
from engine.sealed import AdmitForm, AdmitInst, NewDatum, NewForm, NewInst, NewRuleAll, Regime, replay, sealed_iso
from engine.structure import FiniteStructure, RelSym

DATUM = Stage("datum", 1, frozenset({"witness_inst", "witness_form", "datum"}), 2)
ARITY3 = Stage("arity3", 1, frozenset({"witness_inst", "witness_form"}), 3)
STRUCT_LEVELS = ("edge_endpoints", "cell_faces", "cell_orientation", "distance_form")


def _graph() -> tuple[RegimeK, int, int]:
    fs = FiniteStructure((("node", 3),), (RelSym("arc", ("node", "node")),), (("arc", (0, 1)), ("arc", (1, 2))))
    e = encode(fs)
    node, arc = e.form("node"), e.form("arc")
    return host(e.history, frozenset({0, 1}), ()), node, arc


# ---------------------------------------------------------------- kinds


def test_each_kind_decides() -> None:
    s, node, arc = _graph()
    o = RegimeOracle(s.base)
    cases: list[tuple[Req, bool]] = [
        (Separate("s", 0, 2), True),
        (Holds("h", (arc, (0, 1))), True),
        (Holds("h2", (arc, (1, 0))), False),
        (Denied("d", (arc, (1, 0))), True),
        (Denied("d2", (arc, (0, 1))), False),
        (Closure("c", ((arc, ("x", "y")),), ((node, ("y",)),)), True),
        (Closure("c2", ((arc, ("x", "y")),), ((arc, ("y", "x")),)), False),
        (Forbid("f", ((arc, ("x", "x")),)), True),
        (Forbid("f2", ((arc, ("x", "y")), (arc, ("y", "z")))), False),
        (Functional("fn", arc, 1), True),
        (Functional("fn2", arc, 0), False),
        (Functional("fn3", 9, 1), True),
        (Total("t", ((node, ("x",)),), ((arc, ("x", "y")),)), False),
        (Total("t2", ((arc, ("x", "y")),), ((arc, ("y", "z")),)), False),
    ]
    for q, want in cases:
        assert satisfies(o, q) is want, q.rid
        assert (refutation(o, q) == ()) is want
    closure_ref = refutation(o, Closure("c2", ((arc, ("x", "y")),), ((arc, ("y", "x")),)))
    assert closure_ref == ((((("x", 0), ("y", 1))), ((arc, (1, 0)),)), (((("x", 1), ("y", 2))), ((arc, (2, 1)),)))
    assert list(matches(o, ((arc, ("x", "y")), (99, ("y",))))) == []
    assert kind_of(Functional("fn", arc, 1)) == "functional"


def test_kind_validation() -> None:
    with pytest.raises(ValueError):
        Holds("h", (0, ("x",)))
    with pytest.raises(ValueError):
        Denied("d", (0, ("x",)))
    with pytest.raises(ValueError):
        Closure("c", ((0, ("x",)),), ((0, ("y",)),))
    with pytest.raises(ValueError):
        Total("t", ((0, ("x",)),), ((0, ("x",)),))


def test_stubbed_derivability_closed_forms() -> None:
    s, node, arc = _graph()
    t, f = ConstOracle(s.base, True), ConstOracle(s.base, False)
    table: list[tuple[Req, bool, bool]] = [
        (Separate("s", 0, 2), False, False),
        (Holds("h", (arc, (0, 1))), True, False),
        (Denied("d", (arc, (0, 1))), False, True),
        (Closure("c", ((arc, ("x", "y")),), ((node, ("y",)),)), True, True),
        (Closure("c0", (), ((node, (0,)),)), True, False),
        (Forbid("f", ((arc, ("x", "x")),)), False, True),
        (Forbid("f0", ()), False, False),
        (Total("t", ((node, ("x",)),), ((arc, ("x", "y")),)), True, True),
        (Functional("fn", arc, 1), False, True),
    ]
    for q, want_t, want_f in table:
        assert satisfies(t, q) is want_t, q.rid
        assert satisfies(f, q) is want_f, q.rid
        assert (refutation(t, q) == ()) is want_t
    assert list(t.instances(node)) == [(0,), (1,), (2,)] and list(f.instances(node)) == []
    assert t.derivable((arc, (2, 2))) and not f.derivable((arc, (0, 1)))


def test_rule_forms_enumerate_all_tuples() -> None:
    r = replay((AdmitForm(1),) + tuple())  # no data
    assert list(RegimeOracle(r).instances(0)) == []
    s, node, arc = _graph()
    from engine.sealed import AdmitRuleAll

    rr = replay(s.history + (AdmitRuleAll(arc),))
    assert len(list(RegimeOracle(rr).instances(arc))) == 9


def test_rename_and_json_are_structural() -> None:
    s, node, arc = _graph()
    pi, phi = (2, 1, 0), (1, 0)
    reqs: list[Req] = [
        Separate("s", 0, 2),
        Holds("h", (arc, (0, 1))),
        Denied("d", (arc, (0, 1))),
        Closure("c", ((arc, ("x", 0)),), ((node, ("x",)),)),
        Forbid("f", ((arc, ("x", "x")),)),
        Total("t", ((node, ("x",)),), ((arc, ("x", "y")),)),
        Functional("fn", arc, 1),
    ]
    for q in reqs:
        r = rename_req(q, pi, phi)
        assert kind_of(r) == kind_of(q)
        assert req_json(r)["id"] == q.rid
    assert rename_req(Separate("s", 0, 1), pi, phi) == Separate("s", 1, 2)
    assert req_json(Closure("c", ((arc, ("x", 0)),), ((node, ("x",)),)))["body"] == [[arc, ["?x", 0]]]
    assert forms_of(Separate("s", 0, 1)) is None
    assert forms_of(Holds("h", (arc, (0, 1)))) == frozenset({arc})
    assert forms_of(Forbid("f", ((arc, ("x", "x")),))) == frozenset({arc})
    assert forms_of(Functional("fn", arc, 1)) == frozenset({arc})


# ---------------------------------------------------------------- fixed claims


def _all_hosted() -> list[tuple[str, RegimeK, int]]:
    out = []
    for cid in STRUCT_LEVELS:
        spec = load_spec(cid)
        for fx in load_fixtures(ROOT / "payload" / cid):
            try:
                e = encode(fx.structure)
            except Refusal:
                continue
            s, _ = hosted(spec, e, fx)
            out.append((f"{cid}:{fx.fid}", s, spec.BOUND))
    return out


def test_claims_frozen_over_every_declared_class() -> None:
    """No delta of any declared class, pruned or not, at any stage used
    here, adds an instance on a claim form; applying it leaves every claim
    form's instances unchanged."""
    checked = 0
    for name, s, bound in _all_hosted():
        for stage in (BASE, DATUM):
            for pruned in (True, False):
                b = ResourceBound(min(bound, 2))
                for delta in iter_class(s, stage, b, pruned):
                    for it in delta:
                        assert not (isinstance(it, NewInst) and it.form in s.claim_forms), name
                        assert not isinstance(it, NewRuleAll)
                    assert claims_unchanged(s, admit_response(s, stage, delta)), name
                    checked += 1
    assert checked > 1000


def test_a_claim_edit_cannot_be_expressed() -> None:
    """The claim-overwrite repair (add the missing side of a cell) is refused
    by name before any state changes."""
    spec = load_spec("cell_faces")
    fx = next(f for f in load_fixtures(ROOT / "payload" / "cell_faces") if f.fid == "near_side_outer")
    e = encode(fx.structure)
    s, _ = hosted(spec, e, fx)
    side = e.form("side")
    with pytest.raises(ClaimFrozen) as err:
        admit_response(s, BASE, (NewInst(side, (0, 2)),))
    assert err.value.code == "CLAIM_FROZEN"
    with pytest.raises(ClaimFrozen) as err:
        admit_response(s, BASE, (NewRuleAll(side),))
    assert err.value.code == "CLAIM_FROZEN"


def test_witness_only_refusals() -> None:
    s, node, arc = _graph()
    sw = host(s.history, frozenset({0, 1}), (), ((2, ()),), new_forms_allowed=False)
    sn = host(s.history, frozenset({0, 1}), (), (), new_forms_allowed=True)
    w3 = host(s.history, frozenset({0, 1}), (), ((3, ()),))
    cases: list[tuple[RegimeK, Stage, tuple[object, ...], str]] = [
        (sw, BASE, (NewRuleAll(2),), "RULE_ITEM"),
        (sw, BASE, (NewDatum(),), "ITEM_KIND"),
        (sw, BASE, (NewForm(1),), "ITEM_KIND"),
        (sn, BASE, (NewForm(3),), "WITNESS_ARITY"),
        (sn, BASE, (NewInst(2, (0,)),), "MALFORMED_DELTA"),
        (w3, BASE, (NewInst(2, (0, 0, 0)),), "WITNESS_ARITY"),
    ]
    for regk, stage, delta, code in cases:
        with pytest.raises(StageRefusal) as err:
            check_witness_only(regk, stage, delta)  # type: ignore[arg-type]
        assert err.value.code == code
    with pytest.raises(StageRefusal):
        Stage("r", 0, frozenset({"rule"}), 2)
    with pytest.raises(StageRefusal):
        Stage("u", 0, frozenset({"unknown"}), 2)
    with pytest.raises(StageRefusal):
        Stage("z", 0, frozenset(), 0)


def test_extended_state_validation() -> None:
    s, node, arc = _graph()
    with pytest.raises(StageRefusal) as err:
        RegimeK(s.base, s.history[:-1], (), frozenset({0, 1}))
    assert err.value.code == "REPLAY_MISMATCH"
    with pytest.raises(StageRefusal) as err:
        RegimeK(s.base, s.history, (), frozenset({0}))
    assert err.value.code == "SPLIT"
    with pytest.raises(StageRefusal) as err:
        RegimeK(s.base, s.history, (), frozenset({0, 1}), ((1, ()),))
    assert err.value.code == "SPLIT"
    assert s.claim_only(Holds("h", (arc, (0, 1)))) and not s.claim_only(Separate("x", 0, 1))
    w = host(s.history, frozenset({0, 1}), (), ((2, (node, node)),))
    assert w.sorts_of(2) == (node, node)
    with pytest.raises(KeyError):
        w.sorts_of(0)


# ---------------------------------------------------------------- classes and counts


@pytest.mark.parametrize("stage", [BASE, DATUM, ARITY3])
@pytest.mark.parametrize("pruned", [True, False])
@pytest.mark.parametrize("b", [0, 1, 2, 3])
def test_class_count_equals_the_independent_formula(stage: Stage, pruned: bool, b: int) -> None:
    s, node, arc = _graph()
    regk = host(s.history, frozenset({0, 1}), (), ((2, (node, node)), (1, ())), new_forms_allowed=True)
    deltas = list(iter_class(regk, stage, ResourceBound(b), pruned))
    assert len(deltas) == len(set(deltas))
    assert len(deltas) == class_size_formula(regk, stage, ResourceBound(b), pruned)


def test_count_mismatch_is_refused() -> None:
    check_count(5, 5)
    with pytest.raises(Refusal) as err:
        check_count(4, 5)
    assert err.value.code == "RR-EXHAUSTION"


def test_pruning_soundness_side_condition() -> None:
    s, node, arc = _graph()
    sorted_w = ((2, (node, node)),)
    ok = host(s.history, frozenset({0, 1}), (Forbid("f", ((2, ("x", "x")),)),), sorted_w)
    assert pruning_sound(ok)
    for q in (
        Separate("s", 0, 1),
        Holds("h", (2, (0, 1))),
        Total("t", ((node, ("x",)),), ((2, ("x", "y")),)),
    ):
        assert not pruning_sound(host(s.history, frozenset({0, 1}), (q,), sorted_w))
    guarded = Total("t", ((node, ("x",)),), ((2, ("x", "y")), (node, ("y",))))
    assert pruning_sound(host(s.history, frozenset({0, 1}), (guarded,), sorted_w))
    assert pruning_sound(host(s.history, frozenset({0, 1}), (Closure("g", ((node, ("x",)),), ((2, ("x", 0)),)),), sorted_w))


def test_pruned_and_unpruned_minima_agree() -> None:
    for name, s, bound in _all_hosted():
        b = ResourceBound(min(bound, 2))
        for m in ("mu1", "mu2"):
            p = decide_k(s, BASE, b, m)
            u = decide_k(s, BASE, b, m, pruned=False)
            assert (p.grade, p.cost, len(p.classes), p.minima) == (u.grade, u.cost, len(u.classes), u.minima), name


def test_denied_terminal_holds_exhaustively() -> None:
    """Where a claim-only requirement fails, no delta of the unpruned class
    (fresh data and fresh forms allowed) is a valid response."""
    from engine.regimek import valid_response
    from engine.search import denied_terminal

    seen = 0
    for name, s, bound in _all_hosted():
        if not denied_terminal(s):
            continue
        s2 = RegimeK(s.base, s.history, s.reqs, s.claim_forms, s.witness_forms, True)
        for delta in iter_class(s2, DATUM, ResourceBound(2), pruned=False):
            assert not valid_response(s2, DATUM, delta), name
            seen += 1
    assert seen > 500


def test_canonical_key_agrees_with_the_sealed_partition() -> None:
    from derivation.engine import READINGS

    from engine.sealed import delta_events, Impose

    for rd in READINGS:
        base = replay(rd.genesis)
        s = RegimeK(base, rd.genesis, (Separate("sep", *rd.target),), frozenset(), (), True)
        deltas = list(iter_class(s, BASE, ResourceBound(2), pruned=True))
        ours: dict[str, set[int]] = {}
        theirs: dict[object, set[int]] = {}
        for k, d in enumerate(deltas):
            ours.setdefault(repr(canonical_k(admit_response(s, BASE, d))), set()).add(k)
            child = replay((Impose(*rd.target),) + delta_events(base, d), base)
            theirs.setdefault(sealed_iso.canonical(child), set()).add(k)
        assert sorted(map(sorted, ours.values())) == sorted(map(sorted, theirs.values()))


def test_iso_budget_is_a_named_terminal() -> None:
    fs = FiniteStructure((("node", 9),), (), ())
    e = encode(fs)
    s = host(e.history, frozenset({0}), ())
    with pytest.raises(sealed_iso.IsoBudgetError):
        canonical_k(s)


def test_budget_unknown_when_evaluation_budget_runs_out(monkeypatch: pytest.MonkeyPatch) -> None:
    import engine.search as S

    s, node, arc = _graph()
    regk = host(s.history, frozenset({0, 1}), (Holds("h", (2, (0, 1))), Holds("h2", (2, (1, 2)))), ((2, ()),))
    monkeypatch.setattr(S, "EVAL_BUDGET", 3)
    w = S.decide_k(regk, BASE, ResourceBound(2))
    assert w.grade == "budget_unknown" and w.exhaustion.status == "BUDGET_UNKNOWN"
    assert w.to_json()["grade"] == "budget_unknown"


def test_a_class_over_the_budget_is_declared_before_enumeration(monkeypatch: pytest.MonkeyPatch) -> None:
    import engine.search as S

    s, node, arc = _graph()
    regk = host(s.history, frozenset({0, 1}), (Holds("h", (2, (0, 1))), Holds("h2", (2, (1, 2)))), ((2, ()),))
    count = S.class_size_formula(regk, BASE, ResourceBound(3), True)
    monkeypatch.setattr(S, "EVAL_BUDGET", count - 1)
    tried: list[object] = []
    real = S.iter_class

    def counting(*a: object) -> object:
        tried.append(a)
        return real(*a)  # type: ignore[arg-type]

    monkeypatch.setattr(S, "iter_class", counting)
    w = S.decide_k(regk, BASE, ResourceBound(3))
    ex = w.exhaustion
    assert (w.grade, ex.status, ex.theorem) == ("budget_unknown", "BUDGET_UNKNOWN", "class_over_budget")
    assert (ex.class_size, ex.class_size_expected, tried) == (0, count, [])
    monkeypatch.setattr(S, "EVAL_BUDGET", count)
    assert S.decide_k(regk, BASE, ResourceBound(3)).exhaustion.status == "FOUND"


def test_an_enumeration_that_outruns_its_count_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    import engine.search as S

    s, node, arc = _graph()
    regk = host(s.history, frozenset({0, 1}), (Holds("h", (2, (0, 1))),), ((2, ()),))
    monkeypatch.setattr(S, "class_size_formula", lambda *a: 2)
    with pytest.raises(Refusal) as e:
        S.decide_k(regk, BASE, ResourceBound(2))
    assert e.value.code == "RR-EXHAUSTION"


def test_unique_delta_and_mu2_refinement() -> None:
    s, node, arc = _graph()
    regk = host(s.history, frozenset({0, 1}), (Holds("h", (2, (0, 1))),), ((2, ()),))
    w = decide_k(regk, BASE, ResourceBound(2))
    assert w.grade == "unique_delta" and w.cost == (1, -1) and w.minima == ((NewInst(2, (0, 1)),),)
    j = w.to_json()
    assert j["literal_minima"] == 1 and j["classes"] == [{"representative": [["inst", 2, [0, 1]]], "size": 1}]


def test_regime_type_is_the_sealed_one() -> None:
    s, node, arc = _graph()
    assert isinstance(s.base, Regime)
    assert s.history[-1] == AdmitInst(arc, (1, 2))
