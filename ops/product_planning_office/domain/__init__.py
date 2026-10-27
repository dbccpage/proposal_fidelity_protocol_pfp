"""Domain package for product planning and epic manifest verification.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from product_planning_office.domain.manifest_models import CONTENT_ENTRY_KEYS, EPIC_DIRECTORY, EPIC_FILENAME_RE, EXPECTED_EPIC_COUNT, EXPECTED_SOURCE_SNAPSHOT_COUNT, HASH_ALGORITHM, MANIFEST_PATH, OIKONOMIA_STATUSES, SCHEMA_VERSION, SHA256_RE, SOURCE_ENTRY_KEYS, SOURCE_SNAPSHOT_PATH, TOP_LEVEL_KEYS, EpicManifestAuditReport, EpicManifestError, fail, require_exact_keys, require_exact_type, validate_entry, validate_entry_list, validate_nonnegative_int, validate_repo_path, validate_sha256
    from product_planning_office.domain.manifest_hasher import compute_content_set_sha256, line_profile
    from product_planning_office.domain.policy import extract_markdown_field, verify_epic_policy
    from product_planning_office.domain.protocols import EpicManifestAuditProtocol, EpicManifestStorageProtocol
    from product_planning_office.domain.epic_claim_gate import StaleClaim, UnresolvedSubject, audit as audit_claims, audit_documents as audit_claim_documents, audit_unreachability
    from product_planning_office.domain.epic_criteria_audit import EpicCriteriaError, EpicCriteriaFinding, TargetFinding, audit_epics, audit_targets, audit_epic_file, audit_epic_text, format_report, format_target_report

__all__ = ['CONTENT_ENTRY_KEYS', 'EPIC_DIRECTORY', 'EPIC_FILENAME_RE', 'EXPECTED_EPIC_COUNT', 'EXPECTED_SOURCE_SNAPSHOT_COUNT', 'EpicManifestAuditProtocol', 'EpicManifestAuditReport', 'EpicManifestError', 'EpicManifestStorageProtocol', 'HASH_ALGORITHM', 'MANIFEST_PATH', 'OIKONOMIA_STATUSES', 'SCHEMA_VERSION', 'SHA256_RE', 'SOURCE_ENTRY_KEYS', 'SOURCE_SNAPSHOT_PATH', 'TOP_LEVEL_KEYS', 'compute_content_set_sha256', 'extract_markdown_field', 'fail', 'line_profile', 'require_exact_keys', 'require_exact_type', 'validate_entry', 'validate_entry_list', 'validate_nonnegative_int', 'validate_repo_path', 'validate_sha256', 'verify_epic_policy', 'StaleClaim', 'UnresolvedSubject', 'audit_claims', 'audit_claim_documents', 'audit_unreachability', 'EpicCriteriaError', 'EpicCriteriaFinding', 'TargetFinding', 'audit_epics', 'audit_targets', 'audit_epic_file', 'audit_epic_text', 'format_report', 'format_target_report']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CONTENT_ENTRY_KEYS': ('product_planning_office.domain.manifest_models', 'CONTENT_ENTRY_KEYS'),
    'EPIC_DIRECTORY': ('product_planning_office.domain.manifest_models', 'EPIC_DIRECTORY'),
    'EPIC_FILENAME_RE': ('product_planning_office.domain.manifest_models', 'EPIC_FILENAME_RE'),
    'EXPECTED_EPIC_COUNT': ('product_planning_office.domain.manifest_models', 'EXPECTED_EPIC_COUNT'),
    'EXPECTED_SOURCE_SNAPSHOT_COUNT': ('product_planning_office.domain.manifest_models', 'EXPECTED_SOURCE_SNAPSHOT_COUNT'),
    'HASH_ALGORITHM': ('product_planning_office.domain.manifest_models', 'HASH_ALGORITHM'),
    'MANIFEST_PATH': ('product_planning_office.domain.manifest_models', 'MANIFEST_PATH'),
    'OIKONOMIA_STATUSES': ('product_planning_office.domain.manifest_models', 'OIKONOMIA_STATUSES'),
    'SCHEMA_VERSION': ('product_planning_office.domain.manifest_models', 'SCHEMA_VERSION'),
    'SHA256_RE': ('product_planning_office.domain.manifest_models', 'SHA256_RE'),
    'SOURCE_ENTRY_KEYS': ('product_planning_office.domain.manifest_models', 'SOURCE_ENTRY_KEYS'),
    'SOURCE_SNAPSHOT_PATH': ('product_planning_office.domain.manifest_models', 'SOURCE_SNAPSHOT_PATH'),
    'TOP_LEVEL_KEYS': ('product_planning_office.domain.manifest_models', 'TOP_LEVEL_KEYS'),
    'EpicManifestAuditReport': ('product_planning_office.domain.manifest_models', 'EpicManifestAuditReport'),
    'EpicManifestError': ('product_planning_office.domain.manifest_models', 'EpicManifestError'),
    'fail': ('product_planning_office.domain.manifest_models', 'fail'),
    'require_exact_keys': ('product_planning_office.domain.manifest_models', 'require_exact_keys'),
    'require_exact_type': ('product_planning_office.domain.manifest_models', 'require_exact_type'),
    'validate_entry': ('product_planning_office.domain.manifest_models', 'validate_entry'),
    'validate_entry_list': ('product_planning_office.domain.manifest_models', 'validate_entry_list'),
    'validate_nonnegative_int': ('product_planning_office.domain.manifest_models', 'validate_nonnegative_int'),
    'validate_repo_path': ('product_planning_office.domain.manifest_models', 'validate_repo_path'),
    'validate_sha256': ('product_planning_office.domain.manifest_models', 'validate_sha256'),
    'compute_content_set_sha256': ('product_planning_office.domain.manifest_hasher', 'compute_content_set_sha256'),
    'line_profile': ('product_planning_office.domain.manifest_hasher', 'line_profile'),
    'extract_markdown_field': ('product_planning_office.domain.policy', 'extract_markdown_field'),
    'verify_epic_policy': ('product_planning_office.domain.policy', 'verify_epic_policy'),
    'EpicManifestAuditProtocol': ('product_planning_office.domain.protocols', 'EpicManifestAuditProtocol'),
    'EpicManifestStorageProtocol': ('product_planning_office.domain.protocols', 'EpicManifestStorageProtocol'),
    'StaleClaim': ('product_planning_office.domain.epic_claim_gate', 'StaleClaim'),
    'UnresolvedSubject': ('product_planning_office.domain.epic_claim_gate', 'UnresolvedSubject'),
    'audit_claims': ('product_planning_office.domain.epic_claim_gate', 'audit'),
    'audit_claim_documents': ('product_planning_office.domain.epic_claim_gate', 'audit_documents'),
    'audit_unreachability': ('product_planning_office.domain.epic_claim_gate', 'audit_unreachability'),
    'EpicCriteriaError': ('product_planning_office.domain.epic_criteria_audit', 'EpicCriteriaError'),
    'EpicCriteriaFinding': ('product_planning_office.domain.epic_criteria_audit', 'EpicCriteriaFinding'),
    'TargetFinding': ('product_planning_office.domain.epic_criteria_audit', 'TargetFinding'),
    'audit_epics': ('product_planning_office.domain.epic_criteria_audit', 'audit_epics'),
    'audit_targets': ('product_planning_office.domain.epic_criteria_audit', 'audit_targets'),
    'audit_epic_file': ('product_planning_office.domain.epic_criteria_audit', 'audit_epic_file'),
    'audit_epic_text': ('product_planning_office.domain.epic_criteria_audit', 'audit_epic_text'),
    'format_report': ('product_planning_office.domain.epic_criteria_audit', 'format_report'),
    'format_target_report': ('product_planning_office.domain.epic_criteria_audit', 'format_target_report'),
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
