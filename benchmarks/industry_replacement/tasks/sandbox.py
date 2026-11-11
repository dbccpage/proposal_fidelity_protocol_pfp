"""Candidate execution boundary for public checks and sealed scenarios.

Every candidate runs in a fresh ``python -I -B`` process in its own temporary
directory, one candidate per process (no shared interpreter, no bytecode
cache). The process gets:

* a scrubbed environment (only what the interpreter needs to start; no
  provider keys or user variables);
* an audit-hook jail installed before the candidate is imported. It refuses
  file writes outside the working directory, reads outside the working
  directory and the Python installation, sockets, process creation, ctypes,
  registry access, frame and garbage-collector introspection, and SQLite
  databases other than ``:memory:``;
* an output cap (the reader kills the process tree past ``MAX_OUTPUT_BYTES``)
  and a wall-clock timeout that kills the process tree;
* a result channel: exactly one ``@@RESULT@@`` line, parsed as JSON and
  checked against the caller's schema. Anything else is a typed failure.

What this is not: an operating-system sandbox. An audit-hook jail is
in-process, and native code or interpreter bugs can defeat it; memory is not
capped on Windows. Verdicts never come from this process: sealed scenarios
return observations only, and the parent judges them (see
the sealed grader). Live campaigns stay disabled until candidate
execution moves to an OS-enforced sandbox (``run_live.LIVE_EXECUTION_ENABLED``).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from typing import Callable

MAX_OUTPUT_BYTES = 1_000_000
MARKER = '@@RESULT@@'

JAIL = r'''
import json as _json, os as _os, sys as _sys
_ROOT = _os.path.realpath(_os.getcwd())
_READ = [_ROOT] + sorted({_os.path.realpath(p) for p in (_sys.prefix, _sys.base_prefix, _sys.exec_prefix,
                                                        _os.path.dirname(_os.__file__))})
_BLOCKED = ('socket.', 'subprocess.', 'os.system', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.startfile',
            'os.fork', 'os.kill', 'os.putenv', 'os.unsetenv', 'os.chdir', 'os.remove', 'os.rename', 'os.rmdir',
            'os.link', 'os.symlink', 'os.truncate', 'os.chmod', 'ctypes.', 'winreg.', '_winapi.', 'gc.get_',
            'sys._current_frames', 'sys.settrace', 'sys.setprofile', 'sqlite3.enable_load',
            'sqlite3.load_extension', 'cpython.run_', 'urllib.', 'http.', 'webbrowser.', 'shutil.')
_DENIED_MODULES = {'ctypes', '_ctypes', 'socket', '_socket', 'subprocess', '_posixsubprocess', 'multiprocessing',
                   'winreg', '_winapi', 'msvcrt', 'pty', 'signal', 'faulthandler'}
_FRAMES = {'tb_frame', 'gi_frame', 'cr_frame', 'ag_frame', 'f_back', 'f_locals', 'f_globals', '__code__'}


def _inside(path, roots):
    try:
        real = _os.path.realpath(_os.fspath(path))
    except (TypeError, ValueError):
        return False
    return any(real == r or real.startswith(r + _os.sep) for r in roots)


def _hook(event, args):
    if event == 'open':
        path, mode = args[0], args[1]
        if isinstance(path, int) or path is None:
            return
        writing = mode is not None and any(c in str(mode) for c in 'wax+')
        if not _inside(path, [_ROOT] if writing else _READ):
            raise PermissionError('jail: ' + event)
    elif event in ('os.listdir', 'os.scandir') and args and args[0] is not None:
        if not _inside(args[0], _READ):
            raise PermissionError('jail: ' + event)
    elif event == 'import' and args[0].split('.')[0] in _DENIED_MODULES:
        raise ImportError('jail: import ' + args[0])
    elif event == 'object.__getattr__' and len(args) > 1 and args[1] in _FRAMES:
        raise PermissionError('jail: introspection')
    elif event == 'sys._getframe':  # sys._getframemodulename (used by namedtuple) stays allowed
        raise PermissionError('jail: introspection')
    elif event == 'sqlite3.connect' and args and str(args[0]) != ':memory:':
        raise PermissionError('jail: sqlite file')
    elif event.startswith(_BLOCKED):
        raise PermissionError('jail: ' + event)


_sys.addaudithook(_hook)
_sys.path.insert(0, _ROOT)
_write = _sys.__stdout__.write


def emit(obj):
    _write('@@RESULT@@' + _json.dumps(obj, default=repr) + '\n')
    _sys.__stdout__.flush()
'''

_RESULTS: dict[str, dict] = {}


def _key(code: str, driver: str, extra_files: dict | None) -> str:
    raw = json.dumps([code, driver, sorted((extra_files or {}).items())]).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _env() -> dict:
    env = {'PYTHONHASHSEED': '0', 'PYTHONIOENCODING': 'utf-8'}
    if os.name == 'nt':
        env['SYSTEMROOT'] = os.environ.get('SYSTEMROOT', r'C:\Windows')
    return env


def _kill_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)], capture_output=True)
    else:
        try:
            os.killpg(proc.pid, 9)
        except OSError:
            proc.kill()
    proc.wait()


def _run_one(code: str, driver: str, extra_files: dict | None, timeout: float) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'candidate.py').write_text(code, encoding='utf-8')
        (root / 'driver.py').write_text(JAIL + '\n' + driver, encoding='utf-8')
        for name, body in (extra_files or {}).items():
            (root / name).write_text(body, encoding='utf-8')
        kwargs = {'start_new_session': True} if os.name != 'nt' else {
            'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
        proc = subprocess.Popen([sys.executable, '-I', '-B', 'driver.py'], cwd=root, env=_env(),
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                **kwargs)
        chunks, size, flooded = [], 0, threading.Event()

        def read():
            nonlocal size
            for block in iter(lambda: proc.stdout.read(65536), b''):
                size += len(block)
                if size > MAX_OUTPUT_BYTES:
                    flooded.set()
                    _kill_tree(proc)
                    return
                chunks.append(block)
        reader = threading.Thread(target=read, daemon=True)
        reader.start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            reader.join(5)
            return {'error': 'timeout'}
        reader.join(5)
        proc.stdout.close()
        if flooded.is_set():
            return {'error': 'output_limit'}
        try:
            text = b''.join(chunks).decode('utf-8')
        except UnicodeDecodeError:
            return {'error': 'output_not_utf8'}
        lines = [line[len(MARKER):] for line in text.splitlines() if line.startswith(MARKER)]
        if len(lines) != 1:
            return {'error': f'result_lines={len(lines)}'}  # none, or a forged second result
        try:
            return {'result': json.loads(lines[0])}
        except json.JSONDecodeError:
            return {'error': 'result_not_json'}


def run_isolated(code: str, driver: str, extra_files: dict[str, str] | None = None, timeout: float = 10,
                 validate: Callable[[object], bool] | None = None) -> dict:
    """Run ``driver`` against ``code`` in a fresh jailed process.

    Returns ``{'result': value}`` when exactly one result line parsed and
    ``validate(value)`` holds, else ``{'error': label}``. Never raises for
    candidate behaviour. Results are cached by content.
    """
    key = _key(code, driver, extra_files)
    if key not in _RESULTS:
        _RESULTS[key] = _run_one(code, driver, extra_files, timeout)
    out = _RESULTS[key]
    if 'result' in out and validate is not None:
        try:
            ok = bool(validate(out['result']))
        except Exception:
            ok = False
        if not ok:
            return {'error': 'result_schema'}
    return out


def prewarm(codes: list[str], driver: str, extra_files: dict[str, str] | None = None, workers: int = 8) -> None:
    """Fill the cache with independent processes run in parallel (one candidate per process)."""
    todo = sorted({c for c in codes if _key(c, driver, extra_files) not in _RESULTS})
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for code, out in zip(todo, pool.map(lambda c: _run_one(c, driver, extra_files, 10), todo)):
            _RESULTS[_key(code, driver, extra_files)] = out


def clear_cache() -> None:
    _RESULTS.clear()
