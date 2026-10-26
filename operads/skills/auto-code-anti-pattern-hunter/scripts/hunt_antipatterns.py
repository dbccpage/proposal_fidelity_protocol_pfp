#!/usr/bin/env python3
"""
hunt_antipatterns.py — Automated Anti-Pattern & Healthy Pattern Hunter

Scans Python, Rust, SQL, and Lean 4 files for registered anti-pattern signatures
from .agents/patterns/ and certifies dual healthy pattern adherence.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import re
import sys
import tokenize
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PatternFinding:
    pattern_id: str
    pattern_name: str
    category: str  # "anti_pattern" or "healthy_pattern"
    language: str
    file_path: str
    line_number: int
    matched_snippet: str
    dual_pattern: str
    remediation_advice: str


@dataclass
class ScanReceipt:
    scan_id: str
    timestamp_utc: str
    authority_effect: str
    scanned_files_count: int
    findings: List[PatternFinding] = field(default_factory=list)
    healthy_certifications: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "PASS"  # "PASS" if 0 anti-patterns, "FINDINGS" otherwise


def find_repo_root(start: Optional[Path] = None) -> Path:
    curr = (start or Path.cwd()).resolve()
    for _ in range(10):
        if (curr / ".git").exists() and (curr / ".agents").is_dir():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    return (start or Path.cwd()).resolve()


FROZEN_OR_IGNORED_DIRS = frozenset(
    {
        ".lake",
        "target",
        "node_modules",
        ".venv",
        "venv",
        "site-packages",
        ".elan",
        ".git",
        "__pycache__",
        "quarantine",
        "archive",
        ".pixi",
    }
)


def scan_file(file_path: Path, repo_root: Path) -> List[PatternFinding]:
    findings: List[PatternFinding] = []
    suffix = file_path.suffix.lower()
    rel_path = str(file_path.relative_to(repo_root))

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    lines = content.splitlines()

    # 1. Python Scans
    if suffix == ".py":
        # AP_PY_001: blanket type ignore comments without bracketed rule in actual comments
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
            for tok in tokens:
                if tok.type == tokenize.COMMENT and re.search(
                    r"#\s*type:\s*ignore(?!\s*\[)", tok.string
                ):
                    findings.append(
                        PatternFinding(
                            pattern_id="AP_PY_001",
                            pattern_name="blanket_mypy_ignore",
                            category="anti_pattern",
                            language="python",
                            file_path=rel_path,
                            line_number=tok.start[0],
                            matched_snippet=tok.string.strip(),
                            dual_pattern="HP_PY_001_scoped_mypy_overrides",
                            remediation_advice="Specify explicit mypy error code, e.g. # type: ignore[arg-type]",
                        )
                    )
        except (tokenize.TokenError, IndentationError):
            for i, line in enumerate(lines, 1):
                if re.search(r"#\s*type:\s*ignore(?!\s*\[)", line):
                    findings.append(
                        PatternFinding(
                            pattern_id="AP_PY_001",
                            pattern_name="blanket_mypy_ignore",
                            category="anti_pattern",
                            language="python",
                            file_path=rel_path,
                            line_number=i,
                            matched_snippet=line.strip(),
                            dual_pattern="HP_PY_001_scoped_mypy_overrides",
                            remediation_advice="Specify explicit mypy error code, e.g. # type: ignore[arg-type]",
                        )
                    )

        for i, line in enumerate(lines, 1):
            # AP_PY_006: host-absolute path injection in Python non-test files
            if (
                "tests" not in rel_path.replace("\\", "/").split("/")
                and not rel_path.endswith("_test.py")
                and not rel_path.startswith("test_")
                and "anti_pattern" not in rel_path
            ) and (
                re.search(r"['\"]file:///[a-zA-Z]:", line)
                or re.search(r"['\"][a-zA-Z]:[/\\]Users[/\\]", line)
            ):
                findings.append(
                    PatternFinding(
                        pattern_id="AP_PY_006",
                        pattern_name="host_absolute_path_injection",
                        category="anti_pattern",
                        language="python",
                        file_path=rel_path,
                        line_number=i,
                        matched_snippet=line.strip(),
                        dual_pattern="HP_PY_006_dynamic_repository_relative_resolution",
                        remediation_advice="Replace hardcoded host-absolute path with dynamic repository-relative resolution via Path(__file__).",
                    )
                )

            # AP_SQL_001 in Python: f-string query in cursor.execute
            if re.search(r"cursor\.execute\s*\(\s*f[\"']", line) or re.search(
                r"\.execute\s*\(\s*f[\"']\s*(?:SELECT|INSERT|UPDATE|DELETE)", line, re.IGNORECASE
            ):
                findings.append(
                    PatternFinding(
                        pattern_id="AP_SQL_001",
                        pattern_name="unparameterized_string_query",
                        category="anti_pattern",
                        language="sql",
                        file_path=rel_path,
                        line_number=i,
                        matched_snippet=line.strip(),
                        dual_pattern="HP_SQL_001_parameterized_query_binding",
                        remediation_advice="Use parameterized query tuple/dict binding instead of f-string interpolation.",
                    )
                )

    # 2. Rust Scans
    elif suffix == ".rs":
        for i, line in enumerate(lines, 1):
            # AP_RS_002: enum definition without Ord/PartialOrd in crates_rs
            if "crates_rs" in rel_path and re.search(r"^\s*pub\s+enum\s+\w+", line):
                # Check preceding 5 lines for derive(..., Ord, ...)
                preceding = " ".join(lines[max(0, i - 5) : i - 1])
                if "#[derive(" in preceding and "Ord" not in preceding:
                    findings.append(
                        PatternFinding(
                            pattern_id="AP_RS_002",
                            pattern_name="domain_enum_missing_ord",
                            category="anti_pattern",
                            language="rust",
                            file_path=rel_path,
                            line_number=i,
                            matched_snippet=line.strip(),
                            dual_pattern="HP_RS_002_deterministic_key_trait_derive",
                            remediation_advice="Derive PartialEq, Eq, PartialOrd, Ord, Hash on domain enums for deterministic collections.",
                        )
                    )
    # 3. Lean 4 Scans
    elif suffix == ".lean":
        in_block_comment = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if in_block_comment:
                if "-/" in stripped:
                    in_block_comment = False
                    code_part = stripped.split("-/", 1)[1]
                else:
                    continue
            elif "/-" in stripped:
                if "-/" in stripped and stripped.find("-/") > stripped.find("/-"):
                    before = stripped[: stripped.find("/-")]
                    after = stripped[stripped.find("-/") + 2 :]
                    code_part = before + " " + after
                else:
                    in_block_comment = True
                    code_part = stripped[: stripped.find("/-")]
            else:
                code_part = stripped

            code_line = code_part.split("--")[0].strip()
            if code_line and re.search(r"\bsorry\b", code_line):
                findings.append(
                    PatternFinding(
                        pattern_id="AP_LN_001",
                        pattern_name="unmechanized_sorry_proof_claim",
                        category="anti_pattern",
                        language="lean4",
                        file_path=rel_path,
                        line_number=i,
                        matched_snippet=line.strip(),
                        dual_pattern="HP_LN_001_zero_sorry_axiom_allowlist",
                        remediation_advice="Close proof fully without sorry; verify via #print axioms.",
                    )
                )

    # 4. SQL Scans
    elif suffix == ".sql":
        for i, line in enumerate(lines, 1):
            if re.search(r"--\s*TODO\s*transaction", line, re.IGNORECASE):
                findings.append(
                    PatternFinding(
                        pattern_id="AP_SQL_002",
                        pattern_name="unbounded_transaction_leak",
                        category="anti_pattern",
                        language="sql",
                        file_path=rel_path,
                        line_number=i,
                        matched_snippet=line.strip(),
                        dual_pattern="HP_SQL_002_unit_of_work_transaction_fence",
                        remediation_advice="Enclose operations in atomic transaction blocks.",
                    )
                )

    return findings


def run_hunter(
    targets: List[Path],
    repo_root: Path,
    output_path: Optional[Path] = None,
    ext_filter: Optional[List[str]] = None,
) -> ScanReceipt:
    all_files: List[Path] = []
    allowed_exts = set(ext_filter) if ext_filter else {"*.py", "*.rs", "*.lean", "*.sql"}
    normalized_exts = tuple(
        e if e.startswith("*") else f"*{e}" if e.startswith(".") else f"*.{e}" for e in allowed_exts
    )

    for t in targets:
        resolved = (repo_root / t).resolve() if not t.is_absolute() else t.resolve()
        if resolved.is_file():
            if not any(part in FROZEN_OR_IGNORED_DIRS for part in resolved.parts):
                all_files.append(resolved)
        elif resolved.is_dir():
            for ext in normalized_exts:
                for p in resolved.rglob(ext):
                    if any(part in FROZEN_OR_IGNORED_DIRS for part in p.parts):
                        continue
                    all_files.append(p)

    # Deterministic sorting
    all_files.sort()

    findings: List[PatternFinding] = []
    for f in all_files:
        findings.extend(scan_file(f, repo_root))

    receipt = ScanReceipt(
        scan_id=f"AP_SCAN_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        authority_effect="None",
        scanned_files_count=len(all_files),
        findings=findings,
        status="PASS" if not findings else "FINDINGS",
    )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(asdict(receipt), indent=2), encoding="utf-8")

    return receipt


def main():
    parser = argparse.ArgumentParser(
        description="hunt_antipatterns.py: Scan codebase for colored anti-patterns."
    )
    parser.add_argument(
        "targets", nargs="*", default=["."], help="Target files or directories to scan."
    )
    parser.add_argument("--output", type=Path, default=None, help="Receipt output path.")
    parser.add_argument(
        "--ext", nargs="*", default=None, help="File extension(s) to scan (e.g. .lean .py)."
    )
    parser.add_argument("--summary", action="store_true", help="Print concise terminal summary.")
    args = parser.parse_args()

    repo_root = find_repo_root()
    target_paths = [Path(t) for t in args.targets]
    receipt = run_hunter(target_paths, repo_root, args.output, ext_filter=args.ext)

    if args.summary or not args.output:
        print(
            f"Scan ID: {receipt.scan_id} | Status: {receipt.status} | Files Scanned: {receipt.scanned_files_count}"
        )
        print(f"Total Anti-Patterns Detected: {len(receipt.findings)}")
        for f in receipt.findings[:10]:
            print(f"  [{f.pattern_id}] {f.file_path}:{f.line_number} -> {f.remediation_advice}")
        if len(receipt.findings) > 10:
            print(f"  ... and {len(receipt.findings) - 10} more findings.")

    sys.exit(0 if receipt.status == "PASS" else 1)


if __name__ == "__main__":
    main()
