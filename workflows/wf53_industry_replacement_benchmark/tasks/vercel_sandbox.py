"""Run one candidate in a throwaway Vercel Sandbox micro-VM.

Each call creates a fresh, non-persistent Firecracker VM with
``networkPolicy: deny-all`` (no outbound traffic at all), uploads the
candidate's working directory, runs ``python3 -I -B driver.py`` under shell
resource limits, streams stdout with the same output cap as the local
backends, and stops the VM in a ``finally`` block. The image is pinned by
digest. The candidate never sees the API token: the token stays in this
host process, and the VM's environment holds only the image's defaults.

Configuration (host side only):

* ``VERCEL_TOKEN``: read from the environment, else from ``PFP_ENV_FILE`` or
  the repository's ``.env`` (git-ignored). Never logged or returned.
* ``PFP_VERCEL_PROJECT``: project id or name; default ``pfp-sandbox``.
* ``PFP_VERCEL_TEAM``: optional team id.
"""
from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request

API = 'https://api.vercel.com'
IMAGE = 'vercel/sandbox/universal@sha256:ba3173060e0732c8103533bff9fe9715995e83a5bb32a67d23fff75edab39f57'
REPO = Path(__file__).resolve().parents[3]
WORKDIR = '/vercel/pfp'
# Shell limits inside the VM: 512 MB address space per process, 32 MB per file, 256 open files.
# RLIMIT_NPROC (128) is set but the VM does not enforce it; a fork bomb is contained by the
# 1-vCPU VM and the time limit instead (tests/test_vercel_sandbox.py).
LIMITS = 'ulimit -v 524288 && ulimit -f 32768 && ulimit -u 128 && ulimit -n 256'
SETUP_SECONDS = 60  # VM create, upload and teardown allowance on top of the candidate's own limit
_OK = False


class VercelError(RuntimeError):
    pass


def _token() -> str | None:
    tok = os.environ.get('VERCEL_TOKEN')
    if tok:
        return tok.strip()
    env = Path(os.environ.get('PFP_ENV_FILE') or REPO / '.env')
    try:
        for line in env.read_text(encoding='utf-8').splitlines():
            if line.startswith('VERCEL_TOKEN='):
                return line.split('=', 1)[1].strip().strip('"').strip("'") or None
    except OSError:
        return None
    return None


def _query() -> str:
    team = os.environ.get('PFP_VERCEL_TEAM')
    return '?' + urllib.parse.urlencode({'teamId': team}) if team else ''


def _request(method: str, path: str, body=None, ctype: str = 'application/json', timeout: float = 60):
    tok = _token()
    if not tok:
        raise VercelError('no_token')
    data = body if isinstance(body, bytes) or body is None else json.dumps(body).encode('utf-8')
    sep = '&' if '?' in path else ''
    q = _query()
    url = API + path + (sep + q[1:] if sep and q else q)
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', 'Bearer ' + tok)
    if data is not None:
        req.add_header('Content-Type', ctype)
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        raise VercelError(f'http_{e.code}') from None
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise VercelError(f'network:{type(e).__name__}') from None


def _json(method: str, path: str, body=None, ctype: str = 'application/json', timeout: float = 60) -> dict:
    with _request(method, path, body, ctype, timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw.strip() else {}


def available() -> bool:
    """True when a token is configured and the sandbox project answers. Cached once true."""
    global _OK
    if _OK:
        return True
    project = os.environ.get('PFP_VERCEL_PROJECT', 'pfp-sandbox')
    try:
        _json('GET', '/v9/projects/' + urllib.parse.quote(project, safe=''), timeout=20)
    except (VercelError, ValueError):
        return False
    _OK = True
    return True


def _tarball(root: Path) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tf:
        for path in sorted(root.iterdir()):
            if path.is_file():
                data = path.read_bytes()
                info = tarfile.TarInfo('pfp/' + path.name)
                info.size, info.mode = len(data), 0o644
                tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _create(timeout: float) -> str:
    body = {'projectId': os.environ.get('PFP_VERCEL_PROJECT', 'pfp-sandbox'), 'image': IMAGE,
            'persistent': False, 'networkPolicy': {'mode': 'deny-all'},
            'resources': {'vcpus': 1, 'memory': 2048}, 'timeout': int((timeout + SETUP_SECONDS) * 1000)}
    delay = 2.0
    for attempt in range(5):
        try:
            return _json('POST', '/v4/sandboxes', body)['session']['id']
        except VercelError as e:
            if str(e) != 'http_429' or attempt == 4:  # 429: concurrency limit, wait for a slot
                raise
            time.sleep(delay)
            delay *= 2
    raise VercelError('unreachable')


def run(root: Path, timeout: float, run_key: bytes, max_output: int) -> dict:
    """Return ``{'stdout': bytes}`` or ``{'error': label}``. Never raises."""
    try:
        sid = _create(timeout)
    except (VercelError, KeyError, ValueError) as e:
        return {'error': f'sandbox_unavailable:{e}'}
    started = time.monotonic()
    try:
        _json('POST', f'/v2/sandboxes/sessions/{sid}/fs/write', _tarball(root), 'application/gzip')
        cmd = _json('POST', f'/v2/sandboxes/sessions/{sid}/cmd', {
            'command': 'bash', 'args': ['-c', f'{LIMITS}; exec python3 -I -B driver.py'],
            'cwd': WORKDIR, 'env': {'PYTHONHASHSEED': '0', 'PYTHONIOENCODING': 'utf-8'},
            'timeout': max(100, int(timeout * 1000)), 'attachStdin': True})
        cid = cmd['command']['id']
        _json('POST', f'/v2/sandboxes/sessions/{sid}/cmd/{cid}/stdin',
              {'data': base64.b64encode(run_key.hex().encode('ascii') + b'\n').decode('ascii'), 'close': True})
        chunks, size = [], 0
        with _request('GET', f'/v2/sandboxes/sessions/{sid}/cmd/{cid}/logs',
                      timeout=timeout + SETUP_SECONDS) as stream:
            for line in stream:
                if time.monotonic() - started > timeout + SETUP_SECONDS:
                    return {'error': 'timeout'}
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get('stream') != 'stdout' or not isinstance(entry.get('data'), str):
                    continue
                block = entry['data'].encode('utf-8', errors='surrogateescape')
                size += len(block)
                if size > max_output:
                    return {'error': 'output_limit'}
                chunks.append(block)
        status = _json('GET', f'/v2/sandboxes/sessions/{sid}/cmd/{cid}?wait=true', timeout=timeout + SETUP_SECONDS)
        code = status.get('command', {}).get('exitCode')
        if code in (137, -9) or code is None:
            elapsed = (status.get('command', {}).get('durationMs') or 0) / 1000
            return {'error': 'timeout' if code is None or elapsed >= timeout else 'killed'}
        return {'stdout': b''.join(chunks), 'exit': code}
    except (VercelError, KeyError, ValueError) as e:
        return {'error': f'sandbox_unavailable:{e}'}
    finally:
        try:
            _json('POST', f'/v2/sandboxes/sessions/{sid}/stop', {}, timeout=30)
        except (VercelError, ValueError):
            pass  # the VM's own timeout stops it regardless
