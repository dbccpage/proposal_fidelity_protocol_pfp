"""Escape tests for the Vercel Sandbox backend (a throwaway micro-VM per candidate).

Every attack runs with the in-process audit-hook jail switched off
(``_jail=False``), so a pass shows the VM boundary holds on its own. Skipped
when no Vercel token or sandbox project is configured.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(HERE), str(HERE.parent.parent)]

from tasks import sandbox, vercel_sandbox  # noqa: E402

pytestmark = pytest.mark.skipif(not vercel_sandbox.available(), reason='Vercel token or sandbox project unavailable')


def bare(driver: str, timeout: float = 20) -> dict:
    """Run ``driver`` in a fresh VM with the Python jail off."""
    return sandbox._run_one('', driver, None, timeout, backend='vercel', _jail=False)


def test_honest_run_matches_process_backend():
    driver = 'emit({"x": [1, 2], "s": "ok"})'
    assert bare(driver)['result'] == sandbox._run_one('', driver, None, 10, backend='process')['result']


def test_no_network_even_as_root():
    out = bare('import socket, subprocess\n'
               'res = []\n'
               'for host, port in (("1.1.1.1", 53), ("8.8.8.8", 443), ("huggingface.co", 443)):\n'
               '    try:\n'
               '        socket.create_connection((host, port), timeout=3); res.append("open")\n'
               '    except OSError as e:\n'
               '        res.append(type(e).__name__)\n'
               'root = subprocess.run(["sudo", "-n", "curl", "-s", "-m", "5", "-o", "/dev/null", "-w", "%{http_code}",\n'
               '                       "https://huggingface.co"], capture_output=True, text=True)\n'
               'emit({"res": res, "root_http": root.stdout})', timeout=40)
    r = out['result']
    assert 'open' not in r['res']
    assert r['root_http'] in ('', '000')  # no response, even with root inside the VM


def test_no_host_files_or_secrets(monkeypatch):
    monkeypatch.setenv('PFP_CANARY_SECRET', 'must-not-arrive')
    out = bare('import os\n'
               'emit({"env": sorted(os.environ), "work": sorted(os.listdir(".")),\n'
               '      "win": any(os.path.exists(p) for p in ("/mnt/c", "/c", "/Users", "/host"))})')
    r = out['result']
    assert not r['win']
    assert r['work'] == ['candidate.py', 'driver.py']
    leaked = [k for k in r['env'] if any(w in k.upper() for w in ('TOKEN', 'SECRET', 'API_KEY', 'VERCEL', 'ANTHROPIC'))]
    assert leaked == []


def test_each_run_gets_a_fresh_vm():
    first = bare('open("/tmp/pfp_marker", "w").write("x")\nemit("wrote")')
    second = bare('import os\nemit(os.path.exists("/tmp/pfp_marker"))')
    assert first['result'] == 'wrote' and second['result'] is False


def test_file_size_is_capped():
    out = bare('try:\n'
               '    with open("big", "wb") as f:\n'
               '        for _ in range(64):\n'
               '            f.write(b"x" * 1_048_576)\n'
               '    emit("filled")\n'
               'except OSError as e:\n'
               '    emit(type(e).__name__)')
    assert out.get('result') != 'filled'


def test_fork_bomb_is_contained_to_its_vm():
    # RLIMIT_NPROC is set but not enforced inside the VM, so the process count itself is not
    # capped. What must hold: the bomb stays inside a 1-vCPU VM, the run ends on time, and the
    # next candidate gets a clean VM.
    import time
    t = time.monotonic()
    out = bare('import os\nwhile True:\n    try:\n        os.fork()\n    except OSError:\n        pass', timeout=5)
    assert 'result' not in out
    assert time.monotonic() - t < 5 + vercel_sandbox.SETUP_SECONDS
    assert bare('emit("clean")')['result'] == 'clean'


def test_memory_is_capped():
    out = bare('b = bytearray(1024 * 1024 * 1024)\nemit(len(b))', timeout=20)
    assert 'result' not in out


def test_hang_is_killed():
    out = bare('while True:\n    pass', timeout=3)
    assert out == {'error': 'timeout'}


def test_output_flood_is_cut():
    out = bare('import sys\nwhile True:\n    sys.stdout.write("x" * 65536)', timeout=30)
    assert out == {'error': 'output_limit'}
