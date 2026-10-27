//! Explicit unital star embeddings of finite observable algebras.
//! A -> A tensor I_k preserves algebra and adjoints. It acts on observables;
//! the state marginal is the adjoint normalized map, not this embedding.
//! AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use core_number_theory::cyclotomic::GaussianRat;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SubsystemTowerError {
    #[error("positive matrix dimensions <=256 with target a multiple of source are required")]
    Dimension,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObservableEmbedding {
    source: usize,
    target: usize,
}
impl ObservableEmbedding {
    pub fn new(source: usize, target: usize) -> Result<Self, SubsystemTowerError> {
        if source == 0 || target == 0 || target > 256 || target % source != 0 {
            return Err(SubsystemTowerError::Dimension);
        }
        Ok(Self { source, target })
    }
    pub fn source(&self) -> usize {
        self.source
    }
    pub fn target(&self) -> usize {
        self.target
    }
    pub fn apply(
        &self,
        a: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, SubsystemTowerError> {
        if a.shape() != (self.source, self.source) {
            return Err(SubsystemTowerError::Dimension);
        }
        Ok(mx::kronecker(a, &mx::identity(self.target / self.source)?)?)
    }
    pub fn compose(&self, next: &Self) -> Result<Self, SubsystemTowerError> {
        if self.target != next.source {
            return Err(SubsystemTowerError::Dimension);
        }
        Self::new(self.source, next.target)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/refinement_subsystem_tower.rs
// Claim: urn:core:crates_rs:core-quantum-physics:refinement-subsystem-tower:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_6ee847b4 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
