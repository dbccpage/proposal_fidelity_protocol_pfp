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

Container backend (``BACKEND = 'container'``, or ``PFP_SANDBOX=container``): the
same jailed process runs inside a throwaway Docker container instead of on the
host. The container has no network, a read-only root filesystem, every Linux
capability dropped, ``no-new-privileges``, an unprivileged user, memory, CPU
and process limits, and only a small tmpfs to write to. The candidate's files
are mounted read-only and copied into that tmpfs. The container is removed
when the run ends, and force-removed on timeout or output flood. The image is
pinned by digest (``CONTAINER_IMAGE``). This is the OS-enforced boundary; the
audit-hook jail stays inside it as a second layer.

What the process backend is not: an operating-system sandbox. An audit-hook jail is
in-process, and native code or interpreter bugs can defeat it; memory is not
capped on Windows. Verdicts never come from this process: sealed scenarios
return observations only, and the parent judges them (see
the sealed grader). Live campaigns never use this backend:
``run_live.require_container_sandbox`` forces the container backend or refuses to start.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from typing import Callable

MAX_OUTPUT_BYTES = 1_000_000
# 'process' runs on the host (offline matrix, tests); 'container' runs in Docker.
BACKEND = os.environ.get('PFP_SANDBOX', 'process')
CONTAINER_IMAGE = 'python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b'  # python:3.12-slim
CONTAINER_LIMITS = {'memory': '256m', 'cpus': '1', 'pids': '64', 'tmpfs': '16m'}
MARKER = '@@RESULT@@'

JAIL = r'''
import json as _json, os as _os, sys as _sys
import _hashlib as _hashlib_c
# Captured before the candidate exists: C functions and bound C methods that candidate code
# cannot rebind for us (it can only rebind module attributes, which we no longer read).
_hmac_digest, _srepr, _dumps = _hashlib_c.hmac_digest, repr, _json.dumps
_stdout_write, _stdout_flush, _stdin_readline = _sys.__stdout__.write, _sys.__stdout__.flush, _sys.stdin.readline
_inf = float('inf')


def _norm_key(k):
    # JSON keys must be strings. A str (or str subclass) keeps its character content; anything
    # else is repr'd. Either way the key becomes a JSON string that dumps escapes, so a hostile
    # __repr__/__str__ can place text only inside one key value, never break the structure.
    return str(k) if isinstance(k, str) else _srepr(k)


def _norm(o, depth=0):
    # Structural, type-exact normalization. Candidate objects reach the result only as JSON
    # scalars/containers or, as a last resort, a repr'd string value -- never as raw body text,
    # so a candidate __repr__ cannot inject or restructure the signed result.
    if depth > 40:
        return {'__truncated__': True}
    t = type(o)
    if o is None or t is bool or t is int or t is str:
        return o
    if t is float:
        return {'__nonfinite__': _srepr(o)} if (o != o or o == _inf or o == -_inf) else o
    if t is list or t is tuple:
        return [_norm(x, depth + 1) for x in o]
    if t is dict:
        return {_norm_key(k): _norm(v, depth + 1) for k, v in o.items()}
    return {'__repr__': _srepr(o)}


def _result_body(obj):
    return _dumps(_norm(obj), ensure_ascii=True, allow_nan=False, separators=(',', ':'))


# Neutralize sys.monitoring (PEP 669, 3.12+): it raises no audit events, so a candidate could
# install a CALL callback and read the per-run key from the hmac call or rewrite the emitted
# object before it is signed. It is not needed by candidate business logic. Deleting it also
# cannot be undone by reload() or _imp (the cached module object has no such attribute again).
try:
    del _sys.monitoring
except AttributeError:
    pass

# Deny ATTACH/VACUUM INTO on every sqlite connection (the audit hook sees sqlite3.connect but
# not later ATTACH, which opens a file in C). Patched before the candidate runs so both the
# driver's and a candidate's :memory: connections carry the authorizer. A candidate that reaches
# the C extension directly still bypasses this -- an in-process limit, which is why live stays off.
try:
    import sqlite3 as _sqlite3_mod
    _sqlite3_orig_connect, _SQLITE_DENY, _SQLITE_OK, _SQLITE_ATTACH = (
        _sqlite3_mod.connect, _sqlite3_mod.SQLITE_DENY, _sqlite3_mod.SQLITE_OK, _sqlite3_mod.SQLITE_ATTACH)

    def _sqlite3_guarded_connect(*a, **k):
        conn = _sqlite3_orig_connect(*a, **k)
        try:
            conn.set_authorizer(lambda action, *_rest: _SQLITE_DENY if action == _SQLITE_ATTACH else _SQLITE_OK)
        except Exception:
            pass
        return conn

    _sqlite3_mod.connect = _sqlite3_guarded_connect
    _sqlite3_mod.dbapi2.connect = _sqlite3_guarded_connect
except Exception:
    pass
_WRITE_FLAGS = 0
for _flag in ('O_WRONLY', 'O_RDWR', 'O_CREAT', 'O_TRUNC', 'O_APPEND', 'O_EXCL', 'O_TEMPORARY'):
    _WRITE_FLAGS |= getattr(_os, _flag, 0)
_ROOT = _os.path.realpath(_os.getcwd())
_READ = [_ROOT] + sorted({_os.path.realpath(p) for p in (_sys.prefix, _sys.base_prefix, _sys.exec_prefix,
                                                        _os.path.dirname(_os.__file__))})
_BLOCKED = ('socket.', 'subprocess.', 'os.system', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.startfile',
            'os.fork', 'os.kill', 'os.putenv', 'os.unsetenv', 'os.chdir', 'os.remove', 'os.rename', 'os.rmdir',
            'os.link', 'os.symlink', 'os.truncate', 'os.chmod', 'os.mkdir', 'os.makedirs', 'os.utime',
            'ctypes.', 'winreg.', '_winapi.', 'gc.get_',
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
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        if isinstance(path, int) or path is None:
            return
        # os.open reports mode=None and carries write intent in its integer flags.
        writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or bool(flags & _WRITE_FLAGS)
        # The open event carries no dir_fd. A relative write path with dir_fd set resolves against
        # that descriptor, not the cwd, so _inside(path, [_ROOT]) would pass while the write lands
        # elsewhere. Writes must be absolute paths inside _ROOT; relative reads stay allowed.
        if writing:
            try:
                absolute = _os.path.isabs(_os.fspath(path))
            except (TypeError, ValueError):
                absolute = False
            if not absolute:
                raise PermissionError('jail: relative write')
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
'''

