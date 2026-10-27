"""Packaging & File Estate Gate Rules.

AuthorityEffect: None.

Implements strict validation of manifest completeness, Windows path limits,
clean directory envelopes, and release ZIP archives.
"""

from __future__ import annotations

import re
from typing import Dict, List

from .base_rule import (
    BasePaperRule,
    PaperContext,
    RuleCategory,
    RuleFinding,
    RuleResult,
    RuleSeverity,
)

FORBIDDEN_ROOT_DIRS = {
    "dist",
    "rt",
    "dev_rips",
    "scratchpad",
    "paper_build_prep",
    "scratch",
    "legacy_omnibus",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "evidence",
}

FORBIDDEN_REVIEW_PATTERNS = [
    re.compile(r"^publication_review_.*\.md$"),
    re.compile(r"^review_validation_.*\.json$"),
    re.compile(r"^.*_swarm_dossier\.md$"),
    re.compile(r"^.*_review_report\.md$"),
]


class ManifestBijectionRule(BasePaperRule):
    """Enforces that checksum manifests match on-disk file bytes exactly with zero omission."""

    @property
    def rule_id(self) -> str:
        return "R_MANIFEST_BIJECTION"

    @property
    def name(self) -> str:
        return "Checksum Manifest Bijection"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "SHA256SUMS or MANIFEST.sha256 must match on-disk file bytes with zero omission and no self-references."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        manifest_path = "SHA256SUMS" if ctx.has_file("SHA256SUMS") else "MANIFEST.sha256"
        if not ctx.has_file(manifest_path):
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="Neither SHA256SUMS nor MANIFEST.sha256 found in package root.",
                    file_path=manifest_path,
                    remediation="Generate SHA256SUMS using tools/rebuild_release.py or scripts/regen_sha256sums.py.",
                )
            ])

        findings: List[RuleFinding] = []
        raw_manifest = ctx.read_text(manifest_path)
        manifest_entries: Dict[str, str] = {}

        for line_no, line in enumerate(raw_manifest.splitlines(), start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Malformed manifest entry on line {line_no}: '{line}'",
                        file_path=manifest_path,
                        line_number=line_no,
                    )
                )
                continue
            digest, file_name = parts[0], parts[1].lstrip("*").strip().replace("\\", "/")
            if file_name in manifest_entries:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Duplicate manifest entry for '{file_name}' on line {line_no}",
                        file_path=manifest_path,
                        line_number=line_no,
                    )
                )
            manifest_entries[file_name] = digest

        # Self-reference check
        if manifest_path in manifest_entries:
            findings.append(
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Manifest illegally contains self-hash for '{manifest_path}'",
                    file_path=manifest_path,
                    remediation="Exclude SHA256SUMS/MANIFEST.sha256 from manifest calculation.",
                )
            )

        # Outer ZIP check
        for fn in manifest_entries:
            if fn.endswith(".zip"):
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Manifest illegally indexes root release ZIP '{fn}'",
                        file_path=manifest_path,
                        remediation="Exclude release ZIP archives from manifest entries.",
                    )
                )

        # Check every indexed file exists and matches hash
        for fn, expected_digest in manifest_entries.items():
            if not ctx.has_file(fn):
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"File indexed in manifest missing from disk/payload: '{fn}'",
                        file_path=fn,
                    )
                )
            else:
                actual_digest = ctx.sha256_of(fn)
                if actual_digest.lower() != expected_digest.lower():
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Hash mismatch for '{fn}': expected {expected_digest}, computed {actual_digest}",
                            file_path=fn,
                            remediation="Recompute checksums or restore untampered file bytes.",
                        )
                    )

        # Check for unmanifested on-disk files (excluding manifests and outer archives)
        ignored_names = {
            "SHA256SUMS",
            "MANIFEST.sha256",
            "lggr_v_local_green_global_red.aux",
        }
        for on_disk in ctx.list_paths():
            if (
                on_disk in ignored_names
                or on_disk.endswith(".zip")
                or "/__pycache__/" in on_disk
                or on_disk.startswith(".lake/")
                or "/.lake/" in on_disk
            ):
                continue
            if on_disk not in manifest_entries:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Unmanifested file present in deposit: '{on_disk}'",
                        file_path=on_disk,
                        remediation="Add file to manifest or remove unrecorded file from deposit.",
                    )
                )

        if findings:
            return self.fail_result(findings, {"indexed_count": len(manifest_entries)})
        return self.pass_result({"indexed_count": len(manifest_entries)})


class WindowsMaxPathRule(BasePaperRule):
    """Enforces that no file path in the package exceeds the 250 character limit."""

    @property
    def rule_id(self) -> str:
        return "R_WINDOWS_MAX_PATH"

    @property
    def name(self) -> str:
        return "Windows MAX_PATH Depth Fence"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "No package-relative path may exceed 250 characters to prevent Win32 MAX_PATH truncation."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in ctx.list_paths():
            if len(path) > 250:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"[DEPOSIT_MAXPATH_OVERFLOW_AND_DIR_POLLUTION] Path length {len(path)} exceeds 250 character limit: '{path}'",
                        file_path=path,
                        remediation="Shorten filename or reorganize directory nesting.",
                    )
                )
        if findings:
            return self.fail_result(findings, {"violating_paths_count": len(findings)})
        return self.pass_result({"max_path_checked": max((len(p) for p in ctx.list_paths()), default=0)})


