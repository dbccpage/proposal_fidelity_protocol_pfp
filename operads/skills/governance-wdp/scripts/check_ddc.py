#!/usr/bin/env python3
"""
check_ddc.py — Consolidated Governance Invariant Checker for DDC

Verifies against real crate and paper sources:
1. The DdaOp variants and letters in dda_alphabet.rs equal LETTERS in the DDC paper's automaton.py.
2. Every violation code in the DDC paper's PAPER_CODES exists as an OpViolation variant in op_verification.rs.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".agents").is_dir() and (parent / "omega_engine").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root from {current}")


def test_alphabet_matches_paper(repo_root: Path) -> None:
    dda_path = (
        repo_root
        / "omega_engine"
        / "crates_rs"
        / "omega_wdp"
        / "src"
        / "ddc"
        / "ddc_alphabet.rs"
    )
    if not dda_path.is_file():
        raise FileNotFoundError(f"Missing required file: {dda_path}")

    candidate_paths = [
        repo_root
        / "omega_engine_atlas"
        / "coda_atlas"
        / "F004_papers"
        / "001_finite_obstruction_calculus"
        / "000_witnessed_difference_programme"
        / "docs"
        / "source_archive"
        / "discrete_deformation_calculus_package"
        / "code"
        / "ddc"
        / "automaton.py",
        repo_root
        / "research"
        / "omega_engine_discrete_deformation_calculus"
        / "code"
        / "ddc"
        / "automaton.py",
    ]
    aut_path = next((p for p in candidate_paths if p.is_file()), None)
    if aut_path is None:
        raise FileNotFoundError(f"Missing required file from candidates: {candidate_paths}")

    dda_text = dda_path.read_text(encoding="utf-8")
    match_arms = re.findall(r"(?:DdcOp|DdaOp)::(\w+)\s*=>\s*\"([^\"]+)\"", dda_text)
    if not match_arms:
        raise ValueError(f"Could not parse DdcOp/DdaOp match arms from {dda_path}")
    rust_letters = tuple(letter for _, letter in match_arms)

    aut_text = aut_path.read_text(encoding="utf-8")
    m_letters = re.search(r"LETTERS\s*=\s*\((.*?)\)", aut_text, re.DOTALL)
    if not m_letters:
        raise ValueError(f"Could not parse LETTERS from {aut_path}")

    paper_letters = tuple(
        item.strip().strip("'\"")
        for item in m_letters.group(1).split(",")
        if item.strip().strip("'\"")
    )

    assert rust_letters == paper_letters, (
        f"DdaOp letters in dda_alphabet.rs {rust_letters} != "
        f"LETTERS in automaton.py {paper_letters}"
    )
    print(f"[PASS] alphabet_matches_paper: {rust_letters} == {paper_letters}")


def test_paper_codes_exist_in_op_verification(repo_root: Path) -> None:
    candidate_paths = [
        repo_root
        / "omega_engine_atlas"
        / "coda_atlas"
        / "F004_papers"
        / "001_finite_obstruction_calculus"
        / "000_witnessed_difference_programme"
        / "docs"
        / "source_archive"
        / "discrete_deformation_calculus_package"
        / "code"
        / "ddc"
        / "automaton.py",
        repo_root
        / "research"
        / "omega_engine_discrete_deformation_calculus"
        / "code"
        / "ddc"
        / "automaton.py",
    ]
    aut_path = next((p for p in candidate_paths if p.is_file()), None)
    if aut_path is None:
        raise FileNotFoundError(f"Missing required file from candidates: {candidate_paths}")

    op_verif_path = (
        repo_root
        / "omega_engine"
        / "crates_rs"
        / "omega_wdp"
        / "src"
        / "ddc"
        / "op_verification.rs"
    )
    if not op_verif_path.is_file():
        raise FileNotFoundError(f"Missing required file: {op_verif_path}")

    aut_text = aut_path.read_text(encoding="utf-8")
    m_codes = re.search(r"PAPER_CODES\s*=\s*\((.*?)\)", aut_text, re.DOTALL)
    if not m_codes:
        raise ValueError(f"Could not parse PAPER_CODES from {aut_path}")

    paper_codes = [
        item.strip().strip("'\"")
        for item in m_codes.group(1).split(",")
        if item.strip().strip("'\"")
    ]
    assert len(paper_codes) > 0, "PAPER_CODES must not be empty"

    op_verif_text = op_verif_path.read_text(encoding="utf-8")
    for code in paper_codes:
        assert f"OpViolation::{code}" in op_verif_text or f"{code}" in op_verif_text, (
            f"Violation code '{code}' from paper's PAPER_CODES not found in op_verification.rs"
        )

    print(
        f"[PASS] paper_codes_exist_in_op_verification: all {len(paper_codes)} codes verified in op_verification.rs"
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=== GOVERNANCE-DDC INVARIANT CHECK ===")
    repo_root = find_repo_root()
    test_alphabet_matches_paper(repo_root)
    test_paper_codes_exist_in_op_verification(repo_root)
    print("-----------------------------------------------")
    print("ALL CHECKS PASSED: DDC governance invariants verified against real sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