# The driver body runs inside this function. The per-run key arrives on stdin before the
# candidate is imported and lives only in this frame and in the local ``emit`` closure, which
# is never handed to candidate code; frame and closure introspection are refused by the jail.
MAIN_HEAD = '''
def __pfp_main(__pfp_key, __pfp_hd=_hmac_digest, __pfp_body=_result_body, __pfp_w=_stdout_write, __pfp_f=_stdout_flush):
    def emit(obj):
        body = __pfp_body(obj)
        __pfp_w('@@RESULT@@' + __pfp_hd(__pfp_key, body.encode('utf-8'), 'sha256').hex() + ' ' + body + '\\n')
        __pfp_f()
'''
MAIN_TAIL = '''
__pfp_main(bytes.fromhex(_stdin_readline().strip()))
'''

_RESULTS: dict[str, dict] = {}


def _key(code: str, driver: str, extra_files: dict | None, timeout: float) -> str:
    raw = json.dumps([code, driver, sorted((extra_files or {}).items()), timeout, BACKEND]).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _script(driver: str) -> str:
    import textwrap
    return JAIL + MAIN_HEAD + textwrap.indent(driver, '    ') + '\n' + MAIN_TAIL


def _env() -> dict:
    env = {'PYTHONHASHSEED': '0', 'PYTHONIOENCODING': 'utf-8'}
    if os.name == 'nt':
        env['SYSTEMROOT'] = os.environ.get('SYSTEMROOT', r'C:\Windows')
    return env


def docker_exe() -> str | None:
    import shutil
    found = shutil.which('docker')
    if found:
        return found
    default = Path(r'C:\Program Files\Docker\Docker\resources\bin\docker.exe')
    return str(default) if default.exists() else None


_CONTAINER_OK = False