class RestrictedDirectoryStructureRule(BasePaperRule):
    """Enforces that the root folder contains only permitted primary artifacts."""

    @property
    def rule_id(self) -> str:
        return "R_RESTRICTED_DIR_STRUCTURE"

    @property
    def name(self) -> str:
        return "Restricted Top-Level Directory Law"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Paper root must contain only canonical monograph artifacts; forbidden ephemeral directories are prohibited."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in ctx.list_paths():
            parts = path.split("/")
            top = parts[0]
            if top in FORBIDDEN_ROOT_DIRS:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"[DEPOSIT_MAXPATH_OVERFLOW_AND_DIR_POLLUTION] Forbidden ephemeral or build directory in package root: '{top}/'",
                        file_path=path,
                        remediation=f"Delete or clean directory '{top}/' prior to publication.",
                    )
                )
            for part in parts[:-1]:
                if part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox"}:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"[DEPOSIT_MAXPATH_OVERFLOW_AND_DIR_POLLUTION] Forbidden transient directory detected: '{part}' in '{path}'",
                            file_path=path,
                            remediation=f"Delete transient directory '{part}' prior to publication.",
                        )
                    )
                    break
        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class NoInternalReviewDossiersRule(BasePaperRule):
    """Enforces that internal review dossiers and swarm audits do not leak into public deposit."""

    @property
    def rule_id(self) -> str:
        return "R_NO_INTERNAL_REVIEW_DOSSIERS"

    @property
    def name(self) -> str:
        return "No Internal Review Dossiers in Deposit"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Internal review dossiers, swarm reports, and ephemeral validations must not pollute public deposit."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in ctx.list_paths():
            filename = path.split("/")[-1]
            for pat in FORBIDDEN_REVIEW_PATTERNS:
                if pat.search(filename):
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Internal review document leaked into release package: '{path}'",
                            file_path=path,
                            remediation="Move internal review dossiers to _intelligence/core_paper_reviews/.",
                        )
                    )
        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class StandaloneReleaseVerifierRule(BasePaperRule):
    """Enforces that the paper repository contains an executable standalone rebuild/verification script."""

    @property
    def rule_id(self) -> str:
        return "R_RELEASE_VERIFIER_PRESENCE"

    @property
    def name(self) -> str:
        return "Standalone Release Verifier Presence"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Paper repository must contain an executable, self-contained rebuild and verification script "
            "(verify_deposit.py, tools/rebuild_release.py, scripts/verify_deposit.py, or scripts/build_deposit_zip.py)."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        valid_scripts = [
            "verify_deposit.py",
            "tools/rebuild_release.py",
            "scripts/verify_deposit.py",
            "scripts/build_deposit_zip.py",
        ]
        has_verifier = any(ctx.has_file(s) for s in valid_scripts)
        if not has_verifier:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        "[UNVERIFIED_RELEASE_SCRIPT] No standalone release verification script found "
                        "(expected verify_deposit.py, tools/rebuild_release.py, scripts/verify_deposit.py, or scripts/build_deposit_zip.py)."
                    ),
                    remediation="Add canonical verify_deposit.py or tools/rebuild_release.py to package.",
                )
            ])
        return self.pass_result({"verifiers_found": [s for s in valid_scripts if ctx.has_file(s)]})


class DualWitnessCertificateRule(BasePaperRule):
    """Enforces discrete dual-witness certificates for exactness or coboundary vanishing claims."""

    @property
    def rule_id(self) -> str:
        return "R_DUAL_WITNESS_CERTIFICATE"

    @property
    def name(self) -> str:
        return "Discrete Dual-Witness Certificate Requirement"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Mathematical papers asserting coboundary vanishing or exactness must provide dual witness certificates "
            "(witnesses/, docs/witnesses/, manifests/release_verification.json, or *witness*/*certificate*)."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        exactness_claimed = False
        exactness_triggers = ("exactness", "coboundary", "phi_1 = 0", "\\phi_1 = 0", "gamma_2 = 0", "\\gamma_2 = 0")
        for path in ctx.list_paths():
            if path.endswith(".md"):
                text = ctx.read_text(path).lower()
                if any(trig in text for trig in exactness_triggers):
                    exactness_claimed = True
                    break

        if not exactness_claimed:
            return self.pass_result({"exactness_claimed": False})

        has_witness = (
            any(
                p.startswith("witnesses/")
                or p.startswith("docs/witnesses/")
                or p == "manifests/release_verification.json"
                or "certificate" in p.lower()
                or "witness" in p.lower()
                for p in ctx.list_paths()
            )
        )
        if not has_witness:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=(
                        "[EXACTNESS_WITHOUT_DUAL_WITNESS_CERTIFICATE] Exactness or coboundary vanishing "
                        "asserted in manuscript/claim ledgers but no dedicated witnesses/ or certificate files found."
                    ),
                    remediation="Provide primal and dual cochain witness certificates or deterministic solver receipts under witnesses/.",
                )
            ], {"exactness_claimed": True, "has_witness": False})

        return self.pass_result({"exactness_claimed": True, "has_witness": True})

