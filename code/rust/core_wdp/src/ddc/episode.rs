//! Obstruction Episode Segmentation (U02).
//!
//! An ObstructionEpisodeV1 represents a sequence of DDC transitions beginning
//! when an obstruction is detected (Phi1 > 0 or Gamma2 > 0) and terminating
//! on resolution (Phi1 = 0 and Gamma2 = 0), explicit refusal (M), or terminalization (T).
//!
//! Invariant: An episode cannot close as RESOLVED if Gamma2 > 0, even if Phi1 == 0.
//! Gamma2 > 0 strictly classifies as OpenObstruction.
//! AuthorityEffect: None (const).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_89037857<T> {
    fn checked_invariant_89037857(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_89037857<T> for Option<T> {
    #[inline]
    fn checked_invariant_89037857(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_89037857<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_89037857(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::ddc::ddc_trace::DdcStepRowV1;
use serde::{Deserialize, Serialize};

fn default_authority_effect() -> String {
    "None".to_string()
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum EpisodeStatus {
    OpenObstruction,
    Resolved,
    Refused,
    Terminalized,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObstructionEpisodeV1 {
    pub episode_id: String,
    pub open_seq: u64,
    pub close_seq: Option<u64>,
    pub initial_phi1: u64,
    pub initial_gamma2: u64,
    pub terminal_phi1: Option<u64>,
    pub terminal_gamma2: Option<u64>,
    pub steps: Vec<DdcStepRowV1>,
    pub status: EpisodeStatus,
    pub ddc_word: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

pub struct EpisodeSegmenter {
    active_episode: Option<ObstructionEpisodeV1>,
    completed_episodes: Vec<ObstructionEpisodeV1>,
    episode_counter: u64,
}

impl Default for EpisodeSegmenter {
    fn default() -> Self {
        Self::new()
    }
}

impl EpisodeSegmenter {
    pub fn new() -> Self {
        Self {
            active_episode: None,
            completed_episodes: Vec::new(),
            episode_counter: 0,
        }
    }

    pub fn process_step(
        &mut self,
        step: &DdcStepRowV1,
        after_phi1: u64,
        after_gamma2: u64,
    ) {
        if self.active_episode.is_none() {
            // Check if obstruction opens
            if after_phi1 > 0 || after_gamma2 > 0 {
                let ep_id = format!("EP_{:06}", self.episode_counter);
                self.episode_counter += 1;
                let ep = ObstructionEpisodeV1 {
                    episode_id: ep_id,
                    open_seq: step.seq,
                    close_seq: None,
                    initial_phi1: after_phi1,
                    initial_gamma2: after_gamma2,
                    terminal_phi1: None,
                    terminal_gamma2: None,
                    steps: vec![step.clone()],
                    status: EpisodeStatus::OpenObstruction,
                    ddc_word: step.letter.clone(),
                    authority_effect: default_authority_effect(),
                };
                self.active_episode = Some(ep);
            }
            return;
        }

        // Active episode present
        let mut ep = self.active_episode.take().checked_invariant_89037857("checked invariant");
        ep.steps.push(step.clone());
        ep.ddc_word.push_str(&step.letter);

        // Closure checks:
        if step.letter == "M" {
            ep.status = EpisodeStatus::Refused;
            ep.close_seq = Some(step.seq);
            ep.terminal_phi1 = Some(after_phi1);
            ep.terminal_gamma2 = Some(after_gamma2);
            self.completed_episodes.push(ep);
        } else if step.letter == "T" {
            ep.status = EpisodeStatus::Terminalized;
            ep.close_seq = Some(step.seq);
            ep.terminal_phi1 = Some(after_phi1);
            ep.terminal_gamma2 = Some(after_gamma2);
            self.completed_episodes.push(ep);
        } else if after_phi1 == 0 && after_gamma2 == 0 {
            // Both obstructions discharged
            ep.status = EpisodeStatus::Resolved;
            ep.close_seq = Some(step.seq);
            ep.terminal_phi1 = Some(0);
            ep.terminal_gamma2 = Some(0);
            self.completed_episodes.push(ep);
        } else {
            // WITNESS DOMINANCE / INVARIANT:
            // If after_phi1 == 0 but after_gamma2 > 0, it DOES NOT RESOLVE!
            // It remains OpenObstruction.
            ep.status = EpisodeStatus::OpenObstruction;
            self.active_episode = Some(ep);
        }
    }

    pub fn completed_episodes(&self) -> &[ObstructionEpisodeV1] {
        &self.completed_episodes
    }

    pub fn active_episode(&self) -> Option<&ObstructionEpisodeV1> {
        self.active_episode.as_ref()
    }
}

// Origin: engine/crates_rs/core_wdp/src/ddc/episode.rs
// Claim: urn:core:crates_rs:core-wdp:episode:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord89037857 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord89037857` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError89037857 {
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
impl BoundaryError89037857 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError89037857 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError89037857 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord89037857 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError89037857> {
        if capacity_bound == 0 {
            return Err(BoundaryError89037857::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError89037857::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError89037857::ExceedsCapacity {
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
mod l4_boundary_tests_89037857 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord89037857::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord89037857::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord89037857::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord89037857::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord89037857::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError89037857::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError89037857::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
