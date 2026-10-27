"""Domain solvers, requirement kinds, homology/holonomy routing, and stage contracts.

Targeted test suite verifying:
- 7 base requirement kinds + sovereign HomologyBoundaryClosed & HolonomyLoopClosed.
- Direct delegation of algebraic topology obligations to core_homology & core_holonomy.
- Exhaustion enumeration parity with independent binomial formula.
- Stage-change routing, 11-condition certification, licence gating, and LevelCounter.
- Value Object Exact-Type Equality Invariant across all domain dataclasses.

Governing Invariant: Zero Python Math Re-invention & Sovereign Rust Delegation.
Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
AuthorityEffect: None.
"""

from __future__ import annotations

import dataclasses
import pytest

from pfp.domain.exact.q import Q
from pfp.domain.solvers import (
    BASE,
    AdmitDatum,
    AdmitForm,
    AdmitInst,
    AdmitRuleAll,
    Closure,
    ConditionResult,
    ConstOracle,
    Denied,
    DownCheck,
    DownRule,
    Encoding,
    Exhaustion,
    FiniteStructure,
    Forbid,
    Functional,
    Holds,
    HolonomyLoopClosed,
    HomologyBoundaryClosed,
    Impose,
    Leaf,
    LevelCounter,
    Licence,
    NewDatum,
    NewForm,
    NewInst,
    NewRuleAll,
    Refusal,
    Regime,
    RegimeK,
    RegimeOracle,
    RelSym,
    Req,
    ResourceBound,
    Route,
    Separate,
    Setting,
    Stage,
    StageProposal,
    StageRefusal,
    Total,
    WitnessResult,
    certify,
    check_count,
    check_witness_only,
    class_size_formula,
    decide_k,
    encode,
    execute,
    explore,
    forms_of,
    get_holonomy_port,
    get_homology_port,
    host,
    iter_class,
    kind_of,
    licensed,
    matches,
    minima,
    pruning_sound,
    refutation,
    rename_req,
    replay,
    req_json,
    route,
    satisfies,
    universe_size,
)
from pfp.infrastructure.adapters.exact_rust_adapter import RustExactEngineAdapter

DATUM = Stage("datum", 1, frozenset({"witness_inst", "witness_form", "datum"}), 2)
ARITY3 = Stage("arity3", 1, frozenset({"witness_inst", "witness_form"}), 3)
FAMILY = (DATUM, ARITY3)


def _graph() -> tuple[RegimeK, int, int]:
    fs = FiniteStructure(
        (("node", 3),),
        (RelSym("arc", ("node", "node")),),
        (("arc", (0, 1)), ("arc", (1, 2))),
    )
    e = encode(fs)
    node, arc = e.form("node"), e.form("arc")
    return host(e.history, frozenset({0, 1}), ()), node, arc


# ---------------------------------------------------------------------------
# Sovereign Domain Ports & Delegation Verification
# ---------------------------------------------------------------------------


def test_sovereign_domain_ports_are_rust_adapters() -> None:
    """Verify that homology and holonomy ports are wired to the sovereign Rust adapter."""
    hom_port = get_homology_port()
    hol_port = get_holonomy_port()
    assert isinstance(hom_port, RustExactEngineAdapter)
    assert isinstance(hol_port, RustExactEngineAdapter)


def test_homology_boundary_closed_native_delegation() -> None:
    """Verify HomologyBoundaryClosed routes to native Rust core_homology adapter."""
    # Net cell boundary vanishing on closed cycle: 0->1, 1->2, 2->0 (sum of signed incident edges is 0)
    cycle_face = ((0, 1, 1), (1, 2, 1), (2, 0, 1))
    q_closed = HomologyBoundaryClosed("h_closed", (cycle_face,))
    o = RegimeOracle(Regime((), (), frozenset(), frozenset(), frozenset()))
    assert satisfies(o, q_closed) is True
    assert refutation(o, q_closed) == ()

    # Open line: 0->1, 1->2 has net boundary (+1 at 2, -1 at 0)
    open_face = ((0, 1, 1), (1, 2, 1))
    q_open = HomologyBoundaryClosed("h_open", (open_face,))
    assert satisfies(o, q_open) is False
    assert refutation(o, q_open) == ("boundary_law_violation",)

    # Test FiniteStructure integration
    fs = FiniteStructure(
        sorts=(("node", 3), ("edge", 3), ("face", 1)),
        symbols=(
            RelSym("edge", ("edge", "node", "node")),
            RelSym("plus", ("face", "edge")),
            RelSym("face", ("face",)),
        ),
        tuples=(
            ("edge", (3, 0, 1)),
            ("edge", (4, 1, 2)),
            ("edge", (5, 2, 0)),
            ("face", (6,)),
            ("plus", (6, 3)),
            ("plus", (6, 4)),
            ("plus", (6, 5)),
        ),
    )
    assert fs.verify_boundary_closed() is True


