"""
source_parser.py
================

Abstract Syntax Tree (AST) Source Parser discovering modules, imports, and calls.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from typing import List, Optional, Set, Tuple


class ASTSourceParser:
    """Parse Python source texts into structured AST nodes, imports, and cross-calls."""

    @staticmethod
    def parse_module(source_code: str) -> Optional[ast.Module]:
        try:
            return ast.parse(source_code)
        except SyntaxError:
            return None

    @staticmethod
    def extract_imports(tree: ast.Module) -> List[Tuple[str, str]]:
        """Returns tuples of (imported_module, imported_name)."""
        imports: List[Tuple[str, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append((mod, alias.name))
        return imports

    @staticmethod
    def extract_defined_names(tree: ast.Module) -> Set[str]:
        names: Set[str] = set()
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
        return names
