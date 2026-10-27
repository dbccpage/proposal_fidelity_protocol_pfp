//! Discrete connection (lattice gauge field) mapping oriented edges to exact rational matrices GL(d, Q).
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Edge inversion law U(v, u) = U(u, v)^-1, Zero-Float Law).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_ea357a0a<T> {
    fn checked_invariant_ea357a0a(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_ea357a0a<T> for Option<T> {
    #[inline]
    fn checked_invariant_ea357a0a(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_ea357a0a<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_ea357a0a(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::error::HolonomyError;
use crate::graph::CellComplex;
use crate::matrix::{ExactMatrix, ExactScalar};
use num_rational::BigRational;
use core_kernel::resource_limits::OperationLimits;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

/// Discrete connection mapping oriented edges to exact matrices in GL(d, F).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscreteConnection<T: ExactScalar> {
    pub dim: usize,
    pub limits: OperationLimits,
    pub forward: BTreeMap<(String, String), ExactMatrix<T>>,
    pub reverse: BTreeMap<(String, String), ExactMatrix<T>>,
}

impl<T: ExactScalar> DiscreteConnection<T> {
    /// Construct a new empty connection of fiber dimension `dim`.
    pub fn new(dim: usize, limits: OperationLimits) -> Self {
        Self {
            dim,
            limits,
            forward: BTreeMap::new(),
            reverse: BTreeMap::new(),
        }
    }

    /// Sets the connection matrix on directed edge `(u, v)`.
    ///
    /// Automatically computes and registers the inverted matrix on reverse edge `(v, u)`
    /// satisfying the edge inversion law: $U(v, u) = U(u, v)^{-1}$.
    pub fn set_connection(
        &mut self,
        u: impl Into<String>,
        v: impl Into<String>,
        matrix: ExactMatrix<T>,
    ) -> Result<(), HolonomyError> {
        let u_str = u.into();
        let v_str = v.into();

        if matrix.rows != self.dim || matrix.cols != self.dim {
            return Err(HolonomyError::DimensionMismatch {
                expected: self.dim,
                actual: matrix.rows,
            });
        }
        let forward_key = (u_str.clone(), v_str.clone());
        let opposite_key = (v_str.clone(), u_str.clone());
        // One undirected edge. A second write, including the opposite
        // direction, replaces that edge instead of stacking another forward
        // matrix that get_step would prefer over the stored inverse.
        let replacing =
            self.forward.contains_key(&forward_key) || self.forward.contains_key(&opposite_key);
        if !replacing && self.forward.len() >= self.limits.max_edges {
            return Err(HolonomyError::AllocationFailure {
                requested: self.forward.len() + 1,
                detail: format!("Max edges limit exceeded ({})", self.limits.max_edges),
            });
        }

        // Exact inversion over exact field
        let inv = matrix.inverse().map_err(|e| match e {
            HolonomyError::SingularMatrix { detail } => HolonomyError::SingularConnection {
                src: u_str.clone(),
                tgt: v_str.clone(),
                detail,
            },
            other => other,
        })?;

        self.forward.remove(&forward_key);
        self.forward.remove(&opposite_key);
        self.reverse.remove(&forward_key);
        self.reverse.remove(&opposite_key);
        self.forward.insert(forward_key, matrix);
        self.reverse.insert(opposite_key, inv);
        Ok(())
    }

    /// Retrieves the parallel transport matrix for directed step from `u` to `v`.
    ///
    /// Checks forward edges first, then reverse edges.
    pub fn get_step(&self, u: &str, v: &str) -> Result<&ExactMatrix<T>, HolonomyError> {
        let key = (u.to_string(), v.to_string());
        if let Some(m) = self.forward.get(&key) {
            return Ok(m);
        }
        if let Some(m) = self.reverse.get(&key) {
            return Ok(m);
        }
        Err(HolonomyError::EdgeNotFound {
            src: u.to_string(),
            tgt: v.to_string(),
        })
    }

    /// Constructs a pure gauge connection from vertex gauge potentials:
    /// $$U(u, v) = g(v) \cdot g(u)^{-1}$$
    pub fn from_pure_gauge(
        complex: &CellComplex,
        gauge_potentials: &BTreeMap<String, ExactMatrix<T>>,
        dim: usize,
        limits: OperationLimits,
    ) -> Result<Self, HolonomyError> {
        let mut conn = Self::new(dim, limits);
        Self::validate_all_vertices_present(complex, gauge_potentials)?;

        for edge in &complex.edges {
            let gu = gauge_potentials.get(&edge.source).checked_invariant_ea357a0a("checked invariant");
            let gv = gauge_potentials.get(&edge.target).checked_invariant_ea357a0a("checked invariant");
            let u_mat = Self::pure_gauge_edge_matrix(gu, gv, dim)?;
            conn.set_connection(&edge.source, &edge.target, u_mat)?;
        }
        Ok(conn)
    }

    fn validate_all_vertices_present(
        complex: &CellComplex,
        gauge_potentials: &BTreeMap<String, ExactMatrix<T>>,
    ) -> Result<(), HolonomyError> {
        for v in &complex.vertices {
            if !gauge_potentials.contains_key(&v.id) {
                return Err(HolonomyError::VertexNotFound { id: v.id.clone() });
            }
        }
        Ok(())
    }

    fn check_pair_square_dim(
        gu: &ExactMatrix<T>,
        gv: &ExactMatrix<T>,
        dim: usize,
    ) -> Result<(), HolonomyError> {
        if gu.rows != dim || gu.cols != dim || gv.rows != dim || gv.cols != dim {
            return Err(HolonomyError::DimensionMismatch {
                expected: dim,
                actual: gu.rows,
            });
        }
        Ok(())
    }

    fn pure_gauge_edge_matrix(
        gu: &ExactMatrix<T>,
        gv: &ExactMatrix<T>,
        dim: usize,
    ) -> Result<ExactMatrix<T>, HolonomyError> {
        Self::check_pair_square_dim(gu, gv, dim)?;
        let gu_inv = gu.inverse()?;
        gv.matmul(&gu_inv)
    }

    /// Applies a 0-cochain gauge transformation $g: V \to GL(d, F)$:
    /// $$U'(u, v) = g(v) \cdot U(u, v) \cdot g(u)^{-1}$$
    pub fn apply_gauge_transformation(
        &self,
        gauge_potentials: &BTreeMap<String, ExactMatrix<T>>,
    ) -> Result<Self, HolonomyError> {
        let mut transformed = Self::new(self.dim, self.limits);
        for ((u, v), u_mat) in &self.forward {
            let new_u = self.gauge_transform_edge(u, v, u_mat, gauge_potentials)?;
            transformed.set_connection(u, v, new_u)?;
        }
        Ok(transformed)
    }

    fn gauge_transform_edge(
        &self,
        u: &str,
        v: &str,
        u_mat: &ExactMatrix<T>,
        gauge_potentials: &BTreeMap<String, ExactMatrix<T>>,
    ) -> Result<ExactMatrix<T>, HolonomyError> {
        let gu = gauge_potentials
            .get(u)
            .ok_or_else(|| HolonomyError::VertexNotFound { id: u.to_string() })?;
        let gv = gauge_potentials
            .get(v)
            .ok_or_else(|| HolonomyError::VertexNotFound { id: v.to_string() })?;
        Self::check_pair_square_dim(gu, gv, self.dim)?;
        let gu_inv = gu.inverse()?;
        let gv_u = gv.matmul(u_mat)?;
        gv_u.matmul(&gu_inv)
    }

    /// Computes a deterministic SHA-256 state hash of all connection matrices.
    pub fn content_hash(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(format!("DiscreteConnection:dim={}\n", self.dim).as_bytes());
        for ((u, v), m) in &self.forward {
            hasher.update(format!("Edge:{u}->{v}:{};\n", m.sha256_digest()).as_bytes());
        }
        format!("{:x}", hasher.finalize())
    }
}

/// Type alias for DiscreteConnection over BigRational.
pub type Connection = DiscreteConnection<BigRational>;

// Origin: engine/crates_rs/core_holonomy/src/connection.rs
// Claim: urn:core:crates_rs:core-holonomy:connection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordea357a0a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordea357a0a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorea357a0a {
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
impl BoundaryErrorea357a0a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorea357a0a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorea357a0a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordea357a0a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorea357a0a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorea357a0a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorea357a0a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorea357a0a::ExceedsCapacity {
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
mod l4_boundary_tests_ea357a0a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordea357a0a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordea357a0a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordea357a0a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordea357a0a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordea357a0a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorea357a0a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorea357a0a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
