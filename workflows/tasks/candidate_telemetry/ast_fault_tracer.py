"""AST fault tracer for multi-round candidate critique.

Analyzes candidate syntax trees, syntax errors, illegal AST nodes (e.g. float constants),
and caller-callee dependency boundaries.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List, Set, Tuple


@dataclass(frozen=True)
class AstFaultReport:
    """Diagnostic report emitted by the AST dependency fault tracer."""

    has_syntax_error: bool
    syntax_error_detail: str
    illegal_nodes_detected: Tuple[str, ...]
    declared_functions: Tuple[str, ...]
    referenced_names: Tuple[str, ...]
    diagnostics: str


class _AstFaultVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.illegal_nodes: List[str] = []
        self.declared_functions: List[str] = []
        self.referenced_names: Set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.declared_functions.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.declared_functions.append(node.name)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, float):
            self.illegal_nodes.append(f"FloatConstant(value={node.value}, line={node.lineno})")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.referenced_names.add(node.id)
        self.generic_visit(node)


def trace_ast_faults(code_content: str) -> AstFaultReport:
    """Parse candidate source and trace AST syntax and structural defects."""
    try:
        tree = ast.parse(code_content)
    except SyntaxError as exc:
        detail = f"SyntaxError at line {exc.lineno}, col {exc.offset}: {exc.msg}"
        return AstFaultReport(
            has_syntax_error=True,
            syntax_error_detail=detail,
            illegal_nodes_detected=(),
            declared_functions=(),
            referenced_names=(),
            diagnostics=f"AST parse failure: {detail}",
        )

    visitor = _AstFaultVisitor()
    visitor.visit(tree)

    diagnostics = "AST clean; no syntax errors detected."
    if visitor.illegal_nodes:
        diagnostics = f"Illegal nodes detected: {', '.join(visitor.illegal_nodes)}"

    return AstFaultReport(
        has_syntax_error=False,
        syntax_error_detail="",
        illegal_nodes_detected=tuple(visitor.illegal_nodes),
        declared_functions=tuple(visitor.declared_functions),
        referenced_names=tuple(sorted(visitor.referenced_names)),
        diagnostics=diagnostics,
    )
