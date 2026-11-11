"""Shared public helpers: code extraction and isolated execution.

Nothing here reads the sealed evaluator. Candidate code always runs in a
separate ``python -I`` process with a timeout; it is never imported into the
host process.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

_FENCE = re.compile(r'```(?:python|py)?[ \t]*\n(.*?)```', re.S)


def extract_code(text: str) -> str:
    """Public normalizer: the longest fenced Python block, else the whole text."""
    blocks = _FENCE.findall(text)
    return max(blocks, key=len) if blocks else text


def parses(code: str) -> str | None:
    """None when ``code`` parses, else a short error label."""
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return f'SyntaxError line {exc.lineno}'
    return None


def signatures(code: str, names: tuple[str, ...]) -> dict[str, str]:
    """``name -> ast.dump(arguments, returns)`` for top-level functions in ``names``."""
    out = {}
    for node in ast.parse(code).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            out[node.name] = ast.dump(node.args) + '->' + (ast.dump(node.returns) if node.returns else '')
    return out


_RESULTS: dict[str, dict] = {}


def _key(code: str, driver: str, extra_files: dict | None) -> str:
    raw = json.dumps([code, driver, sorted((extra_files or {}).items())]).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def run_isolated(code: str, driver: str, extra_files: dict[str, str] | None = None, timeout: float = 10) -> dict:
    """Write ``candidate.py`` and ``driver.py`` into a temp dir, run the driver in its own process.

    The driver must print one JSON object on its last stdout line. Results are
    cached by content, since the driver is a pure function of its files.
    """
    key = _key(code, driver, extra_files)
    if key not in _RESULTS:
        _RESULTS[key] = _run_one(code, driver, extra_files, timeout)
    return _RESULTS[key]


_BATCH = '''
import contextlib, importlib, io, json, os, runpy, shutil, sys
sys.path.insert(0, '.')
results = []
for name in json.loads(open('batch.json', encoding='utf-8').read()):
    shutil.copyfile(name, 'candidate.py')
    for mod in ('candidate', 'sealed_tests'):
        sys.modules.pop(mod, None)
    importlib.invalidate_caches()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_path('driver.py', run_name='__main__')
    except SystemExit:
        pass
    except BaseException as exc:
        results.append({'error': 'driver failed: ' + type(exc).__name__})
        continue
    lines = buf.getvalue().strip().splitlines()
    results.append(json.loads(lines[-1]) if lines else {'error': 'no output'})
print(json.dumps(results))
'''


def prewarm(codes: list[str], driver: str, extra_files: dict[str, str] | None = None, timeout: float = 60) -> None:
    """Offline speed-up for trusted fixtures: run many candidates in one process, fill the cache.

    Candidates share one interpreter here, so this is used only for the
    repository's own fixtures; any failure falls back to one process each.
    """
    todo = sorted({c for c in codes if _key(c, driver, extra_files) not in _RESULTS})
    if not todo:
        return
    files = {f'cand_{i}.py': c for i, c in enumerate(todo)}
    files.update(extra_files or {})
    files['batch.json'] = json.dumps([f'cand_{i}.py' for i in range(len(todo))])
    files['driver.py'] = driver
    out = _run_one('', _BATCH, files, timeout, driver_name='batch_driver.py')
    if isinstance(out, list) and len(out) == len(todo):
        for code, result in zip(todo, out):
            _RESULTS[_key(code, driver, extra_files)] = result


def _run_one(code: str, driver: str, extra_files: dict | None, timeout: float, driver_name: str = 'driver.py'):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'candidate.py').write_text(code, encoding='utf-8')
        (root / driver_name).write_text(driver, encoding='utf-8')
        for name, body in (extra_files or {}).items():
            (root / name).write_text(body, encoding='utf-8')
        try:
            proc = subprocess.run([sys.executable, '-I', driver_name], cwd=root, capture_output=True,
                                  text=True, timeout=timeout, encoding='utf-8')
        except subprocess.TimeoutExpired:
            return {'error': 'timeout'}
        lines = proc.stdout.strip().splitlines()
        if proc.returncode != 0 or not lines:
            return {'error': (proc.stderr.strip().splitlines() or ['no output'])[-1][:200]}
        return json.loads(lines[-1])


SMOKE_DRIVER_HEAD = '''
import json, sys
sys.path.insert(0, '.')
try:
    import candidate
except BaseException as exc:
    print(json.dumps({"error": "import failed: " + type(exc).__name__}))
    raise SystemExit(0)
'''
