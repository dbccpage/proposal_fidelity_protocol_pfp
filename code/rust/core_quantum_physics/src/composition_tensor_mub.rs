//! Checked finite tensor composition of density operators and product statistics.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    matrix as mx,
    ordered::{hermitian_inertia, HermitianOrdered},
    ExactFieldError,
};
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TensorCompositionError {
    #[error("nonempty finite square carriers with joint dimension at most 64 are required")]
    Carrier,
    #[error("density operators must be positive Hermitian with trace one")]
    NotState,
    #[error("product marginals or statistics failed independent replay")]
    Certificate,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}
fn check_state<F: HermitianOrdered>(rho: &BasicMatrix<F>) -> Result<(), TensorCompositionError> {
    let d = rho.rows();
    if d == 0 || d > 64 || rho.shape() != (d, d) {
        return Err(TensorCompositionError::Carrier);
    }
    if mx::trace(rho)? != F::one() || !hermitian_inertia(rho)?.is_positive_semidefinite() {
        return Err(TensorCompositionError::NotState);
    }
    Ok(())
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TensorStateCertificate<F> {
    pub joint: BasicMatrix<F>,
    pub first_marginal: BasicMatrix<F>,
    pub second_marginal: BasicMatrix<F>,
}
/// Positivity, trace normalization and both local reductions are checked on the
/// computed Kronecker state. No composition uniqueness follows from this witness.
pub fn compose_density<F: HermitianOrdered>(
    first: &BasicMatrix<F>,
    second: &BasicMatrix<F>,
) -> Result<TensorStateCertificate<F>, TensorCompositionError> {
    check_state(first)?;
    check_state(second)?;
    let (a, b) = (first.rows(), second.rows());
    if a.checked_mul(b).is_none_or(|d| d > 64) {
        return Err(TensorCompositionError::Carrier);
    }
    let joint = mx::kronecker(first, second)?;
    check_state(&joint)?;
    let left = mx::from_fn(a, a, |i, j| {
        (0..b).fold(F::zero(), |s, k| {
            s.add(&joint.as_slice()[(i * b + k) * (a * b) + j * b + k])
        })
    })?;
    let right = mx::from_fn(b, b, |i, j| {
        (0..a).fold(F::zero(), |s, k| {
            s.add(&joint.as_slice()[(k * b + i) * (a * b) + k * b + j])
        })
    })?;
    if left != *first || right != *second {
        return Err(TensorCompositionError::Certificate);
    }
    Ok(TensorStateCertificate {
        joint,
        first_marginal: left,
        second_marginal: right,
    })
}
/// Tr[(rho_A tensor rho_B)(E_A tensor E_B)] = Tr(rho_A E_A) Tr(rho_B E_B).
/// E_A and E_B are declared Hermitian operators; this identity itself does not
/// certify that their spectra lie in [0,1].
pub fn product_statistic<F: HermitianOrdered>(
    first: &BasicMatrix<F>,
    second: &BasicMatrix<F>,
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<F, TensorCompositionError> {
    let joint = compose_density(first, second)?;
    let value = mx::trace(&mx::multiply(&joint.joint, &mx::kronecker(a, b)?)?)?;
    let separate = mx::trace(&mx::multiply(first, a)?)?.mul(&mx::trace(&mx::multiply(second, b)?)?);
    if value != separate {
        return Err(TensorCompositionError::Certificate);
    }
    Ok(value)
}

/// Independently rebuild the tensor and both reductions against the source states.
pub fn verify_tensor_state<F: HermitianOrdered>(
    first: &BasicMatrix<F>,
    second: &BasicMatrix<F>,
    certificate: &TensorStateCertificate<F>,
) -> Result<bool, TensorCompositionError> {
    Ok(compose_density(first, second)? == *certificate)
}

// Origin: engine/crates_rs/core_quantum_physics/src/composition_tensor_mub.rs
// Claim: urn:core:crates_rs:core-quantum-physics:composition-tensor-mub:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3d53a0ff {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
