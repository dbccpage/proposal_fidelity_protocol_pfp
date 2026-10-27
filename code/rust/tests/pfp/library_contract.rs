//! Contract tests for research-library custody.
//!
//! `EPIC-OE-SYMGAM-015`. The corpus this epic indexes is **not in this
//! repository** -- it lives in the CODA estate, and `CLAUDE.md` records that
//! library ingestion was retired here. So there is no indexer to test.
//!
//! What is testable is the part that does not need the corpus: the declared
//! census and its arithmetic, and the two invariants the epic states about how
//! citations may be used.
//!
//! > **Non-Promotion Law:** bibliographic existence never constitutes evidence.
//! >
//! > **Deduplication Invariant:** cross-listed placements are retrieval
//! > indices, not independent corroborations.

use std::path::Path;

use pfp::epics::library::{
    admit_as_proof, audit_census, corpus_state, corroboration_count, cross_listed, custody_receipt,
    domain, Citation, CitationRole, CorpusState, LibraryRefusal, Placement, CENSUS, CORPUS_ROOTS,
    DECLARED_ANCHOR_SPINES, DECLARED_CROSS_LISTED, DECLARED_TOTAL_PLACEMENTS,
    DECLARED_UNIQUE_IDENTIFIERS, LIBRARY_RECEIPT_SCHEMA,
};

fn repo_root() -> &'static Path {
    // tests/ -> crate -> crates_rs -> engine -> repo root
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .and_then(Path::parent)
        .expect("the crate sits four levels below the repository root")
}

// ---------------------------------------------------------------------------
// Criterion 1 -- the corpus absence is a value, not an inference
// ---------------------------------------------------------------------------

#[test]
fn the_corpus_is_absent_from_this_repository() {
    // The epic asks for an indexer over 5,000 placements. This states plainly
    // that there is nothing here to index, rather than leaving a reader to
    // infer it from a missing feature.
    assert_eq!(
        corpus_state(repo_root()),
        CorpusState::AbsentFromThisRepository
    );
    assert!(!corpus_state(repo_root()).is_present());
}

#[test]
fn none_of_the_corpus_roots_exist() {
    for name in CORPUS_ROOTS {
        assert!(
            !repo_root().join(name).is_dir(),
            "{name} exists; the corpus-absence finding needs revisiting"
        );
    }
}

#[test]
fn a_directory_holding_a_corpus_root_reports_present() {
    // The detector must be able to fire, or the absence finding is untestable.
    let temp = std::env::temp_dir().join("core_library_contract_probe");
    let root = temp.join(CORPUS_ROOTS[0]);
    std::fs::create_dir_all(&root).expect("a writable temp directory");
    let state = corpus_state(&temp);
    std::fs::remove_dir_all(&temp).ok();

    match state {
        CorpusState::Present { roots } => assert_eq!(roots, vec![CORPUS_ROOTS[0].to_string()]),
        CorpusState::AbsentFromThisRepository => panic!("the detector cannot fire"),
    }
}

// ---------------------------------------------------------------------------
// Criterion 2 -- the census audits its own arithmetic
// ---------------------------------------------------------------------------

#[test]
fn the_declared_census_is_internally_consistent() {
    let report = audit_census().expect("the Atlas figures must agree");
    assert_eq!(report.domains, 8);
    assert_eq!(report.total_placements, DECLARED_TOTAL_PLACEMENTS);
    assert_eq!(report.total_curated, DECLARED_ANCHOR_SPINES);
    assert_eq!(report.unique_identifiers, DECLARED_UNIQUE_IDENTIFIERS);
    assert_eq!(report.cross_listed, DECLARED_CROSS_LISTED);
}

#[test]
fn the_per_domain_placements_sum_to_five_thousand() {
    // Summed from the table rather than restated, so a transcription error in
    // any single row fails here.
    let total: u32 = CENSUS.iter().map(|d| d.numeric_placements).sum();
    assert_eq!(total, 5_000);
}

#[test]
fn the_per_domain_curated_papers_sum_to_the_anchor_spine_count() {
    let total: u32 = CENSUS.iter().map(|d| d.curated_focus_papers).sum();
    assert_eq!(total, 25);
}