def test_holonomy_loop_closed_native_delegation() -> None:
    """Verify HolonomyLoopClosed routes to native Rust core_holonomy adapter."""
    # 2x2 permutation matrix [[0, 1], [1, 0]]
    # Table 0: swap (order 2)
    t0 = ((Q(0), Q(1)), (Q(1), Q(0)))
    # Path word [(0, False), (0, False)]: swap * swap = identity
    q_closed = HolonomyLoopClosed("loop_closed", (t0,), ((0, False), (0, False)))
    o = RegimeOracle(Regime((), (), frozenset(), frozenset(), frozenset()))
    assert satisfies(o, q_closed) is True

    # Path word [(0, False)]: single swap != identity
    q_open = HolonomyLoopClosed("loop_open", (t0,), ((0, False),))
    assert satisfies(o, q_open) is False

    # Test FiniteStructure integration with turn tables
    fs = FiniteStructure(
        sorts=(("axis", 3), ("turn", 1)),
        symbols=(
            RelSym("image", ("turn", "axis", "axis")),
            RelSym("flips", ("turn", "axis")),
        ),
        tuples=(
            ("image", (3, 0, 1)),
            ("image", (3, 1, 0)),
            ("image", (3, 2, 2)),
        ),
    )
    tables = fs.turn_tables()
    assert len(tables) == 1
    assert fs.is_loop_closed(((0, False), (0, False))) is True
    assert fs.is_loop_closed(((0, False),)) is False


# ---------------------------------------------------------------------------
# Base Requirement Kinds
# ---------------------------------------------------------------------------


def test_each_base_kind_decides() -> None:
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
    assert len(closure_ref) == 2
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


def test_rule_forms_enumerate_all_tuples() -> None:
    r = replay((AdmitForm(1),))
    assert list(RegimeOracle(r).instances(0)) == []
    s, node, arc = _graph()
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


# ---------------------------------------------------------------------------
# Classes, Binomial Formula, and Exhaustion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("stage", [BASE, DATUM, ARITY3])
@pytest.mark.parametrize("pruned", [True, False])
@pytest.mark.parametrize("b", [0, 1, 2])
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


# ---------------------------------------------------------------------------
# Stage Transitions, 11 Conditions, and LevelCounter
# ---------------------------------------------------------------------------


def _toy_stage_setup() -> RegimeK:
    e = encode(FiniteStructure((("elem", 2),), (), ()))
    el = e.form("elem")
    link = e.n_claim_forms()
    req = Total("reach", ((el, ("x",)),), ((link, ("x", "y", "x")), (el, ("y",))))
    return host(e.history, frozenset(range(e.n_claim_forms())), (req,), ((3, (el, el, el)),))


