# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""The per-level work unit: load fixtures, host each one, decide it, probe
which clauses the grammar carries, and compare with frozen expectations.

A fixture's verdict: hosting first (sealed admission may refuse it); then
the claim-only requirements on the frozen claim (the claim-only part); then,
where the level has an existential part, the minimal witness search; then,
only when every relational clause holds, the decoded clauses (incidence is
checked before anything is computed from values).

AuthorityEffect: None
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

from omega_engine_operations.domain.level_engine_context import (
    current_context,
)

from .canon import load_path
from .components import available, lean_report, within_policy
from .encoding import DownCheck, Encoding, certify_hosting, encode
from .errors import IntakeRefusal, NonAdmissible
from .guards import ResourceBound
from .kinds import ConstOracle, Oracle, RegimeOracle, Req, refutation, satisfies
from .regimek import BASE, RegimeK, Stage, admit_response, host
from .sealed import AdmitDatum, AdmitForm, Regime, replay
from .search import WitnessResult, decide_k
from .structure import FiniteStructure, from_json

ROOT = current_context().runtime_root
Role = Literal["positive", "own_negative", "near_miss", "mutation", "extra"]
ROLES: tuple[str, ...] = ("positive", "own_negative", "near_miss", "mutation", "extra")


@dataclass(frozen=True)
class Fixture:
    fid: str
    role: str
    structure: FiniteStructure
    protected: tuple[tuple[int, int], ...] = ()
    violates: str | None = None
    note: str = ""


@dataclass(frozen=True)
class DecodedClause:
    """A clause decided over decoded exact values.  It receives the oracle so
    that the probe can see whether it reads derivability."""

    cid: str
    fn: Callable[[FiniteStructure, Oracle], bool]
    components: tuple[str, ...]


@dataclass(frozen=True)
class Compiled:
    reqs: tuple[Req, ...]
    witness_forms: tuple[tuple[int, tuple[int, ...]], ...] = ()
    new_forms_allowed: bool = False
    witness_needed: bool = False
    decoded: tuple[DecodedClause, ...] = ()


class Spec(Protocol):
    CHALLENGE_ID: str
    ANSWER_TYPE: str
    BOUND: int
    MEASURE: Literal["mu1", "mu2"]
    LEAN_COMPONENTS: tuple[str, ...]

    def compile_obligation(self, e: Encoding, fx: Fixture) -> Compiled: ...


@dataclass(frozen=True)
class FixtureVerdict:
    fid: str
    role: str
    admitted: bool
    satisfied: bool
    code: str
    failed: tuple[str, ...]
    refutations: tuple[tuple[str, str], ...] = ()
    witness: WitnessResult | None = None
    decoded: tuple[tuple[str, str], ...] = ()
    detail: str = ""

    def to_json(self) -> dict[str, object]:
        return {
            "admitted": self.admitted,
            "code": self.code,
            "decoded": {k: v for k, v in self.decoded},
            "detail": self.detail,
            "failed": list(self.failed),
            "fixture": self.fid,
            "refutations": {k: v for k, v in self.refutations},
            "role": self.role,
            "satisfied": self.satisfied,
            "witness": self.witness.to_json() if self.witness is not None else None,
        }


@dataclass(frozen=True)
class LevelResult:
    challenge_id: str
    answer_type: str
    verdicts: tuple[FixtureVerdict, ...]
    census: tuple[tuple[str, str, tuple[str, ...]], ...]
    hosting: DownCheck | None
    missing_components: tuple[str, ...]
    extra: Mapping[str, object] = field(default_factory=dict)
    carrier_part: str = "harness_computation"
    native_claims: tuple[Mapping[str, object], ...] = ()
    sources: tuple[str, ...] = ()

    def census_json(self) -> dict[str, object]:
        return {cid: {"census": c, "changed_on": list(on)} for cid, c, on in self.census}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


PAYLOAD_PACKAGE = "omega_engine_pfp.infrastructure.tower_research.level_engine.payload"


