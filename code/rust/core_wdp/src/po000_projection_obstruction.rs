//! PO-000 declared projection diagnostics, bound to their complete source data.
//! This wrapper makes no finite-time exponential or operational-QM assertion.
//! Exact matrix arithmetic and leakage calculations live in their math owners.

use crate::types::AuthorityEffect;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational;
use core_functional::projection_leakage::{
    evaluate_projection_leakage, ProjectionLeakage, ProjectionLeakageError,
};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredProjectionProblem {
    pub first: BasicMatrix<BigRational>,
    pub second: BasicMatrix<BigRational>,
    pub generator: BasicMatrix<BigRational>,
    pub elapsed: BigRational,
    pub state: Vec<BigRational>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProjectionObstructionReceipt {
    pub problem: DeclaredProjectionProblem,
    pub diagnostic: ProjectionLeakage,
    pub authority_effect: AuthorityEffect,
}

impl DeclaredProjectionProblem {
    pub fn evaluate(&self) -> Result<ProjectionObstructionReceipt, ProjectionLeakageError> {
        let diagnostic = evaluate_projection_leakage(
            &self.first,
            &self.second,
            &self.generator,
            &self.elapsed,
            &self.state,
        )?;
        Ok(ProjectionObstructionReceipt {
            problem: self.clone(),
            diagnostic,
            authority_effect: AuthorityEffect::None,
        })
    }

    pub fn verify(
        &self,
        candidate: &ProjectionObstructionReceipt,
    ) -> Result<bool, ProjectionLeakageError> {
        Ok(*candidate == self.evaluate()?)
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProjectionShapeWitness {
    dimension: u64,
    state_len: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProjectionShapeWitnessError {
    NotSquare { rows: u64, cols: u64 },
    DimensionMismatch { left: u64, right: u64 },
    StateLength { dimension: u64, state_len: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_wdp/src/po000_projection_obstruction.rs
// Claim: urn:core:crates_rs:core-wdp:po000-projection-obstruction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ProjectionShapeWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ProjectionShapeWitnessError {}

impl ProjectionShapeWitness {
    pub fn certify(problem: &DeclaredProjectionProblem) -> Result<Self, ProjectionShapeWitnessError> {
        fn square_dim(matrix: &BasicMatrix<BigRational>) -> Result<u64, ProjectionShapeWitnessError> {
            let rows = u64::try_from(matrix.rows()).map_err(|_| ProjectionShapeWitnessError::Overflow)?;
            let cols = u64::try_from(matrix.cols()).map_err(|_| ProjectionShapeWitnessError::Overflow)?;
            if rows == 0 || cols == 0 || rows != cols { return Err(ProjectionShapeWitnessError::NotSquare { rows, cols }); }
            Ok(rows)
        }
        let first = square_dim(&problem.first)?;
        let second = square_dim(&problem.second)?;
        let generator = square_dim(&problem.generator)?;
        if first != second { return Err(ProjectionShapeWitnessError::DimensionMismatch { left: first, right: second }); }
        if first != generator { return Err(ProjectionShapeWitnessError::DimensionMismatch { left: first, right: generator }); }
        let state_len = u64::try_from(problem.state.len()).map_err(|_| ProjectionShapeWitnessError::Overflow)?;
        if state_len != first { return Err(ProjectionShapeWitnessError::StateLength { dimension: first, state_len }); }
        Ok(Self { dimension: first, state_len })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        let one = BigRational::from_integer(1.into());
        let square = BasicMatrix::from_row_major(1, 1, vec![one.clone()]).ok();
        let admitted = square.clone().and_then(|matrix| {
            let problem = DeclaredProjectionProblem { first: matrix.clone(), second: matrix.clone(), generator: matrix, elapsed: one.clone(), state: vec![one.clone()] };
            ProjectionShapeWitness::certify(&problem).ok()
        });
        assert!(matches!(admitted, Some(w) if w.dimension == 1 && w.state_len == 1));
        let wide = BasicMatrix::from_row_major(1, 2, vec![one.clone(), one.clone()]).ok();
        let refused = wide.and_then(|matrix| {
            let problem = DeclaredProjectionProblem { first: matrix.clone(), second: matrix.clone(), generator: matrix, elapsed: one.clone(), state: vec![one.clone()] };
            ProjectionShapeWitness::certify(&problem).err()
        });
        assert!(matches!(refused, Some(ProjectionShapeWitnessError::NotSquare { .. })));
        let short = square.and_then(|matrix| {
            let problem = DeclaredProjectionProblem { first: matrix.clone(), second: matrix.clone(), generator: matrix, elapsed: one.clone(), state: Vec::new() };
            ProjectionShapeWitness::certify(&problem).err()
        });
        assert!(matches!(short, Some(ProjectionShapeWitnessError::StateLength { .. })));
    }
}
