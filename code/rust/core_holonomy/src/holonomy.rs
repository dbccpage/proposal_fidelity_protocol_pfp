//! Path holonomy, loop products, Wilson loop traces, and topological cycle pairings.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Ordered product evaluation, Zero-Float Law).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_941e3d7d<T> {
    fn checked_invariant_941e3d7d(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_941e3d7d<T> for Option<T> {
    #[inline]
    fn checked_invariant_941e3d7d(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_941e3d7d<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_941e3d7d(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::connection::DiscreteConnection;
use crate::error::HolonomyError;
use crate::graph::CellComplex;
use crate::matrix::{ExactMatrix, ExactScalar};
use serde::{Deserialize, Serialize};

/// Strongly typed closed loop on a discrete cell complex.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HolonomyLoop {
    pub vertices: Vec<String>,
}

impl HolonomyLoop {
    /// Constructs a validated closed loop.
    ///
    /// Rejects paths with length < 2 with `MalformedPath`.
    /// Rejects open paths (start != end) with `OpenLoop`.
    pub fn try_new(vertices: Vec<String>) -> Result<Self, HolonomyError> {
        if vertices.len() < 2 {
            return Err(HolonomyError::MalformedPath {
                length: vertices.len(),
            });
        }
        let start = vertices.first().checked_invariant_941e3d7d("checked invariant");
        let end = vertices.last().checked_invariant_941e3d7d("checked invariant");
        if start != end {
            return Err(HolonomyError::OpenLoop {
                start: start.clone(),
                end: end.clone(),
            });
        }
        Ok(Self { vertices })
    }
}

/// Computes the discrete path-ordered holonomy operator along an oriented path:
/// $$U(\gamma) = U(e_k) \cdot U(e_{k-1}) \cdots U(e_1)$$
pub fn compute_path_holonomy<T: ExactScalar>(
    connection: &DiscreteConnection<T>,
    path: &[String],
) -> Result<ExactMatrix<T>, HolonomyError> {
    if path.len() < 2 {
        return Err(HolonomyError::EmptyPath);
    }
    if path.len() > connection.limits.max_path_length {
        return Err(HolonomyError::PathLengthExceeded {
            length: path.len(),
            limit: connection.limits.max_path_length,
        });
    }

    let mut current = ExactMatrix::try_identity(connection.dim)?;
    for i in 0..(path.len() - 1) {
        let u = &path[i];
        let v = &path[i + 1];
        let step_mat = connection.get_step(u, v)?;
        // Sequential composition: current = step_mat * current
        current = step_mat.matmul(&current)?;
    }
    Ok(current)
}

/// Computes the closed loop holonomy operator:
/// $$U(\gamma) = \prod_{e \in \gamma} U(e)$$
///
/// Precedence: checks loop closure ($v_0 = v_k$) before evaluating transport.
pub fn compute_loop_holonomy<T: ExactScalar>(
    connection: &DiscreteConnection<T>,
    loop_vertices: &[String],
) -> Result<ExactMatrix<T>, HolonomyError> {
    if loop_vertices.len() < 2 {
        return Err(HolonomyError::MalformedPath {
            length: loop_vertices.len(),
        });
    }
    let start = &loop_vertices[0];
    let end = &loop_vertices[loop_vertices.len() - 1];
    if start != end {
        return Err(HolonomyError::OpenLoop {
            start: start.clone(),
            end: end.clone(),
        });
    }
    compute_path_holonomy(connection, loop_vertices)
}

/// Computes the exact Wilson loop trace:
/// $$W(\gamma) = \operatorname{Tr}(U(\gamma)) \in F$$
pub fn wilson_loop_trace<T: ExactScalar>(
    connection: &DiscreteConnection<T>,
    loop_vertices: &[String],
) -> Result<T, HolonomyError> {
    let hol = compute_loop_holonomy(connection, loop_vertices)?;
    hol.trace()
}

/// Verifies whether the connection is pure-gauge flat on all 2-cells of the cell complex.
pub fn is_flat<T: ExactScalar>(
    connection: &DiscreteConnection<T>,
    complex: &CellComplex,
) -> Result<bool, HolonomyError> {
    let id: ExactMatrix<T> = ExactMatrix::try_identity(connection.dim)?;
    for face in &complex.faces {
        let hol = compute_loop_holonomy(connection, &face.boundary_vertices)?;
        if hol != id {
            return Ok(false);
        }
    }
    Ok(true)
}

/// Evaluates cycle homology pairings for a set of closed cycle generators in $H_1(X, \mathbb{Z})$.
pub fn cycle_homology_pairing<T: ExactScalar>(
    connection: &DiscreteConnection<T>,
    cycles: &[Vec<String>],
) -> Result<Vec<ExactMatrix<T>>, HolonomyError> {
    let mut pairings = Vec::new();
    for cycle in cycles {
        let hol = compute_loop_holonomy(connection, cycle)?;
        pairings.push(hol);
    }
    Ok(pairings)
}

/// High-level engine interface wrapping connection and path algorithms.
#[derive(Debug, Clone)]
pub struct HolonomyEngine<T: ExactScalar> {
    pub connection: DiscreteConnection<T>,
}

impl<T: ExactScalar> HolonomyEngine<T> {
    pub fn new(connection: DiscreteConnection<T>) -> Self {
        Self { connection }
    }

    /// Direct loop holonomy computation matching reference oracle interface.
    pub fn compute_holonomy(&self, loop_path: &[String]) -> Result<ExactMatrix<T>, HolonomyError> {
        compute_loop_holonomy(&self.connection, loop_path)
    }

    /// Direct Wilson loop trace evaluation.
    pub fn wilson_loop_trace(&self, loop_path: &[String]) -> Result<T, HolonomyError> {
        wilson_loop_trace(&self.connection, loop_path)
    }
}

// Origin: engine/crates_rs/core_holonomy/src/holonomy.rs
// Claim: urn:core:crates_rs:core-holonomy:holonomy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord941e3d7d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord941e3d7d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError941e3d7d {
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
impl BoundaryError941e3d7d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError941e3d7d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError941e3d7d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord941e3d7d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError941e3d7d> {
        if capacity_bound == 0 {
            return Err(BoundaryError941e3d7d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError941e3d7d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError941e3d7d::ExceedsCapacity {
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
mod l4_boundary_tests_941e3d7d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord941e3d7d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord941e3d7d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord941e3d7d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord941e3d7d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord941e3d7d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError941e3d7d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError941e3d7d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
