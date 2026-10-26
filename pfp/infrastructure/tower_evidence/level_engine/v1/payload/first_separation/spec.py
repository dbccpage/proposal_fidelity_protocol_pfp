"""The first response to the first imposed separation adds exactly one form
and one instance, and the replayed history keeps the initial inscription.

Replay of sealed evidence.  The sealed bounded search is re-run at the sealed
bounds (two items, inside the embargo) for both readings and both measures,
and the engine's own stage-0 search is run beside it; both must agree.

Clauses:

* ``shape``: the minimal response has one form and one instance.  Decided by
  derivability (the separation it answers is a derivability fact).
* ``source_kept``: the presented response keeps the supplied inscription.
  Supply provably changes no state, so this is decided on the replayed
  history: apparatus.
* ``pairing``: the new form is presented first and the new instance second.
  The order is a declared transport choice: apparatus.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.canon import load_path
from engine.components import ROOT
from engine.guards import ResourceBound
from engine.kinds import ConstOracle, Oracle, RegimeOracle, Separate, satisfies
from engine.level import FixtureVerdict, LevelResult
from engine.regimek import BASE, RegimeK, admit_response
from engine.search import decide_k
from engine.sealed import Bounds, NewForm, NewInst, Supply, replay
from engine.sealed_evidence import lean_citation
import partial_decide
from derivation.engine import READINGS

CHALLENGE_ID = "first_separation"
ANSWER_TYPE = "D"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu2"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = (
    "Derivation.cost1_insufficient_general",
    "Derivation.deltaU0_valid",
    "Derivation.deltaU0F_valid",
    "Derivation.mu1_minimum_not_unique",
    "Derivation.mu2_unique",
    "Derivation.mu2_unique_F",
    "Derivation.historyL_replays",
    "Derivation.historyF_replays",
    "Bridge.single_token_carrier_bound",
    "Bridge.second_token_required",
)
SOURCES = (
    "code/derivation/candidates.py",
    "code/derivation/engine.py",
    "code/derivation/iso.py",
    "code/derivation/model.py",
    "research/partial_decide/partial_decide.py",
)
DECLARED_PAIRING = ["0", "1"]  # new form, then new instance


def packets() -> list[tuple[str, str, dict[str, object], str | None]]:
    d = ROOT / "payload" / CHALLENGE_ID
    inst = load_path(d / "instance.json")
    assert isinstance(inst, dict) and isinstance(inst["fixtures"], list)
    out = [(str(f["id"]), str(f["role"]), dict(f["packet"]), f.get("violates")) for f in inst["fixtures"]]
    m = load_path(d / "mutation.json")
    assert isinstance(m, dict)
    base = next(p for fid, _, p, _ in out if fid == m["of"])
    out.append((str(m["id"]), "mutation", {**base, "source": m["set_source"]}, str(m["violates"])))
    return out


def lineage_table() -> dict[str, object]:
    rows: dict[str, object] = {}
    for rd in READINGS:
        base = replay(rd.genesis)
        i, j = rd.target
        s = RegimeK(base, rd.genesis, (Separate("separate", i, j),), frozenset(), (), True)
        for m in ("mu1", "mu2"):
            g = partial_decide.decide(base, i, j, m, Bounds())
            sealed_classes = len(g.quotient.classes) if isinstance(g, (partial_decide.Tie, partial_decide.UniqueClass)) else (0 if g is None else 1)
            w = decide_k(s, BASE, ResourceBound(2), m)
            rows[f"{rd.name}.{m}"] = {
                "engine_classes": len(w.classes),
                "engine_grade": w.grade,
                "engine_literal_minima": len(w.minima),
                "agree": partial_decide.grade_kind(g) == w.grade and sealed_classes == len(w.classes),
                "sealed_classes": sealed_classes,
                "sealed_grade": partial_decide.grade_kind(g),
            }
    return rows


def _shape_holds(o_for: "OracleFactory") -> bool:
    """One form and one instance separate the pair, in both readings, under
    the oracle the factory gives for the child regime."""
    for rd in READINGS:
        base = replay(rd.genesis)
        i, j = rd.target
        sep = Separate("separate", i, j)
        s = RegimeK(base, rd.genesis, (sep,), frozenset(), (), True)
        w = decide_k(s, BASE, ResourceBound(2), "mu2")
        if not w.minima:
            return False
        d = w.minima[0]
        if sorted(type(it).__name__ for it in d) != ["NewForm", "NewInst"]:
            return False
        assert any(isinstance(it, NewForm) for it in d) and any(isinstance(it, NewInst) for it in d)
        if not satisfies(o_for(admit_response(s, BASE, d).base), sep):
            return False
    return True


class OracleFactory:
    def __init__(self, stub: bool | None) -> None:
        self.stub = stub

    def __call__(self, r: object) -> Oracle:
        from engine.sealed import Regime

        assert isinstance(r, Regime)
        return RegimeOracle(r) if self.stub is None else ConstOracle(r, self.stub)


def source_token() -> str:
    first = READINGS[0].genesis[0]
    assert isinstance(first, Supply)
    return first.token


def transport(delta: tuple[object, ...]) -> dict[str, object]:
    """The declared map from a native response to a presented packet."""
    gens = [DECLARED_PAIRING[0] if isinstance(it, NewForm) else DECLARED_PAIRING[1] for it in delta]
    return {"generators": gens, "source": source_token()}


def packets_of_all_classes() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for rd in READINGS:
        base = replay(rd.genesis)
        s = RegimeK(base, rd.genesis, (Separate("separate", *rd.target),), frozenset(), (), True)
        for m in ("mu1", "mu2"):
            w = decide_k(s, BASE, ResourceBound(2), m)
            out += [transport(rep) for rep, _ in w.classes]
    return out


def evaluate(have: frozenset[str]) -> LevelResult:
    kept = all(Supply(source_token()) in rd.genesis for rd in READINGS)
    shape_real = _shape_holds(OracleFactory(None))
    shape_stub = {_shape_holds(OracleFactory(True)), _shape_holds(OracleFactory(False))}
    verdicts = []
    changed_shape = []
    for fid, role, pk, _ in packets():
        gens = pk.get("generators")
        two = isinstance(gens, list) and len(gens) == 2
        shape = shape_real and two
        if {st and two for st in shape_stub} != {shape}:
            changed_shape.append(fid)
        failed = []
        if not shape:
            failed.append("shape")
        if not (kept and pk.get("source") == source_token()):
            failed.append("source_kept")
        if gens != DECLARED_PAIRING:
            failed.append("pairing")
        ok = not failed
        verdicts.append(FixtureVerdict(fid, role, True, ok, "ACCEPT" if ok else "FAILS:" + ",".join(sorted(failed)),
                                       tuple(sorted(failed))))
    census = (
        ("shape", "derivability" if changed_shape else "decoded", tuple(sorted(changed_shape))),
        ("source_kept", "apparatus", ()),
        ("pairing", "apparatus", ()),
    )
    extra = {
        "lineages": lineage_table(),
        "state_level": {
            "L_admits_inscription": source_token() in replay(READINGS[0].genesis).data,
            "F_admits_inscription": source_token() in replay(READINGS[1].genesis).data,
        },
        "transport": {
            "declared_pairing": {"new_form": "0", "new_instance": "1", "kept_inscription": "source"},
            "packet_text": "op<<0><><0><1>>",
            "distinct_packets_over_all_classes": len({repr(p) for p in packets_of_all_classes()}),
            "classes_mapped": len(packets_of_all_classes()),
        },
    }
    claims = tuple({"id": n.split(".")[-1], "lean": [lean_citation(n)], "status": "PROVED_THEOREM"} for n in LEAN)
    return LevelResult(CHALLENGE_ID, ANSWER_TYPE, tuple(verdicts), census, None, (), extra,
                       "repo_content", claims, SOURCES)
