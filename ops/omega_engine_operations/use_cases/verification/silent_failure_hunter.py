"""Silent Failure Hunter: detects swallowed exceptions and unhandled error fall-throughs.

Provides scoped AST and textual diagnostics, not control-flow or type proofs.
Rust regular expressions and Python unwrap warnings can produce false positives.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

AUTHORITY_EFFECT_NONE = "None"


@dataclass(frozen=True)
class SilentFailureFinding:
    rule_id: str
    file_path: str
    line_number: int
    column_number: int
    message: str
    snippet: str
    severity: str = "ERROR"
    authority_effect: str = AUTHORITY_EFFECT_NONE


class PythonSilentFailureVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_lines: list[str]) -> None:
        self.file_path = file_path
        self.source_lines = source_lines
        self.findings: list[SilentFailureFinding] = []

    def _get_snippet(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""

    def visit_Try(self, node: ast.Try) -> None:
        for handler in node.handlers:
            # 1. Bare except:
            if handler.type is None:
                self.findings.append(
                    SilentFailureFinding(
                        rule_id="SFH-PY-001",
                        file_path=self.file_path,
                        line_number=handler.lineno,
                        column_number=handler.col_offset,
                        message="Bare 'except:' statement swallows all exceptions including system exits.",
                        snippet=self._get_snippet(handler.lineno),
                    )
                )

            # 2. Swallowed exception with only 'pass' or Ellipsis
            body_statements = handler.body
            if len(body_statements) == 1:
                stmt = body_statements[0]
                if isinstance(stmt, ast.Pass) or (
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and stmt.value.value is ...
                ):
                    self.findings.append(
                        SilentFailureFinding(
                            rule_id="SFH-PY-002",
                            file_path=self.file_path,
                            line_number=handler.lineno,
                            column_number=handler.col_offset,
                            message=f"Exception handler for '{ast.unparse(handler.type) if handler.type else 'all'}' "
                            f"silently swallows failure with bare pass/ellipsis.",
                            snippet=self._get_snippet(handler.lineno),
                        )
                    )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # 3. Detect bare unwrap() without prior is_ok check in non-test code
        if isinstance(node.func, ast.Attribute) and node.func.attr == "unwrap":
            path_obj = Path(self.file_path)
            is_test_file = (
                path_obj.name.startswith("test_")
                or path_obj.name.endswith("_test.py")
                or "tests" in path_obj.parts
            )
            if not is_test_file:
                self.findings.append(
                    SilentFailureFinding(
                        rule_id="SFH-PY-003",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        message="Direct '.unwrap()' call on Result monad in non-test source. "
                        "Check '.is_ok' / '.is_err' or propagate via Result[T, Refusal].",
                        snippet=self._get_snippet(node.lineno),
                        severity="WARNING",
                    )
                )
        self.generic_visit(node)


def scan_python_file(path: Path) -> list[SilentFailureFinding]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return [
            SilentFailureFinding(
                "SFH-INPUT-001", str(path), 1, 0, "Source unreadable; scan incomplete", ""
            )
        ]
    source_lines = content.splitlines()
    try:
        tree = ast.parse(content, filename=str(path))
    except SyntaxError as exc:
        return [
            SilentFailureFinding(
                "SFH-INPUT-002",
                str(path),
                exc.lineno or 1,
                0,
                "Source syntax invalid; scan incomplete",
                "",
            )
        ]

    visitor = PythonSilentFailureVisitor(str(path), source_lines)
    visitor.visit(tree)
    return visitor.findings


RUST_NAKED_UNWRAP_RE = re.compile(
    r"\b(\w+(?:\.[a-zA-Z0-9_]+)*)\.(?:unwrap|expect)\s*\(", re.MULTILINE
)
RUST_DISCARD_RESULT_RE = re.compile(r"^\s*let\s+_\s*=\s*(.*?);", re.MULTILINE)
RUST_EMPTY_ERR_MATCH_RE = re.compile(r"\bif\s+let\s+Err\([^)]*\)\s*=\s*.*?\{\s*\}", re.MULTILINE)


def scan_rust_file(path: Path) -> list[SilentFailureFinding]:
    findings: list[SilentFailureFinding] = []
    is_test = "tests" in path.parts or path.name.startswith("test_")
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return [
            SilentFailureFinding(
                "SFH-INPUT-001", str(path), 1, 0, "Source unreadable; scan incomplete", ""
            )
        ]

    lines = content.splitlines()

    if not is_test:
        for match in RUST_NAKED_UNWRAP_RE.finditer(content):
            start_pos = match.start()
            lineno = content.count("\n", 0, start_pos) + 1
            line = lines[lineno - 1] if lineno <= len(lines) else ""
            if line.strip().startswith("//") or "#[cfg(test)]" in content[:start_pos]:
                continue
            findings.append(
                SilentFailureFinding(
                    rule_id="SFH-RS-001",
                    file_path=str(path),
                    line_number=lineno,
                    column_number=match.start() - content.rfind("\n", 0, match.start()),
                    message="Naked .unwrap() or .expect() in non-test Rust source. Propagate error via '?' operator.",
                    snippet=line.strip(),
                    severity="WARNING",
                )
            )

    for match in RUST_EMPTY_ERR_MATCH_RE.finditer(content):
        start_pos = match.start()
        lineno = content.count("\n", 0, start_pos) + 1
        line = lines[lineno - 1] if lineno <= len(lines) else ""
        findings.append(
            SilentFailureFinding(
                rule_id="SFH-RS-002",
                file_path=str(path),
                line_number=lineno,
                column_number=match.start() - content.rfind("\n", 0, match.start()),
                message="Empty 'if let Err(...) = ... {}' block silently drops errors.",
                snippet=line.strip(),
                severity="ERROR",
            )
        )

    return findings


def scan_file(path: Path) -> list[SilentFailureFinding]:
    if path.suffix.lower() == ".py":
        return scan_python_file(path)
    if path.suffix.lower() == ".rs":
        return scan_rust_file(path)
    return []


def scan_directory(
    root: Path, extensions: Sequence[str] = (".py", ".rs")
) -> list[SilentFailureFinding]:
    findings: list[SilentFailureFinding] = []
    skip_dirs = {
        ".git",
        "__pycache__",
        "target",
        "node_modules",
        ".venv",
        "archive",
        "scratch",
    }
    root = root.resolve()
    for p in root.rglob("*"):
        relative = p.relative_to(root)
        if any(part in skip_dirs for part in relative.parts):
            continue
        if p.is_file() and p.suffix.lower() in extensions:
            findings.extend(scan_file(p))
    return findings


def run_silent_failure_hunt(
    target_paths: Sequence[str],
    json_output: bool = False,
) -> int:
    all_findings: list[SilentFailureFinding] = []
    for target in target_paths:
        p = Path(target).resolve()
        if p.is_file():
            all_findings.extend(scan_file(p))
        elif p.is_dir():
            all_findings.extend(scan_directory(p))
        else:
            all_findings.append(
                SilentFailureFinding(
                    "SFH-INPUT-000", str(p), 1, 0, "Target unavailable; scan incomplete", ""
                )
            )

    if json_output:
        report = {
            "authority_effect": AUTHORITY_EFFECT_NONE,
            "total_findings": len(all_findings),
            "findings": [asdict(f) for f in all_findings],
        }
        print(json.dumps(report, indent=2))
    else:
        if not all_findings:
            print(
                f"Silent Failure Hunter: no configured patterns found across {len(target_paths)} target(s)."
            )
            print(f"AuthorityEffect: {AUTHORITY_EFFECT_NONE}")
            return 0

        print(f"Silent Failure Hunter: {len(all_findings)} finding(s) detected:")
        for f in all_findings:
            print(f"[{f.rule_id}] {f.file_path}:{f.line_number}:{f.column_number} [{f.severity}]")
            print(f"  Message: {f.message}")
            if f.snippet:
                print(f"  Snippet: {f.snippet}")
        print(f"\nAuthorityEffect: {AUTHORITY_EFFECT_NONE}")

    errors = [f for f in all_findings if f.severity == "ERROR"]
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Hunt swallowed exceptions and unhandled error fall-throughs in Python and Rust."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to scan (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings as structured JSON.",
    )
    args = parser.parse_args()
    return run_silent_failure_hunt(args.paths, json_output=args.json)


if __name__ == "__main__":
    sys.exit(main())
