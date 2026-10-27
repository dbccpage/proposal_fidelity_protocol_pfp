#!/usr/bin/env python3
"""Consolidated pipeline attestation and probe defect firewall linter.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path


def get_repo_root() -> Path:
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / ".git").exists() and (p / ".agents").exists():
            return p
    return Path(__file__).resolve().parents[4]


def check_pipeline_attestation(root: Path) -> int:
    errors = 0
    print("Checking pipeline attestation and probe firewall invariants...")

    # 1. Check for float tolerance violations in core guard implementations
    fda_core = (
        root
        / "atlas"
        / "coda_atlas"
        / "F004_papers" / "001_finite_obstruction_calculus" / "000_witnessed_difference_programme" / "docs" / "source_archive" / "coda_component_packages"
        / "fda"
        / "code"
        / "coda_fda_core.py"
    )
    if not fda_core.is_file():
        print(f"[ERROR] Required core FDA solver bridge missing: {fda_core}")
        errors += 1
    else:
        content = fda_core.read_text(encoding="utf-8")
        if "tol: float" in content or "tolerance: float" in content:
            print(
                "[ERROR] coda_fda_core.py: Found float tolerance in exact quotient guard interface"
            )
            errors += 1
        if "Fraction" not in content:
            print(
                "[ERROR] coda_fda_core.py: Missing exact rational Fraction usage in core solver bridge"
            )
            errors += 1

    # 2. Check for probe defect firewall tests
    coda_test = (
        root
        / "atlas"
        / "coda_atlas"
        / "F004_papers" / "001_finite_obstruction_calculus" / "000_witnessed_difference_programme" / "docs" / "source_archive" / "coda_component_packages"
        / "cs_q"
        / "code"
        / "tests"
        / "test_coda_cs_q.py"
    )
    if not coda_test.is_file():
        print(f"[ERROR] Required probe defect firewall test missing: {coda_test}")
        errors += 1
    else:
        content = coda_test.read_text(encoding="utf-8")
        if "STUCK" in content and "raise" not in content:
            print(f"[WARN] {coda_test.name}: Ensure STUCK does not launder probe errors")

    if errors == 0:
        print("[OK] Pipeline attestation invariants hold.")
        return 0
    else:
        print(f"[FAIL] Found {errors} attestation violations.")
        return 1


if __name__ == "__main__":
    sys.exit(check_pipeline_attestation(get_repo_root()))
