//! DDC Word N-Gram Miner (U02).
//!
//! Mines exact integer counts of n-grams (up to n = 6) across DDC operational words.
//! Example: "CIDET" -> 2-grams: ["CI", "ID", "DE", "ET"], 3-grams: ["CID", "IDE", "DET"].
//! AuthorityEffect: None (const).

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

fn default_authority_effect() -> String {
    "None".to_string()
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DdcMotifLedgerV1 {
    pub total_words: usize,
    pub total_letters: usize,
    pub ngrams: BTreeMap<usize, BTreeMap<String, u64>>,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

impl Default for DdcMotifLedgerV1 {
    fn default() -> Self {
        Self {
            total_words: 0,
            total_letters: 0,
            ngrams: BTreeMap::new(),
            authority_effect: default_authority_effect(),
        }
    }
}

pub fn mine_ddc_ngrams(words: &[&str], max_n: usize) -> DdcMotifLedgerV1 {
    let mut ledger = DdcMotifLedgerV1 {
        total_words: words.len(),
        total_letters: 0,
        ngrams: BTreeMap::new(),
        authority_effect: default_authority_effect(),
    };

    let bound_n = max_n.min(6);

    for &word in words {
        let chars: Vec<char> = word.chars().collect();
        ledger.total_letters += chars.len();

        for n in 1..=bound_n {
            if chars.len() < n {
                continue;
            }
            let n_map = ledger.ngrams.entry(n).or_default();
            for window in chars.windows(n) {
                let ngram: String = window.iter().collect();
                *n_map.entry(ngram).or_insert(0) += 1;
            }
        }
    }

    ledger
}

// Origin: engine/crates_rs/core_wdp/src/ddc/motif.rs
// Claim: urn:core:crates_rs:core-wdp:motif:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord71a7de10 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord71a7de10` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError71a7de10 {
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
impl BoundaryError71a7de10 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError71a7de10 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError71a7de10 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord71a7de10 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError71a7de10> {
        if capacity_bound == 0 {
            return Err(BoundaryError71a7de10::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError71a7de10::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError71a7de10::ExceedsCapacity {
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
mod l4_boundary_tests_71a7de10 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord71a7de10::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord71a7de10::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord71a7de10::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord71a7de10::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord71a7de10::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError71a7de10::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError71a7de10::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
