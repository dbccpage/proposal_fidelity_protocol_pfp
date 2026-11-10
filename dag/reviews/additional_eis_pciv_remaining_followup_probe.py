"""One pure source-extracted follow-up; no imports from the reviewed package."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
PREFIX = "additional_eis_pciv_remaining"
scope = json.loads((HERE / (PREFIX + "_scope.json")).read_text(encoding="utf-8"))
path = "eis/tests/architecture/test_clean_architecture_ast_boundaries.py"
pin = next(row for row in scope["files"] if row["path"] == path)
raw = (ROOT / path).read_bytes()
assert hashlib.sha256(raw).hexdigest() == pin["sha256"]
tree = ast.parse(raw.decode("utf-8"))
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_foreign_context")
assert [node.lineno, node.end_lineno] == [92, 96]
print(ast.get_source_segment(raw.decode("utf-8"), node))
namespace = {"PACKAGE": "eis"}
exec(compile(ast.Module(body=[node], type_ignores=[]), path + ":isolated-helper", "exec"), namespace)
observed = {name: namespace["_foreign_context"](name) for name in (
    "engine_foreign.infrastructure.module", "pciv.infrastructure.module", "pfp.domain.module",
    "operads.domain.module", "operations.infrastructure.module", "eis.domain.module",
)}
assert observed["engine_foreign.infrastructure.module"] == "engine_foreign"
assert all(observed[name] is None for name in observed if not name.startswith("engine_"))
report = {
    "kind": "fresh_pure_extracted_function_probe",
    "source_evidence": [{"path": path, "sha256": pin["sha256"], "lines": [[92, 96]]}],
    "observed": observed,
    "passed_expected_observation": True,
    "claim": "The helper does not recognize modern non-engine context roots.",
    "ceiling": "Only helper classification; no production package imports, module test run, filesystem mutation by reviewed code, or claim of an actual dependency violation.",
}
(HERE / (PREFIX + "_followup_probe.json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
