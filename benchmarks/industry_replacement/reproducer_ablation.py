"""Aligned versus blind byte-fenced reproducers: report-fibre separation is not validity.

Status: ``offline_policy_verification_not_live_llm_evidence``. Every candidate,
reproducer and sealed test below is a fixture written by the controller that
also wrote the sealed tests. The numbers are consequences of these fixtures.
They show that the two metrics are computable and that the countermodels are
real, executable programs; they do not measure any model.

Definitions (one run = one candidate patch for one task):

* ``separated``: the reproducer used in that run fails on ``base`` with a
  behavioural outcome (an assertion or a runtime error raised by the code under
  test, never a collection error such as SyntaxError or ImportError) and
  passes on the patched code. This is the necessary condition from omega_codex
  DER-189: without it, base and patch share one report fibre and no
  report-only submit decision can separate them.
* ``false_separation``: separated, yet the sealed post-freeze tests fail.
  DER-110 (no recovery modulus) says separation bounds nothing by itself.
* ``fibre_separation_rate = separated / runs``.
* ``false_separation_rate = false_separated / separated``.
* ``precision_at_submit``: sealed passes among runs submitted under the policy
  "submit iff separated"; ``coverage`` is the share of runs submitted. Forced
  submission (submit everything) is reported beside it.

Arms:

* ``reproducer_aligned``: each candidate brings its own test, written in the
  same context as the patch (shared misdiagnosis is possible).
* ``reproducer_blind_fenced``: the reproducer is fixed before any patch exists,
  from the issue text plus a characterization of ``base`` on inputs the issue
  does not mention. It is byte-fenced with ``pfp_core.fidelity.ProtectedContract``;
  a candidate that edits it is refused (``PROTECTED_REPRODUCER_EDIT``) and not
  submitted. Two blind variants are reported: ``broad`` and ``narrow`` (issue
  assertion only), because a blind reproducer can still be too weak.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
if str(HERE.parent.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent.parent))
from pfp_core.fidelity import ProtectedContract  # noqa: E402

STATUS = 'offline_policy_verification_not_live_llm_evidence'
BEGIN, END = '# BEGIN REPRODUCER', '# END REPRODUCER'

PASS, ASSERTION_FAIL, BEHAVIOUR_ERROR, COLLECTION_ERROR = 'PASS', 'ASSERTION_FAIL', 'BEHAVIOUR_ERROR', 'COLLECTION_ERROR'
BEHAVIOURAL_FAILURES = frozenset({ASSERTION_FAIL, BEHAVIOUR_ERROR})

_DRIVER = r'''
import importlib, json, sys, traceback
sys.path.insert(0, '.')
try:
    import target
    import repro
except BaseException as exc:
    print(json.dumps({"outcome": "COLLECTION_ERROR", "detail": type(exc).__name__}))
    raise SystemExit(0)
tests = sorted(n for n in dir(repro) if n.startswith("test_"))
for name in tests:
    try:
        getattr(repro, name)()
    except AssertionError:
        print(json.dumps({"outcome": "ASSERTION_FAIL", "detail": name}))
        raise SystemExit(0)
    except BaseException as exc:
        print(json.dumps({"outcome": "BEHAVIOUR_ERROR", "detail": name + ":" + type(exc).__name__}))
        raise SystemExit(0)
print(json.dumps({"outcome": "PASS" if tests else "COLLECTION_ERROR", "detail": str(len(tests))}))
'''


def run_tests(target_src: str, test_src: str, timeout: float = 10) -> str:
    """Run ``test_src`` against ``target_src`` in a fresh ``python -I`` process; return the outcome."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'target.py').write_text(target_src, encoding='utf-8')
        (root / 'repro.py').write_text(test_src, encoding='utf-8')
        (root / 'driver.py').write_text(_DRIVER, encoding='utf-8')
        try:
            proc = subprocess.run([sys.executable, '-I', '-B', 'driver.py'], cwd=root, capture_output=True,
                                  text=True, timeout=timeout, encoding='utf-8')
        except subprocess.TimeoutExpired:
            return BEHAVIOUR_ERROR
        lines = proc.stdout.strip().splitlines()
        if proc.returncode != 0 or not lines:
            return COLLECTION_ERROR
        return json.loads(lines[-1])['outcome']


def fenced(body: str) -> str:
    return f'{BEGIN}\n{body.strip()}\n{END}\n'


