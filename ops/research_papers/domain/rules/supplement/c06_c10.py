"""Rules C06-C10 for supplement republication review.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from ..base_rule import (
    BasePaperRule,
    PaperContext,
    RuleCategory,
    RuleFinding,
    RuleResult,
    RuleSeverity,
)
from .common import _cap, _python_code_files

class LowerBoundNotPromotedToEnclosureRule(BasePaperRule):
    """Enforces that one-sided lower bounds are not presented as tight two-sided intervals."""

    @property
    def rule_id(self) -> str:
        return "R_LOWER_BOUND_NOT_ENCLOSURE"

    @property
    def name(self) -> str:
        return "Lower Bound Enclosure Promotion Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.CLAIM_HYGIENE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return (
            "Propagating parameter uncertainties on a one-sided lower bound must not collapse "
            "to [bound, bound] with zero uncertainty, which falsely implies an exact enclosure."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            content = ctx.read_text(path)
            if "propagate_parameter_uncertainties" in content:
                # Check if upper bound defaults to base_bound when uncertainty is zero
                for line_no, line in enumerate(content.splitlines(), start=1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if re.search(r"upper\s*=\s*base_bound\s*\+", stripped) and "max_val" not in content:
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=(
                                    f"Uncertainty propagation on line {line_no} in '{path}' centers upper bound on "
                                    f"base_bound, allowing zero uncertainty to collapse lower bound into an enclosure."
                                ),
                                file_path=path,
                                line_number=line_no,
                                remediation="Set upper bound to physical cap (e.g. 2.0) unless two-sided interval is supplied.",
                            )
                        )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C07: Quantum carrier admission
# ---------------------------------------------------------------------------


class QuantumCarrierAdmissionRule(BasePaperRule):
    """Enforces that quantum state and observational distance inputs reject NaNs and malformed carriers."""

    @property
    def rule_id(self) -> str:
        return "R_QUANTUM_CARRIER_ADMISSION"

    @property
    def name(self) -> str:
        return "Quantum Carrier and Report Admission Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return (
            "Quantum carrier and distance validators must check finiteness (no NaNs), "
            "require non-empty matching coordinate sets, and enforce physical trace-norm "
            "caps (<= 2) on difference states."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            content = ctx.read_text(path)
            # Check state validity checks
            if "def verify_state_validity" in content and "np.isfinite" not in content:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"verify_state_validity in '{path}' does not check np.isfinite on state matrix.",
                        file_path=path,
                        remediation="Add np.all(np.isfinite(state)) to state validation.",
                    )
                )
            # Check difference state validation for trace-norm cap
            if "evaluate_difference_set_conditioning" in content and "2.0" not in content and "trace_norm" in content:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"evaluate_difference_set_conditioning in '{path}' does not enforce trace-norm cap <= 2.",
                        file_path=path,
                        remediation="Enforce trace_norm <= 2.0 on difference state validity.",
                    )
                )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C08: Calibration field completeness
# ---------------------------------------------------------------------------


class CalibrationFieldCompletenessRule(BasePaperRule):
    """Enforces that calibration checkers recompute statistics and enforce authority metadata."""

    @property
    def rule_id(self) -> str:
        return "R_CALIBRATION_FIELD_COMPLETENESS"

    @property
    def name(self) -> str:
        return "Calibration Field Completeness Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return (
            "Calibration certificate checkers must recompute mean circulation from raw cochains "
            "and enforce fixed authority metadata (authority_effect == 'None')."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            content = ctx.read_text(path)
            if "CalibrationQuotientCertificate" in content and "def verify" in content:
                if "mean_circulation" in content and "expected_mean" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Calibration checker in '{path}' accepts certificate without recomputing mean_circulation.",
                            file_path=path,
                            remediation="Recompute expected mean from cochain and assert self.mean_circulation == expected_mean.",
                        )
                    )
                if "authority_effect" in content and not re.search(r'authority_effect\s*(?:==|!=)\s*["\']None["\']', content):
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Calibration checker in '{path}' does not enforce authority_effect == 'None'.",
                            file_path=path,
                            remediation="Add check that authority_effect == 'None'.",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C09: Exact matrix coordinate validation
# ---------------------------------------------------------------------------


class ExactMatrixCoordinateValidationRule(BasePaperRule):
    """Enforces that exact matrix setters and extractors validate coordinate bounds."""

    @property
    def rule_id(self) -> str:
        return "R_EXACT_MATRIX_BOUNDS"

    @property
    def name(self) -> str:
        return "Exact Matrix Coordinate Validation Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return (
            "Exact matrix classes implementing item assignment or submatrix extraction "
            "must validate coordinate bounds against matrix dimensions, preventing silent entry aliasing."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            content = ctx.read_text(path)
            if "class Matrix" in content and "def __setitem__" in content:
                # Check if __setitem__ flattens without bounds check
                for line_no, line in enumerate(content.splitlines(), start=1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "self.elements[r * self.cols + c]" in stripped:
                        # Check previous lines for bounds check
                        window = "\n".join(content.splitlines()[max(0, line_no - 8):line_no])
                        if "IndexError" not in window and "< 0" not in window:
                            findings.append(
                                RuleFinding(
                                    rule_id=self.rule_id,
                                    severity=self.severity,
                                    message=(
                                        f"Matrix.__setitem__ in '{path}' flattens coordinates on line {line_no} "
                                        f"without checking row/column bounds, allowing coordinate aliasing."
                                    ),
                                    file_path=path,
                                    line_number=line_no,
                                    remediation="Raise IndexError when r < 0 or r >= self.rows or c < 0 or c >= self.cols.",
                                )
                            )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C10: Lowest supported dependency test
# ---------------------------------------------------------------------------


class LowestSupportedDependencyRule(BasePaperRule):
    """Enforces that APIs used in code are compatible with the declared dependency minimum."""

    @property
    def rule_id(self) -> str:
        return "R_LOWEST_SUPPORTED_DEPENDENCY"

    @property
    def name(self) -> str:
        return "Lowest Supported Dependency Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return (
            "APIs used in code must be compatible with the minimum versions declared in pyproject.toml. "
            "For example, calling np.trapezoid when numpy minimum is < 2.0.0 without fallback is prohibited."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        pyproject = ctx.read_text("pyproject.toml") if ctx.has_file("pyproject.toml") else ""

        # Check if numpy minimum is < 2.0.0 (e.g. >= 1.24)
        numpy_min_1x = bool(re.search(r'numpy\s*>=\s*1\.', pyproject))

        if numpy_min_1x:
            for path in _python_code_files(ctx):
                content = ctx.read_text(path)
                for line_no, line in enumerate(content.splitlines(), start=1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    # Calling np.trapezoid directly without fallback
                    if re.search(r"\bnp\.trapezoid\s*\(", stripped) or re.search(r"\bnumpy\.trapezoid\s*\(", stripped):
                        if "getattr" not in stripped and "trapz" not in content:
                            findings.append(
                                RuleFinding(
                                    rule_id=self.rule_id,
                                    severity=self.severity,
                                    message=(
                                        f"Direct call to 'np.trapezoid' on line {line_no} in '{path}' requires NumPy 2.0+, "
                                        f"but pyproject.toml advertises NumPy 1.x support."
                                    ),
                                    file_path=path,
                                    line_number=line_no,
                                    remediation="Use compatibility fallback: getattr(np, 'trapezoid', getattr(np, 'trapz', None))",
                                )
                            )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()

