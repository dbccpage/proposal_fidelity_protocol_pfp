"""Replay of sealed evidence: a peak of the sealed two-rule rewrite system on
event lists, both of its arms and their join, stated over letters.

The sealed system (``derivation.trace_algebra``, read from the pinned clone)
rewrites event lists by adjacent idempotence (``e e -> e``) and terminal
absorption (``halt r ... -> halt``); it is terminating and confluent with a
unique normal form (sealed ``TraceAlgebra.rw_confluent``, ``nf_unique``) and
deliberately incomplete (``rewrite_not_complete``).  Each event of the
sealed rewrite alphabet is written as one letter, in the alphabet's order.
Absorption is stated per letter (``h x -> h``); a step counts only when its
result is one of the sealed system's own one-step reducts.

The positive is found, not written: the first list of the sealed battery (at
the sealed length bound) with two stated steps whose results differ; each
arm then takes the first stated step until no step applies.

Clauses, each decided on the replayed sealed system (outside the regime
grammar):

* ``steps_replayed``: every step's rule occurs at its position, and its
  result is a sealed one-step reduct of the term it rewrites;
* ``arms_meet``: both arms end at one term;
* ``join_is_normal_form``: the declared join is where the arms end, and it is
  the sealed normal form of the source.

AuthorityEffect: None
"""

from __future__ import annotations

from typing import Literal

from engine.canon import load_path
from engine.components import ROOT
from engine.level import FixtureVerdict, LevelResult
from engine.sealed_evidence import lean_citation
from derivation.trace_algebra import REWRITE_ALPHABET, list_battery, nf, no_redex, rw_reducts

CHALLENGE_ID = "positioned_join"
ANSWER_TYPE = "M"
BOUND = 3
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
LEAN = ("TraceAlgebra.rw_confluent", "TraceAlgebra.nf_unique", "TraceAlgebra.rewrite_not_complete",
        "TraceAlgebra.rw_sound")
SOURCES = ("code/derivation/trace_algebra.py", "code/derivation/primitive_passage.py",
           "code/derivation/transition_alphabet.py")
LETTERS = "abch"
CLAUSES = ("steps_replayed", "arms_meet", "join_is_normal_form")
Step = tuple[int, int]


def rules() -> list[tuple[str, str]]:
    """Adjacent idempotence per letter, then absorption per following letter."""
    halt = LETTERS[REWRITE_ALPHABET.index(("halt",))]
    return [(x + x, x) for x in LETTERS] + [(halt + x, halt) for x in LETTERS if x != halt]


def events(term: str) -> list[tuple[object, ...]]:
    return [REWRITE_ALPHABET[LETTERS.index(c)] for c in term]


def word(evs: list[tuple[object, ...]]) -> str:
    return "".join(LETTERS[REWRITE_ALPHABET.index(e)] for e in evs)


def apply(term: str, step: Step) -> str | None:
    """The stated step's result, or ``None`` when its rule does not occur at
    its position or its result is not a sealed one-step reduct."""
    pos, k = step
    rs = rules()
    if not 0 <= k < len(rs) or not 0 <= pos <= len(term):
        return None
    lhs, rhs = rs[k]
    if term[pos:pos + len(lhs)] != lhs:
        return None
    out = term[:pos] + rhs + term[pos + len(lhs):]
    return out if events(out) in rw_reducts(events(term)) else None


def stated_steps(term: str) -> list[tuple[Step, str]]:
    out = []
    for pos in range(len(term)):
        for k in range(len(rules())):
            res = apply(term, (pos, k))
            if res is not None:
                out.append(((pos, k), res))
    return out


def arm(term: str) -> list[Step]:
    steps: list[Step] = []
    while not no_redex(events(term)):
        (step, term) = stated_steps(term)[0]
        steps.append(step)
    return steps


