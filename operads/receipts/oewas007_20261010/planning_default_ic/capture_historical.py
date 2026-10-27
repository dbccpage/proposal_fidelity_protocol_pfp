"""Capture exact small-batch historical-source checks and code custody."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
label = sys.argv[1]
assert not (OUT / (label + ".json")).exists()
prefix = ["C:/Users/a343o/.local/bin/uv.exe", "run", "--offline", "--no-project", "--python",
    "C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe",
    "--with", "pytest==9.1.1", "--with", "pyyaml==6.0.3", "--with", "pydantic==2.13.5", "python", "-X", "utf8"]
if label == "historical_cli":
    argv = prefix + ["-m", "product_planning_office.infrastructure.prior_art_sources"]
else:
    argv = prefix + ["-m", "pytest", "-o", "addopts=", "-o", "filterwarnings=", *sys.argv[2:],
        "--basetemp", str(Path(os.environ["TEMP"]) / (label + "-" + uuid.uuid4().hex)), "-q"]
paths = [
    "product_planning_office/domain/contracts/historical_sources.py",
    "product_planning_office/infrastructure/prior_art_sources.py",
    "product_planning_office/use_cases/prior_art_epic_audit.py",
    "product_planning_office/tests/test_prior_art_historical_sources.py",
    "product_planning_office/tests/test_prior_art_epic_audit.py",
    "operating_system/adapters/intelligence_custody/ic_routing.py",
    "operating_system/adapters/intelligence_custody/ic_migration.py",
    "governance/domain/intelligence_community.py",
    "governance/_types/ic_casefold_v15_1.json",
]
def pins():
    return {rel: {"sha256": hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), "size_bytes": (ROOT / rel).stat().st_size} for rel in paths}
before = pins()
env = os.environ.copy()
env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
start = time.monotonic()
result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=180, check=False)
after = pins()
for stream, raw in (("stdout", result.stdout), ("stderr", result.stderr)):
    (OUT / (label + "." + stream + ".log")).write_bytes(raw)
record = {"authority_effect": "None", "cwd": str(ROOT), "command_argv": argv,
    "environment_overrides": {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1"},
    "exit_code": result.returncode, "elapsed_seconds": round(time.monotonic() - start, 3),
    "source_pins_before": before, "source_pins_after": after, "source_stable_during_command": before == after,
    "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()}
(OUT / (label + ".json")).write_bytes((json.dumps(record, indent=2, sort_keys=True) + "\n").encode())
print(result.stdout.decode("utf-8", errors="replace"), end="")
print(result.stderr.decode("utf-8", errors="replace"), end="", file=sys.stderr)
assert before == after, "Production input changed during command; replay is required"
sys.exit(result.returncode)
