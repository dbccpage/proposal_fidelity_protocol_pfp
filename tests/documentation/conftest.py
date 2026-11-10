"""Shared test configuration, fixtures, and constants for documentation E2E tests.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Set

import pytest

PFP_REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent
ANOMALON_REPO_ROOT: Path = Path("c:/Users/a343o/source/repos/anomalon").resolve()
DOCUMENTATION_DIR: Path = PFP_REPO_ROOT / "documentation"
WORKFLOW_DAG_PATH: Path = PFP_REPO_ROOT / "workflows" / "dag" / "workflow_dag.json"

REQUIRED_DOCUMENTATION_FILES: List[str] = [
    # Operators Track (M1)
    "documentation/operators/taxonomy.md",
    "documentation/operators/ddc_transitions.md",
    "documentation/operators/operad_composition.md",
    "documentation/operators/prompt_families.md",
    # Epistemic Immune System Track (M2)
    "documentation/EIS/overview.md",
    "documentation/EIS/four_gate_protocol.md",
    "documentation/EIS/antibodies.md",
    "documentation/EIS/danger_gating.md",
    # Prompt Sieve Track (M3)
    "documentation/P_sieve/seed_ingestion.md",
    "documentation/P_sieve/nested_prompts.md",
    "documentation/P_sieve/family_dag.md",
    "documentation/P_sieve/evolution_tracking.md",
    # Workflows Track (M4)
    "documentation/workflows/README.md",
    "documentation/workflows/canonical_pipeline.md",
    "documentation/workflows/pfp_lab_governor.md",
    *[f"documentation/workflows/wf{i:04d}.md" for i in range(1, 50)],
    # Anomalon Integration Track (M5)
    "documentation/anomalon/omega_engine_pfp.md",
    "documentation/anomalon/operads_crates.md",
    "documentation/anomalon/epistemic_immune.md",
    "documentation/anomalon/prompt_civilization.md",
    "documentation/anomalon/symbol_game.md",
]

FORBIDDEN_HYPE_WORDS: frozenset[str] = frozenset({
    "proves",
    "guarantees",
    "mathematically verifies",
    "fundamentally",
    "true intelligence",
    "impossible",
    "universal",
    "flawless",
    "perfectly",
    "clearly",
    "obviously",
    "simply",
    "merely",
    "weaponized",
})


class CodebaseIndex(NamedTuple):
    """Indexed ground-truth inventory of files, directories, and crates across repositories."""
    exact_paths: frozenset[str]
    filenames: frozenset[str]
    crate_names: frozenset[str]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the absolute path to the proposal_fidelity_protocol_pfp repository root."""
    return PFP_REPO_ROOT


@pytest.fixture(scope="session")
def anomalon_root() -> Path:
    """Return the absolute path to the sibling anomalon repository root."""
    return ANOMALON_REPO_ROOT


@pytest.fixture(scope="session")
def docs_dir() -> Path:
    """Return the path to the documentation deliverables directory."""
    return DOCUMENTATION_DIR


@pytest.fixture(scope="session")
def all_doc_files(docs_dir: Path) -> List[Path]:
    """Return a list of all markdown files discovered in documentation/."""
    if not docs_dir.exists():
        return []
    return sorted(docs_dir.rglob("*.md"))


@pytest.fixture(scope="session")
def workflow_dag() -> Dict[str, Any]:
    """Load and parse the workflow DAG specification JSON."""
    if not WORKFLOW_DAG_PATH.exists():
        pytest.fail(f"Required workflow DAG file missing at {WORKFLOW_DAG_PATH}")
    with open(WORKFLOW_DAG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def codebase_index(repo_root: Path, anomalon_root: Path) -> CodebaseIndex:
    """Build a fast session-level index of source files and crates across PFP and Anomalon."""
    exact_paths: Set[str] = set()
    filenames: Set[str] = set()
    crate_names: Set[str] = set()

    # Index Rust crates in PFP
    pfp_rust = repo_root / "code" / "rust"
    if pfp_rust.is_dir():
        for item in pfp_rust.iterdir():
            if item.is_dir() and item.name not in ("target", ".cargo"):
                crate_names.add(item.name.lower())

    # Index Rust crates in Anomalon
    anom_rust = anomalon_root / "omega_engine" / "crates_rs"
    if anom_rust.is_dir():
        for item in anom_rust.iterdir():
            if item.is_dir() and item.name not in ("target", ".cargo"):
                crate_names.add(item.name.lower())

    # Key source search trees
    source_subtrees = [
        (repo_root, repo_root / "code" / "rust"),
        (repo_root, repo_root / "pfp"),
        (repo_root, repo_root / "pfp_lab"),
        (repo_root, repo_root / "eis"),
        (repo_root, repo_root / "operads"),
        (repo_root, repo_root / "workflows"),
        (anomalon_root, anomalon_root / "omega_engine_pfp"),
        (anomalon_root, anomalon_root / "omega_engine" / "crates_rs"),
    ]

    for base_root, target_dir in source_subtrees:
        if not target_dir.exists():
            continue
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in ("target", "__pycache__", ".git", ".pytest_cache")]
            rel_dir = Path(root).relative_to(base_root).as_posix().lower()
            exact_paths.add(rel_dir)
            for f in files:
                filenames.add(f.lower())
                exact_paths.add(f"{rel_dir}/{f.lower()}")

    return CodebaseIndex(
        exact_paths=frozenset(exact_paths),
        filenames=frozenset(filenames),
        crate_names=frozenset(crate_names),
    )
