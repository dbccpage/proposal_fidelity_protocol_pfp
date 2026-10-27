//! Core homology / computational algebraic topology.
//!
//! Crate renamed from `core_homological` (2026-08). AuthorityEffect: None.
//! New TDA modules are best-effort shells unless marked otherwise.

// --- Core chain / cochain foundation ---

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_1f3838c4;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_1f3838c4<T> = std::result::Result<T, BoundaryError_1f3838c4>;
pub mod boundary;
pub mod boundary_map;
pub mod boundary_trace;
pub mod carrier;
pub mod carrier_manifest;
pub mod cech_gate;
pub mod cell_grammar;
pub mod certificates;
pub mod chain;
pub mod chain_complex;
pub mod chain_map;
pub mod coboundary;
pub mod coboundary_matrix;
pub mod cochain;
pub mod cochain_complex;
pub mod cochain_primitive_difference;
pub mod cochain_realization;
pub mod cocycle;
pub mod coefficient_domain;
pub mod cohomology;
pub mod cycle;
pub mod cycle_basis;
pub mod directed_multigraph;
pub mod error;
pub mod errors;
pub use cycle_basis::{
    compute_cycle_basis, compute_cycle_basis_with_tree, CycleBasisCertificate, CycleBasisResult,
    Edge as CycleBasisEdge, FundamentalCycle,
};
pub mod f2_cohomology;
pub mod finite_cliques;
pub mod finite_directed_graph;
pub mod finite_poset;
pub mod graph_carrier;
pub mod graph_coloring;
pub mod graph_f2;
pub mod hash;
pub mod hashing;
pub mod homology;
pub mod homology_class;
pub mod ids;
pub mod integral_chain_complex;
pub mod integral_chain_equivalence;
pub mod matrix;
pub mod numerical_dual_witness;
pub mod permutohedral;
pub mod poset_census;
pub mod quotient;
pub mod restriction_dga;
pub mod block_embedding;
pub mod observed_2category;
pub mod scalar;
pub mod serialization;
pub mod declared_incidence;
pub mod simplicial;
pub mod smith_normal_form;
pub mod square_lattice;
pub mod trichotomy_witness;
pub mod witness;

pub mod cycle_aware;
pub mod cycle_space_projector;
pub mod lambda_graph;
pub mod presentation_symmetry;
pub mod primal_residual;
pub mod primitive_decomposition;
pub mod upper_triangular_pairs;

pub mod dgla;
pub mod exact_carrier;
pub mod homological_contract_alignment;
pub mod homological_perturbation;
pub mod l_infinity_operad;
pub mod lefschetz;
pub mod maurer_cartan;
pub mod transition_scorer;

// --- Persistent homology (TDA) ---
pub mod barcode;
pub mod filtration;
pub mod persistence_diagram;
pub mod persistence_pairing;
pub mod persistent_homology;
pub mod ph_matrix_reduction;
pub mod representative_cycle;

// --- Filtration / complex builders ---
pub mod alpha_complex;
pub mod dowker_complex;
pub mod sparse_filtration;
pub mod vietoris_rips;
pub mod witness_complex;

// --- Homology computation infrastructure ---
pub mod clearing_optimization;
pub mod homology_computer;
pub mod matrix_reduction;
pub mod twist_algorithm;

// --- Cohomology products ---
pub mod bockstein_homomorphism;
pub mod cap_product;
pub mod cohomology_algebra;
pub mod cup_product;

// --- Discrete Morse ---
pub mod discrete_morse_complex;
pub mod discrete_morse_function;
pub mod gradient_path;
pub mod morse_smale;

// --- Complex operations ---
pub mod clique_complex;
pub mod join_complex;
pub mod link_star;
pub mod mapping_cone;
pub mod mapping_cylinder;
pub mod subdivision;
pub mod suspension;

// --- Relative (co)homology ---
pub mod relative_chain_map;
pub mod relative_complex;
pub mod relative_homology;

// --- Spectral sequences ---
pub mod filtered_complex;
pub mod mayervietoris_ss;
pub mod serre_spectral_sequence;
pub mod spectral_sequence;

// --- Additional algebra ---
pub mod a_infinity_algebra;
pub mod deformation_complex;
pub mod e_infinity_operad;

