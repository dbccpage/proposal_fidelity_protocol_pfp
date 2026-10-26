"""Product Planning Office Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    EpicClaimGate = audit_claims
    EpicCriteriaAuditor = audit_epics
    EpicManifestAuditor = audit_epic_manifest
    from omega_engine_product_planning_office.domain.manifest_models import CONTENT_ENTRY_KEYS, EPIC_DIRECTORY, EPIC_FILENAME_RE, EXPECTED_EPIC_COUNT, EXPECTED_SOURCE_SNAPSHOT_COUNT, HASH_ALGORITHM, MANIFEST_PATH, OIKONOMIA_STATUSES, SCHEMA_VERSION, SHA256_RE, SOURCE_ENTRY_KEYS, SOURCE_SNAPSHOT_PATH, TOP_LEVEL_KEYS, EpicManifestAuditReport, EpicManifestError, fail, require_exact_keys, require_exact_type, validate_entry, validate_entry_list, validate_nonnegative_int, validate_repo_path, validate_sha256
    from omega_engine_product_planning_office.domain.manifest_hasher import compute_content_set_sha256, line_profile
    from omega_engine_product_planning_office.domain.policy import extract_markdown_field, verify_epic_policy
    from omega_engine_product_planning_office.domain.protocols import EpicManifestAuditProtocol, EpicManifestStorageProtocol
    from omega_engine_product_planning_office.domain.epic_claim_gate import StaleClaim, UnresolvedSubject, audit as audit_claims, audit_documents as audit_claim_documents, audit_unreachability
    from omega_engine_product_planning_office.domain.epic_criteria_audit import EpicCriteriaError, EpicCriteriaFinding, TargetFinding, audit_epics, audit_targets, audit_epic_file, audit_epic_text, format_report, format_target_report
    from omega_engine_product_planning_office.use_cases.epic_manifest_audit import audit_epic_manifest, rebuild_manifest




__all__ = ['CONTENT_ENTRY_KEYS', 'EPIC_DIRECTORY', 'EPIC_FILENAME_RE', 'EXPECTED_EPIC_COUNT', 'EXPECTED_SOURCE_SNAPSHOT_COUNT', 'HASH_ALGORITHM', 'MANIFEST_PATH', 'OIKONOMIA_STATUSES', 'SCHEMA_VERSION', 'SHA256_RE', 'SOURCE_ENTRY_KEYS', 'SOURCE_SNAPSHOT_PATH', 'TOP_LEVEL_KEYS', 'EpicManifestAuditReport', 'EpicManifestError', 'EpicManifestAuditProtocol', 'EpicManifestStorageProtocol', 'fail', 'require_exact_keys', 'require_exact_type', 'validate_entry', 'validate_entry_list', 'validate_nonnegative_int', 'validate_repo_path', 'validate_sha256', 'compute_content_set_sha256', 'line_profile', 'extract_markdown_field', 'verify_epic_policy', 'StaleClaim', 'UnresolvedSubject', 'audit_claims', 'audit_claim_documents', 'audit_unreachability', 'EpicClaimGate', 'EpicCriteriaError', 'EpicCriteriaFinding', 'TargetFinding', 'audit_epics', 'audit_targets', 'audit_epic_file', 'audit_epic_text', 'format_report', 'format_target_report', 'EpicCriteriaAuditor', 'audit_epic_manifest', 'rebuild_manifest', 'EpicManifestAuditor']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'EpicClaimGate': ('omega_engine_product_planning_office.domain.epic_claim_gate', 'audit'),
    'EpicCriteriaAuditor': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'audit_epics'),
    'EpicManifestAuditor': ('omega_engine_product_planning_office.use_cases.epic_manifest_audit', 'audit_epic_manifest'),
    'CONTENT_ENTRY_KEYS': ('omega_engine_product_planning_office.domain.manifest_models', 'CONTENT_ENTRY_KEYS'),
    'EPIC_DIRECTORY': ('omega_engine_product_planning_office.domain.manifest_models', 'EPIC_DIRECTORY'),
    'EPIC_FILENAME_RE': ('omega_engine_product_planning_office.domain.manifest_models', 'EPIC_FILENAME_RE'),
    'EXPECTED_EPIC_COUNT': ('omega_engine_product_planning_office.domain.manifest_models', 'EXPECTED_EPIC_COUNT'),
    'EXPECTED_SOURCE_SNAPSHOT_COUNT': ('omega_engine_product_planning_office.domain.manifest_models', 'EXPECTED_SOURCE_SNAPSHOT_COUNT'),
    'HASH_ALGORITHM': ('omega_engine_product_planning_office.domain.manifest_models', 'HASH_ALGORITHM'),
    'MANIFEST_PATH': ('omega_engine_product_planning_office.domain.manifest_models', 'MANIFEST_PATH'),
    'OIKONOMIA_STATUSES': ('omega_engine_product_planning_office.domain.manifest_models', 'OIKONOMIA_STATUSES'),
    'SCHEMA_VERSION': ('omega_engine_product_planning_office.domain.manifest_models', 'SCHEMA_VERSION'),
    'SHA256_RE': ('omega_engine_product_planning_office.domain.manifest_models', 'SHA256_RE'),
    'SOURCE_ENTRY_KEYS': ('omega_engine_product_planning_office.domain.manifest_models', 'SOURCE_ENTRY_KEYS'),
    'SOURCE_SNAPSHOT_PATH': ('omega_engine_product_planning_office.domain.manifest_models', 'SOURCE_SNAPSHOT_PATH'),
    'TOP_LEVEL_KEYS': ('omega_engine_product_planning_office.domain.manifest_models', 'TOP_LEVEL_KEYS'),
    'EpicManifestAuditReport': ('omega_engine_product_planning_office.domain.manifest_models', 'EpicManifestAuditReport'),
    'EpicManifestError': ('omega_engine_product_planning_office.domain.manifest_models', 'EpicManifestError'),
    'fail': ('omega_engine_product_planning_office.domain.manifest_models', 'fail'),
    'require_exact_keys': ('omega_engine_product_planning_office.domain.manifest_models', 'require_exact_keys'),
    'require_exact_type': ('omega_engine_product_planning_office.domain.manifest_models', 'require_exact_type'),
    'validate_entry': ('omega_engine_product_planning_office.domain.manifest_models', 'validate_entry'),
    'validate_entry_list': ('omega_engine_product_planning_office.domain.manifest_models', 'validate_entry_list'),
    'validate_nonnegative_int': ('omega_engine_product_planning_office.domain.manifest_models', 'validate_nonnegative_int'),
    'validate_repo_path': ('omega_engine_product_planning_office.domain.manifest_models', 'validate_repo_path'),
    'validate_sha256': ('omega_engine_product_planning_office.domain.manifest_models', 'validate_sha256'),
    'compute_content_set_sha256': ('omega_engine_product_planning_office.domain.manifest_hasher', 'compute_content_set_sha256'),
    'line_profile': ('omega_engine_product_planning_office.domain.manifest_hasher', 'line_profile'),
    'extract_markdown_field': ('omega_engine_product_planning_office.domain.policy', 'extract_markdown_field'),
    'verify_epic_policy': ('omega_engine_product_planning_office.domain.policy', 'verify_epic_policy'),
    'EpicManifestAuditProtocol': ('omega_engine_product_planning_office.domain.protocols', 'EpicManifestAuditProtocol'),
    'EpicManifestStorageProtocol': ('omega_engine_product_planning_office.domain.protocols', 'EpicManifestStorageProtocol'),
    'StaleClaim': ('omega_engine_product_planning_office.domain.epic_claim_gate', 'StaleClaim'),
    'UnresolvedSubject': ('omega_engine_product_planning_office.domain.epic_claim_gate', 'UnresolvedSubject'),
    'audit_claims': ('omega_engine_product_planning_office.domain.epic_claim_gate', 'audit'),
    'audit_claim_documents': ('omega_engine_product_planning_office.domain.epic_claim_gate', 'audit_documents'),
    'audit_unreachability': ('omega_engine_product_planning_office.domain.epic_claim_gate', 'audit_unreachability'),
    'EpicCriteriaError': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'EpicCriteriaError'),
    'EpicCriteriaFinding': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'EpicCriteriaFinding'),
    'TargetFinding': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'TargetFinding'),
    'audit_epics': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'audit_epics'),
    'audit_targets': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'audit_targets'),
    'audit_epic_file': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'audit_epic_file'),
    'audit_epic_text': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'audit_epic_text'),
    'format_report': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'format_report'),
    'format_target_report': ('omega_engine_product_planning_office.domain.epic_criteria_audit', 'format_target_report'),
    'audit_epic_manifest': ('omega_engine_product_planning_office.use_cases.epic_manifest_audit', 'audit_epic_manifest'),
    'rebuild_manifest': ('omega_engine_product_planning_office.use_cases.epic_manifest_audit', 'rebuild_manifest'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
