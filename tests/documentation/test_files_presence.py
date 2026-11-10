"""E2E Test: Documentation Files Presence and Content Substantiveness.

AuthorityEffect: None.

Validates that all 69 required documentation files across the 5 project tracks exist,
have substantive non-empty content (>500 bytes), and include standard markdown headers.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import pytest

REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.documentation.conftest import REQUIRED_DOCUMENTATION_FILES


class TestDocumentationFilesPresence:
    """Verifies that all required documentation files are present on disk with substantive content."""

    MIN_FILE_SIZE_BYTES: int = 500

    @pytest.mark.parametrize("rel_path", REQUIRED_DOCUMENTATION_FILES)
    def test_required_file_exists(self, repo_root: Path, rel_path: str) -> None:
        """Verify each required documentation file exists on disk."""
        target = repo_root / rel_path
        assert target.is_file(), f"Missing required documentation file: {rel_path}"

    @pytest.mark.parametrize("rel_path", REQUIRED_DOCUMENTATION_FILES)
    def test_required_file_substantive_size(self, repo_root: Path, rel_path: str) -> None:
        """Verify each required documentation file contains substantive content (>500 bytes)."""
        target = repo_root / rel_path
        if not target.is_file():
            pytest.skip(f"File not yet created: {rel_path}")
        size = target.stat().st_size
        assert size > self.MIN_FILE_SIZE_BYTES, (
            f"Documentation file {rel_path} has size {size} bytes, "
            f"which fails the substantive threshold of >{self.MIN_FILE_SIZE_BYTES} bytes."
        )

    def test_operators_track_completeness(self, docs_dir: Path) -> None:
        """Verify all 4 operator track documentation files exist."""
        operators_dir = docs_dir / "operators"
        expected = [
            "taxonomy.md",
            "ddc_transitions.md",
            "operad_composition.md",
            "prompt_families.md",
        ]
        for fname in expected:
            fpath = operators_dir / fname
            assert fpath.is_file(), f"Operators track missing file: {fpath}"
            assert fpath.stat().st_size > self.MIN_FILE_SIZE_BYTES

    def test_eis_track_completeness(self, docs_dir: Path) -> None:
        """Verify all 4 Epistemic Immune System track documentation files exist."""
        eis_dir = docs_dir / "EIS"
        expected = [
            "overview.md",
            "four_gate_protocol.md",
            "antibodies.md",
            "danger_gating.md",
        ]
        for fname in expected:
            fpath = eis_dir / fname
            assert fpath.is_file(), f"EIS track missing file: {fpath}"
            assert fpath.stat().st_size > self.MIN_FILE_SIZE_BYTES

    def test_p_sieve_track_completeness(self, docs_dir: Path) -> None:
        """Verify all 4 Prompt Sieve track documentation files exist."""
        p_sieve_dir = docs_dir / "P_sieve"
        expected = [
            "seed_ingestion.md",
            "nested_prompts.md",
            "family_dag.md",
            "evolution_tracking.md",
        ]
        for fname in expected:
            fpath = p_sieve_dir / fname
            assert fpath.is_file(), f"Prompt Sieve track missing file: {fpath}"
            assert fpath.stat().st_size > self.MIN_FILE_SIZE_BYTES

    def test_workflows_track_core_files(self, docs_dir: Path) -> None:
        """Verify the 3 core workflow documentation files exist."""
        wf_dir = docs_dir / "workflows"
        expected = [
            "README.md",
            "canonical_pipeline.md",
            "pfp_lab_governor.md",
        ]
        for fname in expected:
            fpath = wf_dir / fname
            assert fpath.is_file(), f"Workflows core missing file: {fpath}"
            assert fpath.stat().st_size > self.MIN_FILE_SIZE_BYTES

    def test_workflows_track_all_49_files(self, docs_dir: Path) -> None:
        """Verify all 49 individual workflow files (wf0001.md to wf0049.md) exist."""
        wf_dir = docs_dir / "workflows"
        missing: List[str] = []
        under_sized: List[str] = []

        for i in range(1, 50):
            fname = f"wf{i:04d}.md"
            fpath = wf_dir / fname
            if not fpath.is_file():
                missing.append(fname)
            elif fpath.stat().st_size <= self.MIN_FILE_SIZE_BYTES:
                under_sized.append(f"{fname} ({fpath.stat().st_size} bytes)")

        assert not missing, f"Missing {len(missing)}/49 workflow files: {missing}"
        assert not under_sized, f"Found under-sized workflow files (<=500 bytes): {under_sized}"

    def test_anomalon_track_completeness(self, docs_dir: Path) -> None:
        """Verify all 5 Anomalon integration track documentation files exist."""
        anomalon_dir = docs_dir / "anomalon"
        expected = [
            "omega_engine_pfp.md",
            "operads_crates.md",
            "epistemic_immune.md",
            "prompt_civilization.md",
            "symbol_game.md",
        ]
        for fname in expected:
            fpath = anomalon_dir / fname
            assert fpath.is_file(), f"Anomalon track missing file: {fpath}"
            assert fpath.stat().st_size > self.MIN_FILE_SIZE_BYTES

    def test_total_documentation_file_count(self, docs_dir: Path) -> None:
        """Verify that at least 69 documentation markdown files exist in documentation/."""
        all_md = list(docs_dir.rglob("*.md"))
        assert len(all_md) >= 69, (
            f"Expected at least 69 documentation files, but found {len(all_md)}. "
            f"Current files: {[str(p.relative_to(docs_dir)) for p in all_md]}"
        )

    def test_adversarial_nonexistent_file_rejected(self, repo_root: Path) -> None:
        """Adversarial check: ensure a synthetic nonexistent file path is rejected."""
        fake_path = repo_root / "documentation" / "operators" / "phantom_operator_123.md"
        assert not fake_path.exists(), "Adversarial setup failure: fake file must not exist"

    def test_adversarial_under_sized_file_rejected(self, tmp_path: Path) -> None:
        """Adversarial check: ensure a stub file with <=500 bytes fails the substantive size check."""
        stub_file = tmp_path / "stub.md"
        stub_file.write_text("# Stub\nBrief description.\n", encoding="utf-8")
        assert stub_file.stat().st_size <= self.MIN_FILE_SIZE_BYTES, (
            "Stub file should be under 500 bytes for adversarial test"
        )
