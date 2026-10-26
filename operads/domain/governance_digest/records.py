"""Frozen records for governance digest and apply.

AuthorityEffect: None. These types carry bytes the application already read.
They do not open files.
"""

from __future__ import annotations

from dataclasses import dataclass

# Pattern files must carry every one of these frontmatter keys.
REQUIRED_FRONTMATTER: tuple[str, ...] = (
    "pattern_id",
    "name",
    "category",
    "operad_type",
    "operad_source_colours",
    "operad_target_colour",
    "operad_arity",
    "operad_residual",
    "dual_pattern",
    "language",
    "authority_effect",
)


@dataclass(frozen=True)
class EditLocator:
    """How a proposal finds its edit site.

    ``replace`` uses ``old_text`` and requires one occurrence.
    ``insert_before`` and ``insert_after`` use ``anchor_text`` and require one occurrence.
    ``new_heading`` is set for a new invariant and must be absent in the pre-edit text.
    """

    mode: str
    old_text: str = ""
    anchor_text: str = ""
    new_heading: str = ""


@dataclass(frozen=True)
class RepairSpec:
    """One permitted repair. The applier trusts this table, not the receipt."""

    repair_id: str
    edit_kind: str
    target_path: str
    target_section: str
    pattern_ids: tuple[str, ...]
    locator: EditLocator
    replacement_text: str
    pre_fingerprint: str
    post_fingerprint: str
    pattern_sha256: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    repair_id: str
    target_path: str
    target_section: str
    edit_kind: str
    expected_target_hash: str
    replacement_text: str
    evidence_ids: tuple[str, ...]
    locator: EditLocator
    pattern_ids: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    finding_id: str
    disposition: str
    corpus: str
    source_paths: tuple[str, ...]
    target_path: str
    target_section: str
    reason: str
    evidence: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class TextDoc:
    corpus: str
    relative_path: str
    sha256: str
    text: str


@dataclass(frozen=True)
class IndexedFile:
    corpus: str
    relative_path: str
    sha256: str


@dataclass(frozen=True)
class PatternDoc:
    relative_path: str
    sha256: str
    pattern_id: str
    name: str
    category: str
    language: str
    dual_pattern: str
    frontmatter_keys: tuple[str, ...]
    detection_text: str
    applicability: tuple[str, ...] = ()


@dataclass(frozen=True)
class GovernanceCorpus:
    """One snapshot. ``anti_pattern`` arrives only as ``patterns``."""

    documentation: tuple[TextDoc, ...] = ()
    patterns: tuple[PatternDoc, ...] = ()
    teamwork_index: tuple[IndexedFile, ...] = ()
    handoffs: tuple[TextDoc, ...] = ()
    harvest_receipts: tuple[TextDoc, ...] = ()
    harvest_index: tuple[IndexedFile, ...] = ()
    omc_records: tuple[TextDoc, ...] = ()
    paper_reviews: tuple[TextDoc, ...] = ()
    unstructured_counts: tuple[tuple[str, int], ...] = ()
    absent_corpora: tuple[str, ...] = ()
    stale_pointers: tuple[TextDoc, ...] = ()
    rules: tuple[TextDoc, ...] = ()
    skills: tuple[TextDoc, ...] = ()


@dataclass(frozen=True)
class ApplyOutcome:
    proposal_id: str
    status: str
    reason: str
    before_hash: str
    after_hash: str
    mirrors: tuple[tuple[str, str], ...] = ()
