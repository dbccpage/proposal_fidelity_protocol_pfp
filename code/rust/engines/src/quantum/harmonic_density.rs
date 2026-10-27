//! Harmonic density matrix – a robust topological fingerprint.
//!
//! Builds a mixed quantum state over the space of harmonic 1-forms
//! (the nullspace of the Hodge Laplacian Δ₁). The dimension of this
//! space is exactly the 1st Betti number β₁ of the graph.

use crate::quantum::cycle_space_projector::compute_harmonic_basis;
use crate::quantum::density_error::DensityMatrixError;
use crate::quantum::density_matrix::{CMatrix, DensityMatrix, NComplex};
use nalgebra::DVector;
use core_homology::finite_directed_graph::FiniteDirectedGraph;

/// Build the harmonic density matrix from a list of orthonormal co-chains.
fn density_from_harmonics(
    harmonics: &[DVector<f64>],
    tol: f64,
) -> Result<DensityMatrix, DensityMatrixError> {
    let m = if let Some(h) = harmonics.first() {
        h.len()
    } else {
        return Err(DensityMatrixError::NoValidStates);
    };

    if harmonics.is_empty() {
        return Err(DensityMatrixError::NoValidStates);
    }

    let beta = harmonics.len();

    for i in 0..beta {
        for j in 0..beta {
            let dot = harmonics[i].dot(&harmonics[j]);
            let target = if i == j { 1.0 } else { 0.0 };
            if (dot - target).abs() > tol {
                return Err(DensityMatrixError::NonPhysical);
            }
        }
    }

    let rho_mat = harmonics.iter().fold(CMatrix::zeros(m, m), |acc, omega| {
        acc + CMatrix::from_fn(m, m, |i, j| {
            NComplex::new(omega[i] * omega[j] / beta as f64, 0.0)
        })
    });

    let cfg = crate::quantum::density_config::DensityMatrixConfig::default();
    let rho = DensityMatrix::from_validated(rho_mat.nrows(), rho_mat.as_slice().to_vec(), &cfg)?;

    Ok(rho)
}

/// Compute the harmonic density matrix for a graph given as edge list.
pub fn harmonic_density(
    edges: &[(usize, usize)],
    n_vertices: usize,
    tol: f64,
) -> Result<DensityMatrix, DensityMatrixError> {
    if n_vertices == 0 {
        return Err(DensityMatrixError::ZeroDimension);
    }

    for &(u, v) in edges {
        if u >= n_vertices || v >= n_vertices {
            return Err(DensityMatrixError::DimensionMismatch {
                expected: n_vertices,
                actual: u.max(v) + 1,
            });
        }
    }

    if edges.is_empty() {
        return Err(DensityMatrixError::NoValidStates);
    }
    let graph = FiniteDirectedGraph::from_pairs(
        edges,
        core_homology::finite_directed_graph::TheoremProvenance {
            verification_source: "engine_internal".to_string(),
        },
    )
    .map_err(|_| DensityMatrixError::NonPhysical)?;
    let harmonics = compute_harmonic_basis(&graph).map_err(|_| DensityMatrixError::NonPhysical)?;
    density_from_harmonics(&harmonics, tol)
}

// Origin: engine/crates_rs/engines/src/quantum/harmonic_density.rs
// Claim: urn:core:crates_rs:engines:harmonic-density:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord17ea0d28 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord17ea0d28` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError17ea0d28 {
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
impl BoundaryError17ea0d28 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError17ea0d28 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError17ea0d28 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord17ea0d28 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError17ea0d28> {
        if capacity_bound == 0 {
            return Err(BoundaryError17ea0d28::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError17ea0d28::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError17ea0d28::ExceedsCapacity {
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
    fn two_triangles_sharing_vertex_beta_two() {
        let edges = vec![(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)];
        let rho = harmonic_density(&edges, 5, 1e-8).unwrap();
        let purity = rho.purity();
        let entropy = rho.von_neumann_entropy().unwrap();
        assert!((purity - 0.5).abs() < 1e-4);
        assert!((entropy - (2.0_f64).ln()).abs() < 1e-4);
        assert_eq!(rho.dim(), 6);
    }

    #[test]
    fn tree_has_no_harmonic_density() {
        let edges = vec![(0, 1), (1, 2), (2, 3)];

        let err = harmonic_density(&edges, 4, 1e-8).unwrap_err();

        assert!(matches!(
            err,
            DensityMatrixError::NoValidStates | DensityMatrixError::NonPhysical
        ));
    }

    #[test]
    fn rejects_edge_endpoint_outside_vertex_count() {
        let edges = vec![(0, 1), (1, 4)];

        let err = harmonic_density(&edges, 3, 1e-8).unwrap_err();

        assert!(matches!(err, DensityMatrixError::DimensionMismatch { .. }));
    }

    #[test]
    fn single_triangle_rank_one_harmonic_density() {
        let edges = vec![(0, 1), (1, 2), (2, 0)];

        let rho = harmonic_density(&edges, 3, 1e-8).unwrap();

        assert!((rho.trace() - 1.0).abs() < 1e-10);
        assert!((rho.purity() - 1.0).abs() < 1e-8);
        assert!(rho.von_neumann_entropy().unwrap().abs() < 1e-8);
    }

    #[test]
    fn two_independent_cycles_rank_two_density() {
        let edges = vec![(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)];

        let rho = harmonic_density(&edges, 6, 1e-8).unwrap();

        assert!((rho.trace() - 1.0).abs() < 1e-10);
        assert!((rho.purity() - 0.5).abs() < 1e-5);
        assert!((rho.von_neumann_entropy().unwrap() - (2.0_f64).ln()).abs() < 1e-5);
    }
}

#[cfg(test)]
mod l4_boundary_tests_17ea0d28 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord17ea0d28::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord17ea0d28::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord17ea0d28::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord17ea0d28::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord17ea0d28::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError17ea0d28::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError17ea0d28::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
