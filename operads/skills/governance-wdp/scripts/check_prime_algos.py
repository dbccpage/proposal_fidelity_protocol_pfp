#!/usr/bin/env python3
"""
check_prime_algos.py — Consolidated Governance Invariant Checker for Algorithm Prime Triad

Verifies against real crate and paper sources:
1. CONTINUATION_CONJUNCTS in oeprmalg2.rs has exactly nine entries.
2. The ALGOS paper's docs/residual_aware_can_continue.md specifies nine canonical conjuncts.
3. oeprmalg0_admission.rs exists.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".agents").is_dir() and (parent / "engine").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root from {current}")


def test_continuation_conjuncts_nine(repo_root: Path) -> list[str]:
    candidates = [
        repo_root
        / "engine"
        / "crates_rs"
        / "core_wdp"
        / "src"
        / "prime_algos"
        / "prime_algorithm_2.rs",
        repo_root
        / "engine"
        / "crates_rs"
        / "core_wdp"
        / "src"
        / "ddc"
        / "prime_algos_2.rs",
        repo_root
        / "engine"
        / "crates_rs"
        / "core_wdp"
        / "src"
        / "ddc"
        / "oeprmalg2.rs",
    ]
    prmalg2_path = next((p for p in candidates if p.is_file()), None)
    if not prmalg2_path:
        raise FileNotFoundError(f"Missing required file from candidates: {candidates}")

    text = prmalg2_path.read_text(encoding="utf-8")
    m = re.search(
        r"pub const CONTINUATION_CONJUNCTS:\s*\[&str;\s*(\d+)\]\s*=\s*\[(.*?)\];",
        text,
        re.DOTALL,
    )
    if not m:
        raise ValueError(f"Could not parse CONTINUATION_CONJUNCTS from {prmalg2_path}")

    declared_len = int(m.group(1))
    raw_entries = m.group(2)
    entries = [e.strip().strip('"') for e in raw_entries.split(",") if e.strip().strip('"')]

    assert declared_len == 9, (
        f"CONTINUATION_CONJUNCTS declared length is {declared_len}, expected 9"
    )
    assert len(entries) == 9, f"Parsed {len(entries)} entries in CONTINUATION_CONJUNCTS, expected 9"

    print(
        f"[PASS] continuation_conjuncts_nine: CONTINUATION_CONJUNCTS in {prmalg2_path.name} has {len(entries)} entries: {entries}"
    )
    return entries


def test_algos_doc_specifies_nine(repo_root: Path) -> None:
    candidate_paths = [
        repo_root
        / "atlas"
        / "coda_atlas"
        / "F004_papers" / "001_finite_obstruction_calculus"
        / "000_witnessed_difference_programme" / "docs" / "source_archive"
        / "prime_algorithm_package"
        / "docs"
        / "residual_aware_can_continue.md",
        repo_root
        / "research"
        / "prime_algos"
        / "docs"
        / "residual_aware_can_continue.md",
    ]
    doc_path = next((p for p in candidate_paths if p.is_file()), None)
    if doc_path is None:
        raise FileNotFoundError(f"Missing required file from candidates: {candidate_paths}")

    doc_text = doc_path.read_text(encoding="utf-8")
    assert "The Nine Canonical Conjuncts" in doc_text, (
        f"Expected section 'The Nine Canonical Conjuncts' in {doc_path}"
    )

    # Extract lines in section 1.1
    section_1_1 = doc_text.split("### 1.1 The Nine Canonical Conjuncts")[1].split("### 1.2")[0]
    canonical_items = [
        line.strip() for line in section_1_1.splitlines() if re.match(r"^\d+\.\s+", line.strip())
    ]
    assert len(canonical_items) == 9, (
        f"Expected 9 numbered canonical conjunct items in section 1.1 of {doc_path}, found {len(canonical_items)}"
    )

    print(
        f"[PASS] algos_doc_specifies_nine: {doc_path.name} specifies 9 canonical conjuncts in §1.1"
    )


def test_oeprmalg0_admission_exists(repo_root: Path) -> None:
    candidates = [
        repo_root
        / "engine"
        / "crates_rs"
        / "core_wdp"
        / "src"
        / "prime_algos"
        / "prime_algorithm_0_admission.rs",
        repo_root
        / "engine"
        / "crates_rs"
        / "core_wdp"
        / "src"
        / "ddc"
        / "prime_algos_0_admission.rs",
        repo_root
        / "engine"
        / "crates_rs"
        / "core_wdp"
        / "src"
        / "ddc"
        / "oeprmalg0_admission.rs",
    ]
    admission_path = next((p for p in candidates if p.is_file()), None)
    if not admission_path:
        raise FileNotFoundError(f"Missing required file from candidates: {candidates}")

    size = admission_path.stat().st_size
    assert size > 0, f"File {admission_path} is empty"

    print(f"[PASS] oeprmalg0_admission_exists: {admission_path.name} exists ({size} bytes)")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=== GOVERNANCE-PRIME-ALGOS INVARIANT CHECK ===")
    repo_root = find_repo_root()
    test_continuation_conjuncts_nine(repo_root)
    test_algos_doc_specifies_nine(repo_root)
    test_oeprmalg0_admission_exists(repo_root)
    print("-----------------------------------------------")
    print(
        "ALL CHECKS PASSED: Prime Algorithms governance invariants verified against real sources."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
