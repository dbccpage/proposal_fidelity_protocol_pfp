"""Rules C11-C17 for supplement republication review.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import re
from pathlib import PurePosixPath
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

class ExactScalarWhitelistRule(BasePaperRule):
    """Enforces that exact calibration/arithmetic routines reject binary floating point values."""

    @property
    def rule_id(self) -> str:
        return "R_EXACT_SCALAR_WHITELIST"

    @property
    def name(self) -> str:
        return "Exact Scalar Whitelist Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return (
            "Exact arithmetic, quotient, and calibration modules must explicitly reject "
            "binary floats (float, np.floating) rather than silently stringifying them into Fractions."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            content = ctx.read_text(path)
            # Find Fraction(str(...)) stringification
            if "Fraction(str(" in content:
                # When converting arbitrary values via str(), must reject np.floating / float
                if "np.floating" not in content and "numpy.floating" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=(
                                f"Stringified Fraction coercion in '{path}' does not explicitly reject NumPy "
                                f"floating types (np.floating), allowing silent stringification of binary floats."
                            ),
                            file_path=path,
                            remediation="Add check: if isinstance(val, (float, np.floating)): raise TypeError(...).",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C12: Observer witness integrity
# ---------------------------------------------------------------------------


class ObserverWitnessIntegrityRule(BasePaperRule):
    """Enforces that observer certificates verify primitive models and reject invalid inequalities."""

    @property
    def rule_id(self) -> str:
        return "R_OBSERVER_WITNESS_INTEGRITY"

    @property
    def name(self) -> str:
        return "Observer Witness Integrity Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Observer certificates and tallies must recheck primitive models, domain coverage, "
            "and passivity inequalities (observed_J <= watched_raw <= raw_I), and reject negative "
            "tallies or ranks rather than relying on unverified boolean flags."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            if "observer" not in path:
                continue
            content = ctx.read_text(path)
            if "class PassivityCertificate" in content:
                if (
                    "row.observed_J <= row.watched_raw_tally" not in content
                    or "row.watched_raw_tally <= row.raw_I" not in content
                ):
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=(
                                f"PassivityCertificate in '{path}' does not mathematically verify "
                                f"observed_J <= watched_raw_tally <= raw_I inequalities."
                            ),
                            file_path=path,
                            remediation="Add explicit arithmetic inequality checks between observed_J, watched_raw_tally, and raw_I.",
                        )
                    )
            if "class ObserverTallies" in content:
                if "self.I < 0" not in content or "self.Lambda < 0" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"ObserverTallies in '{path}' does not check non-negativity of defect tallies (I >= 0, Lambda >= 0).",
                            file_path=path,
                            remediation="Check self.I >= 0, self.Lambda >= 0, and all J values >= 0 in ObserverTallies.verify().",
                        )
                    )
            if "class JointInjectivityCertificate" in content:
                if "r < 0" not in content and "rank < 0" not in content and "v < 0" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"JointInjectivityCertificate in '{path}' does not reject negative combined ranks.",
                            file_path=path,
                            remediation="Ensure edgewise_combined_rank values are non-negative integers.",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C13: Finite family contract
# ---------------------------------------------------------------------------


class FiniteFamilyContractRule(BasePaperRule):
    """Enforces that finite family certificates check positive cardinalities and non-empty inventory."""

    @property
    def rule_id(self) -> str:
        return "R_FINITE_FAMILY_CONTRACT"

    @property
    def name(self) -> str:
        return "Finite Family Contract Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Finite-family certificates and member classes must validate positive integer "
            "cardinalities (rejecting fractional counts and booleans), require non-empty member "
            "bounds on acceptance, and verify bound arithmetic against declared premises."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            if "family_bound" not in path:
                continue
            content = ctx.read_text(path)
            if "class FiniteFamilyMember" in content:
                if "isinstance(site_count, int)" not in content and "isinstance(self.site_count, int)" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"FiniteFamilyMember in '{path}' does not enforce integer type for site_count.",
                            file_path=path,
                            remediation="Validate isinstance(site_count, int) and site_count > 0.",
                        )
                    )
            if "class UniformFamilyBoundCertificate" in content:
                if "not self.member_bounds" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"UniformFamilyBoundCertificate in '{path}' does not verify that accepted certificates have non-empty member_bounds.",
                            file_path=path,
                            remediation="In verify(), require bool(self.member_bounds) when self.accepted is True.",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C14: Capability invariant preservation
# ---------------------------------------------------------------------------


class CapabilityInvariantPreservationRule(BasePaperRule):
    """Enforces that admitted complex capabilities preserve differential nilpotency."""

    @property
    def rule_id(self) -> str:
        return "R_CAPABILITY_INVARIANT_PRESERVATION"

    @property
    def name(self) -> str:
        return "Capability Invariant Preservation Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Admitted complex capabilities must enforce exact differential nilpotency (d1 * d0 == 0), "
            "ensure differential immutability, and validate capability instance types at consumers."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            if "cochain_presentation" not in path:
                continue
            content = ctx.read_text(path)
            if "class AdmittedComplex" in content or "class AdmittedComplexV1" in content:
                if "d1 * d0" not in content and "d1 @ d0" not in content and "d1._data" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"AdmittedComplex in '{path}' does not enforce differential nilpotency d1 * d0 == 0.",
                            file_path=path,
                            remediation="Validate that d1 * d0 is exactly zero during admission and consumer usage.",
                        )
                    )
            if "def induce(" in content:
                if "isinstance(capability, AdmittedComplexV1)" not in content and "isinstance(capability, AdmittedComplex" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"induce() in '{path}' accepts arbitrary capability objects without type validation.",
                            file_path=path,
                            remediation="Validate isinstance(capability, AdmittedComplexV1) in induce().",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C15: Derivative norm admission
# ---------------------------------------------------------------------------


class DerivativeNormAdmissionRule(BasePaperRule):
    """Enforces that numerical derivative kill tests reject NaNs, infinities, and invalid norms."""

    @property
    def rule_id(self) -> str:
        return "R_DERIVATIVE_NORM_ADMISSION"

    @property
    def name(self) -> str:
        return "Derivative Norm Admission Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Numerical derivative and defect certificates must validate generator strengths, "
            "measured norms, and tolerances as finite nonnegative reals, rejecting NaNs and negative values."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            if "short_time_defect_numerical_certificate" not in path:
                continue
            content = ctx.read_text(path)
            if "class SecondDerivativeBoundCertificate" in content:
                if "math.isnan" not in content and "np.isnan" not in content and "isfinite" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"SecondDerivativeBoundCertificate in '{path}' does not check for NaNs or non-finite norms.",
                            file_path=path,
                            remediation="Validate that g, atol, and all measured norms are finite nonnegative reals.",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C16: Artifact output separation
# ---------------------------------------------------------------------------


class ArtifactOutputSeparationRule(BasePaperRule):
    """Enforces that artifact bundle writers reject output path collisions and input overwrites."""

    @property
    def rule_id(self) -> str:
        return "R_ARTIFACT_OUTPUT_SEPARATION"

    @property
    def name(self) -> str:
        return "Artifact Output Separation Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Artifact bundle writers must reject path collisions between certificate and manifest outputs, "
            "and prevent overwriting read-only input sources or publication archives."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            if "artifact_bundle" not in path:
                continue
            content = ctx.read_text(path)
            if "def write_artifact_bundle" in content:
                if (
                    "cert_path == manifest_path" not in content
                    and "certificate_path == manifest_path" not in content
                    and ".resolve()" not in content
                ):
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"write_artifact_bundle in '{path}' does not check for certificate and manifest path aliasing.",
                            file_path=path,
                            remediation="Resolve paths and check that certificate_path != manifest_path before writing.",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# C17: Dual case factorization
# ---------------------------------------------------------------------------


class DualCaseFactorizationRule(BasePaperRule):
    """Enforces that authorization boundary deciders correctly report factors=True when fibers do not split valid."""

    @property
    def rule_id(self) -> str:
        return "R_DUAL_CASE_FACTORIZATION"

    @property
    def name(self) -> str:
        return "Dual Case Factorization Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return (
            "Authorization boundary and report-level deciders must distinguish obstruction from "
            "factorization, reporting factors=True when the fiber does not split valid (e.g. identity reports)."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _python_code_files(ctx):
            if "authorization_boundary" not in path:
                continue
            content = ctx.read_text(path)
            if "def no_report_decision" in content:
                if "factors=True" not in content and "BoundaryResult(True" not in content:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"no_report_decision in '{path}' does not return factors=True when fiber does not split valid.",
                            file_path=path,
                            remediation="Return BoundaryResult(True, ...) when fiber_splits_valid is False.",
                        )
                    )

        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()

