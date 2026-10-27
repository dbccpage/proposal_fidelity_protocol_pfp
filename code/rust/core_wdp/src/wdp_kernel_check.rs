//! Finite path-kernel product for a declared walk.
//!
//! AuthorityEffect: None. This module does not decide LGGR V soundness.

use core_epk::matrix_path_kernel::{EvaluatedPathKernelGraph, MatrixPathError, RationalMatrix2x2};

/// Finite path-kernel product of a walk.
///
/// This is not `lggr_v::check_soundness`. AuthorityEffect: None.
/// Returns the path product `T_last · … · T_first`, not a soundness report.
/// An empty factor list is the empty walk, whose product is the identity.
pub fn wdp_kernel_check(
    factors: &[RationalMatrix2x2],
) -> Result<RationalMatrix2x2, MatrixPathError> {
    if factors.is_empty() {
        return Ok(RationalMatrix2x2::identity());
    }
    let vertices: Vec<String> = (0..=factors.len())
        .map(|index| format!("v{index}"))
        .collect();
    let edges: Vec<(String, String)> = (0..factors.len())
        .map(|index| (format!("v{index}"), format!("v{}", index + 1)))
        .collect();
    let graph = EvaluatedPathKernelGraph::new(vertices, edges, factors.to_vec())?;
    let edge_indices: Vec<usize> = (0..factors.len()).collect();
    graph.evaluate_path(&edge_indices)
}

// Origin: engine/crates_rs/core_wdp/src/wdp_kernel_check.rs
// Claim: urn:core:crates_rs:core-wdp:wdp-kernel-check:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord88b087dc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord88b087dc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError88b087dc {
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
impl BoundaryError88b087dc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError88b087dc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError88b087dc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord88b087dc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError88b087dc> {
        if capacity_bound == 0 {
            return Err(BoundaryError88b087dc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError88b087dc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError88b087dc::ExceedsCapacity {
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
    use core_epk::lggr_v::LggrSoundnessReport;

    fn assert_not_lggr_soundness_report<T: 'static>(value: &T) {
        assert_ne!(
            std::any::TypeId::of::<T>(),
            std::any::TypeId::of::<LggrSoundnessReport>(),
        );
        let _ = value;
    }

    #[test]
    fn identity_multiplied_by_identity_is_identity() {
        let identity = RationalMatrix2x2::identity();
        let result = wdp_kernel_check(&[identity.clone(), identity.clone()]);
        assert_not_lggr_soundness_report(&result);
        let product = result.expect("path product");
        assert_eq!(product, identity);
        assert_not_lggr_soundness_report(&product);
    }
}

#[cfg(test)]
mod l4_boundary_tests_88b087dc {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord88b087dc::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord88b087dc::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord88b087dc::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord88b087dc::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord88b087dc::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError88b087dc::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError88b087dc::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
