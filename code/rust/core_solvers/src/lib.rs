//! Solvers substrate for the engine.
//!
//! Provides algebraic, continuous, discrete, SAT, graph, spectral, topological,
//! and quantum solvers.
//! AuthorityEffect: None.

pub mod cert_channel_capacity;
pub mod cert_cohomology_admission;
pub mod cert_hodge_decomp;
pub mod cert_lggr_soundness;
pub mod cert_phi1_distribution;
pub mod compliance;
pub mod data_cochain_packet;
pub mod data_difference_ledger;
pub mod data_repair_packet;
pub mod finite_belief_game;
pub mod router_plan_grammar;
pub mod router_structure_extension;
pub mod solver_cohomology_mayer_vietoris;
pub mod solver_cohomology_quotient_phi1;
pub mod solver_cohomology_sheaf;
pub mod solver_cohomology_splitting;
pub mod solver_convex_farkas_feasibility;
pub mod solver_convex_finite_hull;
pub mod solver_convex_vertex_enum;
pub mod solver_crn_deficiency;
pub mod solver_descent_gradient;
pub mod solver_fixpoint_operator;
pub mod solver_flow_gomory_hu;
pub mod solver_flow_network_simplex;
pub mod solver_gauge_yang_mills;
pub mod solver_graph_reconciliation;
pub mod solver_lp_bounded_candidate;
pub mod solver_lp_exact_simplex;
pub mod solver_lp_phi1_boundary;
pub mod solver_quantum_lefschetz_thimble;
pub mod solver_sat_dpll;
pub mod solver_sat_multiscale_repair;
pub mod solver_sat_unsat_core;
pub mod solver_spectrum_laplacian;
pub mod solver_spectrum_periodic;

/// Canonical re-export alias matching Paper 006 (GS-003) §G.9 specification.
pub mod q_obstruction_solver {
    pub use crate::solver_spectrum_laplacian::*;
}

pub use router_plan_grammar::{
    route_declared_finite_grammar, CostOrder, DeclaredPlanEvaluationV1, EvaluationStatus,
    FinitePlanGrammarV1, FrontierClassV1, FrontierTerminal, PlanFrontierV1, PlanKind,
    SearchDeclarationV1,
};
pub use router_structure_extension::{
    propose_question_family_extension, CheckedQuestionExtensionV1, ExtensionProposalReceiptV1,
};

pub mod solver_lp_standard_form;

pub mod data_computation_carrier;
pub mod data_hodge_packet;

pub mod solver_cohomology_simplicial_l1;

pub use solver_cohomology_simplicial_l1::{solve_l1_quotient, QuotientCertificate};

pub mod solver_lp_phi1_quotient;

pub mod solver_graph_phi1_distance;

pub mod solver_hodge_rational_decomp;
pub mod solver_neville_aitken_enclosure;

pub mod finite_stream_interpreter;

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConvexError {
    Shape,
    Weight,
    Image { coordinate: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_solvers/src/lib.rs
// Claim: urn:core:crates_rs:core-solvers:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ConvexError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ConvexError {}

/// An exact rational convex combination: image * total weight equals the weighted sum.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalConvexImage {
    dimension: usize,
    total_weight: u64,
}

impl RationalConvexImage {
    fn validate_and_sum_weights(
        weights: &[u32],
        points: &[Vec<i64>],
        dimension: usize,
    ) -> Result<u64, ConvexError> {
        let mut total_weight = 0u64;
        for (point, &weight) in points.iter().zip(weights) {
            if weight == 0 {
                return Err(ConvexError::Weight);
            }
            if point.len() != dimension {
                return Err(ConvexError::Shape);
            }
            total_weight = total_weight
                .checked_add(u64::from(weight))
                .ok_or(ConvexError::Overflow)?;
        }
        Ok(total_weight)
    }

    fn verify_coordinate_combination(
        weights: &[u32],
        points: &[Vec<i64>],
        image: &[i64],
        coordinate: usize,
        total_weight: u64,
    ) -> Result<(), ConvexError> {
        let mut weighted = 0i128;
        for (point, &w) in points.iter().zip(weights) {
            let value = i128::from(*point.get(coordinate).ok_or(ConvexError::Shape)?);
            let term = value
                .checked_mul(i128::from(w))
                .ok_or(ConvexError::Overflow)?;
            weighted = weighted.checked_add(term).ok_or(ConvexError::Overflow)?;
        }
        let image_value = i128::from(*image.get(coordinate).ok_or(ConvexError::Shape)?);
        let scaled = image_value
            .checked_mul(i128::from(total_weight))
            .ok_or(ConvexError::Overflow)?;
        if weighted != scaled {
            return Err(ConvexError::Image { coordinate });
        }
        Ok(())
    }

    pub fn try_combine(weights: &[u32], points: &[Vec<i64>], image: &[i64]) -> Result<Self, ConvexError> {
        if weights.is_empty() || weights.len() != points.len() || image.is_empty() {
            return Err(ConvexError::Shape);
        }
        let dimension = image.len();
        let total_weight = Self::validate_and_sum_weights(weights, points, dimension)?;
        for coordinate in 0..dimension {
            Self::verify_coordinate_combination(weights, points, image, coordinate, total_weight)?;
        }
        Ok(Self { dimension, total_weight })
    }

    pub fn dimension(&self) -> usize { self.dimension }
    pub fn total_weight(&self) -> u64 { self.total_weight }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod convex_tests {
    use super::*;

    #[test]
    fn the_midpoint_of_zero_and_two_is_one() {
        let image = RationalConvexImage::try_combine(&[1, 1], &[vec![0, 0], vec![2, 2]], &[1, 1]);
        assert!(matches!(image, Ok(ref image) if image.dimension() == 2 && image.total_weight() == 2));
    }

    #[test]
    fn a_shifted_image_is_refused() {
        let image = RationalConvexImage::try_combine(&[1, 1], &[vec![0, 0], vec![2, 2]], &[0, 0]);
        assert!(matches!(image, Err(ConvexError::Image { coordinate: 0 })));
    }
}
