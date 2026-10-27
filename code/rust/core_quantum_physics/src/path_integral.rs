//! Finite time-sliced kernels and normalized zero-dimensional Gaussian integrals.
//! Formal perturbative coefficients do not assert convergence or a continuum measure.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::graded_path_sum::{TimeSlicedTransport, TransportError};
use linear_algebra::{
    backend::basic_matrix::{BasicMatrix, OperationLimits},
    exact_field::{elimination, ordered},
    scalars::Semiring,
};
use num_bigint::BigInt;
use num_traits::{One, Zero};
use core_number_theory::{
    power_series::{SeriesError, TruncatedSeries},
    rational::Rational,
};
use std::collections::BTreeMap;
pub const AUTHORITY_FENCE: &str = "AuthorityEffect None; not PROVED; not GlobalGreen; finite kernels and formal Gaussian integrals.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum IntegralError {
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("precision must be a nonempty symmetric positive definite rational matrix of size at most eight")]
    Precision,
    #[error("moment or perturbative order exceeds its exact work budget")]
    Budget,
    #[error("multiindex length differs from Gaussian dimension")]
    Multiindex,
    #[error("finite path integral does not close onto its initial carrier")]
    NotClosed,
    #[error(transparent)]
    Transport(#[from] TransportError),
    #[error(transparent)]
    Series(#[from] SeriesError),
    #[error("matrix operation refused: {0}")]
    Matrix(String),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PathIntegral<W> {
    transport: TimeSlicedTransport<W>,
}
impl<W: Semiring> PathIntegral<W> {
    pub fn from_transport(transport: TimeSlicedTransport<W>) -> Result<Self, IntegralError> {
        if transport.slice_sizes().len() > 4097 || transport.slice_sizes().iter().any(|&s| s > 64) {
            return Err(IntegralError::Budget);
        }
        Ok(Self { transport })
    }
    pub fn kernel(&self, source: usize, target: usize) -> Result<W, IntegralError> {
        Ok(self.transport.path_sum(source, target)?)
    }
    pub fn partition(&self) -> Result<W, IntegralError> {
        let slices = self.transport.slice_sizes();
        if slices.first() != slices.last() {
            return Err(IntegralError::NotClosed);
        }
        let propagator = self.transport.propagator();
        let mut total = W::zero();
        for i in 0..propagator.rows() {
            total = total.add(propagator.get_ref(i, i)?);
        }
        Ok(total)
    }
    pub fn transport(&self) -> &TimeSlicedTransport<W> {
        &self.transport
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GaussianMeasure {
    precision: BasicMatrix<Rational>,
    covariance: BasicMatrix<Rational>,
}
impl GaussianMeasure {
    pub fn new(precision: BasicMatrix<Rational>) -> Result<Self, IntegralError> {
        let n = precision.rows();
        if n == 0 || n > 8 || precision.cols() != n {
            return Err(IntegralError::Precision);
        }
        let limits = OperationLimits {
            max_elements: 1 << 12,
            max_scalar_ops: 1 << 20,
        };
        if !ordered::hermitian_inertia_with_limits(&precision, limits)
            .map_err(|_| IntegralError::Precision)?
            .is_positive_definite()
        {
            return Err(IntegralError::Precision);
        }
        let covariance = elimination::inverse_with_limits(&precision, limits)
            .map_err(|e| IntegralError::Matrix(e.to_string()))?;
        Ok(Self {
            precision,
            covariance,
        })
    }
    pub fn precision(&self) -> &BasicMatrix<Rational> {
        &self.precision
    }
    pub fn covariance(&self) -> &BasicMatrix<Rational> {
        &self.covariance
    }
    /// Isserlis recursion grouped by repeated field indices. Memoization avoids
    /// enumerating every individually labeled Wick pairing.
    pub fn moment(&self, multiindex: &[usize]) -> Result<Rational, IntegralError> {
        if multiindex.len() != self.precision.rows() {
            return Err(IntegralError::Multiindex);
        }
        let degree = multiindex
            .iter()
            .try_fold(0usize, |a, &b| a.checked_add(b))
            .ok_or(IntegralError::Budget)?;
        if degree > 256 {
            return Err(IntegralError::Budget);
        }
        if degree % 2 != 0 {
            return Ok(<Rational as Zero>::zero());
        }
        fn wick(
            cov: &BasicMatrix<Rational>,
            powers: &[usize],
            memo: &mut BTreeMap<Vec<usize>, Rational>,
        ) -> Result<Rational, IntegralError> {
            if let Some(v) = memo.get(powers) {
                return Ok(v.clone());
            }
            if memo.len() >= 1 << 16 {
                return Err(IntegralError::Budget);
            }
            let Some(i) = powers.iter().position(|&p| p != 0) else {
                return Ok(<Rational as One>::one());
            };
            let mut remaining = powers.to_vec();
            remaining[i] -= 1;
            let mut total = <Rational as Zero>::zero();
            for j in 0..remaining.len() {
                let multiplicity = remaining[j];
                if multiplicity == 0 {
                    continue;
                }
                remaining[j] -= 1;
                total += Rational::from_integer(multiplicity.into())
                    * cov
                        .get_ref(i, j)
                        .map_err(|e| IntegralError::Matrix(e.to_string()))?
                    * wick(cov, &remaining, memo)?;
                remaining[j] += 1;
            }
            memo.insert(powers.to_vec(), total.clone());
            Ok(total)
        }
        wick(&self.covariance, multiindex, &mut BTreeMap::new())
    }
    /// Normalized phi-four vacuum partition function for one variable,
    /// action g*x^4/4!, modulo g^(order+1).
    pub fn phi4_partition_series(
        &self,
        order: usize,
    ) -> Result<TruncatedSeries<Rational>, IntegralError> {
        if self.precision.rows() != 1 || order > 64 {
            return Err(IntegralError::Budget);
        }
        let mut coefficients = Vec::new();
        let mut denominator = BigInt::one();
        for n in 0..=order {
            if n > 0 {
                denominator *= BigInt::from(24 * n);
            }
            let sign = if n % 2 == 0 { 1 } else { -1 };
            coefficients
                .push(self.moment(&[4 * n])? * Rational::new(sign.into(), denominator.clone()));
        }
        Ok(TruncatedSeries::from_coefficients(coefficients, order)?)
    }
    pub fn phi4_two_point_series(
        &self,
        order: usize,
    ) -> Result<TruncatedSeries<Rational>, IntegralError> {
        if order > 63 {
            return Err(IntegralError::Budget);
        }
        let z = self.phi4_partition_series(order)?;
        let mut coefficients = Vec::new();
        let mut denominator = BigInt::one();
        for n in 0..=order {
            if n > 0 {
                denominator *= BigInt::from(24 * n);
            }
            coefficients.push(
                self.moment(&[4 * n + 2])?
                    * Rational::new(
                        if n % 2 == 0 { 1.into() } else { (-1).into() },
                        denominator.clone(),
                    ),
            );
        }
        Ok(TruncatedSeries::from_coefficients(coefficients, order)?.mul(&z.inverse()?)?)
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/path_integral.rs
// Claim: urn:core:crates_rs:core-quantum-physics:path-integral:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graded_path_sum::NonNegative;
    use core_number_theory::rational::rq;
    #[test]
    fn gaussian_moments_and_phi4_integrals_match_exact_wick_coefficients() {
        let g = GaussianMeasure::new(BasicMatrix::from_row_major(1, 1, vec![rq(1, 1)]).unwrap())
            .unwrap();
        assert_eq!(g.moment(&[6]).unwrap(), rq(15, 1));
        assert_eq!(g.moment(&[3]).unwrap(), rq(0, 1));
        let z = g.phi4_partition_series(5).unwrap();
        assert_eq!(
            &z.coefficients()[..5],
            &[
                rq(1, 1),
                rq(-1, 8),
                rq(35, 384),
                rq(-385, 3072),
                rq(25025, 98304)
            ]
        );
        assert_eq!(
            &z.log().unwrap().coefficients()[1..],
            &[rq(-1, 8), rq(1, 12), rq(-11, 96), rq(17, 72), rq(-619, 960)]
        );
        assert_eq!(
            g.phi4_two_point_series(4).unwrap().coefficients(),
            &[rq(1, 1), rq(-1, 2), rq(2, 3), rq(-11, 8), rq(34, 9)]
        );
        let g = GaussianMeasure::new(
            BasicMatrix::from_row_major(2, 2, vec![rq(2, 1), rq(-1, 1), rq(-1, 1), rq(2, 1)])
                .unwrap(),
        )
        .unwrap();
        assert_eq!(g.moment(&[2, 2]).unwrap(), rq(2, 3));
        assert!(
            GaussianMeasure::new(BasicMatrix::from_row_major(1, 1, vec![rq(-1, 1)]).unwrap())
                .is_err()
        );
    }
    #[test]
    fn finite_chain_partition_is_the_trace_of_the_transfer_product() {
        let transfer = vec![
            vec![
                NonNegative::new(rq(3, 1)).unwrap(),
                NonNegative::new(rq(1, 1)).unwrap(),
            ],
            vec![
                NonNegative::new(rq(1, 1)).unwrap(),
                NonNegative::new(rq(3, 1)).unwrap(),
            ],
        ];
        let path = PathIntegral::from_transport(
            TimeSlicedTransport::new(vec![2; 5], vec![transfer; 4]).unwrap(),
        )
        .unwrap();
        assert_eq!(path.partition().unwrap().value(), &rq(272, 1));
        assert_eq!(
            path.transport().sliced_composition(0, 0, 2).unwrap(),
            path.transport().path_sum(0, 0).unwrap()
        );
    }
}
