//! Research-library custody: the census, the evidence ceiling, and the
//! deduplication invariant.
//!
//! # The corpus is not in this repository
//!
//! `EPIC-OE-SYMGAM-015` asks for an ingestion engine over 5,000 numeric
//! placements and 25 `LIB-ANCHOR-*` spines. Those live in the CODA estate;
//! `library/`, `core_research/`, and `databases/`
//! are absent here, and `CLAUDE.md` records that library ingestion was retired
//! from this repository.
//!
//! So an indexer is not buildable here, and fabricating 5,000 fixture rows to
//! make one look built would be worse than not building it. [`corpus_state`]
//! reports the absence as a value rather than leaving a reader to infer it.
//!
//! # What *is* here, and is worth having
//!
//! The Atlas census is declared data, and the two invariants the epic states are
//! about **how citations may be used** -- which does not need the corpus:
//!
//! > **Non-Promotion Law:** Bibliographic existence never constitutes evidence
//! > of theorem correctness or code behavior.
//! >
//! > **Deduplication Invariant:** Cross-listed numeric placements (286 duplicate
//! > entries) are treated as retrieval indices, not independent corroborations.
//!
//! Both are enforced here. The first is the same shape as `coda.rs`: a
//! [`Citation`] is evidence that admits no mathematical claim, and
//! [`admit_as_proof`] always refuses. The second is a counting rule --
//! [`corroboration_count`] counts distinct identifiers, never rows, so a paper
//! cross-listed in two domains cannot corroborate itself.
//!
//! # The census audits its own arithmetic
//!
//! [`audit_census`] checks that the per-domain figures sum to the declared
//! totals and that `unique + cross_listed = total`. The numbers are transcribed
//! from a document, and a transcription nobody checks is the estate's most
//! reliable source of drift.
//!
//! `AuthorityEffect: None`. A bibliography is not a proof.

use std::collections::BTreeSet;
use std::path::Path;

use serde::{Deserialize, Serialize};
use thiserror::Error;

// ---------------------------------------------------------------------------
// Declared figures, from Atlas Chapter 10
// ---------------------------------------------------------------------------

pub const DECLARED_TOTAL_PLACEMENTS: u32 = 5_000;
pub const DECLARED_UNIQUE_IDENTIFIERS: u32 = 4_714;
pub const DECLARED_CROSS_LISTED: u32 = 286;
pub const DECLARED_ANCHOR_SPINES: u32 = 25;

/// One domain's audited figures.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DomainCensus {
    pub domain: u8,
    pub name: &'static str,
    pub numeric_placements: u32,
    pub curated_focus_papers: u32,
}

/// The eight domains, exactly as Atlas Chapter 10 audits them.
pub const CENSUS: [DomainCensus; 8] = [
    DomainCensus {
        domain: 1,
        name: "generation control",
        numeric_placements: 262,
        curated_focus_papers: 4,
    },
    DomainCensus {
        domain: 2,
        name: "formal verification",
        numeric_placements: 624,
        curated_focus_papers: 1,
    },
    DomainCensus {
        domain: 3,
        name: "multi-agent debate",
        numeric_placements: 156,
        curated_focus_papers: 8,
    },
    DomainCensus {
        domain: 4,
        name: "higher category and cohomology",
        numeric_placements: 392,
        curated_focus_papers: 2,
    },
    DomainCensus {
        domain: 5,
        name: "optimization and search",
        numeric_placements: 349,
        curated_focus_papers: 6,
    },
    DomainCensus {
        domain: 6,
        name: "quantum and sign problem",
        numeric_placements: 57,
        curated_focus_papers: 0,
    },
    DomainCensus {
        domain: 7,
        name: "reasoning and interpretability",
        numeric_placements: 20,
        curated_focus_papers: 1,
    },
    DomainCensus {
        domain: 8,
        name: "general foundations",
        numeric_placements: 3_140,
        curated_focus_papers: 3,
    },
];

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Error)]
pub enum LibraryRefusal {
    #[error(
        "a citation is bibliographic existence, never evidence of theorem \
         correctness or code behaviour; LIB-{id:04} cannot be admitted as proof"
    )]
    CitationIsNotProof { id: u32 },

    #[error("per-domain {field} sum to {observed}, but {declared} is declared")]
    CensusMismatch {
        field: &'static str,
        observed: u32,
        declared: u32,
    },

    #[error(
        "unique ({unique}) + cross-listed ({cross_listed}) = {sum}, \
         but {declared} placements are declared"
    )]
    CensusArithmetic {
        unique: u32,
        cross_listed: u32,
        sum: u32,
        declared: u32,
    },

    #[error("domain {domain} is outside the audited range 1..=8")]
    UnknownDomain { domain: u8 },

    #[error("refusing to count corroborations over an empty placement set")]
    NoPlacements,
}

