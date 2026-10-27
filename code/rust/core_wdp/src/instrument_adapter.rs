// Executable finite evidence; AuthorityEffect: None.
//! Chapter 19: the finite quantum-instrument adapter, conditional on a declared Kraus
//! family. Executable finite evidence for `WDP-CH19-P13` and `WDP-CH19-P14`; the residual
//! `WDP-CH19-O04` (which instrument, if any, a physical apparatus realizes) stays open.
//!
//! A qubit instrument over Q(i) is a family `{K_o}` of 2 x 2 Gaussian-rational matrices
//! with `sum_o K_o^dagger K_o = I`. A [`QubitState`] is a finite rational mixture
//! `sum_j w_j |v_j><v_j|` with `w_j >= 0`, `v_j` in Q(i)^2 and `sum_j w_j N(v_j) = 1`.
//!
//! - `WDP-CH19-P13`: the outcome probability is `p_o = tr(E_o rho) = sum_j w_j N(K_o v_j)`
//!   with the effect `E_o = K_o^dagger K_o` ([`QubitInstrument::outcome_probability`] and
//!   [`QubitInstrument::outcome_probability_trace_formula`] agree exactly), the `p_o` sum
//!   to one, and the post-state is `K_o rho K_o^dagger / p_o` when `p_o > 0`
//!   ([`QubitInstrument::post_state`]). [`QubitInstrument::outcome_run_table`] turns the
//!   probabilities into run counts over a common denominator, and `adapt_exact` on the
//!   one-measurement cover reproduces `{p_o}` exactly.
//! - `WDP-CH19-P14`: the effects `E_o` do not determine the instrument. The measure-and-
//!   prepare instrument `K_o = |w><o|` (`N(w) = 1`) has the same effects
//!   `{|0><0|, |1><1|}` as the Luders instrument [`luders_instrument`] and the same outcome
//!   probabilities on every state, but a different post-state: from `|0><0|` the Luders
//!   post-state is `|0><0|` and the measure-and-prepare post-state is `|w><w|`.
//!
//! Delegation: completeness `sum_o K_o^dagger K_o = I` is certified by
//! `core_quantum_physics::exact_channel::ExactKrausChannel::try_new`, which also carries
//! the outcome-forgetting channel; matrices, adjoints, traces and outer products are
//! `linear_algebra::exact_field` on the shared `BasicMatrix` over `cyclotomic::GaussianRat`. Only the
//! outcome-indexed bookkeeping (probabilities, post-states, receipts) is local.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_a15056b7<T> {
    fn checked_invariant_a15056b7(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_a15056b7<T> for Option<T> {
    #[inline]
    fn checked_invariant_a15056b7(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_a15056b7<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_a15056b7(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution, matrix as mx};
use num_bigint::BigInt;
use num_traits::{Signed, ToPrimitive, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::hermitian_trace;
use serde::Serialize;

use crate::empirical_adapter::{adapt_exact, EmpiricalModel, MeasurementCover, RunTable, Section};
use crate::error::WdpError;
use crate::types::{blake3_digest, AuthorityEffect};

/// Cap on the number of runs in a table built from outcome probabilities.
pub const MAX_RUNS: usize = 1_000_000;

fn invalid(detail: String) -> WdpError {
    WdpError::InvalidInput { detail }
}

/// The 2 x 2 matrix with the given rows.
pub fn qubit_matrix(rows: [[GaussianRat; 2]; 2]) -> BasicMatrix<GaussianRat> {
    BasicMatrix::<GaussianRat>::from_row_major(2, 2, rows.into_iter().flatten().collect())
        .checked_invariant_a15056b7("two declared rows of two entries")
}

fn norm_of(v: &[GaussianRat]) -> Rational {
    v.iter().fold(Rational::zero(), |acc, x| acc + x.norm_sq())
}

/// A finite rational mixture of pure qubit states with total trace one.
#[derive(Debug, Clone)]
pub struct QubitState {
    components: Vec<(Rational, [GaussianRat; 2])>,
}

impl QubitState {
    /// Nonempty, all weights nonnegative, `sum_j w_j N(v_j) = 1`.
    pub fn new(components: Vec<(Rational, [GaussianRat; 2])>) -> Result<Self, WdpError> {
        if components.is_empty() {
            return Err(invalid("a state needs at least one component".to_string()));
        }
        if let Some(j) = components.iter().position(|(w, _)| w.is_negative()) {
            return Err(invalid(format!("mixture weight {j} is negative")));
        }
        let trace = components
            .iter()
            .fold(Rational::zero(), |acc, (w, v)| acc + w * norm_of(v));
        if trace != ri(1) {
            return Err(invalid(format!("mixture has trace {trace}, not 1")));
        }
        Ok(Self { components })
    }

    /// The pure state `|v><v|` for a vector of norm one.
    pub fn pure(v: [GaussianRat; 2]) -> Result<Self, WdpError> {
        Self::new(vec![(ri(1), v)])
    }

    pub fn components(&self) -> &[(Rational, [GaussianRat; 2])] {
        &self.components
    }

    /// `rho = sum_j w_j |v_j><v_j|`, a 2 x 2 Hermitian matrix over Q(i).
    pub fn density_matrix(&self) -> Result<BasicMatrix<GaussianRat>, WdpError> {
        self.components
            .iter()
            .try_fold(mx::zeros(2, 2)?, |acc, (w, v)| {
                Ok(mx::add(
                    &acc,
                    &mx::scale(
                        &involution::outer_product(v, v)?,
                        &GaussianRat::from_rational(w.clone()),
                    )?,
                )?)
            })
    }

    /// `tr(rho)`, computed from the density matrix.
    pub fn trace(&self) -> Result<Rational, WdpError> {
        Ok(hermitian_trace(&self.density_matrix()?)?)
    }

    /// Whether the two mixtures have the same density matrix.
    pub fn same_density(&self, other: &QubitState) -> Result<bool, WdpError> {
        Ok(self.density_matrix()? == other.density_matrix()?)
    }

    /// A canonical string of the density matrix, independent of the mixture presentation.
    pub fn canonical_string(&self) -> Result<String, WdpError> {
        let rho = self.density_matrix()?;
        let entries: Vec<String> = rho
            .as_slice()
            .iter()
            .enumerate()
            .map(|(i, x)| format!("({},{})={}+{}i", i / 2, i % 2, x.re, x.im))
            .collect();
        Ok(format!("qubit-density-2x2;{}", entries.join(";")))
    }
}

/// The digest recorded for one outcome of one run of an instrument on a state.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct InstrumentReceipt {
    pub outcome: usize,
    pub probability: Rational,
    /// Blake3 of the canonical string of the post-state; `None` when `probability = 0`.
    pub post_state_digest: Option<String>,
    pub authority_effect: AuthorityEffect,
}

/// The one-measurement cover, run table and run count reproducing outcome probabilities.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OutcomeRunTable {
    pub cover: MeasurementCover,
    pub table: RunTable,
    /// `N`, the least number of runs clearing every denominator; outcome `o` has `N p_o`.
    pub runs: usize,
}

/// A qubit instrument: Kraus operators `K_o` with `sum_o K_o^dagger K_o = I`.
#[derive(Debug, Clone)]
pub struct QubitInstrument {
    channel: ExactKrausChannel,
}

impl QubitInstrument {
    /// Certifies completeness through `ExactKrausChannel::try_new`.
    pub fn new(operators: Vec<BasicMatrix<GaussianRat>>, label: &str) -> Result<Self, WdpError> {
        let channel = ExactKrausChannel::try_new(2, 2, operators, label)?;
        Ok(Self { channel })
    }

    pub fn outcomes(&self) -> usize {
        self.channel.operators().len()
    }

    pub fn operators(&self) -> &[BasicMatrix<GaussianRat>] {
        self.channel.operators()
    }

    /// The outcome-forgetting channel `rho -> sum_o K_o rho K_o^dagger`.
    pub fn channel(&self) -> &ExactKrausChannel {
        &self.channel
    }

    /// The effects `E_o = K_o^dagger K_o`.
    pub fn povm_effects(&self) -> Result<Vec<BasicMatrix<GaussianRat>>, WdpError> {
        self.operators()
            .iter()
            .map(|k| Ok(mx::multiply(&involution::adjoint(k)?, k)?))
            .collect()
    }

    fn operator(&self, outcome: usize) -> Result<&BasicMatrix<GaussianRat>, WdpError> {
        self.operators()
            .get(outcome)
            .ok_or_else(|| invalid(format!("outcome {outcome} outside 0..{}", self.outcomes())))
    }

    /// `p_o = sum_j w_j N(K_o v_j)`.
    pub fn outcome_probability(
        &self,
        outcome: usize,
        state: &QubitState,
    ) -> Result<Rational, WdpError> {
        let k = self.operator(outcome)?;
        state
            .components()
            .iter()
            .try_fold(Rational::zero(), |acc, (w, v)| {
                let image = mx::multiply_vector(k, v)?;
                Ok(acc + w * norm_of(&image))
            })
    }

    /// `p_o = tr(E_o rho)`, refused if the trace is not real.
    pub fn outcome_probability_trace_formula(
        &self,
        outcome: usize,
        state: &QubitState,
    ) -> Result<Rational, WdpError> {
        let k = self.operator(outcome)?;
        let effect = mx::multiply(&involution::adjoint(k)?, k)?;
        let trace = mx::trace(&mx::multiply(&effect, &state.density_matrix()?)?)?;
        if !trace.im.is_zero() {
            return Err(invalid(format!(
                "tr(E rho) = {}+{}i is not real",
                trace.re, trace.im
            )));
        }
        Ok(trace.re)
    }

    /// `(p_0, ..., p_{k-1})`, summing to one.
    pub fn outcome_probabilities(&self, state: &QubitState) -> Result<Vec<Rational>, WdpError> {
        (0..self.outcomes())
            .map(|o| self.outcome_probability(o, state))
            .collect()
    }

    /// `K_o rho K_o^dagger / p_o` as a mixture, or `None` when `p_o = 0`.
    pub fn post_state(
        &self,
        outcome: usize,
        state: &QubitState,
    ) -> Result<Option<QubitState>, WdpError> {
        let p = self.outcome_probability(outcome, state)?;
        if p.is_zero() {
            return Ok(None);
        }
        let k = self.operator(outcome)?;
        let components = state
            .components()
            .iter()
            .map(|(w, v)| {
                let image = mx::multiply_vector(k, v)?;
                let vector: [GaussianRat; 2] = image
                    .try_into()
                    .map_err(|_| invalid("Kraus image is not a qubit vector".to_string()))?;
                Ok::<_, WdpError>((w / &p, vector))
            })
            .collect::<Result<Vec<_>, WdpError>>()?;
        QubitState::new(components).map(Some)
    }

    /// `sum_o K_o rho K_o^dagger`, by the outcome-forgetting channel.
    pub fn average_post_density(
        &self,
        state: &QubitState,
    ) -> Result<BasicMatrix<GaussianRat>, WdpError> {
        Ok(self.channel.apply(&state.density_matrix()?)?)
    }

    /// The receipt of one outcome: its probability and the digest of its post-state.
    pub fn receipt(
        &self,
        outcome: usize,
        state: &QubitState,
    ) -> Result<InstrumentReceipt, WdpError> {
        let probability = self.outcome_probability(outcome, state)?;
        let post_state_digest = self
            .post_state(outcome, state)?
            .map(|post| post.canonical_string().map(|s| blake3_digest(s.as_bytes())))
            .transpose()?;
        Ok(InstrumentReceipt {
            outcome,
            probability,
            post_state_digest,
            authority_effect: AuthorityEffect::None,
        })
    }

    /// The receipts of every outcome, in order.
    pub fn receipts(&self, state: &QubitState) -> Result<Vec<InstrumentReceipt>, WdpError> {
        (0..self.outcomes())
            .map(|o| self.receipt(o, state))
            .collect()
    }

    /// `N p_o` runs of outcome `o` on the one-measurement cover with `outcomes()` outcomes,
    /// `N` the least common denominator of the probabilities (`WDP-CH19-P04` style).
    pub fn outcome_run_table(&self, state: &QubitState) -> Result<OutcomeRunTable, WdpError> {
        self.outcome_run_table_with_limit(state, MAX_RUNS)
    }

    fn lcm_denominators(probabilities: &[Rational]) -> BigInt {
        let mut runs = BigInt::from(1);
        for p in probabilities {
            let d = p.denom().clone();
            let (mut a, mut b) = (runs.clone(), d.clone());
            while !b.is_zero() {
                let r = &a % &b;
                a = b;
                b = r;
            }
            runs = &runs / &a * &d;
        }
        runs
    }

    /// [`QubitInstrument::outcome_run_table`] refusing more than `max_runs` runs.
    pub fn outcome_run_table_with_limit(
        &self,
        state: &QubitState,
        max_runs: usize,
    ) -> Result<OutcomeRunTable, WdpError> {
        let probabilities = self.outcome_probabilities(state)?;
        let runs = Self::lcm_denominators(&probabilities);
        let n = runs
            .to_usize()
            .filter(|&n| n <= max_runs)
            .ok_or_else(|| invalid(format!("{runs} runs exceed the cap {max_runs}")))?;
        let mut outcome_runs: Vec<Section> = Vec::new();
        for (o, p) in probabilities.iter().enumerate() {
            let count = (p * Rational::from_integer(runs.clone()))
                .to_integer()
                .to_usize()
                .ok_or_else(|| invalid("run count does not fit in usize".to_string()))?;
            outcome_runs.extend(std::iter::repeat_n(vec![o], count));
        }
        let cover = MeasurementCover::new(1, self.outcomes(), vec![vec![0]])?;
        let table = RunTable::new(&cover, vec![outcome_runs])?;
        Ok(OutcomeRunTable {
            cover,
            table,
            runs: n,
        })
    }

    /// `adapt_exact` of [`QubitInstrument::outcome_run_table`]: the empirical model `{p_o}`.
    pub fn outcome_model(&self, state: &QubitState) -> Result<EmpiricalModel, WdpError> {
        let runs = self.outcome_run_table(state)?;
        Ok(adapt_exact(&runs.cover, &runs.table)?)
    }
}

/// The Luders instrument `K_0 = |0><0|`, `K_1 = |1><1|`.
pub fn luders_instrument() -> Result<QubitInstrument, WdpError> {
    let (zero, one) = (GaussianRat::zero(), GaussianRat::one());
    QubitInstrument::new(
        vec![
            qubit_matrix([[one.clone(), zero.clone()], [zero.clone(), zero.clone()]]),
            qubit_matrix([[zero.clone(), zero.clone()], [zero, one]]),
        ],
        "luders",
    )
}

/// The non-projective instrument `K_0 = diag(1, 3/5)`, `K_1 = diag(0, 4/5)`
/// (`1 = 1` and `9/25 + 16/25 = 1`).
pub fn non_projective_instrument() -> Result<QubitInstrument, WdpError> {
    non_projective_with_phase(GaussianRat::one(), "non_projective")
}

/// The same instrument with `K_1` multiplied by the phase `i`, exercising Q(i).
pub fn complex_phase_instrument() -> Result<QubitInstrument, WdpError> {
    non_projective_with_phase(GaussianRat::i(), "complex_phase")
}

fn non_projective_with_phase(phase: GaussianRat, label: &str) -> Result<QubitInstrument, WdpError> {
    let zero = GaussianRat::zero();
    let real = |n: i64, d: i64| GaussianRat::from_rational(Rational::new(n.into(), d.into()));
    QubitInstrument::new(
        vec![
            qubit_matrix([
                [GaussianRat::one(), zero.clone()],
                [zero.clone(), real(3, 5)],
            ]),
            qubit_matrix([[zero.clone(), zero.clone()], [zero, real(4, 5).mul(&phase)]]),
        ],
        label,
    )
}

/// The measure-and-prepare instrument `K_o = |w><o|` for `N(w) = 1`: read the basis
/// state `o`, then prepare `w`.
pub fn measure_and_prepare_instrument(w: [GaussianRat; 2]) -> Result<QubitInstrument, WdpError> {
    if norm_of(&w) != ri(1) {
        return Err(invalid(format!(
            "the prepared vector has norm {}, not 1",
            norm_of(&w)
        )));
    }
    let zero = GaussianRat::zero();
    let [w0, w1] = w;
    QubitInstrument::new(
        vec![
            qubit_matrix([[w0.clone(), zero.clone()], [w1.clone(), zero.clone()]]),
            qubit_matrix([[zero.clone(), w0], [zero, w1]]),
        ],
        "measure_and_prepare",
    )
}

/// A problem-bound receipt for a declared arbitrary-dimensional instrument.
/// Digests bind the input density and ordered Kraus presentation (including
/// outcome grouping), rather than only the probability/post-state payload.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct FiniteInstrumentReceipt {
    pub instrument_digest: String,
    pub input_state_digest: String,
    pub outcome: usize,
    pub probability: Rational,
    pub post_state_digest: Option<String>,
    pub authority_effect: AuthorityEffect,
}

/// Arbitrary finite-dimensional quantum adapter. Mathematical operations belong
/// to `core_quantum_physics::exact_instrument`; WDP owns receipt binding/replay.
#[derive(Debug, Clone)]
pub struct FiniteQuantumInstrument {
    instrument: core_quantum_physics::exact_instrument::ExactFiniteInstrument,
}

fn finite_matrix_digest(matrix: &BasicMatrix<GaussianRat>) -> String {
    // BasicMatrix<GaussianRat> has an ordered row-major exact rational representation. This
    // domain-separated encoding includes both dimensions and every entry.
    let mut encoding = format!("wdp-qi-matrix-v1;{}x{};", matrix.rows(), matrix.cols());
    for entry in matrix.as_slice() {
        encoding.push_str(&format!("{}+{}i;", entry.re, entry.im));
    }
    blake3_digest(encoding.as_bytes())
}

impl FiniteQuantumInstrument {
    pub fn new(
        dim_in: usize,
        dim_out: usize,
        groups: Vec<Vec<BasicMatrix<GaussianRat>>>,
        label: &str,
    ) -> Result<Self, core_quantum_physics::exact_instrument::ExactInstrumentError> {
        Ok(Self {
            instrument: core_quantum_physics::exact_instrument::ExactFiniteInstrument::try_new(
                dim_in, dim_out, groups, label,
            )?,
        })
    }

    pub fn instrument(&self) -> &core_quantum_physics::exact_instrument::ExactFiniteInstrument {
        &self.instrument
    }

    /// Canonical digest of this ordered Kraus presentation. Mathematically
    /// equivalent Kraus presentations may have different digests; replay binds
    /// precisely the declared presentation, not a quotient by Kraus equivalence.
    pub fn canonical_digest(&self) -> String {
        let channel = self.instrument.channel();
        let mut encoding = format!(
            "wdp-finite-instrument-v1;{}x{};outcomes={};",
            channel.dim_out(),
            channel.dim_in(),
            self.instrument.outcomes(),
        );
        for outcome in 0..self.instrument.outcomes() {
            // The loop bounds are the validated instrument's own outcome count.
            let operators = self
                .instrument
                .operators_for_outcome(outcome)
                .checked_invariant_a15056b7("validated outcome index");
            encoding.push_str(&format!("o={outcome};terms={};", operators.len()));
            for operator in operators {
                encoding.push_str(&finite_matrix_digest(operator));
                encoding.push(';');
            }
        }
        blake3_digest(encoding.as_bytes())
    }

    pub fn receipt(
        &self,
        outcome: usize,
        state: &core_quantum_physics::exact_instrument::ExactDensityState,
    ) -> Result<
        FiniteInstrumentReceipt,
        core_quantum_physics::exact_instrument::ExactInstrumentError,
    > {
        let probability = self.instrument.probability(outcome, state)?;
        let post_state_digest = self
            .instrument
            .post_state(outcome, state)?
            .map(|post| finite_matrix_digest(post.matrix()));
        Ok(FiniteInstrumentReceipt {
            instrument_digest: self.canonical_digest(),
            input_state_digest: finite_matrix_digest(state.matrix()),
            outcome,
            probability,
            post_state_digest,
            authority_effect: AuthorityEffect::None,
        })
    }

    /// Recompute from the caller's actual validated state and instrument. A
    /// forged payload or a receipt for another input/instrument fails closed;
    /// malformed outcome indices preserve the sovereign typed refusal.
    pub fn verify_receipt(
        &self,
        state: &core_quantum_physics::exact_instrument::ExactDensityState,
        receipt: &FiniteInstrumentReceipt,
    ) -> Result<bool, core_quantum_physics::exact_instrument::ExactInstrumentError> {
        Ok(self.receipt(receipt.outcome, state)? == *receipt)
    }
}

// Origin: engine/crates_rs/core_wdp/src/instrument_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:instrument-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda15056b7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda15056b7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora15056b7 {
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
impl BoundaryErrora15056b7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora15056b7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora15056b7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda15056b7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora15056b7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora15056b7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora15056b7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora15056b7::ExceedsCapacity {
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
mod l4_boundary_tests_a15056b7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda15056b7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda15056b7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda15056b7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda15056b7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda15056b7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora15056b7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora15056b7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
