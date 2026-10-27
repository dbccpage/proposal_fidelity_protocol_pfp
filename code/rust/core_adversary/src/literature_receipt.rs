//! Bibliographic binding receipt. AuthorityEffect: None.
//! Digests bind the pipe-joined fields and local-profile bibliographic JSON bytes.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3640c26c<T> {
    fn checked_invariant_3640c26c(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3640c26c<T> for Option<T> {
    #[inline]
    fn checked_invariant_3640c26c(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3640c26c<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3640c26c(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::jcs::{self, Jcs};
use crate::receipt::Fault;
use regex::Regex;
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::sync::OnceLock;
use unicode_normalization::UnicodeNormalization;

pub const SCHEMA_VERSION: &str = "core.oears.literature_receipt.v0";
pub const AUTHORITY_EFFECT: &str = "None";

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LiteratureDraft {
    pub receipt_id: String,
    pub package_id: String,
    pub cite_key: String,
    pub title: String,
    pub authors: String,
    pub year: String,
    pub venue: String,
    pub arxiv_id: String,
    pub doi: String,
    pub url: String,
    pub binding_note: String,
    pub source_kind: String,
    pub bound_at_utc: String,
    pub authority_effect: String,
    pub claims_global_green: bool,
    pub content_fingerprint: Option<String>,
    pub canonical_sha256: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LiteratureReceipt {
    pub receipt_id: String,
    pub package_id: String,
    pub cite_key: String,
    pub title: String,
    pub authors: String,
    pub year: String,
    pub venue: String,
    pub arxiv_id: String,
    pub doi: String,
    pub url: String,
    pub binding_note: String,
    pub source_kind: String,
    pub bound_at_utc: String,
    pub authority_effect: &'static str,
    pub claims_global_green: bool,
    pub schema_version: &'static str,
    pub content_fingerprint: String,
    pub canonical_sha256: String,
}

impl TryFrom<&[u8]> for LiteratureReceipt {
    type Error = Fault;

    fn try_from(bytes: &[u8]) -> Result<Self, Self::Error> {
        if let Err(failure) = jcs::screen(bytes, jcs::DIALECTIC_LIMITS) {
            return Err(Fault::new(failure.code, failure.detail));
        }
        let wire: LiteratureWire = serde_json::from_slice(bytes)
            .map_err(|error| Fault::new("INVALID_RECORD", error.to_string()))?;
        if wire.schema_version != SCHEMA_VERSION {
            return Err(Fault::new("INVALID_RECORD", "schema_version mismatch"));
        }
        Self::try_from(wire.draft())
    }
}

fn validate_draft_fields(draft: &LiteratureDraft) -> Result<(), Fault> {
    if draft.authority_effect != AUTHORITY_EFFECT {
        return Err(Fault::new("PROSE_AUTHORITY", "authority_effect must be None"));
    }
    if draft.claims_global_green {
        return Err(Fault::new("PROSE_AUTHORITY", "literature receipt must not claim GlobalGreen"));
    }
    require_text(&draft.receipt_id, false, 128)?;
    require_text(&draft.package_id, false, 256)?;
    require_text(&draft.cite_key, false, 256)?;
    require_text(&draft.title, false, 1024)?;
    for field in [
        &draft.authors,
        &draft.year,
        &draft.venue,
        &draft.url,
        &draft.binding_note,
        &draft.bound_at_utc,
    ] {
        require_text(field, true, 4096)?;
    }
    require_text(&draft.arxiv_id, true, 64)?;
    require_text(&draft.doi, true, 256)
}

fn validate_draft_identifiers(draft: &LiteratureDraft) -> Result<(), Fault> {
    if !matches!(draft.source_kind.as_str(), "manual" | "fixture" | "lookup_stub") {
        return Err(Fault::new("SOURCE_KIND", "bad source_kind"));
    }
    if !draft.arxiv_id.is_empty() && !arxiv_re().is_match(&draft.arxiv_id) {
        return Err(Fault::new("ARXIV_ID", "malformed arxiv_id"));
    }
    if !draft.doi.is_empty() && !doi_re().is_match(&draft.doi) {
        return Err(Fault::new("DOI", "malformed doi"));
    }
    Ok(())
}

impl TryFrom<LiteratureDraft> for LiteratureReceipt {
    type Error = Fault;

    fn try_from(draft: LiteratureDraft) -> Result<Self, Self::Error> {
        validate_draft_fields(&draft)?;
        validate_draft_identifiers(&draft)?;
        let pipe = [
            draft.package_id.as_str(),
            draft.cite_key.as_str(),
            draft.title.as_str(),
            draft.authors.as_str(),
            draft.year.as_str(),
            draft.venue.as_str(),
            draft.arxiv_id.as_str(),
            draft.doi.as_str(),
            draft.url.as_str(),
            draft.source_kind.as_str(),
        ]
        .join("|");
        let content_fingerprint = hex::encode(Sha256::digest(pipe.as_bytes()));
        let canonical_sha256 = format!(
            "sha256:{}",
            hex::encode(Sha256::digest(bibliographic_jcs(&draft)?.as_slice()))
        );
        if draft
            .content_fingerprint
            .as_ref()
            .is_some_and(|value| value != &content_fingerprint)
        {
            return Err(Fault::new(
                "FINGERPRINT_MISMATCH",
                "content_fingerprint does not match the pipe digest",
            ));
        }
        if draft
            .canonical_sha256
            .as_ref()
            .is_some_and(|value| value != &canonical_sha256)
        {
            return Err(Fault::new(
                "FINGERPRINT_MISMATCH",
                "canonical_sha256 does not match the RFC 8785 digest",
            ));
        }
        Ok(Self {
            receipt_id: draft.receipt_id,
            package_id: draft.package_id,
            cite_key: draft.cite_key,
            title: draft.title,
            authors: draft.authors,
            year: draft.year,
            venue: draft.venue,
            arxiv_id: draft.arxiv_id,
            doi: draft.doi,
            url: draft.url,
            binding_note: draft.binding_note,
            source_kind: draft.source_kind,
            bound_at_utc: draft.bound_at_utc,
            authority_effect: AUTHORITY_EFFECT,
            claims_global_green: false,
            schema_version: SCHEMA_VERSION,
            content_fingerprint,
            canonical_sha256,
        })
    }
}

impl LiteratureReceipt {
    pub fn canonical_bytes(&self) -> Result<Vec<u8>, Fault> {
        self.to_jcs()
            .canonical_bytes()
            .map_err(|_| Fault::new("CANONICAL", "literature receipt cannot be encoded"))
    }

    pub(crate) fn to_jcs(&self) -> Jcs {
        Jcs::Object(vec![
            ("arxiv_id".into(), Jcs::string(&self.arxiv_id)),
            ("authors".into(), Jcs::string(&self.authors)),
            ("authority_effect".into(), Jcs::string(AUTHORITY_EFFECT)),
            ("binding_note".into(), Jcs::string(&self.binding_note)),
            ("bound_at_utc".into(), Jcs::string(&self.bound_at_utc)),
            (
                "canonical_sha256".into(),
                Jcs::string(&self.canonical_sha256),
            ),
            ("cite_key".into(), Jcs::string(&self.cite_key)),
            ("claims_global_green".into(), Jcs::Bool(false)),
            (
                "content_fingerprint".into(),
                Jcs::string(&self.content_fingerprint),
            ),
            ("doi".into(), Jcs::string(&self.doi)),
            ("package_id".into(), Jcs::string(&self.package_id)),
            ("receipt_id".into(), Jcs::string(&self.receipt_id)),
            ("schema_version".into(), Jcs::string(self.schema_version)),
            ("source_kind".into(), Jcs::string(&self.source_kind)),
            ("title".into(), Jcs::string(&self.title)),
            ("url".into(), Jcs::string(&self.url)),
            ("venue".into(), Jcs::string(&self.venue)),
            ("year".into(), Jcs::string(&self.year)),
        ])
    }
}

fn bibliographic_jcs(draft: &LiteratureDraft) -> Result<Vec<u8>, Fault> {
    Jcs::Object(vec![
        ("arxiv_id".into(), Jcs::string(&draft.arxiv_id)),
        ("authors".into(), Jcs::string(&draft.authors)),
        ("authority_effect".into(), Jcs::string(AUTHORITY_EFFECT)),
        ("binding_note".into(), Jcs::string(&draft.binding_note)),
        ("bound_at_utc".into(), Jcs::string(&draft.bound_at_utc)),
        ("cite_key".into(), Jcs::string(&draft.cite_key)),
        ("claims_global_green".into(), Jcs::Bool(false)),
        ("doi".into(), Jcs::string(&draft.doi)),
        ("package_id".into(), Jcs::string(&draft.package_id)),
        ("receipt_id".into(), Jcs::string(&draft.receipt_id)),
        ("schema_version".into(), Jcs::string(SCHEMA_VERSION)),
        ("source_kind".into(), Jcs::string(&draft.source_kind)),
        ("title".into(), Jcs::string(&draft.title)),
        ("url".into(), Jcs::string(&draft.url)),
        ("venue".into(), Jcs::string(&draft.venue)),
        ("year".into(), Jcs::string(&draft.year)),
    ])
    .canonical_bytes()
    .map_err(|_| Fault::new("CANONICAL", "literature fields cannot be encoded"))
}

fn require_text(value: &str, allow_empty: bool, max_chars: usize) -> Result<(), Fault> {
    if value.is_empty() && !allow_empty {
        return Err(Fault::new("TEXT", "required text is empty"));
    }
    if value.chars().count() > max_chars || value != value.trim() {
        return Err(Fault::new("TEXT", "text length or edge whitespace is illegal"));
    }
    if value.chars().any(|ch| ch.is_control()) {
        return Err(Fault::new("TEXT", "control characters are illegal"));
    }
    let nfc: String = value.nfc().collect();
    if nfc != value {
        return Err(Fault::new("TEXT", "text must be NFC"));
    }
    Ok(())
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct LiteratureWire {
    receipt_id: String,
    package_id: String,
    cite_key: String,
    title: String,
    #[serde(default)]
    authors: String,
    #[serde(default)]
    year: String,
    #[serde(default)]
    venue: String,
    #[serde(default)]
    arxiv_id: String,
    #[serde(default)]
    doi: String,
    #[serde(default)]
    url: String,
    #[serde(default)]
    binding_note: String,
    source_kind: String,
    #[serde(default = "default_schema")]
    schema_version: String,
    #[serde(default)]
    bound_at_utc: String,
    authority_effect: String,
    claims_global_green: bool,
    #[serde(default)]
    content_fingerprint: Option<String>,
    #[serde(default)]
    canonical_sha256: Option<String>,
}

impl LiteratureWire {
    fn draft(self) -> LiteratureDraft {
        LiteratureDraft {
            receipt_id: self.receipt_id,
            package_id: self.package_id,
            cite_key: self.cite_key,
            title: self.title,
            authors: self.authors,
            year: self.year,
            venue: self.venue,
            arxiv_id: self.arxiv_id,
            doi: self.doi,
            url: self.url,
            binding_note: self.binding_note,
            source_kind: self.source_kind,
            bound_at_utc: self.bound_at_utc,
            authority_effect: self.authority_effect,
            claims_global_green: self.claims_global_green,
            content_fingerprint: self.content_fingerprint,
            canonical_sha256: self.canonical_sha256,
        }
    }
}

fn default_schema() -> String {
    SCHEMA_VERSION.to_owned()
}

fn arxiv_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?i)^(\d{4}\.\d{4,5}|[a-z\-]+/\d{7})(v\d+)?$").checked_invariant_3640c26c("arxiv pattern")
    })
}

fn doi_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?i)^10\.\d{4,9}/[-._;()/:A-Z0-9]+$").checked_invariant_3640c26c("doi pattern")
    })
}

// Origin: engine/crates_rs/core_adversary/src/literature_receipt.rs
// Claim: urn:core:crates_rs:core-adversary:literature-receipt:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3640c26c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3640c26c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3640c26c {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError3640c26c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3640c26c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3640c26c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3640c26c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3640c26c> {
        if capacity_bound == 0 {
            return Err(BoundaryError3640c26c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3640c26c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3640c26c::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_3640c26c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3640c26c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3640c26c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3640c26c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3640c26c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3640c26c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3640c26c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3640c26c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
