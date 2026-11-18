"""Python Code Anti-Pattern and Clean Pattern Auditor.

Audits Python modules, packages, and configuration files for:
1. AP_PY_001: Blanket mypy ignore (unscoped type: ignore without error codes)
   or global un-scoped ignore_missing_imports in configuration.
2. AP_PY_002: Array/Collection hash and equality asymmetry in value objects / frozen dataclasses.
3. AP_PY_003: Bare except clauses (bare 'except:' or 'except Exception: pass').
4. AP_PY_004: Unmanaged resource / file handle leaks (bare open() without context manager).
5. AP_PY_005: Mutable default arguments in functions or dataclasses.
6. AP_PY_006: Arrow Anti-Pattern / Deep Loop Nesting (depth >= 4 in domain/use_cases).
7. AP_PY_007: Domain Re-Export / Forwarder Shim (RULE_CLEAN_ARCH_NO_SHIMS_001).
8. AP_PY_008: Host I/O Leakage in Domain Objects (subprocess imports in domain).

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import sys
import tokenize
from pathlib import Path
from typing import Any, Dict, List, Set

BLANKET_TYPE_IGNORE_REGEX = re.compile(r"#\s*type:\s*ignore(?!\s*\[)")
SCOPED_TYPE_IGNORE_REGEX = re.compile(r"#\s*type:\s*ignore\s*\[([a-zA-Z0-9_,\s\-]+)\]")
GLOBAL_MYPY_IGNORE_REGEX = re.compile(
    r"^\s*ignore_missing_imports\s*=\s*(?:true|True)\b", re.MULTILINE
)


class PythonAntiPatternVisitor(ast.NodeVisitor):
    """AST visitor inspecting Python syntax trees for canonical anti-patterns."""

    def __init__(self, filename: str, source_lines: List[str]) -> None:
        self.filename = filename
        self.source_lines = source_lines
        self.findings: List[Dict[str, Any]] = []
        self._with_call_ids: Set[int] = set()
        self._loop_depth: int = 0

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                self._with_call_ids.add(id(item.context_expr))
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                self._with_call_ids.add(id(item.context_expr))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # AP_PY_004: Bare open() call not managed by a `with` statement
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            if id(node) not in self._with_call_ids:
                self.findings.append(
                    {
                        "file": self.filename,
                        "line": node.lineno,
                        "col": node.col_offset,
                        "id": "AP_PY_004",
                        "severity": "MAJOR",
                        "anti_pattern": "Unmanaged File Handle (bare open() without with-statement)",
                        "hazard": "Resource descriptor leak on failure or early exit",
                        "repair": "Wrap file opening in a 'with open(...) as handle:' context manager",
                    }
                )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_mutable_defaults(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_mutable_defaults(node)
        self.generic_visit(node)

    def _check_mutable_defaults(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # AP_PY_005: Mutable default arguments (def foo(x=[]))
        for default in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.findings.append(
                    {
                        "file": self.filename,
                        "line": default.lineno,
                        "col": default.col_offset,
                        "id": "AP_PY_005",
                        "severity": "MAJOR",
                        "anti_pattern": "Mutable Default Argument in Function Signature",
                        "hazard": "State leaks across calls causing non-deterministic mutations",
                        "repair": "Use None as default and initialize inside function body",
                    }
                )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        is_frozen_dataclass = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == "dataclass":
                pass
            elif isinstance(dec, ast.Call):
                func = dec.func
                if (isinstance(func, ast.Name) and func.id == "dataclass") or (
                    isinstance(func, ast.Attribute) and func.attr == "dataclass"
                ):
                    for kw in dec.keywords:
                        if (
                            kw.arg == "frozen"
                            and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True
                        ):
                            is_frozen_dataclass = True

        if is_frozen_dataclass:
            # Check for mutable fields like list, dict, np.ndarray without custom hash/eq
            has_custom_hash = any(
                isinstance(item, ast.FunctionDef) and item.name == "__hash__" for item in node.body
            )
            for item in node.body:
                if isinstance(item, ast.AnnAssign):
                    # Check mutable default in dataclass: field: list = []
                    if isinstance(item.value, (ast.List, ast.Dict, ast.Set)):
                        self.findings.append(
                            {
                                "file": self.filename,
                                "line": item.lineno,
                                "col": item.col_offset,
                                "id": "AP_PY_005",
                                "severity": "BLOCKER",
                                "anti_pattern": "Mutable Default Value in Dataclass Field",
                                "hazard": "Shared mutable state across dataclass instances",
                                "repair": "Use dataclasses.field(default_factory=list/dict)",
                            }
                        )
                    # AP_PY_002: Mutable collection in frozen dataclass without custom hash
                    if not has_custom_hash and isinstance(item.annotation, ast.Subscript):
                        target_name = ""
                        if isinstance(item.annotation.value, ast.Name):
                            target_name = item.annotation.value.id
                        if target_name in {"List", "Dict", "Set"}:
                            self.findings.append(
                                {
                                    "file": self.filename,
                                    "line": item.lineno,
                                    "col": item.col_offset,
                                    "id": "AP_PY_002",
                                    "severity": "MAJOR",
                                    "anti_pattern": "Array/Collection Hash & Equality Asymmetry in Frozen Dataclass",
                                    "hazard": "Frozen dataclass with mutable collection causes unhashable type errors or non-deterministic set membership",
                                    "repair": "Use immutable tuples (Sequence[...], Tuple[...]) or implement canonical __hash__ and __eq__",
                                }
                            )

        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        for handler in node.handlers:
            # AP_PY_003: Bare except: or except Exception: pass
            if handler.type is None:
                self.findings.append(
                    {
                        "file": self.filename,
                        "line": handler.lineno,
                        "col": handler.col_offset,
                        "id": "AP_PY_003",
                        "severity": "MAJOR",
                        "anti_pattern": "Bare 'except:' Clause",
                        "hazard": "Catches KeyboardInterrupt, SystemExit, and silences critical bugs",
                        "repair": "Catch specific exception classes (e.g. ValueError, OSError) or catch Exception with logging",
                    }
                )
            elif isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                    self.findings.append(
                        {
                            "file": self.filename,
                            "line": handler.lineno,
                            "col": handler.col_offset,
                            "id": "AP_PY_003",
                            "severity": "MAJOR",
                            "anti_pattern": "Silent 'except Exception: pass'",
                            "hazard": "Silences all exceptions without logging or recovery, masking system failures",
                            "repair": "Log the exception or handle typed refusal explicitly",
                        }
                    )
        self.generic_visit(node)

    def _visit_loop(self, node: ast.For | ast.AsyncFor | ast.While) -> None:
        self._loop_depth += 1
        norm_name = self.filename.replace("\\", "/")
        is_domain = "/domain/" in norm_name or "/use_cases/" in norm_name
        if self._loop_depth >= 4 and is_domain:
            self.findings.append(
                {
                    "file": self.filename,
                    "line": node.lineno,
                    "col": node.col_offset,
                    "id": "AP_PY_006",
                    "severity": "MAJOR",
                    "anti_pattern": f"Arrow Anti-Pattern / Deep Loop Nesting (depth={self._loop_depth})",
                    "hazard": "Exponential cyclomatic complexity, state-mutation opacity, and maintainability collapse",
                    "repair": "Decompose into named helper functions with early returns and guard clauses",
                }
            )
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_For(self, node: ast.For) -> None:
        self._visit_loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_loop(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_loop(node)

    def visit_Import(self, node: ast.Import) -> None:
        norm_name = self.filename.replace("\\", "/")
        if "/domain/" in norm_name:
            for alias in node.names:
                if alias.name == "subprocess":
                    self.findings.append(
                        {
                            "file": self.filename,
                            "line": node.lineno,
                            "col": node.col_offset,
                            "id": "AP_PY_008",
                            "severity": "BLOCKER",
                            "anti_pattern": "Host I/O Leakage in Domain Module (imports subprocess)",
                            "hazard": "Clean Architecture breach: domain objects must have zero host I/O or OS process spawning",
                            "repair": "Move subprocess logic to infrastructure adapter behind an abstract domain port",
                        }
                    )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        norm_name = self.filename.replace("\\", "/")
        if "/domain/" in norm_name and node.module == "subprocess":
            self.findings.append(
                {
                    "file": self.filename,
                    "line": node.lineno,
                    "col": node.col_offset,
                    "id": "AP_PY_008",
                    "severity": "BLOCKER",
                    "anti_pattern": "Host I/O Leakage in Domain Module (imports from subprocess)",
                    "hazard": "Clean Architecture breach: domain objects must have zero host I/O or OS process spawning",
                    "repair": "Move subprocess logic to infrastructure adapter behind an abstract domain port",
                }
            )
        self.generic_visit(node)


def audit_python_file(path: Path) -> List[Dict[str, Any]]:
    """Audits a single Python file for canonical anti-patterns."""
    findings: List[Dict[str, Any]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [
            {
                "file": str(path),
                "line": 1,
                "col": 0,
                "id": "AP_READ_ERR",
                "severity": "WARN",
                "anti_pattern": f"File read error: {exc}",
                "hazard": "Cannot audit file content",
                "repair": "Ensure valid UTF-8 encoding",
            }
        ]

    lines = content.splitlines()

    # Scan for AP_PY_007: Domain Re-Export / Forwarder Shim
    norm_path = path.as_posix()
    if "/domain/" in norm_path and "Canonical forwarder to" in content:
        findings.append(
            {
                "file": str(path),
                "line": 1,
                "col": 0,
                "id": "AP_PY_007",
                "severity": "MAJOR",
                "anti_pattern": "Domain Re-Export / Forwarder Shim",
                "hazard": "Leaves duplicate competing import paths and masks incomplete refactoring (RULE_CLEAN_ARCH_NO_SHIMS_001)",
                "repair": "Migrate all callers to import directly from the canonical sub-package and delete this shim file",
            }
        )

    # 1. Token-level scan for AP_PY_001 (Blanket mypy ignore in real comments)
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
        for tok in tokens:
            if tok.type == tokenize.COMMENT and BLANKET_TYPE_IGNORE_REGEX.search(tok.string):
                findings.append(
                    {
                        "file": str(path),
                        "line": tok.start[0],
                        "col": tok.start[1],
                        "id": "AP_PY_001",
                        "severity": "BLOCKER",
                        "anti_pattern": "Blanket Mypy Ignore (unscoped type: ignore)",
                        "hazard": "Silences all type errors on the line, hiding interface regressions and type erosion",
                        "repair": "Scope ignore to specific error code, e.g. # type: ignore[arg-type]",
                    }
                )
    except (tokenize.TokenError, IndentationError):
        for idx, line in enumerate(lines, start=1):
            if BLANKET_TYPE_IGNORE_REGEX.search(line):
                findings.append(
                    {
                        "file": str(path),
                        "line": idx,
                        "col": line.find("#"),
                        "id": "AP_PY_001",
                        "severity": "BLOCKER",
                        "anti_pattern": "Blanket Mypy Ignore (unscoped type: ignore)",
                        "hazard": "Silences all type errors on the line, hiding interface regressions and type erosion",
                        "repair": "Scope ignore to specific error code, e.g. # type: ignore[arg-type]",
                    }
                )

    # 2. AST-level inspection
    try:
        tree = ast.parse(content, filename=str(path))
        visitor = PythonAntiPatternVisitor(str(path), lines)
        visitor.visit(tree)
        findings.extend(visitor.findings)
    except SyntaxError as err:
        findings.append(
            {
                "file": str(path),
                "line": err.lineno or 1,
                "col": err.offset or 0,
                "id": "AP_SYNTAX_ERR",
                "severity": "WARN",
                "anti_pattern": f"Python syntax error: {err.msg}",
                "hazard": "File cannot be parsed into AST",
                "repair": "Fix syntax errors in Python module",
            }
        )

    return findings


def audit_config_file(path: Path) -> List[Dict[str, Any]]:
    """Audits pyproject.toml or mypy.ini for global ignore_missing_imports."""
    findings: List[Dict[str, Any]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    if path.name == "pyproject.toml":
        in_tool_mypy = False
        in_module_override = False
        for idx, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("[tool.mypy]"):
                in_tool_mypy = True
                in_module_override = False
            elif stripped.startswith("[[tool.mypy.overrides]]") or stripped.startswith(
                "[tool.mypy."
            ):
                in_tool_mypy = False
                in_module_override = True
            elif stripped.startswith("[") and stripped.endswith("]"):
                in_tool_mypy = False
                in_module_override = False

            if in_tool_mypy and not in_module_override:
                if re.match(r"^\s*ignore_missing_imports\s*=\s*(?:true|True)\b", stripped):
                    findings.append(
                        {
                            "file": str(path),
                            "line": idx,
                            "col": 0,
                            "id": "AP_PY_001",
                            "severity": "BLOCKER",
                            "anti_pattern": "Global ignore_missing_imports = true in [tool.mypy]",
                            "hazard": "Silences type errors across the entire codebase globally",
                            "repair": "Use scoped [[tool.mypy.overrides]] with module list per HP_PY_001",
                        }
                    )
    elif path.name in {"mypy.ini", "setup.cfg"}:
        in_mypy_main = False
        for idx, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped == "[mypy]":
                in_mypy_main = True
            elif stripped.startswith("[mypy-") or (
                stripped.startswith("[") and stripped.endswith("]")
            ):
                in_mypy_main = False

            if in_mypy_main:
                if re.match(r"^\s*ignore_missing_imports\s*=\s*(?:True|true|1)\b", stripped):
                    findings.append(
                        {
                            "file": str(path),
                            "line": idx,
                            "col": 0,
                            "id": "AP_PY_001",
                            "severity": "BLOCKER",
                            "anti_pattern": "Global ignore_missing_imports in [mypy] section",
                            "hazard": "Silences type errors globally across all modules",
                            "repair": "Scope to specific modules under [mypy-module.*] per HP_PY_001",
                        }
                    )

    return findings


def run_audit(target: Path) -> List[Dict[str, Any]]:
    """Runs Python anti-pattern audit recursively over target path."""
    findings: List[Dict[str, Any]] = []
    if target.is_file():
        if target.suffix == ".py":
            findings.extend(audit_python_file(target))
        elif target.name in {"pyproject.toml", "mypy.ini", "setup.cfg"}:
            findings.extend(audit_config_file(target))
    elif target.is_dir():
        for py_file in sorted(target.rglob("*.py")):
            # Skip hidden, virtualenv, and build directories
            parts = py_file.parts
            if any(
                p.startswith(".") or p in {"venv", ".venv", "build", "dist", "__pycache__"}
                for p in parts
            ):
                continue
            findings.extend(audit_python_file(py_file))
        for cfg_name in ("pyproject.toml", "mypy.ini"):
            cfg_file = target / cfg_name
            if cfg_file.exists():
                findings.extend(audit_config_file(cfg_file))
    return findings


def generate_markdown_report(findings: List[Dict[str, Any]], target: Path) -> str:
    """Generates an audit report in Markdown with claim hygiene discipline."""
    blocker_count = sum(1 for f in findings if f.get("severity") == "BLOCKER")
    major_count = sum(1 for f in findings if f.get("severity") == "MAJOR")
    warn_count = sum(1 for f in findings if f.get("severity") == "WARN")

    lines = [
        "# Python Code Anti-Pattern Audit Report",
        "",
        "**AuthorityEffect:** None",
        f"**Target:** `{target}`",
        f"**Total Findings:** {len(findings)} (BLOCKER: {blocker_count}, MAJOR: {major_count}, WARN: {warn_count})",
        "",
    ]

    if not findings:
        lines.append("## Status: Clean")
        lines.append("")
        lines.append("No canonical Python anti-patterns detected under active audit rules.")
        return "\n".join(lines)

    lines.append("## Detected Anti-Patterns")
    lines.append("")
    lines.append("| ID | Severity | File:Line | Anti-Pattern | Repair Direction |")
    lines.append("|---|---|---|---|---|")
    for f in findings:
        f_id = f.get("id", "UNKNOWN")
        sev = f.get("severity", "INFO")
        loc = f"{Path(f['file']).as_posix()}:{f.get('line', 1)}"
        pat = f.get("anti_pattern", "")
        repair = f.get("repair", "")
        lines.append(
            f"| `{f_id}` | **{sev}** | [`{loc}`](file:///{Path(f['file']).resolve().as_posix()}#L{f.get('line', 1)}) | {pat} | {repair} |"
        )

    lines.append("")
    lines.append("## Claim Discipline & Scope")
    lines.append("")
    lines.append(
        "1. **What this report supports:** Identifies syntactically verifiable occurrences of `AP_PY_001` through `AP_PY_005` in audited targets."
    )
    lines.append(
        "2. **What this report does not support:** Does not certify semantic correctness, runtime performance, or absence of other unmodeled edge cases."
    )
    lines.append(
        "3. **Narrowest defensible claim:** The audited source files adhere to or deviate from the specified AST and pattern constraints."
    )
    lines.append(
        "4. **Next test needed:** Execute scoped type checker (`mypy`) and unit test suite against repaired modules."
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Python Code Anti-Pattern Auditor")
    parser.add_argument("--path", type=str, default=".", help="File or directory path to audit")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with non-zero status if blockers or majors are found",
    )
    parser.add_argument("--json", action="store_true", help="Output findings as JSON")
    parser.add_argument(
        "--report-out", type=str, default="", help="Write markdown report to specified path"
    )

    args = parser.parse_args()
    target_path = Path(args.path).resolve()

    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}", file=sys.stderr)
        return 2

    findings = run_audit(target_path)

    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        blockers = sum(1 for f in findings if f.get("severity") == "BLOCKER")
        majors = sum(1 for f in findings if f.get("severity") == "MAJOR")
        warns = sum(1 for f in findings if f.get("severity") == "WARN")
        print(f"--- Python Anti-Pattern Audit Summary ({target_path}) ---")
        print(
            f"  Total findings: {len(findings)} (BLOCKER: {blockers}, MAJOR: {majors}, WARN: {warns})"
        )
        for f in findings:
            loc = f"{Path(f['file']).as_posix()}:{f.get('line', 1)}"
            print(f"  [{f['id']}] {loc} - {f['anti_pattern']} ({f['severity']})")
            print(f"      Hazard: {f.get('hazard', '')}")
            print(f"      Repair: {f.get('repair', '')}")

    if args.report_out:
        report_path = Path(args.report_out).resolve()
        report_content = generate_markdown_report(findings, target_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_content, encoding="utf-8")
        print(f"Report written to: {report_path}")

    if args.check:
        has_critical = any(f.get("severity") in {"BLOCKER", "MAJOR"} for f in findings)
        return 1 if has_critical else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
