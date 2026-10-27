# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""The lift certifier for a reading ladder: every condition of a stage change,
computed from the carrier's pinned evidence, never read from the proposal.

A proposal names a step from rung j to rung j + 1: the demand (a tape the
carrier exhibits), the claimed witnesses, the answer at the target rung, the
down map it relies on, the budget and the old certificates.  The certifier
recomputes each condition from the pinned claims (the demand and the setting
as the carrier's evidence has them) and compares what the proposal declares.
All sixteen step conditions are evaluated; nothing short-circuits.  The
chain condition is evaluated over the steps in order, and the certified
depth is the longest licensed prefix of an unbroken chain.

The down map is the carrier's own.  A step whose carrier map is total, or
missing, fails the rollback or descent condition by name.  The same step is
also certified with the harness's partial restriction as a diagnostic, which
never enters the verdict or the depth.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from operations.domain.level_engine_context import (
    current_context,
)
from pfp.domain.lean_bridge.models import STANDARD_LEAN_AXIOMS

from .canon import dumps, load_path, sha256_tag
from .errors import NonDescent, Refusal
from .ladder import (
    Key,
    Leaf,
    Setting,
    carrier_forget,
    collisions,
    explore,
    full_tables,
    functional,
    harness_restrict,
    key_at,
    leaves_digest,
    lift_table,
    minima,
    run,
    universe_size,
)
from .sealed import vendored

ROOT = current_context().runtime_root
Variant = Literal["carrier", "harness"]

# (condition, section of the reach definition, depth criterion, refusal code)
CONDITIONS: tuple[tuple[str, str, str, str], ...] = (
    ("survivor", "5.1", "R2.2", "NO_CERTIFIED_SURVIVOR"),
    ("claims_fixed", "5.1", "R2.2", "CLAIM_FROZEN"),
    ("exhaustion", "5.2", "R2.4", "EXHAUSTION_NOT_CLOSED"),
    ("context_witness", "5.3", "R2.3", "NO_CONTEXT_WITNESS"),
    ("class_preregistered", "5.4", "R2.5", "CLASS_NOT_PREREGISTERED"),
    ("minimal", "5.4", "R2.6", "NOT_MINIMAL_OVER_A_CLASS"),
    ("traceable", "5.5", "R2.5", "UNTRACEABLE"),
    ("resolved", "5.5", "R2.6", "NOT_RESOLVED"),
    ("preserved", "5.5", "R2.7", "NOT_PRESERVED"),
    ("rollback", "5.5", "R2.8", "RR-ROLLBACK"),
    ("non_descent", "5.5", "R2.8", "RR-NON-DESCENT"),
    ("nontrivial", "5.5", "R2.9", "RR-TRIVIAL-LIFT"),
    ("survival", "5.6", "R2.10", "SILENT_DRIFT"),
    ("authority", "5.7", "R2.13", "AUTHORITY_FIELD"),
    ("budget", "5.8", "R2.11", "BUDGET_NOT_DECREASING"),
    ("replay", "5.5", "R2.13", "REPLAY_MISMATCH"),
)
CHAIN = ("chain", "5", "R2.1", "CHAIN_BROKEN")
CODES = {name: code for name, _, _, code in CONDITIONS} | {CHAIN[0]: CHAIN[3]}
STOPS = frozenset({"continued", "saturated", "blocked", "self_reference_stop", "budget_exhausted"})
FORBIDDEN_FIELDS = frozenset({"licence", "license", "licensed", "execute", "execution", "activate", "activation"})
POLICY = frozenset(STANDARD_LEAN_AXIOMS)

# The carrier's down maps, by (source width, target width).  record_reading
# defines ``forget`` from the width-two machine to the memoryless one, and no
# map from the width-three machine down.
CARRIER_DOWN: dict[str, tuple[int, int, Callable[[Mapping[Key, int | None], Setting], dict[Key, int | None]]]] = {
    "forget": (1, 2, carrier_forget),
}


@dataclass(frozen=True)
class Condition:
    name: str
    section: str
    criterion: str
    passed: bool
    code: str
    detail: str

    def to_json(self) -> dict[str, object]:
        return {"code": "OK" if self.passed else self.code, "criterion": self.criterion, "detail": self.detail,
                "name": self.name, "passed": self.passed, "section": self.section}


@dataclass(frozen=True)
class StepResult:
    step: str
    variant: Variant
    conditions: tuple[Condition, ...]
    facts: Mapping[str, object]

    @property
    def licensed(self) -> bool:
        return all(c.passed for c in self.conditions)

    def failed(self) -> tuple[str, ...]:
        return tuple(c.code for c in self.conditions if not c.passed)


# ---------------------------------------------------------------------------
# Pinned inputs
# ---------------------------------------------------------------------------


def pointer(doc: object, path: Sequence[str | int]) -> object:
    cur = doc
    for part in path:
        if isinstance(part, int) and isinstance(cur, list) and 0 <= part < len(cur):
            cur = cur[part]
        elif isinstance(part, str) and isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise Refusal("POINTER", f"no {part!r} along {list(path)}")
    return cur


def _ints(obj: object) -> tuple[int, ...]:
    if not isinstance(obj, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in obj):
        raise Refusal("NOT_A_TAPE", "expected a list of data")
    return tuple(obj)


@dataclass(frozen=True)
class Pinned:
    evidence: Mapping[str, object]
    lean_reports: Mapping[str, tuple[str, ...]]
    setting: Setting
    class_doc: Mapping[str, object]
    class_sha256: str
    preregistered_sha256: str | None


def load_pinned(props: Mapping[str, object], root: Path = ROOT) -> Pinned:
    carrier = props["carrier"]
    assert isinstance(carrier, dict)
    ev = load_path(vendored(str(carrier["evidence"])))
    assert isinstance(ev, dict)
    lean = load_path(vendored(str(carrier["lean_evidence"])))
    assert isinstance(lean, dict)
    reports_raw = lean["reports"]
    assert isinstance(reports_raw, dict)
    reports = {str(k): tuple(str(a) for a in v) for k, v in reports_raw.items()}
    st = props["setting"]
    assert isinstance(st, dict)
    n = pointer(ev, st["n_pointer"])
    ops = pointer(ev, st["ops_pointer"])
    assert isinstance(n, int) and isinstance(ops, list)
    setting = Setting(n, tuple(_ints(op) for op in ops))
    class_bytes = (root / str(props["class"])).read_bytes()
    class_doc = load_path(root / str(props["class"]))
    assert isinstance(class_doc, dict)
    frozen = load_path(current_context().historical_path(str(props["pre_registration"])))
    assert isinstance(frozen, dict)
    pre = frozen.get("pre_registered", {})
    assert isinstance(pre, dict)
    entry = next((v for v in pre.values() if isinstance(v, dict) and v.get("path") == props["class"]), None)
    return Pinned(ev, reports, setting, class_doc, sha256_tag(class_bytes),
                  None if entry is None else str(entry["sha256"]))


def widths(pinned: Pinned) -> dict[str, int]:
    members = pinned.class_doc["members"]
    assert isinstance(members, list)
    return {str(m["name"]): int(m["key_width"]) for m in members}


def table_of(pairs: object) -> dict[Key, int | None]:
    assert isinstance(pairs, list)
    out: dict[Key, int | None] = {}
    for k, v in pairs:
        out[tuple(int(x) for x in k)] = None if v is None else int(v)
    return out


def exhibit_table(enablements: object) -> dict[Key, int | None]:
    """The carrier's enablement rows ``[..key.., op]`` as a table."""
    assert isinstance(enablements, list)
    return {tuple(int(x) for x in row[:-1]): int(row[-1]) for row in enablements}


# ---------------------------------------------------------------------------
# One step
# ---------------------------------------------------------------------------


def _down(step: Mapping[str, object], variant: Variant, ws: int, wt: int, s: Setting
          ) -> Callable[[Mapping[Key, int | None]], dict[Key, int | None]] | None:
    if variant == "harness":
        return lambda t: harness_restrict(t, ws, s)
    name = step.get("down_map")
    if not isinstance(name, str) or name not in CARRIER_DOWN:
        return None
    src_w, tgt_w, fn = CARRIER_DOWN[name]
    if (src_w, tgt_w) != (ws, wt):
        return None
    return lambda t: fn(t, s)


def _record(res: list[Condition], name: str, ok: bool, detail: str) -> None:
    sec, crit, code = next((a, b, c) for n, a, b, c in CONDITIONS if n == name)
    res.append(Condition(name, sec, crit, ok, code, detail))


def _certify_51(
    res: list[Condition], facts: dict[str, object], step: Mapping[str, object], props: Mapping[str, object],
    demand: tuple[int, ...], ws: int, s: Setting, realizers: int, size: int,
) -> None:
    # 5.1 survivor: nothing at the source rung writes the demand, and the
    # declared dual witness replays on the demand alone
    dw = step.get("dual_witness")
    dual_ok = False
    if isinstance(dw, list) and len(dw) == 2 and ws:
        i, j = int(dw[0]), int(dw[1])
        dual_ok = (0 <= i < j < len(demand) - 1 and key_at(demand, i, ws) == key_at(demand, j, ws)
                   and demand[i + 1] != demand[j + 1])
    facts["dual_witnesses"] = [list(p) for p in collisions(demand, ws)] if ws else []
    _record(res, "survivor", realizers == 0 and dual_ok and size > 0,
            f"{realizers} programs of {size} write the demand; declared dual witness replays: {dual_ok}")
    # 5.1 claims fixed: the demand and the setting are the carrier's
    n_decl = pointer(props, ["setting", "n"])
    assert isinstance(n_decl, int)
    declared_setting = Setting(n_decl, tuple(_ints(o) for o in _list(pointer(props, ["setting", "ops"]))))
    claims_ok = tuple(_ints(step["demand"])) == demand and declared_setting == s
    _record(res, "claims_fixed", claims_ok, "declared demand and setting equal the pinned evidence" if claims_ok
            else "the proposal rewrites the demand or the setting")


def _certify_52(res: list[Condition], step: Mapping[str, object], covered: int, size: int) -> None:
    # 5.2 exhaustion
    ex_ok = covered == size and size > 0 and step.get("move_universe_size") == size
    _record(res, "exhaustion", ex_ok, f"covered {covered} of {size}; declared {step.get('move_universe_size')}")


def _certify_53(
    res: list[Condition], facts: dict[str, object], step: Mapping[str, object],
    demand: tuple[int, ...], ws: int, wt: int,
) -> tuple[int, int] | None:
    # 5.3 context witness: collapsed at the source, separated at the target by the new entry
    cw = step.get("context_witness")
    ctx_ok = False
    if isinstance(cw, dict) and ws and wt:
        pos = cw.get("positions")
        off = cw.get("separating_offset")
        if isinstance(pos, list) and len(pos) == 2 and isinstance(off, int):
            i, j = int(pos[0]), int(pos[1])
            if 0 <= i < j < len(demand) - 1 and 0 <= off < wt:
                ki, kj = key_at(demand, i, wt), key_at(demand, j, wt)
                diff = [wt - 1 - t for t in range(wt) if ki[t] != kj[t]]
                ctx_ok = (key_at(demand, i, ws) == key_at(demand, j, ws) and demand[i + 1] != demand[j + 1]
                          and diff == [off] and off >= ws)
    found = next(((i, j) for i, j in collisions(demand, ws) if key_at(demand, i, wt) != key_at(demand, j, wt)),
                 None) if ws and wt else None
    facts["context_witness"] = None if found is None else {
        "context": f"the entry {ws} back", "x": list(key_at(demand, found[0], wt)),
        "y": list(key_at(demand, found[1], wt)), "positions": list(found)}
    _record(res, "context_witness", ctx_ok, "the declared pair is collapsed at the source and separated by the new entry"
            if ctx_ok else "the declared pair does not recompute as a context witness")
    return found


def _certify_54(
    res: list[Condition], facts: dict[str, object], step: Mapping[str, object], pinned: Pinned,
    s: Setting, demand: tuple[int, ...], ws: int, wt: int, ws_all: dict[str, int], src: str, tgt: str,
) -> tuple[tuple[tuple[tuple[Key, int], ...], ...], dict[Key, int | None]]:
    # 5.4 class frozen before the run
    members = sorted(ws_all.items(), key=lambda kv: kv[1])
    cls_ok = (pinned.preregistered_sha256 == pinned.class_sha256 and src in ws_all and tgt in ws_all
              and len({w for _, w in members}) == len(members))
    _record(res, "class_preregistered", cls_ok, f"class {pinned.class_sha256} pre-registered as {pinned.preregistered_sha256}")
    # 5.4 minimal over the class, ties retained
    mins = minima(wt, s, demand) if wt else ()
    between = [n for n, w in members if ws < w < wt]
    between_fail = all(not minima(ws_all[n], s, demand) for n in between)
    answer = table_of(step["answer"])
    cost = len(mins[0]) if mins else -1
    above = [n for n, w in members if w > wt]
    facts["minimal_extension"] = {
        "cost": cost, "tied_minima": len(mins),
        "tied_minima_sha256": sha256_tag(dumps([[[list(k), v] for k, v in m] for m in mins])),
        "nonminimal_probe": [{"member": n, "writes_the_demand": bool(minima(ws_all[n], s, demand)),
                              "refused": "NONMINIMAL_EXTENSION"} for n in above],
    }
    min_ok = (bool(mins) and wt > ws and between_fail and step.get("tied_minima") == len(mins)
              and len(answer) == cost and all(v is not None for v in answer.values()))
    _record(res, "minimal", min_ok, f"{len(mins)} tied minima of cost {cost}; answer cost {len(answer)}")
    return mins, answer


def _certify_traceable(
    res: list[Condition], step: Mapping[str, object], answer: Mapping[Key, int | None], s: Setting, ws: int, wt: int,
) -> None:
    # 5.5 traceable: the new entry separates the witness and the answer reads it
    cw = step.get("context_witness")
    new_offsets = list(range(ws, wt))
    try:
        harness_restrict(answer, ws, s)
        reads_new = False
    except NonDescent:
        reads_new = True
    tr_ok = (step.get("new_entry_offset") in new_offsets and len(new_offsets) == 1 and reads_new
             and isinstance(cw, dict) and cw.get("separating_offset") == step.get("new_entry_offset"))
    _record(res, "traceable", tr_ok, f"new entry offsets {new_offsets}; the answer reads it: {reads_new}")


def _certify_resolved(
    res: list[Condition], answer: Mapping[Key, int | None], wt: int, s: Setting, demand: tuple[int, ...], fuel: int,
) -> None:
    # 5.5 resolved: the answer writes the demand at the target
    try:
        written = run(answer, wt, s, demand[0], fuel, strict=True) if wt else ()
    except Refusal:
        written = ()
    _record(res, "resolved", written == demand, f"the answer writes {list(written)}")


def _certify_preserved(
    res: list[Condition], facts: dict[str, object], s: Setting, fuel: int, ws: int, wt: int, size: int,
) -> tuple[set[tuple[int, ...]], bool]:
    # 5.5 preserved: every source program, lifted, writes the same tape from every start
    pres_cov = 0
    pres_ok = bool(ws) and wt > ws
    old_tapes: set[tuple[int, ...]] = set()
    for start in range(s.n) if pres_ok else ():
        for lf in explore(ws, s, start, fuel):
            pres_cov += lf.weight
            old_tapes.add(lf.tape)
            try:
                same = run(lift_table(dict(lf.assign), ws, wt, s), wt, s, start, fuel, strict=True) == lf.tape
            except Refusal:
                same = False
            pres_ok = pres_ok and same
    pres_ok = pres_ok and pres_cov == s.n * size
    facts["protected"] = {"distinct_old_tapes": len(old_tapes), "programs_by_start": pres_cov,
                          "tapes_sha256": sha256_tag(dumps(sorted(list(x) for x in old_tapes)))}
    _record(res, "preserved", pres_ok, f"{pres_cov} source programs by start checked against their lifts")
    return old_tapes, pres_ok


def _certify_rollback(
    res: list[Condition], step: Mapping[str, object], variant: Variant, ws: int, wt: int, s: Setting,
    leaves: tuple[Leaf, ...],
) -> tuple[Callable[[Mapping[Key, int | None]], dict[Key, int | None]] | None, int, int]:
    # 5.5 rollback and descent, through the down map this variant uses
    down = _down(step, variant, ws, wt, s) if ws and wt else None
    old_cases = old_programs = 0
    rb_ok = down is not None
    if down is not None:
        try:
            tables = [(t, 1) for t in full_tables(ws, s)]
        except Refusal:
            tables = [(dict(lf.assign), lf.weight) for lf in leaves]
        for t, weight in tables:
            old_cases += 1
            old_programs += weight
            try:
                back = down(lift_table(t, ws, wt, s))
            except NonDescent:
                rb_ok = False
                continue
            rb_ok = rb_ok and back == t
    _record(res, "rollback", rb_ok, f"d(u(x)) = x on {old_cases} old images standing for {old_programs} programs" if rb_ok
            else "no carrier down map for this step" if down is None else "d(u(x)) differs from x")
    return down, old_cases, old_programs


def _certify_non_descent(
    res: list[Condition], facts: dict[str, object], step: Mapping[str, object], pinned: Pinned, variant: Variant,
    mins: tuple[tuple[tuple[Key, int], ...], ...],
    down: Callable[[Mapping[Key, int | None]], dict[Key, int | None]] | None,
    old_cases: int, old_programs: int,
) -> None:
    new_terms: list[dict[Key, int | None]] = [dict(m) for m in mins]
    new_terms.append(exhibit_table(pointer(pinned.evidence, step["exhibit_pointer"])))
    refused = defaulted = 0
    for t in new_terms:
        if down is None:
            continue
        try:
            down(t)
            defaulted += 1
        except NonDescent:
            refused += 1
    facts["down_rule"] = {"map": step.get("down_map") if variant == "carrier" else "harness_partial_restriction",
                          "old_image_identity_cases": old_cases, "old_image_programs": old_programs,
                          "new_terms": len(new_terms),
                          "non_descent_refusals": refused, "defaulted": defaulted}
    _record(res, "non_descent", down is not None and refused > 0 and defaulted == 0,
            f"{refused} new terms refused, {defaulted} given an old meaning" if down is not None
            else "no down map, so no new term is refused")


def _certify_nontrivial(
    res: list[Condition], facts: dict[str, object], step: Mapping[str, object], s: Setting,
    demand: tuple[int, ...], ws: int, wt: int, found: tuple[int, int] | None, answer: Mapping[Key, int | None],
) -> None:
    # 5.5 non-trivial and priced
    price = {"enablements": len(answer), "key_width_added": wt - ws}
    acts = False
    if found is not None:
        oi, oj = answer.get(key_at(demand, found[0], wt)), answer.get(key_at(demand, found[1], wt))
        acts = oi is not None and oj is not None and s.ops[oi][demand[found[0]]] != s.ops[oj][demand[found[1]]]
    nt_ok = acts and step.get("price") == price and price["enablements"] > 0
    facts["price"] = price
    _record(res, "nontrivial", nt_ok, f"acts differently on the collapsed pair: {acts}; price {price}")


def _certify_55(
    res: list[Condition], facts: dict[str, object], step: Mapping[str, object], pinned: Pinned, variant: Variant,
    s: Setting, demand: tuple[int, ...], fuel: int, ws: int, wt: int, leaves: tuple[Leaf, ...], size: int,
    found: tuple[int, int] | None, mins: tuple[tuple[tuple[Key, int], ...], ...], answer: Mapping[Key, int | None],
) -> tuple[set[tuple[int, ...]], bool]:
    _certify_traceable(res, step, answer, s, ws, wt)
    _certify_resolved(res, answer, wt, s, demand, fuel)
    old_tapes, pres_ok = _certify_preserved(res, facts, s, fuel, ws, wt, size)
    down, old_cases, old_programs = _certify_rollback(res, step, variant, ws, wt, s, leaves)
    _certify_non_descent(res, facts, step, pinned, variant, mins, down, old_cases, old_programs)
    _certify_nontrivial(res, facts, step, s, demand, ws, wt, found, answer)
    return old_tapes, pres_ok


def _certify_56(
    res: list[Condition], facts: dict[str, object], steps: list[object], index: int, pinned: Pinned, s: Setting,
    demand: tuple[int, ...], ws: int, wt: int, ws_all: dict[str, int], src: str, step: Mapping[str, object],
    old_tapes: set[tuple[int, ...]], pres_ok: bool,
) -> None:
    # 5.6 survival accounting
    computed: dict[str, str] = {}
    if ws and wt:
        old_ceiling = all(functional(t, ws) for t in old_tapes)
        computed[f"ceiling_{src}"] = ("preserved" if functional(demand, ws) else
                                      "refined" if old_ceiling and functional(demand, wt) else "invalidated")
        computed[f"tapes_{src}"] = "preserved" if pres_ok else "invalidated"
    for k in range(index if ws and wt else 0):
        prev = steps[k]
        assert isinstance(prev, dict)
        pd = _ints(pointer(pinned.evidence, prev["demand_pointer"]))
        pw = ws_all.get(str(prev["target"]), 0)
        try:
            ok = pw == ws and run(lift_table(table_of(prev["answer"]), pw, wt, s), wt, s, pd[0], len(pd) - 1,
                                  strict=True) == pd
        except Refusal:
            ok = False
        computed[f"demand_{prev['id']}"] = "preserved" if ok else "invalidated"
    declared = {str(c["id"]): str(c["class"]) for c in _list(step.get("old_certificates", [])) if isinstance(c, dict)}
    facts["survival"] = dict(sorted(computed.items()))
    _record(res, "survival", declared == computed, f"computed {dict(sorted(computed.items()))}")


def _certify_57(res: list[Condition], props: Mapping[str, object], step: Mapping[str, object]) -> None:
    # 5.7 authority: evidence only
    auth_ok = props.get("authority_effect") == "None" and not (set(step) & FORBIDDEN_FIELDS) and not (
        set(props) & FORBIDDEN_FIELDS)
    _record(res, "authority", auth_ok, "no licence, execution or activation field" if auth_ok else "an authority field")


def _certify_58(res: list[Condition], step: Mapping[str, object]) -> None:
    # 5.8 budget and a typed stop
    bb, ba = step.get("budget_before"), step.get("budget_after")
    bud_ok = (isinstance(bb, int) and isinstance(ba, int) and not isinstance(bb, bool) and not isinstance(ba, bool)
              and 0 <= ba < bb and step.get("stop") in STOPS)
    _record(res, "budget", bud_ok, f"{bb} -> {ba}, stop {step.get('stop')}")


def _certify_replay(
    res: list[Condition], step: Mapping[str, object], pinned: Pinned, s: Setting,
    demand: tuple[int, ...], fuel: int, wt: int,
) -> None:
    # replay: the carrier's exhibit program writes the demand through this
    # mirror, and the mirror reproduces the carrier's committed census
    exhibit = exhibit_table(pointer(pinned.evidence, step["exhibit_pointer"]))
    exhibit_tape = run(exhibit, wt, s, demand[0], fuel) if wt else ()
    census_ok = census_agrees(pinned.evidence)
    _record(res, "replay", exhibit_tape == demand and census_ok,
            f"the carrier's exhibit writes {list(exhibit_tape)}; the mirror's census agrees: {census_ok}")


def certify_step(props: Mapping[str, object], index: int, pinned: Pinned, variant: Variant = "carrier") -> StepResult:
    steps = props["steps"]
    assert isinstance(steps, list)
    step = steps[index]
    assert isinstance(step, dict)
    s = pinned.setting
    ws_all = widths(pinned)
    src, tgt = str(step["source"]), str(step["target"])
    ws, wt = ws_all.get(src, 0), ws_all.get(tgt, 0)
    demand = _ints(pointer(pinned.evidence, step["demand_pointer"]))
    fuel = len(demand) - 1
    res: list[Condition] = []
    facts: dict[str, object] = {"demand": list(demand), "source": src, "target": tgt,
                                "source_key_width": ws, "target_key_width": wt}

    # same-level search at the source rung, over every program, from the demand's start
    leaves: tuple[Leaf, ...] = explore(ws, s, demand[0], fuel) if ws else ()
    covered = sum(lf.weight for lf in leaves)
    size = universe_size(ws, s) if ws else 0
    realizers = sum(lf.weight for lf in leaves if lf.tape == demand)
    facts["same_level_search"] = {"closed": covered == size and size > 0, "covered": covered,
                                  "leaves": len(leaves), "leaves_sha256": leaves_digest(leaves),
                                  "move_universe_size": size, "realizers": realizers}

    _certify_51(res, facts, step, props, demand, ws, s, realizers, size)
    _certify_52(res, step, covered, size)
    found = _certify_53(res, facts, step, demand, ws, wt)
    mins, answer = _certify_54(res, facts, step, pinned, s, demand, ws, wt, ws_all, src, tgt)
    old_tapes, pres_ok = _certify_55(
        res, facts, step, pinned, variant, s, demand, fuel, ws, wt, leaves, size, found, mins, answer,
    )
    _certify_56(
        res, facts, steps, index, pinned, s, demand, ws, wt, ws_all, src, step, old_tapes, pres_ok,
    )
    _certify_57(res, props, step)
    _certify_58(res, step)
    _certify_replay(res, step, pinned, s, demand, fuel, wt)

    lean = []
    for name in _list(step.get("lean", [])):
        ax = pinned.lean_reports.get(str(name))
        lean.append({"axioms": None if ax is None else list(ax), "name": str(name),
                     "within_policy": ax is not None and set(ax) <= POLICY})
    facts["lean"] = lean
    return StepResult(str(step["id"]), variant, tuple(res), facts)


def _list(obj: object) -> list[object]:
    if not isinstance(obj, list):
        raise Refusal("NOT_A_LIST", "expected a list")
    return obj


def census_agrees(evidence: Mapping[str, object]) -> bool:
    """The mirror against the carrier's committed ladder census: every
    deterministic program of each rung on its two-point setting, every start."""
    lad = pointer(evidence, ["depth_two", "ladder"])
    assert isinstance(lad, dict)
    s2 = Setting(2, tuple(_ints(o) for o in _list(lad["ops_in_index_order"])))
    fuel = int(lad["fuel"])
    below: set[tuple[int, ...]] = set()
    ok = True
    for w, row in zip((1, 2, 3), _list(lad["rows"])):
        assert isinstance(row, dict)
        tapes = {lf.tape for st in range(s2.n) for lf in explore(w, s2, st, fuel)}
        ok = ok and len(tapes) == row["tapes_realised"] and all(functional(t, w) for t in tapes)
        if w > 1:
            ok = ok and sorted(list(t) for t in tapes if not functional(t, w - 1)) == row[
                "tapes_breaking_the_ceiling_below"]
            ok = ok and sorted(list(t) for t in tapes - below) == row["tapes_the_depth_below_cannot_realise"]
        below = tapes
    return ok


# ---------------------------------------------------------------------------
# The chain and the depth
# ---------------------------------------------------------------------------


def chain(props: Mapping[str, object], pinned: Pinned) -> Condition:
    steps = _list(props["steps"])
    ok = bool(steps)
    notes = []
    demands = []
    for k, st in enumerate(steps):
        assert isinstance(st, dict)
        demands.append(_ints(pointer(pinned.evidence, st["demand_pointer"])))
        if k == 0:
            if st.get("budget_before") != props.get("budget_initial"):
                ok = False
                notes.append("the first step does not start from the declared budget")
            continue
        prev = steps[k - 1]
        assert isinstance(prev, dict)
        if st.get("source") != prev.get("target"):
            ok = False
            notes.append(f"{st['id']} does not start where {prev['id']} ends")
        if st.get("budget_before") != prev.get("budget_after"):
            ok = False
            notes.append(f"{st['id']} does not start from {prev['id']}'s remaining budget")
    if len(set(demands)) != len(demands):
        ok = False
        notes.append("one residual licenses two steps")
    for k, st in enumerate(steps):
        assert isinstance(st, dict)
        last = k == len(steps) - 1
        if (st.get("stop") == "continued") == last:
            ok = False
            notes.append(f"{st['id']} has the wrong stop for its place")
    return Condition(CHAIN[0], CHAIN[1], CHAIN[2], ok, CHAIN[3], "; ".join(notes) or "unbroken")


@dataclass(frozen=True)
class LadderResult:
    steps: tuple[StepResult, ...]
    diagnostics: tuple[StepResult, ...]
    chain: Condition
    depth: int


def certify_ladder(props: Mapping[str, object], root: Path = ROOT) -> LadderResult:
    pinned = load_pinned(props, root)
    n = len(_list(props["steps"]))
    steps = tuple(certify_step(props, k, pinned, "carrier") for k in range(n))
    diags = tuple(certify_step(props, k, pinned, "harness") for k in range(n))
    ch = chain(props, pinned)
    depth = 0
    for r in steps:
        if not (r.licensed and ch.passed):
            break
        depth += 1
    return LadderResult(steps, diags, ch, depth)


def load_proposals(rel: str = "lifts/record_reading/proposals.json", root: Path = ROOT) -> dict[str, object]:
    doc = load_path(root / rel)
    assert isinstance(doc, dict)
    return doc


def verdicts(result: LadderResult) -> dict[str, object]:
    """The per-condition outcomes, in the shape the frozen expectations use."""
    def one(r: StepResult) -> dict[str, str]:
        return {c.name: ("PASS" if c.passed else c.code) for c in r.conditions}

    return {
        "chain": "PASS" if result.chain.passed else result.chain.code,
        "depth": result.depth,
        "diagnostic": {r.step: one(r) for r in result.diagnostics},
        "steps": {r.step: one(r) for r in result.steps},
    }


def drift(result: LadderResult, expected: Mapping[str, object]) -> tuple[str, ...]:
    """Every difference from the frozen expectations, named with the code."""
    got = verdicts(result)
    out: list[str] = []
    for part in ("steps", "diagnostic"):
        want = expected.get(part, {})
        have = got[part]
        assert isinstance(want, dict) and isinstance(have, dict)
        for step in sorted(set(want) | set(have)):
            w, h = want.get(step, {}), have.get(step, {})
            for name in sorted(set(w) | set(h)):
                if w.get(name) != h.get(name):
                    code = h.get(name) if h.get(name) not in (None, "PASS") else CODES.get(name, name)
                    out.append(f"LIFT_VERDICT_DRIFT {part}:{step}:{name}: expected {w.get(name)}, computed "
                               f"{h.get(name)} ({code})")
    if expected.get("chain") != got["chain"]:
        out.append(f"LIFT_VERDICT_DRIFT chain: expected {expected.get('chain')}, computed {got['chain']} "
                   f"({CHAIN[3]})")
    if expected.get("depth") != got["depth"]:
        out.append(f"LIFT_VERDICT_DRIFT depth: expected {expected.get('depth')}, computed {got['depth']}")
    return tuple(out)
