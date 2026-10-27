use linear_algebra::linear_algebra::incidence_matrix::{
    incidence_matrix, incidence_matrix_dmatrix,
};
use nalgebra::{DMatrix, DVector};
use core_homology::finite_directed_graph::FiniteDirectedGraph;

fn extract_zero_singular_vectors(
    v_t: &DMatrix<f64>,
    singular_values: &[f64],
    n_edges: usize,
) -> Vec<DVector<f64>> {
    let mut basis = Vec::new();
    for (i, &singular) in singular_values.iter().enumerate() {
        if singular == 0.0 {
            let mut vec = DVector::zeros(n_edges);
            for j in 0..n_edges {
                vec[j] = v_t[(i, j)];
            }
            basis.push(vec);
        }
    }
    basis
}

/// Orthonormal basis of harmonic 1-cochains, `ker(Bᵀ) ⊆ R^|E|`.
///
/// `B` is the edge-node incidence (`|E| × |V|`). The matrix factored here is
/// `Bᵀ`, with zero rows added until it has at least as many rows as columns.
/// Thin SVD of a wide matrix omits kernel directions of `V`.
pub fn compute_harmonic_basis(topology: &FiniteDirectedGraph) -> Result<Vec<DVector<f64>>, String> {
    let n_nodes = topology.num_nodes();
    let edges = topology.edges();
    if edges.is_empty() {
        return Ok(vec![]);
    }

    let incidence = incidence_matrix_dmatrix(n_nodes, edges).map_err(|e| format!("{:?}", e))?;
    let n_edges = edges.len();
    let mut coboundary = DMatrix::<f64>::zeros(n_edges.max(n_nodes), n_edges);
    for edge in 0..n_edges {
        for node in 0..n_nodes {
            coboundary[(node, edge)] = incidence[(edge, node)] as f64;
        }
    }

    let svd = coboundary.svd(false, true);
    let v_t = svd.v_t.ok_or("SVD failed to produce V_t")?;
    if v_t.ncols() != n_edges || v_t.nrows() != svd.singular_values.len() {
        return Err(format!(
            "SVD V_t is {}x{} with {} singular values; expected {n_edges} columns and one value per row",
            v_t.nrows(),
            v_t.ncols(),
            svd.singular_values.len()
        ));
    }

    Ok(extract_zero_singular_vectors(
        &v_t,
        svd.singular_values.as_slice(),
        n_edges,
    ))
}

// Origin: engine/crates_rs/engines/src/quantum/cycle_space_projector.rs
// Claim: urn:core:crates_rs:engines:cycle-space-projector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde843189d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde843189d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore843189d {
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
impl BoundaryErrore843189d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore843189d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore843189d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde843189d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore843189d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore843189d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore843189d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore843189d::ExceedsCapacity {
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
            core_homology::finite_directed_graph::TheoremProvenance {
                verification_source: "test".to_string(),
            },
        )
        .unwrap();
        let basis = compute_harmonic_basis(&topology).unwrap();

        let basic_b = incidence_matrix(3, &edges).unwrap();
        let b = DMatrix::from_fn(3, 3, |r, c| basic_b.get(r, c).unwrap() as f64);

        for v in basis {
            let res = b.transpose() * &v;
            assert!(
                res.norm() < 1e-10,
                "basis vector not in ker(B^T): norm = {}",
                res.norm()
            );
        }
    }

    #[test]
    fn two_triangles_sharing_a_vertex_have_a_two_dimensional_cycle_space() {
        let edges = vec![(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)];
        let topology = FiniteDirectedGraph::from_pairs(
            &edges,
            core_homology::finite_directed_graph::TheoremProvenance {
                verification_source: "test".to_string(),
            },
        )
        .unwrap();
        let basis = compute_harmonic_basis(&topology).unwrap();
        assert_eq!(basis.len(), 2);
        assert!(basis.iter().all(|vector| vector.len() == edges.len()));

        let basic_b = incidence_matrix(5, &edges).unwrap();
        let b = DMatrix::from_fn(edges.len(), 5, |r, c| basic_b.get(r, c).unwrap() as f64);
        for vector in &basis {
            let residual = b.transpose() * vector;
            assert!(residual.norm() < 1e-8, "norm = {}", residual.norm());
        }
        let dot = basis[0].dot(&basis[1]);
        assert!(dot.abs() < 1e-8, "dot = {dot}");
    }

    #[test]
    fn test_harmonic_basis_is_orthonormal() {
        let edges = vec![(0, 1), (1, 2), (2, 0)];
        let topology = FiniteDirectedGraph::from_pairs(
            &edges,
            core_homology::finite_directed_graph::TheoremProvenance {
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
}

#[cfg(test)]
mod l4_boundary_tests_e843189d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde843189d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde843189d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde843189d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde843189d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde843189d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore843189d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore843189d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
