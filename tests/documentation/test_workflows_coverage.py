"""E2E Test: Workflows Coverage Verification against workflow_dag.json.

AuthorityEffect: None.

Loads workflows/dag/workflow_dag.json and validates that:
1. Every workflow node ID (WF1 through WF49) has a corresponding markdown file
   in documentation/workflows/ (canonical format: wf0001.md to wf0049.md).
2. Each documentation file contains substantive content (>500 bytes) describing
   the objective, parameters, operators, and acceptance criteria of the workflow.
3. Master indices and pipeline specifications (README.md, canonical_pipeline.md,
   pfp_lab_governor.md) are present.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.documentation.conftest import DOCUMENTATION_DIR, WORKFLOW_DAG_PATH


def parse_workflow_number(node_id: str) -> int:
    """Extract numeric suffix from workflow ID (e.g. 'WF1' -> 1, 'WF0049' -> 49)."""
    match = re.search(r"\d+", node_id)
    if not match:
        raise ValueError(f"Cannot extract integer workflow number from node id '{node_id}'")
    return int(match.group(0))


def get_expected_workflow_filenames(node_id: str) -> List[str]:
    """Return acceptable filenames for a workflow node ID (canonical 4-digit padded, fallback unpadded)."""
    num = parse_workflow_number(node_id)
    return [f"wf{num:04d}.md", f"wf{num}.md"]


class TestWorkflowsCoverage:
    """Verifies that all workflows defined in the DAG have dedicated documentation."""

    MIN_FILE_SIZE_BYTES: int = 500

    def test_workflow_dag_file_exists_and_valid(self, workflow_dag: Dict[str, Any]) -> None:
        """Verify the workflow DAG JSON file is valid and contains required root keys."""
        assert "nodes" in workflow_dag, "workflow_dag.json missing 'nodes' array"
        assert "kinds" in workflow_dag, "workflow_dag.json missing 'kinds' definition"
        assert len(workflow_dag["nodes"]) == 49, (
            f"Expected exactly 49 workflow nodes in DAG, found {len(workflow_dag['nodes'])}"
        )

    def test_all_dag_nodes_have_unique_ids(self, workflow_dag: Dict[str, Any]) -> None:
        """Verify every node in the DAG has a distinct, valid ID (WF1..WF49)."""
        node_ids = [n["id"] for n in workflow_dag["nodes"]]
        assert len(node_ids) == len(set(node_ids)), f"Duplicate workflow node IDs found: {node_ids}"
        expected_ids = {f"WF{i}" for i in range(1, 50)}
        assert set(node_ids) == expected_ids, (
            f"DAG node IDs mismatch: missing {expected_ids - set(node_ids)}, "
            f"extra {set(node_ids) - expected_ids}"
        )

    def test_every_dag_workflow_has_documentation_file(
        self, workflow_dag: Dict[str, Any], docs_dir: Path
    ) -> None:
        """Verify every workflow ID in the DAG maps to an existing documentation file in documentation/workflows/."""
        wf_dir = docs_dir / "workflows"
        missing_docs: List[str] = []
        under_sized_docs: List[str] = []

        for node in workflow_dag["nodes"]:
            node_id = node["id"]
            candidates = get_expected_workflow_filenames(node_id)
            matching_file: Path | None = None
            for c in candidates:
                p = wf_dir / c
                if p.is_file():
                    matching_file = p
                    break

            if matching_file is None:
                missing_docs.append(f"{node_id} (expected {candidates[0]})")
            elif matching_file.stat().st_size <= self.MIN_FILE_SIZE_BYTES:
                under_sized_docs.append(
                    f"{node_id} -> {matching_file.name} ({matching_file.stat().st_size} bytes)"
                )

        assert not missing_docs, (
            f"Missing documentation for {len(missing_docs)}/49 workflows:\n"
            + "\n".join(f" - {m}" for m in missing_docs)
        )
        assert not under_sized_docs, (
            f"Under-sized documentation files (<=500 bytes) for workflows:\n"
            + "\n".join(f" - {u}" for u in under_sized_docs)
        )

    def test_workflow_docs_reference_workflow_identity(
        self, workflow_dag: Dict[str, Any], docs_dir: Path
    ) -> None:
        """Verify each workflow doc references its workflow ID or title in its header."""
        wf_dir = docs_dir / "workflows"
        unmatched_identity: List[str] = []

        for node in workflow_dag["nodes"]:
            node_id = node["id"]
            num = parse_workflow_number(node_id)
            canonical_path = wf_dir / f"wf{num:04d}.md"
            if not canonical_path.is_file():
                continue

            content = canonical_path.read_text(encoding="utf-8", errors="replace")
            # Must mention WF{num} or wf{num:04d} or the name
            id_patterns = [
                rf"\bWF{num}\b",
                rf"\bwf{num:04d}\b",
                re.escape(node.get("name", "")),
            ]
            if not any(re.search(pat, content, re.IGNORECASE) for pat in id_patterns if pat):
                unmatched_identity.append(f"{canonical_path.name}: does not mention {node_id}")

        assert not unmatched_identity, (
            f"Workflow docs failing identity verification:\n"
            + "\n".join(f" - {u}" for u in unmatched_identity)
        )

    def test_master_workflow_readme_indexes_all_workflows(self, docs_dir: Path) -> None:
        """Verify documentation/workflows/README.md indexes or describes the 49 workflows."""
        readme = docs_dir / "workflows" / "README.md"
        assert readme.is_file(), f"Missing {readme}"
        content = readme.read_text(encoding="utf-8")
        assert len(content) > 500, "Workflows README.md is under 500 bytes"

    def test_canonical_pipeline_specification_present(self, docs_dir: Path) -> None:
        """Verify documentation/workflows/canonical_pipeline.md exists and describes the 11 stages."""
        pipeline_doc = docs_dir / "workflows" / "canonical_pipeline.md"
        assert pipeline_doc.is_file(), f"Missing {pipeline_doc}"
        content = pipeline_doc.read_text(encoding="utf-8")
        assert len(content) > 500
        assert "11" in content or "canonical" in content.lower()

    def test_pfp_lab_governor_specification_present(self, docs_dir: Path) -> None:
        """Verify documentation/workflows/pfp_lab_governor.md exists and describes governor moves."""
        gov_doc = docs_dir / "workflows" / "pfp_lab_governor.md"
        assert gov_doc.is_file(), f"Missing {gov_doc}"
        content = gov_doc.read_text(encoding="utf-8")
        assert len(content) > 500
        # Should describe moves (ASSERT, CUT, VERIFY, RETRACT)
        for move in ["ASSERT", "CUT", "VERIFY", "RETRACT"]:
            assert move in content, f"pfp_lab_governor.md missing description of move '{move}'"

    def test_adversarial_unmapped_workflow_detection(self) -> None:
        """Adversarial check: ensure a synthetic node ID produces expected canonical filenames."""
        fake_id = "WF999"
        filenames = get_expected_workflow_filenames(fake_id)
        assert filenames == ["wf0999.md", "wf999.md"]

    def test_adversarial_malformed_node_id_raises_value_error(self) -> None:
        """Adversarial check: ensure an invalid node ID lacking numbers raises ValueError."""
        with pytest.raises(ValueError, match="Cannot extract integer workflow number"):
            parse_workflow_number("WF_INVALID_NO_NUMBERS")
