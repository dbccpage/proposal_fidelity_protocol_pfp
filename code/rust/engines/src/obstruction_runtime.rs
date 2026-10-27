//! Obstruction-guided runtime contracts.
//!
//! This module is intentionally small and reviewable. It turns the research
//! backlog for an obstruction runtime into executable Rust contracts:
//! generators propose candidates, functionals compute metrics, evaluators issue
//! verdicts, and the runtime records an auditable step trace.
//!
//! This is a candidate-search runtime, not the exact CODA classifier. Its `f64`
//! fields are diagnostic projections, `ObstructionVerdict::Accept` means only
//! "eligible for exact replay", and every `RuntimeStep` has `AuthorityEffect::None`.
//! Exact classification and any later authority gate live in
//! `core_wdp::coda::coda_gtla`.
//!
//! Part A types (ObstructionMetrics, ObstructionVerdict, ObstructionThresholds,
//! ScoreWeights, obstruction_score) live in crate::obstruction_metrics.

// Re-export Part A types for backward compatibility

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_168f3f50;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_168f3f50<T> = std::result::Result<T, BoundaryError_168f3f50>;
pub use crate::obstruction_metrics::{
    obstruction_score, ObstructionMetrics, ObstructionThresholds, ObstructionVerdict, ScoreWeights,
};

/// Computes candidate-ranking metrics for a state.
///
/// These metrics require exact replay before they can support an exact
/// obstruction status.
pub trait ObstructionFunctional<S> {
    fn compute(&self, state: &S) -> ObstructionMetrics;
}

/// Applies runtime policy to already-computed metrics.
pub trait ObstructionEvaluator {
    fn decide(&self, parent: &ObstructionMetrics, child: &ObstructionMetrics)
        -> ObstructionVerdict;
}

/// Default evaluator used by tests and examples.
#[derive(Debug, Clone, PartialEq, Default)]
pub struct DefaultObstructionEvaluator {
    pub thresholds: ObstructionThresholds,
}

impl DefaultObstructionEvaluator {
    pub fn try_new(thresholds: ObstructionThresholds) -> Result<Self, &'static str> {
        thresholds.validate()?;
        Ok(Self { thresholds })
    }

    /// Constructs without validation. Use only when thresholds have already been
    /// validated by a compiler or trusted construction path (e.g. YAML compiler).
    pub fn new_unchecked(thresholds: ObstructionThresholds) -> Self {
        Self { thresholds }
    }

    /// Search `Accept` inside `phi_tol` is not an authority admission.
    pub fn admits_authority(
        &self,
        parent: &ObstructionMetrics,
        child: &ObstructionMetrics,
    ) -> Result<(), &'static str> {
        match self.decide(parent, child) {
            ObstructionVerdict::Accept => Err("FLOAT_PHI_TOLERANCE_IS_NOT_AUTHORITY"),
            _ => Err("OBSTRUCTION_VERDICT_IS_NOT_AUTHORITY"),
        }
    }
}

impl DefaultObstructionEvaluator {
    fn has_excess_noether_drift(&self, child: &ObstructionMetrics) -> bool {
        child
            .noether_drift
            .map(|drift| drift.abs() > self.thresholds.noether_drift_threshold)
            .unwrap_or(false)
    }

    fn is_oscillatory(&self, child: &ObstructionMetrics) -> bool {
        child.gamma_2 > self.thresholds.gamma2_threshold
            || child
                .gamma2_delta
                .map(|delta| delta.abs() > self.thresholds.gamma2_delta_threshold)
                .unwrap_or(false)
    }
}

impl ObstructionEvaluator for DefaultObstructionEvaluator {
    fn decide(
        &self,
        parent: &ObstructionMetrics,
        child: &ObstructionMetrics,
    ) -> ObstructionVerdict {
        // Gate 0: finiteness (parent AND child)
        if !parent.is_finite() || !child.is_finite() {
            return ObstructionVerdict::Invalid;
        }

        // Gate 0b: range validity
        if !parent.is_valid_range() || !child.is_valid_range() {
            return ObstructionVerdict::Invalid;
        }

        if self.has_excess_noether_drift(child) {
            return ObstructionVerdict::Invalid;
        }

        if child.xi < self.thresholds.xi_threshold {
            return ObstructionVerdict::Incoherent;
        }

        if self.is_oscillatory(child) {
            return ObstructionVerdict::Oscillatory;
        }

        if child.phi_1 <= parent.phi_1 {
            ObstructionVerdict::Accept
        } else if child.phi_1 <= parent.phi_1 + self.thresholds.phi_tol {
            ObstructionVerdict::DiagnosticWithinTolerance
        } else {
            ObstructionVerdict::Reject
        }
    }
}

