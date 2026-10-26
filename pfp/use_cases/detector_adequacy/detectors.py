"""Locked detectors for PREREG-DA-001: trace extractors feeding one residual terminalizer.

The terminalizer pi is ``TraceValidator.validate_trace`` from paper 033 of the finite
obstruction calculus (exact rational l1 obstruction on a declared carrier graph). It is
loaded from its file and pinned by SHA-256 in the lock manifest; it is not modified here.

Each extractor turns a trace into a carrier graph and a 1-cochain ``omega``. All three
share the same per-step relations (``relation_defects``) and differ only in the carrier
they build and in how they treat a relation they cannot evaluate:

* ``E0_tree``: one edge per step, to its first citation. The carrier is a forest, every
  cochain on a forest is a coboundary, so pi returns Exact on every trace. This is the
  collapsing extractor named in ch07 and serves as the negative control of the battery.
* ``E0b_citation_graph``: one edge per citation, each carrying the citing step's defect.
  Cycles exist, but a defect that sits on every incoming edge of a step cancels around
  any cycle through two of those edges.
* ``E1_disjoint_triangles``: each relation gets its own 3-cycle with the defect on one
  edge, so no two relations share an edge or a vertex and nothing can cancel. A step that
  lacks a required citation makes the extractor refuse (non-certifying), instead of
  skipping the relation.

Verdicts: Exact -> ``green``; CohomologicalObstruction -> ``red`` with a witness naming
the steps whose edges carry the dual certificate; anything else -> ``noncertifying``.
Defects are exact: every relation compares rationals parsed from ``"p/q"`` strings, and a
non-rational field is a refusal, never a zero. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

PI_RELATIVE_PATH = (
    "omega_engine_atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/"
    "033_reasoning_trace_validation_via_l1_obstruction_geometry/code/"
    "mod_reasoning_trace_validation_core.py"
)

GREEN = "green"
RED = "red"
NONCERTIFYING = "noncertifying"


def repo_root(start: Path = Path(__file__).resolve()) -> Path:
    for parent in start.parents:
        if (parent / "pyproject.toml").is_file() and (parent / "omega_engine_pfp").is_dir():
            return parent
    raise FileNotFoundError("repository root with pyproject.toml not found")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


_PI_MODULE: Any = None


def load_pi() -> Any:
    global _PI_MODULE
    if _PI_MODULE is None:
        path = repo_root() / PI_RELATIVE_PATH
        if not path.is_file():
            raise FileNotFoundError(str(path))
        spec = importlib.util.spec_from_file_location("da001_trace_validation_core", path)
        if spec is None or spec.loader is None:
            raise ImportError(str(path))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _PI_MODULE = module
    return _PI_MODULE


class Refusal(Exception):
    """The extractor cannot evaluate a relation; the code names the reason."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Verdict:
    detector: str
    status: str
    pi_status: str
    phi_1: Optional[Fraction]
    certified: Optional[bool]
    witness: Tuple[Tuple[str, Fraction], ...]
    refusal: Optional[str]


# ---- exact parsing ------------------------------------------------------------


def rat(value: Any) -> Fraction:
    if type(value) is not str:
        raise Refusal("NON_RATIONAL_FIELD")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise Refusal("NON_RATIONAL_FIELD") from exc


def vec(values: Any) -> List[Fraction]:
    if not isinstance(values, list) or not values:
        raise Refusal("MALFORMED_VECTOR")
    return [rat(v) for v in values]


def mat(rows: Any) -> List[List[Fraction]]:
    if not isinstance(rows, list) or not rows:
        raise Refusal("MALFORMED_MATRIX")
    out = [vec(r) for r in rows]
    if len({len(r) for r in out}) != 1:
        raise Refusal("RAGGED_MATRIX")
    return out


def l1(u: List[Fraction], v: List[Fraction]) -> Fraction:
    if len(u) != len(v):
        raise Refusal("DIMENSION_MISMATCH")
    return sum((abs(a - b) for a, b in zip(u, v)), Fraction(0))


def matvec(a: List[List[Fraction]], x: List[Fraction]) -> List[Fraction]:
    if any(len(row) != len(x) for row in a):
        raise Refusal("DIMENSION_MISMATCH")
    return [sum((p * q for p, q in zip(row, x)), Fraction(0)) for row in a]


# ---- per-step relations -------------------------------------------------------

Steps = Dict[str, Dict[str, Any]]


