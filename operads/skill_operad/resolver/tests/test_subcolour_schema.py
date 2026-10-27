"""Sub-colour payload schemas: real executor outputs pass, malformed ones are refused."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from operads.canon import SUBCOLOUR_SCHEMAS, TYPES
from operads.skill_operad.resolver import executors, subcolour_schema
from operads.skill_operad.skill_compiler.op_inventory import INVENTORY_PATH, load_inventory

REPO = Path(__file__).resolve().parents[4]
INVENTORY = load_inventory(REPO / INVENTORY_PATH)
OUTPUTS = {op.op_id: op.output for skill in INVENTORY.skills for op in skill.ops}


def test_every_subcolour_has_a_schema() -> None:
    assert set(SUBCOLOUR_SCHEMAS) == set(TYPES["operad_subcolour"]["values"])


def test_every_subcolour_port_in_the_inventory_has_a_schema() -> None:
    ports = {port for skill in INVENTORY.skills for op in skill.ops for port in (*op.inputs, op.output)}
    assert {port for port in ports if "." in port} <= set(SUBCOLOUR_SCHEMAS)


def test_a_plain_colour_accepts_anything() -> None:
    assert subcolour_schema.output_problem("Audit", {"anything": 1}) is None


def _check(op_id: str, value: object) -> None:
    assert subcolour_schema.output_problem(OUTPUTS[op_id], value) is None


def test_real_outputs_pass(tmp_path: Path) -> None:
    source = tmp_path / "mod.py"
    source.write_text("try:\n    x = 1\nexcept:\n    pass\n", encoding="utf-8")
    findings = executors._scan([str(source)])
    _check("sfh.scan", findings)
    assert findings

    docs = {"json.py": "x = 1\n", "pkg/test_a.py": "import sys\nsys.path.append('.')\n"}
    _check("gti.shadow_scan", executors._gti_shadow(docs))
    _check("gti.layout_check", executors._gti_layout(docs))

    ledger = executors._ara_bind({"paths": [str(source)], "omitted_variables": []})
    _check("ara.bind_source_hashes", ledger)
    claim = {"source_hashes": {str(source): hashlib.sha256(source.read_bytes()).hexdigest()}}
    _check("ara.refute", executors._ara_refute(ledger, claim))

    _check("mnc.purge", executors._mnc_purge({"pkg/mod.py": "x = 1  # note\n"}))
    hits = [{"gate": "G3-hype", "severity": "WARN", "path": "p.md", "line": 1, "message": "m"}]
    _check("glossa.merge_hits", hits)
    _check("glossa.propose_replacements", executors._glossa_replacements(hits))


@pytest.mark.parametrize(
    ("port", "value", "reason"),
    [
        ("Audit.hype_hits", {"hits": "none"}, "expected array"),
        ("Audit.shadow_violations", [{"code": "OTHER", "path": "x.py"}], "expected 'STDLIB_SHADOW'"),
        ("Audit.verdict", {"status": "OK", "ledger": {}, "claim": None, "scope": ""}, "is not one of"),
        ("Ledger.source_hashes", {"sources": {"a": "not-a-digest"}, "omitted_variables": []}, "does not match"),
        ("Code.purged", {"sources": {}, "input_digest": "a"}, "missing 'output_digest'"),
        ("Audit.lint_diff", [{"finding": {}, "suggestion": "s", "applied": True}], "expected False"),
        ("Audit.layout_findings", [{"code": "UNSCOPED_TEST", "path": "t.py", "extra": 1}], "unexpected 'extra'"),
    ],
)
def test_malformed_outputs_are_refused(port: str, value: object, reason: str) -> None:
    found = subcolour_schema.output_problem(port, value)
    assert found is not None and reason in found
