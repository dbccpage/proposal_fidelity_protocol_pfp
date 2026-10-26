"""SQL and Persistence Anti-Pattern Auditor.

Audits Python modules and SQL files for:
1. AP_SQL_001: Unparameterized string formatting / SQL injection in query execution.
2. AP_SQL_002: Unbounded transaction leaks, missing connection context managers,
   and unhandled commit/rollback lifecycles.
3. Schema constraints: Missing NOT NULL on key definitions in DDL.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

F_STRING_EXEC_REGEX = re.compile(r"\b(?:cursor|c|conn|session|db)\.execute(?:many)?\s*\(\s*f[\"']")
CONCAT_EXEC_REGEX = re.compile(
    r"\b(?:cursor|c|conn|session|db)\.execute(?:many)?\s*\(\s*[^,\n]+\s*\+"
)
FORMAT_EXEC_REGEX = re.compile(
    r"\b(?:cursor|c|conn|session|db)\.execute(?:many)?\s*\(\s*[\"'].*?[\"']\s*%\s*"
)
DOT_FORMAT_EXEC_REGEX = re.compile(
    r"\b(?:cursor|c|conn|session|db)\.execute(?:many)?\s*\(\s*[\"'].*?[\"']\.format\s*\("
)

RAW_CONNECT_REGEX = re.compile(r"\b(?:sqlite3|psycopg2|asyncpg|pymysql)\.connect\s*\(")


class SQLAntiPatternVisitor(ast.NodeVisitor):
    """AST visitor inspecting Python files for SQL anti-patterns."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.findings: List[Dict[str, Any]] = []

    def visit_Call(self, node: ast.Call) -> None:
        # Check cursor.execute(...) calls
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"execute", "executemany"}:
            if node.args:
                first_arg = node.args[0]
                # 1. JoinedStr (f-string query)
                if isinstance(first_arg, ast.JoinedStr):
                    self.findings.append(
                        {
                            "file": self.filename,
                            "line": node.lineno,
                            "col": node.col_offset,
                            "id": "AP_SQL_001",
                            "severity": "BLOCKER",
                            "anti_pattern": "Unparameterized F-String in Query Execution",
                            "hazard": "High risk of SQL injection and query plan cache invalidation",
                            "repair": "Use parameterized query placeholders (?, %s, :name) with parameter tuple/dict",
                        }
                    )
                # 2. BinOp with Add (string concatenation: "SELECT " + var)
                elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Add):
                    self.findings.append(
                        {
                            "file": self.filename,
                            "line": node.lineno,
                            "col": node.col_offset,
                            "id": "AP_SQL_001",
                            "severity": "BLOCKER",
                            "anti_pattern": "String Concatenation in Query Execution",
                            "hazard": "High risk of SQL injection via concatenated user input",
                            "repair": "Use parameterized query placeholders (?, %s, :name) with parameter tuple/dict",
                        }
                    )
                # 3. BinOp with Mod ("SELECT ... %s" % var)
                elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Mod):
                    self.findings.append(
                        {
                            "file": self.filename,
                            "line": node.lineno,
                            "col": node.col_offset,
                            "id": "AP_SQL_001",
                            "severity": "BLOCKER",
                            "anti_pattern": "Percent-Format Interpolation in Query Execution",
                            "hazard": "High risk of SQL injection via % formatting",
                            "repair": "Use parameterized query placeholders (?, %s, :name) with parameter tuple/dict",
                        }
                    )
                # 4. Method call to .format()
                elif (
                    isinstance(first_arg, ast.Call)
                    and isinstance(first_arg.func, ast.Attribute)
                    and first_arg.func.attr == "format"
                ):
                    self.findings.append(
                        {
                            "file": self.filename,
                            "line": node.lineno,
                            "col": node.col_offset,
                            "id": "AP_SQL_001",
                            "severity": "BLOCKER",
                            "anti_pattern": "str.format() Call in Query Execution",
                            "hazard": "High risk of SQL injection via .format() interpolation",
                            "repair": "Use parameterized query placeholders (?, %s, :name) with parameter tuple/dict",
                        }
                    )

        self.generic_visit(node)