/// Typed operator identifier (prevents accidental field swaps).
#[derive(Debug, Clone, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct OperatorId(pub String);

impl<T: Into<String>> From<T> for OperatorId {
    fn from(s: T) -> Self {
        Self(s.into())
    }
}

impl std::fmt::Display for OperatorId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(f)
    }
}

/// Typed provenance tag for blue-team replay.
#[derive(Debug, Clone, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct Provenance(pub String);

impl<T: Into<String>> From<T> for Provenance {
    fn from(s: T) -> Self {
        Self(s.into())
    }
}

impl std::fmt::Display for Provenance {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(f)
    }
}

/// Candidate state with provenance for blue-team replay.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct Candidate<S> {
    pub state: S,
    pub operator_id: OperatorId,
    pub provenance: Provenance,
}

impl<S> Candidate<S> {
    pub fn new(
        state: S,
        operator_id: impl Into<OperatorId>,
        provenance: impl Into<Provenance>,
    ) -> Self {
        Self {
            state,
            operator_id: operator_id.into(),
            provenance: provenance.into(),
        }
    }
}

/// Produces candidate states from the current state.
pub trait CandidateGenerator<S> {
    fn generate(&self, state: &S) -> Vec<Candidate<S>>;
}

/// Auditable result for one candidate.
#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct EvaluatedCandidate<S> {
    pub candidate_index: usize,
    pub candidate: Candidate<S>,
    pub metrics: ObstructionMetrics,
    pub verdict: ObstructionVerdict,
    pub score: f64,
}

/// Auditable result for one runtime step.
#[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct RuntimeStep<S> {
    pub step_index: usize,
    pub parent_metrics: ObstructionMetrics,
    pub evaluated: Vec<EvaluatedCandidate<S>>,
    pub selected: Option<EvaluatedCandidate<S>>,
}

impl<S> RuntimeStep<S> {
    /// Candidate selection is diagnostic-only, including on acceptance.
    /// Authorization requires the separate authenticated host promotion path;
    /// exact replay and certification remain evidence-only inputs to that path.
    pub fn authority_effect(&self) -> core_types::authority::AuthorityEffect {
        core_types::authority::AuthorityEffect::None
    }
}
/// Selector policy: chooses among accepted candidates.
///
/// Factored out of the runtime to allow swappable selection strategies
/// (best-score, MCTS, beam, stable-first, etc.).
pub trait CandidateSelector<S> {
    fn select(&self, evaluated: &[EvaluatedCandidate<S>]) -> Option<EvaluatedCandidate<S>>;
}

/// Default selector: picks the accepted candidate with the highest score.
pub struct BestScoreSelector;

impl<S: Clone> CandidateSelector<S> for BestScoreSelector {
    fn select(&self, evaluated: &[EvaluatedCandidate<S>]) -> Option<EvaluatedCandidate<S>> {
        select_best_accepted(evaluated)
    }
}

/// Minimal obstruction-guided runtime.
///
/// The runtime does not compute metrics itself and does not hide rejected
/// candidates. That makes the behavior suitable for:
/// - red-team rejection tests,
/// - green-team descent and scoring tests,
/// - blue-team provenance and replay checks.
pub struct ObstructionRuntime<S, F, E, G, Sel = BestScoreSelector>
where
    S: Clone,
    F: ObstructionFunctional<S>,
    E: ObstructionEvaluator,
    G: CandidateGenerator<S>,
    Sel: CandidateSelector<S>,
{
    current_state: S,
    functional: F,
    evaluator: E,
    generator: G,
    selector: Sel,
    weights: ScoreWeights,
    step_index: usize,
    trace: Vec<RuntimeStep<S>>,
}