def _cited(step: Dict[str, Any], steps: Steps, kind: str, tool: Optional[str] = None) -> List[Dict[str, Any]]:
    out = []
    for cid in step.get("cites", []):
        if cid not in steps:
            raise Refusal("DANGLING_CITATION")
        cited = steps[cid]
        if cited.get("kind") == kind and (tool is None or cited.get("tool") == tool):
            out.append(cited)
    return out


def _one(found: List[Dict[str, Any]], code: str) -> Dict[str, Any]:
    if len(found) != 1:
        raise Refusal(code)
    return found[0]


def _given_defect(step: Dict[str, Any], steps: Steps, posed: Dict[str, Any]) -> Fraction:
    a, b = mat(step["output"]["A"]), vec(step["output"]["b"])
    pa, pb = mat(posed["A"]), vec(posed["b"])
    if len(a) != len(pa):
        raise Refusal("DIMENSION_MISMATCH")
    return sum((l1(r, s) for r, s in zip(a, pa)), Fraction(0)) + l1(b, pb)


def _rref_defect(step: Dict[str, Any], steps: Steps, posed: Dict[str, Any]) -> Fraction:
    given = _one(_cited(step, steps, "given"), "RREF_WITHOUT_GIVEN")
    a, b = mat(given["output"]["A"]), vec(given["output"]["b"])
    r = mat(step["output"]["R"])
    n = len(a)
    if len(r) != n or len(r[0]) != n + 1:
        raise Refusal("DIMENSION_MISMATCH")
    left = sum((abs(r[i][j] - (1 if i == j else 0)) for i in range(n) for j in range(n)), Fraction(0))
    x = [row[-1] for row in r]
    return left + l1(matvec(a, x), b)


def _read_defect(step: Dict[str, Any], steps: Steps, posed: Dict[str, Any]) -> Fraction:
    rref = _one(_cited(step, steps, "tool", "rref"), "CLAIM_WITHOUT_RREF")
    return l1(vec(step["output"]["x"]), [row[-1] for row in mat(rref["output"]["R"])])


def _residual_defect(step: Dict[str, Any], steps: Steps, posed: Dict[str, Any]) -> Fraction:
    given = _one(_cited(step, steps, "given"), "RESIDUAL_WITHOUT_GIVEN")
    claim = _one(_cited(step, steps, "claim"), "RESIDUAL_WITHOUT_CLAIM")
    a, b = mat(given["output"]["A"]), vec(given["output"]["b"])
    ax = matvec(a, vec(claim["output"]["x"]))
    return l1(vec(step["output"]["r"]), [p - q for p, q in zip(ax, b)])


def _answer_defect(step: Dict[str, Any], steps: Steps, posed: Dict[str, Any]) -> Fraction:
    claim = _one(_cited(step, steps, "claim"), "ANSWER_WITHOUT_CLAIM")
    checks = _cited(step, steps, "tool", "residual")
    if not checks:
        raise Refusal("ANSWER_WITHOUT_RESIDUAL_CHECK")
    defect = l1(vec(step["output"]["x"]), vec(claim["output"]["x"]))
    for check in checks:
        defect += sum((abs(v) for v in vec(check["output"]["r"])), Fraction(0))
    return defect


def _relation(step: Dict[str, Any]) -> Callable[[Dict[str, Any], Steps, Dict[str, Any]], Fraction]:
    kind, tool = step.get("kind"), step.get("tool")
    if kind == "given":
        return _given_defect
    if kind == "tool" and tool == "rref":
        return _rref_defect
    if kind == "tool" and tool == "residual":
        return _residual_defect
    if kind == "claim" and step.get("claim") == "read_solution":
        return _read_defect
    if kind == "answer":
        return _answer_defect
    raise Refusal("UNKNOWN_STEP")


def index_steps(trace: Dict[str, Any]) -> Steps:
    steps: Steps = {}
    for step in trace.get("steps", []):
        sid = step.get("id")
        if type(sid) is not str or sid in steps:
            raise Refusal("BAD_STEP_ID")
        steps[sid] = step
    if sum(1 for s in steps.values() if s.get("kind") == "answer") != 1:
        raise Refusal("ANSWER_COUNT")
    return steps