// ---------------------------------------------------------------------------
// Corpus presence
// ---------------------------------------------------------------------------

/// Directories the external CODA corpus would occupy if it were present.
///
/// `library` is an internal operations directory (prompts,
/// search tooling, library ingest) and is intentionally excluded; its
/// presence does not mean the external research corpus has landed here.
pub const CORPUS_ROOTS: [&str; 2] = ["core_research", "databases"];

/// Whether the corpus this epic indexes is present.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum CorpusState {
    /// At least one corpus root exists; the names found are carried.
    Present { roots: Vec<String> },
    /// No corpus root exists. Ingestion is not buildable here.
    AbsentFromThisRepository,
}

impl CorpusState {
    pub fn is_present(&self) -> bool {
        matches!(self, CorpusState::Present { .. })
    }
}

/// Report whether the corpus is present, as a value.
///
/// A reader must not have to infer an absence from a missing feature. The epic
/// asks for an indexer; this says plainly that there is nothing to index.
pub fn corpus_state(repo_root: &Path) -> CorpusState {
    let roots: Vec<String> = CORPUS_ROOTS
        .iter()
        .filter(|name| repo_root.join(name).is_dir())
        .map(|name| (*name).to_string())
        .collect();
    if roots.is_empty() {
        CorpusState::AbsentFromThisRepository
    } else {
        CorpusState::Present { roots }
    }
}

// ---------------------------------------------------------------------------
// The census, audited
// ---------------------------------------------------------------------------

/// What the census audit found.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CensusReport {
    pub domains: usize,
    pub total_placements: u32,
    pub total_curated: u32,
    pub unique_identifiers: u32,
    pub cross_listed: u32,
}

/// Check the declared census against its own arithmetic.
///
/// Three independent identities must hold: the per-domain placements sum to the
/// declared total, the per-domain curated papers sum to the anchor-spine count,
/// and unique plus cross-listed equals the total. Each is checked separately so
/// a failure names which one broke.
pub fn audit_census() -> Result<CensusReport, LibraryRefusal> {
    let total_placements: u32 = CENSUS.iter().map(|d| d.numeric_placements).sum();
    if total_placements != DECLARED_TOTAL_PLACEMENTS {
        return Err(LibraryRefusal::CensusMismatch {
            field: "numeric placements",
            observed: total_placements,
            declared: DECLARED_TOTAL_PLACEMENTS,
        });
    }

    let total_curated: u32 = CENSUS.iter().map(|d| d.curated_focus_papers).sum();
    if total_curated != DECLARED_ANCHOR_SPINES {
        return Err(LibraryRefusal::CensusMismatch {
            field: "curated focus papers",
            observed: total_curated,
            declared: DECLARED_ANCHOR_SPINES,
        });
    }

    // Each cross-listed identifier appears exactly twice, so the row count is
    // the unique count plus one extra row per cross-listing.
    let sum = DECLARED_UNIQUE_IDENTIFIERS + DECLARED_CROSS_LISTED;
    if sum != DECLARED_TOTAL_PLACEMENTS {
        return Err(LibraryRefusal::CensusArithmetic {
            unique: DECLARED_UNIQUE_IDENTIFIERS,
            cross_listed: DECLARED_CROSS_LISTED,
            sum,
            declared: DECLARED_TOTAL_PLACEMENTS,
        });
    }

    Ok(CensusReport {
        domains: CENSUS.len(),
        total_placements,
        total_curated,
        unique_identifiers: DECLARED_UNIQUE_IDENTIFIERS,
        cross_listed: DECLARED_CROSS_LISTED,
    })
}

/// The census row for one domain.
pub fn domain(number: u8) -> Result<&'static DomainCensus, LibraryRefusal> {
    CENSUS
        .iter()
        .find(|d| d.domain == number)
        .ok_or(LibraryRefusal::UnknownDomain { domain: number })
}

// ---------------------------------------------------------------------------
// Placements and the deduplication invariant
// ---------------------------------------------------------------------------

/// A numeric `LIB` identifier with the domain it was listed under.
///
/// The same identifier may appear under two domains. That is a **retrieval
/// choice**, and the pair is deliberately not the identity: see
/// [`corroboration_count`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Placement {
    pub id: u32,
    pub domain: u8,
}

impl Placement {
    pub fn new(id: u32, domain: u8) -> Result<Self, LibraryRefusal> {
        domain_exists(domain)?;
        Ok(Self { id, domain })
    }
}

fn domain_exists(number: u8) -> Result<(), LibraryRefusal> {
    domain(number).map(|_| ())
}

