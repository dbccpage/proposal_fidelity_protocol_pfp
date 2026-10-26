"""AST inspection utilities and import extraction for python_development_office."""

from __future__ import annotations

import ast
import re

from omega_engine_operads.domain.python_development_office import (
    ImportedSymbol,
)


def extract_imported_symbols(tree: ast.AST) -> list[ImportedSymbol]:
    """Extract all import statements and imported symbol names from an AST."""
    symbols: list[ImportedSymbol] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                symbols.append(
                    ImportedSymbol(
                        module=alias.name,
                        name=alias.name,
                        alias=alias.asname,
                        lineno=node.lineno,
                        is_relative=False,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            is_rel = node.level > 0
            for alias in node.names:
                symbols.append(
                    ImportedSymbol(
                        module=module_name,
                        name=alias.name,
                        alias=alias.asname,
                        lineno=node.lineno,
                        is_relative=is_rel,
                    )
                )
    return symbols


def extract_module_imports(tree: ast.AST) -> set[str]:
    """Extract root and package module names imported by an AST."""
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules


def has_len_call_in_args(node: ast.Call) -> bool:
    """Check if any argument in range(...) is a len(...) call."""
    if len(node.args) == 3:
        # Strided range e.g. range(0, len(items), 3) is batching/chunking, not simple index iteration
        return False
    for arg in node.args:
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
            if arg.func.id == "len":
                return True
    return False


def get_decorator_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> set[str]:
    """Extract simple decorator names."""
    names: set[str] = set()
    for d in node.decorator_list:
        if isinstance(d, ast.Name):
            names.add(d.id)
        elif isinstance(d, ast.Attribute):
            names.add(d.attr)
        elif isinstance(d, ast.Call):
            if isinstance(d.func, ast.Name):
                names.add(d.func.id)
            elif isinstance(d.func, ast.Attribute):
                names.add(d.func.attr)
    return names


_NOQA_RE = re.compile(r"#\s*noqa(?::\s*([^#\n\r-]+))?", re.IGNORECASE)

_RULE_CODE_ALIASES: dict[str, str] = {
    "BLE001": "BROAD_EXCEPTION_CATCH",
    "E711": "NONE_COMPARISON",
    "E712": "EXPLICIT_BOOLEAN_COMPARISON",
    "E721": "TYPE_EQUALITY_CHECK",
}


def parse_suppressions(source_lines: list[str]) -> dict[int, set[str]]:
    """Map 1-indexed line numbers to suppressed rule codes.

    `# noqa` suppresses all rules on that line.
    `# noqa: RULE_A, RULE_B` suppresses specified rule codes on that line.
    """
    suppressions: dict[int, set[str]] = {}
    for idx, line in enumerate(source_lines, start=1):
        match = _NOQA_RE.search(line)
        if match:
            codes = match.group(1)
            if codes is None:
                suppressions[idx] = {"*"}
            else:
                rule_set: set[str] = set()
                for c in codes.split(","):
                    cleaned = c.strip().upper()
                    if cleaned:
                        rule_set.add(cleaned)
                        if cleaned in _RULE_CODE_ALIASES:
                            rule_set.add(_RULE_CODE_ALIASES[cleaned])
                suppressions[idx] = rule_set if rule_set else {"*"}
    return suppressions


def is_suppressed(lineno: int, rule_code: str, suppressions: dict[int, set[str]]) -> bool:
    """Check if a rule code is suppressed on a specific line."""
    if lineno not in suppressions:
        return False
    codes = suppressions[lineno]
    return "*" in codes or rule_code.upper() in codes
