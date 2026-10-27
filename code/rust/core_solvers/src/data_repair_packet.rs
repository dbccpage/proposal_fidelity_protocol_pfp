// AuthorityEffect: None.

//! The finite Banach shadow of the repair cofiber: `Phi1` as the quotient norm
//! of `C^1 / im(d0)`.
//!
//! A repair packet is a rational map `d0 : Q^k -> Q^m`, given row-wise, with
//! strictly positive weights on `Q^m`. In finite dimension `im(d0)` is closed,
//! so the separated quotient `C^1 / closure(im d0)` is `C^1 / im(d0)`, the
//! cokernel of `d0`. On it:
//!
//! - [`RepairPacket::quotient_norm`] is `Phi1([x]) = min_a ||x - d0 a||_{1,w}`,
//!   an infimum over the image that is attained and certified: `core_solvers`
//!   proposes it and `core_functional` replays its primal and dual witnesses;
//! - [`RepairPacket::repair_witness`] decides `x in im(d0)` exactly with
//!   `core_linear_algebra` and returns a preimage, so the zero set of the
//!   quotient norm is decided by linear algebra, not by the optimiser;
//! - [`RepairPacket::cokernel_dimension`] is `m - rank(d0)`.
//!
//! The bridge is scalar. Two packets on the same `Q^m` can give the same
//! class the same `Phi1` while their cokernels have different dimensions, so
//! the number does not determine the cofiber object, and `Phi1 = R_Lambda` is
//! ill-typed. Outside this finite repair specialization no bridge is claimed.

use crate::solver_cohomology_quotient_phi1::{certified_phi1, CertifiedPhi1Error};
use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::elimination::{self, LinearSolution};
use num_traits::{One, Signed, Zero};
use core_functional::phi1::VerifiedExactPhi1;
use core_number_theory::rational::Rational;

/// Refusals for repair packets and their classes.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RepairPacketError {
    #[error("d0 row {row} has {actual} columns, expected {expected}")]
    Ragged {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("{weights} weights for {coordinates} coordinates")]
    WeightCount { coordinates: usize, weights: usize },
    #[error("weight {index} is not strictly positive")]
    NonPositiveWeight { index: usize },
    #[error("vector has {actual} coordinates, expected {expected}")]
    Length { expected: usize, actual: usize },
    #[error("obstruction functional refused: {0}")]
    Functional(#[from] CertifiedPhi1Error),
    #[error("{what} exceeds the declared bound {limit}")]
    ResourceBudget { what: &'static str, limit: usize },
    #[error(transparent)]
    LinearAlgebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
}

/// A declared finite weighted-`l1` repair packet `d0 : Q^c0 -> Q^m`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepairPacket {
    c0: usize,
    d0: Vec<Vec<Rational>>,
    weights: Vec<Rational>,
    matrix: BasicMatrix<Rational>,
    rank: usize,
}

pub const MAX_REPAIR_DIMENSION: usize = 4096;
const LIMITS: OperationLimits = OperationLimits {
    max_elements: 1 << 20,
    max_scalar_ops: 1 << 26,
};

impl RepairPacket {
    pub fn new(
        d0: Vec<Vec<Rational>>,
        c0: usize,
        weights: Vec<Rational>,
    ) -> Result<Self, RepairPacketError> {
        // Zero axes still determine the size of returned witness vectors.
        if c0 > MAX_REPAIR_DIMENSION || d0.len() > MAX_REPAIR_DIMENSION {
            return Err(RepairPacketError::ResourceBudget {
                what: "repair dimension",
                limit: MAX_REPAIR_DIMENSION,
            });
        }
        if c0 * d0.len() > LIMITS.max_elements {
            return Err(RepairPacketError::ResourceBudget {
                what: "repair matrix entries",
                limit: LIMITS.max_elements,
            });
        }
        if let Some((row, r)) = d0.iter().enumerate().find(|(_, r)| r.len() != c0) {
            return Err(RepairPacketError::Ragged {
                row,
                expected: c0,
                actual: r.len(),
            });
        }
        if weights.len() != d0.len() {
            return Err(RepairPacketError::WeightCount {
                coordinates: d0.len(),
                weights: weights.len(),
            });
        }
        if let Some(index) = weights.iter().position(|w| !w.is_positive()) {
            return Err(RepairPacketError::NonPositiveWeight { index });
        }
        let matrix =
            BasicMatrix::from_row_major(d0.len(), c0, d0.iter().flatten().cloned().collect())?;
        let rank = elimination::rank_with_limits(&matrix, LIMITS)?;
        Ok(Self {
            c0,
            d0,
            weights,
            matrix,
            rank,
        })
    }

    /// Unit weights on every coordinate.
    pub fn with_unit_weights(d0: Vec<Vec<Rational>>, c0: usize) -> Result<Self, RepairPacketError> {
        if d0.len() > MAX_REPAIR_DIMENSION {
            return Err(RepairPacketError::ResourceBudget {
                what: "repair dimension",
                limit: MAX_REPAIR_DIMENSION,
            });
        }
        let weights = vec![Rational::one(); d0.len()];
        Self::new(d0, c0, weights)
    }

    pub fn ambient_dimension(&self) -> usize {
        self.d0.len()
    }