// --- Diagram metrics & viz ---
pub mod bottleneck_distance;
pub mod diagram_plotting;
pub mod interleaving_distance;
pub mod wasserstein_distance;

// --- I/O formats ---
pub mod dipha_io;
pub mod exact_betti;
pub mod gudhi_io;
pub mod perseus_io;
pub mod phat_io;

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests;

#[cfg(test)]
mod contract_property_witnesses;

pub mod cyclic_phase;
pub mod finite_rational_homology;

// Exact invariant envelope.
// Origin: engine/crates_rs/core_homology/src/lib.rs
// Claim: urn:core:homology:cyclomatic-number:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CyclomaticWitness {
    vertices: u64,
    edges: u64,
    components: u64,
    betti_one: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CyclomaticError {
    Empty,
    TooWide,
    DuplicateVertex { index: usize },
    EmptyVertex { index: usize },
    Endpoint { index: usize },
    Components { components: u64, vertices: u64 },
    NegativeBetti { vertices: u64, edges: u64, components: u64 },
}

// Origin: engine/crates_rs/core_homology/src/lib.rs
// Claim: urn:core:crates_rs:core-homology:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CyclomaticError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CyclomaticError {}

impl CyclomaticWitness {
    pub fn vertices(&self) -> u64 { self.vertices }
    pub fn edges(&self) -> u64 { self.edges }
    pub fn components(&self) -> u64 { self.components }
    pub fn betti_one(&self) -> u64 { self.betti_one }

    pub fn try_from_graph(
        vertices: &[String],
        edges: &[cycle_basis::Edge],
        components: u64,
    ) -> Result<Self, CyclomaticError> {
        if vertices.is_empty() {
            return Err(CyclomaticError::Empty);
        }
        if vertices.len() > 1024 || edges.len() > 1024 {
            return Err(CyclomaticError::TooWide);
        }
        Self::validate_vertices_and_edges(vertices, edges)?;
        let vertex_count = u64::try_from(vertices.len()).map_err(|_| CyclomaticError::TooWide)?;
        let edge_count = u64::try_from(edges.len()).map_err(|_| CyclomaticError::TooWide)?;
        if components == 0 || components > vertex_count {
            return Err(CyclomaticError::Components { components, vertices: vertex_count });
        }
        let betti_one = edge_count.checked_add(components).and_then(|n| n.checked_sub(vertex_count)).ok_or(
            CyclomaticError::NegativeBetti { vertices: vertex_count, edges: edge_count, components },
        )?;
        Ok(Self { vertices: vertex_count, edges: edge_count, components, betti_one })
    }

    fn validate_vertices_and_edges(
        vertices: &[String],
        edges: &[cycle_basis::Edge],
    ) -> Result<(), CyclomaticError> {
        for (index, name) in vertices.iter().enumerate() {
            if name.is_empty() {
                return Err(CyclomaticError::EmptyVertex { index });
            }
            if vertices.iter().take(index).any(|earlier| earlier == name) {
                return Err(CyclomaticError::DuplicateVertex { index });
            }
        }
        for (index, edge) in edges.iter().enumerate() {
            if !vertices.iter().any(|name| name == &edge.u) || !vertices.iter().any(|name| name == &edge.v) {
                return Err(CyclomaticError::Endpoint { index });
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod cyclomatic_tests {
    use super::*;

    fn edge(u: &str, v: &str) -> cycle_basis::Edge {
        cycle_basis::Edge { u: u.to_string(), v: v.to_string(), weight: 1 }
    }

    #[test]
    fn a_triangle_has_betti_number_one() {
        let vertices = vec!["a".to_string(), "b".to_string(), "c".to_string()];
        let edges = vec![edge("a", "b"), edge("b", "c"), edge("c", "a")];
        let witness = CyclomaticWitness::try_from_graph(&vertices, &edges, 1);
        assert!(matches!(witness, Ok(ref row) if row.betti_one() == 1 && row.edges() == 3 && row.vertices() == 3));
    }

    #[test]
    fn a_forest_claim_with_too_few_components_is_negative() {
        let vertices = vec!["a".to_string(), "b".to_string()];
        let witness = CyclomaticWitness::try_from_graph(&vertices, &[], 1);
        assert!(matches!(
            witness,
            Err(CyclomaticError::NegativeBetti { vertices: 2, edges: 0, components: 1 })
        ));
    }
}
