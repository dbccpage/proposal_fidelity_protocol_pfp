"""Capture final static checks for the root-owned implementation and CI prerequisite."""
import hashlib
import json
import subprocess
from pathlib import Path

root = Path.cwd()
out = Path(__file__).resolve().parent
runtime = "C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe"
prefix = ["C:/Users/a343o/.local/bin/uv.exe", "run", "--offline", "--no-project", "--python", runtime, "--with", "ruff==0.16.10", "python", "-m", "ruff"]
files = [
    "omega_engine_operations/use_cases/cicd/pr_fast_gate.py",
    "omega_engine_operations/tests/cicd/test_pr_fast_gate_receipt_selection.py",
    "omega_engine_woland/infrastructure/estates/oewas_native_anti_skill.py",
    "omega_engine_woland/tests/spine/test_native_anti_skill_ingress.py",
    "omega_engine_woland/tests/spine/test_cross_engine_task_binding.py",
    "omega_engine_woland/tests/spine/test_native_cross_engine_pipeline.py",
    "omega_engine_woland/tests/test_oewas_signed_ingress.py",
    *(p.relative_to(root).as_posix() for p in out.glob("*.py")),
]
workflow = root / ".github/workflows/pr-fast.yml"
text = workflow.read_text()
start = text.index("          if python -c")
end = text.index("\n      - name: Fast gate", start)
shell = out / "native_host_ci_check.sh"
shell.write_text("\n".join(v[10:] for v in text[start:end].splitlines()) + "\n", encoding="utf-8", newline="\n")
commands = [
    ("ruff_version", prefix + ["--version"]),
    ("python_lint", prefix + ["check", "--select", "F401,F841,I001", *files]),
    ("native_adapter_complexity", prefix + ["check", "--select", "C901", "--config", "lint.mccabe.max-complexity=10", "omega_engine_woland/infrastructure/estates/oewas_native_anti_skill.py"]),
    ("workflow_shell", ["C:/Program Files/Git/bin/bash.exe", "-n", str(shell)]),
]
records = []
for label, command in commands:
    result = subprocess.run(command, cwd=root, capture_output=True, check=False)
    (out / (label + ".stdout.log")).write_bytes(result.stdout)
    (out / (label + ".stderr.log")).write_bytes(result.stderr)
    records.append({"label": label, "argv": command, "exit_code": result.returncode,
                    "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                    "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()})
record = {"commands": records, "workflow_sha256": hashlib.sha256(workflow.read_bytes()).hexdigest(),
          "named_source_sha256": {v: hashlib.sha256((root / v).read_bytes()).hexdigest() for v in files},
          "authority_effect": "None"}
(out / "static_checks.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({v["label"]: v["exit_code"] for v in records}))
raise SystemExit(any(v["exit_code"] for v in records))
