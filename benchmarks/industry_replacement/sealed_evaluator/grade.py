"""Post-freeze sealed grading. Imported only by the harness after deliveries freeze.

Each task's sealed tests run in an isolated process against the delivered
code. A refusal (no delivery) scores zero delivered points; it is reported
separately from a delivered wrong answer.
"""
from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from tasks.common import extract_code, run_isolated  # noqa: E402

SEALED = {
    't1_api_refactor_under_contract': 't1_sealed.py',
    't2_sql_security_and_analytics_migration': 't2_sealed.py',
    't3_bloated_skill_repository_triage': 't3_sealed.py',
    't4_stateful_protocol_synthesis': 't4_sealed.py',
}

DRIVER = '''
import json, sys, traceback
sys.path.insert(0, '.')
try:
    import sealed_tests
except BaseException as exc:
    print(json.dumps({"passed": 0, "total": -1, "error": "import failed: " + type(exc).__name__}))
    raise SystemExit(0)
names = sorted(n for n in dir(sealed_tests) if n.startswith("test_"))
failed = []
for n in names:
    try:
        getattr(sealed_tests, n)()
    except BaseException as exc:
        failed.append(n)
print(json.dumps({"passed": len(names) - len(failed), "total": len(names), "failed": failed}))
'''


def sealed_path(task_id: str) -> Path:
    return HERE / SEALED[task_id]


def grade(task_id: str, delivered_text: str | None) -> dict:
    if delivered_text is None:
        return {'delivered': False, 'correct': False, 'passed': 0, 'total': None}
    code = extract_code(delivered_text)
    tests = sealed_path(task_id).read_text(encoding='utf-8')
    result = run_isolated(code, DRIVER, {'sealed_tests.py': tests}, timeout=20)
    total = result.get('total')
    correct = bool(total and total > 0 and result.get('passed') == total)
    return {'delivered': True, 'correct': correct, 'passed': result.get('passed', 0), 'total': total,
            'failed': result.get('failed', [result.get('error', 'unknown')])}


def prewarm_offline(task_id: str, texts: list[str]) -> None:
    """Batch-grade trusted offline fixtures in one process (cache warm-up only)."""
    from tasks.common import prewarm
    tests = sealed_path(task_id).read_text(encoding='utf-8')
    prewarm([extract_code(t) for t in texts], DRIVER, {'sealed_tests.py': tests})