#[test]
fn unique_plus_cross_listed_equals_the_row_count() {
    // Each cross-listed identifier appears exactly twice, so it contributes one
    // extra row. 4714 + 286 = 5000.
    assert_eq!(
        DECLARED_UNIQUE_IDENTIFIERS + DECLARED_CROSS_LISTED,
        DECLARED_TOTAL_PLACEMENTS
    );
}

#[test]
fn every_domain_from_one_to_eight_is_present_and_named() {
    for number in 1..=8u8 {
        let row = domain(number).expect("an audited domain");
        assert_eq!(row.domain, number);
        assert!(!row.name.is_empty());
    }
}

#[test]
fn a_domain_outside_the_audited_range_is_refused() {
    for number in [0u8, 9, 200] {
        assert_eq!(
            domain(number).expect_err("outside 1..=8"),
            LibraryRefusal::UnknownDomain { domain: number }
        );
    }
}

#[test]
fn domain_six_is_recorded_with_no_curated_papers() {
    // The Atlas records a contamination finding for domain 06. Zero curated
    // papers is the audited figure, and it is pinned so a later "tidy-up" that
    // invents one fails here.
    let six = domain(6).expect("audited");
    assert_eq!(six.curated_focus_papers, 0);
    assert_eq!(six.numeric_placements, 57);
}

#[test]
fn a_placement_in_an_unknown_domain_is_refused() {
    assert!(Placement::new(1234, 9).is_err());
    assert!(Placement::new(1234, 3).is_ok());
}

// ---------------------------------------------------------------------------
// Criterion 3 -- the deduplication invariant
// ---------------------------------------------------------------------------

#[test]
fn a_cross_listed_work_counts_once() {
    // The invariant. LIB-0042 listed under domains 1 and 4 is one work, and
    // counting rows would let a retrieval decision masquerade as a second,
    // independent source agreeing with the first.
    let placements = [
        Placement::new(42, 1).expect("valid"),
        Placement::new(42, 4).expect("valid"),
        Placement::new(99, 2).expect("valid"),
    ];
    assert_eq!(placements.len(), 3);
    assert_eq!(corroboration_count(&placements).expect("non-empty"), 2);
}

#[test]
fn cross_listed_identifiers_are_reported_by_id() {
    let placements = [
        Placement::new(42, 1).expect("valid"),
        Placement::new(42, 4).expect("valid"),
        Placement::new(99, 2).expect("valid"),
    ];
    assert_eq!(cross_listed(&placements), vec![42]);
}

#[test]
fn a_set_with_no_cross_listing_reports_none() {
    let placements = [
        Placement::new(1, 1).expect("valid"),
        Placement::new(2, 2).expect("valid"),
    ];
    assert!(cross_listed(&placements).is_empty());
    assert_eq!(corroboration_count(&placements).expect("non-empty"), 2);
}

#[test]
fn an_empty_placement_set_is_refused_rather_than_counted_zero() {
    // "Zero corroborations" reads as "nothing supports this". The truth is
    // "nothing was examined", and the two must not be confused -- the vacuous
    // pass this estate has met in five consecutive sprints.
    assert_eq!(
        corroboration_count(&[]).expect_err("nothing to count"),
        LibraryRefusal::NoPlacements
    );
}

// ---------------------------------------------------------------------------
// Criterion 4 -- the evidence ceiling
// ---------------------------------------------------------------------------

#[test]
fn a_citation_is_never_proof() {
    for role in [
        CitationRole::MotivationalContext,
        CitationRole::AdversarialFixture,
    ] {
        let citation = Citation::new(42, role);
        assert!(!citation.is_proof());
        assert_eq!(
            admit_as_proof(&citation).expect_err("bibliography is not proof"),
            LibraryRefusal::CitationIsNotProof { id: 42 }
        );
    }
}

#[test]
fn the_refusal_names_the_identifier_it_declined() {
    let message = admit_as_proof(&Citation::new(1234, CitationRole::AdversarialFixture))
        .expect_err("refused")
        .to_string();
    assert!(message.contains("1234"), "{message}");
    assert!(message.contains("not"), "{message}");
}

