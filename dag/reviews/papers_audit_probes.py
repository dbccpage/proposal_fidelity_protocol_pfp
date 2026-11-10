"""Offline audit probes; imports no provider and reads no private benchmark."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
report = {"python": sys.version, "scope": "Four finite PFP replay scripts plus isolated PFP020 target predicate and documented import", "checks": []}
for paper in (13, 14, 15, 16):
    directory = next((ROOT / "papers/pfp").glob(f"{paper:03d}_*"))
    script = directory / "code/replay.py"
    proc = subprocess.run([sys.executable, "-B", str(script)], cwd=directory, capture_output=True, text=True, timeout=30)
    report["checks"].append({"path": script.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(script.read_bytes()).hexdigest(), "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})

source = ROOT / "papers/pfp/020_pfp_frontier_research/code/l8_n4_cross_validation.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "L8N4CrossValidationRunner")
method = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == "_verify_target_gate")
module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), method], type_ignores=[])
ast.fix_missing_locations(module)
namespace = {}
exec(compile(module, str(source), "exec"), namespace)
gate = namespace["_verify_target_gate"]
cases = [
    ("double-CNOT-is-identity", "cnot_14", (("cnot", (1, 4)), ("cnot", (1, 4)))),
    ("GHZ-missing-two-entanglers", "ghz_4", (("hadamard", (1, 0)), ("cnot", (1, 4)))),
]
for name, target, schedule in cases:
    report["checks"].append({"probe": name, "isolated_source_method": str(source.relative_to(ROOT)), "actual_acceptance": gate(None, target, schedule), "scope": "Executed actual AST-extracted method without unavailable project import. Gate names interpreted by their claimed standard semantics."})
proc = subprocess.run([sys.executable, "-B", str(source)], cwd=source.parent.parent, capture_output=True, text=True, timeout=30)
report["checks"].append({"probe": "documented-cross-validation-entrypoint", "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
destination = ROOT / "dag/reviews/papers_audit_probe_results.json"
destination.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"report": str(destination), "finite_replays": [x["returncode"] for x in report["checks"][:4]], "target_false_acceptances": [x["actual_acceptance"] for x in report["checks"][4:6]], "cross_validation_returncode": proc.returncode}))
