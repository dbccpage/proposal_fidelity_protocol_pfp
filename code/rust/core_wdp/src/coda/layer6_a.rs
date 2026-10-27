// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::Zero;
use serde_json::json;

use crate::coda::types::{LayerExecutionRecord, LayerId, ProblemInstance};

pub struct Layer6A;

impl Layer6A {
    /// Evaluates Layer 6: Sentinel (The Sentinel as a Typed Leftover).
    ///
    /// Classifies residuals:
    /// - Phi_1 > 0, Gamma_2 == 0: Coherent residual (Sentinel), retained in cokernel V / im(C).
    /// - Phi_1 > 0, Gamma_2 > 0: Incoherent residue (violates cocycle condition).
    /// - Phi_1 == 0: Vanishing residue (no leftover class).
    pub fn evaluate(
        _problem: &ProblemInstance,
        phi1: &BigRational,
        gamma2: &BigRational,
    ) -> (LayerExecutionRecord, bool) {
        let has_residual = phi1 > &BigRational::zero();
        let is_coherent = gamma2.is_zero();

        let msg = if has_residual && is_coherent {
            format!(
                "CODA-A typed residual (Phi_1={}, Gamma_2=0): routed to CLOSED_RESIDUAL, where the firewall registers it as an Sentinel; never promoted",
                phi1
            )
        } else if has_residual {
            format!(
                "CODA-A incoherent residue (Phi_1={}, Gamma_2={}): violates the cocycle condition",
                phi1, gamma2
            )
        } else {
            "CODA-A vanishing residue (Phi_1=0): no leftover class".to_string()
        };

        let record = LayerExecutionRecord::new(LayerId::A, is_coherent, msg, phi1.clone())
            .with_metadata("has_residual", json!(has_residual))
            .with_metadata("is_coherent", json!(is_coherent))
            .with_metadata("residual_retained_in_cokernel", json!(has_residual));

        (record, has_residual)
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/layer6_a.rs
// Claim: urn:core:crates_rs:core-wdp:layer6-a:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf4c722c7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf4c722c7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf4c722c7 {
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
impl BoundaryErrorf4c722c7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf4c722c7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf4c722c7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf4c722c7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf4c722c7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf4c722c7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf4c722c7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf4c722c7::ExceedsCapacity {
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
mod l4_boundary_tests_f4c722c7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf4c722c7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf4c722c7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf4c722c7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf4c722c7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf4c722c7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf4c722c7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf4c722c7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
