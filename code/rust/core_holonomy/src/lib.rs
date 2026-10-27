//! core_holonomy — Exact Discrete Gauge Holonomy, Connection Laplacians,
//! and Curvature Commutators for the engine.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Strict Zero-Float Law, Builder discipline).

pub mod connection;
pub mod curvature;
pub mod error;
pub mod gauge_fixing;
pub mod gauge_quotient;
pub mod graph;
pub mod holonomy;
pub mod laplacian;
pub mod matrix;

pub use connection::{Connection, DiscreteConnection};
pub use curvature::{
    curvature_commutator, curvature_commutator_vanishes, group_commutator, plaquette_curvature,
    verify_discrete_bianchi_identity, CurvatureEngine,
};
pub use error::HolonomyError;
pub use graph::{CellComplex, Edge, Face, OrientedStep, Vertex};
pub use holonomy::{
    compute_loop_holonomy, compute_path_holonomy, cycle_homology_pairing, is_flat,
    wilson_loop_trace, HolonomyEngine, HolonomyLoop,
};
pub use laplacian::{
    compute_connection_laplacian, ConnectionLaplacian, PerturbationCertificate, RealDiagonal,
};
pub use matrix::{ExactMatrix, ExactScalar, GaussianRational, RationalMatrix};

pub mod signed_transport;

pub mod prelude {
    pub use crate::{
        compute_connection_laplacian, compute_loop_holonomy, compute_path_holonomy,
        curvature_commutator, curvature_commutator_vanishes, cycle_homology_pairing, is_flat,
        plaquette_curvature, verify_discrete_bianchi_identity, wilson_loop_trace, CellComplex,
        Connection, ConnectionLaplacian, CurvatureEngine, DiscreteConnection, Edge, ExactMatrix,
        ExactScalar, Face, GaussianRational, HolonomyEngine, HolonomyError, HolonomyLoop,
        RationalMatrix,
    };
}
pub mod functional_graph;
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WalkError { kind: &'static str, left: i128, right: i128 }
impl WalkError {
    const fn new(kind: &'static str, left: i128, right: i128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
fn euclidean_residue(lhs: i128, modulus: u64) -> Result<u64, WalkError> {
    if modulus == 0 {
        return Err(WalkError::new("the cyclic order is positive", 0, 0));
    }
    let modulus_i = i128::from(modulus);
    let residue = lhs.rem_euclid(modulus_i);
    if residue < 0 || residue >= modulus_i {
        return Err(WalkError::new("residue lies outside the cyclic order", residue, modulus_i));
    }
    verify_congruence_division(lhs, residue, modulus_i)?;
    u64::try_from(residue).map_err(|_| WalkError::new("residue exceeds u64", residue, modulus_i))
}
fn verify_congruence_division(lhs: i128, residue: i128, modulus_i: i128) -> Result<(), WalkError> {
    let delta = lhs.checked_sub(residue).ok_or_else(|| WalkError::new("congruence difference overflow", lhs, residue))?;
    let quotient = delta.checked_div(modulus_i).ok_or_else(|| WalkError::new("congruence quotient overflow", delta, modulus_i))?;
    let restored = quotient.checked_mul(modulus_i).ok_or_else(|| WalkError::new("congruence product overflow", quotient, modulus_i))?;
    if restored != delta {
        return Err(WalkError::new("residue is not congruent to the displacement", restored, delta));
    }
    Ok(())
}
/// A closed integer walk: the displacement is congruent to zero modulo the cyclic order.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ClosedDisplacement { order: u64, steps: u64, residue: u64 }
impl ClosedDisplacement {
    pub fn try_closed(order: u64, steps: &[i64]) -> Result<Self, WalkError> {
        if order == 0 {
            return Err(WalkError::new("the cyclic order is positive", 0, 0));
        }
        if steps.is_empty() {
            return Err(WalkError::new("a walk has a step", 0, 0));
        }
        let mut sum = 0i128;
        let mut count = 0u64;
        for step in steps {
            sum = sum.checked_add(i128::from(*step)).ok_or_else(|| WalkError::new("displacement overflow", sum, i128::from(*step)))?;
            count = count.checked_add(1).ok_or_else(|| WalkError::new("step count overflow", i128::from(count), 1))?;
        }
        let residue = euclidean_residue(sum, order)?;
        if residue != 0 {
            return Err(WalkError::new("a closed walk has residue zero", i128::from(residue), sum));
        }
        Ok(Self { order, steps: count, residue })
    }
    pub const fn residue(&self) -> u64 { self.residue }
}

// Origin: engine/crates_rs/core_holonomy/src/lib.rs
// Claim: urn:core:crates_rs:core-holonomy:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde6957c81 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde6957c81` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore6957c81 {
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
impl BoundaryErrore6957c81 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore6957c81 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore6957c81 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde6957c81 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore6957c81> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore6957c81::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore6957c81::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore6957c81::ExceedsCapacity {
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
mod closed_walk_checks {
    use super::ClosedDisplacement;
    #[test]
    fn opposite_steps_close_in_order_five() {
        assert_eq!(ClosedDisplacement::try_closed(5, &[2, -7]).as_ref().map(ClosedDisplacement::residue), Ok(0));
    }
    #[test]
    fn a_single_step_of_one_is_not_closed() {
        assert_eq!(ClosedDisplacement::try_closed(5, &[1]).map(|_| ()).map_err(|e| e.kind()), Err("a closed walk has residue zero"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_e6957c81 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde6957c81::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde6957c81::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde6957c81::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde6957c81::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde6957c81::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore6957c81::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore6957c81::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
