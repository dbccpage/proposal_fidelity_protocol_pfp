"""Pure verification of source-bound Python test execution receipts."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath

from omega_engine_operads.domain.python_development_office.quality_inventory import (
    FileQualityRecord,
    QualityFinding,
    TestTierEvidence,
    TestTierRule,
)
from omega_engine_operads.domain.python_development_office.test_execution_receipt import (
    TestExecutionReceipt,
)

_PYTHON_312 = re.compile(r"^3\.12(?:\.|$)")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:/")


@dataclass(frozen=True)
class ReceiptVerificationRequest:
    """Complete immutable input to test receipt verification."""

    rules: tuple[TestTierRule, ...]
    files: tuple[FileQualityRecord, ...]
    receipts: tuple[TestExecutionReceipt, ...]
    source_sha256: str
    policy_sha256: str
    now: datetime
    max_age_hours: int


@dataclass(frozen=True)
class _ReceiptBinding:
    source_sha256: str
    policy_sha256: str
    now: datetime
    max_age: timedelta


def verify_test_execution_receipts(
    request: ReceiptVerificationRequest,
) -> tuple[tuple[TestTierEvidence, ...], tuple[QualityFinding, ...]]:
    """Verify every declared tier against exactly one bounded execution receipt."""

    if request.now.tzinfo is None:
        raise ValueError("verification clock must be timezone-aware")
    duplicate_ids = _duplicates(tuple(receipt.receipt_id for receipt in request.receipts))
    if duplicate_ids:
        raise ValueError(f"duplicate test receipt ids: {', '.join(duplicate_ids)}")
    binding = _ReceiptBinding(
        source_sha256=request.source_sha256,
        policy_sha256=request.policy_sha256,
        now=request.now.astimezone(timezone.utc),
        max_age=timedelta(hours=request.max_age_hours),
    )
    evidence, findings = _verify_declared_tiers(request, binding)
    findings.extend(_unknown_tier_findings(request))
    return tuple(evidence), tuple(findings)


def _verify_declared_tiers(
    request: ReceiptVerificationRequest,
    binding: _ReceiptBinding,
) -> tuple[list[TestTierEvidence], list[QualityFinding]]:
    evidence: list[TestTierEvidence] = []
    findings: list[QualityFinding] = []
    paths = tuple(record.path for record in request.files)
    for rule in request.rules:
        matched = tuple(path for path in paths if _matches_any(path, rule.patterns))
        tier_receipts = tuple(receipt for receipt in request.receipts if receipt.tier == rule.name)
        tier_evidence, detail = _verify_tier(
            rule=rule,
            matched=matched,
            receipts=tier_receipts,
            binding=binding,
        )
        evidence.append(tier_evidence)
        if detail is not None:
            findings.append(
                QualityFinding(
                    code=_finding_code(tier_evidence.status),
                    path=".",
                    line=1,
                    detail=f"Test tier {rule.name!r}: {detail}",
                )
            )
    return evidence, findings


def _unknown_tier_findings(
    request: ReceiptVerificationRequest,
) -> tuple[QualityFinding, ...]:
    unknown_tiers = sorted(
        {receipt.tier for receipt in request.receipts} - {rule.name for rule in request.rules}
    )
    return tuple(
        QualityFinding(
            code="UNKNOWN_TEST_RECEIPT_TIER",
            path=".",
            line=1,
            detail=f"Execution receipt declares unknown tier {tier!r}.",
        )
        for tier in unknown_tiers
    )


def _verify_tier(
    *,
    rule: TestTierRule,
    matched: tuple[str, ...],
    receipts: tuple[TestExecutionReceipt, ...],
    binding: _ReceiptBinding,
) -> tuple[TestTierEvidence, str | None]:
    if not matched:
        return _evidence(rule.name, matched, "MISSING_TEST_FILES"), "no test files matched policy"
    if not receipts:
        return _evidence(rule.name, matched, "MISSING_RECEIPT"), "execution receipt is absent"
    if len(receipts) != 1:
        detail = f"expected exactly one execution receipt, found {len(receipts)}"
        return _evidence(rule.name, matched, "INVALID_RECEIPT", detail=detail), detail
    receipt = receipts[0]
    errors = _receipt_errors(
        rule=rule,
        matched=matched,
        receipt=receipt,
        binding=binding,
    )
    if errors:
        detail = "; ".join(errors)
        return _evidence_from_receipt(receipt, matched, "INVALID_RECEIPT", detail), detail
    return _evidence_from_receipt(receipt, matched, _verified_status(rule), "verified"), None


def _receipt_errors(
    *,
    rule: TestTierRule,
    matched: tuple[str, ...],
    receipt: TestExecutionReceipt,
    binding: _ReceiptBinding,
) -> tuple[str, ...]:
    errors: list[str] = []
    if receipt.execution_kind != rule.execution_kind:
        errors.append("execution kind does not match policy")
    if receipt.asserted_status != "PASS" or receipt.exit_code != 0 or receipt.test_count <= 0:
        errors.append("PASS requires exit code zero and positive test count")
    if not _PYTHON_312.match(receipt.python_version):
        errors.append("Python version is not 3.12")
    if receipt.source_sha256 != binding.source_sha256:
        errors.append("source digest mismatch")
    if receipt.policy_sha256 != binding.policy_sha256:
        errors.append("policy digest mismatch")
    completed = receipt.completed_at.astimezone(timezone.utc)
    if completed > binding.now + timedelta(minutes=5):
        errors.append("completion timestamp is in the future")
    if completed < binding.now - binding.max_age:
        errors.append("execution receipt is stale")
    errors.extend(_target_errors(receipt, matched))
    errors.extend(_mutation_errors(rule, receipt))
    return tuple(errors)


def _target_errors(receipt: TestExecutionReceipt, matched: tuple[str, ...]) -> tuple[str, ...]:
    normalized_targets: list[str] = []
    errors: list[str] = []
    for target in receipt.target_paths:
        normalized = target.replace("\\", "/").removeprefix("./")
        pure = PurePosixPath(normalized)
        if pure.is_absolute() or _WINDOWS_ABSOLUTE.match(normalized) or ".." in pure.parts:
            errors.append(f"target path escapes repository: {target}")
            continue
        normalized_targets.append(normalized.rstrip("/"))
        command_paths = {part.replace("\\", "/").removeprefix("./") for part in receipt.command}
        if normalized not in command_paths:
            errors.append(f"target path is absent from command argv: {target}")
    if normalized_targets and not all(
        any(path == target or path.startswith(f"{target}/") for target in normalized_targets)
        for path in matched
    ):
        errors.append("receipt targets do not cover every policy-matched test file")
    return tuple(errors)


def _mutation_errors(rule: TestTierRule, receipt: TestExecutionReceipt) -> tuple[str, ...]:
    if rule.execution_kind != "mutation_engine":
        return (
            () if receipt.mutation_score is None else ("non-engine receipt claims mutation score",)
        )
    if receipt.mutation_score is None:
        return ("mutation engine receipt lacks mutation score",)
    minimum = rule.minimum_mutation_score
    if minimum is None or receipt.mutation_score < minimum:
        return (f"mutation score {receipt.mutation_score} is below required {minimum}",)
    return ()


def _evidence(
    tier: str,
    matched: tuple[str, ...],
    status: str,
    *,
    detail: str = "",
) -> TestTierEvidence:
    return TestTierEvidence(tier=tier, matched_files=matched, status=status, detail=detail)


def _evidence_from_receipt(
    receipt: TestExecutionReceipt,
    matched: tuple[str, ...],
    status: str,
    detail: str,
) -> TestTierEvidence:
    return TestTierEvidence(
        tier=receipt.tier,
        matched_files=matched,
        status=status,
        receipt_id=receipt.receipt_id,
        test_count=receipt.test_count,
        completed_at=receipt.completed_at.isoformat(),
        mutation_score=receipt.mutation_score,
        detail=detail,
    )


def _verified_status(rule: TestTierRule) -> str:
    if rule.execution_kind == "mutation_style":
        return "MUTATION_STYLE_VERIFIED"
    if rule.execution_kind == "mutation_engine":
        return "MUTATION_ENGINE_VERIFIED"
    return "VERIFIED_EXECUTION"


def _finding_code(status: str) -> str:
    return {
        "MISSING_TEST_FILES": "MISSING_TEST_TIER",
        "MISSING_RECEIPT": "MISSING_TEST_EXECUTION_RECEIPT",
        "INVALID_RECEIPT": "INVALID_TEST_EXECUTION_RECEIPT",
    }[status]


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if values.count(value) > 1}))


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    return any(
        fnmatch.fnmatchcase(normalized, pattern) or pure.match(pattern) for pattern in patterns
    )