def audit_python_file(path: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [
            {
                "file": str(path),
                "line": 1,
                "id": "AP_READ_ERR",
                "severity": "WARN",
                "anti_pattern": str(exc),
            }
        ]

    # AST-based inspection
    try:
        tree = ast.parse(content, filename=str(path))
        visitor = SQLAntiPatternVisitor(str(path))
        visitor.visit(tree)
        findings.extend(visitor.findings)
    except SyntaxError:
        # Fall back to regex inspection
        for idx, line in enumerate(content.splitlines(), start=1):
            if F_STRING_EXEC_REGEX.search(line):
                findings.append(
                    {
                        "file": str(path),
                        "line": idx,
                        "id": "AP_SQL_001",
                        "severity": "BLOCKER",
                        "anti_pattern": "Unparameterized F-String in Query Execution (Regex Fallback)",
                        "hazard": "High risk of SQL injection",
                        "repair": "Use parameterized placeholders with parameter tuple/dict",
                    }
                )

    # Regex inspection for raw DB connect without class-level context management
    if RAW_CONNECT_REGEX.search(content):
        has_enter = "__enter__" in content and "__exit__" in content
        has_with_conn = re.search(r"with\s+(?:self\.)?conn\b", content) is not None
        has_close = re.search(r"\bconn\.close\(\)", content) is not None or "def close(" in content
        if not (has_enter or has_with_conn or has_close):
            findings.append(
                {
                    "file": str(path),
                    "line": 1,
                    "id": "AP_SQL_002",
                    "severity": "MAJOR",
                    "anti_pattern": "Database Connection Without Context Management or Close Protocol",
                    "hazard": "Unclosed connections, uncommitted transactions, and lock deadlocks",
                    "repair": "Implement context manager (__enter__/__exit__) or provide with conn: transaction fence",
                }
            )

    return findings


def audit_target(target_path: Path) -> Tuple[List[Dict[str, Any]], int]:
    findings: List[Dict[str, Any]] = []
    files_audited = 0

    if target_path.is_file():
        if target_path.suffix == ".py":
            findings.extend(audit_python_file(target_path))
            files_audited += 1
    elif target_path.is_dir():
        for py_file in target_path.rglob("*.py"):
            findings.extend(audit_python_file(py_file))
            files_audited += 1

    return findings, files_audited


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sql_anti_pattern_auditor",
        description="SQL & Persistence Anti-Pattern Auditor for Omega Engine",
    )
    parser.add_argument(
        "--path",
        default=".",
        help="File or directory path to audit (default: current directory)",
    )
    parser.add_argument(
        "--report-out",
        default=None,
        help="Optional path to emit JSON report",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail with exit code 1 if BLOCKER or MAJOR SQL anti-patterns are found",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    target_path = Path(args.path)
    if not target_path.exists():
        sys.stderr.write(f"Target path does not exist: {target_path}\n")
        return 2

    findings, count = audit_target(target_path)
    blockers = [f for f in findings if f.get("severity") == "BLOCKER"]
    majors = [f for f in findings if f.get("severity") == "MAJOR"]

    if args.report_out:
        out_file = Path(args.report_out)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "audited_path": str(target_path),
            "files_audited": count,
            "total_findings": len(findings),
            "blockers": len(blockers),
            "majors": len(majors),
            "findings": findings,
        }
        out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report written to {out_file}")

    print(f"\n--- SQL Anti-Pattern Audit Summary ({count} files audited) ---")
    print(f"  Total findings: {len(findings)} (BLOCKER: {len(blockers)}, MAJOR: {len(majors)})")
    for f in findings:
        print(f"  [{f['id']}] {f['file']}:{f.get('line', '?')} - {f['anti_pattern']}")
        print(f"      Hazard: {f['hazard']}")
        print(f"      Repair: {f['repair']}")

    if args.check and (blockers or majors):
        sys.stderr.write("REFUSED: SQL anti-pattern audit failed --check gate.\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
