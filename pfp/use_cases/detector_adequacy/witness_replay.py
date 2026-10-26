"""Independent replay of red witnesses, and the outcome judge.

Two separate code paths from the detectors:

* ``replay_witness`` re-derives each named step's relation with Cramer's rule and the
  Woland dossier checker's ``mv`` (``omega_engine_woland/tests/pilots/replay_runners/
  dossier_capsules/checking.py``), not with the detectors' parsing or arithmetic. A red
  verdict is sound only when every step it names is confirmed defective here.
* ``answer_is_correct`` is the outcome judge: the Woland checker's ``check_answer`` on the
  final answer against the posed system. The detectors never call it.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import sys
from fractions import Fraction
from typing import Any, Dict, Iterable, List, Tuple

from omega_engine_pfp.use_cases.detector_adequacy.detectors import repo_root
from omega_engine_pfp.use_cases.detector_adequacy.traces import cramer

WOLAND_CHECKER = "omega_engine_woland/tests/pilots/replay_runners/dossier_capsules/checking.py"

_CHECKER: Any = None


def woland_checker() -> Any:
    global _CHECKER
    if _CHECKER is None:
        path = repo_root() / WOLAND_CHECKER
        spec = importlib.util.spec_from_file_location("da001_woland_dossier_checking", path)
        if spec is None or spec.loader is None:
            raise ImportError(str(path))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _CHECKER = module
    return _CHECKER


def _f(values: Iterable[str]) -> List[Fraction]:
    return [Fraction(v) for v in values]


def _by_id(trace: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {s["id"]: s for s in trace["steps"]}


def _cited(steps: Dict[str, Dict[str, Any]], step: Dict[str, Any], kind: str) -> List[Dict[str, Any]]:
    return [steps[c] for c in step.get("cites", []) if c in steps and steps[c].get("kind") == kind]


def step_is_defective(trace: Dict[str, Any], sid: str) -> bool:
    """Re-derive one step's relation independently; True when the step is wrong."""
    steps = _by_id(trace)
    step = steps[sid]
    mv = woland_checker().mv
    kind = step["kind"]
    if kind == "given":
        return step["output"] != trace["posed"]
    if kind == "tool" and step.get("tool") == "rref":
        given = _cited(steps, step, "given")[0]["output"]
        a, b = [_f(r) for r in given["A"]], _f(given["b"])
        x = cramer(a, b)
        n = len(x)
        expected = [[Fraction(int(i == j)) for j in range(n)] + [x[i]] for i in range(n)]
        return [_f(r) for r in step["output"]["R"]] != expected
    if kind == "claim":
        rref = [s for s in _cited(steps, step, "tool") if s.get("tool") == "rref"][0]
        return _f(step["output"]["x"]) != [Fraction(r[-1]) for r in rref["output"]["R"]]
    if kind == "tool" and step.get("tool") == "residual":
        given = _cited(steps, step, "given")[0]["output"]
        x = _f(_cited(steps, step, "claim")[0]["output"]["x"])
        expected = [p - Fraction(q) for p, q in zip(mv(given["A"], x), given["b"])]
        return _f(step["output"]["r"]) != expected
    if kind == "answer":
        claim = _cited(steps, step, "claim")[0]
        checks = [s for s in _cited(steps, step, "tool") if s.get("tool") == "residual"]
        if _f(step["output"]["x"]) != _f(claim["output"]["x"]):
            return True
        return any(any(Fraction(v) != 0 for v in c["output"]["r"]) for c in checks)
    raise ValueError(f"UNKNOWN_STEP:{sid}")


def replay_witness(trace: Dict[str, Any], witness: Tuple[Tuple[str, Fraction], ...]) -> bool:
    """A witness replays when it names at least one step and every named step is defective."""
    if not witness:
        return False
    return all(step_is_defective(trace, sid) for sid, _ in witness)


def answer_is_correct(trace: Dict[str, Any]) -> bool:
    answer = next(s for s in trace["steps"] if s["kind"] == "answer")
    posed = trace["posed"]
    n = len(posed["A"])
    task = {"kind": "linear", "matrix": posed["A"], "b": posed["b"], "target": [1] + [0] * (n - 1)}
    xs = [str(Fraction(v)) for v in answer["output"]["x"]]
    return bool(woland_checker().check_answer(task, {"solution": xs, "target": xs[0]}))
