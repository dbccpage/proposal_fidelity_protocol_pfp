"""Judge-set hygiene for C022 (2026-09-29 correction).

Counterexamples removed by the correction: c022_base_12 repeated c022_base_04.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

_JUDGE = importlib.import_module(
    "omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.judge_packet"
)
JUDGE_DIR = Path(list(_JUDGE.__path__)[0])
PACKAGE_DIR = JUDGE_DIR.parent
META_KEYS = {"id", "case_id", "description"}
KEY_ORDER_CONTROLS: list[
    str
] = []  # identical once parsed; kept on purpose (they test key order in prompts)


def _input(data: object) -> object:
    if (
        isinstance(data, dict)
        and "input" in data
        and ("expected_output" in data or set(data) == {"input"})
    ):
        data = data["input"]
    if isinstance(data, dict):
        data = {k: v for k, v in data.items() if k not in META_KEYS}
    return data


def _key(path: Path) -> str:
    return json.dumps(_input(json.loads(path.read_text(encoding="utf-8"))), sort_keys=True)


def _judge_cases() -> list[Path]:
    cases = sorted((JUDGE_DIR / "cases").rglob("*.json"))
    assert len(cases) >= 40
    return cases


def test_judge_cases_are_pairwise_distinct() -> None:
    seen: dict[str, str] = {}
    duplicates = []
    for path in _judge_cases():
        if path.name in KEY_ORDER_CONTROLS:
            continue
        key = _key(path)
        if key in seen:
            duplicates.append((path.name, seen[key]))
        seen.setdefault(key, path.name)
    assert duplicates == []
