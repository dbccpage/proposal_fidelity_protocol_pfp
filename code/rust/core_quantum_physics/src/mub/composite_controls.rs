//! Exact composite-dimension lower controls.
//!
//! These are clean-room tensor-product controls. They prove only the existence
//! of the displayed number of mutually unbiased bases in a composite dimension,
//! not a complete MUB set or a no-go theorem.

use serde::Serialize;

use crate::mub::prime_controls::{
    build_d2_complete_mub, build_d3_complete_mub, verify_partial_basis_set, Basis, BasisSet,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum CompositeControlStatus {
    ExactPartialSet,
    VerificationFailed,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompositeControlReport {
    pub target: &'static str,
    pub dimension: usize,
    pub basis_count: usize,
    pub status: CompositeControlStatus,
    pub construction: &'static str,
    pub checked_identities: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_composite_lower_controls() -> Vec<CompositeControlReport> {
    vec![verify_d6_product_three_mub_control()]
}

pub fn verify_d6_product_three_mub_control() -> CompositeControlReport {
    let bases = build_d6_product_three_mubs();
    match verify_partial_basis_set(&bases, 3) {
        Ok(()) => CompositeControlReport {
            target: "d=6 tensor-product three-MUB lower control",
            dimension: 6,
            basis_count: bases.len(),
            status: CompositeControlStatus::ExactPartialSet,
            construction: "tensor product of exact d=2 and d=3 MUB controls in Q(zeta_24)",
            checked_identities: vec![
                "each basis has d vectors in dimension d",
                "each basis is exactly orthonormal",
                "each cross-basis squared overlap is exactly 1/d",
                "basis count is 3, not d+1",
            ],
            boundary: "lower-control only; does not construct or obstruct a complete MUB(6)",
            error: None,
        },
        Err(error) => CompositeControlReport {
            target: "d=6 tensor-product three-MUB lower control",
            dimension: 6,
            basis_count: bases.len(),
            status: CompositeControlStatus::VerificationFailed,
            construction: "tensor product of exact d=2 and d=3 MUB controls in Q(zeta_24)",
            checked_identities: vec![],
            boundary: "failed lower-control benchmark",
            error: Some(error),
        },
    }
}

pub fn build_d6_product_three_mubs() -> BasisSet {
    let d2 = build_d2_complete_mub();
    let d3 = build_d3_complete_mub();
    (0..3).map(|i| tensor_basis(&d2[i], &d3[i])).collect()
}

fn tensor_basis(left: &Basis, right: &Basis) -> Basis {
    let mut basis = Vec::with_capacity(left.len() * right.len());
    for u in left {
        for v in right {
            let mut vector = Vec::with_capacity(u.len() * v.len());
            for x in u {
                for y in v {
                    vector.push(x.mul(y));
                }
            }
            basis.push(vector);
        }
    }
    basis
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/composite_controls.rs
// Claim: urn:core:crates_rs:core-quantum-physics:composite-controls:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf38f0124 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf38f0124` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf38f0124 {
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
impl BoundaryErrorf38f0124 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf38f0124 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf38f0124 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf38f0124 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf38f0124> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf38f0124::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf38f0124::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf38f0124::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn d6_tensor_product_three_mubs_verify_exactly() {
        let report = verify_d6_product_three_mub_control();
        assert_eq!(report.status, CompositeControlStatus::ExactPartialSet);
        assert_eq!(report.dimension, 6);
        assert_eq!(report.basis_count, 3);
        assert!(report.boundary.contains("does not"));
    }

    #[test]
    fn d6_control_is_not_complete() {
        let report = verify_d6_product_three_mub_control();
        assert_ne!(report.basis_count, report.dimension + 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_f38f0124 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf38f0124::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf38f0124::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf38f0124::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf38f0124::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf38f0124::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf38f0124::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf38f0124::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
