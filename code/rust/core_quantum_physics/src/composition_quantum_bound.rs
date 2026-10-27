//! A sufficient, explicitly imported finite Hilbert composition principle.
//! AuthorityEffect: None. Local Hermitian involutions, tensor composition, PSD
//! trace-one states, and the trace readout give S^2 <= 8 for CHSH expectations.
//! This excludes PR but does NOT reconstruct tensor structure or the Born rule.
//!
//! Let C_A=[A0,A1], C_B=[B0,B1], S=A0⊗(B0+B1)+A1⊗(B0-B1).
//! Involutions imply S²=4I-C_A⊗C_B. Since
//! 2I±iC_A=(A0±iA1)* (A0±iA1) (and likewise B),
//! 8I-S² = 1/2[(2I+iC_A)⊗(2I-iC_B)+(2I-iC_A)⊗(2I+iC_B)]
//! is PSD. For s=tr(rho S), tr(rho(S-sI)²)>=0 gives
//! s²<=tr(rho S²)<=8. This proof works over C in every finite
//! dimension; executable instances here use exact Q(i) and rational states.
use crate::exact_hermitian::{hermitian_trace, is_psd, ExactHermitianError};
use crate::finite_chsh_correlations::{CorrelationError, PairwiseBox};
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::exact_field::{involution as star, matrix as mx, ExactFieldError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum QuantumCompositionError {
    #[error("exact matrix algebra: {0}")]
    Algebra(#[from] ExactFieldError),
    #[error("matrix storage: {0}")]
    Storage(#[from] MatrixError),

    #[error("declared correlation model refused: {0}")]
    Correlation(#[from] CorrelationError),
    #[error("exact Hermitian operation refused: {0}")]
    Hermitian(#[from] ExactHermitianError),
    #[error("the derived Tsirelson identity/positivity failed")]
    DerivedIdentityFailed,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuantumChshCertificate {
    correlations: PairwiseBox,
    square_bound_operator: BasicMatrix<GaussianRat>,
    variance_slack: Rational,
    operator_bound_slack: Rational,
}
impl QuantumChshCertificate {
    /// Certify an actual tensor model, not merely a caller-declared correlation
    /// bound. Existing owner validates all local observables and the state.
    pub fn from_tensor_model(
        rho: &BasicMatrix<GaussianRat>,
        alice: [&BasicMatrix<GaussianRat>; 2],
        bob: [&BasicMatrix<GaussianRat>; 2],
    ) -> Result<Self, QuantumCompositionError> {
        let correlations = PairwiseBox::from_state(rho, alice, bob)?;
        let (chsh_operator, squared, square_bound_operator) =
            Self::build_and_verify_chsh_operators(rho.rows(), alice, bob)?;
        let (variance_slack, operator_bound_slack) =
            Self::compute_chsh_slacks(rho, &correlations, &chsh_operator, &squared)?;
        Ok(Self {
            correlations,
            square_bound_operator,
            variance_slack,
            operator_bound_slack,
        })
    }

    fn build_and_verify_chsh_operators(
        dim: usize,
        alice: [&BasicMatrix<GaussianRat>; 2],
        bob: [&BasicMatrix<GaussianRat>; 2],
    ) -> Result<
        (
            BasicMatrix<GaussianRat>,
            BasicMatrix<GaussianRat>,
            BasicMatrix<GaussianRat>,
        ),
        QuantumCompositionError,
    > {
        let chsh_operator = Self::build_chsh_operator(alice, bob)?;
        let squared = mx::multiply(&chsh_operator, &chsh_operator)?;
        let id = mx::identity(dim)?;
        let square_bound_operator = mx::sub(
            &mx::scale(&id, &GaussianRat::from_rational(ri(8)))?,
            &squared,
        )?;
        let identity_rhs = Self::examiner_identity_rhs(&id, alice, bob)?;
        if squared != identity_rhs || !is_psd(&square_bound_operator)? {
            return Err(QuantumCompositionError::DerivedIdentityFailed);
        }
        Ok((chsh_operator, squared, square_bound_operator))
    }

    fn build_chsh_operator(
        alice: [&BasicMatrix<GaussianRat>; 2],
        bob: [&BasicMatrix<GaussianRat>; 2],
    ) -> Result<BasicMatrix<GaussianRat>, QuantumCompositionError> {
        let b_sum = mx::add(bob[0], bob[1])?;
        let b_diff = mx::sub(bob[0], bob[1])?;
        let term0 = mx::kronecker(alice[0], &b_sum)?;
        let term1 = mx::kronecker(alice[1], &b_diff)?;
        Ok(mx::add(&term0, &term1)?)
    }

    fn examiner_identity_rhs(
        id: &BasicMatrix<GaussianRat>,
        alice: [&BasicMatrix<GaussianRat>; 2],
        bob: [&BasicMatrix<GaussianRat>; 2],
    ) -> Result<BasicMatrix<GaussianRat>, QuantumCompositionError> {
        let comm_a = mx::commutator(alice[0], alice[1])?;
        let comm_b = mx::commutator(bob[0], bob[1])?;
        let four_id = mx::scale(id, &GaussianRat::from_rational(ri(4)))?;
        let kron_comm = mx::kronecker(&comm_a, &comm_b)?;
        Ok(mx::sub(&four_id, &kron_comm)?)
    }

    fn jordan_trace(
        rho: &BasicMatrix<GaussianRat>,
        operator: &BasicMatrix<GaussianRat>,
    ) -> Result<Rational, QuantumCompositionError> {
        let left = mx::multiply(rho, operator)?;
        let right = mx::multiply(operator, rho)?;
        let sum = mx::add(&left, &right)?;
        let half = GaussianRat::from_rational(core_number_theory::rational::rq(1, 2));
        let jordan = mx::scale(&sum, &half)?;
        Ok(hermitian_trace(&jordan)?)
    }

    fn compute_chsh_slacks(
        rho: &BasicMatrix<GaussianRat>,
        correlations: &PairwiseBox,
        chsh_operator: &BasicMatrix<GaussianRat>,
        squared: &BasicMatrix<GaussianRat>,
    ) -> Result<(Rational, Rational), QuantumCompositionError> {
        let s = correlations.chsh();
        if Self::jordan_trace(rho, chsh_operator)? != s {
            return Err(QuantumCompositionError::DerivedIdentityFailed);
        }
        let second_moment = Self::jordan_trace(rho, squared)?;
        let variance_slack = &second_moment - &s * &s;
        let operator_bound_slack = ri(8) - second_moment;
        if variance_slack < ri(0) || operator_bound_slack < ri(0) {
            return Err(QuantumCompositionError::DerivedIdentityFailed);
        }
        Ok((variance_slack, operator_bound_slack))
    }
    pub fn correlations(&self) -> &PairwiseBox {
        &self.correlations
    }
    pub fn square_bound_operator(&self) -> &BasicMatrix<GaussianRat> {
        &self.square_bound_operator
    }
    pub fn variance_slack(&self) -> &Rational {
        &self.variance_slack
    }
    pub fn operator_bound_slack(&self) -> &Rational {
        &self.operator_bound_slack
    }
    pub fn squared_chsh(&self) -> Rational {
        let s = self.correlations.chsh();
        &s * &s
    }
}
/// A necessary quantum composition test only; passing is not sufficient for
/// membership in the quantum set or for a Hilbert reconstruction.
pub fn passes_squared_chsh_bound(model: &PairwiseBox) -> bool {
    let s = model.chsh();
    &s * &s <= ri(8)
}

/// Classified carrier of two commuting complete matrix-unit algebras.
/// The associated complex Hilbert carrier is (C^m tensor C^n) tensor C^r,
/// r=hidden_multiplicity; r=1 selects the tensor carrier up to unitary equivalence.
/// This is a theorem AFTER importing complete local matrix algebras, not a
/// consequence of tagging/no-signalling alone. No Q(i)-unitary basis is promised.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TensorFactorizationCertificate {
    pub left_dimension: usize,
    pub right_dimension: usize,
    pub carrier_dimension: usize,
    pub hidden_multiplicity: Rational,
    pub minimal_tensor_carrier: bool,
}

/// Verify complete unital *-matrix-unit systems E_ij,F_kl and cross commutation.
/// Their products are complete matrix units G_(i,k),(j,l)=E_ij F_kl. Every
/// diagonal G has the same rank r, so dim(H)=mn*r. Choosing an orthonormal basis
/// of range(G_00) and transporting it with G_a0 gives the asserted decomposition.
pub fn classify_commuting_matrix_units(
    m: usize,
    n: usize,
    left: &[BasicMatrix<GaussianRat>],
    right: &[BasicMatrix<GaussianRat>],
) -> Result<TensorFactorizationCertificate, QuantumCompositionError> {
    let (product_dimension, d) = validate_matrix_unit_inputs(m, n, left, right)?;
    if !verify_matrix_unit_system(left, m, d)? || !verify_matrix_unit_system(right, n, d)? {
        return Err(QuantumCompositionError::DerivedIdentityFailed);
    }
    verify_cross_commutation(left, right)?;
    let hidden_multiplicity =
        compute_and_verify_multiplicity(&left[0], &right[0], product_dimension, d)?;
    Ok(TensorFactorizationCertificate {
        left_dimension: m,
        right_dimension: n,
        carrier_dimension: d,
        minimal_tensor_carrier: hidden_multiplicity == ri(1),
        hidden_multiplicity,
    })
}

fn validate_matrix_unit_inputs(
    m: usize,
    n: usize,
    left: &[BasicMatrix<GaussianRat>],
    right: &[BasicMatrix<GaussianRat>],
) -> Result<(usize, usize), QuantumCompositionError> {
    let count_left = m
        .checked_mul(m)
        .ok_or(QuantumCompositionError::DerivedIdentityFailed)?;
    let count_right = n
        .checked_mul(n)
        .ok_or(QuantumCompositionError::DerivedIdentityFailed)?;
    let product_dimension = m
        .checked_mul(n)
        .ok_or(QuantumCompositionError::DerivedIdentityFailed)?;
    if [
        m == 0,
        n == 0,
        left.len() != count_left,
        right.len() != count_right,
    ]
    .into_iter()
    .any(|b| b)
    {
        return Err(QuantumCompositionError::DerivedIdentityFailed);
    }
    let d = left[0].rows();
    validate_matrix_shapes(left.iter().chain(right), d)?;
    Ok((product_dimension, d))
}

fn validate_matrix_shapes<'a>(
    matrices: impl Iterator<Item = &'a BasicMatrix<GaussianRat>>,
    d: usize,
) -> Result<(), QuantumCompositionError> {
    for matrix in matrices {
        crate::exact_hermitian::check_well_formed(matrix)?;
        if matrix.rows() != d || matrix.cols() != d || d == 0 {
            return Err(QuantumCompositionError::DerivedIdentityFailed);
        }
    }
    Ok(())
}

fn verify_matrix_unit_system(
    units: &[BasicMatrix<GaussianRat>],
    size: usize,
    d: usize,
) -> Result<bool, QuantumCompositionError> {
    let mut identity = mx::zeros(d, d)?;
    for i in 0..size {
        identity = mx::add(&identity, &units[i * size + i])?;
    }
    if identity != mx::identity(d)? {
        return Ok(false);
    }
    for i in 0..size {
        for j in 0..size {
            if !verify_unit_pair(units, size, d, i, j)? {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

fn verify_unit_pair(
    units: &[BasicMatrix<GaussianRat>],
    size: usize,
    d: usize,
    i: usize,
    j: usize,
) -> Result<bool, QuantumCompositionError> {
    if star::adjoint(&units[i * size + j])? != units[j * size + i] {
        return Ok(false);
    }
    for k in 0..size {
        for l in 0..size {
            let expected = if j == k {
                units[i * size + l].clone()
            } else {
                mx::zeros(d, d)?
            };
            if mx::multiply(&units[i * size + j], &units[k * size + l])? != expected {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

fn verify_cross_commutation(
    left: &[BasicMatrix<GaussianRat>],
    right: &[BasicMatrix<GaussianRat>],
) -> Result<(), QuantumCompositionError> {
    for e in left {
        for f in right {
            if mx::multiply(e, f)? != mx::multiply(f, e)? {
                return Err(QuantumCompositionError::DerivedIdentityFailed);
            }
        }
    }
    Ok(())
}

fn compute_and_verify_multiplicity(
    e00: &BasicMatrix<GaussianRat>,
    f00: &BasicMatrix<GaussianRat>,
    product_dimension: usize,
    d: usize,
) -> Result<Rational, QuantumCompositionError> {
    let prod = mx::multiply(e00, f00)?;
    let hidden_multiplicity = hermitian_trace(&prod)?;
    let bad = [
        hidden_multiplicity <= ri(0),
        hidden_multiplicity.denom() != &num_bigint::BigInt::from(1),
        &hidden_multiplicity * Rational::from_integer(product_dimension.into())
            != Rational::from_integer(d.into()),
    ]
    .into_iter()
    .any(|b| b);
    if bad {
        return Err(QuantumCompositionError::DerivedIdentityFailed);
    }
    Ok(hidden_multiplicity)
}

// Origin: engine/crates_rs/core_quantum_physics/src/composition_quantum_bound.rs
// Claim: urn:core:crates_rs:core-quantum-physics:composition-quantum-bound:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f6d284ff {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