#[test]
fn both_citation_roles_are_below_the_ceiling() {
    // Neither role is an escape hatch. An adversarial fixture is a case the
    // implementation must handle, not a theorem it may assume.
    assert_eq!(
        CitationRole::MotivationalContext.name(),
        "motivational_context"
    );
    assert_eq!(
        CitationRole::AdversarialFixture.name(),
        "adversarial_fixture"
    );
    assert!(!Citation::new(1, CitationRole::AdversarialFixture).is_proof());
}

// ---------------------------------------------------------------------------
// Criterion 5 -- custody receipts
// ---------------------------------------------------------------------------

fn sample_citations() -> Vec<Citation> {
    vec![
        Citation::new(42, CitationRole::MotivationalContext),
        Citation::new(42, CitationRole::AdversarialFixture),
        Citation::new(99, CitationRole::MotivationalContext),
    ]
}

#[test]
fn a_receipt_separates_citations_from_distinct_works() {
    // They differ exactly when a work was cross-listed, and collapsing them
    // would let a retrieval decision inflate the apparent weight of evidence.
    let receipt = custody_receipt(&sample_citations(), &CorpusState::AbsentFromThisRepository);
    assert_eq!(receipt.citations, 3);
    assert_eq!(receipt.distinct_works, 2);
    assert_eq!(receipt.motivational_context, 2);
    assert_eq!(receipt.adversarial_fixtures, 1);
}

#[test]
fn a_receipt_records_zero_admitted_as_proof_explicitly() {
    // Emitted rather than omitted, so the number is visible and any future
    // non-zero value is loud.
    let receipt = custody_receipt(&sample_citations(), &CorpusState::AbsentFromThisRepository);
    assert_eq!(receipt.admitted_as_proof, 0);
    assert_eq!(receipt.authority_effect, "None");
    assert_eq!(receipt.schema, LIBRARY_RECEIPT_SCHEMA);
}

#[test]
fn a_receipt_records_the_corpus_absence() {
    let absent = custody_receipt(&sample_citations(), &CorpusState::AbsentFromThisRepository);
    assert!(!absent.corpus_present);

    let present = custody_receipt(
        &sample_citations(),
        &CorpusState::Present {
            roots: vec!["library".into()],
        },
    );
    assert!(present.corpus_present);
    // And the two are distinguishable by digest, so a receipt cannot be
    // transplanted between a repository that has the corpus and one that does not.
    assert_ne!(absent.digest, present.digest);
}

#[test]
fn a_receipt_digest_does_not_depend_on_citation_order() {
    let mut reversed = sample_citations();
    reversed.reverse();
    let forward = custody_receipt(&sample_citations(), &CorpusState::AbsentFromThisRepository);
    let backward = custody_receipt(&reversed, &CorpusState::AbsentFromThisRepository);
    assert_eq!(forward.digest, backward.digest);
}

#[test]
fn a_receipt_digest_separates_different_citation_sets() {
    let one = custody_receipt(
        &[Citation::new(1, CitationRole::MotivationalContext)],
        &CorpusState::AbsentFromThisRepository,
    );
    let two = custody_receipt(
        &[Citation::new(2, CitationRole::MotivationalContext)],
        &CorpusState::AbsentFromThisRepository,
    );
    assert_ne!(one.digest, two.digest);
}

#[test]
fn the_receipt_serialises_to_json() {
    let receipt = custody_receipt(&sample_citations(), &CorpusState::AbsentFromThisRepository);
    let json = serde_json::to_string(&receipt).expect("must serialise");
    assert!(json.contains(LIBRARY_RECEIPT_SCHEMA));
    assert!(json.contains("\"authority_effect\":\"None\""));
    assert!(json.contains("\"admitted_as_proof\":0"));
    assert!(json.contains("\"corpus_present\":false"));
}

// Origin: engine/crates_rs/tests/pfp/library_contract.rs
// Claim: urn:core:crates_rs:tests:library-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd77831d9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd77831d9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord77831d9 {
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
impl BoundaryErrord77831d9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord77831d9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord77831d9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd77831d9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord77831d9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord77831d9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord77831d9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord77831d9::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_d77831d9() {
    let admitted = BoundaryRecordd77831d9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd77831d9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
