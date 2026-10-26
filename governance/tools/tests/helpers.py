"""Helpers for the governance tool tests: hashing, git and valid records.

AuthorityEffect: None.
Contract: urn:pfp-governance:tests:helpers:v1
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=root, check=True, capture_output=True
    )


def records_for(root: Path, path: str, **score_changes: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """A valid contract and a valid L4C score for ``path`` with optional overrides."""
    language = "C#" if path.endswith(".cs") else "Python"
    artifact = {"path": path, "language": language, "sha256": digest(root / path)}
    evidence = root / "governance" / "evidence" / "ok.log"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("passed\n", encoding="utf-8")
    contract = {
        "AuthorityEffect": "None",
        "artifact": artifact,
        "contract_urn": "urn:test:mod:v1",
        "symbols": ["VALUE"],
        "owned_invariants": ["VALUE is 1"],
        "boundaries": [],
    }
    score: dict[str, Any] = {
        "schema_version": "2.0.0",
        "AuthorityEffect": "None",
        "artifact": artifact,
        "profile": "Non-Numeric",
        "level": "L4",
        "level_basis": "test",
        "gates": {"G1": "C", "G2": "B", "G3": "C", "G4": "C", "G5": "A"},
        "basis": {gate: "reason" for gate in ("G1", "G2", "G3", "G4", "G5")},
        "composite_grade": "C",
        "score_token": "L4C",
        "is_complete": True,
        "grade_ceiling": "A",
        "evaluation_timestamp": "2026-10-26T00:00:00+00:00",
        "evidence": [{"path": "governance/evidence/ok.log", "sha256": digest(evidence)}],
    }
    score.update(score_changes)
    return contract, score


def write_records(root: Path, contract: dict[str, Any], score: dict[str, Any]) -> tuple[Path, Path]:
    contract_file, score_file = root / "contract.json", root / "score.json"
    contract_file.write_text(json.dumps(contract), encoding="utf-8")
    score_file.write_text(json.dumps(score), encoding="utf-8")
    return contract_file, score_file
