"""Local-only detectors for PREREG-DA-001 decision B1 (Jeremy, 2026-10-15).

The rule is that no evaluator has a global view. Each local evaluator sees one step and the
steps it cites directly, and nothing else. It never sees the posed item, never sees the outcome
judge, and never counts across the whole trace. A step's relation that would need more than
that is not evaluated, so the given step has no local relation at all.

Both detectors reuse the locked relations in ``detectors.py`` (imported, not edited) and the
locked paper 033 pi. They place each step's local defect on its own triangle, as D2 does.

* ``D3_local_all`` keeps every local relation. On these traces the local relations together
  re-derive ``A x = b`` for the trace's own copy of the system. It measures what locality alone
  hides.
* ``D4_local_restricted`` keeps only the read relation (claim against the cited reduction). This
  is the B1 candidate, because its relations do not jointly re-derive ``A x = b``.

These detectors are exploratory. They were written after the held-out families were seen, so
their battery rates are not adequacy certificates. AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Callable, Dict, List, Tuple

from pfp.use_cases.detector_adequacy import detectors as d

Relation = Callable[[Dict[str, Any], d.Steps, Dict[str, Any]], Fraction]

NO_POSED: Dict[str, Any] = {}


def _local_relations(step: Dict[str, Any]) -> Dict[str, Relation]:
    kind, tool = step.get("kind"), step.get("tool")
    if kind == "tool" and tool == "rref":
        return {"rref": d._rref_defect}
    if kind == "tool" and tool == "residual":
        return {"residual": d._residual_defect}
    if kind == "claim" and step.get("claim") == "read_solution":
        return {"read": d._read_defect}
    if kind == "answer":
        return {"answer": d._answer_defect}
    return {}


def _neighbourhood(step: Dict[str, Any], steps: d.Steps) -> d.Steps:
    """The step and the steps it cites directly: the whole of a local evaluator's view."""
    view = {step["id"]: step}
    for c in step.get("cites", []):
        if c in steps:
            view[c] = steps[c]
    return view


def _steps(trace: Dict[str, Any]) -> d.Steps:
    steps: d.Steps = {}
    for step in trace.get("steps", []):
        sid = step.get("id")
        if type(sid) is not str or sid in steps:
            raise d.Refusal("BAD_STEP_ID")
        steps[sid] = step
    return steps


def local_defects(trace: Dict[str, Any], keep: Tuple[str, ...]) -> Dict[str, Fraction]:
    """Each step's defect, computed from its one-hop view only. Refuses what it cannot read."""
    steps = _steps(trace)
    out: Dict[str, Fraction] = {}
    for sid in sorted(steps):
        for name, relation in _local_relations(steps[sid]).items():
            if name not in keep:
                continue
            try:
                out[sid] = relation(steps[sid], _neighbourhood(steps[sid], steps), NO_POSED)
            except (KeyError, TypeError, IndexError) as exc:
                raise d.Refusal("MALFORMED_TRACE") from exc
    return out


def _carrier(defects: Dict[str, Fraction]) -> d.Carrier:
    vertices: List[str] = []
    edges: List[Tuple[str, str]] = []
    omega: Dict[Tuple[str, str], Fraction] = {}
    owner: Dict[Tuple[str, str], str] = {}
    for sid, defect in sorted(defects.items()):
        src, claim, check = f"{sid}:src", f"{sid}:claim", f"{sid}:check"
        vertices += [src, claim, check]
        for e, w in (((src, claim), Fraction(0)), ((src, check), Fraction(0)), ((claim, check), defect)):
            edges.append(e)
            omega[e] = w
            owner[e] = sid
    return vertices, edges, omega, owner


ALL_LOCAL = ("rref", "read", "residual", "answer")
RESTRICTED = ("read",)

LOCAL_DETECTORS: Dict[str, Tuple[str, ...]] = {
    "D3_local_all": ALL_LOCAL,
    "D4_local_restricted": RESTRICTED,
}


def run_local(name: str, trace: Dict[str, Any]) -> d.Verdict:
    pi = d.load_pi()
    try:
        vertices, edges, omega, owner = _carrier(local_defects(trace, LOCAL_DETECTORS[name]))
    except d.Refusal as exc:
        return d.Verdict(name, d.NONCERTIFYING, "ExtractorRefused", None, None, (), exc.code)
    if not edges:
        return d.Verdict(name, d.NONCERTIFYING, "ExtractorRefused", None, None, (), "NOTHING_LOCAL")
    verdict = pi.TraceValidator.validate_trace(pi.CarrierGraph.create(vertices, edges), omega)
    certified = verdict.diagnostics.get("certified")
    if verdict.status == pi.STATUS_EXACT:
        return d.Verdict(name, d.GREEN, verdict.status, verdict.phi_1, certified, (), None)
    if verdict.status != pi.STATUS_OBSTRUCTION:
        return d.Verdict(name, d.NONCERTIFYING, verdict.status, None, certified, (),
                         str(verdict.diagnostics.get("error", verdict.status)))
    dual = verdict.dual_witness or {}
    named: Dict[str, Fraction] = {}
    for e, w in core.items():
        if w != 0 and dual.get(e, Fraction(0)) != 0:
            named[owner[e]] = named.get(owner[e], Fraction(0)) + w
    return d.Verdict(name, d.RED, verdict.status, verdict.phi_1, certified, tuple(sorted(named.items())), None)
