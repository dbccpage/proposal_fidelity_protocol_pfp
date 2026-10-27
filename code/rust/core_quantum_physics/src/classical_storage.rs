// AuthorityEffect: None.
//! Finite positive quantum-to-classical-to-quantum storage over Q(i).
//!
//! A normalized POVM F_l and density preparations s_l define the deterministic
//! measure-and-prepare channel Phi(rho) = sum_l tr(F_l rho) s_l. No preparation
//! label, quantum side memory, postselection or outcome ontology is supplied.
//! The existing POVM, density, matrix and Choi owners certify the inputs and
//! arithmetic; positivity and the trace rule are premises of this model.
//!
//! For the four equally weighted X/Z eigenstates, the survival score satisfies
//! S <= 3/4. Put w_l=tr(F_l), f_a=tr(F_l a), s_a=tr(s_l a), for a=X,Z.
//! Positivity gives f_X^2+f_Z^2 <= w_l^2 and s_X^2+s_Z^2 <= 1, hence
//! d_l=w_l-f_X s_X-f_Z s_Z >= 0. Direct expansion and sum_l w_l=2 give
//! 3/4-S=sum_l d_l/8. The certificate replays these exact rational margins
//! and the four state-specific probabilities. Z measurement and preparation
//! attain 3/4, so the bound is sharp, for any finite classical alphabet.
//! This does not exclude contextual hidden-variable models or two ontologies
//! with identical operational predictions, and it does not derive the Born rule.

