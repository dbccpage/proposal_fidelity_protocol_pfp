
#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_ec7bd15e;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_ec7bd15e<T> = std::result::Result<T, BoundaryError_ec7bd15e>;
use crate::obstruction_runtime::{Candidate, CandidateGenerator};
pub use core_homology::cycle_aware::{
    apply_correction, CorrectionStrategy, CycleAwareConfig, CycleCorrectableState, XiDiagnostic,
    XiDiagnosticError, XiDiagnosticFunctional, XiWitness, XiWitnessError,
};

// Re-export OperatorId so test code using `use super::*` can access it
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
pub(crate) use crate::obstruction_runtime::OperatorId;

/// A generator that proposes candidates targeting cycle obstructions
/// identified by Xi witnesses.
///
/// When the parent state has low Xi, this generator:
/// 1. Consumes a `XiDiagnostic` to compute harmonic projection and witness.
/// 2. Identifies the worst distorted edges via `XiWitness`.
/// 3. Proposes candidates that correct those edges (snap or nudge toward harmonic).
///
/// When Xi is already high, this generator produces no candidates, deferring
/// to other generators in the scheduler's mixture.
pub struct CycleAwareGenerator<D> {
    pub config: CycleAwareConfig,
    /// A diagnostic functional that securely computes harmonic projection and Xi value.
    pub diagnostic: D,
}

impl<S, D> CandidateGenerator<S> for CycleAwareGenerator<D>
where
    S: CycleCorrectableState,
    D: XiDiagnosticFunctional<S>,
{
    fn generate(&self, state: &S) -> Vec<Candidate<S>> {
        if self.config.validate().is_err() {
            return Vec::new();
        }

        if !state.validate_cycle_correctable() {
            return Vec::new();
        }

        let diagnostic = match self.diagnostic.diagnose(state) {
            Ok(d) => d,
            Err(_) => return Vec::new(),
        };

        // Validate diagnostic consistency against state
        if !diagnostic.is_valid_for_edge_count(state.edge_values().len()) {
            return Vec::new();
        }

        // Only activate when coherence is below threshold
        if diagnostic.xi_value >= self.config.xi_activation_threshold {
            return vec![];
        }

        let witness = diagnostic.witness;
        if witness.worst_edges.is_empty() {
            return vec![];
        }

        let worst_edges: Vec<usize> = witness
            .worst_edges
            .iter()
            .copied()
            .take(self.config.top_k_edges)
            .collect();

        if worst_edges.is_empty() {
            return vec![];
        }

        let mut candidates = Vec::new();

        // Strategy 1: Correct ALL worst edges simultaneously
        let corrected_all = apply_correction(
            state.edge_values(),
            &diagnostic.harmonic_projection,
            &worst_edges,
            &self.config.strategy,
        );
        candidates.push(Candidate::new(
            state.with_corrected_edges(corrected_all),
            "cycle_aware.bulk_correction",
            format!(
                "corrects {} worst edges (max_distortion={:.4}, xi={:.4})",
                worst_edges.len(),
                witness.max_distortion(),
                diagnostic.xi_value,
            ),
        ));

        // Strategy 2: Correct each worst edge individually (one candidate per edge)
        for &edge_idx in &worst_edges {
            let corrected_single = apply_correction(
                state.edge_values(),
                &diagnostic.harmonic_projection,
                &[edge_idx],
                &self.config.strategy,
            );
            candidates.push(Candidate::new(
                state.with_corrected_edges(corrected_single),
                "cycle_aware.single_edge",
                format!(
                    "corrects edge {} (distortion={:.4})",
                    edge_idx, witness.edge_distortions[edge_idx],
                ),
            ));
        }

        candidates
    }
}

// Origin: engine/crates_rs/engines/src/cycle_aware.rs
// Claim: urn:core:crates_rs:engines:cycle-aware:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordec7bd15e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordec7bd15e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorec7bd15e {
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
impl BoundaryErrorec7bd15e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorec7bd15e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorec7bd15e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordec7bd15e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorec7bd15e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorec7bd15e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorec7bd15e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorec7bd15e::ExceedsCapacity {
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
mod tests {
    use super::*;
    use core_homology::cycle_aware::{try_compute_xi_witness, XiDiagnostic, XiWitness};

