"""Escape tests for the container backend.

Every attack here runs with the in-process audit-hook jail switched off
(``_jail=False``), so a pass shows the container boundary holds on its own.
Skipped when Docker or the pinned image is not available locally.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(HERE), str(HERE.parent.parent)]

from tasks import sandbox  # noqa: E402

pytestmark = pytest.mark.skipif(not sandbox.container_available(), reason='Docker or pinned image unavailable')


def bare(driver: str, timeout: float = 20) -> dict:
    """Run ``driver`` in the container with the Python jail off."""
    return sandbox._run_one('', driver, None, timeout, backend='container', _jail=False)


def test_honest_run_matches_process_backend():
    driver = 'emit({"x": [1, 2], "s": "ok"})'
    assert bare(driver)['result'] == sandbox._run_one('', driver, None, 10, backend='process')['result']


def test_no_network():
    out = bare('import socket\n'
               'res = []\n'
               'for host in ("1.1.1.1", "8.8.8.8", "host.docker.internal"):\n'
               '    try:\n'
               '        socket.create_connection((host, 53), timeout=2); res.append("open")\n'
               '    except OSError as e:\n'
               '        res.append(type(e).__name__)\n'
               'ifs = sorted(n for _, n in socket.if_nameindex())\n'
               'emit({"res": res, "ifs": ifs})')
    assert 'open' not in out['result']['res']
    assert out['result']['ifs'] == ['lo']


IMAGE_ENV = {'PATH', 'LANG', 'GPG_KEY', 'PYTHON_VERSION', 'PYTHON_SHA256', 'HOME', 'HOSTNAME',
             'PYTHONHASHSEED', 'PYTHONIOENCODING', 'PWD'}  # PWD: set by sh; GPG_KEY: the image's public release-key id


def test_no_host_files_or_secrets(monkeypatch):
    monkeypatch.setenv('PFP_CANARY_SECRET', 'must-not-arrive')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'must-not-arrive')
    out = bare('import os\n'
               'emit({"mnt": os.path.exists("/mnt/c") or os.path.exists("/mnt/host"),\n'
               '      "users": os.path.exists("/Users") or os.path.exists("/c/Users"),\n'
               '      "sock": os.path.exists("/var/run/docker.sock"),\n'
               '      "env": sorted(os.environ), "uid": os.getuid()})')
    r = out['result']
    assert not r['mnt'] and not r['users'] and not r['sock']
    assert r['uid'] == 65534
    assert set(r['env']) <= IMAGE_ENV


def test_writes_only_to_scratch():
    out = bare('res = {}\n'
               'for path in ("/usr/local/lib/x", "/etc/x", "/src/x", "/work/x"):\n'
               '    try:\n'
               '        open(path, "w").write("x"); res[path] = "wrote"\n'
               '    except OSError as e:\n'
               '        res[path] = type(e).__name__\n'
               'emit(res)')
    r = out['result']
    assert r['/work/x'] == 'wrote'
    assert all(v != 'wrote' for k, v in r.items() if k != '/work/x')


def test_scratch_is_size_capped():
    out = bare('try:\n'
               '    with open("/work/big", "wb") as f:\n'
               '        for _ in range(64):\n'
               '            f.write(b"x" * 1_048_576)\n'
               '    emit("filled")\n'
               'except OSError as e:\n'
               '    emit(type(e).__name__)')
    assert out['result'] != 'filled'


def test_process_count_is_capped():
    out = bare('import os, time\n'
               'n = 0\n'
               'try:\n'
               '    for _ in range(500):\n'
               '        if os.fork() == 0:\n'
               '            time.sleep(30); os._exit(0)\n'
               '        n += 1\n'
               'except OSError:\n'
               '    pass\n'
               'emit(n)', timeout=20)
    assert out['result'] < 64


def test_memory_is_capped():
    out = bare('b = bytearray(1024 * 1024 * 1024)\nemit(len(b))', timeout=20)
    assert 'result' not in out and out['error'] in ('killed', 'authenticated_result_lines=0')


def test_hang_is_killed_and_container_removed():
    out = bare('while True:\n    pass', timeout=2)
    assert out == {'error': 'timeout'}
    left = subprocess.run([sandbox.docker_exe(), 'ps', '-aq', '--filter', 'name=pfp-cand-'],
                          capture_output=True, text=True, timeout=30)
    assert left.stdout.strip() == ''


def test_output_flood_is_cut():
    out = bare('import sys\nwhile True:\n    sys.stdout.write("x" * 65536)', timeout=20)
    assert out == {'error': 'output_limit'}


def test_jail_off_is_refused_on_the_host():
    assert sandbox._run_one('', 'emit(1)', None, 5, backend='process', _jail=False) == \
        {'error': 'jail_required_on_process_backend'}
