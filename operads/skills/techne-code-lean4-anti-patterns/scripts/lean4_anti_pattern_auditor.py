"""Lean 4 anti-pattern auditor.

Checks the admitted catalog at operads/patterns/anti/lean4/:
  AP_LN_001 sorry outside comments
  AP_LN_002 lake build or lake update in a shell script with no lake exe cache get
  AP_LN_003 thermodynamic_limit theorem line with no finite envelope word

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SKIP_DIRS = frozenset(
    {
        ".git",
        ".lake",
        ".venv",
        "venv",
        "target",
        "node_modules",
        "__pycache__",
        "quarantine",
        "archive",
        "library",
    }
)
SHELL_SUFFIXES = {".ps1", ".sh", ".bat", ".cmd"}
LAKE_CMD = re.compile(r"^\s*lake\s+(build|update)\b")
THEOREM_LIMIT = re.compile(r"\btheorem\b.*thermodynamic_limit\b")
FINITE_ENVELOPE = re.compile(r"\b(finite|envelope|residual)\b")


def _walk(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS or part.startswith(".") for part in path.parts):
            continue
        yield path


def _lean_code(text: str) -> List[tuple[int, str]]:
    """Return (line_number, code) with line and block comments removed."""
    rows: List[tuple[int, str]] = []
    in_block = False
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if in_block:
            if "-/" in stripped:
                in_block = False
                code = stripped.split("-/", 1)[1]
            else:
                continue
        elif "/-" in stripped:
            if "-/" in stripped and stripped.find("-/") > stripped.find("/-"):
                before = stripped[: stripped.find("/-")]
                after = stripped[stripped.find("-/") + 2 :]
                code = before + " " + after
            else:
                in_block = True
                code = stripped[: stripped.find("/-")]
        else:
            code = stripped
        rows.append((number, code.split("--", 1)[0].strip()))
    return rows


def audit(root: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for path in _walk(root):
        suffix = path.suffix.lower()
        if suffix == ".lean":
            text = path.read_text(encoding="utf-8", errors="replace")
            for number, code in _lean_code(text):
                if re.search(r"\bsorry\b", code):
                    findings.append(
                        {
                            "id": "AP_LN_001",
                            "file": path.as_posix(),
                            "line": number,
                            "severity": "BLOCKER",
                            "anti_pattern": "unmechanized_sorry_proof_claim",
                            "repair": "Remove sorry and check the axiom list.",
                        }
                    )
                if THEOREM_LIMIT.search(code) and not FINITE_ENVELOPE.search(code):
                    findings.append(
                        {
                            "id": "AP_LN_003",
                            "file": path.as_posix(),
                            "line": number,
                            "severity": "MAJOR",
                            "anti_pattern": "unhedged_thermodynamic_limit_assertion",
                            "repair": "Name the finite envelope or residual on the theorem line.",
                        }
                    )
        elif suffix in SHELL_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="replace")
            if "lake exe cache get" in text:
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if LAKE_CMD.search(line):
                    findings.append(
                        {
                            "id": "AP_LN_002",
                            "file": path.as_posix(),
                            "line": number,
                            "severity": "MAJOR",
                            "anti_pattern": "unconstrained_lake_mathlib_rebuild",
                            "repair": "Run lake exe cache get before lake build or lake update.",
                        }
                    )
                    break
    return findings


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Lean 4 anti-pattern auditor")
    parser.add_argument("--path", default=".", help="File or directory to audit")
    parser.add_argument("--report-out", default=None, help="JSON receipt path")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when any finding is present",
    )
    args = parser.parse_args(argv)
    target = Path(args.path)
    if not target.exists():
        print(f"Target path does not exist: {target}", file=sys.stderr)
        return 2
    findings = audit(target)
    payload = {
        "authority_effect": "None",
        "audited_path": str(target),
        "total_findings": len(findings),
        "findings": findings,
    }
    if args.report_out:
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Lean 4 anti-pattern findings: {len(findings)}")
    if args.check and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
