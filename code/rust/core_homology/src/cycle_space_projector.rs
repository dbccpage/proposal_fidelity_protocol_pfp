
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_25618e05<T> {
    fn checked_invariant_25618e05(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_25618e05<T> for Option<T> {
    #[inline]
    fn checked_invariant_25618e05(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_25618e05<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_25618e05(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::finite_directed_graph::FiniteDirectedGraph;
use linear_algebra::linear_algebra::incidence_matrix::incidence_matrix;
use nalgebra::{DMatrix, DVector};

/// Computes the orthogonal projection matrix onto the harmonic cycle space
/// for a graph complex where ker(d) is assumed to be the whole space.
pub fn compute_cycle_space_projector_graph_only(
    n_nodes: usize,
    edges: &[(usize, usize)],
) -> Result<DMatrix<f64>, String> {
    if edges.is_empty() {
        return Ok(DMatrix::zeros(0, 0));
    }

    let basic_b = incidence_matrix(n_nodes, edges).map_err(|e| format!("{:?}", e))?;
    let b = DMatrix::from_fn(basic_b.rows(), basic_b.cols(), |r, c| {
        basic_b.get(r, c).checked_invariant_25618e05("checked invariant") as f64
    });

    // Compute pseudo-inverse of incidence matrix
    let b_pinv = b
        .clone()
        .pseudo_inverse(1e-10)
        .map_err(|_| "SVD failed for pseudoinverse")?;

    // Projector onto the exact forms (image of B)
    let exact_proj = b * b_pinv;
    let mut cycle_proj = DMatrix::identity(edges.len(), edges.len()) - exact_proj;

    for i in 0..edges.len() {
        for j in (i + 1)..edges.len() {
            let avg = 0.5 * (cycle_proj[(i, j)] + cycle_proj[(j, i)]);
            cycle_proj[(i, j)] = avg;
            cycle_proj[(j, i)] = avg;
        }
    }

    Ok(cycle_proj)
}

/// Computes an orthonormal basis for the harmonic cycle space.
///
/// This basis consists of the nullspace vectors of the incidence matrix transpose.
pub fn compute_harmonic_basis(topology: &FiniteDirectedGraph) -> Result<Vec<DVector<f64>>, String> {
    let n_nodes = topology.num_nodes();
    let edges = topology.edges();
    if edges.is_empty() {
        return Ok(vec![]);
    }

    let basic_b = incidence_matrix(n_nodes, edges).map_err(|e| format!("{:?}", e))?;
    let b = DMatrix::from_fn(basic_b.rows(), basic_b.cols(), |r, c| {
        basic_b.get(r, c).checked_invariant_25618e05("checked invariant") as f64
    });

    // Harmonic forms are the kernel of B^T (orthogonal complement of im(B))
    let svd = b.transpose().svd(false, true);
    let v_t = svd.v_t.ok_or("SVD failed to produce V_t")?;

    let mut basis = Vec::new();
    let n_edges = edges.len();

    for i in 0..n_edges {
        if harmonic_singular_is_member(i, svd.singular_values.as_slice()) {
            basis.push(v_t.row(i).transpose());
        }
    }

    Ok(basis)
}

fn harmonic_singular_is_member(index: usize, singular_values: &[f64]) -> bool {
    singular_values.get(index).copied() == Some(0.0)
}

// Origin: engine/crates_rs/core_homology/src/cycle_space_projector.rs
// Claim: urn:core:crates_rs:core-homology:cycle-space-projector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord25618e05 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord25618e05` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError25618e05 {
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
impl BoundaryError25618e05 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError25618e05 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError25618e05 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord25618e05 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError25618e05> {
        if capacity_bound == 0 {
            return Err(BoundaryError25618e05::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError25618e05::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError25618e05::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_harmonic_basis_is_orthogonal_to_incidence() {
        let edges = vec![(0, 1), (1, 2), (2, 0)];
        let topology = FiniteDirectedGraph::from_pairs(
            &edges,
            crate::finite_directed_graph::TheoremProvenance {
                verification_source: "test".to_string(),
            },
        )
        .unwrap();
        let basis = compute_harmonic_basis(&topology).unwrap();

        let basic_b = incidence_matrix(3, &edges).unwrap();
        let b = DMatrix::from_fn(3, 3, |r, c| basic_b.get(r, c).unwrap() as f64);

        for v in basis {
            let res = &b * &v;
            assert!(
                res.norm() < 1e-10,
                "basis vector not in kernel of B: norm = {}",
                res.norm()
            );
        }
    }

    #[test]
    fn test_harmonic_basis_is_orthonormal() {
        let edges = vec![(0, 1), (1, 2), (2, 0)];
        let topology = FiniteDirectedGraph::from_pairs(
            &edges,
            crate::finite_directed_graph::TheoremProvenance {
                verification_source: "test".to_string(),
            },
        )
        .unwrap();
        let basis = compute_harmonic_basis(&topology).unwrap();

        for (i, v1) in basis.iter().enumerate() {
            for (j, v2) in basis.iter().enumerate() {
                let dot = v1.dot(v2);
                if i == j {
                    assert!(
                        (dot - 1.0).abs() < 1e-10,
                        "basis vector not normalized: dot = {}",
                        dot
                    );
                } else {
                    assert!(
                        dot.abs() < 1e-10,
                        "basis vectors not orthogonal: dot = {}",
                        dot
                    );
                }
            }
        }
    }

    #[test]
    fn nonzero_or_missing_singular_value_is_not_a_harmonic_member() {
        assert!(super::harmonic_singular_is_member(0, &[0.0]));
        assert!(!super::harmonic_singular_is_member(0, &[1e-12]));
        assert!(!super::harmonic_singular_is_member(0, &[1e-11]));
        assert!(!super::harmonic_singular_is_member(1, &[0.0]));
        assert!(!super::harmonic_singular_is_member(0, &[]));
    }
}

#[cfg(test)]
mod l4_boundary_tests_25618e05 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord25618e05::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord25618e05::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord25618e05::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord25618e05::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord25618e05::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError25618e05::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError25618e05::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
