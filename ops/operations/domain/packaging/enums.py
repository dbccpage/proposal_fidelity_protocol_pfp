#!/usr/bin/env python3
"""Domain enumerations for the packaging and agent-system inventory Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class AssetDisposition(str, Enum):
    """Disposition lifecycle stage of an agent system asset."""

    RETAIN = "Retain"
    MERGE = "Merge"
    SUPERSEDE = "Supersede"
    QUARANTINE = "Quarantine"
    ARCHIVE = "Archive"
    EXTERNAL_LOCAL = "ExternalLocal"


class RuleDisposition(str, Enum):
    """Classification disposition of a governance rule."""

    RETAINED = "Retained"
    NARROWED = "Narrowed"
    PROVIDER_SPECIFIC = "ProviderSpecific"
    SUPERSEDED = "Superseded"
    REFUSED = "Refused"
    HISTORICAL = "Historical"


class ContentHashMode(str, Enum):
    """Hashing normalizer mode for source verification."""

    EXACT_RAW_BYTES = "ExactRawBytes"
    CANONICAL_LF = "CanonicalLF"


class RuleSurface(str, Enum):
    """Surface context where a governance rule or instruction originates."""

    AGENT = "agent"
    SKILL = "skill"
    RULE = "rule"
    HOOK = "hook"
    WORKFLOW = "workflow"
    GITHUB_INSTRUCTION = "github_instruction"
