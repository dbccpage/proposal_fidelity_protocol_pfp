"""Rules C01-C05 for supplement republication review.

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

class BoundPremiseSingleSourceRule(BasePaperRule):
    """Enforces that open-system defect helpers use proved curvature bounds."""

    @property
    def rule_id(self) -> str:
        return "R_BOUND_PREMISE_SINGLE_SOURCE"

    @property
    def name(self) -> str:
        return "Bound Premise Single Source Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Open-system defect lower bound helpers must route through proved global "
            "curvature bounds (e.g. 6*Lambda_*^2 = 24*(g_v+G_v)^2) and must not expose "
            "freely weakenable curvature terms like 2*(g_v+G_v)^2."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        weakened_pattern = re.compile(
            r"2\s*\*\s*\(\s*(?:g_v|gv|g)\s*\+\s*(?:G_v|Gv|G)\s*\)\s*\*\*\s*2\s*\*\s*t\s*\*\*\s*2"
        )

        for path in _python_code_files(ctx):
            content = ctx.read_text(path)
            for line_no, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if weakened_pattern.search(stripped) and "6 *" not in stripped and "24 *" not in stripped:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=(
                                f"Unproved weakened curvature term '2*(g_v+G_v)^2*t^2' found on line {line_no} "
                                f"in '{path}'. Proved bound requires 6*Lambda_*^2 = 24*(g_v+G_v)^2."
                            ),
                            file_path=path,
                            line_number=line_no,
                            remediation="Route lower-bound calculation to proved global bound 24*(g_v+G_v)^2*t^2.",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C02: Core certificate witness replay
# ---------------------------------------------------------------------------


class CoreWitnessReplayRule(BasePaperRule):
    """Enforces that certificate verifiers mathematically recheck witness contents."""

    @property
    def rule_id(self) -> str:
        return "R_CORE_WITNESS_REPLAY"

    @property
    def name(self) -> str:
        return "Core Certificate Witness Replay Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Certificate verifiers must mathematically validate witness contents: "
            "they must reject empty witnesses, check non-negativity of norm fields, "
            "and verify that witness bounds satisfy claimed relations."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            if "verify_certificate" not in path and "verify_finite" not in path:
                continue
            content = ctx.read_text(path)
            # Check if verifier checks isinstance(w, dict) but allows empty dict as valid
            if "isinstance(witness, dict)" in content or "isinstance(w, dict)" in content:
                # Must check that witness is non-empty when status is pass
                if "not witness" not in content and "len(witness) == 0" not in content and "not w" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Certificate verifier '{path}' does not check for empty witness dictionaries.",
                            file_path=path,
                            remediation="Require witness to be non-empty and validate required identity fields.",
                        )
                    )
            # Check if negative raw norms are explicitly checked
            if "raw_I" in content:
                has_nonneg_guard = any(
                    pat in content
                    for pat in ("raw_I < 0", "raw_val < 0", "val_str) < 0", "float(val_str) < 0.0", "raw_I must be non-negative")
                )
                if not has_nonneg_guard:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Certificate verifier '{path}' processes 'raw_I' without non-negativity guard.",
                            file_path=path,
                            remediation="Add explicit check: if raw_I < 0: errors.append('negative norm').",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C03: Certificate subcheck conjunction
# ---------------------------------------------------------------------------


class CertificateSubcheckConjunctionRule(BasePaperRule):
    """Enforces that parent certificates depend strictly on the conjunction of subchecks."""

    @property
    def rule_id(self) -> str:
        return "R_CERTIFICATE_SUBCHECK_CONJUNCTION"

    @property
    def name(self) -> str:
        return "Certificate Subcheck Conjunction Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Parent certificates must compute acceptance status as a strict boolean "
            "conjunction of all required subchecks (interval verification, root isolation, "
            "and numerical attainment)."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            content = ctx.read_text(path)
            # Look for pattern where universal_lower_bound_proved is set unconditionally
            # or status = "verified" without checking proof subcheck status
            for line_no, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r'["\']universal_lower_bound_proved["\']\s*:\s*True\b', stripped):
                    # Check surrounding context for condition
                    window = "\n".join(content.splitlines()[max(0, line_no - 6):min(len(content.splitlines()), line_no + 6)])
                    if "is_interval_verified" not in window and "proof.get" not in window and "proof[" not in window:
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=(
                                    f"Unconditional 'universal_lower_bound_proved: True' on line {line_no} in '{path}' "
                                    f"without checking interval and sub-root status."
                                ),
                                file_path=path,
                                line_number=line_no,
                                remediation="Make universal_lower_bound_proved conditional on proof status and interval check.",
                            )
                        )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C04: Model-bound comparative benchmark
# ---------------------------------------------------------------------------


class ModelBoundComparativeBenchmarkRule(BasePaperRule):
    """Enforces that benchmarks derive cancellation and onset from models rather than hardcoding."""

    @property
    def rule_id(self) -> str:
        return "R_MODEL_BOUND_BENCHMARK"

    @property
    def name(self) -> str:
        return "Model-Bound Comparative Benchmark Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Comparative benchmarks must not emit hardcoded commutator cancellation flags "
            "('exact_commutator_cancels = True') or apply higher-order remainder constants "
            "B_(k,m) as onset bounds without checking model geometry."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            content = ctx.read_text(path)
            for line_no, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r'["\']exact_commutator_cancels["\']\s*:\s*True\b', stripped):
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=(
                                f"Hardcoded 'exact_commutator_cancels = True' found on line {line_no} in '{path}'. "
                                f"Commutator cancellation must be computed from the Hamiltonian."
                            ),
                            file_path=path,
                            line_number=line_no,
                            remediation="Dynamically compute commutator cancellation based on model couplings and state.",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C05: Strict zip in dynamics
# ---------------------------------------------------------------------------


class StrictZipInDynamicsRule(BasePaperRule):
    """Enforces that jump/rate pairings in physical dynamics use strict=True."""

    @property
    def rule_id(self) -> str:
        return "R_STRICT_ZIP_DYNAMICS"

    @property
    def name(self) -> str:
        return "Strict Zip In Physical Dynamics Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Pairing jump operators and dissipation rates in Lindblad generators or simulators "
            "must use strict=True or explicit length assertions to prevent silent truncation."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        zip_pattern = re.compile(r"zip\s*\(\s*(?:jumps|jump_ops|L_list|operators)\s*,\s*(?:rates|gamma|gammas)\b")

        for path in _python_code_files(ctx):
            content = ctx.read_text(path)
            for line_no, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if zip_pattern.search(stripped) and "strict=True" not in stripped:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=(
                                f"Non-strict zip across jump operators and rates on line {line_no} in '{path}'. "
                                f"Mismatched lists silently drop dissipative channels."
                            ),
                            file_path=path,
                            line_number=line_no,
                            remediation="Add strict=True to zip(jumps, rates) or explicitly assert len(jumps) == len(rates).",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()