def relation_defects(trace: Dict[str, Any], lenient: bool) -> Dict[str, Fraction]:
    """Exact defect of every step's relation. Lenient extractors skip what they cannot evaluate."""
    steps = index_steps(trace)
    posed = trace.get("posed")
    if not isinstance(posed, dict):
        raise Refusal("NO_POSED_ITEM")
    defects: Dict[str, Fraction] = {}
    for sid in sorted(steps):
        try:
            defects[sid] = _relation(steps[sid])(steps[sid], steps, posed)
        except (Refusal, KeyError, TypeError):
            if not lenient:
                raise
    return defects


# ---- extractors ---------------------------------------------------------------

Carrier = Tuple[List[str], List[Tuple[str, str]], Dict[Tuple[str, str], Fraction], Dict[Tuple[str, str], str]]


def extract_e0_tree(trace: Dict[str, Any]) -> Carrier:
    steps = index_steps(trace)
    defects = relation_defects(trace, lenient=True)
    vertices = sorted(steps)
    edges, omega, owner = [], {}, {}
    for sid in vertices:
        cites = [c for c in steps[sid].get("cites", []) if c in steps]
        if cites and sid in defects:
            e = (cites[0], sid)
            edges.append(e)
            omega[e] = defects[sid]
            owner[e] = sid
    return vertices, edges, omega, owner


def extract_e0b_citation_graph(trace: Dict[str, Any]) -> Carrier:
    steps = index_steps(trace)
    defects = relation_defects(trace, lenient=True)
    vertices = sorted(steps)
    edges, omega, owner = [], {}, {}
    for sid in vertices:
        if sid not in defects:
            continue
        for c in steps[sid].get("cites", []):
            if c in steps and (c, sid) not in omega:
                e = (c, sid)
                edges.append(e)
                omega[e] = defects[sid]
                owner[e] = sid
    return vertices, edges, omega, owner


def extract_e1_disjoint_triangles(trace: Dict[str, Any]) -> Carrier:
    defects = relation_defects(trace, lenient=False)
    vertices, edges, omega, owner = [], [], {}, {}
    for sid, d in sorted(defects.items()):
        src, claim, check = f"{sid}:src", f"{sid}:claim", f"{sid}:check"
        vertices += [src, claim, check]
        for e, w in (((src, claim), Fraction(0)), ((src, check), Fraction(0)), ((claim, check), d)):
            edges.append(e)
            omega[e] = w
            owner[e] = sid
    return vertices, edges, omega, owner


EXTRACTORS: Dict[str, Callable[[Dict[str, Any]], Carrier]] = {
    "D0_E0_tree": extract_e0_tree,
    "D1_E0b_citation_graph": extract_e0b_citation_graph,
    "D2_E1_disjoint_triangles": extract_e1_disjoint_triangles,
}


def run_detector(name: str, trace: Dict[str, Any]) -> Verdict:
    pi = load_pi()
    try:
        vertices, edges, omega, owner = EXTRACTORS[name](trace)
    except Refusal as exc:
        return Verdict(name, NONCERTIFYING, "ExtractorRefused", None, None, (), exc.code)
    except (KeyError, TypeError):
        return Verdict(name, NONCERTIFYING, "ExtractorRefused", None, None, (), "MALFORMED_TRACE")
    graph = pi.CarrierGraph.create(vertices, edges)
    verdict = pi.TraceValidator.validate_trace(graph, omega)
    certified = verdict.diagnostics.get("certified")
    if verdict.status == pi.STATUS_EXACT:
        return Verdict(name, GREEN, verdict.status, verdict.phi_1, certified, (), None)
    if verdict.status != pi.STATUS_OBSTRUCTION:
        return Verdict(name, NONCERTIFYING, verdict.status, None, certified, (),
                       str(verdict.diagnostics.get("error", verdict.status)))
    dual = verdict.dual_witness or {}
    named: Dict[str, Fraction] = {}
    for e, w in omega.items():
        if w != 0 and dual.get(e, Fraction(0)) != 0:
            named[owner[e]] = named.get(owner[e], Fraction(0)) + w
    return Verdict(name, RED, verdict.status, verdict.phi_1, certified, tuple(sorted(named.items())), None)


def locked_files() -> Dict[str, str]:
    """Repository-relative paths whose bytes the lock manifest pins."""
    here = Path(__file__).resolve()
    root = repo_root()
    rel = here.parent.relative_to(root).as_posix()
    return {
        "pi": PI_RELATIVE_PATH,
        "detectors": f"{rel}/detectors.py",
        "witness_replay": f"{rel}/witness_replay.py",
        "pre_lock_mutants": f"{rel}/traces.py",
    }