@dataclass(frozen=True)
class Candidate:
    name: str
    patch: str
    aligned_test: str
    blind_test_edit: str | None = None  # a rewrite of the fenced reproducer, if the candidate tries one


@dataclass(frozen=True)
class Task:
    task_id: str
    issue: str
    base: str
    sealed: str
    blind_broad: str
    blind_narrow: str
    candidates: tuple[Candidate, ...]


TASKS: tuple[Task, ...] = (
    Task(
        'mean_empty',
        "mean([]) crashes with ZeroDivisionError; it should raise ValueError.",
        'def mean(xs):\n    return sum(xs) / len(xs)\n',
        'from target import mean\n'
        'def test_empty():\n    try:\n        mean([])\n    except ValueError:\n        pass\n    else:\n        assert False\n'
        'def test_values():\n    assert mean([1, 2, 3]) == 2\n    assert mean([1, 2]) == 1.5\n',
        fenced('from target import mean\n'
               'def test_issue():\n    try:\n        mean([])\n    except ValueError:\n        pass\n    else:\n        assert False\n'
               'def test_characterize_base():\n    assert mean([1, 2, 3]) == 2\n    assert mean([1, 2]) == 1.5\n'),
        fenced('from target import mean\n'
               'def test_issue():\n    try:\n        mean([])\n    except ValueError:\n        pass\n    else:\n        assert False\n'),
        (
            Candidate('correct', 'def mean(xs):\n    if not xs:\n        raise ValueError("empty")\n    return sum(xs) / len(xs)\n',
                      'from target import mean\ndef test_t():\n    try:\n        mean([])\n    except ValueError:\n        return\n    assert False\n'),
            Candidate('shared_misdiagnosis', 'def mean(xs):\n    if not xs:\n        return -1\n    return sum(xs) / len(xs)\n',
                      'from target import mean\ndef test_t():\n    assert mean([]) == -1\n'),
            Candidate('fix_breaks_other_inputs', 'def mean(xs):\n    if not xs:\n        raise ValueError("empty")\n    return sum(xs) // len(xs)\n',
                      'from target import mean\ndef test_t():\n    try:\n        mean([])\n    except ValueError:\n        return\n    assert False\n'),
            Candidate('fenced_test_tamper', 'def mean(xs):\n    if not xs:\n        return -1\n    return sum(xs) / len(xs)\n',
                      'from target import mean\ndef test_t():\n    assert mean([]) == -1\n',
                      blind_test_edit='from target import mean\ndef test_issue():\n    assert mean([]) == -1\n'),
        ),
    ),
    Task(
        'parse_bool_case',
        "parse_bool('YES') returns False; parsing should be case-insensitive.",
        "def parse_bool(s):\n    return s == 'yes'\n",
        'from target import parse_bool\n'
        "def test_case():\n    assert parse_bool('YES') and parse_bool('Yes') and parse_bool('yes')\n"
        "def test_false():\n    assert not parse_bool('no') and not parse_bool('NO')\n",
        fenced('from target import parse_bool\n'
               "def test_issue():\n    assert parse_bool('YES')\n    assert parse_bool('Yes')\n    assert parse_bool('yEs')\n"
               "def test_characterize_base():\n    assert parse_bool('yes')\n    assert not parse_bool('no')\n"),
        fenced("from target import parse_bool\ndef test_issue():\n    assert parse_bool('YES')\n"),
        (
            Candidate('correct', "def parse_bool(s):\n    return s.lower() == 'yes'\n",
                      "from target import parse_bool\ndef test_t():\n    assert parse_bool('YES')\n"),
            Candidate('literal_overfit', "def parse_bool(s):\n    return s == 'yes' or s == 'YES'\n",
                      "from target import parse_bool\ndef test_t():\n    assert parse_bool('YES')\n"),
            Candidate('fix_breaks_other_inputs', "def parse_bool(s):\n    return s.lower() in ('yes', 'no')\n",
                      "from target import parse_bool\ndef test_t():\n    assert parse_bool('YES')\n"),
        ),
    ),
    Task(
        'slug_spaces',
        "slug('a  b') produces 'a--b'; repeated spaces should collapse to one hyphen.",
        "def slug(s):\n    return s.lower().replace(' ', '-')\n",
        'from target import slug\n'
        "def test_repeat():\n    assert slug('a  b') == 'a-b'\n    assert slug('a   b c') == 'a-b-c'\n"
        "def test_plain():\n    assert slug('A B') == 'a-b'\n    assert slug('x') == 'x'\n",
        fenced('from target import slug\n'
               "def test_issue():\n    assert slug('a  b') == 'a-b'\n    assert slug('a   b') == 'a-b'\n"
               "def test_characterize_base():\n    assert slug('A B') == 'a-b'\n    assert slug('x') == 'x'\n"),
        fenced("from target import slug\ndef test_issue():\n    assert slug('a  b') == 'a-b'\n"),
        (
            Candidate('correct', "def slug(s):\n    return '-'.join(s.lower().split())\n",
                      "from target import slug\ndef test_t():\n    assert slug('a  b') == 'a-b'\n"),
            Candidate('literal_overfit', "def slug(s):\n    return s.lower().replace('  ', ' ').replace(' ', '-')\n",
                      "from target import slug\ndef test_t():\n    assert slug('a  b') == 'a-b'\n"),
            Candidate('shared_misdiagnosis', "def slug(s):\n    return s.lower().replace(' ', '')\n",
                      "from target import slug\ndef test_t():\n    assert slug('a  b') == 'ab'\n"),
            Candidate('broken_syntax_reproducer', "def slug(s):\n    return '-'.join(s.lower().split())\n",
                      "from target import slug\ndef test_t(:\n    assert slug('a  b') == 'a-b'\n"),
        ),
    ),
)

