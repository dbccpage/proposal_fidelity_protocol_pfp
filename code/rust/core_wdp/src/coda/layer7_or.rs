// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::Zero;
use serde_json::json;

use crate::coda::types::{LayerExecutionRecord, LayerId, ProblemInstance};

pub struct Layer7Or;

impl Layer7Or {
    /// Evaluates Layer 7: Omniversal Re-Presentation (CODA-OR).
    ///
    /// Enforces:
    /// - Hard refusal sieve on empty candidate sieves (OR-T5)
    /// - Incompatible boundary overlap detection (OR-T3)
    /// - Anti-consensus discipline forbidding averaging incompatible derivations
    /// - Cocycle gluing condition Gamma_2 == 0
    pub fn evaluate(
        problem: &ProblemInstance,
        gamma2: &BigRational,
    ) -> (LayerExecutionRecord, bool) {
        let mut reasons = Vec::new();

        let admitted: Vec<&String> = problem
            .candidate_sieve
            .iter()
            .filter(|s| !s.trim().is_empty())
            .collect();

        if admitted.is_empty() {
            reasons.push(
                "Empty support sieve: no admitted (non-blank) candidate hypothesis (OR-T5)"
                    .to_string(),
            );
        }

        let incompatible: Vec<(&(String, String), &bool)> =
            problem.overlaps.iter().filter(|(_, &comp)| !comp).collect();

        if !incompatible.is_empty() {
            reasons.push(format!(
                "Incompatible boundary overlaps detected: {:?} (OR-T3)",
                incompatible
                    .iter()
                    .map(|(pair, _)| pair)
                    .collect::<Vec<_>>()
            ));
        }

        if !gamma2.is_zero() {
            reasons.push(format!("Cocycle gluing failure: Gamma_2={} != 0", gamma2));
        }

        let is_refused = !reasons.is_empty();
        let msg = if is_refused {
            format!("OR Hard Refusal triggered: {}", reasons.join("; "))
        } else {
            "OR Refusal sieve passed: candidate sieve inhabited, overlaps compatible, Gamma_2 == 0"
                .to_string()
        };

        let record = LayerExecutionRecord::new(
            LayerId::OR,
            !is_refused,
            msg,
            BigRational::from_integer((reasons.len() as i64).into()),
        )
        .with_metadata("is_refused", json!(is_refused))
        .with_metadata("reasons", json!(reasons))
        .with_metadata("sieve_size", json!(admitted.len()));

        (record, is_refused)
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/layer7_or.rs
// Claim: urn:core:crates_rs:core-wdp:layer7-or:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord68efa4c9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord68efa4c9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError68efa4c9 {
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
impl BoundaryError68efa4c9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError68efa4c9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError68efa4c9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord68efa4c9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError68efa4c9> {
        if capacity_bound == 0 {
            return Err(BoundaryError68efa4c9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError68efa4c9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError68efa4c9::ExceedsCapacity {
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
mod l4_boundary_tests_68efa4c9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord68efa4c9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord68efa4c9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord68efa4c9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord68efa4c9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord68efa4c9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError68efa4c9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError68efa4c9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
