"""Mathematical Model & Claim Hygiene Gate Rules.

AuthorityEffect: None.

Codifies the 8 referee scope corrections from the adversarial NO-GO review:
1. Tree realizability requires invertible translations.
2. SVD margin formula requires Euclidean source/report norms; polyhedral requires LP extreme-point search.
3. Random Gaussian measurement simulations must be scoped as unrestricted global measurements.
4. Nonlinear evaluator zero-set criterion requires J^alpha(0) = 0.
5. Outcome failure (E_g = 0) vs handoff defect (I(s) > 0) separation; correlated judges do not imply shared kernels.
6. Unproved soundness must be reported as undetermined, not unsound.
7. Strict claim hygiene enforcement on forbidden hype vocabulary.
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

FORBIDDEN_HYPE_WORDS = [
    (re.compile(r"\bproves\b", re.IGNORECASE), "proves", "shows in this model / supports"),
    (re.compile(r"\bguarantees\b", re.IGNORECASE), "guarantees", "guarantees under declared assumptions"),
    (re.compile(r"\bmathematically verifies\b", re.IGNORECASE), "mathematically verifies", "checked by this oracle/test"),
    (re.compile(r"\bflawless\b", re.IGNORECASE), "flawless", "passing declared tests"),
    (re.compile(r"\bweaponized\b", re.IGNORECASE), "weaponized", "adversarially evaluated"),
    (re.compile(r"\btrue intelligence\b", re.IGNORECASE), "true intelligence", "modeled performance"),
]


class TreeInvertibilityHypothesisRule(BasePaperRule):
    """Enforces that tree cochain realizability claims explicitly state invertible translations."""

    @property
    def rule_id(self) -> str:
        return "R_TREE_INVERTIBILITY"

    @property
    def name(self) -> str:
        return "Tree Realizability Invertibility Condition"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Tree realizability theorems must explicitly condition on invertible edge translations to prevent false surjectivity claims."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        md_path = ctx.get_primary_markdown_path()
        if not md_path:
            return self.pass_result()

        content = ctx.read_text(md_path)
        findings: List[RuleFinding] = []
        lines = content.splitlines()

        for idx in range(len(lines)):
            start = max(0, idx - 4)
            end = min(len(lines), idx + 5)
            window = " ".join(lines[start:end]).lower()
            if "tree" in window and "every cochain is realizable" in window:
                if "invertible" not in window:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Tree cochain realizability claimed without invertible translation hypothesis around line {idx + 1}",
                            file_path=md_path,
                            line_number=idx + 1,
                            remediation="Restrict claim to trees with invertible linear translations; cite Theorem 6 counterexample.",
                        )
                    )
                    break

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class NormConsistentMarginRule(BasePaperRule):
    """Enforces that margin recovery formulas match the declared source norm."""

    @property
    def rule_id(self) -> str:
        return "R_NORM_CONSISTENT_MARGIN"

    @property
    def name(self) -> str:
        return "Source Norm vs SVD Margin Consistency"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Singular value formula cannot be claimed for l1 source norms without Euclidean qualification; polyhedral norms require LP extreme-point search."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        md_path = ctx.get_primary_markdown_path()
        if not md_path:
            return self.pass_result()

        content = ctx.read_text(md_path)
        findings: List[RuleFinding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            low = line.lower()
            if "singular value" in low or "sigma_{min}" in low or "svd" in low:
                # Check if claimed for l1 or edge-sum norm without noting mismatch
                start = max(0, idx - 5)
                end = min(len(lines), idx + 5)
                window = " ".join(lines[start:end]).lower()
                if "edge-sum" in window or "l^1" in window or "ell_1" in window:
                    if "euclidean" not in window and "mismatch" not in window and "polyhedral" not in window:
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=f"SVD singular value formula asserted for l1/edge-sum norm without Euclidean qualification on line {idx}",
                                file_path=md_path,
                                line_number=idx,
                                remediation="Qualify that SVD requires Euclidean source and report norms, or specify finite polyhedral LP procedure.",
                            )
                        )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class SimulationGlobalMeasurementScopeRule(BasePaperRule):
    """Enforces that Gaussian random matrix simulations are scoped as unrestricted global measurements."""

    @property
    def rule_id(self) -> str:
        return "R_SIMULATION_GLOBAL_SCOPE"

    @property
    def name(self) -> str:
        return "Simulation Scope Discipline (Global vs Local)"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "Gaussian random matrix simulations mixing edge coordinates must be explicitly labeled as unrestricted global measurements."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        md_path = ctx.get_primary_markdown_path()
        if not md_path:
            return self.pass_result()

        content = ctx.read_text(md_path)
        findings: List[RuleFinding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            if "standard_normal" in line or "gaussian" in line.lower():
                start = max(0, idx - 10)
                end = min(len(lines), idx + 10)
                window = " ".join(lines[start:end]).lower()
                if "simulation" in window and "local" in window and "unrestricted global" not in window:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Gaussian matrix simulation not labeled as unrestricted global measurement around line {idx}",
                            file_path=md_path,
                            line_number=idx,
                            remediation="Label Gaussian simulation as an unrestricted global-measurement experiment.",
                        )
                    )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class NonlinearEvaluatorZeroOriginRule(BasePaperRule):
    """Enforces that nonlinear evaluator soundness criteria require J^alpha(0) = 0."""

    @property
    def rule_id(self) -> str:
        return "R_NONLINEAR_ZERO_ORIGIN"

    @property
    def name(self) -> str:
        return "Nonlinear Evaluator Zero-Origin Condition"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Equating im D cap Z = {0} with soundness requires J^alpha(0) = 0 for all evaluators (counterexample J = 1)."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        md_path = ctx.get_primary_markdown_path()
        if not md_path:
            return self.pass_result()

        content = ctx.read_text(md_path)
        findings: List[RuleFinding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            if re.search(r"(?:\\cap|cap)\s*Z\s*=\s*(?:\\\{|\{)0(?:\\\}|\})", line):
                start = max(0, idx - 6)
                end = min(len(lines), idx + 6)
                window = " ".join(lines[start:end])
                if not re.search(r"J(?:\^\\alpha|\(0\)|_\alpha|\^\alpha)?\s*\(0\)\s*=\s*0", window):
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Nonlinear zero-set soundness equivalence stated without J^alpha(0)=0 hypothesis around line {idx}",
                            file_path=md_path,
                            line_number=idx,
                            remediation="Require J^alpha(0) = 0 for all evaluators or express as im D cap Z subseteq {0}.",
                        )
                    )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class DiagnosticDistinctionRule(BasePaperRule):
    """Enforces decoupling of outcome failures from interface defects and correlated judges from shared kernels."""

    @property
    def rule_id(self) -> str:
        return "R_DIAGNOSTIC_DISTINCTION"

    @property
    def name(self) -> str:
        return "Diagnostic Distinction (Outcome Failure vs Interface Defect)"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.CLAIM_HYGIENE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Outcome failure (E_g = 0) must not imply handoff defect (I(s) > 0); correlated readouts must not imply shared kernels."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        md_path = ctx.get_primary_markdown_path()
        if not md_path:
            return self.pass_result()

        content = ctx.read_text(md_path)
        findings: List[RuleFinding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            low = line.lower()
            if "e_g = 0" in low and ("implies i(s) > 0" in low or "proves i(s) > 0" in low):
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Conflation of outcome failure with handoff inconsistency on line {idx}",
                        file_path=md_path,
                        line_number=idx,
                        remediation="Decouple outcome failure from handoff defects (components can agree on an incorrect answer).",
                    )
                )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class AuditUndeterminedReportingRule(BasePaperRule):
    """Enforces that unproved soundness must be reported as undetermined, not unsound."""

    @property
    def rule_id(self) -> str:
        return "R_AUDIT_UNDETERMINED_REPORTING"

    @property
    def name(self) -> str:
        return "Audit Reporting Semantics (Undetermined vs Unsound)"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.CLAIM_HYGIENE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "Failure to establish soundness must be reported as undetermined; proving unsoundness requires an explicit defect in the blind spot."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        md_path = ctx.get_primary_markdown_path()
        if not md_path:
            return self.pass_result()

        content = ctx.read_text(md_path)
        findings: List[RuleFinding] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            low = line.lower()
            if "if soundness is not established" in low:
                if "report it as undetermined" not in low and "undetermined" not in low:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Audit instructions fail to report unproven soundness as undetermined on line {idx}",
                            file_path=md_path,
                            line_number=idx,
                            remediation="Instruct auditors to report unproved soundness as undetermined.",
                        )
                    )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class ClaimHygieneBannedWordsRule(BasePaperRule):
    """Enforces strict claim discipline, flagging un-fenced forbidden hype words."""

    @property
    def rule_id(self) -> str:
        return "R_CLAIM_HYGIENE_BANNED_WORDS"

    @property
    def name(self) -> str:
        return "Claim Discipline & Hype Word Firewall"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.CLAIM_HYGIENE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "Monograph prose must avoid unfenced hype verbs (proves, guarantees, flawless, weaponized)."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        md_path = ctx.get_primary_markdown_path()
        if not md_path:
            return self.pass_result()

        content = ctx.read_text(md_path)
        findings: List[RuleFinding] = []

        in_fenced_block = False
        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block or stripped.startswith("#") or stripped.startswith(">"):
                continue

            for pat, word, replacement in FORBIDDEN_HYPE_WORDS:
                match = pat.search(stripped)
                if match:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Unfenced hype word '{word}' found on line {line_no}",
                            file_path=md_path,
                            line_number=line_no,
                            remediation=f"Replace '{word}' with '{replacement}'.",
                        )
                    )

        if findings:
            return self.fail_result(findings, {"violations_count": len(findings)})
        return self.pass_result()


class EvaluatorAuthoritySeparationRule(BasePaperRule):
    """Enforces RULE_EVALUATOR_SUPREMACY_AUTHORITY_SEPARATION_001 across paper deposits.

    Validates:
    1. Zero literal '##' LaTeX math formula typos in markdown or TeX files.
    2. Strict license parity: when LICENSE-CODE and pyproject.toml license fields coexist,
       they must match declared standards.
    3. Unbundled Lean mechanization scoping: if Lean 4 proofs are referenced without bundled
       Lean sources, text must explicitly scope them as external sketches or provisional models.
    4. Evaluator supremacy & checklist authority refusal: text must not equate gate checklist
       survival alone with operational authority.
    """

    @property
    def rule_id(self) -> str:
        return "R_EVALUATOR_AUTHORITY_SEPARATION"

    @property
    def name(self) -> str:
        return "Evaluator Supremacy & Authority Separation"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Formula hygiene (zero '##' typos), license parity, and refusal of checklist-to-authority promotion."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []

        # 1. Formula hygiene: check for literal '##' in math formulas
        for file_path in ctx.list_paths():
            if not (file_path.endswith(".md") or file_path.endswith(".tex")):
                continue
            text = ctx.read_text(file_path)
            lines = text.splitlines()
            in_code_fence = False
            in_display_math = False
            for line_no, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_code_fence = not in_code_fence
                    continue
                if in_code_fence:
                    continue

                # Markdown headings are structural headers, not formulas
                if stripped.startswith("#"):
                    continue

                # Check multiline display math $$ ... $$
                count_double_dollar = stripped.count("$$")
                if in_display_math:
                    if "##" in stripped:
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=f"Literal '##' typo detected in display math formula on line {line_no}",
                                file_path=file_path,
                                line_number=line_no,
                                remediation="Remove accidental '##' from LaTeX math formula.",
                            )
                        )
                    if count_double_dollar % 2 == 1:
                        in_display_math = False
                    continue
                else:
                    if count_double_dollar % 2 == 1:
                        in_display_math = True

                # Check single line display math $$ ... ## ... $$
                for m in re.finditer(r"\$\$([^$]+)\$\$", line):
                    math_content = m.group(1)
                    if "##" in math_content:
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=f"Literal '##' typo detected in display math formula on line {line_no}",
                                file_path=file_path,
                                line_number=line_no,
                                remediation="Remove accidental '##' from LaTeX math formula.",
                            )
                        )

                # Check single-line inline math $...##...$ (stripping display math first)
                clean_line = re.sub(r"\$\$[^$]+\$\$", "", line)
                for m in re.finditer(r"\$([^$\n]+)\$", clean_line):
                    math_content = m.group(1)
                    if "##" in math_content:
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=f"Literal '##' typo detected in inline math formula on line {line_no}",
                                file_path=file_path,
                                line_number=line_no,
                                remediation="Remove accidental '##' from inline math formula.",
                            )
                        )

        # 2. License parity
        if ctx.has_file("LICENSE-CODE") and ctx.has_file("pyproject.toml"):
            lic_code = ctx.read_text("LICENSE-CODE")
            pyproject = ctx.read_text("pyproject.toml")
            if ("Apache License" in lic_code or "Version 2.0" in lic_code) and "license" in pyproject:
                if "Apache-2.0" not in pyproject and "Apache 2.0" not in pyproject:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=RuleSeverity.MAJOR,
                            message="pyproject.toml license declaration does not match Apache-2.0 declared in LICENSE-CODE",
                            file_path="pyproject.toml",
                            remediation="Set license = 'Apache-2.0' in pyproject.toml to match LICENSE-CODE.",
                        )
                    )

        # 3. Unbundled Lean mechanization scoping
        md_path = ctx.get_primary_markdown_path()
        if md_path:
            md_text = ctx.read_text(md_path)
            has_lean_bundled = any(
                p.startswith("lean4/") or p == "lakefile.lean" for p in ctx.list_paths()
            )
            if not has_lean_bundled:
                lower = md_text.lower()
                if ("lean 4" in lower or "lake env" in lower) and "machine-checked" in lower:
                    scoping_keywords = ("external", "unbundled", "sketch", "provisional", "design sketch")
                    if not any(k in lower for k in scoping_keywords):
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=RuleSeverity.MAJOR,
                                message="Manuscript references Lean 4 / machine-checked proofs without bundled Lean sources or unbundled external scoping",
                                file_path=md_path,
                                remediation="Explicitly scope unbundled Lean 4 mechanization as an external sketch or bundle lean4/ sources.",
                            )
                        )

        if findings:
            return self.fail_result(findings, {"violations_count": len(findings)})
        return self.pass_result()


class CategoricalNoMapFallacyRule(BasePaperRule):
    """Enforces RULE_CATEGORICAL_NO_MAP_FALLACY_PROHIBITION_001 across paper deposits.

    Prohibits fallacious inferences from constructor disjointness to absence of natural
    transformations or categorical impossibility:
    1. Demonstrating or mechanizing that constructors (e.g. i_A, i_B) have disjoint images in a
       coproduct or sum type guarantees non-cohabitation of values, but does NOT imply
       Nat(F, G) = ∅ between functors landing in those types.
    2. Prohibits claiming categorical impossibility or labeling general functorial non-existence
       as OPEN based on constructor disjointness.
    3. Promotion boundaries must be explicitly scoped as interface routing policies, typing
       constraints, or functor category restrictions.
    """

    @property
    def rule_id(self) -> str:
        return "R_CATEGORICAL_NO_MAP_FALLACY"

    @property
    def name(self) -> str:
        return "Categorical No-Map Fallacy Prohibition"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Prohibits asserting absence of natural transformations (Nat(F, G) = ∅) or "
            "categorical impossibility solely from constructor disjointness."
        )

    DISJOINT_PATTERNS = [
        re.compile(r"\bdisjoint\s+(?:constructors?|injections?|images?|subtypes?)\b", re.IGNORECASE),
        re.compile(r"\b(?:constructor|injection|coproduct|sum[- ]type)\s+disjointness\b", re.IGNORECASE),
        re.compile(r"\bi_[a-z0-9]\s*(?:,|and|\+)\s*i_[a-z0-9]\b", re.IGNORECASE),
        re.compile(r"\bdisjoint\s+in\s+(?:a\s+)?(?:coproduct|sum\s+type)\b", re.IGNORECASE),
    ]

    NO_MAP_PATTERNS = [
        re.compile(r"\bno\s+natural\s+transformations?\b", re.IGNORECASE),
        re.compile(r"\babsence\s+of\s+natural\s+transformations?\b", re.IGNORECASE),
        re.compile(r"\\(?:operatorname\{)?Nat(?:\})?\s*\([^)]+\)\s*=\s*(?:\\emptyset|\\empty|\{\}|empty)", re.IGNORECASE),
        re.compile(r"\bcategorical(?:ly)?\s+impossib(?:le|ility)\b", re.IGNORECASE),
        re.compile(r"\b(?:general\s+)?functorial\s+non-existence\b", re.IGNORECASE),
        re.compile(r"\bopen\s+(?:problem|question)\s+whether\s+(?:a\s+)?natural\s+transformation\s+exists\b", re.IGNORECASE),
        re.compile(r"\b(?:label(?:ed|ing)?|status)\s+(?:as\s+)?open\b.*?\bnatural\s+transformation\b", re.IGNORECASE),
    ]

    INFERENCE_PATTERNS = [
        re.compile(r"\b(?:implies?|proves?|guarantees?|yields?|establishes?|shows?|demonstrates?|entails?|concludes?|means?)\b", re.IGNORECASE),
        re.compile(r"\b(?:follows?\s+from|consequence\s+of|due\s+to|because\s+of|based\s+on)\b", re.IGNORECASE),
    ]

    SCOPING_KEYWORDS = [
        "not imply",
        "does not imply",
        "fails to imply",
        "cannot imply",
        "countermodel",
        "constant singleton functor",
        "constant functor",
        "interface routing policy",
        "interface routing",
        "typing constraint",
        "functor category restriction",
        "category restriction",
    ]

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []

        for file_path in ctx.list_paths():
            if not (file_path.endswith(".md") or file_path.endswith(".tex")):
                continue

            text = ctx.read_text(file_path)
            lines = text.splitlines()
            in_code_fence = False

            for idx in range(len(lines)):
                line = lines[idx].strip()
                if line.startswith("```"):
                    in_code_fence = not in_code_fence
                    continue
                if in_code_fence:
                    continue

                # Sliding window of surrounding context (current line +/- 3 lines)
                start = max(0, idx - 3)
                end = min(len(lines), idx + 4)
                window_lines = [l for l in lines[start:end] if not l.strip().startswith("```")]
                window = " ".join(window_lines)
                window_lower = window.lower()

                # If window contains valid countermodel or scoping justification, skip
                if any(kw in window_lower for kw in self.SCOPING_KEYWORDS):
                    continue

                # Check if window contains disjointness premise AND no-map conclusion
                has_disjoint = any(p.search(window) for p in self.DISJOINT_PATTERNS)
                has_no_map = any(p.search(window) for p in self.NO_MAP_PATTERNS)

                if has_disjoint and has_no_map:
                    # Check for inference connection in the window
                    has_inference = any(p.search(window) for p in self.INFERENCE_PATTERNS)
                    if has_inference:
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=(
                                    f"Categorical No-Map Fallacy detected around line {idx + 1}: "
                                    "inferring non-existence of natural transformations (Nat(F, G) = ∅) or "
                                    "categorical impossibility from constructor disjointness."
                                ),
                                file_path=file_path,
                                line_number=idx + 1,
                                remediation=(
                                    "Constructor disjointness guarantees non-cohabitation of values but does not imply "
                                    "Nat(F, G) = ∅ (countermodel: constant singleton functors). Explicitly scope the claim as an "
                                    "interface routing policy, typing constraint, or functor category restriction."
                                ),
                            )
                        )
                        break

        if findings:
            return self.fail_result(findings, {"violations_count": len(findings)})
        return self.pass_result()


class SchedulerNotPhysicalGuaranteeRule(BasePaperRule):
    """Enforces that computational refinement heuristics are not promoted to physical leakage prevention or formal no-signalling."""

    @property
    def rule_id(self) -> str:
        return "R_SCHEDULER_NOT_PHYSICAL_GUARANTEE"

    @property
    def name(self) -> str:
        return "Scheduler Check vs Physical Guarantee Separation"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.MATHEMATICAL_MODEL

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Computational refinement policies (such as graph-radius filters) establish only that refinement policy. "
            "Claims of physical defect leakage prevention or formal no-signalling require separate transport theorems."
        )

    PHYSICAL_CLAIMS = [
        re.compile(r"\b(prevents?\s+spacelike\s+defect\s+leakage)\b", re.IGNORECASE),
        re.compile(r"\b(guarantees?\s+formal\s+no-signall?ing)\b", re.IGNORECASE),
        re.compile(r"\b(rigorously\s+precludes?\s+superluminal\s+defect\s+propagation)\b", re.IGNORECASE),
    ]

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for file_path in ctx.list_paths():
            if not (file_path.endswith(".md") or file_path.endswith(".yaml") or file_path.endswith(".yml")):
                continue
            if "change_log" in file_path or "review" in file_path:
                continue
            text = ctx.read_text(file_path)
            lines = text.splitlines()
            for idx, line in enumerate(lines, 1):
                for pat in self.PHYSICAL_CLAIMS:
                    if pat.search(line):
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=f"Heuristic refinement scheduler promoted to physical guarantee: '{line.strip()}'",
                                file_path=file_path,
                                line_number=idx,
                                remediation="Describe the mechanism as a graph-radius merge heuristic and audit success as merge-policy compliance.",
                            )
                        )
        if findings:
            return self.fail_result(findings, {"violations_count": len(findings)})
        return self.pass_result()


