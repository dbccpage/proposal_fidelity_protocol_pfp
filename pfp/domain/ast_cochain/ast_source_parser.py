from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Dict, Mapping, Set

from .ast_models import ASTDefect


@dataclass(frozen=True)
class ParsedSourceTree:
    modules: tuple[str, ...]
    trees: Mapping[str, ast.AST]
    imports: Mapping[str, Set[str]]
    symbols: Mapping[str, Set[str]]
    syntax_defects: tuple[ASTDefect, ...]


class PythonSourceParser:
    """Parse source only. No graph construction and no obstruction valuation."""

    def parse(self, sources: Mapping[str, str]) -> ParsedSourceTree:
        modules = tuple(sorted(sources))
        trees: Dict[str, ast.AST] = {}
        imports: Dict[str, Set[str]] = {m: set() for m in modules}
        symbols: Dict[str, Set[str]] = {m: set() for m in modules}
        defects: list[ASTDefect] = []

        for module_name, code in sources.items():
            try:
                tree = ast.parse(code, filename=module_name)
                trees[module_name] = tree
                self._collect(tree, imports[module_name], symbols[module_name])
            except SyntaxError as exc:
                defects.append(
                    ASTDefect(
                        defect_type="syntax_error",
                        source_module=module_name,
                        target_module=None,
                        description=(
                            f"SyntaxError in {module_name}: {exc.msg} at line {exc.lineno}"
                        ),
                        weight=2.0,
                    )
                )

        return ParsedSourceTree(
            modules=modules,
            trees=trees,
            imports=imports,
            symbols=symbols,
            syntax_defects=tuple(defects),
        )

    @staticmethod
    def _collect(tree: ast.AST, imports: Set[str], symbols: Set[str]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.add(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
