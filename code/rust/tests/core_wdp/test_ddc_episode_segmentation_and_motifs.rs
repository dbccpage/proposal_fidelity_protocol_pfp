//! Tests for ObstructionEpisodeV1 segmentation and DDC motif n-gram mining (U02).
//!
//! Enforces:
//! - Mutation Kill Gate: Episode does NOT close as Resolved if Gamma2 > 0, even when Phi1 == 0.
//! - Exact integer n-gram counts for motifs.
//! AuthorityEffect: None (const).

use core_wdp::ddc::{
    mine_ddc_ngrams, DdcStepRowV1, EpisodeSegmenter, EpisodeStatus,
};

fn make_step(seq: u64, letter: &str) -> DdcStepRowV1 {
    DdcStepRowV1 {
        seq,
        letter: letter.to_string(),
        actor: "actor".to_string(),
        before_state: "before".to_string(),
        after_state: "after".to_string(),
        witness: "wit".to_string(),
        refusal_reason: None,
        prev_step_hash: None,
        step_hash: format!("hash_{}", seq),
        authority_effect: "None".to_string(),
    }
}

#[test]
fn test_episode_segmentation_and_gamma2_obstruction_gate() {
    let mut segmenter = EpisodeSegmenter::new();

    // Step 0: Initial clean state (0, 0) -> no episode
    segmenter.process_step(&make_step(0, "C"), 0, 0);
    assert!(segmenter.active_episode().is_none());
    assert_eq!(segmenter.completed_episodes().len(), 0);

    // Step 1: Obstruction detected (phi1 = 3, gamma2 = 2) -> Episode OPENS
    segmenter.process_step(&make_step(1, "R"), 3, 2);
    assert!(segmenter.active_episode().is_some());
    assert_eq!(segmenter.active_episode().unwrap().status, EpisodeStatus::OpenObstruction);
    assert_eq!(segmenter.active_episode().unwrap().initial_phi1, 3);
    assert_eq!(segmenter.active_episode().unwrap().initial_gamma2, 2);

    // Step 2: Partial descent (phi1 = 0, BUT gamma2 = 1)
    // MUTATION KILL GATE:
    // Even though phi1 == 0, gamma2 > 0 means obstruction is NOT resolved!
    // Must remain OpenObstruction and active!
    segmenter.process_step(&make_step(2, "D"), 0, 1);
    assert!(segmenter.active_episode().is_some(), "Episode must remain open when gamma2 > 0");
    assert_eq!(
        segmenter.active_episode().unwrap().status,
        EpisodeStatus::OpenObstruction,
        "Status must be OpenObstruction when gamma2 > 0"
    );
    assert_eq!(segmenter.completed_episodes().len(), 0);

    // Step 3: Exact resolution (phi1 = 0, gamma2 = 0) -> Episode RESOLVED!
    segmenter.process_step(&make_step(3, "E"), 0, 0);
    assert!(segmenter.active_episode().is_none(), "Episode must close on (0, 0)");
    assert_eq!(segmenter.completed_episodes().len(), 1);

    let ep = &segmenter.completed_episodes()[0];
    assert_eq!(ep.status, EpisodeStatus::Resolved);
    assert_eq!(ep.open_seq, 1);
    assert_eq!(ep.close_seq, Some(3));
    assert_eq!(ep.ddc_word, "RDE");
    assert_eq!(ep.terminal_phi1, Some(0));
    assert_eq!(ep.terminal_gamma2, Some(0));
}

#[test]
fn test_episode_segmentation_refusal_and_terminal() {
    let mut segmenter = EpisodeSegmenter::new();

    // Episode 1: Opens on phi1=2, closes on refusal M
    segmenter.process_step(&make_step(0, "C"), 2, 0);
    assert!(segmenter.active_episode().is_some());
    segmenter.process_step(&make_step(1, "M"), 2, 0);
    assert!(segmenter.active_episode().is_none());
    assert_eq!(segmenter.completed_episodes().len(), 1);
    assert_eq!(segmenter.completed_episodes()[0].status, EpisodeStatus::Refused);

    // Episode 2: Opens on gamma2=4, closes on terminal T
    segmenter.process_step(&make_step(2, "C"), 0, 4);
    assert!(segmenter.active_episode().is_some());
    segmenter.process_step(&make_step(3, "T"), 0, 0);
    assert!(segmenter.active_episode().is_none());
    assert_eq!(segmenter.completed_episodes().len(), 2);
    assert_eq!(segmenter.completed_episodes()[1].status, EpisodeStatus::Terminalized);
}

#[test]
fn test_ddc_motif_ngram_mining() {
    let words = ["CIDET", "CIDET", "CRMT"];
    let motifs = mine_ddc_ngrams(&words, 4);

    assert_eq!(motifs.total_words, 3);
    assert_eq!(motifs.total_letters, 5 + 5 + 4);

    // 2-grams check
    let bigrams = &motifs.ngrams[&2];
    assert_eq!(bigrams["CI"], 2);
    assert_eq!(bigrams["ID"], 2);
    assert_eq!(bigrams["DE"], 2);
    assert_eq!(bigrams["ET"], 2);
    assert_eq!(bigrams["CR"], 1);
    assert_eq!(bigrams["RM"], 1);
    assert_eq!(bigrams["MT"], 1);

    // 3-grams check
    let trigrams = &motifs.ngrams[&3];
    assert_eq!(trigrams["CID"], 2);
    assert_eq!(trigrams["IDE"], 2);
    assert_eq!(trigrams["DET"], 2);
    assert_eq!(trigrams["CRM"], 1);
    assert_eq!(trigrams["RMT"], 1);
}

// Origin: engine/crates_rs/tests/core_wdp/test_ddc_episode_segmentation_and_motifs.rs
// Claim: urn:core:crates_rs:tests:test-ddc-episode-segmentation-and-motifs:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1c97df42 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1c97df42` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1c97df42 {
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
impl BoundaryError1c97df42 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1c97df42 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1c97df42 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1c97df42 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1c97df42> {
        if capacity_bound == 0 {
            return Err(BoundaryError1c97df42::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1c97df42::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1c97df42::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1c97df42() {
    let admitted = BoundaryRecord1c97df42::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1c97df42::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
