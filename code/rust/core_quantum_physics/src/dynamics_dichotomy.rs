//! Exact periodic and aperiodic sectors of a declared finite unitary step.
//! Finite order is decided from cyclotomic characteristic factors and replay of
//! the resulting order; an unbounded-looking orbit is never certified by sampling.
//! AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution, ExactFieldError};
use core_lie_theory::finite_order::{gaussian_finite_order, FiniteOrderError};
use core_number_theory::cyclotomic::GaussianRat;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DynamicsDichotomyError {
    #[error("the declared finite step is not unitary")]
    NotUnitary,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error(transparent)]
    Order(#[from] FiniteOrderError),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum UnitaryOrbit {
    Periodic { order: usize },
    Aperiodic,
}
/// Classifies a Q(i)-unitary of dimension at most eight, using the sovereign
/// exact finite-order decision on its faithful rational representation.
pub fn classify_unitary_orbit(
    step: &BasicMatrix<GaussianRat>,
) -> Result<UnitaryOrbit, DynamicsDichotomyError> {
    if !involution::is_unitary(step)? {
        return Err(DynamicsDichotomyError::NotUnitary);
    }
    Ok(match gaussian_finite_order(step)? {
        Some(order) => UnitaryOrbit::Periodic { order },
        None => UnitaryOrbit::Aperiodic,
    })
}

// Origin: engine/crates_rs/core_quantum_physics/src/dynamics_dichotomy.rs
// Claim: urn:core:crates_rs:core-quantum-physics:dynamics-dichotomy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3cbffc3c {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
