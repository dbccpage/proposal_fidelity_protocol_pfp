"""Domain package for packaging and agent-system A00 inventory.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_operations.domain.packaging.constants import A00_TOOLING_EXCLUDED_PATHS, ASSET_DISPOSITION_OVERRIDES, ASSET_DISPOSITIONS, AUTHORITY_REVIEW_CANDIDATE_RE, BASE_IGNORED_PATHS, BASE_TRACKED_PATHS, CANONICAL_LF_HASH_MODE, CLAUDE_A00_OVERRIDE, CLAUDE_NARROWED_RULE_RANGES, CLAUDE_PRESERVED_ORIGINAL_TARGET, CONTAINMENT_ROOT_METADATA, CONTAINMENT_TARGET_OVERRIDES, CONTENT_HASH_MODES, EXACT_RAW_HASH_MODE, EXCLUDED_PROVIDER_RUNTIME_ROOTS, FENCE_RE, FILESYSTEM_PROVIDER_EXACT_PATHS, FILESYSTEM_PROVIDER_ROOTS, GENERIC_CONSUMER_TOKENS, HEADING_RE, LIST_RE, LIVE_SURFACE_ALLOWED_DIRECTORIES, LIVE_SURFACE_ALLOWED_FILES, LIVE_SURFACE_ROOTS, LOCK_SELF_VERIFICATION_NOTE, MALFORMED_CLAUDE_AGENTS, MARKDOWN_SUFFIXES, OUTPUT_NAMES, POLICY, QUARANTINE_AGENTS, QUARANTINE_SKILLS, QUOTE_RE, REVIEWED_RULE_SHA256, REVIEWED_RULE_SHA256_OVERRIDES, RULE_DISPOSITIONS, RULE_SURFACES, SCHEMA_VERSION, SENSITIVE_KEY_RE, TABLE_DELIMITER_RE, TEXT_SUFFIXES, THEMATIC_RE, UNAVAILABLE_SKILL_ROUTES
    from omega_engine_operations.domain.packaging.enums import AssetDisposition, ContentHashMode, RuleDisposition, RuleSurface
    from omega_engine_operations.domain.packaging.errors import InventoryValidationError, PackagingDomainError, QuarantineViolationError
    from omega_engine_operations.domain.packaging.protocols import InventoryRendererProtocol, InventoryScannerProtocol, InventoryValidatorProtocol
    from omega_engine_operations.domain.packaging.value_objects import AssetEntry, SourceAssetLockEntry, ValidationFinding

__all__ = ['A00_TOOLING_EXCLUDED_PATHS', 'ASSET_DISPOSITION_OVERRIDES', 'ASSET_DISPOSITIONS', 'AUTHORITY_REVIEW_CANDIDATE_RE', 'AssetDisposition', 'AssetEntry', 'BASE_IGNORED_PATHS', 'BASE_TRACKED_PATHS', 'CANONICAL_LF_HASH_MODE', 'CLAUDE_A00_OVERRIDE', 'CLAUDE_NARROWED_RULE_RANGES', 'CLAUDE_PRESERVED_ORIGINAL_TARGET', 'CONTAINMENT_ROOT_METADATA', 'CONTAINMENT_TARGET_OVERRIDES', 'CONTENT_HASH_MODES', 'ContentHashMode', 'EXACT_RAW_HASH_MODE', 'EXCLUDED_PROVIDER_RUNTIME_ROOTS', 'FENCE_RE', 'FILESYSTEM_PROVIDER_EXACT_PATHS', 'FILESYSTEM_PROVIDER_ROOTS', 'GENERIC_CONSUMER_TOKENS', 'HEADING_RE', 'InventoryRendererProtocol', 'InventoryScannerProtocol', 'InventoryValidationError', 'InventoryValidatorProtocol', 'LIST_RE', 'LIVE_SURFACE_ALLOWED_DIRECTORIES', 'LIVE_SURFACE_ALLOWED_FILES', 'LIVE_SURFACE_ROOTS', 'LOCK_SELF_VERIFICATION_NOTE', 'MALFORMED_CLAUDE_AGENTS', 'MARKDOWN_SUFFIXES', 'OUTPUT_NAMES', 'POLICY', 'PackagingDomainError', 'QUARANTINE_AGENTS', 'QUARANTINE_SKILLS', 'QUOTE_RE', 'QuarantineViolationError', 'REVIEWED_RULE_SHA256', 'REVIEWED_RULE_SHA256_OVERRIDES', 'RULE_DISPOSITIONS', 'RULE_SURFACES', 'RuleDisposition', 'RuleSurface', 'SCHEMA_VERSION', 'SENSITIVE_KEY_RE', 'SourceAssetLockEntry', 'TABLE_DELIMITER_RE', 'TEXT_SUFFIXES', 'THEMATIC_RE', 'UNAVAILABLE_SKILL_ROUTES', 'ValidationFinding']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'A00_TOOLING_EXCLUDED_PATHS': ('omega_engine_operations.domain.packaging.constants', 'A00_TOOLING_EXCLUDED_PATHS'),
    'ASSET_DISPOSITION_OVERRIDES': ('omega_engine_operations.domain.packaging.constants', 'ASSET_DISPOSITION_OVERRIDES'),
    'ASSET_DISPOSITIONS': ('omega_engine_operations.domain.packaging.constants', 'ASSET_DISPOSITIONS'),
    'AUTHORITY_REVIEW_CANDIDATE_RE': ('omega_engine_operations.domain.packaging.constants', 'AUTHORITY_REVIEW_CANDIDATE_RE'),
    'BASE_IGNORED_PATHS': ('omega_engine_operations.domain.packaging.constants', 'BASE_IGNORED_PATHS'),
    'BASE_TRACKED_PATHS': ('omega_engine_operations.domain.packaging.constants', 'BASE_TRACKED_PATHS'),
    'CANONICAL_LF_HASH_MODE': ('omega_engine_operations.domain.packaging.constants', 'CANONICAL_LF_HASH_MODE'),
    'CLAUDE_A00_OVERRIDE': ('omega_engine_operations.domain.packaging.constants', 'CLAUDE_A00_OVERRIDE'),
    'CLAUDE_NARROWED_RULE_RANGES': ('omega_engine_operations.domain.packaging.constants', 'CLAUDE_NARROWED_RULE_RANGES'),
    'CLAUDE_PRESERVED_ORIGINAL_TARGET': ('omega_engine_operations.domain.packaging.constants', 'CLAUDE_PRESERVED_ORIGINAL_TARGET'),
    'CONTAINMENT_ROOT_METADATA': ('omega_engine_operations.domain.packaging.constants', 'CONTAINMENT_ROOT_METADATA'),
    'CONTAINMENT_TARGET_OVERRIDES': ('omega_engine_operations.domain.packaging.constants', 'CONTAINMENT_TARGET_OVERRIDES'),
    'CONTENT_HASH_MODES': ('omega_engine_operations.domain.packaging.constants', 'CONTENT_HASH_MODES'),
    'EXACT_RAW_HASH_MODE': ('omega_engine_operations.domain.packaging.constants', 'EXACT_RAW_HASH_MODE'),
    'EXCLUDED_PROVIDER_RUNTIME_ROOTS': ('omega_engine_operations.domain.packaging.constants', 'EXCLUDED_PROVIDER_RUNTIME_ROOTS'),
    'FENCE_RE': ('omega_engine_operations.domain.packaging.constants', 'FENCE_RE'),
    'FILESYSTEM_PROVIDER_EXACT_PATHS': ('omega_engine_operations.domain.packaging.constants', 'FILESYSTEM_PROVIDER_EXACT_PATHS'),
    'FILESYSTEM_PROVIDER_ROOTS': ('omega_engine_operations.domain.packaging.constants', 'FILESYSTEM_PROVIDER_ROOTS'),
    'GENERIC_CONSUMER_TOKENS': ('omega_engine_operations.domain.packaging.constants', 'GENERIC_CONSUMER_TOKENS'),
    'HEADING_RE': ('omega_engine_operations.domain.packaging.constants', 'HEADING_RE'),
    'LIST_RE': ('omega_engine_operations.domain.packaging.constants', 'LIST_RE'),
    'LIVE_SURFACE_ALLOWED_DIRECTORIES': ('omega_engine_operations.domain.packaging.constants', 'LIVE_SURFACE_ALLOWED_DIRECTORIES'),
    'LIVE_SURFACE_ALLOWED_FILES': ('omega_engine_operations.domain.packaging.constants', 'LIVE_SURFACE_ALLOWED_FILES'),
    'LIVE_SURFACE_ROOTS': ('omega_engine_operations.domain.packaging.constants', 'LIVE_SURFACE_ROOTS'),
    'LOCK_SELF_VERIFICATION_NOTE': ('omega_engine_operations.domain.packaging.constants', 'LOCK_SELF_VERIFICATION_NOTE'),
    'MALFORMED_CLAUDE_AGENTS': ('omega_engine_operations.domain.packaging.constants', 'MALFORMED_CLAUDE_AGENTS'),
    'MARKDOWN_SUFFIXES': ('omega_engine_operations.domain.packaging.constants', 'MARKDOWN_SUFFIXES'),
    'OUTPUT_NAMES': ('omega_engine_operations.domain.packaging.constants', 'OUTPUT_NAMES'),
    'POLICY': ('omega_engine_operations.domain.packaging.constants', 'POLICY'),
    'QUARANTINE_AGENTS': ('omega_engine_operations.domain.packaging.constants', 'QUARANTINE_AGENTS'),
    'QUARANTINE_SKILLS': ('omega_engine_operations.domain.packaging.constants', 'QUARANTINE_SKILLS'),
    'QUOTE_RE': ('omega_engine_operations.domain.packaging.constants', 'QUOTE_RE'),
    'REVIEWED_RULE_SHA256': ('omega_engine_operations.domain.packaging.constants', 'REVIEWED_RULE_SHA256'),
    'REVIEWED_RULE_SHA256_OVERRIDES': ('omega_engine_operations.domain.packaging.constants', 'REVIEWED_RULE_SHA256_OVERRIDES'),
    'RULE_DISPOSITIONS': ('omega_engine_operations.domain.packaging.constants', 'RULE_DISPOSITIONS'),
    'RULE_SURFACES': ('omega_engine_operations.domain.packaging.constants', 'RULE_SURFACES'),
    'SCHEMA_VERSION': ('omega_engine_operations.domain.packaging.constants', 'SCHEMA_VERSION'),
    'SENSITIVE_KEY_RE': ('omega_engine_operations.domain.packaging.constants', 'SENSITIVE_KEY_RE'),
    'TABLE_DELIMITER_RE': ('omega_engine_operations.domain.packaging.constants', 'TABLE_DELIMITER_RE'),
    'TEXT_SUFFIXES': ('omega_engine_operations.domain.packaging.constants', 'TEXT_SUFFIXES'),
    'THEMATIC_RE': ('omega_engine_operations.domain.packaging.constants', 'THEMATIC_RE'),
    'UNAVAILABLE_SKILL_ROUTES': ('omega_engine_operations.domain.packaging.constants', 'UNAVAILABLE_SKILL_ROUTES'),
    'AssetDisposition': ('omega_engine_operations.domain.packaging.enums', 'AssetDisposition'),
    'ContentHashMode': ('omega_engine_operations.domain.packaging.enums', 'ContentHashMode'),
    'RuleDisposition': ('omega_engine_operations.domain.packaging.enums', 'RuleDisposition'),
    'RuleSurface': ('omega_engine_operations.domain.packaging.enums', 'RuleSurface'),
    'InventoryValidationError': ('omega_engine_operations.domain.packaging.errors', 'InventoryValidationError'),
    'PackagingDomainError': ('omega_engine_operations.domain.packaging.errors', 'PackagingDomainError'),
    'QuarantineViolationError': ('omega_engine_operations.domain.packaging.errors', 'QuarantineViolationError'),
    'InventoryRendererProtocol': ('omega_engine_operations.domain.packaging.protocols', 'InventoryRendererProtocol'),
    'InventoryScannerProtocol': ('omega_engine_operations.domain.packaging.protocols', 'InventoryScannerProtocol'),
    'InventoryValidatorProtocol': ('omega_engine_operations.domain.packaging.protocols', 'InventoryValidatorProtocol'),
    'AssetEntry': ('omega_engine_operations.domain.packaging.value_objects', 'AssetEntry'),
    'SourceAssetLockEntry': ('omega_engine_operations.domain.packaging.value_objects', 'SourceAssetLockEntry'),
    'ValidationFinding': ('omega_engine_operations.domain.packaging.value_objects', 'ValidationFinding'),
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