impl<S, F, E, G> ObstructionRuntime<S, F, E, G, BestScoreSelector>
where
    S: Clone,
    F: ObstructionFunctional<S>,
    E: ObstructionEvaluator,
    G: CandidateGenerator<S>,
{
    pub fn try_new(
        seed_state: S,
        functional: F,
        evaluator: E,
        generator: G,
        weights: ScoreWeights,
    ) -> Result<Self, &'static str> {
        weights.validate()?;
        Ok(Self {
            current_state: seed_state,
            functional,
            evaluator,
            generator,
            selector: BestScoreSelector,
            weights,
            step_index: 0,
            trace: Vec::new(),
        })
    }

    /// Constructs without validation. Use only when weights have already been
    /// validated by a compiler or trusted construction path.
    pub fn new_unchecked(
        seed_state: S,
        functional: F,
        evaluator: E,
        generator: G,
        weights: ScoreWeights,
    ) -> Self {
        Self {
            current_state: seed_state,
            functional,
            evaluator,
            generator,
            selector: BestScoreSelector,
            weights,
            step_index: 0,
            trace: Vec::new(),
        }
    }
}

impl<S, F, E, G, Sel> ObstructionRuntime<S, F, E, G, Sel>
where
    S: Clone,
    F: ObstructionFunctional<S>,
    E: ObstructionEvaluator,
    G: CandidateGenerator<S>,
    Sel: CandidateSelector<S>,
{
    pub fn try_with_selector(
        seed_state: S,
        functional: F,
        evaluator: E,
        generator: G,
        selector: Sel,
        weights: ScoreWeights,
    ) -> Result<Self, &'static str> {
        weights.validate()?;
        Ok(Self {
            current_state: seed_state,
            functional,
            evaluator,
            generator,
            selector,
            weights,
            step_index: 0,
            trace: Vec::new(),
        })
    }

    /// Constructs without validation. Use only when weights have already been
    /// validated by a compiler or trusted construction path.
    pub fn with_selector_unchecked(
        seed_state: S,
        functional: F,
        evaluator: E,
        generator: G,
        selector: Sel,
        weights: ScoreWeights,
    ) -> Self {
        Self {
            current_state: seed_state,
            functional,
            evaluator,
            generator,
            selector,
            weights,
            step_index: 0,
            trace: Vec::new(),
        }
    }

    pub fn current_state(&self) -> &S {
        &self.current_state
    }

    pub fn step_index(&self) -> usize {
        self.step_index
    }

    pub fn trace(&self) -> &[RuntimeStep<S>] {
        &self.trace
    }

    pub fn step(&mut self) -> RuntimeStep<S> {
        let parent_metrics = self.functional.compute(&self.current_state);
        let mut evaluated = Vec::new();

        for (candidate_index, candidate) in self
            .generator
            .generate(&self.current_state)
            .into_iter()
            .enumerate()
        {
            let metrics = self.functional.compute(&candidate.state);
            let verdict = self.evaluator.decide(&parent_metrics, &metrics);
            let score = match verdict {
                ObstructionVerdict::Invalid => f64::NEG_INFINITY,
                _ => obstruction_score(&metrics, self.weights),
            };

            evaluated.push(EvaluatedCandidate {
                candidate_index,
                candidate,
                metrics,
                verdict,
                score,
            });
        }

        let selected = self.selector.select(&evaluated);

        if let Some(next) = &selected {
            self.current_state = next.candidate.state.clone();
        }

        let step = RuntimeStep {
            step_index: self.step_index,
            parent_metrics,
            evaluated,
            selected,
        };
        self.step_index += 1;
        self.trace.push(step.clone());
        step
    }
}

fn select_best_accepted<S: Clone>(
    evaluated: &[EvaluatedCandidate<S>],
) -> Option<EvaluatedCandidate<S>> {
    let mut best = None;

    for candidate in evaluated
        .iter()
        .filter(|candidate| candidate.verdict.is_accepted() && candidate.score.is_finite())
    {
        let replace = best
            .as_ref()
            .map(|existing: &EvaluatedCandidate<S>| candidate.score > existing.score)
            .unwrap_or(true);

        if replace {
            best = Some(candidate.clone());
        }
    }

    best
}

