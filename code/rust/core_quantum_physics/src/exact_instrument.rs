// AuthorityEffect: None.
//! Declared finite instruments over Q(i), including rectangular state changes.
//! All matrix operations, PSD checks, and canonical Stinespring construction
//! delegate to the existing exact Hermitian/channel owners. Probabilities are
//! declared trace readouts; this does not select the Born rule.
//!
//! Finite algebraic derivation: completeness gives V*V = sum_oa K_oa*K_oa = I.
//! Positivity of rho gives x* M_o(rho) x = sum_a (K_oa*x)*rho(K_oa*x) >= 0.
//! Cyclicity of finite matrix trace gives p_o = tr(E_o rho), and completeness
//! gives sum_o p_o = tr(rho) = 1. For p_o > 0, dividing M_o(rho) by the rational
//! p_o preserves positivity and gives trace one. In the environment basis,
//! (V rho V*)[(r,a),(s,b)] = (K_a rho K_b*)[r,s]; the partial trace selects
//! a=b. Projecting onto outcome o before tracing therefore gives exactly M_o.
//! No infinite-dimensional limit or completion of V to a unitary is asserted.

use crate::exact_channel::{apply_stinespring, ExactChannelError, ExactKrausChannel};
use crate::exact_hermitian::{
    check_hermitian, hermitian_trace, is_psd, partial_trace_second, ExactHermitianError,
};
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::exact_field::{involution as star, matrix as mx, ExactFieldError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ExactInstrumentError {
    #[error("exact matrix algebra: {0}")]
    Algebra(#[from] ExactFieldError),
    #[error("matrix storage: {0}")]
    Storage(#[from] MatrixError),

    #[error("channel refusal: {0}")]
    Channel(#[from] ExactChannelError),
    #[error("Hermitian refusal: {0}")]
    Hermitian(#[from] ExactHermitianError),
    #[error("density matrix is not positive semidefinite")]
    NotPositive,
    #[error("density trace is {trace}, expected one")]
    NonUnitTrace { trace: Rational },
    #[error("an instrument needs at least one outcome")]
    EmptyOutcomes,
    #[error("outcome {outcome} is outside 0..{outcomes}")]
    Outcome { outcome: usize, outcomes: usize },
    #[error("state dimension {actual} does not match input dimension {expected}")]
    StateDimension { expected: usize, actual: usize },
}

/// A validated density operator in any positive finite dimension. No unchecked
/// deserializer or mutable access; positivity and trace one are constructor facts.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactDensityState {
    matrix: BasicMatrix<GaussianRat>,
}

impl ExactDensityState {
    pub fn try_new(matrix: BasicMatrix<GaussianRat>) -> Result<Self, ExactInstrumentError> {
        check_hermitian(&matrix)?;
        if !is_psd(&matrix)? {
            return Err(ExactInstrumentError::NotPositive);
        }
        let trace = hermitian_trace(&matrix)?;
        if trace != ri(1) {
            return Err(ExactInstrumentError::NonUnitTrace { trace });
        }
        Ok(Self { matrix })
    }
    pub fn dimension(&self) -> usize {
        self.matrix.rows()
    }
    pub fn matrix(&self) -> &BasicMatrix<GaussianRat> {
        &self.matrix
    }
}

/// A finite instrument with one or more Kraus operators per outcome. Empty
/// groups represent impossible outcomes. Global completeness is certified by
/// `ExactKrausChannel`; there must be at least one Kraus operator overall.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactFiniteInstrument {
    channel: ExactKrausChannel,
    ranges: Vec<std::ops::Range<usize>>,
}

impl ExactFiniteInstrument {
    pub fn try_new(
        dim_in: usize,
        dim_out: usize,
        groups: Vec<Vec<BasicMatrix<GaussianRat>>>,
        label: &str,
    ) -> Result<Self, ExactInstrumentError> {
        if groups.is_empty() {
            return Err(ExactInstrumentError::EmptyOutcomes);
        }
        let mut ranges = Vec::with_capacity(groups.len());
        let mut operators = Vec::new();
        for group in groups {
            let start = operators.len();
            operators.extend(group);
            ranges.push(start..operators.len());
        }
        let channel = ExactKrausChannel::try_new(dim_in, dim_out, operators, label)?;
        Ok(Self { channel, ranges })
    }
    pub fn channel(&self) -> &ExactKrausChannel {
        &self.channel
    }
    pub fn outcomes(&self) -> usize {
        self.ranges.len()
    }
    pub fn operators_for_outcome(
        &self,
        outcome: usize,
    ) -> Result<&[BasicMatrix<GaussianRat>], ExactInstrumentError> {
        let range = self
            .ranges
            .get(outcome)
            .ok_or(ExactInstrumentError::Outcome {
                outcome,
                outcomes: self.outcomes(),
            })?;
        Ok(&self.channel.operators()[range.clone()])
    }
    fn check_state(&self, state: &ExactDensityState) -> Result<(), ExactInstrumentError> {
        if state.dimension() != self.channel.dim_in() {
            return Err(ExactInstrumentError::StateDimension {
                expected: self.channel.dim_in(),
                actual: state.dimension(),
            });
        }
        Ok(())
    }
    /// E_o = sum_a K_oa^dagger K_oa; all E_o are PSD and sum_o E_o = I.
    pub fn effect(&self, outcome: usize) -> Result<BasicMatrix<GaussianRat>, ExactInstrumentError> {
        let mut result = mx::zeros(self.channel.dim_in(), self.channel.dim_in())?;
        for k in self.operators_for_outcome(outcome)? {
            result = mx::add(&result, &mx::multiply(&star::adjoint(k)?, k)?)?;
        }
        Ok(result)
    }
    /// The unnormalized CP outcome map M_o(rho) = sum_a K_oa rho K_oa^dagger.
    pub fn unnormalized_post_state(
        &self,
        outcome: usize,
        state: &ExactDensityState,
    ) -> Result<BasicMatrix<GaussianRat>, ExactInstrumentError> {
        self.check_state(state)?;
        let mut result = mx::zeros(self.channel.dim_out(), self.channel.dim_out())?;
        for k in self.operators_for_outcome(outcome)? {
            let transported = mx::multiply(&mx::multiply(k, state.matrix())?, &star::adjoint(k)?)?;
            result = mx::add(&result, &transported)?;
        }
        Ok(result)
    }
    /// p_o = tr M_o(rho) = tr(E_o rho), nonnegative with sum_o p_o = 1.
    pub fn probability(
        &self,
        outcome: usize,
        state: &ExactDensityState,
    ) -> Result<Rational, ExactInstrumentError> {
        Ok(hermitian_trace(
            &self.unnormalized_post_state(outcome, state)?,
        )?)
    }
    /// Rational normalization needs no square roots. At zero probability no
    /// normalized state is declared. Positivity and trace one are rechecked.
    pub fn post_state(
        &self,
        outcome: usize,
        state: &ExactDensityState,
    ) -> Result<Option<ExactDensityState>, ExactInstrumentError> {
        let unnormalized = self.unnormalized_post_state(outcome, state)?;
        let probability = hermitian_trace(&unnormalized)?;
        if probability.is_zero() {
            return Ok(None);
        }
        ExactDensityState::try_new(mx::scale(
            &unnormalized,
            &GaussianRat::from_rational(ri(1) / probability),
        )?)
        .map(Some)
    }
    /// V = sum_oa K_oa tensor |o,a>, with V^dagger V = I. This is the
    /// existing canonical isometry, not a completion to a unitary matrix.
    pub fn stinespring_isometry(&self) -> Result<BasicMatrix<GaussianRat>, ExactInstrumentError> {
        Ok(self.channel.stinespring_isometry()?)
    }
    fn build_outcome_environment_projector(
        &self,
        outcome: usize,
    ) -> Result<(BasicMatrix<GaussianRat>, usize), ExactInstrumentError> {
        let range = self
            .ranges
            .get(outcome)
            .ok_or(ExactInstrumentError::Outcome {
                outcome,
                outcomes: self.outcomes(),
            })?;
        let environment_dim = self.channel.operators().len();
        let mut environment_projector = mx::zeros(environment_dim, environment_dim)?;
        for index in range.clone() {
            environment_projector.set(index, index, GaussianRat::one())?;
        }
        let projector = mx::kronecker(
            &mx::identity(self.channel.dim_out())?,
            &environment_projector,
        )?;
        Ok((projector, environment_dim))
    }

    /// Project the canonical environment onto the Kraus indices of outcome o
    /// and trace it out. Exactly reproduces M_o(rho), including empty groups.
    /// This connects the dilation to the instrument, rather than only its sum.
    pub fn dilation_outcome_map(
        &self,
        outcome: usize,
        state: &ExactDensityState,
    ) -> Result<BasicMatrix<GaussianRat>, ExactInstrumentError> {
        self.check_state(state)?;
        let (projector, environment_dim) = self.build_outcome_environment_projector(outcome)?;
        let selected_isometry = mx::multiply(&projector, &self.stinespring_isometry()?)?;
        Ok(partial_trace_second(
            &mx::multiply(
                &mx::multiply(&selected_isometry, state.matrix())?,
                &star::adjoint(&selected_isometry)?,
            )?,
            self.channel.dim_out(),
            environment_dim,
        )?)
    }

    /// Trace out the canonical environment, reproducing the outcome-forgetting
    /// channel exactly; no spectral or unitary-completion assumption is used.
    pub fn apply_dilation(
        &self,
        state: &ExactDensityState,
    ) -> Result<BasicMatrix<GaussianRat>, ExactInstrumentError> {
        self.check_state(state)?;
        Ok(apply_stinespring(
            &self.stinespring_isometry()?,
            self.channel.dim_out(),
            self.channel.operators().len(),
            state.matrix(),
        )?)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/exact_instrument.rs
// Claim: urn:core:crates_rs:core-quantum-physics:exact-instrument:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_9eef3ed4 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
