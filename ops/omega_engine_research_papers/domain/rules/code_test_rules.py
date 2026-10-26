"""Python Code & Test Engineering Gate Rules.

AuthorityEffect: None.

Enforces test locations, strict mypy typing configuration, and isolation
between unit test suites and notebook execution engines.
"""

from __future__ import annotations

import re
from typing import List

from .base_rule import (
    BasePaperRule,
    PaperContext,
    RuleCategory,
    RuleFinding,
    RuleResult,
    RuleSeverity,
)


class PythonTestLocationRule(BasePaperRule):
    """Enforces that Python test files reside in code/ or code/tests/."""

    @property
    def rule_id(self) -> str:
        return "R_TEST_LOCATION"

    @property
    def name(self) -> str:
        return "Python Test Location Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Python tests must reside in code/ or code/tests/ to prevent ambient root test discovery."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        test_files = [p for p in ctx.list_paths() if p.endswith(".py") and ("test_" in p or "_test.py" in p)]
        findings: List[RuleFinding] = []

        for p in test_files:
            if not p.startswith("code/"):
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Test file '{p}' is outside canonical code/ tree.",
                        file_path=p,
                        remediation="Move test file into code/ or code/tests/.",
                    )
                )

        if findings:
            return self.fail_result(findings, {"test_count": len(test_files)})
        return self.pass_result({"test_count": len(test_files)})


class StrictMypyConfigRule(BasePaperRule):
    """Enforces that pyproject.toml does not use blanket ignore_missing_imports = true."""

    @property
    def rule_id(self) -> str:
        return "R_STRICT_MYPY"

    @property
    def name(self) -> str:
        return "Strict Mypy Type Configuration"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "pyproject.toml must configure mypy_path and avoid global ignore_missing_imports = true."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        if not ctx.has_file("pyproject.toml"):
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="pyproject.toml missing from package root.",
                    file_path="pyproject.toml",
                )
            ])

        content = ctx.read_text("pyproject.toml")
        findings: List[RuleFinding] = []

        # Check for global ignore_missing_imports under [tool.mypy]
        in_tool_mypy = False
        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped == "[tool.mypy]":
                in_tool_mypy = True
            elif stripped.startswith("["):
                in_tool_mypy = False

            if in_tool_mypy and re.search(r"ignore_missing_imports\s*=\s*true", stripped, re.IGNORECASE):
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Global ignore_missing_imports = true found on line {line_no} under [tool.mypy]",
                        file_path="pyproject.toml",
                        line_number=line_no,
                        remediation="Remove global ignore_missing_imports; scope un-typed modules via [[tool.mypy.overrides]].",
                    )
                )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class NoNotebookClientsInPytestRule(BasePaperRule):
    """Enforces that unit test files do not directly import nbclient or nbconvert."""

    @property
    def rule_id(self) -> str:
        return "R_NO_NOTEBOOK_CLIENTS_IN_PYTEST"

    @property
    def name(self) -> str:
        return "Pytest / Notebook Client Separation"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Pytest files must test domain/computational logic directly and avoid importing nbclient or nbconvert."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        test_files = [p for p in ctx.list_paths() if p.startswith("code/") and p.endswith(".py") and "test" in p]
        findings: List[RuleFinding] = []

        for p in test_files:
            content = ctx.read_text(p)
            for line_no, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r"\bimport\s+nbclient\b", stripped) or re.search(r"\bfrom\s+nbclient\b", stripped):
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Illegal direct import of nbclient on line {line_no} in '{p}'",
                            file_path=p,
                            line_number=line_no,
                            remediation="Execute notebook replay via standalone CLI or dedicated integration runners.",
                        )
                    )
                if re.search(r"\bimport\s+nbconvert\b", stripped) or re.search(r"\bfrom\s+nbconvert\b", stripped):
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Illegal direct import of nbconvert on line {line_no} in '{p}'",
                            file_path=p,
                            line_number=line_no,
                        )
                    )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()
