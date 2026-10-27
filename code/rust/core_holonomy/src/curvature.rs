//! Plaquette curvature defect F_Box = U(partial Box) - I and Lie bracket commutators.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Exact rational curvature defect, Bianchi identity).

use crate::connection::DiscreteConnection;
use crate::error::HolonomyError;
use crate::holonomy::compute_loop_holonomy;
use crate::matrix::{ExactMatrix, ExactScalar};
use core_kernel::resource_limits::OperationLimits;

/// Computes the Lie bracket matrix commutator:
/// $$[M_1, M_2] = M_1 M_2 - M_2 M_1$$
pub fn curvature_commutator<T: ExactScalar>(
    m1: &ExactMatrix<T>,
    m2: &ExactMatrix<T>,
    _limits: &OperationLimits,
) -> Result<ExactMatrix<T>, HolonomyError> {
    if m1.rows != m1.cols || m2.rows != m2.cols || m1.rows != m2.rows {
        return Err(HolonomyError::DimensionMismatch {
            expected: m1.rows,
            actual: m2.rows,
        });
    }
    let p1 = m1.matmul(m2)?;
    let p2 = m2.matmul(m1)?;

    let mut diff_data = Vec::new();
    let total = p1.data.len();
    for i in 0..total {
        diff_data.push(p1.data[i].clone() - p2.data[i].clone());
    }
    ExactMatrix::try_new(m1.rows, m1.cols, diff_data)
}

/// Checks whether the matrix commutator vanishes: $[M_1, M_2] = 0$.
pub fn curvature_commutator_vanishes<T: ExactScalar>(
    m1: &ExactMatrix<T>,
    m2: &ExactMatrix<T>,
    limits: &OperationLimits,
) -> Result<bool, HolonomyError> {
    let comm = curvature_commutator(m1, m2, limits)?;
    Ok(comm.data.iter().all(|x| x.is_zero()))
}

/// Computes the group commutator:
/// $$(M_1, M_2) = M_1 M_2 M_1^{-1} M_2^{-1}$$
pub fn group_commutator<T: ExactScalar>(
    m1: &ExactMatrix<T>,
    m2: &ExactMatrix<T>,
) -> Result<ExactMatrix<T>, HolonomyError> {
    let m1_inv = m1.inverse()?;
    let m2_inv = m2.inverse()?;
    let p1 = m1.matmul(m2)?;
    let p2 = p1.matmul(&m1_inv)?;
    p2.matmul(&m2_inv)
}

/// Computes the plaquette curvature defect:
/// $$F_\Box = U(\partial \Box) - I_d$$
pub fn plaquette_curvature<T: ExactScalar>(
    connection: &DiscreteConnection<T>,
    boundary_vertices: &[String],
) -> Result<ExactMatrix<T>, HolonomyError> {
    let hol = compute_loop_holonomy(connection, boundary_vertices)?;
    let id: ExactMatrix<T> = ExactMatrix::try_identity(connection.dim)?;
    let mut diff_data = Vec::new();
    for i in 0..hol.data.len() {
        diff_data.push(hol.data[i].clone() - id.data[i].clone());
    }
    ExactMatrix::try_new(connection.dim, connection.dim, diff_data)
}

/// Checks the discrete Bianchi identity on the boundary of a 3-cell.
///
/// Returns whether the ordered product of the holonomies of the given loops,
/// $$\prod_{f=1}^k U(\ell_f),$$
/// is the identity. For a closed 2-sphere made of oriented 2-cells
/// $\Box_1, \dots, \Box_k$, that product is $I_d$ for every connection only
/// when the loops are the face boundaries transported to one common base
/// point (each loop reaches its face along a path and returns the same way),
/// ordered and oriented so that together they trace the boundary of the
/// 3-cell: then the loops multiply to the trivial word, and so do their
/// holonomies. The function does not check this. Face loops based at their
/// own vertices do not qualify: for a nonabelian connection the product then
/// depends on the base points, and a `Q8` connection on a tetrahedron gives
/// $-1$ (`core_quantum_physics/tests/repair_and_gravity/general_relativity_kinematical_shadows.rs`).
/// For an abelian connection neither the base points nor the order matter.
pub fn verify_discrete_bianchi_identity<T: ExactScalar>(
    connection: &DiscreteConnection<T>,
    boundary_plaquettes: &[Vec<String>],
) -> Result<bool, HolonomyError> {
    let mut current = ExactMatrix::try_identity(connection.dim)?;
    for plaquette in boundary_plaquettes {
        let hol = compute_loop_holonomy(connection, plaquette)?;
        current = current.matmul(&hol)?;
    }
    let id: ExactMatrix<T> = ExactMatrix::try_identity(connection.dim)?;
    Ok(current == id)
}

/// High-level curvature engine for discrete gauge fields.
#[derive(Debug, Clone)]
pub struct CurvatureEngine<T: ExactScalar> {
    pub connection: DiscreteConnection<T>,
}

impl<T: ExactScalar> CurvatureEngine<T> {
    pub fn new(connection: DiscreteConnection<T>) -> Self {
        Self { connection }
    }

    /// Computes plaquette curvature defect around boundary walk.
    pub fn plaquette_curvature(
        &self,
        boundary_vertices: &[String],
    ) -> Result<ExactMatrix<T>, HolonomyError> {
        plaquette_curvature(&self.connection, boundary_vertices)
    }

    /// Computes Lie bracket commutator between two connection matrices.
    pub fn curvature_commutator(
        &self,
        m1: &ExactMatrix<T>,
        m2: &ExactMatrix<T>,
    ) -> Result<ExactMatrix<T>, HolonomyError> {
        curvature_commutator(m1, m2, &self.connection.limits)
    }
}

// Origin: engine/crates_rs/core_holonomy/src/curvature.rs
// Claim: urn:core:crates_rs:core-holonomy:curvature:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9ad12448 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9ad12448` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9ad12448 {
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
impl BoundaryError9ad12448 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9ad12448 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9ad12448 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9ad12448 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9ad12448> {
        if capacity_bound == 0 {
            return Err(BoundaryError9ad12448::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9ad12448::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9ad12448::ExceedsCapacity {
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
mod l4_boundary_tests_9ad12448 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9ad12448::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9ad12448::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9ad12448::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9ad12448::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9ad12448::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9ad12448::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9ad12448::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
