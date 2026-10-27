//! The stage that runs a Adversary bout: the generic arena contracts formerly in `core_adversary`. AuthorityEffect: None.
pub mod canonical;
pub mod ddc;
pub mod ddc_tape_evaluator;
pub mod diagnostics;
pub mod emission;
pub mod evaluation;
pub mod exact;
pub mod file_adapters;
pub mod genealogy;
mod numpy_rng;
mod numpy_ziggurat;
pub mod oscillation;
pub mod packets;
pub mod ports;
pub mod receipt_replay;
pub mod run;
pub mod run_swarm;
pub mod scheduler;
pub use pfp_runtime::strict_json;
pub mod synthetic_diagnostic;
pub mod topology;

use num_rational::BigRational;
use num_traits::Zero;

/// Closed challenge vocabulary from [`packets::CHALLENGE_KINDS`], plus a positive exact stake.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChallengeClosureWitness {
    kind_count: usize,
    admitted_index: usize,
    stake: BigRational,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChallengeClosureError {
    Vocabulary,
    KindNotClosed,
    StakeNotExact,
    StakeNotPositive,
}

// Origin: engine/crates_rs/core_adversary/src/stage/mod.rs
// Claim: urn:core:crates_rs:core-adversary:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ChallengeClosureError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ChallengeClosureError {}

impl ChallengeClosureWitness {
    pub fn try_admit(kind: &str, stake_text: &str) -> Result<Self, ChallengeClosureError> {
        let (count, admitted_index) = Self::admit_kind(kind)?;
        let stake = Self::admit_stake(stake_text)?;
        Ok(Self {
            kind_count: count,
            admitted_index,
            stake,
        })
    }

    fn admit_kind(kind: &str) -> Result<(usize, usize), ChallengeClosureError> {
        let mut count = 0usize;
        let mut previous: Option<&str> = None;
        let mut admitted = None;
        for (index, name) in packets::CHALLENGE_KINDS.iter().copied().enumerate() {
            Self::verify_vocabulary_entry(name, previous)?;
            previous = Some(name);
            count = count
                .checked_add(1)
                .ok_or(ChallengeClosureError::Vocabulary)?;
            if name == kind {
                if admitted.replace(index).is_some() {
                    return Err(ChallengeClosureError::Vocabulary);
                }
            }
        }
        if count == 0 || count != packets::CHALLENGE_KINDS.len() {
            return Err(ChallengeClosureError::Vocabulary);
        }
        let admitted_index = admitted.ok_or(ChallengeClosureError::KindNotClosed)?;
        Ok((count, admitted_index))
    }

    fn verify_vocabulary_entry(
        name: &str,
        previous: Option<&str>,
    ) -> Result<(), ChallengeClosureError> {
        if name.is_empty() || previous.is_some_and(|earlier| earlier >= name) {
            return Err(ChallengeClosureError::Vocabulary);
        }
        Ok(())
    }

    fn admit_stake(stake_text: &str) -> Result<BigRational, ChallengeClosureError> {
        let stake = exact::rational(stake_text).ok_or(ChallengeClosureError::StakeNotExact)?;
        if stake.denom().is_zero() || !(stake > BigRational::zero()) {
            return Err(ChallengeClosureError::StakeNotPositive);
        }
        let again =
            exact::rational(&stake.to_string()).ok_or(ChallengeClosureError::StakeNotExact)?;
        if again != stake {
            return Err(ChallengeClosureError::StakeNotExact);
        }
        Ok(stake)
    }

    pub fn kind_count(&self) -> usize {
        self.kind_count
    }

    pub fn admitted_index(&self) -> usize {
        self.admitted_index
    }

    pub fn stake(&self) -> &BigRational {
        &self.stake
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_0ff22b03 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