def test_stage_routing_and_certification() -> None:
    s = _toy_stage_setup()
    r = route(s, BASE, ResourceBound(2), FAMILY, budget=3)
    assert r.kind == "EXTEND"
    p = r.proposals[0]
    assert p.target == ARITY3 and p.chosen == ("arity3",)
    assert p.attempts.status == "CLOSED" and p.attempts.class_size == p.attempts.class_size_expected
    assert p.residual == ("reach",) and p.protected == ()
    assert p.down.defaulted == 0 and p.down.non_descent_cases > 0
    assert p.responses.grade in ("tie", "unique_class", "unique_delta")

    # Evaluate all 11 conditions
    res = certify(p, s)
    assert [c.number for c in res] == list(range(1, 12))
    assert licensed(res)

    # Execute stage progression with LevelCounter
    c0 = LevelCounter(BASE, 0, 3)
    c1 = execute(c0, p, res, Licence(True, "author"))
    assert (c1.stage, c1.count, c1.budget) == (ARITY3, 1, 2)

    # Refusals
    with pytest.raises(StageRefusal) as err:
        execute(c0, p, res, Licence(False, "nobody"))
    assert err.value.code == "NO_LICENCE"

    with pytest.raises(StageRefusal) as err:
        execute(LevelCounter(BASE, 0, 0), p, res, Licence(True, "author"))
    assert err.value.code == "NO_BUDGET"

    with pytest.raises(StageRefusal) as err:
        execute(LevelCounter(DATUM, 0, 3), p, res, Licence(True, "author"))
    assert err.value.code == "STALE_SOURCE"


# ---------------------------------------------------------------------------
# Reading Ladder Exploration
# ---------------------------------------------------------------------------


def test_reading_ladder_exploration() -> None:
    s = Setting(2, ((1, 0),))
    leaves = explore(1, s, start=0, fuel=2)
    assert len(leaves) > 0
    assert sum(lf.weight for lf in leaves) == universe_size(1, s)
    mins = minima(1, s, demand=(0, 1, 0))
    assert len(mins) >= 1


# ---------------------------------------------------------------------------
# Value Object Exact-Type Equality Invariants
# ---------------------------------------------------------------------------


class _ForeignObject:
    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


def test_value_object_exact_type_equality_rejects_cross_class() -> None:
    """Assert all solver Value Objects reject cross-class comparisons via type(self) is type(other)."""
    r = Regime((), (), frozenset(), frozenset(), frozenset())
    assert (r == _ForeignObject()) is False

    ad = AdmitDatum("tok")
    assert (ad == _ForeignObject(token="tok")) is False

    af = AdmitForm(2)
    assert (af == _ForeignObject(arity=2)) is False

    ai = AdmitInst(0, (1, 2))
    assert (ai == _ForeignObject(form=0, args=(1, 2))) is False

    ar = AdmitRuleAll(0)
    assert (ar == _ForeignObject(form=0)) is False

    imp = Impose(0, 1)
    assert (imp == _ForeignObject(i=0, j=1)) is False

    nd = NewDatum()
    assert (nd == _ForeignObject()) is False

    nf = NewForm(2)
    assert (nf == _ForeignObject(arity=2)) is False

    ni = NewInst(0, (1, 2))
    assert (ni == _ForeignObject(form=0, args=(1, 2))) is False

    nr = NewRuleAll(0)
    assert (nr == _ForeignObject(form=0)) is False

    sep = Separate("s", 0, 1)
    assert (sep == _ForeignObject(rid="s", i=0, j=1)) is False

    st = Stage("base", 0, frozenset({"witness_inst"}), 2)
    assert (st == _ForeignObject(name="base", index=0, item_kinds=frozenset({"witness_inst"}), witness_arity=2)) is False

    rb = ResourceBound(2)
    assert (rb == _ForeignObject(max_items=2)) is False

    fs = FiniteStructure((("node", 2),), (), ())
    assert (fs == _ForeignObject(sorts=(("node", 2),), symbols=(), tuples=(), values=(), digests=())) is False

    rs = RelSym("arc", ("node", "node"))
    assert (rs == _ForeignObject(name="arc", sorts=("node", "node"))) is False

    down = DownRule(1, 0, 0)
    assert (down == _ForeignObject(old_image_cases=1, non_descent_cases=0, defaulted=0)) is False

    lic = Licence(True, "author")
    assert (lic == _ForeignObject(granted=True, by="author")) is False

    cr = ConditionResult(1, True, "OK")
    assert (cr == _ForeignObject(number=1, passed=True, reason="OK")) is False

    lc = LevelCounter(st, 0, 3)
    assert (lc == _ForeignObject(stage=st, count=0, budget=3)) is False