def found_peak() -> dict[str, object]:
    for lst in list_battery(BOUND):
        term = word(lst)
        steps = stated_steps(term)
        for i, (s1, r1) in enumerate(steps):
            for s2, r2 in steps[i + 1:]:
                if r1 != r2:
                    return {"join": word(nf(lst)), "left_arm": [list(s) for s in arm(r1)], "left_step": list(s1),
                            "right_arm": [list(s) for s in arm(r2)], "right_step": list(s2),
                            "rules": [list(r) for r in rules()], "source": term}
    raise RuntimeError("no peak in the sealed battery")


def packets() -> list[tuple[str, str, dict[str, object], str | None]]:
    """The found positive, then each declared fixture as a set of fields
    replaced in it, then the mutation."""
    d = ROOT / "payload" / CHALLENGE_ID
    pos = found_peak()
    inst = load_path(d / "instance.json")
    assert isinstance(inst, dict) and isinstance(inst["fixtures"], list)
    out: list[tuple[str, str, dict[str, object], str | None]] = [("pos", "positive", pos, None)]
    for f in inst["fixtures"]:
        out.append((str(f["id"]), str(f["role"]), {**pos, **f["set"]}, f.get("violates")))
    m = load_path(d / "mutation.json")
    assert isinstance(m, dict)
    out.append((str(m["id"]), "mutation", {**pos, **m["set"]}, str(m["violates"])))
    return out


def _steps(value: object) -> list[Step] | None:
    if not isinstance(value, list) or not all(isinstance(s, list) and len(s) == 2 for s in value):
        return None
    return [(int(s[0]), int(s[1])) for s in value]


def decide(pk: dict[str, object]) -> tuple[str, ...]:
    """The clauses a packet fails, decided on the replayed sealed system."""
    source = str(pk["source"])
    if pk["rules"] != [list(r) for r in rules()]:
        return CLAUSES
    peak = _steps([pk["left_step"], pk["right_step"]])
    arms = (_steps(pk["left_arm"]), _steps(pk["right_arm"]))
    if peak is None or arms[0] is None or arms[1] is None:
        return ("steps_replayed",)
    ends: list[str] = []
    for first, rest in zip(peak, arms):
        term: str | None = apply(source, first)
        for s in rest or []:
            term = None if term is None else apply(term, s)
        if term is None:
            return ("steps_replayed",)
        ends.append(term)
    if ends[0] != ends[1]:
        return ("arms_meet",)
    if pk["join"] != ends[0] or events(ends[0]) != nf(events(source)):
        return ("join_is_normal_form",)
    return ()


EMPTY_ARM_SEARCH = 4


def peaks_with_an_empty_arm(bound: int = EMPTY_ARM_SEARCH) -> list[str]:
    """Sources of the sealed battery (up to ``bound``) with a peak of two
    stated steps where one result is already normal, so its arm is empty."""
    out = []
    for lst in list_battery(bound):
        term = word(lst)
        steps = stated_steps(term)
        if any(r1 != r2 and (no_redex(events(r1)) or no_redex(events(r2)))
               for i, (_, r1) in enumerate(steps) for _, r2 in steps[i + 1:]):
            out.append(term)
    return out


def evaluate(have: frozenset[str]) -> LevelResult:
    verdicts = []
    for fid, role, pk, _ in packets():
        failed = decide(pk)
        verdicts.append(FixtureVerdict(fid, role, True, not failed,
                                       "ACCEPT" if not failed else "FAILS:" + ",".join(sorted(failed)), failed))
    census = tuple((c, "decoded", ()) for c in CLAUSES)
    claims = tuple({"id": n.split(".")[-1], "lean": [lean_citation(n)], "status": "PROVED_THEOREM"} for n in LEAN)
    extra = {"peak": found_peak(), "battery_bound": BOUND, "rules": len(rules()),
             "peaks_with_an_empty_arm": {"searched_up_to_length": EMPTY_ARM_SEARCH,
                                         "sources": peaks_with_an_empty_arm()}}
    return LevelResult(CHALLENGE_ID, ANSWER_TYPE, tuple(verdicts), census, None, (), extra,
                       "repo_content", claims, SOURCES)