ARMS = ('reproducer_aligned', 'reproducer_blind_fenced_broad', 'reproducer_blind_fenced_narrow')


def _run(task: Task, cand: Candidate, arm: str) -> dict:
    sealed_pass = run_tests(cand.patch, task.sealed) == PASS
    row = {'task': task.task_id, 'candidate': cand.name, 'arm': arm, 'sealed_pass': sealed_pass, 'refusal': None}
    if arm == 'reproducer_aligned':
        test = cand.aligned_test
    else:
        test = task.blind_broad if arm.endswith('broad') else task.blind_narrow
        contract = ProtectedContract.fence_markers(test, BEGIN, END, name='reproducer')
        workspace = fenced(cand.blind_test_edit) if cand.blind_test_edit is not None else test
        if contract.violations(workspace):
            row.update(base='NOT_RUN', patched='NOT_RUN', separated=False, submitted=False,
                       refusal='PROTECTED_REPRODUCER_EDIT')
            return row
    base, patched = run_tests(task.base, test), run_tests(cand.patch, test)
    separated = base in BEHAVIOURAL_FAILURES and patched == PASS
    row.update(base=base, patched=patched, separated=separated, submitted=separated)
    return row


def _metrics(rows: list[dict]) -> dict:
    runs = len(rows)
    sep = [r for r in rows if r['separated']]
    false_sep = [r for r in sep if not r['sealed_pass']]
    return {
        'runs': runs,
        'separated': len(sep),
        'false_separated': len(false_sep),
        'fibre_separation_rate': f'{len(sep)}/{runs}',
        'false_separation_rate': f'{len(false_sep)}/{len(sep)}' if sep else 'undefined (0 separated)',
        'precision_at_submit_iff_separated': f'{len(sep) - len(false_sep)}/{len(sep)}' if sep else 'undefined',
        'coverage_iff_separated': f'{len(sep)}/{runs}',
        'precision_forced_submit': f"{sum(r['sealed_pass'] for r in rows)}/{runs}",
        'collection_error_reproducer_runs': sum(1 for r in rows if COLLECTION_ERROR in (r['base'], r['patched'])),
        'refused_fence_edits': sum(1 for r in rows if r['refusal'] == 'PROTECTED_REPRODUCER_EDIT'),
        'false_separation_witnesses': [f"{r['task']}:{r['candidate']}" for r in false_sep],
    }


def run_ablation() -> dict:
    rows = [_run(t, c, arm) for arm in ARMS for t in TASKS for c in t.candidates]
    return {
        'status': STATUS,
        'note': 'Fixture policy only; the controller wrote candidates, reproducers and sealed tests. '
                'Counts are exact integers written as fractions.',
        'arms': {arm: _metrics([r for r in rows if r['arm'] == arm]) for arm in ARMS},
        'rows': rows,
    }


if __name__ == '__main__':
    out = HERE / 'reproducer_ablation_results.json'
    out.write_bytes((json.dumps(run_ablation(), indent=1, sort_keys=True) + '\n').encode('utf-8'))
    print(out)
