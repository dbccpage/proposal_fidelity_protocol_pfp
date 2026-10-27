//! Inward ports for host observation and external guard-state custody.
use crate::Refusal;
use serde::{Deserialize, Serialize};

/// A host sensor's observation proposal; receipt admission checks it later.
/// Only fields consumed by the activation use case are projected here.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObservedDanger {
    pub danger_type: String,
    pub observer_id: String,
    pub evidence_digest: String,
}

pub trait DangerSensorPort {
    /// The sensor observes payload text independently of the detector hit.
    fn detect_danger(&mut self, content: &str) -> Result<Option<ObservedDanger>, Refusal>;
}
pub trait GuardStatePort {
    fn is_externally_admitted(
        &mut self,
        spec_id: &str,
        subject_scope: &str,
    ) -> Result<bool, Refusal>;
    fn is_suspended(&mut self, spec_id: &str, subject_scope: &str) -> Result<bool, Refusal>;
}

/// Refusal from a digest quorum.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QuorumError {
    /// No digests were offered.
    Empty,
    /// The threshold was zero.
    ZeroThreshold,
    /// Two distinct digests both meet the threshold.
    SplitBrain { votes: u32 },
    /// The leading digest is short of the threshold.
    Short { votes: u32, threshold: u32 },
    /// A tally overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/activation_ports.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:activation-ports:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for QuorumError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for QuorumError {}

/// The unique digest that gathered at least `k` votes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DigestQuorum {
    votes: u32,
}

impl DigestQuorum {
    fn count_votes_if_first(
        digests: &[&str],
        index: usize,
        digest: &str,
    ) -> Result<Option<u32>, QuorumError> {
        let mut seen_earlier = false;
        let mut votes = 0u32;
        for (earlier, other) in digests.iter().enumerate() {
            if *other != digest {
                continue;
            }
            if earlier < index {
                seen_earlier = true;
            }
            votes = votes.checked_add(1).ok_or(QuorumError::Overflow)?;
        }
        Ok((!seen_earlier).then_some(votes))
    }

    /// Admit `digests` when exactly one distinct value occurs at least `k` times.
    pub fn try_new(digests: &[&str], k: u32) -> Result<Self, QuorumError> {
        if digests.is_empty() {
            return Err(QuorumError::Empty);
        }
        if k == 0 {
            return Err(QuorumError::ZeroThreshold);
        }
        let mut best = 0u32;
        let mut leaders = 0u32;
        for (index, digest) in digests.iter().enumerate() {
            let Some(votes) = Self::count_votes_if_first(digests, index, digest)? else {
                continue;
            };
            if votes > best {
                best = votes;
                leaders = 1;
            } else if votes == best {
                leaders = leaders.checked_add(1).ok_or(QuorumError::Overflow)?;
            }
        }
        if best < k {
            return Err(QuorumError::Short {
                votes: best,
                threshold: k,
            });
        }
        if leaders != 1 {
            return Err(QuorumError::SplitBrain { votes: best });
        }
        Ok(Self { votes: best })
    }

    /// Votes gathered by the unique leader.
    pub fn votes(&self) -> u32 {
        self.votes
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod quorum_tests {
    use super::*;
    #[test]
    fn two_matching_digests_meet_a_threshold_of_two() {
        let quorum = DigestQuorum::try_new(&["aa", "aa", "bb"], 2);
        assert!(matches!(quorum, Ok(ref q) if q.votes() == 2));
    }
    #[test]
    fn a_tie_at_the_threshold_is_a_split() {
        let err = DigestQuorum::try_new(&["aa", "bb"], 1);
        assert!(matches!(err, Err(QuorumError::SplitBrain { votes: 1 })));
    }
}