def load_spec(challenge_id: str) -> Spec:
    # The payloads stayed in the research package when the engine moved into
    # operations (ff295c01); resolving them beside the engine found nothing.
    mod = importlib.import_module(f"{PAYLOAD_PACKAGE}.{challenge_id}.spec")
    return mod


def _fixture(d: Mapping[str, object], where: str) -> Fixture:
    role = str(d.get("role"))
    if role not in ROLES:
        raise IntakeRefusal("MALFORMED_FIXTURE", f"{where}: unknown role {role}")
    prot = d.get("protected", [])
    assert isinstance(prot, list)
    viol = d.get("violates")
    return Fixture(
        str(d["id"]), role, from_json(d.get("structure"), f"{where}.structure"),
        tuple((int(a), int(b)) for a, b in prot), None if viol is None else str(viol), str(d.get("note", "")),
    )


def apply_mutation(pos: Fixture, m: Mapping[str, object]) -> Fixture:
    fs = pos.structure
    rm = {(str(s), tuple(int(x) for x in a)) for s, a in m.get("remove_tuples", [])}  # type: ignore[attr-defined]
    add = {(str(s), tuple(int(x) for x in a)) for s, a in m.get("add_tuples", [])}  # type: ignore[attr-defined]
    missing = rm - set(fs.tuples)
    if missing:
        raise IntakeRefusal("MALFORMED_FIXTURE", "the mutation removes a tuple the positive lacks")
    tuples = tuple(sorted((set(fs.tuples) - rm) | add))
    out = FiniteStructure(fs.sorts, fs.symbols, tuples, fs.values, fs.digests, fs.texts)
    if out == fs:
        raise IntakeRefusal("MUTATION_IS_IDENTITY", "the decisive mutation changes nothing")
    return Fixture(str(m["id"]), "mutation", out, pos.protected, str(m["violates"]), str(m.get("description", "")))


def load_fixtures(payload_dir: Path) -> tuple[Fixture, ...]:
    inst = load_path(payload_dir / "instance.json")
    if not isinstance(inst, dict) or not inst.get("fixtures"):
        raise IntakeRefusal("EMPTY_FIXTURE", f"{payload_dir.name}: no fixtures")
    raw = inst["fixtures"]
    assert isinstance(raw, list)
    fixtures = [_fixture(d, f"{payload_dir.name}.{i}") for i, d in enumerate(raw)]
    roles = [f.role for f in fixtures]
    if "own_negative" not in roles:
        raise IntakeRefusal("MISSING_NEGATIVE", f"{payload_dir.name}: no own negative")
    if "positive" not in roles:
        raise IntakeRefusal("MISSING_POSITIVE", f"{payload_dir.name}: no positive")
    mpath = payload_dir / "mutation.json"
    if mpath.exists():
        m = load_path(mpath)
        assert isinstance(m, dict)
        pos = next(f for f in fixtures if f.fid == m["of"])
        fixtures.append(apply_mutation(pos, m))
    ids = [f.fid for f in fixtures]
    if len(set(ids)) != len(ids):
        raise IntakeRefusal("MALFORMED_FIXTURE", "duplicate fixture id")
    return tuple(fixtures)


# ---------------------------------------------------------------------------
# Deciding one fixture
# ---------------------------------------------------------------------------


def hosted(spec: Spec, e: Encoding, fx: Fixture) -> tuple[RegimeK, Compiled]:
    comp = spec.compile_obligation(e, fx)
    claim = frozenset(range(e.n_claim_forms()))
    s = host(e.history, claim, comp.reqs, comp.witness_forms, comp.new_forms_allowed)
    return s, comp


def _decoded(comp: Compiled, fs: FiniteStructure, o: Oracle, have: frozenset[str]) -> tuple[tuple[str, str], ...]:
    out = []
    for c in comp.decoded:
        missing = [x for x in c.components if x not in have]
        if missing:
            out.append((c.cid, "MISSING_COMPONENT:" + ",".join(missing)))
        else:
            out.append((c.cid, "PASS" if c.fn(fs, o) else "FAIL"))
    return tuple(out)