    // --- Test state ---

    #[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
    struct GraphState {
        node_count: usize,
        edges: Vec<(usize, usize)>,
        edge_values: Vec<f64>,
    }

    impl CycleCorrectableState for GraphState {
        fn edge_values(&self) -> &[f64] {
            &self.edge_values
        }
        fn edges(&self) -> &[(usize, usize)] {
            &self.edges
        }
        fn node_count(&self) -> usize {
            self.node_count
        }
        fn with_corrected_edges(&self, corrected: Vec<f64>) -> Self {
            Self {
                node_count: self.node_count,
                edges: self.edges.clone(),
                edge_values: corrected,
            }
        }
    }

    fn triangle_state(edge_vals: Vec<f64>) -> GraphState {
        GraphState {
            node_count: 3,
            edges: vec![(0, 1), (1, 2), (2, 0)],
            edge_values: edge_vals,
        }
    }

    // --- Mock Diagnostic ---

    struct MockDiagnostic(Vec<f64>, f64);

    impl XiDiagnosticFunctional<GraphState> for MockDiagnostic {
        fn diagnose(&self, state: &GraphState) -> Result<XiDiagnostic, XiDiagnosticError> {
            let witness = try_compute_xi_witness(state.edge_values(), &self.0, self.1, 0)?;
            Ok(XiDiagnostic {
                harmonic_projection: self.0.clone(),
                xi_value: self.1,
                witness,
            })
        }
    }

    #[test]
    fn invalid_alpha_produces_no_candidates() {
        let state = triangle_state(vec![3.0, 1.0, 2.0]);

        let gen = CycleAwareGenerator {
            config: CycleAwareConfig {
                xi_activation_threshold: 0.5,
                top_k_edges: 2,
                strategy: CorrectionStrategy::GradientStep { alpha: f64::NAN },
            },
            diagnostic: MockDiagnostic(vec![2.0, 2.0, 2.0], 0.3),
        };

        assert!(gen.generate(&state).is_empty());
    }

    #[test]
    fn invalid_state_edge_lengths_produce_no_candidates() {
        let state = GraphState {
            node_count: 3,
            edges: vec![(0, 1), (1, 2), (2, 0)],
            edge_values: vec![1.0], // mismatch length
        };

        let gen = CycleAwareGenerator {
            config: CycleAwareConfig::default(),
            diagnostic: MockDiagnostic(vec![1.0], 0.2), // length 1 harmonic matches omega length but fails state cycle check
        };

        assert!(gen.generate(&state).is_empty());
    }

    // --- Generator tests ---

    #[test]
    fn generator_produces_no_candidates_when_xi_high() {
        let state = triangle_state(vec![1.0, 1.0, 1.0]);
        let gen = CycleAwareGenerator {
            config: CycleAwareConfig {
                xi_activation_threshold: 0.5,
                top_k_edges: 3,
                strategy: CorrectionStrategy::default(),
            },
            diagnostic: MockDiagnostic(vec![1.0, 1.0, 1.0], 0.95),
        };

        let candidates = gen.generate(&state);
        assert!(candidates.is_empty(), "should not generate when xi is high");
    }

    #[test]
    fn generator_produces_candidates_when_xi_low() {
        let state = triangle_state(vec![3.0, 1.0, 2.0]);
        let gen = CycleAwareGenerator {
            config: CycleAwareConfig {
                xi_activation_threshold: 0.5,
                top_k_edges: 2,
                strategy: CorrectionStrategy::GradientStep { alpha: 0.5 },
            },
            diagnostic: MockDiagnostic(vec![2.0, 2.0, 2.0], 0.3),
        };

        let candidates = gen.generate(&state);

        // 1 bulk + 2 single-edge = 3 candidates
        assert_eq!(candidates.len(), 3);

        assert_eq!(
            candidates[0].operator_id,
            OperatorId::from("cycle_aware.bulk_correction")
        );
        assert!(candidates[0]
            .provenance
            .0
            .contains("corrects 2 worst edges"));

        assert_eq!(
            candidates[1].operator_id,
            OperatorId::from("cycle_aware.single_edge")
        );
        assert_eq!(
            candidates[2].operator_id,
            OperatorId::from("cycle_aware.single_edge")
        );
    }

