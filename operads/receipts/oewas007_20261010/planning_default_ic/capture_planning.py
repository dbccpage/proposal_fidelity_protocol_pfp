"""Capture a bounded planning command and exact output bytes."""
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
UV = "C:/Users/a343o/.local/bin/uv.exe"
PYTHON = "C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe"
PREFIX = [UV, "run", "--offline", "--no-project", "--python", PYTHON,
          "--with", "pytest==9.1.1", "--with", "pyyaml==6.0.3", "--with", "pydantic==2.13.5", "python", "-X", "utf8"]
label = sys.argv[1]
assert not (OUT / (label + ".json")).exists(), "Do not overwrite evidence"
if label.startswith("manifest_write"):
    argv = PREFIX + ["-m", "product_planning_office.use_cases.epic_manifest_audit", "--write"]
elif label in {"red", "green"}:
    argv = PREFIX + ["-m", "pytest", "-o", "addopts=", "-o", "filterwarnings=",
        *( [
            "product_planning_office/tests/test_epic_tdd_plan_audit.py::test_shipped_walk_covers_every_reviewed_epic",
            "product_planning_office/tests/test_prior_art_epic_audit.py::test_current_map_resolves_all_declared_systems",
            "product_planning_office/tests/test_epic_manifest_audit.py::test_the_shipped_manifest_audits_clean",
        ] if label == "red" else [
            "product_planning_office/tests/test_epic_tdd_plan_audit.py",
            "product_planning_office/tests/test_prior_art_epic_audit.py",
            "product_planning_office/tests/test_epic_manifest_audit.py",
        ] ),
        "--basetemp", str(Path(os.environ["TEMP"]) / ("oewas007-default-ic-" + label + "-" + uuid.uuid4().hex)), "-q"]
elif label == "versions":
    argv = PREFIX + ["-c", "import sys,pytest,yaml,pydantic; print(sys.version); print('pytest='+pytest.__version__); print('pyyaml='+yaml.__version__); print('pydantic='+pydantic.__version__)"]
else:
    raise ValueError(label)
env = os.environ.copy()
overrides = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1"}
env.update(overrides)
start = time.monotonic()
result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=180, check=False)
(OUT / (label + ".stdout.log")).write_bytes(result.stdout)
(OUT / (label + ".stderr.log")).write_bytes(result.stderr)
relpaths = [p.relative_to(ROOT).as_posix() for p in (ROOT / "product_planning_office/plans/epics").rglob("epic_*.md")]
relpaths += ["product_planning_office/use_cases/epic_tdd_plan_audit.py", "product_planning_office/use_cases/prior_art_epic_audit.py", "product_planning_office/use_cases/epic_manifest_audit.py"]
relpaths += [p.relative_to(ROOT).as_posix() for p in (ROOT / "product_planning_office/receipts").glob("*oewas007*successor.json")]
relpaths += [p.relative_to(ROOT).as_posix() for p in (ROOT / "product_planning_office").rglob("epic_manifest*.json")]
relpaths += ["product_planning_office/tests/test_epic_tdd_plan_audit.py", "product_planning_office/tests/test_prior_art_epic_audit.py", "product_planning_office/tests/test_epic_manifest_audit.py", "product_planning_office/plans/decisions/adr_20261010_oewas_intelligence_migration.md", "workflows_agents_skills/documentation/intelligence_migration_v1.md"]
pins = {rel:{"sha256":hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(), "size_bytes":(ROOT/rel).stat().st_size} for rel in sorted(set(relpaths))}
record = {"schema":"oewas007.planning.command.v1", "authority_effect":"None", "base_sha":"4d207641277ef3d3af16e11aafb411ada1ee10ed", "cwd":str(ROOT), "command_argv":argv, "environment_overrides":overrides, "exit_code":result.returncode, "elapsed_seconds":round(time.monotonic()-start,3), "pins":pins, "stdout_sha256":hashlib.sha256(result.stdout).hexdigest(), "stderr_sha256":hashlib.sha256(result.stderr).hexdigest()}
(OUT / (label + ".json")).write_bytes((json.dumps(record,indent=2,sort_keys=True)+"\n").encode())
print(result.stdout.decode("utf-8",errors="replace"),end="")
print(result.stderr.decode("utf-8",errors="replace"),end="",file=sys.stderr)
print("Captured exit",result.returncode)
sys.exit(result.returncode)
