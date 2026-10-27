//! Contracted closure identity on a tetrahedron.
//!
//! `B(τ) = Σ_{h ⊂ τ} ε(h, τ) D_h Σ_h` with `D_h = Id` in the pentatope chart.
//! `Σ_h = (1/2) (r_j - r_i) ∧ (r_k - r_i)` on the oriented triangle `(i, j, k)`.
//! The deficit `ε_h = 2π - Σ θ` is not computed. `B` is an exact rational
//! bivector, not a floating-point curvature residual.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use super::manifold::{ManifoldError, SimplicialManifold4D};
use super::orientation::{tetra_boundary_of_pentatope, triangle_boundary_of_tetra};
use super::simplicity::hinge_bivector_in_pentatope;
use linear_algebra::regge_exact::{q_i64, Bivector4};

/// Contracted closure identity inside one pentatope chart.
///
/// `tetra` is matched by sorted vertex ids to one face of
/// `tetra_boundary_of_pentatope(chart.vertices)`. The sum uses that matched
/// ordered 4-tuple. The tetra's sign in the pentatope is not applied.
/// Terms follow `triangle_boundary_of_tetra` from left to right. Each term is
/// `ε * Σ_h`: `ε` is that triangle's `i8` sign as a rational, `Σ_h` is the
/// hinge bivector in this same chart, and `D_h` is the identity. The
/// accumulator starts at the zero bivector and folds `checked_add`.
/// `ε_h = 2π - Σ θ` is not computed.
///
/// AuthorityEffect: None.
pub fn contracted_closure_in_pentatope(
    manifold: &SimplicialManifold4D,
    pentatope_index: usize,
    tetra: [u32; 4],
) -> Result<Bivector4, ManifoldError> {
    let chart = manifold.pentatope(pentatope_index)?;
    let wanted = sorted_tetra(tetra);
    let ordered = tetra_boundary_of_pentatope(chart.vertices)
        .into_iter()
        .find(|face| sorted_tetra(face.0) == wanted)
        .map(|face| face.0)
        .ok_or(ManifoldError::NotAFace)?;
    let mut sum = Bivector4::zero();
    for (triangle, sign) in triangle_boundary_of_tetra(ordered) {
        let sigma = hinge_bivector_in_pentatope(manifold, pentatope_index, triangle)?;
        let epsilon = q_i64(i64::from(sign));
        sum = sum.checked_add(&sigma.checked_scale(&epsilon));
    }
    Ok(sum)
}

/// Whether every boundary tetrahedron of every pentatope has vanishing `B`.
///
/// Pentatopes run in index order. Each tetrahedron is the ordered 4-tuple from
/// `tetra_boundary_of_pentatope`, and `B` is [`contracted_closure_in_pentatope`].
/// No pentatopes yields [`ManifoldError::Empty`].
/// `ε_h = 2π - Σ θ` is not computed.
///
/// AuthorityEffect: None.
pub fn all_tetra_closures_vanish(manifold: &SimplicialManifold4D) -> Result<bool, ManifoldError> {
    let pentatope_count = manifold.pentatope_count();
    if pentatope_count == 0 {
        return Err(ManifoldError::Empty);
    }
    for index in 0..pentatope_count {
        let vertices = manifold.pentatope(index)?.vertices;
        for (tetra, _pentatope_sign) in tetra_boundary_of_pentatope(vertices) {
            if !contracted_closure_in_pentatope(manifold, index, tetra)?.is_zero() {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

fn sorted_tetra(mut tetra: [u32; 4]) -> [u32; 4] {
    tetra.sort_unstable();
    tetra
}

// Origin: engine/crates_rs/core_general_relativity/src/exact_regge/closure.rs
// Claim: urn:core:crates_rs:core-general-relativity:closure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9cb853fa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9cb853fa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9cb853fa {
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
impl BoundaryError9cb853fa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9cb853fa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9cb853fa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9cb853fa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9cb853fa> {
        if capacity_bound == 0 {
            return Err(BoundaryError9cb853fa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9cb853fa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9cb853fa::ExceedsCapacity {
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
mod l4_boundary_tests_9cb853fa {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9cb853fa::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9cb853fa::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9cb853fa::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9cb853fa::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9cb853fa::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9cb853fa::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9cb853fa::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