    #[test]
    fn bulk_correction_moves_state_toward_harmonic() {
        let state = triangle_state(vec![4.0, 0.0, 2.0]);
        let gen = CycleAwareGenerator {
            config: CycleAwareConfig {
                xi_activation_threshold: 0.5,
                top_k_edges: 3,
                strategy: CorrectionStrategy::GradientStep { alpha: 1.0 },
            },
            diagnostic: MockDiagnostic(vec![2.0, 2.0, 2.0], 0.1),
        };

        let candidates = gen.generate(&state);
        let bulk = &candidates[0];

        // With alpha=1.0 on all edges, the corrected state should equal the harmonic
        assert_eq!(
            bulk.state.edge_values,
            vec![2.0, 2.0, 2.0],
            "full step should snap to harmonic"
        );
    }

    // --- Diagnostic validation tests ---

    struct BadDiagnostic;

    impl XiDiagnosticFunctional<GraphState> for BadDiagnostic {
        fn diagnose(&self, _state: &GraphState) -> Result<XiDiagnostic, XiDiagnosticError> {
            Ok(XiDiagnostic {
                harmonic_projection: vec![1.0, 1.0, 1.0],
                xi_value: 0.2,
                witness: XiWitness {
                    edge_distortions: vec![f64::NAN],
                    worst_edges: vec![0],
                    xi_value: 0.2,
                },
            })
        }
    }

    #[test]
    fn invalid_diagnostic_produces_no_candidates() {
        let state = triangle_state(vec![3.0, 1.0, 2.0]);
        let gen = CycleAwareGenerator {
            config: CycleAwareConfig::default(),
            diagnostic: BadDiagnostic,
        };

        assert!(gen.generate(&state).is_empty());
    }

    #[test]
    fn diagnostic_xi_mismatch_produces_no_candidates() {
        struct MismatchDiagnostic;

        impl XiDiagnosticFunctional<GraphState> for MismatchDiagnostic {
            fn diagnose(&self, state: &GraphState) -> Result<XiDiagnostic, XiDiagnosticError> {
                let witness =
                    try_compute_xi_witness(state.edge_values(), &[2.0, 2.0, 2.0], 0.9, 3)?;

                // xi_value intentionally mismatched with witness.xi_value
                Ok(XiDiagnostic {
                    harmonic_projection: vec![2.0, 2.0, 2.0],
                    xi_value: 0.2,
                    witness,
                })
            }
        }

        let state = triangle_state(vec![3.0, 1.0, 2.0]);
        let gen = CycleAwareGenerator {
            config: CycleAwareConfig::default(),
            diagnostic: MismatchDiagnostic,
        };

        assert!(gen.generate(&state).is_empty());
    }

    #[test]
    fn invalid_edge_endpoint_produces_no_candidates() {
        let state = GraphState {
            node_count: 3,
            edges: vec![(0, 99), (1, 2), (2, 0)],
            edge_values: vec![1.0, 1.0, 1.0],
        };

        let gen = CycleAwareGenerator {
            config: CycleAwareConfig::default(),
            diagnostic: MockDiagnostic(vec![0.0, 0.0, 0.0], 0.2),
        };

        assert!(gen.generate(&state).is_empty());
    }
}

#[cfg(test)]
mod l4_boundary_tests_ec7bd15e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordec7bd15e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordec7bd15e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordec7bd15e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordec7bd15e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordec7bd15e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorec7bd15e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorec7bd15e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
