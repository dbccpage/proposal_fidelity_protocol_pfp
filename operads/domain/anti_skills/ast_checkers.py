"""AST Anti-Skill Checkers for Candidate Prosecution.

Provides sovereign AST visitors scanning candidate Python source code or diffs
for anti-patterns and ungrounded execution traps before passing to verification.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple


@dataclass(frozen=True, slots=True)
class AstAntiSkillFinding:
    """A deterministic AST violation identified during candidate prosecution."""

    kind: str
    description: str
    line_number: int
    column: int
    node_type: str
    severity: str = "BLOCKER"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "description": self.description,
            "line_number": self.line_number,
            "column": self.column,
            "node_type": self.node_type,
            "severity": self.severity,
        }


class AntiSkillAstVisitor(ast.NodeVisitor):
    """AST visitor implementing the OEWAS anti-skill structural checks."""

    def __init__(self) -> None:
        self.findings: List[AstAntiSkillFinding] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.findings.append(
                AstAntiSkillFinding(
                    kind="ANTI-BARE-EXCEPT",
                    description="Bare except: clause detected (risks swallowing BaseException / KeyboardInterrupt)",
                    line_number=node.lineno,
                    column=node.col_offset,
                    node_type="ExceptHandler",
                    severity="BLOCKER",
                )
            )
        if len(node.body) == 1:
            first = node.body[0]
            if isinstance(first, ast.Pass) or (
                isinstance(first, ast.Return) and first.value is None
            ):
                self.findings.append(
                    AstAntiSkillFinding(
                        kind="ANTI-SWALLOWED-EXCEPTION",
                        description="Exception handler swallows exception silently with pass or return None",
                        line_number=node.lineno,
                        column=node.col_offset,
                        node_type="ExceptHandler",
                        severity="BLOCKER",
                    )
                )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_mutable_defaults(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_mutable_defaults(node)
        self.generic_visit(node)

    def _check_mutable_defaults(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        all_defaults = list(node.args.defaults) + [
            d for d in node.args.kw_defaults if d is not None
        ]
        for default in all_defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.findings.append(
                    AstAntiSkillFinding(
                        kind="ANTI-MUTABLE-DEFAULT",
                        description=f"Mutable default argument in function '{node.name}' causes mutable shared state",
                        line_number=default.lineno,
                        column=default.col_offset,
                        node_type="FunctionDef",
                        severity="BLOCKER",
                    )
                )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                mod_name = node.module or "..."
                self.findings.append(
                    AstAntiSkillFinding(
                        kind="ANTI-STAR-IMPORT",
                        description=f"Wildcard import 'from {mod_name} import *' pollutes namespace",
                        line_number=node.lineno,
                        column=node.col_offset,
                        node_type="ImportFrom",
                        severity="MAJOR",
                    )
                )
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Is, ast.IsNot)):
                if isinstance(comparator, ast.Constant) and comparator.value not in (
                    None,
                    True,
                    False,
                    Ellipsis,
                ):
                    self.findings.append(
                        AstAntiSkillFinding(
                            kind="ANTI-LITERAL-IS-COMPARISON",
                            description=f"Literal identity comparison 'is {comparator.value!r}' (use ==)",
                            line_number=node.lineno,
                            column=node.col_offset,
                            node_type="Compare",
                            severity="BLOCKER",
                        )
                    )
                if isinstance(node.left, ast.Constant) and node.left.value not in (
                    None,
                    True,
                    False,
                    Ellipsis,
                ):
                    self.findings.append(
                        AstAntiSkillFinding(
                            kind="ANTI-LITERAL-IS-COMPARISON",
                            description=f"Literal identity comparison '{node.left.value!r} is ...' (use ==)",
                            line_number=node.lineno,
                            column=node.col_offset,
                            node_type="Compare",
                            severity="BLOCKER",
                        )
                    )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        # Check eval / exec
        if isinstance(func, ast.Name):
            if func.id in ("eval", "exec"):
                self.findings.append(
                    AstAntiSkillFinding(
                        kind="ANTI-UNCONTRACTED-IO",
                        description=f"Dangerous dynamic code execution call to '{func.id}'",
                        line_number=node.lineno,
                        column=node.col_offset,
                        node_type="Call",
                        severity="BLOCKER",
                    )
                )
            elif func.id in ("load_dotenv", "find_dotenv"):
                self.findings.append(
                    AstAntiSkillFinding(
                        kind="ANTI-AMBIENT-CREDENTIAL-SEARCH",
                        description=f"Implicit ambient credential loader call '{func.id}'",
                        line_number=node.lineno,
                        column=node.col_offset,
                        node_type="Call",
                        severity="BLOCKER",
                    )
                )
        self.generic_visit(node)


def scan_candidate_ast_for_anti_skills(
    code_or_bytes: str | bytes,
) -> tuple[AstAntiSkillFinding, ...]:
    """Scans candidate Python code for anti-skill AST defects."""
    if isinstance(code_or_bytes, bytes):
        try:
            source = code_or_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            return (
                AstAntiSkillFinding(
                    kind="ANTI-ENCODING-DEFECT",
                    description=f"UTF-8 decoding defect: {exc}",
                    line_number=1,
                    column=0,
                    node_type="DecodeError",
                    severity="BLOCKER",
                ),
            )
    else:
        source = code_or_bytes

    # If code looks like a unified diff, extract the added lines
    if "diff --git" in source or (source.startswith("---") and "\n+++" in source):
        lines = []
        for line in source.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                lines.append(line[1:])
            elif not line.startswith("-") and not line.startswith("@@"):
                lines.append(line)
        source = "\n".join(lines)

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return (
            AstAntiSkillFinding(
                kind="ANTI-SYNTAX-ERROR",
                description=f"Python syntax error in candidate: {exc}",
                line_number=exc.lineno or 1,
                column=exc.offset or 0,
                node_type="SyntaxError",
                severity="BLOCKER",
            ),
        )

    visitor = AntiSkillAstVisitor()
    visitor.visit(tree)
    return tuple(visitor.findings)
