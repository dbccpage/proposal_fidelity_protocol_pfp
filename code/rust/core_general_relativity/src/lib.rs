//! `core_general_relativity` — domain dual-face GR crate.
//!
//! **Deepened (finite Regge / simplicial):**
//! - [`discrete_spacetime`] — face-closed complex via `core_homology::simplicial`
//! - [`regge_calculus`] — edge lengths, vertex deficits, 2D Regge action
//! - [`scalar_curvature`] — deficit carriers
//! - [`einstein_hilbert_action`] — f64 face; not the exact proxy (the sum of area_squared times kappa)
//!
//! **No separate `core_simplex` crate:** simplicial complexes already live in
//! `core_homology::simplicial` (`Simplex`, `OrientedSimplex`, `SimplicialComplex`).
//!
//! Remaining modules may still be shape scaffolds. AuthorityEffect: None.
//! Not continuum GR. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_c462cb37;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_c462cb37<T> = std::result::Result<T, BoundaryError_c462cb37>;
pub mod bi_crossed_product;
pub mod causal_dynamical_triangulation;
pub mod causal_set;
pub mod certified_dihedral;
pub mod cayley_menger;
pub mod connection;
pub mod cosmological_constant;
pub mod curvature_tensor;
pub mod dec_laplacian;
pub mod dihedral_angles;
pub mod dirac_operator_discrete;
pub mod discrete_spacetime;
pub mod einstein_hilbert_action;
/// Exact rational 4D Regge engine over `BigRational`.
/// Does not call [`regge_4d`], [`regge_action`], [`regge_calculus`], or [`cayley_menger`].
/// AuthorityEffect: None.
pub mod exact_regge;
pub mod field_equation;
pub mod gauge_transformation;
pub mod hamiltonian_constraint;
pub mod holonomy;
pub mod initial_value_formulation;
pub mod loop_quantum_gravity;
pub mod metric_hinge_transport;
pub mod quantum_group_symmetry;
pub mod quantum_regge;
pub mod regge_4d;
pub mod regge_action;
pub mod regge_calculus;
pub mod regge_deficit_holonomy;
pub mod ricci_curvature;
pub mod scalar_curvature;
pub mod schlafli;
pub mod spectral_triple;
pub mod spin_connection;
pub mod spin_foam;
pub mod spinor_field;
pub mod tetrad_formalism;

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod certified_authority_fence;

pub mod simplicial_dynamics;

/// Refusal from an integer complete-simplex edge count.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EdgeCountError {
    /// Fewer than two vertices, or more than 16.
    VertexCount { n: u32 },
    /// The product formula and Pascal's recurrence disagreed.
    Disagreement { product: u32, pascal: u32 },
    /// Checked arithmetic overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_general_relativity/src/lib.rs
// Claim: urn:core:crates_rs:core-general-relativity:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for EdgeCountError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for EdgeCountError {}

/// `C(n, 2)`, the number of edges of a complete simplex on `n` vertices.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SimplexEdgeCount {
    edges: u32,
}

impl SimplexEdgeCount {
    /// Compute `n(n-1)/2` and the same value by Pascal's recurrence `C(n,2) = C(n-1,2) + (n-1)`.
    pub fn try_complete(vertices: u32) -> Result<Self, EdgeCountError> {
        if vertices < 2 || vertices > 16 {
            return Err(EdgeCountError::VertexCount { n: vertices });
        }
        let prev = vertices.checked_sub(1).ok_or(EdgeCountError::Overflow)?;
        let product = vertices
            .checked_mul(prev)
            .ok_or(EdgeCountError::Overflow)?
            / 2;
        let mut pascal = 0u32;
        for n in 2..=vertices {
            let add = n.checked_sub(1).ok_or(EdgeCountError::Overflow)?;
            pascal = pascal.checked_add(add).ok_or(EdgeCountError::Overflow)?;
        }
        if product != pascal {
            return Err(EdgeCountError::Disagreement { product, pascal });
        }
        Ok(Self { edges: product })
    }

    /// Edge count.
    pub fn edges(&self) -> u32 { self.edges }
}

#[cfg(test)]
mod simplex_edge_tests {
    use super::*;
    #[test]
    fn a_4_simplex_has_ten_edges() {
        let edges = SimplexEdgeCount::try_complete(5);
        assert!(matches!(edges, Ok(ref e) if e.edges() == 10));
    }
}
