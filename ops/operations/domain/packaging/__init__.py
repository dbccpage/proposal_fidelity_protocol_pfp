"""Domain package for packaging and agent-system A00 inventory.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from operations.domain.packaging.constants import A00_TOOLING_EXCLUDED_PATHS, ASSET_DISPOSITION_OVERRIDES, ASSET_DISPOSITIONS, AUTHORITY_REVIEW_CANDIDATE_RE, BASE_IGNORED_PATHS, BASE_TRACKED_PATHS, CANONICAL_LF_HASH_MODE, CLAUDE_A00_OVERRIDE, CLAUDE_NARROWED_RULE_RANGES, CLAUDE_PRESERVED_ORIGINAL_TARGET, CONTAINMENT_ROOT_METADATA, CONTAINMENT_TARGET_OVERRIDES, CONTENT_HASH_MODES, EXACT_RAW_HASH_MODE, EXCLUDED_PROVIDER_RUNTIME_ROOTS, FENCE_RE, FILESYSTEM_PROVIDER_EXACT_PATHS, FILESYSTEM_PROVIDER_ROOTS, GENERIC_CONSUMER_TOKENS, HEADING_RE, LIST_RE, LIVE_SURFACE_ALLOWED_DIRECTORIES, LIVE_SURFACE_ALLOWED_FILES, LIVE_SURFACE_ROOTS, LOCK_SELF_VERIFICATION_NOTE, MALFORMED_CLAUDE_AGENTS, MARKDOWN_SUFFIXES, OUTPUT_NAMES, POLICY, QUARANTINE_AGENTS, QUARANTINE_SKILLS, QUOTE_RE, REVIEWED_RULE_SHA256, REVIEWED_RULE_SHA256_OVERRIDES, RULE_DISPOSITIONS, RULE_SURFACES, SCHEMA_VERSION, SENSITIVE_KEY_RE, TABLE_DELIMITER_RE, TEXT_SUFFIXES, THEMATIC_RE, UNAVAILABLE_SKILL_ROUTES
    from operations.domain.packaging.enums import AssetDisposition, ContentHashMode, RuleDisposition, RuleSurface
    from operations.domain.packaging.errors import InventoryValidationError, PackagingDomainError, QuarantineViolationError
    from operations.domain.packaging.protocols import InventoryRendererProtocol, InventoryScannerProtocol, InventoryValidatorProtocol
    from operations.domain.packaging.value_objects import AssetEntry, SourceAssetLockEntry, ValidationFinding

__all__ = ['A00_TOOLING_EXCLUDED_PATHS', 'ASSET_DISPOSITION_OVERRIDES', 'ASSET_DISPOSITIONS', 'AUTHORITY_REVIEW_CANDIDATE_RE', 'AssetDisposition', 'AssetEntry', 'BASE_IGNORED_PATHS', 'BASE_TRACKED_PATHS', 'CANONICAL_LF_HASH_MODE', 'CLAUDE_A00_OVERRIDE', 'CLAUDE_NARROWED_RULE_RANGES', 'CLAUDE_PRESERVED_ORIGINAL_TARGET', 'CONTAINMENT_ROOT_METADATA', 'CONTAINMENT_TARGET_OVERRIDES', 'CONTENT_HASH_MODES', 'ContentHashMode', 'EXACT_RAW_HASH_MODE', 'EXCLUDED_PROVIDER_RUNTIME_ROOTS', 'FENCE_RE', 'FILESYSTEM_PROVIDER_EXACT_PATHS', 'FILESYSTEM_PROVIDER_ROOTS', 'GENERIC_CONSUMER_TOKENS', 'HEADING_RE', 'InventoryRendererProtocol', 'InventoryScannerProtocol', 'InventoryValidationError', 'InventoryValidatorProtocol', 'LIST_RE', 'LIVE_SURFACE_ALLOWED_DIRECTORIES', 'LIVE_SURFACE_ALLOWED_FILES', 'LIVE_SURFACE_ROOTS', 'LOCK_SELF_VERIFICATION_NOTE', 'MALFORMED_CLAUDE_AGENTS', 'MARKDOWN_SUFFIXES', 'OUTPUT_NAMES', 'POLICY', 'PackagingDomainError', 'QUARANTINE_AGENTS', 'QUARANTINE_SKILLS', 'QUOTE_RE', 'QuarantineViolationError', 'REVIEWED_RULE_SHA256', 'REVIEWED_RULE_SHA256_OVERRIDES', 'RULE_DISPOSITIONS', 'RULE_SURFACES', 'RuleDisposition', 'RuleSurface', 'SCHEMA_VERSION', 'SENSITIVE_KEY_RE', 'SourceAssetLockEntry', 'TABLE_DELIMITER_RE', 'TEXT_SUFFIXES', 'THEMATIC_RE', 'UNAVAILABLE_SKILL_ROUTES', 'ValidationFinding']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'A00_TOOLING_EXCLUDED_PATHS': ('operations.domain.packaging.constants', 'A00_TOOLING_EXCLUDED_PATHS'),
    'ASSET_DISPOSITION_OVERRIDES': ('operations.domain.packaging.constants', 'ASSET_DISPOSITION_OVERRIDES'),
    'ASSET_DISPOSITIONS': ('operations.domain.packaging.constants', 'ASSET_DISPOSITIONS'),
    'AUTHORITY_REVIEW_CANDIDATE_RE': ('operations.domain.packaging.constants', 'AUTHORITY_REVIEW_CANDIDATE_RE'),
    'BASE_IGNORED_PATHS': ('operations.domain.packaging.constants', 'BASE_IGNORED_PATHS'),
    'BASE_TRACKED_PATHS': ('operations.domain.packaging.constants', 'BASE_TRACKED_PATHS'),
    'CANONICAL_LF_HASH_MODE': ('operations.domain.packaging.constants', 'CANONICAL_LF_HASH_MODE'),
    'CLAUDE_A00_OVERRIDE': ('operations.domain.packaging.constants', 'CLAUDE_A00_OVERRIDE'),
    'CLAUDE_NARROWED_RULE_RANGES': ('operations.domain.packaging.constants', 'CLAUDE_NARROWED_RULE_RANGES'),
    'CLAUDE_PRESERVED_ORIGINAL_TARGET': ('operations.domain.packaging.constants', 'CLAUDE_PRESERVED_ORIGINAL_TARGET'),
    'CONTAINMENT_ROOT_METADATA': ('operations.domain.packaging.constants', 'CONTAINMENT_ROOT_METADATA'),
    'CONTAINMENT_TARGET_OVERRIDES': ('operations.domain.packaging.constants', 'CONTAINMENT_TARGET_OVERRIDES'),
    'CONTENT_HASH_MODES': ('operations.domain.packaging.constants', 'CONTENT_HASH_MODES'),
    'EXACT_RAW_HASH_MODE': ('operations.domain.packaging.constants', 'EXACT_RAW_HASH_MODE'),
    'EXCLUDED_PROVIDER_RUNTIME_ROOTS': ('operations.domain.packaging.constants', 'EXCLUDED_PROVIDER_RUNTIME_ROOTS'),
    'FENCE_RE': ('operations.domain.packaging.constants', 'FENCE_RE'),
    'FILESYSTEM_PROVIDER_EXACT_PATHS': ('operations.domain.packaging.constants', 'FILESYSTEM_PROVIDER_EXACT_PATHS'),
    'FILESYSTEM_PROVIDER_ROOTS': ('operations.domain.packaging.constants', 'FILESYSTEM_PROVIDER_ROOTS'),
    'GENERIC_CONSUMER_TOKENS': ('operations.domain.packaging.constants', 'GENERIC_CONSUMER_TOKENS'),
    'HEADING_RE': ('operations.domain.packaging.constants', 'HEADING_RE'),
    'LIST_RE': ('operations.domain.packaging.constants', 'LIST_RE'),
    'LIVE_SURFACE_ALLOWED_DIRECTORIES': ('operations.domain.packaging.constants', 'LIVE_SURFACE_ALLOWED_DIRECTORIES'),
    'LIVE_SURFACE_ALLOWED_FILES': ('operations.domain.packaging.constants', 'LIVE_SURFACE_ALLOWED_FILES'),
    'LIVE_SURFACE_ROOTS': ('operations.domain.packaging.constants', 'LIVE_SURFACE_ROOTS'),
    'LOCK_SELF_VERIFICATION_NOTE': ('operations.domain.packaging.constants', 'LOCK_SELF_VERIFICATION_NOTE'),
    'MALFORMED_CLAUDE_AGENTS': ('operations.domain.packaging.constants', 'MALFORMED_CLAUDE_AGENTS'),
    'MARKDOWN_SUFFIXES': ('operations.domain.packaging.constants', 'MARKDOWN_SUFFIXES'),
    'OUTPUT_NAMES': ('operations.domain.packaging.constants', 'OUTPUT_NAMES'),
    'POLICY': ('operations.domain.packaging.constants', 'POLICY'),
    'QUARANTINE_AGENTS': ('operations.domain.packaging.constants', 'QUARANTINE_AGENTS'),
    'QUARANTINE_SKILLS': ('operations.domain.packaging.constants', 'QUARANTINE_SKILLS'),
    'QUOTE_RE': ('operations.domain.packaging.constants', 'QUOTE_RE'),
    'REVIEWED_RULE_SHA256': ('operations.domain.packaging.constants', 'REVIEWED_RULE_SHA256'),
    'REVIEWED_RULE_SHA256_OVERRIDES': ('operations.domain.packaging.constants', 'REVIEWED_RULE_SHA256_OVERRIDES'),
    'RULE_DISPOSITIONS': ('operations.domain.packaging.constants', 'RULE_DISPOSITIONS'),
    'RULE_SURFACES': ('operations.domain.packaging.constants', 'RULE_SURFACES'),
    'SCHEMA_VERSION': ('operations.domain.packaging.constants', 'SCHEMA_VERSION'),
    'SENSITIVE_KEY_RE': ('operations.domain.packaging.constants', 'SENSITIVE_KEY_RE'),
    'TABLE_DELIMITER_RE': ('operations.domain.packaging.constants', 'TABLE_DELIMITER_RE'),
    'TEXT_SUFFIXES': ('operations.domain.packaging.constants', 'TEXT_SUFFIXES'),
    'THEMATIC_RE': ('operations.domain.packaging.constants', 'THEMATIC_RE'),
    'UNAVAILABLE_SKILL_ROUTES': ('operations.domain.packaging.constants', 'UNAVAILABLE_SKILL_ROUTES'),
    'AssetDisposition': ('operations.domain.packaging.enums', 'AssetDisposition'),
    'ContentHashMode': ('operations.domain.packaging.enums', 'ContentHashMode'),
    'RuleDisposition': ('operations.domain.packaging.enums', 'RuleDisposition'),
    'RuleSurface': ('operations.domain.packaging.enums', 'RuleSurface'),
    'InventoryValidationError': ('operations.domain.packaging.errors', 'InventoryValidationError'),
    'PackagingDomainError': ('operations.domain.packaging.errors', 'PackagingDomainError'),
    'QuarantineViolationError': ('operations.domain.packaging.errors', 'QuarantineViolationError'),
    'InventoryRendererProtocol': ('operations.domain.packaging.protocols', 'InventoryRendererProtocol'),
    'InventoryScannerProtocol': ('operations.domain.packaging.protocols', 'InventoryScannerProtocol'),
    'InventoryValidatorProtocol': ('operations.domain.packaging.protocols', 'InventoryValidatorProtocol'),
    'AssetEntry': ('operations.domain.packaging.value_objects', 'AssetEntry'),
    'SourceAssetLockEntry': ('operations.domain.packaging.value_objects', 'SourceAssetLockEntry'),
    'ValidationFinding': ('operations.domain.packaging.value_objects', 'ValidationFinding'),
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
