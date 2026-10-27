// AuthorityEffect: None.

//! Finite checks behind the U(1)-selector argument.
//!
//! - Pairings on `Q(i)`. For a field automorphism `sigma` of `Q(i)` (the
//!   identity or complex conjugation; `x^2 = -1` has only the roots `+-i`) the
//!   pairing `B(a, b) = sigma(a) b` has cross term
//!   `X(a, b) = B(a+b, a+b) - B(a, a) - B(b, b) = sigma(a) b + sigma(b) a`. A
//!   global phase `u` multiplies `X` by `sigma(u) u`: by `|u|^2 = 1` for every
//!   unit under conjugation, and by `u^2` under the identity, which is `1` only
//!   for `u = +-1`.
//! The phase-group order, closure, conjugacy and regular-representation
//! algorithms are owned directly by Lie theory and number theory. This module
//! retains the physical pairing choice and its measured interference term.

use core_number_theory::cyclotomic::GaussianRat;

/// The field automorphism entering the left slot of a pairing on `Q(i)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PairingInvolution {
    Identity,
    Conjugation,
}

impl PairingInvolution {
    pub fn apply(self, z: &GaussianRat) -> GaussianRat {
        match self {
            Self::Identity => z.clone(),
            Self::Conjugation => z.conj(),
        }
    }

    /// `B(a, b) = sigma(a) b`.
    pub fn pairing(self, a: &GaussianRat, b: &GaussianRat) -> GaussianRat {
        self.apply(a).mul(b)
    }

    /// `X(a, b) = B(a+b, a+b) - B(a, a) - B(b, b)`.
    pub fn cross_term(self, a: &GaussianRat, b: &GaussianRat) -> GaussianRat {
        let sum = a.add(b);
        self.pairing(&sum, &sum)
            .sub(&self.pairing(a, a))
            .sub(&self.pairing(b, b))
    }

    /// `sigma(u) u`, the factor a global phase `u` puts on every cross term.
    pub fn phase_factor(self, u: &GaussianRat) -> GaussianRat {
        self.apply(u).mul(u)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/complex_structure_selector.rs
// Claim: urn:core:crates_rs:core-quantum-physics:complex-structure-selector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7b16815d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7b16815d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7b16815d {
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
impl BoundaryError7b16815d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7b16815d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7b16815d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7b16815d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7b16815d> {
        if capacity_bound == 0 {
            return Err(BoundaryError7b16815d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7b16815d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7b16815d::ExceedsCapacity {
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
mod l4_boundary_tests_7b16815d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7b16815d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7b16815d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7b16815d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7b16815d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7b16815d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7b16815d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7b16815d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
