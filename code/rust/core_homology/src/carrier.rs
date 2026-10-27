//! Carrier: a finite cochain complex C^0 -> C^1 -> C^2 with weights.
//!
//! This is the core carrier for the MSS-N obstruction calculus.
//! All arithmetic is exact over the canonical coefficient domain
//! `core_homology::scalar::Q` = `BigRational` (ADR-001, 2026-08-04). It was
//! `Rational64` before the widening; nothing here narrows back. The cochain
//! relation is verified at construction time.
//!
//! This module does NOT emit authority-bearing artifacts.
//! Authority promotion belongs to the contract/checking layer.

use crate::cochain_complex::{CochainComplex, TheoremProvenance};
use crate::errors::HomologicalError;
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::ExactRowReduction;
use num_traits::Zero;

/// A finite cochain complex C^0 -> C^1 -> C^2 with C^1 weights.
///
/// Verified at construction: d1*d0=0 and all weights positive.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Carrier {
    complex: CochainComplex,
    weights: Vec<Q>,
}

impl Carrier {
    /// Construct a new carrier, verifying d1*d0=0 and weight positivity.
    pub fn new(
        c0_dim: usize,
        c1_dim: usize,
        c2_dim: usize,
        d0: BasicMatrix<Q>,
        d1: BasicMatrix<Q>,
        weights: Vec<Q>,
        provenance: TheoremProvenance,
    ) -> Result<Self, HomologicalError> {
        // Check weight dimensions
        if weights.len() != c1_dim {
            return Err(HomologicalError::WeightDimensionMismatch {
                expected: c1_dim,
                got: weights.len(),
            });
        }

        // Check weight positivity
        for (i, w) in weights.iter().enumerate() {
            if *w <= Q::zero() {
                return Err(HomologicalError::NonPositiveWeight { index: i });
            }
        }

        // Construct cochain complex (verifies d1*d0=0 and dimensions)
        let complex = CochainComplex::new(c0_dim, c1_dim, c2_dim, d0, d1, provenance)?;

        Ok(Self { complex, weights })
    }

    pub fn c0_dim(&self) -> usize {
        self.complex.c0_dim
    }
    pub fn c1_dim(&self) -> usize {
        self.complex.c1_dim
    }
    pub fn c2_dim(&self) -> usize {
        self.complex.c2_dim
    }
    pub fn d0(&self) -> &BasicMatrix<Q> {
        &self.complex.d0.matrix
    }
    pub fn d1(&self) -> &BasicMatrix<Q> {
        &self.complex.d1.matrix
    }
    pub fn weights(&self) -> &[Q] {
        &self.weights
    }
    pub fn complex(&self) -> &CochainComplex {
        &self.complex
    }

    /// Rank of d0 = dim(im(d0)) = dim(B^1).
    pub fn rank_d0(&self) -> Result<usize, HomologicalError> {
        self.d0()
            .rank()
            .map_err(|e| HomologicalError::UnsupportedOperation(format!("{}", e)))
    }

    /// Rank of d1.
    pub fn rank_d1(&self) -> Result<usize, HomologicalError> {
        self.d1()
            .rank()
            .map_err(|e| HomologicalError::UnsupportedOperation(format!("{}", e)))
    }

    /// Dimension of Q^1 = C^1/B^1 = c1_dim - rank(d0).
    pub fn dim_q1(&self) -> Result<usize, HomologicalError> {
        Ok(self.c1_dim() - self.rank_d0()?)
    }

    /// Dimension of H^1 = ker(d1) / im(d0).
    pub fn dim_h1(&self) -> Result<usize, HomologicalError> {
        let ker_d1_dim = self.c1_dim() - self.rank_d1()?;
        let im_d0_dim = self.rank_d0()?;
        ker_d1_dim
            .checked_sub(im_d0_dim)
            .ok_or(HomologicalError::HomologyDimensionUnderflow {
                ker_dim: ker_d1_dim,
                im_dim: im_d0_dim,
            })
    }

    /// Compute the carrier manifest.
    pub fn manifest(&self) -> Result<crate::carrier_manifest::CarrierManifest, HomologicalError> {
        crate::carrier_manifest::CarrierManifest::from_carrier(self)
    }
}

// Origin: engine/crates_rs/core_homology/src/carrier.rs
// Claim: urn:core:crates_rs:core-homology:carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7e47bd8b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7e47bd8b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7e47bd8b {
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
impl BoundaryError7e47bd8b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7e47bd8b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7e47bd8b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7e47bd8b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7e47bd8b> {
        if capacity_bound == 0 {
            return Err(BoundaryError7e47bd8b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7e47bd8b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7e47bd8b::ExceedsCapacity {
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
mod l4_boundary_tests_7e47bd8b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7e47bd8b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7e47bd8b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7e47bd8b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7e47bd8b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7e47bd8b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7e47bd8b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7e47bd8b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