def decide_fixture(spec: Spec, fx: Fixture, have: frozenset[str] | None = None) -> FixtureVerdict:
    have = available() if have is None else have
    try:
        e = encode(fx.structure)
    except NonAdmissible as err:
        return FixtureVerdict(fx.fid, fx.role, False, False, "NON_ADMISSIBLE", ("admission",), detail=err.detail)
    s, comp = hosted(spec, e, fx)
    o = RegimeOracle(s.base)
    claim_part = [q for q in s.reqs if s.claim_only(q) or not comp.witness_needed]
    refs = tuple((q.rid, repr(r)) for q in claim_part if (r := refutation(o, q)))
    failed = [rid for rid, _ in refs]
    w = decide_k(s, BASE, ResourceBound(spec.BOUND), spec.MEASURE)
    if comp.witness_needed and w.grade == "none" and not failed:
        failed.append("no_witness")
    if w.grade == "budget_unknown":
        failed.append("budget_unknown")
    decoded: tuple[tuple[str, str], ...] = ()
    if comp.decoded:
        if failed:
            decoded = tuple((c.cid, "NOT_EVALUATED") for c in comp.decoded)
        else:
            decoded = _decoded(comp, fx.structure, o, have)
            failed += [cid for cid, v in decoded if v != "PASS"]
    satisfied = not failed
    code = "ACCEPT" if satisfied else "FAILS:" + ",".join(sorted(failed))
    return FixtureVerdict(fx.fid, fx.role, True, satisfied, code, tuple(sorted(failed)), refs, w, decoded)


# ---------------------------------------------------------------------------
# The native-contribution probe
# ---------------------------------------------------------------------------


def _decision_regime(spec: Spec, s: RegimeK, comp: Compiled, v: FixtureVerdict) -> Regime:
    if comp.witness_needed and v.witness is not None and v.witness.minima:
        return admit_response(s, BASE, v.witness.minima[0]).base
    return s.base