// Origin: engine/crates_rs/engines/src/obstruction_runtime.rs
// Claim: urn:core:crates_rs:engines:obstruction-runtime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]
    struct ReviewState {
        label: &'static str,
        metrics: ObstructionMetrics,
    }

    struct StateFunctional;

    impl ObstructionFunctional<ReviewState> for StateFunctional {
        fn compute(&self, state: &ReviewState) -> ObstructionMetrics {
            state.metrics.clone()
        }
    }

    struct ReviewGenerator;

    impl CandidateGenerator<ReviewState> for ReviewGenerator {
        fn generate(&self, _state: &ReviewState) -> Vec<Candidate<ReviewState>> {
            vec![
                Candidate::new(
                    ReviewState {
                        label: "accepted_descent",
                        metrics: ObstructionMetrics::new(0.6, 0.2, 0.9),
                    },
                    "green.descent",
                    "lowers phi_1 while preserving gamma_2 and xi",
                ),
                Candidate::new(
                    ReviewState {
                        label: "accepted_balanced",
                        metrics: ObstructionMetrics::new(0.55, 0.1, 0.95),
                    },
                    "green.balanced",
                    "best scalar score among accepted candidates",
                ),
                Candidate::new(
                    ReviewState {
                        label: "oscillatory",
                        metrics: ObstructionMetrics::new(0.2, 9.0, 0.95),
                    },
                    "red.gamma2",
                    "should be rejected by stability gate",
                ),
                Candidate::new(
                    ReviewState {
                        label: "incoherent",
                        metrics: ObstructionMetrics::new(0.1, 0.1, 0.05),
                    },
                    "red.xi",
                    "should be rejected by coherence gate",
                ),
            ]
        }
    }

    fn evaluator() -> DefaultObstructionEvaluator {
        DefaultObstructionEvaluator::try_new(ObstructionThresholds {
            phi_tol: 1e-9,
            gamma2_threshold: 1.0,
            gamma2_delta_threshold: 0.5,
            noether_drift_threshold: 0.1,
            xi_threshold: 0.25,
        })
        .unwrap()
    }

    #[test]
    fn red_team_verdicts_cover_invalid_oscillatory_incoherent_and_reject() {
        let parent = ObstructionMetrics::new(1.0, 0.1, 0.9);
        let evaluator = evaluator();

        let invalid = ObstructionMetrics::new(f64::NAN, 0.1, 0.9);
        assert_eq!(
            evaluator.decide(&parent, &invalid),
            ObstructionVerdict::Invalid
        );

        let drift = ObstructionMetrics::new(0.5, 0.1, 0.9).with_noether_drift(0.2);
        assert_eq!(
            evaluator.decide(&parent, &drift),
            ObstructionVerdict::Invalid
        );

        let incoherent = ObstructionMetrics::new(0.5, 0.1, 0.1);
        assert_eq!(
            evaluator.decide(&parent, &incoherent),
            ObstructionVerdict::Incoherent
        );

        let oscillatory = ObstructionMetrics::new(0.5, 2.0, 0.9);
        assert_eq!(
            evaluator.decide(&parent, &oscillatory),
            ObstructionVerdict::Oscillatory
        );

        let gamma_delta = ObstructionMetrics::new(0.5, 0.1, 0.9).with_gamma2_delta(0.75);
        assert_eq!(
            evaluator.decide(&parent, &gamma_delta),
            ObstructionVerdict::Oscillatory
        );

        let worse_phi = ObstructionMetrics::new(1.1, 0.1, 0.9);
        assert_eq!(
            evaluator.decide(&parent, &worse_phi),
            ObstructionVerdict::Reject
        );

        let same = ObstructionMetrics::new(1.0, 0.1, 0.9);
        assert_eq!(evaluator.decide(&parent, &same), ObstructionVerdict::Accept);
        let inside = ObstructionMetrics::new(1.0 + 1e-12, 0.1, 0.9);
        assert_eq!(
            evaluator.decide(&parent, &inside),
            ObstructionVerdict::DiagnosticWithinTolerance
        );
        assert_eq!(
            evaluator.admits_authority(&parent, &inside),
            Err("OBSTRUCTION_VERDICT_IS_NOT_AUTHORITY")
        );
        assert_eq!(
            evaluator.admits_authority(&parent, &same),
            Err("FLOAT_PHI_TOLERANCE_IS_NOT_AUTHORITY")
        );
        assert_eq!(
            evaluator.admits_authority(&parent, &worse_phi),
            Err("OBSTRUCTION_VERDICT_IS_NOT_AUTHORITY")
        );
    }

    #[test]
    fn blue_team_trace_keeps_provenance_and_selected_transition() {
        let seed = ReviewState {
            label: "root",
            metrics: ObstructionMetrics::new(1.0, 0.1, 0.9),
        };
        let weights = ScoreWeights {
            lambda_gamma: 0.5,
            lambda_xi: 0.25,
        };
        let mut runtime = ObstructionRuntime::try_new(
            seed,
            StateFunctional,
            evaluator(),
            ReviewGenerator,
            weights,
        )
        .unwrap();

        let step = runtime.step();

        assert_eq!(step.evaluated.len(), 4);
        assert!(matches!(
            step.authority_effect(),
            core_types::authority::AuthorityEffect::None
        ));
        assert_eq!(
            step.selected
                .as_ref()
                .map(|selected| selected.candidate.state.label),
            Some("accepted_balanced")
        );
        assert_eq!(runtime.current_state().label, "accepted_balanced");
        assert_eq!(runtime.trace().len(), 1);
        assert_eq!(step.step_index, 0);
        assert!(step
            .evaluated
            .iter()
            .any(
                |candidate| candidate.candidate.operator_id == OperatorId::from("red.gamma2")
                    && candidate.verdict == ObstructionVerdict::Oscillatory
            ));
        assert!(step
            .selected
            .as_ref()
            .unwrap()
            .candidate
            .provenance
            .0
            .contains("best scalar score"));

        let serialized =
            serde_json::to_string(&step).expect("finite review traces should serialize for replay");
        assert!(serialized.contains("green.balanced"));
    }

    #[test]
    fn invalid_parent_metrics_return_invalid() {
        let parent = ObstructionMetrics::new(f64::NAN, 0.1, 0.9);
        let child = ObstructionMetrics::new(0.5, 0.1, 0.9);
        assert_eq!(
            evaluator().decide(&parent, &child),
            ObstructionVerdict::Invalid
        );
    }

    #[test]
    fn xi_out_of_range_is_invalid() {
        let parent = ObstructionMetrics::new(1.0, 0.1, 0.9);
        let child = ObstructionMetrics::new(0.5, 0.1, 1.5);
        assert_eq!(
            evaluator().decide(&parent, &child),
            ObstructionVerdict::Invalid
        );
    }

    #[test]
    fn negative_obstruction_metric_is_invalid() {
        let parent = ObstructionMetrics::new(1.0, 0.1, 0.9);
        let child = ObstructionMetrics::new(-0.1, 0.1, 0.9);
        assert_eq!(
            evaluator().decide(&parent, &child),
            ObstructionVerdict::Invalid
        );
    }

    #[test]
    fn step_index_increments() {
        let seed = ReviewState {
            label: "root",
            metrics: ObstructionMetrics::new(1.0, 0.1, 0.9),
        };
        let weights = ScoreWeights::default();
        let mut runtime = ObstructionRuntime::try_new(
            seed,
            StateFunctional,
            evaluator(),
            ReviewGenerator,
            weights,
        )
        .unwrap();

        let s0 = runtime.step();
        let s1 = runtime.step();
        assert_eq!(s0.step_index, 0);
        assert_eq!(s1.step_index, 1);
        assert_eq!(runtime.step_index(), 2);
    }

    #[test]
    fn evaluator_try_new_rejects_invalid_thresholds() {
        let mut thresholds = ObstructionThresholds::default();
        thresholds.xi_threshold = 2.0;

        assert!(DefaultObstructionEvaluator::try_new(thresholds).is_err());
    }

    #[test]
    fn runtime_try_new_rejects_invalid_weights() {
        let seed = ReviewState {
            label: "root",
            metrics: ObstructionMetrics::new(1.0, 0.1, 0.9),
        };

        let weights = ScoreWeights {
            lambda_gamma: f64::NAN,
            lambda_xi: 0.25,
        };

        let runtime = ObstructionRuntime::try_new(
            seed,
            StateFunctional,
            evaluator(),
            ReviewGenerator,
            weights,
        );

        assert!(runtime.is_err());
    }

    #[test]
    fn invalid_child_metrics_get_neg_infinity_score() {
        struct BadGenerator;

        impl CandidateGenerator<ReviewState> for BadGenerator {
            fn generate(&self, _state: &ReviewState) -> Vec<Candidate<ReviewState>> {
                vec![Candidate::new(
                    ReviewState {
                        label: "bad",
                        metrics: ObstructionMetrics::new(f64::NAN, 0.1, 0.9),
                    },
                    "bad.metrics",
                    "invalid metric candidate",
                )]
            }
        }

        let seed = ReviewState {
            label: "root",
            metrics: ObstructionMetrics::new(1.0, 0.1, 0.9),
        };

        let mut runtime = ObstructionRuntime::try_new(
            seed,
            StateFunctional,
            evaluator(),
            BadGenerator,
            ScoreWeights::default(),
        )
        .unwrap();

        let step = runtime.step();
        assert_eq!(step.evaluated[0].verdict, ObstructionVerdict::Invalid);
        assert_eq!(step.evaluated[0].score, f64::NEG_INFINITY);
    }
}
