"""Adversarial Empirical Challenge Test Suite.

AuthorityEffect: None.
Standard: Ground Truth Verification and Empirical Falsification Standard.

This test suite executes rigorous adversarial falsification checks:
1. Workflow Coverage & Attribute Bijection:
   - Validates that every DAG node in workflows/dag/workflow_dag.json maps 1:1 to
     documentation/workflows/wf0001.md .. wf0049.md.
   - Audits correspondence of Workflow ID, Status, Kind, Layer, and Depends-On.
2. WF1–WF5 Runnable Implementations:
   - Verifies input schemas, workflow profiles, and deterministic offline replayability.
3. Anomalon Sovereign Crates:
   - Verifies existence of all 8 surveyed components and their physical crates.
   - Verifies that immune_guarded_substitute in omega_operads/src/immune_guards.rs
     gates operad substitutions via ImmuneScreenPort.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent
ANOMALON_ROOT: Path = Path(r"c:\Users\a343o\source\repos\anomalon")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "ops") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "ops"))


class TestWorkflowDagBijection:
    """Adversarially falsifies workflow documentation completeness and metadata fidelity."""

    def test_dag_node_count_and_uniqueness(self, workflow_dag: Dict[str, Any]) -> None:
        nodes = workflow_dag.get("nodes", [])
        assert len(nodes) == 49, f"Expected exactly 49 nodes in DAG, found {len(nodes)}"
        ids = [n["id"] for n in nodes]
        assert len(ids) == len(set(ids)), f"Duplicate DAG node IDs: {ids}"
        for i in range(1, 50):
            assert f"WF{i}" in ids, f"Missing WF{i} in DAG nodes"

    def test_all_49_files_exist_and_match_canonical_naming(self) -> None:
        wf_dir = REPO_ROOT / "documentation" / "workflows"
        missing = []
        for i in range(1, 50):
            canonical = wf_dir / f"wf{i:04d}.md"
            if not canonical.is_file():
                missing.append(f"wf{i:04d}.md")
        assert not missing, f"Missing canonical workflow doc files: {missing}"

    def test_workflow_identity_and_status_match_dag(self, workflow_dag: Dict[str, Any]) -> None:
        wf_dir = REPO_ROOT / "documentation" / "workflows"
        mismatches: List[str] = []

        for node in workflow_dag["nodes"]:
            node_id = node["id"]
            num = int(node_id.replace("WF", ""))
            doc_file = wf_dir / f"wf{num:04d}.md"
            assert doc_file.is_file(), f"File missing for {node_id}"
            content = doc_file.read_text(encoding="utf-8")

            # 1. AuthorityEffect: None
            if not re.search(r"\*{0,2}AuthorityEffect\*{0,2}\s*[:=]\s*\*{0,2}None", content, re.IGNORECASE):
                mismatches.append(f"{node_id}: missing AuthorityEffect: None")

            # 2. Workflow ID
            if not re.search(r"\*{0,2}Workflow ID:\*{0,2}\s*`?" + re.escape(node_id) + r"`?", content):
                mismatches.append(f"{node_id}: header does not match ID {node_id}")

            # 3. Status
            exp_status = node.get("status")
            if exp_status and not re.search(
                r"\*{0,2}Status:\*{0,2}\s*`?" + re.escape(exp_status) + r"`?", content, re.IGNORECASE
            ):
                mismatches.append(f"{node_id}: status mismatch, expected '{exp_status}'")

            # 4. Kind
            exp_kind = node.get("kind")
            if exp_kind and not re.search(
                r"\*{0,2}Kind:\*{0,2}\s*`?" + re.escape(exp_kind) + r"`?", content, re.IGNORECASE
            ):
                mismatches.append(f"{node_id}: kind mismatch, expected '{exp_kind}'")

            # 5. Depends on / Builds on
            depends_on = node.get("depends_on", [])
            if not depends_on:
                if not re.search(r"\*{0,2}Builds On:\*{0,2}\s*(?:None|Base)", content, re.IGNORECASE):
                    mismatches.append(f"{node_id}: root workflow should state 'Builds On: None'")
            else:
                m_builds = re.search(r"\*\*Builds On:\*\*\s*(.+)", content)
                builds_str = m_builds.group(1).strip() if m_builds else ""
                for dep in depends_on:
                    if dep not in builds_str:
                        mismatches.append(f"{node_id}: missing dependency citation for '{dep}' in '{builds_str}'")

        assert not mismatches, f"Mismatches found in workflow docs:\n" + "\n".join(f" - {m}" for m in mismatches)

    def test_layer_conventions_audit(self, workflow_dag: Dict[str, Any]) -> None:
        """Audits that all 49 workflow documentation headers and README master index match workflow_dag.json layers."""
        wf_dir = REPO_ROOT / "documentation" / "workflows"
        readme_content = (wf_dir / "README.md").read_text(encoding="utf-8")
        layer_divergences = {}
        readme_divergences = {}

        for node in workflow_dag["nodes"]:
            node_id = node["id"]
            num = int(node_id.replace("WF", ""))
            doc_file = wf_dir / f"wf{num:04d}.md"
            content = doc_file.read_text(encoding="utf-8")
            dag_layer = node.get("layer")
            m_layer = re.search(r"\*\*Layer:\*\*\s*(\d+)", content)
            doc_layer = int(m_layer.group(1)) if m_layer else None
            if dag_layer != doc_layer:
                layer_divergences[node_id] = {"dag_layer": dag_layer, "doc_layer": doc_layer}

            m_readme = re.search(
                rf"\|\s*\*\*{re.escape(node_id)}\*\*\s*\|[^|]+\|[^|]+\|[^|]+\|\s*(\d+)\s*\|",
                readme_content,
            )
            readme_layer = int(m_readme.group(1)) if m_readme else None
            if dag_layer != readme_layer:
                readme_divergences[node_id] = {"dag_layer": dag_layer, "readme_layer": readme_layer}

        assert not layer_divergences, (
            f"Layer divergences between workflow_dag.json and workflow docs: {layer_divergences}"
        )
        assert not readme_divergences, (
            f"Layer divergences between workflow_dag.json and README.md: {readme_divergences}"
        )


class TestWF1ToWF5RunnableGroundTruth:
    """Empirically verifies runnable implementations of WF1-WF5 against documentation."""

    @pytest.mark.parametrize("wf_idx", [1, 2, 3, 4, 5])
    def test_wf_code_files_exist(self, wf_idx: int) -> None:
        folder = REPO_ROOT / "pfp" / "workflows" / f"wf{wf_idx:04d}"
        assert folder.is_dir(), f"Missing workflow directory: {folder}"
        assert (folder / "workflow.json").is_file(), f"Missing workflow.json profile: {folder}"
        assert (folder / "workflow.py").is_file(), f"Missing workflow.py: {folder}"
        assert (folder / "runner.py").is_file(), f"Missing runner.py: {folder}"
        # WF1-WF3 have dedicated task_spec.schema.json; WF4-WF5 inherit from WF3
        if wf_idx in [1, 2, 3]:
            assert (folder / "task_spec.schema.json").is_file()
        elif wf_idx == 5:
            assert (folder / "packet.ebnf").is_file()

    @pytest.mark.parametrize("wf_idx", [1, 2, 3])
    def test_schema_conformance_for_base_and_relay(self, wf_idx: int) -> None:
        schema_path = REPO_ROOT / "pfp" / "workflows" / f"wf{wf_idx:04d}" / "task_spec.schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        assert schema.get("type") == "object"
        assert "required" in schema
        required = set(schema["required"])
        assert "task_id" in required
        assert "seed_prompt" in required

    @pytest.mark.parametrize("wf_idx", [1, 2, 3, 4, 5])
    def test_workflow_profile_consistency(self, wf_idx: int) -> None:
        profile_path = REPO_ROOT / "pfp" / "workflows" / f"wf{wf_idx:04d}" / "workflow.json"
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        assert profile.get("workflow_id") == f"WF{wf_idx}"

    def test_offline_fixture_replay_wf1(self, tmp_path: Path) -> None:
        """Empirically exercises WF1 prepare and check without network calls."""
        from pfp.workflows.wf0001 import workflow
        from pfp.workflows.wf0001.runner import runtime as runner

        spec = json.loads(workflow.resource_text("examples/integer_sum.task.json"))
        run_root = tmp_path / "wf1_run"
        runner.prepare_run(spec, run_root)
        assert (run_root / "task.json").is_file()
        assert (run_root / "prepared.json").is_file()

        turn = workflow.prepare_task(spec)
        reply_dict = {
            "task_id": turn.binding["task_id"],
            "attempt_id": turn.binding["attempt_id"],
            "input_sha256": turn.binding["input_sha256"],
            "answer": {"total": 38},
        }
        reply_bytes = json.dumps(reply_dict).encode("utf-8")
        raw_file = tmp_path / "reply.json"
        raw_file.write_bytes(reply_bytes)

        receipt = runner.check_run(run_root, raw_file)
        assert receipt["status"] == "HOST_ACCEPTED"
        assert receipt["external_provider_calls"] is None

        replayed = runner.replay_run(run_root)
        assert replayed["replay_verified"] is True
        assert replayed["status"] == "HOST_ACCEPTED"


class TestAnomalonCratesAndSymbols:
    """Empirically verifies existence of Anomalon crates and critical immune gating symbols."""

    SURVEYED_COMPONENTS = [
        ("omega_engine_pfp", ANOMALON_ROOT / "omega_engine_pfp"),
        ("omega_pfp_engine", ANOMALON_ROOT / "omega_engine_pfp" / "engine_rs"),
        ("omega_operad_theory", ANOMALON_ROOT / "omega_engine" / "crates_rs" / "omega_operad_theory"),
        ("omega_operads", ANOMALON_ROOT / "omega_engine" / "crates_rs" / "omega_operads"),
        ("omega_epistemic_immune_system", ANOMALON_ROOT / "omega_engine" / "crates_rs" / "omega_epistemic_immune_system"),
        ("omega_prompt_civilization", ANOMALON_ROOT / "omega_engine" / "crates_rs" / "omega_prompt_civilization"),
        ("omega_symbol_game", ANOMALON_ROOT / "omega_engine" / "crates_rs" / "omega_symbol_game"),
        ("omega_symbol_game_runtime", ANOMALON_ROOT / "omega_engine" / "crates_rs" / "omega_symbol_game_runtime"),
    ]

    @pytest.mark.parametrize("name,path", SURVEYED_COMPONENTS)
    def test_component_exists_on_disk(self, name: str, path: Path) -> None:
        assert path.exists(), f"Surveyed Anomalon component does not exist: {name} at {path}"
        if (path / "Cargo.toml").exists():
            content = (path / "Cargo.toml").read_text(encoding="utf-8")
            assert f'name = "{name}"' in content or f"name = '{name}'" in content

    def test_immune_guarded_substitute_implementation_and_gating(self) -> None:
        immune_guards_path = (
            ANOMALON_ROOT
            / "omega_engine"
            / "crates_rs"
            / "omega_operads"
            / "src"
            / "immune_guards.rs"
        )
        assert immune_guards_path.is_file(), f"immune_guards.rs not found at {immune_guards_path}"
        code = immune_guards_path.read_text(encoding="utf-8")

        # 1. Verify immune_guarded_substitute signature
        assert "pub fn immune_guarded_substitute(" in code
        assert "immune: &mut dyn ImmuneScreenPort" in code
        assert "evidence: DangerScreenRequest<'_>" in code

        # 2. Verify gating mechanism
        assert "let verdict = immune.danger_verdict(" in code
        assert "if *verdict.blocks() {" in code
        assert '"DANGER_GATE_SUPPRESSION"' in code

        # 3. Verify fallback to substitute on approval
        assert "substitute(theta, index, phi)" in code

    def test_immune_ports_defines_screen_trait(self) -> None:
        immune_ports_path = (
            ANOMALON_ROOT
            / "omega_engine"
            / "crates_rs"
            / "omega_operads"
            / "src"
            / "immune_ports.rs"
        )
        assert immune_ports_path.is_file(), f"immune_ports.rs not found at {immune_ports_path}"
        code = immune_ports_path.read_text(encoding="utf-8")

        assert "pub trait ImmuneScreenPort" in code
        assert "fn danger_verdict(" in code
        assert "fn quorum_verdict(" in code