def probe(spec: Spec, fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Re-decide every clause with derivability stubbed to each constant.
    A clause is ``derivability`` when its verdict changes on some fixture;
    otherwise ``decoded``.  Computed, never declared."""
    changed: dict[str, set[str]] = {}
    order: list[str] = []
    for fx, v in zip(fixtures, verdicts):
        if not v.admitted:
            continue
        e = encode(fx.structure)
        s, comp = hosted(spec, e, fx)
        r = _decision_regime(spec, s, comp, v)
        oracles: list[Oracle] = [RegimeOracle(r), ConstOracle(r, True), ConstOracle(r, False)]
        for q in s.reqs:
            if q.rid not in changed:
                changed[q.rid] = set()
                order.append(q.rid)
            vals = {satisfies(o, q) for o in oracles}
            if len(vals) > 1:
                changed[q.rid].add(fx.fid)
        for c in comp.decoded:
            if c.cid not in changed:
                changed[c.cid] = set()
                order.append(c.cid)
            vals = {c.fn(fx.structure, o) for o in oracles}
            if len(vals) > 1:
                changed[c.cid].add(fx.fid)
    return tuple(
        (cid, "derivability" if changed[cid] else "decoded", tuple(sorted(changed[cid]))) for cid in order
    )


def hosting_check(fixtures: Sequence[Fixture]) -> DownCheck:
    encs = []
    for fx in fixtures:
        try:
            encs.append(encode(fx.structure))
        except NonAdmissible:
            continue

    def new_terms(e: Encoding) -> list[Regime]:
        fresh = replay(e.history + (AdmitDatum("fresh"),))
        form = replay(e.history + (AdmitForm(2),))
        return [fresh, form]

    return certify_hosting(encs, new_terms)


def run_level(challenge_id: str, have: frozenset[str] | None = None) -> LevelResult:
    current_context().require_vendor()
    spec = load_spec(challenge_id)
    have = available() if have is None else have
    custom = getattr(spec, "evaluate", None)
    if custom is not None:
        result: LevelResult = custom(have)
        return result
    fixtures = load_fixtures(ROOT / "payload" / challenge_id)
    verdicts = tuple(decide_fixture(spec, fx, have) for fx in fixtures)
    census = probe(spec, fixtures, verdicts)
    missing = sorted(c for c in spec.LEAN_COMPONENTS if c not in have)
    extra: dict[str, object] = {}
    describe = getattr(spec, "describe", None)
    if describe is not None:
        extra["decoded_values"] = {fx.fid: describe(fx.structure) for fx in fixtures}
    claims: list[Mapping[str, object]] = []
    certificates = getattr(spec, "lean_certificates", None)
    if certificates is not None:
        report = lean_report() if any(c.startswith("lean.") for c in have) else {}
        covered: dict[str, list[bool]] = {}
        for name, fid, clause in certificates(verdicts):
            ok = within_policy(report, name)
            covered.setdefault(clause, []).append(ok)
            if ok:
                claims.append({"fixture": fid, "id": name.rsplit(".", 1)[-1], "clause": clause,
                               "lean": [{"axioms": list(report[name]), "name": name}],
                               "status": "PROVED_THEOREM"})
            else:
                missing.append(f"lean:{name}")
        extra["clause_evidence"] = {
            cid: ("LEAN" if covered.get(cid) and all(covered[cid]) else "COMPUTED") for cid, _, _ in census
        }
    return LevelResult(
        spec.CHALLENGE_ID, spec.ANSWER_TYPE, verdicts, census, hosting_check(fixtures), tuple(sorted(missing)),
        extra, native_claims=tuple(claims),
    )


# ---------------------------------------------------------------------------
# Expectations, frozen with the spec
# ---------------------------------------------------------------------------


def check_expectations(challenge_id: str, verdicts: Sequence[FixtureVerdict]) -> tuple[str, ...]:
    """Mismatches between computed verdicts and the frozen expectations.
    A refused-role fixture that is satisfied is ``RR-FIXTURE-PASSED``; a
    near-miss that fails anything but its own requirement is
    ``RR-WRONG-REASON``."""
    exp = load_path(ROOT / "payload" / challenge_id / "expect.json")
    assert isinstance(exp, dict)
    out: list[str] = []
    seen = set()
    for v in verdicts:
        seen.add(v.fid)
        if v.role in ("own_negative", "near_miss", "mutation") and v.satisfied:
            out.append(f"RR-FIXTURE-PASSED:{v.fid}")
        want = exp.get(v.fid)
        if not isinstance(want, dict):
            out.append(f"EXPECTATION_MISSING:{v.fid}")
            continue
        if want.get("code") != v.code:
            out.append(f"EXPECTATION_MISMATCH:{v.fid}")
        if "grade" in want and (v.witness is None or v.witness.grade != want["grade"]):
            out.append(f"EXPECTATION_MISMATCH:{v.fid}:grade")
    for fid in exp:
        if fid not in seen:
            out.append(f"EXPECTATION_UNUSED:{fid}")
    return tuple(sorted(set(out)))


def check_kill_rules(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> tuple[str, ...]:
    """Every near-miss fails exactly its own requirement; the decisive
    mutation fails the requirement it names."""
    out = []
    for fx, v in zip(fixtures, verdicts):
        if fx.role == "near_miss" and fx.violates is not None and v.admitted and v.failed != (fx.violates,):
            out.append(f"RR-WRONG-REASON:{fx.fid}")
        if fx.role == "mutation" and (fx.violates is None or fx.violates not in v.failed):
            out.append(f"RR-NO-FLIP:{fx.fid}")
    return tuple(out)


def stage_default() -> Stage:
    return BASE
