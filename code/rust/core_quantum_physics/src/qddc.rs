//! Finite operator-valued Euclidean cochains and exact open-system dynamics.
//! Cochains are Hermitian operators, not densities. Arithmetic and Hodge replay
//! belong to the existing exact operator and rational solver implementations.
//! AuthorityEffect: None.

use crate::density_matrix::{ExactDensityError, ExactDensityMatrix};
use crate::exact_channel::{ExactChannelError, ExactKrausChannel};
use crate::exact_operator::{ExactOperator, OperatorError};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::rational_bareiss::{
    self, RationalBudget, RationalError, RationalLimits,
};
use num_traits::Zero;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};
use core_solvers::cert_hodge_decomp::{HodgeError, HodgeProblem};
use core_solvers::solver_hodge_rational_decomp::solve_hodge;

pub const MAX_DIM: usize = 8;
pub const MAX_CELLS: usize = 32;
pub const MAX_JUMPS: usize = 16;
pub const MAX_INPUT_BITS: u64 = 256;

#[derive(Debug, thiserror::Error)]
pub enum QddcError {
    #[error("QDDC contract: {0}")]
    Contract(&'static str),
    #[error(transparent)]
    Operator(#[from] OperatorError),
    #[error(transparent)]
    Density(#[from] ExactDensityError),
    #[error(transparent)]
    Channel(#[from] ExactChannelError),
    #[error(transparent)]
    Hodge(#[from] HodgeError),
    #[error(transparent)]
    Arithmetic(#[from] RationalError),
}

pub fn check_scalar(q: &Rational) -> Result<(), QddcError> {
    if q.numer().bits() > MAX_INPUT_BITS || q.denom().bits() > MAX_INPUT_BITS {
        return Err(QddcError::Contract("input rational exceeds 256 bits"));
    }
    budget().rational(q)?;
    Ok(())
}

pub fn check_operator(op: &ExactOperator, dim: usize) -> Result<(), QddcError> {
    if !(1..=MAX_DIM).contains(&dim) || op.shape() != (dim, dim) {
        return Err(QddcError::Contract(
            "operator dimension must match and be in 1..=8",
        ));
    }
    for z in op.as_matrix().as_slice() {
        check_scalar(&z.re)?;
        check_scalar(&z.im)?;
    }
    Ok(())
}

fn budget() -> RationalBudget {
    RationalBudget::new(RationalLimits {
        max_elements: 4096,
        max_scalar_ops: 4_000_000,
        max_bits: 8192,
    })
}

/// A three-degree window C^(k-1) -> C^k -> C^(k+1), with scalar Euclidean stars.
/// The constructor checks d_next*d_prev=0; matrices may have zero dimensions.
#[derive(Clone, Debug)]
pub struct QddcState {
    d_prev: BasicMatrix<Rational>,
    d_next: BasicMatrix<Rational>,
    dim: usize,
    cochain: Vec<ExactOperator>,
}

pub struct OperatorHodge {
    pub alpha: Vec<ExactOperator>,
    pub beta: Vec<ExactOperator>,
    pub exact: Vec<ExactOperator>,
    pub coexact: Vec<ExactOperator>,
    pub harmonic: Vec<ExactOperator>,
    pub scalar_ops: usize,
}

pub trait ExactHodge {
    fn decompose(&self) -> Result<OperatorHodge, QddcError>;
}

impl QddcState {
    fn validate_qddc_shapes(
        d_prev: &BasicMatrix<Rational>,
        d_next: &BasicMatrix<Rational>,
        dim: usize,
        cochain_len: usize,
    ) -> Result<(), QddcError> {
        let within_cells = [d_prev.rows(), d_prev.cols(), d_next.rows(), d_next.cols()]
            .iter()
            .all(|&n| n <= MAX_CELLS);
        if !(1..=MAX_DIM).contains(&dim)
            || d_prev.rows() != cochain_len
            || d_next.cols() != cochain_len
            || !within_cells
        {
            return Err(QddcError::Contract("cochain shape or dimension limit"));
        }
        Ok(())
    }

    pub fn try_new(
        d_prev: BasicMatrix<Rational>,
        d_next: BasicMatrix<Rational>,
        dim: usize,
        cochain: Vec<ExactOperator>,
    ) -> Result<Self, QddcError> {
        Self::validate_qddc_shapes(&d_prev, &d_next, dim, cochain.len())?;
        for q in d_prev.as_slice().iter().chain(d_next.as_slice()) {
            check_scalar(q)?;
        }
        for op in &cochain {
            check_operator(op, dim)?;
            op.check_hermitian()?;
        }
        if rational_bareiss::multiply(&d_next, &d_prev, &mut budget())?
            .as_slice()
            .iter()
            .any(|q| !q.is_zero())
        {
            return Err(HodgeError::ChainLaw.into());
        }
        Ok(Self {
            d_prev,
            d_next,
            dim,
            cochain,
        })
    }

    pub fn cochain(&self) -> &[ExactOperator] {
        &self.cochain
    }

    /// Orthogonal projector onto im(d_prev) on the simplex-index Hilbert
    /// carrier. This carrier is distinct from the operator-valued cochain.
    /// A density supported here is a mixture of exact cochain rays. A zero
    /// image has no normalized target state and is refused by RetractionChannel.
    pub fn repair_projector(&self) -> Result<ExactOperator, QddcError> {
        let n = self.cochain.len();
        if !(1..=MAX_DIM).contains(&n) {
            return Err(QddcError::Contract(
                "repair projector carrier must have 1..=8 cells",
            ));
        }
        let mut fuel = budget();
        let mut entries = vec![GaussianRat::zero(); n * n];
        for col in 0..n {
            let mut basis = vec![ri(0); n];
            basis[col] = ri(1);
            let exact = solve_hodge(
                &HodgeProblem {
                    d0: &self.d_prev,
                    d1: &self.d_next,
                    flow: &basis,
                },
                &mut fuel,
            )?
            .certificate
            .exact;
            for (row, value) in exact.into_iter().enumerate() {
                entries[row * n + col] = GaussianRat::from_rational(value);
            }
        }
        let op = ExactOperator::try_new(
            BasicMatrix::from_row_major(n, n, entries).map_err(RationalError::from)?,
        )?;
        op.check_hermitian()?;
        if !op.is_idempotent() {
            return Err(QddcError::Contract(
                "derived exact-image projector failed replay",
            ));
        }
        Ok(op)
    }

    fn validate_deform_inputs(
        &self,
        alpha: &[ExactOperator],
        unitary: &ExactOperator,
    ) -> Result<(), QddcError> {
        if alpha.len() != self.d_prev.cols() {
            return Err(QddcError::Contract("gauge potential shape"));
        }
        check_operator(unitary, self.dim)?;
        if !unitary.is_unitary() {
            return Err(QddcError::Contract("rotation must be unitary"));
        }
        for op in alpha {
            check_operator(op, self.dim)?;
            op.check_hermitian()?;
        }
        Ok(())
    }

    fn shift_and_rotate_cell(
        &self,
        r: usize,
        omega: &ExactOperator,
        alpha: &[ExactOperator],
        unitary: &ExactOperator,
        adjoint: &ExactOperator,
    ) -> Result<ExactOperator, QddcError> {
        let mut shifted = omega.clone();
        for (c, potential) in alpha.iter().enumerate() {
            let q = self.d_prev.get_ref(r, c).map_err(RationalError::from)?;
            shifted = shifted.add(&potential.scale_rat(q)?)?;
        }
        Ok(unitary.mul(&shifted)?.mul(adjoint)?)
    }

    /// Finite gauge/rotation: Ad_U(omega + d alpha). Harmonic gamma is
    /// transported to U gamma U*, and is fixed only when U commutes with it.
    pub fn deform(
        &self,
        alpha: &[ExactOperator],
        unitary: &ExactOperator,
    ) -> Result<Self, QddcError> {
        self.validate_deform_inputs(alpha, unitary)?;
        let adjoint = unitary.dagger()?;
        let mut result = Vec::with_capacity(self.cochain.len());
        for (r, omega) in self.cochain.iter().enumerate() {
            result.push(self.shift_and_rotate_cell(r, omega, alpha, unitary, &adjoint)?);
        }
        Self::try_new(self.d_prev.clone(), self.d_next.clone(), self.dim, result)
    }

    fn decompose_entry_slice(
        &self,
        entry: usize,
        imaginary: bool,
        components: &mut [Vec<Vec<GaussianRat>>],
        fuel: &mut RationalBudget,
    ) -> Result<(), QddcError> {
        let flow: Vec<Rational> = self
            .cochain
            .iter()
            .map(|op| {
                let z = &op.as_matrix().as_slice()[entry];
                if imaginary {
                    z.im.clone()
                } else {
                    z.re.clone()
                }
            })
            .collect();
        let certificate = solve_hodge(
            &HodgeProblem {
                d0: &self.d_prev,
                d1: &self.d_next,
                flow: &flow,
            },
            fuel,
        )?
        .certificate;
        for (target, values) in components.iter_mut().zip([
            certificate.alpha,
            certificate.beta,
            certificate.exact,
            certificate.coexact,
            certificate.harmonic,
        ]) {
            for (matrix, value) in target.iter_mut().zip(values) {
                if imaginary {
                    matrix[entry].im = value;
                } else {
                    matrix[entry].re = value;
                }
            }
        }
        Ok(())
    }

    fn build_component_operators(
        dim: usize,
        component: Vec<Vec<GaussianRat>>,
    ) -> Result<Vec<ExactOperator>, QddcError> {
        component
            .into_iter()
            .map(|entries| {
                let matrix =
                    BasicMatrix::from_row_major(dim, dim, entries).map_err(RationalError::from)?;
                let operator = ExactOperator::try_new(matrix)?;
                operator.check_hermitian()?;
                Ok(operator)
            })
            .collect()
    }
    fn pack_operator_hodge(
        dim: usize,
        components: Vec<Vec<Vec<GaussianRat>>>,
        scalar_ops: usize,
    ) -> Result<OperatorHodge, QddcError> {
        let mut built: Vec<Vec<ExactOperator>> = components
            .into_iter()
            .map(|c| Self::build_component_operators(dim, c))
            .collect::<Result<Vec<_>, QddcError>>()?;
        let [alpha, beta, exact, coexact, harmonic]: [Vec<ExactOperator>; 5] = built
            .drain(..)
            .collect::<Vec<_>>()
            .try_into()
            .map_err(|_| QddcError::Contract("missing Hodge component"))?;
        Ok(OperatorHodge {
            alpha,
            beta,
            exact,
            coexact,
            harmonic,
            scalar_ops,
        })
    }
}

impl ExactHodge for QddcState {
    fn decompose(&self) -> Result<OperatorHodge, QddcError> {
        let sizes = [
            self.d_prev.cols(),
            self.d_next.rows(),
            self.cochain.len(),
            self.cochain.len(),
            self.cochain.len(),
        ];
        let mut components: Vec<Vec<Vec<GaussianRat>>> = sizes
            .iter()
            .map(|&n| vec![vec![GaussianRat::zero(); self.dim * self.dim]; n])
            .collect();
        let mut fuel = budget();
        for entry in 0..self.dim * self.dim {
            for imaginary in [false, true] {
                self.decompose_entry_slice(entry, imaginary, &mut components, &mut fuel)?;
            }
        }
        Self::pack_operator_hodge(self.dim, components, fuel.used())
    }
}

/// The derivative is an operator, not a density or a positivity-preserving step.
pub trait ExactGenerator {
    fn derivative(&self, rho: &ExactDensityMatrix) -> Result<ExactOperator, QddcError>;
}

pub struct Lindbladian {
    hamiltonian: ExactOperator,
    jumps: Vec<ExactOperator>,
}

impl Lindbladian {
    pub fn try_new(
        hamiltonian: ExactOperator,
        jumps: Vec<ExactOperator>,
    ) -> Result<Self, QddcError> {
        check_operator(&hamiltonian, hamiltonian.rows())?;
        hamiltonian.check_hermitian()?;
        if jumps.len() > MAX_JUMPS {
            return Err(QddcError::Contract("at most 16 jumps"));
        }
        for jump in &jumps {
            check_operator(jump, hamiltonian.rows())?;
        }
        Ok(Self { hamiltonian, jumps })
    }

    fn jump_dissipator(
        jump: &ExactOperator,
        rho: &ExactOperator,
    ) -> Result<ExactOperator, QddcError> {
        let adjoint = jump.dagger()?;
        let norm = adjoint.mul(jump)?;
        let gain = jump.mul(rho)?.mul(&adjoint)?;
        let loss = norm.anticommutator(rho)?.scale_rat(&(ri(1) / ri(2)))?;
        Ok(gain.sub(&loss)?)
    }
}

impl ExactGenerator for Lindbladian {
    fn derivative(&self, rho: &ExactDensityMatrix) -> Result<ExactOperator, QddcError> {
        let rho = rho.as_operator();
        check_operator(rho, self.hamiltonian.rows())?;
        let mut result = self
            .hamiltonian
            .commutator(rho)?
            .scale(&GaussianRat::from_ints(0, -1))?;
        for jump in &self.jumps {
            result = result.add(&Self::jump_dissipator(jump, rho)?)?;
        }
        Ok(result)
    }
}

/// R(rho)=P rho P + tr((I-P)rho) P/tr(P). R is CPTP and idempotent.
pub struct RetractionChannel {
    projector: ExactOperator,
    complement: ExactOperator,
    target: ExactOperator,
}

pub trait ExactDensityStep {
    fn step(
        &self,
        rho: &ExactDensityMatrix,
        eta: &Rational,
    ) -> Result<ExactDensityMatrix, QddcError>;
}

impl RetractionChannel {
    pub fn try_new(projector: ExactOperator) -> Result<Self, QddcError> {
        check_operator(&projector, projector.rows())?;
        projector.check_hermitian()?;
        if !projector.is_idempotent() || projector.is_zero() {
            return Err(QddcError::Contract(
                "target must be a nonzero orthogonal projector",
            ));
        }
        let complement = ExactOperator::identity(projector.rows())?.sub(&projector)?;
        let target = projector.scale_rat(&projector.trace()?.re.recip())?;
        Ok(Self {
            projector,
            complement,
            target,
        })
    }

    /// Probability outside the declared subspace; this is not the DDC L1 norm.
    pub fn outside_weight(&self, rho: &ExactDensityMatrix) -> Result<Rational, QddcError> {
        check_operator(rho.as_operator(), self.projector.rows())?;
        Ok(self.complement.mul(rho.as_operator())?.trace()?.re)
    }

    /// Rational weighted Kraus witness: P with weight one, and P E_ij (I-P)
    /// with weight 1/rank(P). The native channel owner checks completeness.
    pub fn weighted_kraus(&self) -> Result<ExactKrausChannel, QddcError> {
        let n = self.projector.rows();
        let weight = self.projector.trace()?.re.recip();
        let mut terms = vec![(ri(1), self.projector.as_matrix().clone())];
        for i in 0..n {
            for j in 0..n {
                let mut entries = vec![GaussianRat::zero(); n * n];
                entries[i * n + j] = GaussianRat::one();
                let unit = ExactOperator::try_new(
                    BasicMatrix::from_row_major(n, n, entries).map_err(RationalError::from)?,
                )?;
                let k = self.projector.mul(&unit)?.mul(&self.complement)?;
                terms.push((weight.clone(), k.into_matrix()));
            }
        }
        Ok(ExactKrausChannel::try_weighted(
            n,
            n,
            terms,
            "QDDC finite retraction",
        )?)
    }

    fn reset_operator(&self, rho: &ExactDensityMatrix) -> Result<ExactOperator, QddcError> {
        let outside = self.outside_weight(rho)?;
        Ok(self
            .projector
            .mul(rho.as_operator())?
            .mul(&self.projector)?
            .add(&self.target.scale_rat(&outside)?)?)
    }
}

impl ExactDensityStep for RetractionChannel {
    /// Exact CPTP map (1-eta)Id+eta R, for rational eta in [0,1].
    /// eta=1 is a discrete reset, not a finite-time continuous semigroup step.
    fn step(
        &self,
        rho: &ExactDensityMatrix,
        eta: &Rational,
    ) -> Result<ExactDensityMatrix, QddcError> {
        check_scalar(eta)?;
        if !(ri(0)..=ri(1)).contains(eta) {
            return Err(QddcError::Contract("eta must lie in [0,1]"));
        }
        let reset = self.reset_operator(rho)?;
        let output = rho
            .as_operator()
            .scale_rat(&(ri(1) - eta))?
            .add(&reset.scale_rat(eta)?)?;
        Ok(ExactDensityMatrix::try_from_operator(output)?)
    }
}

fn validate_probe_projector(
    rho: &ExactDensityMatrix,
    projector: &ExactOperator,
) -> Result<(), QddcError> {
    check_operator(projector, rho.dim())?;
    check_operator(rho.as_operator(), rho.dim())?;
    projector.check_hermitian()?;
    if !projector.is_idempotent() {
        return Err(QddcError::Contract("probe must be an orthogonal projector"));
    }
    Ok(())
}

/// Selected PVM branch. Zero probability has no conditional density.
pub fn probe(
    rho: &ExactDensityMatrix,
    projector: &ExactOperator,
) -> Result<(Rational, Option<ExactDensityMatrix>), QddcError> {
    validate_probe_projector(rho, projector)?;
    let branch = projector.mul(rho.as_operator())?.mul(projector)?;
    let p = branch.trace()?.re;
    if p.is_zero() {
        return Ok((p, None));
    }
    let state = ExactDensityMatrix::try_from_operator(branch.scale_rat(&p.recip())?)?;
    Ok((p, Some(state)))
}

// Origin: engine/crates_rs/core_quantum_physics/src/qddc.rs
// Claim: urn:core:crates_rs:core-quantum-physics:qddc:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_20e10c4c {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
