"""Shared scoring and invocation for calibration task checkers. AuthorityEffect: None.

A review answer is a JSON object {"flagged_claims": [ids]} naming every claim that is
false or not supported by the information given. The checker supplies the truth of each
claim from its own computation, never from a typed answer list.

Invocation: `check.py <answer>` prints only {"pass": true|false}, so a workflow that
reads the checker's output during repair cannot learn which items were wrong.
`check.py --detail <answer>` prints the full verdict for the yardstick's own scoring.
`check.py --reference` prints the computed answer key. A checker refuses to score when
its prompt no longer shows the data and claims it scores against.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from pathlib import Path


def score(text: str, claims: dict[str, str], must_flag: set[str]) -> dict:
    try:
        answer = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"pass": False, "problems": [f"not a JSON object: {exc.msg}"]}
    if type(answer) is not dict or set(answer) != {"flagged_claims"}:
        return {"pass": False, "problems": ["answer must be exactly {\"flagged_claims\": [...]}"]}
    flagged = answer["flagged_claims"]
    if type(flagged) is not list or any(type(item) is not str for item in flagged):
        return {"pass": False, "problems": ["flagged_claims must be a list of claim ids"]}
    problems = []
    if len(set(flagged)) != len(flagged):
        problems.append("flagged_claims repeats an id")
    unknown = sorted(set(flagged) - set(claims))
    if unknown:
        problems.append(f"unknown claim ids {unknown}")
    chosen = set(flagged) & set(claims)
    missed, false_alarms = sorted(must_flag - chosen), sorted(chosen - must_flag)
    if missed:
        problems.append(f"missed {missed}")
    if false_alarms:
        problems.append(f"false alarms {false_alarms}")
    return {"pass": not problems, "problems": problems,
            "answer": {"flagged_claims": sorted(chosen), "detected": len(must_flag & chosen),
                       "planted": len(must_flag), "false_alarms": len(false_alarms)}}


def prompt_problems(prompt: Path, fragments: Iterable[str]) -> list[str]:
    try:
        text = prompt.read_text(encoding="utf-8")
    except OSError:
        return ["prompt.md is unreadable"]
    missing = [fragment for fragment in fragments if fragment not in text]
    return ["prompt.md does not show the checked data or claims"] if missing else []


def run(argv: list[str], *, check: Callable[[str], dict], reference: Callable[[], object],
        prompt: Path, fragments: Iterable[str]) -> int:
    """Shared entry point; see the module docstring for the three invocations."""
    if argv[1:] == ["--reference"]:
        print(json.dumps(reference(), sort_keys=True))
        return 0
    detail = len(argv) == 3 and argv[1] == "--detail"
    if not (len(argv) == 2 or detail):
        print(json.dumps({"pass": False, "problems": ["usage: check.py [--detail] <answer-file>"]}))
        return 1
    drift = prompt_problems(prompt, fragments)
    if drift:
        print(json.dumps({"pass": False, "problems": drift}))
        return 1
    try:
        text = Path(argv[-1]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        verdict = {"pass": False, "problems": [f"cannot read answer: {type(exc).__name__}"]}
    else:
        verdict = check(text)
    print(json.dumps(verdict if detail else {"pass": verdict["pass"]}, sort_keys=True))
    return 0 if verdict["pass"] else 1


def claim_fragments(claims: dict[str, str]) -> list[str]:
    return [f"`{claim}`: {text}" for claim, text in claims.items()]


def load_task(task: str):
    """Load another calibration task's checker by path (checkers run with `py -I`)."""
    import importlib.util
    import sys

    name = f"calibration_{task}_check"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / task / "check.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
