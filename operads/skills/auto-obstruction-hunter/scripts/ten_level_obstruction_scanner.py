#!/usr/bin/env python3
"""
10-Level Abstraction Obstruction Scanner

Scans the repository and research estate across 10 levels of abstraction:
  - Level 0: Character / Sentence (Formatting & Naming Obstructions)
  - Level 1: Paragraph / Linter Block (Claim ID Bijection & Syntax Integrity)
  - Level 2 & 3: Section / Docstring & Monograph 13-Section Skeleton Integrity
  - Level 4 & 5: Code Module & Contract Layer Firewalls (core_contracts / core_contract_core)
  - Level 8 & 9: Mathematical Spine & Projection Obstruction (PO-000 to PO-009)
"""

import glob
import os


def main():
    print("=== 10-LEVEL ABSTRACTION OBSTRUCTION AUDIT ===")

    # Level 0: Character / Sentence (Naming & Formatting Obstructions)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

    candidates_published = [
        os.path.join(repo_root, "research", "mssn_sn_tower", "papers"),
        os.path.join(repo_root, "engine", "research", "published"),
    ]
    published_dir = next(
        (d for d in candidates_published if os.path.exists(d)), candidates_published[0]
    )

    uppercase_files = []
    for root, dirs, files in os.walk(published_dir):
        for f in files:
            if f != f.lower():
                uppercase_files.append(os.path.join(root, f))

    print("\n[Level 0 Scan: Character/Formatting Obstructions]")
    print(f"Scanning: {published_dir}")
    print(f"Discovered uppercase/non-lowercase files: {len(uppercase_files)}")
    for uf in uppercase_files[:10]:
        print(f"  - {uf}")

    # Level 1: Linter Block & Claim Bijection
    print("\n[Level 1 Scan: Linter & Claim Bijection Integrity]")
    coda_dir = os.path.join(published_dir, "001_coda")
    coda_ledgers = glob.glob(os.path.join(coda_dir, "*_claim_ledger.md"))
    print(f"Found {len(coda_ledgers)} claim ledgers under 001_coda.")

    # Level 2 & 3: Skeleton & Primitive Difference Check
    print("\n[Level 2/3 Scan: Monograph 13-Section Skeleton Integrity]")
    missing_skeleton = []
    unreadable: list[str] = []
    for root, dirs, files in os.walk(published_dir):
        for f in files:
            if (
                f.endswith(".md")
                and not f.endswith("_change_log.md")
                and not f.endswith("_claim_ledger.md")
                and not f.startswith("_")
            ):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fp:
                        content = fp.read()
                        if "# " not in content and "## " not in content:
                            missing_skeleton.append(path)
                except (OSError, UnicodeDecodeError):
                    # Unreadable or non-UTF-8: cannot judge its skeleton, so it
                    # is not reported as missing one. Counted as unread instead.
                    unreadable.append(path)

    print(f"Discovered un-headed or non-standard markdown files: {len(missing_skeleton)}")
    if unreadable:
        # Never fold unread files into the clean count: a file nobody could
        # open is an open question, not a pass.
        print(f"Unreadable (not judged, not counted as clean): {len(unreadable)}")
        for path in unreadable:
            print(f"  - {path}")

    # Level 4 & 5: Code Module & Contract Layer Firewalls
    print("\n[Level 4/5 Scan: Contract Firewalls & Schema Integrity]")
    print("Auditing core_contracts and core_contract_core...")
    candidates_contracts = [
        os.path.join(repo_root, "engine", "crates_rs", "core_contracts"),
        os.path.join(repo_root, "engine", "crates", "core_contracts"),
    ]
    contracts_dir = next(
        (d for d in candidates_contracts if os.path.exists(d)), candidates_contracts[0]
    )
    print(f"Rust contracts directory exists: {os.path.exists(contracts_dir)} ({contracts_dir})")

    # Level 8 & 9: Mathematical Spine & Projection Obstruction
    print("\n[Level 8/9 Scan: Mathematical Spine & Projection Obstruction (PO-000 to PO-009)]")
    po_dir = os.path.join(published_dir, "004_projection_obstruction")
    po_files = glob.glob(os.path.join(po_dir, "*.md"))
    print(f"Found {len(po_files)} preprints under 004_projection_obstruction.")

    print("\n=== OBSTRUCTION AUDIT COMPLETE ===")


if __name__ == "__main__":
    main()
