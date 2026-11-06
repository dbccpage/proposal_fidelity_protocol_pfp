"""Mutation controls for source/physical-span auditing, using synthetic notes."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).absolute().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


custody = load("source_custody", CODE / "source_custody.py")
auditor = load("paper011_auditor_test", CODE / "audit_findings.py")


@pytest.fixture
def fixture(tmp_path):
    paper, source = tmp_path / "paper", tmp_path / "source"
    (paper / "docs").mkdir(parents=True)
    source.mkdir()
    data = b"# Synthetic note\r\nfixture\r\n"
    digest = custody.sha256(data)
    notes = []
    for number in range(20):
        path = f"note{number:02}.md"
        (source / path).write_bytes(data)
        notes.append({
            "path": path, "sha256": digest, "size_bytes": len(data), "line_count": 2,
            "sections": [{"start_line": 1, "end_line": 2, "section_sha256": digest}],
        })
    inventory = {
        "source_notes": notes,
        "source_snapshot": {"git_head": "1" * 40, "note_bytes_total": len(data) * 20},
        "challenges": [{"id": f"C{number:03}"} for number in range(1, 61)],
        "genesis_challenges": [{"id": f"G{number:02}"} for number in range(1, 26)],
        "aggregate_demo_families": [{"id": f"family{number}"} for number in range(13)],
        "references": [{"availability": "PRESENT", "path": "note00.md", "sha256": digest}],
    }
    return paper, source, inventory


def write(paper, inventory):
    raw = (json.dumps(inventory) + "\n").encode()
    (paper / "docs/findings_demo_inventory.json").write_bytes(raw)
    return custody.sha256(raw)


def test_good_inventory_is_source_only_evidence(fixture):
    paper, source, inventory = fixture
    result = auditor.audit(paper, source, write(paper, inventory))
    assert result["notes"] == 20
    assert result["section_and_line_bindings"] == 20
    assert result["execution_claim"] == "NONE_SOURCE_AUDIT_ONLY"


@pytest.mark.parametrize("mutation", ["source", "span", "duplicate_id", "conflicting_reference", "pin"])
def test_source_binding_mutations_refuse(fixture, mutation):
    paper, source, inventory = fixture
    if mutation == "source":
        (source / "note00.md").write_bytes(b"changed source")
    elif mutation == "span":
        inventory["source_notes"][0]["sections"][0]["section_sha256"] = "0" * 64
    elif mutation == "duplicate_id":
        inventory["challenges"].append({"id": "C001"})
    elif mutation == "conflicting_reference":
        inventory["references"].append({
            "availability": "PRESENT", "path": "note00.md", "sha256": "0" * 64
        })
    pin = write(paper, inventory)
    if mutation == "pin":
        pin = "0" * 64
    with pytest.raises(custody.CustodyError):
        auditor.audit(paper, source, pin)
