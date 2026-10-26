"""Abstract base classes and context for python_development_office rules."""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from omega_engine_operads.domain.python_development_office import (
    AntipatternFinding,
    ArchitectureConfig,
    ModuleInfo,
    RuleCategory,
)


@dataclass
class RuleContext:
    """Context provided to AST rules during single-file analysis."""

    path: Path
    is_test_file: bool
    config: ArchitectureConfig
    suppressions: dict[int, set[str]] = field(default_factory=dict)
    findings: list[AntipatternFinding] = field(default_factory=list)
    current_class_name: str | None = None
    current_function_name: str | None = None
    function_depth: int = 0

    def make_finding(
        self,
        node: ast.AST,
        rule: BaseRule,
        message: str | None = None,
        remediation: str | None = None,
        category: RuleCategory = RuleCategory.PITFALL,
        severity: str = "error",
    ) -> AntipatternFinding | None:
        """Create a finding if not suppressed by inline comment."""
        line = getattr(node, "lineno", 1)
        col = getattr(node, "col_offset", 0)

        # Check line suppression
        if line in self.suppressions:
            allowed = self.suppressions[line]
            if "*" in allowed or rule.rule_code.upper() in allowed:
                return None

        finding = AntipatternFinding(
            path=str(self.path),
            line=line,
            column=col,
            rule_id=rule.rule_id,
            rule_code=rule.rule_code,
            category=category.value,
            message=message or rule.default_message,
            remediation=remediation or rule.default_remediation,
            severity=severity,
        )
        self.findings.append(finding)
        return finding


class BaseRule(ABC):
    """Base class for all analyzer rules."""

    rule_id: int = 0
    rule_code: str = "UNKNOWN_RULE"
    category: RuleCategory = RuleCategory.PITFALL
    default_message: str = "Rule violation detected"
    default_remediation: str = "Refactor code to avoid this pattern"


class AstRule(BaseRule):
    """Rule inspecting AST nodes during single-file traversal."""

    def check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, context: RuleContext
    ) -> None:
        pass

    def check_class(self, node: ast.ClassDef, context: RuleContext) -> None:
        pass

    def check_compare(self, node: ast.Compare, context: RuleContext) -> None:
        pass

    def check_assign(self, node: ast.Assign, context: RuleContext) -> None:
        pass

    def check_aug_assign(self, node: ast.AugAssign, context: RuleContext) -> None:
        pass

    def check_call(self, node: ast.Call, context: RuleContext) -> None:
        pass

    def check_import_from(self, node: ast.ImportFrom, context: RuleContext) -> None:
        pass

    def check_except(self, node: ast.ExceptHandler, context: RuleContext) -> None:
        pass

    def check_raise(self, node: ast.Raise, context: RuleContext) -> None:
        pass

    def check_assert(self, node: ast.Assert, context: RuleContext) -> None:
        pass

    def check_for(self, node: ast.For, context: RuleContext) -> None:
        pass


class ArchitectureRule(BaseRule):
    """Rule inspecting cross-module architecture, layer boundaries, and dependency graph."""

    category: RuleCategory = RuleCategory.CLEAN_ARCH

    @abstractmethod
    def check_project(
        self,
        modules: Sequence[ModuleInfo],
        module_graph: dict[str, ModuleInfo],
        config: ArchitectureConfig,
    ) -> list[AntipatternFinding]:
        """Evaluate architectural invariants across the project module graph."""
        ...
