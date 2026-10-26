"""Bounded production guard mutants in isolated code; exact restoration is mandatory."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path.cwd()
out = Path(__file__).resolve().parent
runner = out / "run_python_check.py"
controls = [
    (
        "decision_binding_mutant",
        "omega_engine_woland/infrastructure/estates/oewas_native_anti_skill.py",
        '    expected["schema_version"] = "omega.native.anti-skill-decision.v1"\n    if any(wire[k] != v for k, v in expected.items()):',
        '    expected["schema_version"] = "omega.native.anti-skill-decision.v1"\n    if False:  # scoped mutation: exact deployment/request binding bypass',
        "omega_engine_woland/tests/spine/test_native_anti_skill_ingress.py::test_actual_native_response_tampering_is_refused",
    ),
    (
        "foreign_task_mutant",
        "omega_engine_woland/use_cases/base_swarm/woland_swarm.py",
        "        if not fixture_mode and outcome.task_key != request.task_key:",
        "        if False:  # scoped mutation: foreign-task write barrier bypass",
        "omega_engine_woland/tests/spine/test_cross_engine_task_binding.py::test_foreign_task_is_refused_before_estate_writes",
    ),
]
results = []
for label, relative, original, replacement, test in controls:
    path = root / relative
    raw = path.read_bytes()
    source = raw.decode("utf-8")
    if "\r\n" in source:
        original = original.replace("\n", "\r\n")
        replacement = replacement.replace("\n", "\r\n")
    if source.count(original) != 1:
        raise ValueError("mutation anchor must be unique: " + label)
    before = hashlib.sha256(raw).hexdigest()
    try:
        path.write_bytes(source.replace(original, replacement, 1).encode("utf-8"))
        outcome = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(runner), label, test], check=False
        )
    finally:
        path.write_bytes(raw)
    restored = hashlib.sha256(path.read_bytes()).hexdigest()
    results.append(
        {
            "label": label,
            "source": relative,
            "original_sha256": before,
            "restored_sha256": restored,
            "exit_code": outcome.returncode,
            "control": test,
            "authority_effect": "None",
        }
    )
    if restored != before or outcome.returncode != 1:
        raise ValueError("mutation control failed or source was not restored")
(out / "root_mutations.json").write_text(
    json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n"
)