def container_available() -> bool:
    """True when Docker answers and the pinned image is present locally (nothing is pulled)."""
    global _CONTAINER_OK
    if _CONTAINER_OK:
        return True
    exe = docker_exe()
    if exe is None:
        return False
    try:
        r = subprocess.run([exe, 'image', 'inspect', CONTAINER_IMAGE, '--format', '{{.Id}}'],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return False
    _CONTAINER_OK = r.returncode == 0
    return _CONTAINER_OK


def _container_cmd(root: Path, name: str, timeout: float) -> list[str]:
    lim = CONTAINER_LIMITS
    return [docker_exe(), 'run', '--rm', '-i', '--name', name,
            '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--user', '65534:65534',
            '--memory', lim['memory'], '--memory-swap', lim['memory'], '--cpus', lim['cpus'],
            '--pids-limit', lim['pids'], '--ulimit', 'nofile=256:256',
            '--tmpfs', f"/work:rw,size={lim['tmpfs']},mode=1777", '--tmpfs', '/tmp:rw,size=4m,mode=1777',
            '-v', f'{root}:/src:ro', '-w', '/work', '--env', 'PYTHONHASHSEED=0',
            '--env', 'PYTHONIOENCODING=utf-8', '--pull', 'never', '--log-driver', 'none',
            '--entrypoint', '/bin/sh', CONTAINER_IMAGE,
            '-c', f'cp -r /src/. /work/ && exec timeout -s KILL {timeout:g} python -I -B driver.py']


def _remove_container(name: str) -> None:
    try:
        subprocess.run([docker_exe(), 'rm', '-f', name], capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        pass


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


def _run_one(code: str, driver: str, extra_files: dict | None, timeout: float,
             extra_read_roots: tuple[str, ...] = (), backend: str | None = None,
             _jail: bool = True) -> dict:
    """``_jail=False`` exists for the container escape tests only: it proves the OS boundary
    holds with the in-process jail switched off. It is refused on the process backend."""
    backend = backend or BACKEND
    if backend not in ('process', 'container', 'vercel'):
        return {'error': f'unknown_backend:{backend}'}
    if not _jail and backend == 'process':
        return {'error': 'jail_required_on_process_backend'}
    with tempfile.TemporaryDirectory() as tmp:
        return _run_in(Path(tmp), code, driver, extra_files, timeout, extra_read_roots, backend, _jail)


def _run_in(root: Path, code: str, driver: str, extra_files: dict | None, timeout: float,
            extra_read_roots: tuple[str, ...], backend: str, jail: bool) -> dict:
    (root / 'candidate.py').write_text(code, encoding='utf-8')
    script = _script(driver)
    if extra_read_roots:  # tests only: a synthetic read-allowed root
        script = script.replace('_sys.addaudithook(_hook)', '_READ.extend(%r)\n_sys.addaudithook(_hook)'
                                % [os.path.realpath(r) for r in extra_read_roots], 1)
    if not jail:
        assert script.count('_sys.addaudithook(_hook)') == 1
        script = script.replace('_sys.addaudithook(_hook)', 'pass  # jail off: container escape test', 1)
    (root / 'driver.py').write_text(script, encoding='utf-8')
    run_key = os.urandom(32)
    for name, body in (extra_files or {}).items():
        (root / name).write_text(body, encoding='utf-8')
    if backend == 'vercel':
        if extra_read_roots:
            return {'error': 'extra_read_roots_not_supported_in_vercel'}
        from tasks import vercel_sandbox
        ran = vercel_sandbox.run(root, timeout, run_key, MAX_OUTPUT_BYTES)
    else:
        ran = _exec_local(root, timeout, run_key, backend, extra_read_roots)
    if 'error' in ran:
        return ran
    # Candidate stdout is untrusted and need not be UTF-8 (under ``-I`` on Windows it is the
    # locale code page). Undecodable bytes become U+FFFD; such a line can never carry a valid
    # tag, so it is counted as forged instead of discarding the authentic result.
    text = ran['stdout'].decode('utf-8', errors='replace')
    authentic, forged = [], 0
    for line in text.splitlines():
        if not line.startswith(MARKER):
            continue
        tag, _, body = line[len(MARKER):].partition(' ')
        # Reject a non-hex tag before compare_digest, which raises TypeError on a non-ASCII
        # character. A candidate line can therefore never crash the reader; it is only counted.
        if len(tag) != 64 or any(c not in '0123456789abcdef' for c in tag):
            forged += 1
            continue
        expected = hmac.new(run_key, body.encode('utf-8'), 'sha256').hexdigest()
        if hmac.compare_digest(tag, expected):
            authentic.append(body)
        else:
            forged += 1  # written by candidate code without the run key: never a result
    if len(authentic) != 1:
        return {'error': f'authenticated_result_lines={len(authentic)}', 'forged_lines': forged}
    # The body is structural JSON built by the trusted emit from a type-exact normalization,
    # so parsing it cannot run candidate code and cannot raise on an unhashable key or a
    # non-literal value the old repr/literal_eval channel choked on.
    try:
        value = json.loads(authentic[0])
    except (ValueError, RecursionError):
        return {'error': 'result_not_json', 'forged_lines': forged}
    out = {'result': value, 'observation_source': 'candidate_process', 'backend': backend}
    if forged:
        out['forged_lines'] = forged
    return out


def _exec_local(root: Path, timeout: float, run_key: bytes, backend: str,
                extra_read_roots: tuple[str, ...]) -> dict:
    """Run driver.py on the host or in Docker. ``{'stdout': bytes}`` or ``{'error': label}``."""
    kwargs = {'start_new_session': True} if os.name != 'nt' else {
        'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
    container = None
    if backend == 'container':
        if extra_read_roots:
            return {'error': 'extra_read_roots_not_supported_in_container'}
        if not container_available():
            return {'error': 'container_unavailable'}
        container = 'pfp-cand-' + os.urandom(8).hex()
        # The candidate is killed inside the container at ``timeout``; the host allows extra
        # time only for container start and teardown, then force-removes it.
        argv, env, cwd = _container_cmd(root, container, timeout), None, None
        host_timeout = timeout + 15
    else:
        argv, env, cwd = [sys.executable, '-I', '-B', 'driver.py'], _env(), root
        host_timeout = timeout
    started = time.monotonic()
    proc = subprocess.Popen(argv, cwd=cwd, env=env,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            **kwargs)
    try:
        proc.stdin.write(run_key.hex().encode('ascii') + b'\n')
        proc.stdin.close()
    except OSError:
        pass
    chunks, size, flooded = [], 0, threading.Event()

    def read():
        nonlocal size
        for block in iter(lambda: proc.stdout.read(65536), b''):
            size += len(block)
            if size > MAX_OUTPUT_BYTES:
                flooded.set()
                if container:
                    _remove_container(container)
                _kill_tree(proc)
                return
            chunks.append(block)
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        proc.wait(timeout=host_timeout)
    except subprocess.TimeoutExpired:
        if container:
            _remove_container(container)
        _kill_tree(proc)
        reader.join(5)
        return {'error': 'timeout'}
    reader.join(5)
    proc.stdout.close()
    if container and proc.returncode == 137 and not flooded.is_set():
        # SIGKILL: the in-container time limit, or the kernel's memory cap.
        return {'error': 'timeout' if time.monotonic() - started >= timeout else 'killed'}
    if flooded.is_set():
        return {'error': 'output_limit'}
    return {'stdout': b''.join(chunks)}


def run_isolated(code: str, driver: str, extra_files: dict[str, str] | None = None, timeout: float = 10,
                 validate: Callable[[object], bool] | None = None) -> dict:
    """Run ``driver`` against ``code`` in a fresh jailed process.

    Returns ``{'result': value}`` when exactly one result line parsed and
    ``validate(value)`` holds, else ``{'error': label}``. Never raises for
    candidate behaviour. Results are cached by content.
    """
    key = _key(code, driver, extra_files, timeout)
    out = _RESULTS.get(key)
    if out is None:
        out = _run_one(code, driver, extra_files, timeout)
        if out.get('error') != 'timeout':  # a timeout says nothing about a longer run
            _RESULTS[key] = out
    if 'result' in out and validate is not None:
        try:
            ok = bool(validate(out['result']))
        except Exception:
            ok = False
        if not ok:
            return {'error': 'result_schema'}
    return out


def prewarm(codes: list[str], driver: str, extra_files: dict[str, str] | None = None, workers: int = 8,
            timeout: float = 10) -> None:
    """Fill the cache with independent processes run in parallel (one candidate per process)."""
    todo = sorted({c for c in codes if _key(c, driver, extra_files, timeout) not in _RESULTS})
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for code, out in zip(todo, pool.map(lambda c: _run_one(c, driver, extra_files, timeout), todo)):
            if out.get('error') != 'timeout':
                _RESULTS[_key(code, driver, extra_files, timeout)] = out


def clear_cache() -> None:
    _RESULTS.clear()