    fn check(&self, x: &[Rational]) -> Result<(), RepairPacketError> {
        if x.len() != self.d0.len() {
            return Err(RepairPacketError::Length {
                expected: self.d0.len(),
                actual: x.len(),
            });
        }
        Ok(())
    }

    /// `Phi1([x])`, the quotient norm, as a replayed primal-dual certificate.
    pub fn quotient_norm(&self, x: &[Rational]) -> Result<VerifiedExactPhi1, RepairPacketError> {
        self.check(x)?;
        Ok(certified_phi1(self.c0, &self.d0, x, &self.weights, 16_384)?)
    }

    /// A preimage `a` with `d0 a = x`, or `None` when `x` is not a repair.
    pub fn repair_witness(
        &self,
        x: &[Rational],
    ) -> Result<Option<Vec<Rational>>, RepairPacketError> {
        self.check(x)?;
        if self.c0 == 0 || x.is_empty() {
            return Ok(x
                .iter()
                .all(Zero::is_zero)
                .then(|| vec![Rational::zero(); self.c0]));
        }
        match elimination::solve_with_limits(&self.matrix, x, LIMITS)? {
            LinearSolution::Consistent { particular, .. } => Ok(Some(particular)),
            LinearSolution::Inconsistent { .. } => Ok(None),
        }
    }

    /// `dim coker(d0) = m - rank(d0)`, the dimension of the Banach shadow.
    pub fn cokernel_dimension(&self) -> Result<usize, RepairPacketError> {
        Ok(self.d0.len() - self.rank)
    }
}

// Origin: engine/crates_rs/core_solvers/src/data_repair_packet.rs
// Claim: urn:core:crates_rs:core-solvers:data-repair-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use linear_algebra::exact_field::matrix;
    use core_number_theory::rational::ri;

    #[test]
    fn repair_preimages_and_weighted_quotients_replay_independently() {
        let packet = RepairPacket::new(
            vec![vec![ri(1)], vec![ri(-1)], vec![ri(0)]],
            1,
            vec![ri(1), ri(2), ri(3)],
        )
        .unwrap();
        let repaired = vec![ri(4), ri(-4), ri(0)];
        let witness = packet.repair_witness(&repaired).unwrap().unwrap();
        assert_eq!(
            matrix::multiply_vector_with_limits(&packet.matrix, &witness, LIMITS).unwrap(),
            repaired
        );
        assert!(packet.quotient_norm(&repaired).unwrap().value().is_zero());
        let defect = vec![ri(0), ri(0), ri(2)];
        assert_eq!(packet.repair_witness(&defect).unwrap(), None);
        assert_eq!(packet.quotient_norm(&defect).unwrap().value(), &ri(6));
        assert_eq!(packet.cokernel_dimension().unwrap(), 2);
        let shifted: Vec<_> = defect.iter().zip(&repaired).map(|(a, b)| a + b).collect();
        assert_eq!(
            packet.quotient_norm(&defect).unwrap().value(),
            packet.quotient_norm(&shifted).unwrap().value()
        );
        assert!(matches!(
            packet.repair_witness(&[]),
            Err(RepairPacketError::Length { .. })
        ));
        assert!(matches!(
            RepairPacket::new(vec![vec![ri(1)]], 1, vec![ri(0)]),
            Err(RepairPacketError::NonPositiveWeight { .. })
        ));
        // The scalar quotient norm does not specify the quotient object.
        let line = RepairPacket::with_unit_weights(vec![vec![ri(1)], vec![ri(0)], vec![ri(0)]], 1)
            .unwrap();
        let plane = RepairPacket::with_unit_weights(
            vec![vec![ri(1), ri(0)], vec![ri(0), ri(1)], vec![ri(0), ri(0)]],
            2,
        )
        .unwrap();
        let same_representative = [ri(0), ri(0), ri(1)];
        assert_eq!(
            line.quotient_norm(&same_representative).unwrap().value(),
            plane.quotient_norm(&same_representative).unwrap().value()
        );
        assert_eq!(line.cokernel_dimension().unwrap(), 2);
        assert_eq!(plane.cokernel_dimension().unwrap(), 1);
    }

    #[test]
    fn zero_axis_packets_are_valid_but_unbounded_witnesses_are_refused() {
        let empty = RepairPacket::with_unit_weights(vec![], 3).unwrap();
        assert_eq!(empty.repair_witness(&[]).unwrap(), Some(vec![ri(0); 3]));
        assert_eq!(empty.cokernel_dimension().unwrap(), 0);
        assert!(empty.quotient_norm(&[]).unwrap().value().is_zero());
        let zero_map = RepairPacket::with_unit_weights(vec![vec![], vec![]], 0).unwrap();
        assert_eq!(
            zero_map.repair_witness(&[ri(0), ri(0)]).unwrap(),
            Some(vec![])
        );
        assert_eq!(zero_map.repair_witness(&[ri(1), ri(0)]).unwrap(), None);
        assert_eq!(zero_map.cokernel_dimension().unwrap(), 2);
        assert!(matches!(
            RepairPacket::with_unit_weights(vec![], MAX_REPAIR_DIMENSION + 1),
            Err(RepairPacketError::ResourceBudget { .. })
        ));
    }
}
