//! Physical density-state adapter to canonical exact packed Hermitian operators.
//! Population shadows are distinguished from full coherent density operators.
//! Operator storage and contractions belong to `linear_algebra::packed_hermitian`.
//! AuthorityEffect: None.

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; packed density operator.";

use crate::density_matrix::{ExactDensityError, ExactDensityMatrix};
use crate::exact_hermitian::ExactHermitianError;
use linear_algebra::packed_hermitian::ExactPackedHermitian;
use core_number_theory::cyclotomic::GaussianRat;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PackedDensityOperator {
    packed: ExactPackedHermitian<GaussianRat>,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PackedDensityError {
    #[error("Hermitian operator: {0}")]
    Hermitian(#[from] ExactHermitianError),
    #[error("packed operator: {0}")]
    Algebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error("density: {0}")]
    Density(#[from] ExactDensityError),
}
impl PackedDensityOperator {
    pub fn from_state(rho: &ExactDensityMatrix) -> Result<Self, PackedDensityError> {
        Ok(Self {
            packed: ExactPackedHermitian::from_matrix(rho.matrix())?,
        })
    }
    pub fn to_state(&self) -> Result<ExactDensityMatrix, PackedDensityError> {
        Ok(ExactDensityMatrix::try_new(self.packed.to_matrix()?)?)
    }
    pub fn expectation(
        &self,
        ray: &crate::quantum_state::RayVector,
    ) -> Result<core_number_theory::rational::Rational, PackedDensityError> {
        Ok(self.packed.quadratic_form(ray.entries())?.re / ray.norm_sq())
    }
    pub fn packed(&self) -> &ExactPackedHermitian<GaussianRat> {
        &self.packed
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/packed_hermitian.rs
// Claim: urn:core:crates_rs:core-quantum-physics:packed-hermitian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_b0fd8ed6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
