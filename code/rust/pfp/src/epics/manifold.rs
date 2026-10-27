//! Constraint pressure, thermodynamic annealing, and grammar termination.
//!
//! `EPIC-OE-SYMGAM-008` asks for a `ConstraintPressureAccumulator`, a
//! `ThermodynamicAnnealer`, a `GrammarTerminationReceiptV1`, and structured
//! prompt topology anchors.
//!
//! # The interesting criterion is 3, and it shapes the whole module
//!
//! > The annealer ranks but never admits. `T(t)` is irreducibly floating-point,
//! > so its output may order candidates and may not decide one. No admission
//! > path reads the temperature.
//!
//! This is the estate's exact-arithmetic law stated honestly rather than
//! absolutely. An exponential decay cannot be computed over the rationals, so
//! the epic does not pretend otherwise -- it confines the float to a role where
//! imprecision cannot change an outcome. A ranking that is one position wrong
//! costs a search a detour. An admission that is one bit wrong is a false
//! certification.
//!
//! Three things enforce it here, and none of them is a comment:
//!
//! 1. **The annealer has no method returning a decision.** It returns a
//!    temperature and an ordering. There is no `admit`, no `is_acceptable`, no
//!    `bool` anywhere on it -- the mutation the epic names has nothing to hook
//!    into without adding a method first.
//! 2. **`admit_terminal` takes only exact rationals.** It cannot read a
//!    temperature because no temperature can be passed to it.
//! 3. **Floats are confined to a marked region** of this file, and a test
//!    asserts they appear nowhere else. Moving one out fails that test.
//!
//! # Pressure is monotone by construction, not by check
//!
//! `Pi(t)` accumulates `sum_i mu_i * ActiveConstraints(s)` over steps. Every
//! `mu_i` is required positive at construction and every active-constraint count
//! is a `u64`, so each increment is non-negative and the sum cannot decrease.
//!
//! There is therefore **no "did it decrease?" guard** -- it could never fire,
//! and sprint 022 removed two of those. The monotonicity is asserted in the
//! tests, where it is a claim about the arithmetic rather than a branch nobody
//! can take.
//!
//! # Termination is bounded, and the bound is arithmetic
//!
//! With a positive floor `mu > 0` and a threshold `Theta`, pressure rises by at
//! least `mu` per step, so termination occurs within `ceil(Theta / mu)` steps.
//! The bound is computed from the floor and the threshold, and the run reports
//! the steps it actually took. A run that exceeds the bound is recorded as an
//! **open residual naming the grammar**, never as a pass.
//!
//! `AuthorityEffect: None`. Pressure forces termination; it does not certify
//! that what terminated was correct.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_44ccc024<T> {
    fn checked_invariant_44ccc024(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_44ccc024<T> for Option<T> {
    #[inline]
    fn checked_invariant_44ccc024(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_44ccc024<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_44ccc024(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::Ratio;
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// The receipt schema this module emits.
pub const TERMINATION_RECEIPT_SCHEMA_V1: &str = "core.symgam.grammar-termination-receipt.v1";

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ManifoldError {
    #[error("constraint {index} has weight {numerator}/{denominator}; the floor must be positive")]
    NonPositiveWeight {
        index: usize,
        numerator: i64,
        denominator: i64,
    },

    #[error("no constraint weights were declared; there is no pressure floor")]
    NoWeights,

    #[error("the termination threshold must be positive")]
    NonPositiveThreshold,

    #[error("run exceeded the bound of {bound} steps on grammar {grammar}")]
    BoundExceeded { bound: u64, grammar: String },

    #[error("the terminal state {state:?} is not legal in grammar {grammar}")]
    IllegalTerminalState { state: String, grammar: String },

    #[error("annealing requires finite initial >= minimum >= 0 and gamma >= 0")]
    InvalidAnnealingSchedule,
}

// ---------------------------------------------------------------------------
// Constraint pressure -- exact
// ---------------------------------------------------------------------------

/// `Pi(t) = sum over steps of sum_i mu_i * ActiveConstraints_i(s)`, exact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConstraintPressureAccumulator {
    weights: Vec<(i64, i64)>,
    /// One entry per step taken, each the pressure *after* that step.
    trace: Vec<(i64, i64)>,
}

impl ConstraintPressureAccumulator {
    /// Declare the constraint weights. Every one must be strictly positive:
    /// that is the floor the termination guarantee rests on.
    pub fn new(weights: &[Ratio<i64>]) -> Result<Self, ManifoldError> {
        if weights.is_empty() {
            return Err(ManifoldError::NoWeights);
        }
        for (index, weight) in weights.iter().enumerate() {
            if *weight <= Ratio::new(0, 1) {
                return Err(ManifoldError::NonPositiveWeight {
                    index,
                    numerator: *weight.numer(),
                    denominator: *weight.denom(),
                });
            }
        }
        Ok(Self {
            weights: weights.iter().map(|w| (*w.numer(), *w.denom())).collect(),
            trace: vec![(0, 1)],
        })
    }

    pub fn weights(&self) -> Vec<Ratio<i64>> {
        self.weights
            .iter()
            .map(|(n, d)| Ratio::new(*n, *d))
            .collect()
    }

    /// The smallest weight -- the per-step floor.
    pub fn floor(&self) -> Ratio<i64> {
        self.weights()
            .into_iter()
            .min()
            .checked_invariant_44ccc024("weights are non-empty by construction")
    }

    pub fn pressure(&self) -> Ratio<i64> {
        let (numerator, denominator) = *self
            .trace
            .last()
            .checked_invariant_44ccc024("the trace always holds the initial zero");
        Ratio::new(numerator, denominator)
    }

    pub fn steps(&self) -> usize {
        self.trace.len() - 1
    }

    pub fn trace(&self) -> Vec<Ratio<i64>> {
        self.trace.iter().map(|(n, d)| Ratio::new(*n, *d)).collect()
    }

    /// Accumulate one generation step.
    ///
    /// `active[i]` is how many instances of constraint `i` were active. Every
    /// term is a positive weight times a non-negative count, so the increment
    /// is non-negative and `Pi` cannot decrease. **No guard checks that** --
    /// it could never fire.
    pub fn step(&mut self, active: &[u64]) -> Ratio<i64> {
        let mut increment = Ratio::new(0, 1);
        for (index, weight) in self.weights().into_iter().enumerate() {
            let count = active.get(index).copied().unwrap_or(0);
            increment += weight * Ratio::new(count as i64, 1);
        }
        let next = self.pressure() + increment;
        self.trace.push((*next.numer(), *next.denom()));
        next
    }
}

// ---------------------------------------------------------------------------
// FLOAT REGION BEGIN -- ranking only, never admission
//
// Every floating-point value in this module lives between these markers, and
// `floats_are_confined_to_the_annealer` asserts it. Criterion 3 permits the
// temperature to order candidates and forbids it from deciding one, so the
// confinement is the enforcement rather than a convention.
// ---------------------------------------------------------------------------

/// `T(p) = max(T_min, T0 * exp(-gamma * p))`, for accumulated pressure `p`.
///
/// Returns a temperature and an ordering. **Nothing here returns a decision**:
/// there is no `bool` on this type, so the mutation criterion 3 names -- letting
/// temperature gate an admission -- has nothing to hook into without first
/// adding a method.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ThermodynamicAnnealer {
    initial: f64,
    gamma: f64,
    minimum: f64,
}

impl ThermodynamicAnnealer {
    pub fn new(initial: f64, gamma: f64) -> Self {
        Self {
            initial,
            gamma,
            minimum: 0.0,
        }
    }

    pub fn with_floor(initial: f64, gamma: f64, minimum: f64) -> Result<Self, ManifoldError> {
        if !initial.is_finite()
            || !gamma.is_finite()
            || !minimum.is_finite()
            || minimum < 0.0
            || initial < minimum
            || gamma < 0.0
        {
            return Err(ManifoldError::InvalidAnnealingSchedule);
        }
        Ok(Self {
            initial,
            gamma,
            minimum,
        })
    }

    pub fn temperature(&self, t: f64) -> f64 {
        (self.initial * (-self.gamma * t).exp()).max(self.minimum)
    }

    /// Read the actual accumulated exact pressure; this conversion only ranks.
    pub fn temperature_for_pressure(&self, accumulator: &ConstraintPressureAccumulator) -> f64 {
        let pressure = accumulator.pressure();
        self.temperature(*pressure.numer() as f64 / *pressure.denom() as f64)
    }

    pub fn rank_at_pressure(
        &self,
        scores: &[f64],
        accumulator: &ConstraintPressureAccumulator,
    ) -> Vec<usize> {
        let pressure = accumulator.pressure();
        self.rank(scores, *pressure.numer() as f64 / *pressure.denom() as f64)
    }

    /// Order candidate indices by score, hottest first, breaking ties by index.
    ///
    /// Returns an **ordering**, never a selection. A caller that wants one
    /// candidate takes the first element and owns that decision itself.
    pub fn rank(&self, scores: &[f64], t: f64) -> Vec<usize> {
        let temperature = self.temperature(t);
        let mut order: Vec<usize> = (0..scores.len()).collect();
        order.sort_by(|left, right| {
            let a = scores[*left] * temperature;
            let b = scores[*right] * temperature;
            b.partial_cmp(&a)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then(left.cmp(right))
        });
        order
    }
}

// ---------------------------------------------------------------------------
// FLOAT REGION END
// ---------------------------------------------------------------------------

/// Whether accumulated pressure has reached the termination threshold.
///
/// Takes only exact rationals. It **cannot** read a temperature, because no
/// temperature can be passed to it -- criterion 3 enforced by the signature
/// rather than by a rule someone has to follow.
pub fn admit_terminal(pressure: Ratio<i64>, threshold: Ratio<i64>) -> bool {
    pressure >= threshold
}

// ---------------------------------------------------------------------------
// Prompt topology anchors
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ContextDelimitersV1 {
    pub open: String,
    pub close: String,
}

impl ContextDelimitersV1 {
    pub fn new(open: &str, close: &str) -> Self {
        Self {
            open: open.to_string(),
            close: close.to_string(),
        }
    }

    pub fn wrap(&self, body: &str) -> String {
        format!("{}{}{}", self.open, body, self.close)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TopologicalAnchorsV1 {
    pub anchors: Vec<String>,
}

impl TopologicalAnchorsV1 {
    pub fn new(anchors: &[&str]) -> Self {
        Self {
            anchors: anchors.iter().map(|a| a.to_string()).collect(),
        }
    }

    /// The anchor block this set renders, in declared order.
    pub fn prefix(&self, delimiters: &ContextDelimitersV1) -> String {
        let mut out = String::new();
        for anchor in &self.anchors {
            out.push_str(&delimiters.wrap(anchor));
            out.push('\n');
        }
        out
    }

    /// Insert every anchor, in declared order. **Idempotent.**
    ///
    /// Criterion 5 requires that inserting twice yield a byte-identical prompt,
    /// so a body already carrying the block is returned unchanged rather than
    /// prefixed again. Appending would make the second insertion a different
    /// document, and a pipeline that re-renders — which is the normal case for
    /// a prompt assembled in stages — would grow a new block per pass.
    pub fn insert_into(&self, body: &str, delimiters: &ContextDelimitersV1) -> String {
        let prefix = self.prefix(delimiters);
        if body.starts_with(&prefix) {
            return body.to_string();
        }
        format!("{prefix}{body}")
    }

    /// How many declared anchors appear in a rendered prompt.
    ///
    /// Counted rather than assumed, so a renderer that dropped one is visible.
    pub fn present_in(&self, rendered: &str, delimiters: &ContextDelimitersV1) -> usize {
        self.anchors
            .iter()
            .filter(|anchor| rendered.contains(&delimiters.wrap(anchor)))
            .count()
    }
}

// ---------------------------------------------------------------------------
// Termination
// ---------------------------------------------------------------------------

/// A grammar for the purposes of termination: a name and the legality rule.
///
/// The legality check is a plain function so the receipt can be validated by a
/// parser that took no part in generation -- criterion 4's independence.
pub type LegalityCheck = fn(&str) -> bool;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GrammarTerminationReceiptV1 {
    pub schema_version: String,
    pub grammar: String,
    pub steps_taken: u64,
    pub step_bound: u64,
    pub floor_numerator: i64,
    pub floor_denominator: i64,
    pub threshold_numerator: i64,
    pub threshold_denominator: i64,
    pub final_pressure_numerator: i64,
    pub final_pressure_denominator: i64,
    pub terminal_state: String,
    pub authority_effect: String,
}

impl GrammarTerminationReceiptV1 {
    pub fn floor(&self) -> Ratio<i64> {
        Ratio::new(self.floor_numerator, self.floor_denominator)
    }

    pub fn final_pressure(&self) -> Ratio<i64> {
        Ratio::new(
            self.final_pressure_numerator,
            self.final_pressure_denominator,
        )
    }

    pub fn threshold(&self) -> Ratio<i64> {
        Ratio::new(self.threshold_numerator, self.threshold_denominator)
    }
}

/// `ceil(threshold / floor)`: the most steps a positive floor can require.
pub fn step_bound(threshold: Ratio<i64>, floor: Ratio<i64>) -> Result<u64, ManifoldError> {
    if threshold <= Ratio::new(0, 1) {
        return Err(ManifoldError::NonPositiveThreshold);
    }
    if floor <= Ratio::new(0, 1) {
        return Err(ManifoldError::NonPositiveWeight {
            index: 0,
            numerator: *floor.numer(),
            denominator: *floor.denom(),
        });
    }
    let quotient = threshold / floor;
    let whole = quotient.numer() / quotient.denom();
    let exact = quotient.numer() % quotient.denom() == 0;
    Ok(if exact {
        whole as u64
    } else {
        (whole + 1) as u64
    })
}

/// Run a generation until pressure admits termination, or exceed the bound.
///
/// `emit` produces the next token given the step index; the caller owns
/// generation. This function owns only the pressure accounting and the bound.
pub fn run_to_termination(
    grammar: &str,
    accumulator: &mut ConstraintPressureAccumulator,
    threshold: Ratio<i64>,
    active_per_step: &[Vec<u64>],
    emit: fn(usize) -> char,
    legality: LegalityCheck,
) -> Result<GrammarTerminationReceiptV1, ManifoldError> {
    let floor = accumulator.floor();
    let bound = step_bound(threshold, floor)?;

    let mut state = String::new();
    let mut steps = 0u64;
    while !admit_terminal(accumulator.pressure(), threshold) {
        if steps >= bound {
            return Err(ManifoldError::BoundExceeded {
                bound,
                grammar: grammar.to_string(),
            });
        }
        let active = active_per_step
            .get(steps as usize)
            .cloned()
            .unwrap_or_else(|| vec![1; accumulator.weights.len()]);
        accumulator.step(&active);
        state.push(emit(steps as usize));
        steps += 1;
    }

    if !legality(&state) {
        return Err(ManifoldError::IllegalTerminalState {
            state,
            grammar: grammar.to_string(),
        });
    }

    let pressure = accumulator.pressure();
    Ok(GrammarTerminationReceiptV1 {
        schema_version: TERMINATION_RECEIPT_SCHEMA_V1.to_string(),
        grammar: grammar.to_string(),
        steps_taken: steps,
        step_bound: bound,
        floor_numerator: *floor.numer(),
        floor_denominator: *floor.denom(),
        threshold_numerator: *threshold.numer(),
        threshold_denominator: *threshold.denom(),
        final_pressure_numerator: *pressure.numer(),
        final_pressure_denominator: *pressure.denom(),
        terminal_state: state,
        authority_effect: "None".to_string(),
    })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

// Origin: engine/crates_rs/pfp/src/epics/manifold.rs
// Claim: urn:core:crates_rs:pfp:manifold:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn ratio(numerator: i64, denominator: i64) -> Ratio<i64> {
        Ratio::new(numerator, denominator)
    }

    fn accumulator() -> ConstraintPressureAccumulator {
        ConstraintPressureAccumulator::new(&[ratio(1, 3), ratio(1, 7), ratio(2, 5)])
            .expect("fixture must build")
    }

    /// Legal iff every character is 'a' -- an independent parser that takes no
    /// part in generation.
    fn all_a(state: &str) -> bool {
        !state.is_empty() && state.chars().all(|c| c == 'a')
    }

    fn emit_a(_step: usize) -> char {
        'a'
    }

    fn emit_b(_step: usize) -> char {
        'b'
    }

    // -- AC1: pressure is non-decreasing, checked pairwise ------------------

    #[test]
    fn pressure_never_decreases_across_a_run() {
        let mut acc = accumulator();
        for step in 0..24u64 {
            acc.step(&[step % 3, step % 5, step % 2]);
        }
        let trace = acc.trace();
        assert_eq!(trace.len(), 25);
        for (index, pair) in trace.windows(2).enumerate() {
            assert!(
                pair[1] >= pair[0],
                "pressure fell at token {index}: {:?} -> {:?}",
                pair[0],
                pair[1]
            );
        }
    }

    #[test]
    fn the_pressure_run_actually_rises() {
        // Without this the monotonicity test above is satisfied by a constant.
        let mut acc = accumulator();
        for step in 0..24u64 {
            acc.step(&[step % 3, step % 5, step % 2]);
        }
        let trace = acc.trace();
        assert!(
            trace.last().expect("nonempty") > trace.first().expect("nonempty"),
            "the fixture must actually accumulate pressure"
        );
        let strict = trace.windows(2).filter(|p| p[1] > p[0]).count();
        assert!(strict > 0, "no step increased the pressure");
    }

    #[test]
    fn a_step_with_no_active_constraints_holds_pressure_flat() {
        // Non-decreasing, not strictly increasing: the boundary the criterion
        // permits.
        let mut acc = accumulator();
        acc.step(&[2, 0, 1]);
        let before = acc.pressure();
        acc.step(&[0, 0, 0]);
        assert_eq!(acc.pressure(), before);
    }

    #[test]
    fn pressure_is_exact_over_the_rationals() {
        // 1/3 + 1/7 + 2/5 = 35/105 + 15/105 + 42/105 = 92/105, a value no
        // binary float represents.
        let mut acc = accumulator();
        acc.step(&[1, 1, 1]);
        assert_eq!(acc.pressure(), ratio(92, 105));
    }

    #[test]
    fn the_accumulator_starts_at_zero_and_counts_its_steps() {
        let mut acc = accumulator();
        assert_eq!(acc.pressure(), ratio(0, 1));
        assert_eq!(acc.steps(), 0);
        acc.step(&[1, 0, 0]);
        assert_eq!(acc.steps(), 1);
    }

    #[test]
    fn a_non_positive_weight_is_refused_and_names_the_index() {
        assert_eq!(
            ConstraintPressureAccumulator::new(&[ratio(1, 2), ratio(0, 1)])
                .expect_err("must refuse"),
            ManifoldError::NonPositiveWeight {
                index: 1,
                numerator: 0,
                denominator: 1
            }
        );
        assert!(matches!(
            ConstraintPressureAccumulator::new(&[ratio(-1, 2)]),
            Err(ManifoldError::NonPositiveWeight { index: 0, .. })
        ));
    }

    #[test]
    fn an_empty_weight_set_is_refused() {
        assert_eq!(
            ConstraintPressureAccumulator::new(&[]).expect_err("must refuse"),
            ManifoldError::NoWeights
        );
    }

    #[test]
    fn the_floor_is_the_smallest_declared_weight() {
        assert_eq!(accumulator().floor(), ratio(1, 7));
    }

    #[test]
    fn missing_active_counts_are_treated_as_zero_not_as_one() {
        let mut acc = accumulator();
        acc.step(&[1]);
        assert_eq!(acc.pressure(), ratio(1, 3));
    }

    // -- AC2: termination is bounded ----------------------------------------

    #[test]
    fn the_step_bound_is_ceiling_of_threshold_over_floor() {
        assert_eq!(step_bound(ratio(1, 1), ratio(1, 4)).expect("ok"), 4);
        assert_eq!(step_bound(ratio(1, 1), ratio(1, 3)).expect("ok"), 3);
        // Non-exact division must round up, not down.
        assert_eq!(step_bound(ratio(5, 2), ratio(1, 1)).expect("ok"), 3);
        assert_eq!(step_bound(ratio(7, 3), ratio(1, 1)).expect("ok"), 3);
    }

    #[test]
    fn a_run_terminates_within_its_bound_and_reports_the_steps() {
        let mut acc = accumulator();
        let receipt = run_to_termination("all-a", &mut acc, ratio(3, 1), &[], emit_a, all_a)
            .expect("must terminate");
        assert!(receipt.steps_taken <= receipt.step_bound);
        assert!(receipt.steps_taken > 0, "a nontrivial run must take steps");
        assert_eq!(receipt.terminal_state.len(), receipt.steps_taken as usize);
    }

    #[test]
    fn an_adversarial_grammar_that_stalls_is_recorded_as_a_residual() {
        // Every step reports zero active constraints, so pressure never rises
        // and the bound is exceeded. The run must name the grammar rather than
        // report a pass.
        let mut acc = accumulator();
        let stalling: Vec<Vec<u64>> = (0..64).map(|_| vec![0, 0, 0]).collect();
        match run_to_termination("stalling", &mut acc, ratio(3, 1), &stalling, emit_a, all_a) {
            Err(ManifoldError::BoundExceeded { bound, grammar }) => {
                assert_eq!(grammar, "stalling");
                assert!(bound > 0);
            }
            other => panic!("expected a bound-exceeded residual, got {other:?}"),
        }
    }

    #[test]
    fn a_zero_floor_cannot_produce_a_bound() {
        assert!(matches!(
            step_bound(ratio(1, 1), ratio(0, 1)),
            Err(ManifoldError::NonPositiveWeight { .. })
        ));
    }

    #[test]
    fn a_non_positive_threshold_is_refused() {
        assert_eq!(
            step_bound(ratio(0, 1), ratio(1, 2)).expect_err("must refuse"),
            ManifoldError::NonPositiveThreshold
        );
    }

    #[test]
    fn a_smaller_floor_gives_a_larger_bound() {
        // The bound must actually depend on the floor.
        let tight = step_bound(ratio(1, 1), ratio(1, 2)).expect("ok");
        let loose = step_bound(ratio(1, 1), ratio(1, 16)).expect("ok");
        assert!(loose > tight, "{loose} should exceed {tight}");
    }

    // -- AC3: the annealer ranks but never admits ---------------------------

    #[test]
    fn floats_are_confined_to_the_annealer() {
        // Criterion 3's enforcement. Every floating-point value in this module
        // lives between the two markers; moving one out fails here.
        let source = include_str!("manifold.rs");
        let implementation = source
            .split("#[cfg(test)]")
            .next()
            .expect("the module must have a non-test half");
        let begin = implementation
            .find("FLOAT REGION BEGIN")
            .expect("the begin marker must exist");
        let end = implementation
            .find("FLOAT REGION END")
            .expect("the end marker must exist");
        assert!(begin < end, "the markers are out of order");

        let outside = format!("{}{}", &implementation[..begin], &implementation[end..]);
        for banned in ["f64", "f32"] {
            assert!(
                !outside.contains(banned),
                "{banned} appears outside the float region"
            );
        }
        // ...and the region really contains floats, or the confinement is
        // vacuous.
        assert!(implementation[begin..end].contains("f64"));
    }

    #[test]
    fn the_admission_function_takes_only_exact_rationals() {
        // It cannot read a temperature because none can be passed to it.
        let source = include_str!("manifold.rs");
        let signature = source
            .split("pub fn admit_terminal(")
            .nth(1)
            .expect("admit_terminal must exist");
        let head = &signature[..signature.find('{').expect("a body must follow")];
        assert!(head.contains("Ratio<i64>"));
        for banned in ["f64", "f32", "Annealer", "temperature"] {
            assert!(
                !head.contains(banned),
                "the admission signature mentions {banned}"
            );
        }
    }

    #[test]
    fn the_annealer_exposes_no_decision() {
        // No method on the annealer returns a bool, so the mutation criterion 3
        // names has nothing to hook into without first adding one.
        let source = include_str!("manifold.rs");
        let block = source
            .split("impl ThermodynamicAnnealer {")
            .nth(1)
            .expect("the impl block must exist");
        let block = &block[..block.find("\n}").expect("the block must close")];
        assert!(
            !block.contains("-> bool"),
            "the annealer returns a decision"
        );
    }

    #[test]
    fn the_temperature_decays() {
        let annealer = ThermodynamicAnnealer::new(10.0, 0.5);
        let hot = annealer.temperature(0.0);
        let warm = annealer.temperature(1.0);
        let cool = annealer.temperature(4.0);
        assert!(hot > warm && warm > cool);
        assert!(cool > 0.0, "an exponential decay never reaches zero");
    }

    #[test]
    fn ranking_orders_by_score_and_breaks_ties_by_index() {
        let annealer = ThermodynamicAnnealer::new(1.0, 0.1);
        assert_eq!(annealer.rank(&[0.1, 0.9, 0.5], 0.0), vec![1, 2, 0]);
        assert_eq!(annealer.rank(&[0.5, 0.5, 0.5], 0.0), vec![0, 1, 2]);
    }

    #[test]
    fn ranking_is_a_permutation_of_every_candidate() {
        let annealer = ThermodynamicAnnealer::new(3.0, 0.7);
        let scores = [0.3, 0.8, 0.1, 0.8, 0.4];
        let mut order = annealer.rank(&scores, 2.0);
        assert_eq!(order.len(), scores.len());
        order.sort_unstable();
        assert_eq!(order, vec![0, 1, 2, 3, 4]);
    }

    #[test]
    fn admission_ignores_temperature_because_it_cannot_see_it() {
        // Behavioural counterpart to the signature test: the same pressure and
        // threshold decide the same way regardless of any annealer state.
        let cold = ThermodynamicAnnealer::new(0.001, 9.0);
        let hot = ThermodynamicAnnealer::new(1000.0, 0.0001);
        assert_ne!(cold.temperature(1.0), hot.temperature(1.0));
        assert!(admit_terminal(ratio(3, 1), ratio(3, 1)));
        assert!(!admit_terminal(ratio(2, 1), ratio(3, 1)));
    }

    #[test]
    fn admission_is_inclusive_at_the_threshold() {
        assert!(admit_terminal(ratio(1, 1), ratio(1, 1)));
        assert!(!admit_terminal(ratio(99, 100), ratio(1, 1)));
    }

    // -- AC4: the terminal state is independently legal ---------------------

    #[test]
    fn a_terminal_state_the_independent_parser_rejects_fails_the_run() {
        let mut acc = accumulator();
        match run_to_termination("all-a", &mut acc, ratio(3, 1), &[], emit_b, all_a) {
            Err(ManifoldError::IllegalTerminalState { state, grammar }) => {
                assert_eq!(grammar, "all-a");
                assert!(state.chars().all(|c| c == 'b'));
            }
            other => panic!("expected an illegality refusal, got {other:?}"),
        }
    }

    #[test]
    fn the_legality_check_takes_no_part_in_generation() {
        // The generator emits from `emit`; legality is a separate function
        // applied afterwards. Shown by the same generation failing under one
        // parser and passing under another.
        fn all_b(state: &str) -> bool {
            !state.is_empty() && state.chars().all(|c| c == 'b')
        }
        let mut first = accumulator();
        assert!(run_to_termination("g", &mut first, ratio(3, 1), &[], emit_b, all_a).is_err());
        let mut second = accumulator();
        assert!(run_to_termination("g", &mut second, ratio(3, 1), &[], emit_b, all_b).is_ok());
    }

    #[test]
    fn the_receipt_records_the_floor_threshold_and_final_pressure() {
        let mut acc = accumulator();
        let receipt =
            run_to_termination("all-a", &mut acc, ratio(3, 1), &[], emit_a, all_a).expect("ok");
        assert_eq!(receipt.floor(), ratio(1, 7));
        assert_eq!(receipt.threshold(), ratio(3, 1));
        assert!(receipt.final_pressure() >= receipt.threshold());
    }

    #[test]
    fn the_receipt_carries_no_authority() {
        let mut acc = accumulator();
        let receipt =
            run_to_termination("all-a", &mut acc, ratio(3, 1), &[], emit_a, all_a).expect("ok");
        assert_eq!(receipt.authority_effect, "None");
        assert_eq!(receipt.schema_version, TERMINATION_RECEIPT_SCHEMA_V1);
    }

    #[test]
    fn the_receipt_round_trips_through_json() {
        let mut acc = accumulator();
        let receipt =
            run_to_termination("all-a", &mut acc, ratio(3, 1), &[], emit_a, all_a).expect("ok");
        let encoded = serde_json::to_string(&receipt).expect("ok");
        assert!(!encoded.contains("0.14285"), "no decimal expansion");
        let decoded: GrammarTerminationReceiptV1 = serde_json::from_str(&encoded).expect("ok");
        assert_eq!(receipt, decoded);
    }

    // -- prompt topology anchors ---------------------------------------------

    #[test]
    fn anchors_are_inserted_in_declared_order() {
        let delimiters = ContextDelimitersV1::new("<<", ">>");
        let anchors = TopologicalAnchorsV1::new(&["alpha", "beta"]);
        let rendered = anchors.insert_into("body", &delimiters);
        assert!(rendered.starts_with("<<alpha>>\n<<beta>>\n"));
        assert!(rendered.ends_with("body"));
        assert!(rendered.find("alpha").expect("present") < rendered.find("beta").expect("present"));
    }

    #[test]
    fn anchor_presence_is_counted_not_assumed() {
        let delimiters = ContextDelimitersV1::new("<<", ">>");
        let anchors = TopologicalAnchorsV1::new(&["alpha", "beta", "gamma"]);
        let rendered = anchors.insert_into("body", &delimiters);
        assert_eq!(anchors.present_in(&rendered, &delimiters), 3);

        // A renderer that dropped one is visible.
        let damaged = rendered.replace("<<beta>>\n", "");
        assert_eq!(anchors.present_in(&damaged, &delimiters), 2);
    }

    #[test]
    fn an_anchor_without_its_delimiters_does_not_count() {
        let delimiters = ContextDelimitersV1::new("<<", ">>");
        let anchors = TopologicalAnchorsV1::new(&["alpha"]);
        assert_eq!(anchors.present_in("alpha appears bare", &delimiters), 0);
    }

    #[test]
    fn delimiters_wrap_exactly() {
        let delimiters = ContextDelimitersV1::new("[", "]");
        assert_eq!(delimiters.wrap("x"), "[x]");
    }

    // -- AC5: insertion is idempotent ---------------------------------------

    #[test]
    fn inserting_twice_yields_a_byte_identical_prompt() {
        let delimiters = ContextDelimitersV1::new("<<", ">>");
        let anchors = TopologicalAnchorsV1::new(&["alpha", "beta"]);
        let once = anchors.insert_into("body", &delimiters);
        let twice = anchors.insert_into(&once, &delimiters);
        assert_eq!(once, twice);
        assert_eq!(once.as_bytes(), twice.as_bytes());
    }

    #[test]
    fn repeated_insertion_never_grows_the_prompt() {
        // A pipeline that re-renders in stages must not accumulate blocks.
        let delimiters = ContextDelimitersV1::new("<<", ">>");
        let anchors = TopologicalAnchorsV1::new(&["alpha", "beta", "gamma"]);
        let mut prompt = anchors.insert_into("body", &delimiters);
        let settled = prompt.clone();
        for _ in 0..5 {
            prompt = anchors.insert_into(&prompt, &delimiters);
            assert_eq!(prompt, settled);
        }
        assert_eq!(anchors.present_in(&prompt, &delimiters), 3);
    }

    #[test]
    fn the_first_insertion_does_change_the_body() {
        // Idempotence must not be achieved by doing nothing.
        let delimiters = ContextDelimitersV1::new("<<", ">>");
        let anchors = TopologicalAnchorsV1::new(&["alpha"]);
        let once = anchors.insert_into("body", &delimiters);
        assert_ne!(once, "body");
        assert!(once.starts_with("<<alpha>>"));
    }

    #[test]
    fn a_body_carrying_a_different_anchor_block_is_still_prefixed() {
        // Only *this* set's own block is recognised, so idempotence is not a
        // blanket "if it looks anchored, leave it".
        let delimiters = ContextDelimitersV1::new("<<", ">>");
        let mine = TopologicalAnchorsV1::new(&["alpha"]);
        let theirs = TopologicalAnchorsV1::new(&["zeta"]);
        let foreign = theirs.insert_into("body", &delimiters);
        let combined = mine.insert_into(&foreign, &delimiters);
        assert!(combined.starts_with("<<alpha>>"));
        assert!(combined.contains("<<zeta>>"));
    }
}
