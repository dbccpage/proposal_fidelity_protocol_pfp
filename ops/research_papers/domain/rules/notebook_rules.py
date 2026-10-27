"""Jupyter Companion Notebook Gate Rules.

AuthorityEffect: None.

Enforces canonical naming conventions, cwd-independent path discovery,
zero absolute machine paths, and error-free stored execution outputs.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from .base_rule import (
    BasePaperRule,
    PaperContext,
    RuleCategory,
    RuleFinding,
    RuleResult,
    RuleSeverity,
)

CANONICAL_NB_NAME = re.compile(r"^(?:[0-9]{3}_)?[a-z0-9_.-]+\.ipynb$")
FORBIDDEN_NB_PREFIX = re.compile(r"^(?:[0-9]{3}_)?reviewer_.*\.ipynb$")
USER_PATH_PATTERNS = [
    re.compile(r"(/home/[a-zA-Z0-9._-]+)"),
    re.compile(r"(/Users/[a-zA-Z0-9._-]+)"),
    re.compile(r"([A-Za-z]:\\[Uu]sers\\[a-zA-Z0-9._-]+)"),
]


class NotebookCanonicalNamingRule(BasePaperRule):
    """Enforces canonical naming for companion notebooks under jupyter_notebooks/."""

    @property
    def rule_id(self) -> str:
        return "R_NOTEBOOK_NAMING"

    @property
    def name(self) -> str:
        return "Notebook Canonical Naming Format"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.NOTEBOOK

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Jupyter companion notebooks must follow <num>_<slug>.ipynb or <slug>.ipynb without legacy reviewer_ prefixes."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        nb_paths = [p for p in ctx.list_paths() if p.endswith(".ipynb")]
        findings: List[RuleFinding] = []

        for p in nb_paths:
            filename = p.split("/")[-1]
            if not p.startswith("jupyter_notebooks/"):
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Notebook '{p}' is outside canonical jupyter_notebooks/ directory.",
                        file_path=p,
                        remediation="Move notebook into jupyter_notebooks/.",
                    )
                )
            if FORBIDDEN_NB_PREFIX.match(filename):
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Notebook '{filename}' uses prohibited legacy reviewer prefix.",
                        file_path=p,
                        remediation="Rename notebook to follow canonical <paper_num>_<slug>.ipynb format.",
                    )
                )
            elif not CANONICAL_NB_NAME.match(filename):
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Notebook '{filename}' violates canonical lowercase naming scheme.",
                        file_path=p,
                    )
                )

        if findings:
            return self.fail_result(findings, {"notebook_count": len(nb_paths)})
        return self.pass_result({"notebook_count": len(nb_paths)})


class NotebookNoUserPathsRule(BasePaperRule):
    """Enforces that notebook cells contain no machine-specific absolute user paths."""

    @property
    def rule_id(self) -> str:
        return "R_NOTEBOOK_NO_USER_PATHS"

    @property
    def name(self) -> str:
        return "Zero Machine-Specific Absolute User Paths"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.NOTEBOOK

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Notebook code cells must use relative path discovery and contain zero /Users/, /home/, or C:\\Users\\ paths."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        nb_paths = [p for p in ctx.list_paths() if p.endswith(".ipynb")]
        findings: List[RuleFinding] = []

        for p in nb_paths:
            try:
                raw = ctx.read_text(p)
                data = json.loads(raw)
            except Exception as e:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Notebook '{p}' failed JSON parsing: {e}",
                        file_path=p,
                    )
                )
                continue

            for cell_idx, cell in enumerate(data.get("cells", [])):
                if cell.get("cell_type") != "code":
                    continue
                source = "".join(cell.get("source", []))
                for pat in USER_PATH_PATTERNS:
                    match = pat.search(source)
                    if match:
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=f"Cell {cell_idx} in '{p}' contains absolute user path: '{match.group(1)}'",
                                file_path=p,
                                line_number=cell_idx,
                                remediation="Replace absolute path with relative Path(__file__) or cwd-independent discovery.",
                            )
                        )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class NotebookExecutionCleanlinessRule(BasePaperRule):
    """Enforces that stored code cells have execution counts and zero unhandled tracebacks/errors."""

    @property
    def rule_id(self) -> str:
        return "R_NOTEBOOK_EXECUTION_CLEANLINESS"

    @property
    def name(self) -> str:
        return "Notebook Stored Execution Cleanliness"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.NOTEBOOK

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "Stored notebook code cells must have execution counts and contain zero error outputs or unhandled exceptions."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        nb_paths = [p for p in ctx.list_paths() if p.endswith(".ipynb")]
        findings: List[RuleFinding] = []

        for p in nb_paths:
            try:
                raw = ctx.read_text(p)
                data = json.loads(raw)
            except Exception as e:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Notebook '{p}' failed JSON parsing: {e}",
                        file_path=p,
                    )
                )
                continue

            for cell_idx, cell in enumerate(data.get("cells", [])):
                if cell.get("cell_type") != "code":
                    continue
                source = "".join(cell.get("source", [])).strip()
                if not source:
                    continue

                if cell.get("execution_count") is None:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Cell {cell_idx} in '{p}' has null execution_count (unexecuted).",
                            file_path=p,
                            line_number=cell_idx,
                            remediation="Execute notebook to completion and store execution outputs.",
                        )
                    )

                for out in cell.get("outputs", []):
                    if out.get("output_type") == "error":
                        ename = out.get("ename", "Error")
                        evalue = out.get("evalue", "")
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=RuleSeverity.BLOCKER,
                                message=f"Cell {cell_idx} in '{p}' stored an error output: {ename}: {evalue}",
                                file_path=p,
                                line_number=cell_idx,
                                remediation="Fix the exception and re-execute the notebook cleanly.",
                            )
                        )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()
