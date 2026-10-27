"""Run bounded Python checks and retain exact launch and raw output evidence."""

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("label")
p.add_argument("files", nargs="+")
args = p.parse_args()
root = Path.cwd()
out = Path(__file__).resolve().parent
runtime = "C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe"
command = [
    "C:/Users/a343o/.local/bin/uv.exe",
    "run",
    "--offline",
    "--no-project",
    "--python",
    runtime,
]
for package in (
    "pytest==9.1.1",
    "pyyaml==6.0.3",
    "pydantic==2.13.5",
    "numpy",
    "scipy",
    "networkx",
    "sympy",
    "blake3",
):
    command += ["--with", package]
command += [
    "python",
    "-B",
    "-X",
    "utf8",
    "-m",
    "pytest",
    "-o",
    "addopts=",
    "-o",
    "filterwarnings=",
    *args.files,
    "-q",
    "--basetemp",
    tempfile.mkdtemp(prefix="oewas009-" + args.label + "-"),
]
env = os.environ.copy()
env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
env["PYTHONPATH"] = str(root)
env["CORE_SYMBOL_GAME_HOST"] = str(
    root / "engine/crates_rs/target/debug/core_symbol_game.exe"
)
tracked = (
    "operations/use_cases/cicd/pr_fast_gate.py",
    "adversary/runtime.py",
    "adversary/infrastructure/estates/oewas_native_anti_skill.py",
    "adversary/infrastructure/estates/oeeis_immune.py",
    "adversary/use_cases/anti_skill_predispatch.py",
    "adversary/use_cases/base_swarm/adversary_swarm.py",
    "engine/crates_rs/core_symbol_game/src/anti_skill_host.rs",
    "engine/crates_rs/core_symbol_game/src/protocol.rs",
    "engine/crates_rs/target/debug/core_symbol_game.exe",
)


def pins():
    paths = (*tracked, *(v.split("::")[0] for v in args.files))
    return {
        v: hashlib.sha256((root / v).read_bytes()).hexdigest()
        for v in paths
        if (root / v).is_file()
    }


before = pins()
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
result = subprocess.run(command, capture_output=True, env=env, check=False)
(out / (args.label + ".log")).write_bytes(result.stdout + result.stderr)
(out / (args.label + ".command.json")).write_text(
    json.dumps(
        {
            "command": command,
            "cwd": str(root),
            "started_utc": started,
            "exit_code": result.returncode,
            "source_pins_before": before,
            "source_pins_after": pins(),
            "scope": "named tests only; no provider performance or mathematical certification claim",
            "authority_effect": "None",
        },
        indent=2,
    )
    + "\n",
    newline="\n",
)
print((result.stdout + result.stderr).decode("utf-8", errors="replace")[-4500:])
raise SystemExit(result.returncode)
