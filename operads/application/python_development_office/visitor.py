"""AST visitor coordinating node dispatch to registered AstRules."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Sequence

from operads.application.python_development_office.ast_utils import (
    extract_imported_symbols,
    parse_suppressions,
)
from operads.application.python_development_office.rules.base import (
    AstRule,
    RuleContext,
)
from operads.domain.python_development_office import (
    AntipatternFinding,
    ArchitectureConfig,
    ModuleInfo,
    RuleCategory,
)


class RuleVisitor(ast.NodeVisitor):
    """AST NodeVisitor dispatching nodes to registered AstRules."""

    def __init__(self, context: RuleContext, rules: Sequence[AstRule]) -> None:
        super().__init__()
        self.context = context
        self.rules = rules

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        prior_fn = self.context.current_function_name
        self.context.current_function_name = node.name
        self.context.function_depth += 1

        for rule in self.rules:
            rule.check_function(node, self.context)

        self.generic_visit(node)
        self.context.function_depth -= 1
        self.context.current_function_name = prior_fn

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        prior_fn = self.context.current_function_name
        self.context.current_function_name = node.name
        self.context.function_depth += 1

        for rule in self.rules:
            rule.check_function(node, self.context)

        self.generic_visit(node)
        self.context.function_depth -= 1
        self.context.current_function_name = prior_fn

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        prior_class = self.context.current_class_name
        self.context.current_class_name = node.name

        for rule in self.rules:
            rule.check_class(node, self.context)

        self.generic_visit(node)
        self.context.current_class_name = prior_class

    def visit_Compare(self, node: ast.Compare) -> None:
        for rule in self.rules:
            rule.check_compare(node, self.context)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for rule in self.rules:
            rule.check_assign(node, self.context)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        for rule in self.rules:
            rule.check_aug_assign(node, self.context)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        for rule in self.rules:
            rule.check_call(node, self.context)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for rule in self.rules:
            rule.check_import_from(node, self.context)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        for rule in self.rules:
            rule.check_except(node, self.context)
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        for rule in self.rules:
            rule.check_raise(node, self.context)
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        for rule in self.rules:
            rule.check_assert(node, self.context)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        for rule in self.rules:
            rule.check_for(node, self.context)
        self.generic_visit(node)


def scan_source_ast(
    content: str,
    path: Path,
    rules: Sequence[AstRule],
    config: ArchitectureConfig,
    is_test_file: bool | None = None,
) -> tuple[list[AntipatternFinding], ModuleInfo | None]:
    """Scan supplied Python source and extract module metadata without file I/O."""
    if is_test_file is None:
        is_test_file = (
            any(path.match(pat) for pat in config.test_file_patterns)
            or "test" in path.name.lower()
            or "tests" in path.parts
            or "evidence" in path.parts
        )

    try:
        lines = content.splitlines()
        tree = ast.parse(content, filename=str(path))
    except SyntaxError as err:
        line = getattr(err, "lineno", 1) or 1
        return (
            [
                AntipatternFinding(
                    path=str(path),
                    line=line,
                    column=0,
                    rule_id=0,
                    rule_code="UNPARSEABLE_FILE",
                    category=RuleCategory.PITFALL.value,
                    message=f"File could not be parsed: {err}",
                    remediation="Ensure file has valid UTF-8 encoding and Python 3 syntax",
                    severity="error",
                )
            ],
            None,
        )

    suppressions = parse_suppressions(lines)
    context = RuleContext(
        path=path,
        is_test_file=is_test_file,
        config=config,
        suppressions=suppressions,
    )

    visitor = RuleVisitor(context, rules)
    visitor.visit(tree)

    # Build ModuleInfo
    imported_symbols = extract_imported_symbols(tree)
    imports = {s.module for s in imported_symbols if s.module}
    classes = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    functions = {
        n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    mod_info = ModuleInfo(
        path=str(path),
        package="",  # assigned during project scan
        layer=None,
        imports=imports,
        imported_symbols=imported_symbols,
        imported_by=set(),
        class_names=classes,
        function_names=functions,
        loc=len(lines),
        is_test=is_test_file,
    )

    return (context.findings, mod_info)