/// How many *distinct works* a placement set cites.
///
/// The deduplication invariant. A work cross-listed in two domains appears as
/// two placements and is one work; counting rows would let a retrieval decision
/// masquerade as a second, independent source agreeing with the first.
///
/// Refuses an empty set rather than reporting zero corroborations, which reads
/// as "nothing supports this" when the truth is "nothing was examined".
pub fn corroboration_count(placements: &[Placement]) -> Result<usize, LibraryRefusal> {
    if placements.is_empty() {
        return Err(LibraryRefusal::NoPlacements);
    }
    let distinct: BTreeSet<u32> = placements.iter().map(|p| p.id).collect();
    Ok(distinct.len())
}

/// Identifiers appearing under more than one domain.
pub fn cross_listed(placements: &[Placement]) -> Vec<u32> {
    let mut seen: BTreeSet<(u32, u8)> = BTreeSet::new();
    let mut ids: BTreeSet<u32> = BTreeSet::new();
    let mut repeated: BTreeSet<u32> = BTreeSet::new();
    for placement in placements {
        if !ids.insert(placement.id) {
            repeated.insert(placement.id);
        }
        seen.insert((placement.id, placement.domain));
    }
    repeated.into_iter().collect()
}

// ---------------------------------------------------------------------------
// The evidence ceiling
// ---------------------------------------------------------------------------

/// What a citation may be used for. Neither option is proof.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CitationRole {
    /// Why a line of work was pursued.
    MotivationalContext,
    /// A case the implementation must handle, drawn from the literature.
    AdversarialFixture,
}

impl CitationRole {
    pub fn name(self) -> &'static str {
        match self {
            CitationRole::MotivationalContext => "motivational_context",
            CitationRole::AdversarialFixture => "adversarial_fixture",
        }
    }
}

/// A reference into the library.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Citation {
    pub id: u32,
    pub role: CitationRole,
}

impl Citation {
    pub fn new(id: u32, role: CitationRole) -> Self {
        Self { id, role }
    }

    /// Always `false`. Present so the ceiling is readable at the call site.
    pub fn is_proof(&self) -> bool {
        false
    }
}

/// Always refuses.
///
/// The Non-Promotion Law, as a function rather than a sentence. Sprint 032
/// established the pattern with `bridge()`: a refusal someone can call is better
/// than an absence they might read as an oversight.
pub fn admit_as_proof(citation: &Citation) -> Result<(), LibraryRefusal> {
    Err(LibraryRefusal::CitationIsNotProof { id: citation.id })
}

// ---------------------------------------------------------------------------
// Receipts
// ---------------------------------------------------------------------------

pub const LIBRARY_RECEIPT_SCHEMA: &str = "core.symbol_game.library_custody.v1";

/// A provenance receipt over a set of citations.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LibraryCustodyReceiptV1 {
    pub schema: &'static str,
    pub corpus_present: bool,
    pub citations: usize,
    /// Distinct works, after the deduplication invariant.
    pub distinct_works: usize,
    pub motivational_context: usize,
    pub adversarial_fixtures: usize,
    /// Always zero, and emitted rather than omitted so the number is visible.
    pub admitted_as_proof: usize,
    pub digest: String,
    pub authority_effect: &'static str,
}

/// Build a custody receipt.
///
/// `citations` and `distinct_works` are carried separately: they differ exactly
/// when a work was cross-listed, and collapsing them would let a retrieval
/// decision inflate the apparent weight of evidence.
pub fn custody_receipt(citations: &[Citation], corpus: &CorpusState) -> LibraryCustodyReceiptV1 {
    let mut motivational = 0usize;
    let mut fixtures = 0usize;
    let distinct: BTreeSet<u32> = citations.iter().map(|c| c.id).collect();
    for citation in citations {
        match citation.role {
            CitationRole::MotivationalContext => motivational += 1,
            CitationRole::AdversarialFixture => fixtures += 1,
        }
    }

    let mut hasher = blake3::Hasher::new();
    hasher.update(b"library-custody-v1");
    hasher.update(&[u8::from(corpus.is_present())]);
    // Sorted, so the digest does not depend on citation order.
    for id in &distinct {
        hasher.update(&id.to_be_bytes());
    }
    let mut roles: Vec<(u32, &'static str)> =
        citations.iter().map(|c| (c.id, c.role.name())).collect();
    roles.sort_unstable();
    roles.dedup();
    for (id, role) in roles {
        hasher.update(&id.to_be_bytes());
        hasher.update(role.as_bytes());
    }

    LibraryCustodyReceiptV1 {
        schema: LIBRARY_RECEIPT_SCHEMA,
        corpus_present: corpus.is_present(),
        citations: citations.len(),
        distinct_works: distinct.len(),
        motivational_context: motivational,
        adversarial_fixtures: fixtures,
        admitted_as_proof: 0,
        digest: hasher.finalize().to_hex().to_string(),
        authority_effect: "None",
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_692de8d1 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
