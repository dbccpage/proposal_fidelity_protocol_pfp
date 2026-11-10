"""E2E Test: Code Grounding Verification.

AuthorityEffect: None.

Validates that code paths, crates, and symbols cited across the documentation suite
actually exist on disk in proposal_fidelity_protocol_pfp or the sibling anomalon repository.
Enforces that documentation is strictly grounded in real source code rather than aspirational docstrings.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Tuple

import pytest

REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.documentation.conftest import ANOMALON_REPO_ROOT, PFP_REPO_ROOT, CodebaseIndex

RUNTIME_ARTIFACT_FILENAMES: frozenset[str] = frozenset({
    "prepared.json",
    "preparation_manifest.json",
    "provider.json",
    "collection.json",
    "receipt_manifest.json",
    "global_receipt.json",
    "rewrite.json",
    "task.json",
    "custody_audit_report.json",
    "claim_scoped_receipt.json",
    "boundary_diagnostic.json",
})


def is_citation_grounded(
    citation: str,
    index: CodebaseIndex,
    repo_root: Path,
    anomalon_root: Path,
    source_file_dir: Path | None = None,
) -> bool:
    """Verify whether a cited code path, file, or crate exists in PFP or Anomalon."""
    clean = citation.strip("`'\" \t\r\n").replace("\\", "/").rstrip(".,:;)")
    clean = re.sub(r":\d+(?:-\d+)?$", "", clean)

    if not clean or any(ign in clean for ign in ["ab_*.json", "anti_*.yaml", "*", "http://", "https://", "urn:"]):
        return True

    # Runtime artifacts produced during workflow executions
    base_name = clean.split("/")[-1].lower()
    if base_name in RUNTIME_ARTIFACT_FILENAMES:
        return True

    # Relative documentation markdown links
    if clean.endswith(".md"):
        if source_file_dir and (source_file_dir / clean).exists():
            return True
        if (repo_root / "documentation" / clean).exists():
            return True
        if (repo_root / clean).exists():
            return True
        # Workflow proposal documents (wf0001.md through wf0049.md)
        if re.match(r"^(?:workflows/)?wf\d{4}\.md$", clean):
            return True

    # Direct filesystem check
    if (repo_root / clean).exists() or (anomalon_root / clean).exists():
        return True

    lower = clean.lower().rstrip("/")

    # Exact relative path in index
    if lower in index.exact_paths:
        return True

    # Suffix match (e.g. "domain/cochain.py" or "src/activation.rs")
    suffix = "/" + lower
    if any(p.endswith(suffix) for p in index.exact_paths):
        return True

    # Standalone filename match (e.g. "activation.rs", "morphisms.py")
    if "/" not in lower and lower in index.filenames:
        return True

    # Crate name match (e.g. "core_operad_canon", "omega_operad_theory")
    if "/" not in lower and lower in index.crate_names:
        return True

    # Subpath within module or crate (e.g. "eis/pharmacy_catalog.py" or "code/rust/...")
    parts = lower.split("/")
    if len(parts) >= 2:
        top_mod = parts[0]
        fname = parts[-1]
        # Check if file exists under the top module in index
        if any(p.startswith(top_mod + "/") and p.endswith("/" + fname) for p in index.exact_paths):
            return True

    # Alias check: 'pfp/tasks/...' mapping to 'workflows/tasks/...'
    if lower.startswith("pfp/tasks/"):
        workflow_candidate = repo_root / "workflows" / lower[len("pfp/") :]
        if workflow_candidate.exists():
            return True

    return False


class TestCodeGrounding:
    """Validates real-world ground truth of all cited codebase paths and crates."""

    # 1. Canonical Anchors declared in PROJECT.md and ORIGINAL_REQUEST.md
    CANONICAL_PFP_PATHS: List[str] = [
        "code/rust/core_operad_canon",
        "code/rust/core_epistemic_immune_system",
        "code/rust/core_prompt_civilization",
        "pfp/use_cases/pfp_stages.py",
        "pfp_lab/core/governor.py",
        "pfp/use_cases/abstention_governor.py",
        "workflows/dag/workflow_dag.json",
        "eis/domain/danger_gate.py",
        "eis/domain/thymus.py",
        "eis/antibodies/pharmacy_catalog.json",
    ]

    CANONICAL_ANOMALON_PATHS: List[str] = [
        "omega_engine_pfp",
        "omega_engine_pfp/ffi.py",
        "omega_engine_pfp/domain",
        "omega_engine_pfp/engine_rs",
        "omega_engine_pfp/packet_schemas",
        "omega_engine/crates_rs/omega_epistemic_immune_system",
        "omega_engine/crates_rs/omega_operad_theory",
        "omega_engine/crates_rs/omega_operads",
        "omega_engine/crates_rs/omega_prompt_civilization",
        "omega_engine/crates_rs/omega_symbol_game",
        "omega_engine/crates_rs/omega_symbol_game_runtime",
    ]

    @pytest.mark.parametrize("pfp_rel_path", CANONICAL_PFP_PATHS)
    def test_canonical_pfp_code_anchors_exist(self, repo_root: Path, pfp_rel_path: str) -> None:
        """Verify each core PFP code anchor exists on disk in the PFP repository."""
        target = repo_root / pfp_rel_path
        assert target.exists(), f"Grounding failure: Canonical PFP path does not exist on disk: {target}"

    @pytest.mark.parametrize("anom_rel_path", CANONICAL_ANOMALON_PATHS)
    def test_canonical_anomalon_code_anchors_exist(
        self, anomalon_root: Path, anom_rel_path: str
    ) -> None:
        """Verify each core Anomalon code anchor exists on disk in the Anomalon repository."""
        target = anomalon_root / anom_rel_path
        assert target.exists(), f"Grounding failure: Canonical Anomalon path does not exist on disk: {target}"

    def test_pfp_rust_crates_contain_cargo_toml(self, repo_root: Path) -> None:
        """Verify Rust crates in PFP cited in documentation contain valid Cargo.toml files."""
        for crate_name in ["core_operad_canon", "core_epistemic_immune_system", "core_prompt_civilization"]:
            cargo_file = repo_root / "code" / "rust" / crate_name / "Cargo.toml"
            assert cargo_file.is_file(), f"Missing Cargo.toml for cited Rust crate: {cargo_file}"
            content = cargo_file.read_text(encoding="utf-8")
            assert f'name = "{crate_name}"' in content or f"name = '{crate_name}'" in content

    def test_anomalon_crates_contain_cargo_toml(self, anomalon_root: Path) -> None:
        """Verify Rust crates in Anomalon cited in documentation contain valid Cargo.toml files."""
        cited_crates = [
            "omega_epistemic_immune_system",
            "omega_operad_theory",
            "omega_operads",
            "omega_prompt_civilization",
            "omega_symbol_game",
            "omega_symbol_game_runtime",
        ]
        for crate_name in cited_crates:
            cargo_file = anomalon_root / "omega_engine" / "crates_rs" / crate_name / "Cargo.toml"
            assert cargo_file.is_file(), f"Missing Cargo.toml in Anomalon crate: {cargo_file}"
            content = cargo_file.read_text(encoding="utf-8")
            assert f'name = "{crate_name}"' in content or f"name = '{crate_name}'" in content

    def test_extract_and_validate_explicit_documentation_path_citations(
        self,
        all_doc_files: List[Path],
        codebase_index: CodebaseIndex,
        repo_root: Path,
        anomalon_root: Path,
    ) -> None:
        """Extract explicit file and directory citations in documentation and verify real-world existence."""
        assert len(all_doc_files) > 0, "No documentation files found to evaluate"

        path_pattern = re.compile(
            r"`([a-zA-Z0-9_\-\./\\]+\.(?:py|rs|json|yaml|toml|md))`|"
            r"`((?:code/|pfp/|pfp_lab/|eis/|operads/|workflows/|documentation/|omega_engine)[a-zA-Z0-9_\-\./\\]*)`"
        )

        unresolved: List[Tuple[str, int, str]] = []
        verified_count = 0

        for fpath in all_doc_files:
            text = fpath.read_text(encoding="utf-8", errors="replace")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if line.strip().startswith("#") or "AuthorityEffect" in line:
                    continue

                # Skip lines that explicitly discuss deleted, aspirational, or non-existent legacy files
                line_lower = line.lower()
                if any(k in line_lower for k in ["deleted", "aspirational", "does not exist", "legacy modules"]):
                    continue

                for match in path_pattern.finditer(line):
                    citation = match.group(1) or match.group(2)
                    if not citation:
                        continue

                    if any(ignore in citation for ignore in ["wf0001.md ... wf0049.md", "ab_*.json", "anti_*.yaml"]):
                        continue

                    grounded = is_citation_grounded(
                        citation, codebase_index, repo_root, anomalon_root, source_file_dir=fpath.parent
                    )
                    if grounded:
                        verified_count += 1
                    else:
                        unresolved.append((str(fpath.relative_to(repo_root)), line_no, citation))

        assert verified_count > 0, "No code citations were verified across documentation"
        if unresolved:
            report = "\n".join(f" - {f}:{ln} -> `{cit}`" for f, ln, cit in unresolved[:25])
            pytest.fail(
                f"Discovered {len(unresolved)} ungrounded or hallucinated code citations:\n{report}"
            )

    def test_adversarial_hallucinated_path_rejection(
        self, codebase_index: CodebaseIndex, repo_root: Path, anomalon_root: Path
    ) -> None:
        """Adversarial check: ensure a synthetic hallucinated path is rejected by the resolver."""
        fake_citations = [
            "pfp/use_cases/phantom_super_optimizer.py",
            "omega_engine/crates_rs/omega_fake_omniscience",
            "code/rust/core_hallucination_crate",
            "nonexistent_hallucinated_file_12345.rs",
        ]
        for fake in fake_citations:
            grounded = is_citation_grounded(fake, codebase_index, repo_root, anomalon_root)
            assert not grounded, f"Adversarial failure: fake path unexpectedly resolved as grounded: {fake}"
