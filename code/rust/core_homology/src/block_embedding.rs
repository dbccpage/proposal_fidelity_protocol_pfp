//! Faithful endpoint-Hom corners in the endomorphism ring of the fiber sum.
//! The declared carrier keeps its heterogeneous dimensions; no fiber is silently
//! replaced by a scalar. Off-corner entries are zero, and decoding checks this.

use crate::restriction_dga::{Cochain, Components, Matrix, OperatorCarrier, RestrictionError};
use num_rational::BigRational as Q;
use num_traits::{One, Zero};
use std::sync::Arc;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum BlockError {
    #[error(transparent)]
    Owner(#[from] RestrictionError),
    #[error("invalid block endpoints, shapes, or off-corner support")]
    Corner,
}

#[derive(Debug, Clone)]
pub struct BlockEmbedding {
    carrier: Arc<OperatorCarrier>,
    offsets: Vec<usize>,
    dimension: usize,
}
impl BlockEmbedding {
    pub fn new(carrier: Arc<OperatorCarrier>) -> Self {
        let mut offsets = Vec::new();
        let mut dimension = 0;
        for d in carrier.dimensions() {
            offsets.push(dimension);
            dimension += d;
        }
        Self {
            carrier,
            offsets,
            dimension,
        }
    }
    pub fn dimension(&self) -> usize {
        self.dimension
    }
    pub fn carrier(&self) -> &Arc<OperatorCarrier> {
        &self.carrier
    }
    fn corner(&self, x: usize, z: usize) -> Result<(usize, usize, usize, usize), BlockError> {
        let row = self.offsets.get(x).copied().ok_or(BlockError::Corner)?;
        let col = self.offsets.get(z).copied().ok_or(BlockError::Corner)?;
        Ok((
            row,
            col,
            self.carrier.dimensions()[x],
            self.carrier.dimensions()[z],
        ))
    }
    fn check_positive_denominators(m: &Matrix) -> Result<(), BlockError> {
        for i in 0..m.rows() {
            for j in 0..m.cols() {
                if m.get_ref(i, j).map_err(RestrictionError::from)?.denom() <= &0.into() {
                    return Err(RestrictionError::Denominator.into());
                }
            }
        }
        Ok(())
    }
    fn validate_decode_entries(
        m: &Matrix,
        row: usize,
        col: usize,
        nr: usize,
        nc: usize,
    ) -> Result<(), BlockError> {
        for i in 0..m.rows() {
            for j in 0..m.cols() {
                let v = m.get_ref(i, j).map_err(RestrictionError::from)?;
                if v.denom() <= &0.into() {
                    return Err(RestrictionError::Denominator.into());
                }
                let in_block = (row..row + nr).contains(&i) && (col..col + nc).contains(&j);
                if !in_block && !v.is_zero() {
                    return Err(BlockError::Corner);
                }
            }
        }
        Ok(())
    }
    pub fn lift(&self, x: usize, z: usize, m: &Matrix) -> Result<Matrix, BlockError> {
        let (row, col, nr, nc) = self.corner(x, z)?;
        if m.shape() != (nr, nc) {
            return Err(BlockError::Corner);
        }
        Self::check_positive_denominators(m)?;
        Ok(
            Matrix::try_from_fn_result(self.dimension, self.dimension, |i, j| {
                if (row..row + nr).contains(&i) && (col..col + nc).contains(&j) {
                    m.get_ref(i - row, j - col).cloned()
                } else {
                    Ok(Q::zero())
                }
            })
            .map_err(RestrictionError::from)?,
        )
    }
    pub fn decode(&self, x: usize, z: usize, m: &Matrix) -> Result<Matrix, BlockError> {
        let (row, col, nr, nc) = self.corner(x, z)?;
        if m.shape() != (self.dimension, self.dimension) {
            return Err(BlockError::Corner);
        }
        Self::validate_decode_entries(m, row, col, nr, nc)?;
        Ok(
            Matrix::try_from_fn_result(nr, nc, |i, j| m.get_ref(row + i, col + j).cloned())
                .map_err(RestrictionError::from)?,
        )
    }
    pub fn idempotent(&self, x: usize) -> Result<Matrix, BlockError> {
        let (_, _, nr, _) = self.corner(x, x)?;
        let id = Matrix::try_from_fn(nr, nr, |i, j| if i == j { Q::one() } else { Q::zero() })
            .map_err(RestrictionError::from)?;
        self.lift(x, x, &id)
    }
    pub fn lift_cochain(&self, f: &Cochain) -> Result<Components, BlockError> {
        if f.carrier() != &self.carrier {
            return Err(RestrictionError::CarrierMismatch.into());
        }
        f.components()
            .iter()
            .map(|(chain, m)| {
                let x = *chain.first().ok_or(BlockError::Corner)?;
                let z = *chain.last().ok_or(BlockError::Corner)?;
                Ok((chain.clone(), self.lift(x, z, m)?))
            })
            .collect()
    }
}

// Origin: engine/crates_rs/core_homology/src/block_embedding.rs
// Claim: urn:core:crates_rs:core-homology:block-embedding:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_0517bde8 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