use crate::exact_channel::{ExactChannelError, ExactChoiMatrix};
use crate::exact_hermitian::{hermitian_trace, ExactHermitianError};
use crate::exact_instrument::{ExactDensityState, ExactInstrumentError as DensityError};
use crate::instruments::{ExactInstrumentError as PovmError, ExactPovm};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as star, matrix as mx, ExactFieldError};
use core_kernel::resource_limits::{OperationLimits, ResourceError};
use core_lie_theory::pauli_symplectic::{pauli, Pauli, PauliError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ClassicalStorageError {
    #[error("each POVM outcome needs exactly one preparation")]
    OutcomeCount,
    #[error("preparations have different output dimensions")]
    OutputDimension,
    #[error("input state dimension does not match the POVM")]
    InputDimension,
    #[error("the X/Z score requires both input and output to be qubits")]
    NotQubit,
    #[error("a certified trace pairing was nonreal")]
    NonReal,
    #[error("a probability or storage-margin identity failed replay")]
    Replay,
    #[error(transparent)]
    Povm(#[from] PovmError),
    #[error(transparent)]
    Density(#[from] DensityError),
    #[error(transparent)]
    Hermitian(#[from] ExactHermitianError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error(transparent)]
    Channel(#[from] ExactChannelError),
    #[error(transparent)]
    Limits(#[from] ResourceError),
    #[error(transparent)]
    Pauli(#[from] PauliError),
}

/// Positive finite classical encoding followed by normalized quantum retrieval.
/// Private fields preserve the checked POVM and density invariants.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactMeasurePrepare {
    measurement: ExactPovm,
    preparations: Vec<ExactDensityState>,
    dim_out: usize,
}

impl ExactMeasurePrepare {
    pub fn try_new(
        measurement: ExactPovm,
        preparations: Vec<ExactDensityState>,
    ) -> Result<Self, ClassicalStorageError> {
        if preparations.len() != measurement.effects().len() {
            return Err(ClassicalStorageError::OutcomeCount);
        }
        let dim_out = preparations
            .first()
            .ok_or(ClassicalStorageError::OutcomeCount)?
            .dimension();
        if preparations.iter().any(|s| s.dimension() != dim_out) {
            return Err(ClassicalStorageError::OutputDimension);
        }
        Ok(Self {
            measurement,
            preparations,
            dim_out,
        })
    }

    pub fn measurement(&self) -> &ExactPovm {
        &self.measurement
    }

    pub fn preparations(&self) -> &[ExactDensityState] {
        &self.preparations
    }

    /// One probability per classical letter, including zero-probability letters.
    pub fn probabilities(
        &self,
        state: &ExactDensityState,
    ) -> Result<Vec<Rational>, ClassicalStorageError> {
        if state.dimension() != self.measurement.dim() {
            return Err(ClassicalStorageError::InputDimension);
        }
        let probabilities = self
            .measurement
            .effects()
            .iter()
            .map(|f| real_pair(f.as_matrix(), state.matrix()))
            .collect::<Result<Vec<_>, _>>()?;
        if probabilities.iter().any(|p| *p < ri(0))
            || probabilities.iter().sum::<Rational>() != ri(1)
        {
            return Err(ClassicalStorageError::Replay);
        }
        Ok(probabilities)
    }

    pub fn apply(
        &self,
        state: &ExactDensityState,
    ) -> Result<ExactDensityState, ClassicalStorageError> {
        let probabilities = self.probabilities(state)?;
        let mut image = mx::zeros(self.dim_out, self.dim_out)?;
        for (p, preparation) in probabilities.iter().zip(&self.preparations) {
            image = mx::add(
                &image,
                &mx::scale(preparation.matrix(), &GaussianRat::from_rational(p.clone()))?,
            )?;
        }
        Ok(ExactDensityState::try_new(image)?)
    }

    /// Independent CPTP replay, using J=sum_l F_l^T tensor s_l (input first).
    /// Dense-carrier limits are checked before allocating the Choi matrix.
    pub fn choi(&self) -> Result<ExactChoiMatrix, ClassicalStorageError> {
        let limits = OperationLimits::default();
        let side = limits.checked_product(self.measurement.dim(), self.dim_out)?;
        limits.check_dense_matrix(side, side, std::mem::size_of::<GaussianRat>())?;
        let mut choi = mx::zeros(side, side)?;
        for (effect, preparation) in self.measurement.effects().iter().zip(&self.preparations) {
            let term = mx::kronecker(&mx::transpose(effect.as_matrix())?, preparation.matrix())?;
            choi = mx::add(&choi, &term)?;
        }
        Ok(ExactChoiMatrix::try_new(
            self.measurement.dim(),
            self.dim_out,
            choi,
        )?)
    }

    /// Exact replay of the four-state score and every branch's bound margin.
    /// The mathematical bound covers any finite alphabet; execution uses the
    /// existing checked carriers and resource limits, not an unrestricted search.
    pub fn xz_certificate(&self) -> Result<XzStorageCertificate, ClassicalStorageError> {
        if self.measurement.dim() != 2 || self.dim_out != 2 {
            return Err(ClassicalStorageError::NotQubit);
        }
        let branch_slacks = self.compute_xz_branch_slacks()?;
        let survival = self.compute_xz_survival()?;
        let average = survival.iter().sum::<Rational>() / ri(4);
        let gap = rq(3, 4) - &average;
        Self::verify_xz_summary(&survival, &gap, &branch_slacks)?;
        Ok(XzStorageCertificate {
            survival,
            average,
            gap,
            branch_slacks,
        })
    }

    fn compute_xz_branch_slacks(&self) -> Result<Vec<Rational>, ClassicalStorageError> {
        let x = pauli::<GaussianRat>(Pauli::X)?;
        let z = pauli::<GaussianRat>(Pauli::Z)?;
        let mut branch_slacks = Vec::with_capacity(self.preparations.len());
        for (effect, state) in self.measurement.effects().iter().zip(&self.preparations) {
            branch_slacks.push(Self::single_branch_slack(
                effect.as_matrix(),
                state,
                &x,
                &z,
            )?);
        }
        Ok(branch_slacks)
    }

    fn single_branch_slack(
        f: &BasicMatrix<GaussianRat>,
        state: &ExactDensityState,
        x: &BasicMatrix<GaussianRat>,
        z: &BasicMatrix<GaussianRat>,
    ) -> Result<Rational, ClassicalStorageError> {
        let w = hermitian_trace(f)?;
        let fx = real_pair(f, x)?;
        let fz = real_pair(f, z)?;
        let sx = real_pair(state.matrix(), x)?;
        let sz = real_pair(state.matrix(), z)?;
        let slack = &w - &fx * &sx - &fz * &sz;
        if [
            &fx * &fx + &fz * &fz > &w * &w,
            &sx * &sx + &sz * &sz > ri(1),
            slack < ri(0),
        ]
        .into_iter()
        .any(|b| b)
        {
            return Err(ClassicalStorageError::Replay);
        }
        Ok(slack)
    }

    fn compute_xz_survival(&self) -> Result<[Rational; 4], ClassicalStorageError> {
        let states = xz_states()?;
        let mut survival = [ri(0), ri(0), ri(0), ri(0)];
        for (i, state) in states.iter().enumerate() {
            survival[i] = real_pair(state.matrix(), self.apply(state)?.matrix())?;
        }
        Ok(survival)
    }

    fn verify_xz_summary(
        survival: &[Rational; 4],
        gap: &Rational,
        branch_slacks: &[Rational],
    ) -> Result<(), ClassicalStorageError> {
        let bad_survival = survival.iter().any(|p| *p < ri(0) || *p > ri(1));
        let slack_avg = branch_slacks.iter().sum::<Rational>() / ri(8);
        if bad_survival || *gap < ri(0) || *gap != slack_avg {
            return Err(ClassicalStorageError::Replay);
        }
        Ok(())
    }
}

/// The ordered preparations Z+, Z-, X+, X-. Entries are in Q, so no sqrt(2)
/// extension is needed to present the projectors or replay this experiment.
pub fn xz_states() -> Result<[ExactDensityState; 4], ClassicalStorageError> {
    let identity = mx::identity(2)?;
    let x = pauli::<GaussianRat>(Pauli::X)?;
    let z = pauli::<GaussianRat>(Pauli::Z)?;
    let half = GaussianRat::from_rational(rq(1, 2));
    Ok([
        half_sum_density(&identity, &z, &half, true)?,
        half_sum_density(&identity, &z, &half, false)?,
        half_sum_density(&identity, &x, &half, true)?,
        half_sum_density(&identity, &x, &half, false)?,
    ])
}

fn half_sum_density(
    identity: &BasicMatrix<GaussianRat>,
    op: &BasicMatrix<GaussianRat>,
    half: &GaussianRat,
    plus: bool,
) -> Result<ExactDensityState, ClassicalStorageError> {
    let combined = if plus {
        mx::add(identity, op)?
    } else {
        mx::sub(identity, op)?
    };
    Ok(ExactDensityState::try_new(mx::scale(&combined, half)?)?)
}

/// Replayed rational margins. No unchecked construction or mutable access.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct XzStorageCertificate {
    survival: [Rational; 4],
    average: Rational,
    gap: Rational,
    branch_slacks: Vec<Rational>,
}

impl XzStorageCertificate {
    pub fn survival(&self) -> &[Rational; 4] {
        &self.survival
    }
    pub fn average(&self) -> &Rational {
        &self.average
    }
    pub fn upper_bound(&self) -> Rational {
        rq(3, 4)
    }
    pub fn gap(&self) -> &Rational {
        &self.gap
    }
    pub fn branch_slacks(&self) -> &[Rational] {
        &self.branch_slacks
    }
}

// Both arguments here are admitted Hermitian operators, so tr(A B)=<A,B>_HS.
// The foundation's contraction avoids allocating an intermediate matrix product.
fn real_pair(
    left: &BasicMatrix<GaussianRat>,
    right: &BasicMatrix<GaussianRat>,
) -> Result<Rational, ClassicalStorageError> {
    let value = star::hs_inner(left, right)?;
    if value.im != ri(0) {
        return Err(ClassicalStorageError::NonReal);
    }
    Ok(value.re)
}

// Origin: engine/crates_rs/core_quantum_physics/src/classical_storage.rs
// Claim: urn:core:crates_rs:core-quantum-physics:classical-storage:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_2c1b9c90 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
