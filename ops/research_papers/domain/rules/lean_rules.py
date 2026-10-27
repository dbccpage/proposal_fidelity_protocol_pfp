"""Lean 4 Formal Proof Kernel Gate Rules.

AuthorityEffect: None.

Enforces Lake build configuration integrity, pinned toolchains,
total absence of proof escape hatches (sorry/admit), and clean axiom reports.
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

SORRY_PATTERN = re.compile(r"\b(sorry|admit)\b")
PLATFORM_TRIPLE_PATTERN = re.compile(r"\b(windows-gnu|linux-gnu|darwin|x86_64-|aarch64-)\b")


class LeanLakeConfigRule(BasePaperRule):
    """Enforces that lean4/ has one top-level lakefile.lean and lake-manifest.json."""

    @property
    def rule_id(self) -> str:
        return "R_LEAN_LAKE_CONFIG"

    @property
    def name(self) -> str:
        return "Lean 4 Lake Configuration Structure"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LEAN4

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Claimed Lean 4 project must have a top-level lakefile.lean and lake-manifest.json under lean4/."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        lean_files = [p for p in ctx.list_paths() if p.startswith("lean4/") and p.endswith(".lean")]
        if not lean_files:
            return self.pass_result({"lean_present": False})

        findings: List[RuleFinding] = []
        if not ctx.has_file("lean4/lakefile.lean"):
            findings.append(
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="Missing 'lean4/lakefile.lean' in Lean 4 kernel root.",
                    file_path="lean4/lakefile.lean",
                )
            )
        if not ctx.has_file("lean4/lake-manifest.json"):
            findings.append(
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="Missing 'lean4/lake-manifest.json' lockfile.",
                    file_path="lean4/lake-manifest.json",
                )
            )

        if findings:
            return self.fail_result(findings, {"lean_present": True})
        return self.pass_result({"lean_present": True})


class LeanToolchainPinnedRule(BasePaperRule):
    """Enforces that lean-toolchain exists under lean4/ and declares a pinned version."""

    @property
    def rule_id(self) -> str:
        return "R_LEAN_TOOLCHAIN_PINNED"

    @property
    def name(self) -> str:
        return "Lean Toolchain Pinning"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LEAN4

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "lean4/lean-toolchain must declare a pinned Lean 4 release version or commit hash."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        lean_files = [p for p in ctx.list_paths() if p.startswith("lean4/") and p.endswith(".lean")]
        if not lean_files:
            return self.pass_result({"lean_present": False})

        if not ctx.has_file("lean4/lean-toolchain"):
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="Missing 'lean4/lean-toolchain' file.",
                    file_path="lean4/lean-toolchain",
                    remediation="Add lean4/lean-toolchain specifying the pinned Lean version (e.g. leanprover/lean4:v4.13.0).",
                )
            ])

        content = ctx.read_text("lean4/lean-toolchain").strip()
        if not content:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="'lean4/lean-toolchain' is empty.",
                    file_path="lean4/lean-toolchain",
                )
            ])

        return self.pass_result({"toolchain": content})


class LeanNoEscapeHatchesRule(BasePaperRule):
    """Enforces that formal Lean 4 sources contain zero sorry or admit tokens."""

    @property
    def rule_id(self) -> str:
        return "R_LEAN_NO_ESCAPE_HATCHES"

    @property
    def name(self) -> str:
        return "Zero Proof Escape Hatches (No Sorry / Admit)"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LEAN4

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "All formal Lean 4 proof terms must be complete with zero sorry or admit statements."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        lean_files = [p for p in ctx.list_paths() if p.startswith("lean4/") and p.endswith(".lean")]
        findings: List[RuleFinding] = []

        for p in lean_files:
            content = ctx.read_text(p)
            for line_no, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("--"):
                    continue
                match = SORRY_PATTERN.search(stripped)
                if match:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Illegal proof escape hatch '{match.group(1)}' on line {line_no} in '{p}'",
                            file_path=p,
                            line_number=line_no,
                            remediation="Complete the formal proof term or retire the unproven lemma.",
                        )
                    )

        if findings:
            return self.fail_result(findings, {"lean_file_count": len(lean_files)})
        return self.pass_result({"lean_file_count": len(lean_files)})


class LeanAxiomReportRule(BasePaperRule):
    """Enforces that lean4/axiom_report.txt exists and contains no host platform target triples."""

    @property
    def rule_id(self) -> str:
        return "R_LEAN_AXIOM_REPORT"

    @property
    def name(self) -> str:
        return "Axiom Report Honesty & Cleanliness"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LEAN4

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "lean4/axiom_report.txt must exist, be non-empty, and contain zero host architecture triples."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        lean_files = [p for p in ctx.list_paths() if p.startswith("lean4/") and p.endswith(".lean")]
        if not lean_files:
            return self.pass_result({"lean_present": False})

        if not ctx.has_file("lean4/axiom_report.txt"):
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="Missing 'lean4/axiom_report.txt' file.",
                    file_path="lean4/axiom_report.txt",
                    remediation="Generate lean4/axiom_report.txt by executing #print axioms on core theorems.",
                )
            ])

        content = ctx.read_text("lean4/axiom_report.txt").strip()
        if not content:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="'lean4/axiom_report.txt' is empty.",
                    file_path="lean4/axiom_report.txt",
                )
            ])

        match = PLATFORM_TRIPLE_PATTERN.search(content)
        if match:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Axiom report contains host platform triple: '{match.group(1)}'",
                    file_path="lean4/axiom_report.txt",
                    remediation="Strip compiler environment triples from formal axiom reports.",
                )
            ])

        return self.pass_result({"axiom_report_bytes": len(content.encode("utf-8"))})


# ---------------------------------------------------------------------------
# C20: Lean axiom report per-declaration fidelity
# ---------------------------------------------------------------------------


class LeanAxiomReportPerDeclarationFidelityRule(BasePaperRule):
    """Enforces that lean4/axiom_report.txt records faithful dependencies and fully-qualified targets."""

    @property
    def rule_id(self) -> str:
        return "R_LEAN_AXIOM_REPORT_FIDELITY"

    @property
    def name(self) -> str:
        return "Lean Axiom Report Per-Declaration Fidelity"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LEAN4

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "lean4/axiom_report.txt must record genuine per-declaration dependencies with fully qualified "
            "target names, use LF-only line endings, and never assign blanket axiom sets to definitional proofs."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        if not ctx.has_file("lean4/axiom_report.txt"):
            return self.pass_result({"lean_present": False})

        findings: List[RuleFinding] = []
        raw_bytes = ctx.read_bytes("lean4/axiom_report.txt")
        if b"\r\n" in raw_bytes:
            findings.append(
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="lean4/axiom_report.txt contains Windows CRLF line endings; must use LF only.",
                    file_path="lean4/axiom_report.txt",
                    remediation="Normalize line endings to LF before hashing and publication.",
                )
            )

        content = ctx.read_text("lean4/axiom_report.txt")

        # Check for blanket assignment to definitional theorems
        definitional_theorems = (
            "AuthorizationBoundary.extra_recovers_negative",
            "PO000ProjectionFactor.residual_not_coboundary_without_adapter",
        )
        for thm in definitional_theorems:
            pattern = re.compile(rf"['\"]?{re.escape(thm)}['\"]?\s+depends on axioms:\s*\[([^\]]+)\]")
            match = pattern.search(content)
            if match:
                axioms = [a.strip() for a in match.group(1).split(",") if a.strip()]
                if any(ax in ("Classical.choice", "Quot.sound", "propext") for ax in axioms):
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=(
                                f"Axiom report assigns blanket axioms {axioms} to definitional theorem '{thm}', "
                                f"which is proved without axioms."
                            ),
                            file_path="lean4/axiom_report.txt",
                            remediation="Regenerate axiom report from actual #print axioms query results.",
                        )
                    )

        # Check for bare unqualified short-name targets
        unqualified_short_names = (
            "first_order_k1",
            "double_factor_k1",
            "double_factor_k2",
        )
        for short_name in unqualified_short_names:
            if re.search(rf"^['\"]?{re.escape(short_name)}['\"]?\s+depends on axioms:", content, re.MULTILINE):
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=(
                            f"Axiom report stores bare unqualified name '{short_name}' without its defining module namespace."
                        ),
                        file_path="lean4/axiom_report.txt",
                        remediation="Store fully qualified declaration identities in the axiom report census.",
                    )
                )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


# ---------------------------------------------------------------------------
# C21: Lean nonvacuous carrier premises
# ---------------------------------------------------------------------------


class LeanNonvacuousCarrierPremisesRule(BasePaperRule):
    """Enforces that real-scalar commutator models are explicitly qualified as zero-bracket controls."""

    @property
    def rule_id(self) -> str:
        return "R_LEAN_NONVACUOUS_PREMISES"

    @property
    def name(self) -> str:
        return "Lean Nonvacuous Carrier Premises Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LEAN4

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return (
            "Lean modules defining Lie brackets over commutative rings where [A, B] = 0 identically must not "
            "claim to mechanize non-zero commutator defect rates without explicit zero-commutator toy qualification."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        lean_files = [p for p in ctx.list_paths() if p.startswith("lean4/") and p.endswith(".lean")]
        findings: List[RuleFinding] = []

        for p in lean_files:
            content = ctx.read_text(p)
            # Detect real-scalar commutator bracket on Real
            if "bracket" in content and ("(A B : ℝ)" in content or "(A B : Real)" in content):
                if "doubleBracket" in content and "≠ 0" in content:
                    # Must be explicitly qualified as a toy control in docstring / header
                    if "toy" not in content.lower() and "zero-commutator" not in content.lower():
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=(
                                    f"File '{p}' defines a real-scalar commutator bracket that vanishes identically "
                                    f"([A,B]=0), but assumes non-zero double bracket without explicit toy control qualification."
                                ),
                                file_path=p,
                                remediation="Qualify the module as an explicit commutative zero-bracket toy control.",
                            )
                        )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


# ---------------------------------------------------------------------------
# C22: Lean formal statement scope match
# ---------------------------------------------------------------------------


class LeanFormalStatementScopeMatchRule(BasePaperRule):
    """Enforces that double-commutator bounds records reflect their actual mathematical contents."""

    @property
    def rule_id(self) -> str:
        return "R_LEAN_STATEMENT_SCOPE_MATCH"

    @property
    def name(self) -> str:
        return "Lean Formal Statement Scope Match Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LEAN4

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return (
            "Structured hypothesis records titled or described as double-commutator bounds must not contain "
            "merely coefficient nonnegativity without an actual bounded commutator quantity, unless explicitly "
            "scoped to factor nonnegativity arithmetic."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        lean_files = [p for p in ctx.list_paths() if p.startswith("lean4/") and p.endswith(".lean")]
        findings: List[RuleFinding] = []

        for p in lean_files:
            content = ctx.read_text(p)
            if "structure DoubleCommutatorBounds" in content:
                # If the structure only asserts factor * A_norm >= 0, check that scope is documented as arithmetic/nonnegativity
                if "firstOrderFactor" in content and "≥ 0" in content:
                    if (
                        "arithmetic" not in content.lower()
                        and "non-negativity" not in content.lower()
                        and "nonnegativity" not in content.lower()
                    ):
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=(
                                    f"DoubleCommutatorBounds in '{p}' asserts only nonnegativity of multiplier factors "
                                    f"rather than upper bounds on actual operator commutators."
                                ),
                                file_path=p,
                                remediation="Scope the record to scalar factor arithmetic and nonnegativity.",
                            )
                        )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


# ---------------------------------------------------------------------------
# C23: Lean scale bound premise binding
# ---------------------------------------------------------------------------


class LeanScaleBoundPremiseBindingRule(BasePaperRule):
    """Enforces that acceleration and scale bounds do not impose contradictory uniform infima."""

    @property
    def rule_id(self) -> str:
        return "R_LEAN_SCALE_BOUND_PREMISE"

    @property
    def name(self) -> str:
        return "Lean Scale Bound Premise Binding Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LEAN4

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Extrinsic acceleration bounds must not require a fixed positive scalar a_e > 0 to satisfy "
            "a_e <= C * g^2 for all g > 0, which forces a_e = 0 by contradiction. Quarantined parked drafts "
            "must be clearly documented as non-claim-bearing."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        lean_files = [p for p in ctx.list_paths() if p.startswith("lean4/") and p.endswith(".lean")]
        findings: List[RuleFinding] = []

        for p in lean_files:
            content = ctx.read_text(p)
            if "∀ (g : Real), g > 0 → a_e ≤" in content or "∀ (g : ℝ), g > 0 → a_e ≤" in content:
                # If a file has this contradictory premise, it must be explicitly quarantined and non-claim-bearing
                if "release-critical" in content.lower():
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=(
                                f"File '{p}' claims 'release-critical' advancements but contains a contradictory "
                                f"premise (forall g > 0, a_e <= 24*g^2) that forces a_e = 0."
                            ),
                            file_path=p,
                            remediation="Align docstrings with quarantined parked draft status and remove 'release-critical' claims.",
                        )
                    )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


LEAN_RULES: tuple[type[BasePaperRule], ...] = (
    LeanLakeConfigRule,
    LeanToolchainPinnedRule,
    LeanNoEscapeHatchesRule,
    LeanAxiomReportRule,
    LeanAxiomReportPerDeclarationFidelityRule,
    LeanNonvacuousCarrierPremisesRule,
    LeanFormalStatementScopeMatchRule,
    LeanScaleBoundPremiseBindingRule,
)

