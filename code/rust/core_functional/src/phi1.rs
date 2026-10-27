//! # Phi1: exact quotient-distance certificates
//!
//! The exact Phi1 path is certificate-gated:
//!
//! ```text
//! Phi1([omega]) = min_alpha ||omega - d0 alpha||_{1,w}
//! ```
//!
//! A raw representative norm is available only as a display diagnostic. It is
//! not Phi1 and cannot be promoted to a verified quotient-distance result.
//!
//! **Warning**:
//! - A replayed certificate seals one fact: the reported value is exactly the
//!   weighted l1 quotient distance, proved by matching primal and dual bounds.
//!   The seal is verifier-scoped evidence about that value and nothing more.
//! - [`VerifiedExactPhi1`] must not be used for authority minting, lift
//!   acceptance, or terminal classification. Authority claims require the CODA-FDA
//!   terminalizer and are not created by CODA-FOC obstruction data alone, zero or
//!   nonzero: a passing certificate is evidence, never a grant.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b9b6d222<T> {
    fn checked_invariant_b9b6d222(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b9b6d222<T> for Option<T> {
    #[inline]
    fn checked_invariant_b9b6d222(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b9b6d222<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b9b6d222(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde::{Deserialize, Serialize};

/// Submitted exact finite rational witness for the weighted l1 quotient
/// distance. Both the primal residual and the dual witness are mandatory.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExactPhi1Certificate {
    pub omega: Vec<BigRational>,
    pub d0: Vec<Vec<BigRational>>,
    pub weights: Vec<BigRational>,
    pub alpha: Vec<BigRational>,
    pub primal_residual: Vec<BigRational>,
    pub dual_witness: Vec<BigRational>,
    pub reported_value: BigRational,
}

/// Sealed result of replaying an [`ExactPhi1Certificate`].
///
/// The fields are private so downstream exact trichotomy and packet code can
/// require a value that only the verifier can construct.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct VerifiedExactPhi1 {
    certificate: ExactPhi1Certificate,
}

impl VerifiedExactPhi1 {
    /// The exact submitted witness, available read-only for bound persistence.
    /// Mutating a cloned certificate requires fresh verification.
    pub fn certificate(&self) -> &ExactPhi1Certificate {
        &self.certificate
    }

    pub fn value(&self) -> &BigRational {
        &self.certificate.reported_value
    }

    pub fn primal_residual(&self) -> &[BigRational] {
        &self.certificate.primal_residual
    }

    pub fn d0(&self) -> &[Vec<BigRational>] {
        &self.certificate.d0
    }

    pub fn alpha(&self) -> &[BigRational] {
        &self.certificate.alpha
    }

    pub fn dual_witness(&self) -> &[BigRational] {
        &self.certificate.dual_witness
    }
}

#[derive(Debug, Clone, thiserror::Error, PartialEq, Eq)]
pub enum ExactPhi1CertificateError {
    #[error("exact Phi1 input contains a rational with zero denominator")]
    ZeroRationalDenominator,
    #[error("omega, residual, dual witness, and weights must have the same length")]
    CochainDimensionMismatch,
    #[error("d0 has {actual} rows but omega has {expected} coordinates")]
    D0RowMismatch { expected: usize, actual: usize },
    #[error("d0 row {row} has {actual} columns but alpha has {expected} coordinates")]
    D0ColumnMismatch {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("weight at index {index} is not strictly positive")]
    NonPositiveWeight { index: usize },
    #[error("primal residual does not equal omega - d0 alpha at index {index}")]
    PrimalResidualMismatch { index: usize },
    #[error("dual witness does not annihilate im(d0) at column {column}")]
    DualAnnihilatorMismatch { column: usize },
    #[error("dual witness violates the weighted dual bound at index {index}")]
    DualNormBoundViolation { index: usize },
    #[error("reported Phi1 value is negative")]
    NegativeReportedValue,
    #[error("reported Phi1 value does not match the weighted primal residual norm")]
    PrimalValueMismatch,
    #[error("reported Phi1 value does not match the dual pairing")]
    DualValueMismatch,
}

pub struct Phi1Functional;

impl Phi1Functional {
    /// Evaluate a proposed repair and dual witness on the declared presentation.
    /// The residual and both objective values are calculated here, before the
    /// same certificate verifier seals the result. No solver-reported scalar is trusted.
    pub fn evaluate_exact_witness(
        omega: &[BigRational],
        d0: &[Vec<BigRational>],
        weights: &[BigRational],
        alpha: &[BigRational],
        dual: &[BigRational],
    ) -> Result<VerifiedExactPhi1, ExactPhi1CertificateError> {
        if omega
            .iter()
            .chain(weights)
            .chain(alpha)
            .chain(dual)
            .chain(d0.iter().flatten())
            .any(|q| q.denom().is_zero())
        {
            return Err(ExactPhi1CertificateError::ZeroRationalDenominator);
        }
        if weights.len() != omega.len() || dual.len() != omega.len() {
            return Err(ExactPhi1CertificateError::CochainDimensionMismatch);
        }
        if d0.len() != omega.len() {
            return Err(ExactPhi1CertificateError::D0RowMismatch {
                expected: omega.len(),
                actual: d0.len(),
            });
        }
        for (row, coefficients) in d0.iter().enumerate() {
            if coefficients.len() != alpha.len() {
                return Err(ExactPhi1CertificateError::D0ColumnMismatch {
                    row,
                    expected: alpha.len(),
                    actual: coefficients.len(),
                });
            }
        }
        let (primal_residual, reported_value) =
            Self::evaluate_representative(omega, d0, weights, alpha)?;
        Self::verify_exact_certificate(ExactPhi1Certificate {
            omega: omega.to_vec(),
            d0: d0.to_vec(),
            weights: weights.to_vec(),
            alpha: alpha.to_vec(),
            primal_residual,
            dual_witness: dual.to_vec(),
            reported_value,
        })
    }

    /// Evaluate an exact repair proposal without claiming quotient optimality.
    pub fn evaluate_representative(
        omega: &[BigRational],
        d0: &[Vec<BigRational>],
        weights: &[BigRational],
        alpha: &[BigRational],
    ) -> Result<(Vec<BigRational>, BigRational), ExactPhi1CertificateError> {
        if omega
            .iter()
            .chain(weights)
            .chain(alpha)
            .chain(d0.iter().flatten())
            .any(|q| q.denom().is_zero())
        {
            return Err(ExactPhi1CertificateError::ZeroRationalDenominator);
        }
        if weights.len() != omega.len() {
            return Err(ExactPhi1CertificateError::CochainDimensionMismatch);
        }
        if d0.len() != omega.len() {
            return Err(ExactPhi1CertificateError::D0RowMismatch {
                expected: omega.len(),
                actual: d0.len(),
            });
        }
        for (row, coefficients) in d0.iter().enumerate() {
            if coefficients.len() != alpha.len() {
                return Err(ExactPhi1CertificateError::D0ColumnMismatch {
                    row,
                    expected: alpha.len(),
                    actual: coefficients.len(),
                });
            }
        }
        let residual: Vec<_> = omega
            .iter()
            .zip(d0)
            .map(|(x, row)| x - dot(row, alpha))
            .collect();
        let mass = Self::weighted_l1_rational(weights, &residual)
            .ok_or(ExactPhi1CertificateError::CochainDimensionMismatch)?;
        Ok((residual, mass))
    }

    /// Raw representative mass only; it does not establish a quotient minimum.
    pub fn unweighted_l1_rational(residual: &[BigRational]) -> Option<BigRational> {
        if residual.iter().any(|q| q.denom().is_zero()) {
            return None;
        }
        Some(l1_mass(residual))
    }

    /// Hamming mass of a packed binary representative, not a minimum claim.
    pub fn binary_representative_mass(words: &[u64]) -> usize {
        words.iter().map(|word| word.count_ones() as usize).sum()
    }

    fn check_dual_bound_dimensions(
        d0: &[Vec<BigRational>],
        omega: &[BigRational],
        weights: &[BigRational],
        witness: &[BigRational],
    ) -> Result<usize, ExactPhi1CertificateError> {
        if omega
            .iter()
            .chain(weights)
            .chain(witness)
            .chain(d0.iter().flatten())
            .any(|v| v.denom().is_zero())
        {
            return Err(ExactPhi1CertificateError::ZeroRationalDenominator);
        }
        if omega.len() != weights.len() || omega.len() != witness.len() {
            return Err(ExactPhi1CertificateError::CochainDimensionMismatch);
        }
        if d0.len() != omega.len() {
            return Err(ExactPhi1CertificateError::D0RowMismatch {
                expected: omega.len(),
                actual: d0.len(),
            });
        }
        let columns = d0.first().map_or(0, Vec::len);
        for (row, coefficients) in d0.iter().enumerate() {
            if coefficients.len() != columns {
                return Err(ExactPhi1CertificateError::D0ColumnMismatch {
                    row,
                    expected: columns,
                    actual: coefficients.len(),
                });
            }
        }
        Ok(columns)
    }

    /// Verify an exact dual feasible witness and return its pairing with omega.
    /// A nonzero pairing refutes exact repair; it need not attain the optimum.
    pub fn verify_exact_dual_bound(
        d0: &[Vec<BigRational>],
        omega: &[BigRational],
        weights: &[BigRational],
        witness: &[BigRational],
    ) -> Result<BigRational, ExactPhi1CertificateError> {
        let columns = Self::check_dual_bound_dimensions(d0, omega, weights, witness)?;
        for (index, weight) in weights.iter().enumerate() {
            if weight <= &BigRational::zero() {
                return Err(ExactPhi1CertificateError::NonPositiveWeight { index });
            }
            if witness[index].abs() > *weight {
                return Err(ExactPhi1CertificateError::DualNormBoundViolation { index });
            }
        }
        for column in 0..columns {
            let value = (0..omega.len())
                .map(|row| d0[row][column].clone() * witness[row].clone())
                .sum::<BigRational>();
            if !value.is_zero() {
                return Err(ExactPhi1CertificateError::DualAnnihilatorMismatch { column });
            }
        }
        Ok(dot(witness, omega))
    }

    /// Express a verified integer-carrier quotient value in declared units.
    /// The scale must be strictly positive; the source remains the sealed
    /// primal-dual result, not a caller-supplied solver objective.
    pub fn scaled_verified_value(verified: &VerifiedExactPhi1, scale: i128) -> Option<BigRational> {
        if scale <= 0 {
            return None;
        }
        Some(verified.value() / BigRational::from_integer(scale.into()))
    }

    fn validate_certificate_dimensions(
        certificate: &ExactPhi1Certificate,
    ) -> Result<usize, ExactPhi1CertificateError> {
        // BigRational::new_raw is public. A typed in-process caller can bypass
        // serde's nonzero-denominator check, so reject before any arithmetic.
        let mut values = certificate
            .omega
            .iter()
            .chain(certificate.weights.iter())
            .chain(certificate.alpha.iter())
            .chain(certificate.primal_residual.iter())
            .chain(certificate.dual_witness.iter())
            .chain(certificate.d0.iter().flatten())
            .chain(std::iter::once(&certificate.reported_value));
        if values.any(|value| value.denom().is_zero()) {
            return Err(ExactPhi1CertificateError::ZeroRationalDenominator);
        }
        let coordinate_count = certificate.omega.len();
        let lengths_match = certificate.primal_residual.len() == coordinate_count
            && certificate.dual_witness.len() == coordinate_count
            && certificate.weights.len() == coordinate_count;
        if !lengths_match {
            return Err(ExactPhi1CertificateError::CochainDimensionMismatch);
        }
        if certificate.d0.len() != coordinate_count {
            return Err(ExactPhi1CertificateError::D0RowMismatch {
                expected: coordinate_count,
                actual: certificate.d0.len(),
            });
        }
        for (row, coefficients) in certificate.d0.iter().enumerate() {
            if coefficients.len() != certificate.alpha.len() {
                return Err(ExactPhi1CertificateError::D0ColumnMismatch {
                    row,
                    expected: certificate.alpha.len(),
                    actual: coefficients.len(),
                });
            }
        }
        Ok(coordinate_count)
    }

    fn validate_certificate_primal_residual(
        certificate: &ExactPhi1Certificate,
        coordinate_count: usize,
    ) -> Result<(), ExactPhi1CertificateError> {
        for (index, weight) in certificate.weights.iter().enumerate() {
            if weight <= &BigRational::zero() {
                return Err(ExactPhi1CertificateError::NonPositiveWeight { index });
            }
        }
        for index in 0..coordinate_count {
            let repair = dot(&certificate.d0[index], &certificate.alpha);
            if certificate.primal_residual[index] != certificate.omega[index].clone() - repair {
                return Err(ExactPhi1CertificateError::PrimalResidualMismatch { index });
            }
        }
        Ok(())
    }

    /// Replay the exact finite rational primal-dual certificate.
    ///
    /// The primal witness gives an upper bound and the dual witness gives a
    /// lower bound. Matching exact values prove optimality by weak duality.
    pub fn verify_exact_certificate(
        certificate: ExactPhi1Certificate,
    ) -> Result<VerifiedExactPhi1, ExactPhi1CertificateError> {
        let coordinate_count = Self::validate_certificate_dimensions(&certificate)?;
        Self::validate_certificate_primal_residual(&certificate, coordinate_count)?;

        let dual_value = Self::verify_exact_dual_bound(
            &certificate.d0,
            &certificate.omega,
            &certificate.weights,
            &certificate.dual_witness,
        )?;

        if certificate.reported_value < BigRational::zero() {
            return Err(ExactPhi1CertificateError::NegativeReportedValue);
        }

        let primal_value =
            Self::weighted_l1_rational(&certificate.weights, &certificate.primal_residual)
                .ok_or(ExactPhi1CertificateError::CochainDimensionMismatch)?;
        if primal_value != certificate.reported_value {
            return Err(ExactPhi1CertificateError::PrimalValueMismatch);
        }

        if dual_value != certificate.reported_value {
            return Err(ExactPhi1CertificateError::DualValueMismatch);
        }

        Ok(VerifiedExactPhi1 { certificate })
    }
}

/// Exact unweighted rational mass `sum |x_i|`; callers check denominators.
pub(crate) fn l1_mass(values: &[BigRational]) -> BigRational {
    values.iter().map(Signed::abs).sum()
}

/// Exact rational dot product over the zipped prefix; the crate-wide copy.
pub(crate) fn dot(left: &[BigRational], right: &[BigRational]) -> BigRational {
    left.iter()
        .zip(right)
        .map(|(left, right)| left.clone() * right.clone())
        .sum()
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Phi1FormReplayError {
    ZeroRationalDenominator,
    NegativeWeight { index: usize },
    DimensionMismatch { expected: usize, actual: usize },
    DualNotPerpendicular { coboundary_index: usize },
    DualExceedsWeight { index: usize },
    DualityGapNonZero,
}

impl Phi1Functional {
    /// Floating residual mass for legacy search proposals. This preserves the
    /// input's floating-point behavior, including nonfinite values, and is not
    /// a quotient minimum or a verified Phi1 certificate.
    pub fn unweighted_l1_diagnostic(residual: &[f64]) -> f64 {
        residual.iter().map(|value| value.abs()).sum()
    }

    fn validate_replay_form_inputs(
        weights: &[BigRational],
        residual: &[BigRational],
        dual: &[BigRational],
        coboundaries: &[Vec<BigRational>],
    ) -> Result<usize, Phi1FormReplayError> {
        if weights
            .iter()
            .chain(residual)
            .chain(dual)
            .chain(coboundaries.iter().flatten())
            .any(|q| q.denom().is_zero())
        {
            return Err(Phi1FormReplayError::ZeroRationalDenominator);
        }
        if let Some(index) = weights.iter().position(|weight| weight.is_negative()) {
            return Err(Phi1FormReplayError::NegativeWeight { index });
        }
        let n = weights.len();
        for actual in [residual.len(), dual.len()] {
            if actual != n {
                return Err(Phi1FormReplayError::DimensionMismatch {
                    expected: n,
                    actual,
                });
            }
        }
        Ok(n)
    }

    /// Replay the finite weighted-l1 achiever and dual against the supplied
    /// spanning coboundaries. The caller is responsible for declaring a full
    /// generating family; no authority is minted by this value.
    pub fn replay_form(
        weights: &[BigRational],
        residual: &[BigRational],
        dual: &[BigRational],
        coboundaries: &[Vec<BigRational>],
    ) -> Result<BigRational, Phi1FormReplayError> {
        let n = Self::validate_replay_form_inputs(weights, residual, dual, coboundaries)?;
        for (index, coboundary) in coboundaries.iter().enumerate() {
            if coboundary.len() != n {
                return Err(Phi1FormReplayError::DimensionMismatch {
                    expected: n,
                    actual: coboundary.len(),
                });
            }
            if !dot(dual, coboundary).is_zero() {
                return Err(Phi1FormReplayError::DualNotPerpendicular {
                    coboundary_index: index,
                });
            }
        }
        for (index, (dual_value, weight)) in dual.iter().zip(weights).enumerate() {
            if dual_value.abs() > *weight {
                return Err(Phi1FormReplayError::DualExceedsWeight { index });
            }
        }
        let value = Self::weighted_l1_rational(weights, residual)
            .checked_invariant_b9b6d222("dimensions checked before replay");
        if dot(dual, residual) != value {
            return Err(Phi1FormReplayError::DualityGapNonZero);
        }
        Ok(value)
    }

    /// Exact weighted residual mass over signed machine integers.
    /// A missing result means mismatched dimensions, a negative weight, or overflow.
    pub fn weighted_l1_i128(weights: &[i128], residual: &[i128]) -> Option<i128> {
        if weights.len() != residual.len() || weights.iter().any(|weight| *weight < 0) {
            return None;
        }
        weights
            .iter()
            .zip(residual)
            .try_fold(0i128, |sum, (weight, value)| {
                let absolute = value.checked_abs()?;
                sum.checked_add(weight.checked_mul(absolute)?)
            })
    }

    /// Exact weighted residual mass over rationals. A missing result means
    /// mismatched dimensions, a zero denominator, or a negative weight.
    /// Strict positivity for quotient certificates is checked by their verifier.
    pub fn weighted_l1_rational(
        weights: &[BigRational],
        residual: &[BigRational],
    ) -> Option<BigRational> {
        if weights.len() != residual.len()
            || weights.iter().chain(residual).any(|x| x.denom().is_zero())
            || weights.iter().any(|x| x.is_negative())
        {
            return None;
        }
        Some(
            weights
                .iter()
                .zip(residual)
                .map(|(weight, value)| weight.clone() * value.abs())
                .sum(),
        )
    }
}

use crate::binary_degree::{
    check_input_length, check_shape, hamming_weight, image_membership_unchecked, BinaryDegreeError,
    MAX_EXHAUSTIVE_BINARY_DOMAIN_DIM,
};
impl Phi1Functional {
    pub fn binary(
        rows: &[Vec<bool>],
        domain_dim: usize,
        residual: &[bool],
    ) -> Result<usize, BinaryDegreeError> {
        check_shape(rows, domain_dim)?;
        check_input_length(residual, rows.len())?;
        if domain_dim > MAX_EXHAUSTIVE_BINARY_DOMAIN_DIM {
            if image_membership_unchecked(rows, domain_dim, residual) {
                return Ok(0);
            }

            let target_weight = hamming_weight(residual);
            if target_weight <= 1 {
                return Ok(target_weight);
            }

            return Err(BinaryDegreeError::ExhaustiveSearchTooLarge {
                domain_dim,
                max_supported: MAX_EXHAUSTIVE_BINARY_DOMAIN_DIM,
            });
        }

        let state_count = 1usize << domain_dim;
        let mut minimum = residual.len();
        let mut source = vec![false; domain_dim];
        for state in 0..state_count {
            for (index, value) in source.iter_mut().enumerate() {
                *value = ((state >> index) & 1) == 1;
            }
            let distance = rows
                .iter()
                .zip(residual)
                .filter(|(row, target_value)| {
                    let image_value = row
                        .iter()
                        .zip(&source)
                        .fold(false, |parity, (coeff, val)| parity ^ (*coeff && *val));
                    **target_value != image_value
                })
                .count();
            minimum = minimum.min(distance);
            if minimum == 0 {
                break;
            }
        }
        Ok(minimum)
    }
}

/// Floating replay measurements. These are not a verified exact quotient value.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct PrimalDualDiagnostic {
    pub primal_mass: f64,
    pub dual_pairing: f64,
    pub identity_defect: f64,
    pub dual_boundary_defect: f64,
    pub dual_norm_defect: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
pub enum PrimalDualDiagnosticError {
    #[error("primal/dual diagnostic dimensions differ")]
    DimensionMismatch,
    #[error("primal/dual diagnostic contains nonfinite input or arithmetic")]
    NonFinite,
}

impl Phi1Functional {
    /// Measure a floating primal/dual proposal. The caller decides policy over
    /// the result; no tolerance, admission status, or authorization is accepted here.
    pub fn diagnose_primal_dual(
        d0: &nalgebra::DMatrix<f64>,
        omega: &nalgebra::DVector<f64>,
        alpha: &nalgebra::DVector<f64>,
        dual: &nalgebra::DVector<f64>,
    ) -> Result<PrimalDualDiagnostic, PrimalDualDiagnosticError> {
        if d0.nrows() != omega.len() || d0.ncols() != alpha.len() || dual.len() != omega.len() {
            return Err(PrimalDualDiagnosticError::DimensionMismatch);
        }
        if d0
            .iter()
            .chain(omega.iter())
            .chain(alpha.iter())
            .chain(dual.iter())
            .any(|x| !x.is_finite())
        {
            return Err(PrimalDualDiagnosticError::NonFinite);
        }
        let residual = omega - d0 * alpha;
        let primal_mass = Self::unweighted_l1_diagnostic(residual.as_slice());
        let dual_pairing = dual.dot(omega);
        let boundary = d0.transpose() * dual;
        let dual_boundary_defect = boundary.iter().map(|x| x.abs()).fold(0.0, f64::max);
        let dual_norm_defect = (dual.iter().map(|x| x.abs()).fold(0.0, f64::max) - 1.0).max(0.0);
        let identity_defect = (primal_mass - dual_pairing).abs();
        if [
            primal_mass,
            dual_pairing,
            dual_boundary_defect,
            dual_norm_defect,
            identity_defect,
        ]
        .iter()
        .any(|x| !x.is_finite())
        {
            return Err(PrimalDualDiagnosticError::NonFinite);
        }
        Ok(PrimalDualDiagnostic {
            primal_mass,
            dual_pairing,
            identity_defect,
            dual_boundary_defect,
            dual_norm_defect,
        })
    }
}

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum DualWitnessError {
    #[error("dual and primal must have the same length")]
    DimensionMismatch,
    #[error("dual or primal entry is non-finite")]
    NonFiniteEntry,
    #[error("dual norm exceeds the unit bound")]
    DualNormBoundViolation,
    #[error("claimed evaluation {claimed} does not equal pairing {computed}")]
    EvaluationMismatch { claimed: f64, computed: f64 },
}

impl Phi1Functional {
    /// Bounded finite pairing only; this does not establish primal optimality.
    pub fn verify_display_dual_pairing(
        dual: &[f64],
        primal: &[f64],
        claimed_evaluation: f64,
    ) -> Result<f64, DualWitnessError> {
        if dual.len() != primal.len() {
            return Err(DualWitnessError::DimensionMismatch);
        }
        if dual.iter().any(|v| !v.is_finite())
            || primal.iter().any(|v| !v.is_finite())
            || !claimed_evaluation.is_finite()
        {
            return Err(DualWitnessError::NonFiniteEntry);
        }
        let linf = dual.iter().map(|v| v.abs()).fold(0.0_f64, f64::max);
        if linf > 1.0 {
            return Err(DualWitnessError::DualNormBoundViolation);
        }
        let computed = dual
            .iter()
            .zip(primal.iter())
            .map(|(y, x)| y * x)
            .sum::<f64>();
        if computed != claimed_evaluation {
            return Err(DualWitnessError::EvaluationMismatch {
                claimed: claimed_evaluation,
                computed,
            });
        }
        Ok(computed)
    }
}

impl Phi1Functional {
    fn weighted_representative_term(
        weight: &core_kernel::bounded_rational::StackRational,
        x: &core_kernel::bounded_rational::StackRational,
        repair: &core_kernel::bounded_rational::StackRational,
    ) -> Result<
        core_kernel::bounded_rational::StackRational,
        core_kernel::bounded_rational::BoundedRationalError,
    > {
        use core_kernel::bounded_rational::{BoundedRationalError, StackRational};
        let weight = StackRational::new(weight.numerator, weight.denominator)?;
        let x = StackRational::new(x.numerator, x.denominator)?;
        let repair = StackRational::new(repair.numerator, repair.denominator)?;
        if weight.numerator < 0 {
            return Err(BoundedRationalError::Overflow);
        }
        weight.mul(x.sub(repair)?.abs())
    }

    /// Fixed-width weighted mass for a bounded proposal. Evaluation owns the
    /// residual subtraction, absolute values and reduction; no heap is allocated.
    pub fn bounded_representative_mass(
        weights: &[core_kernel::bounded_rational::StackRational],
        reading: &[core_kernel::bounded_rational::StackRational],
        exact_part: &[core_kernel::bounded_rational::StackRational],
    ) -> Result<
        core_kernel::bounded_rational::StackRational,
        core_kernel::bounded_rational::BoundedRationalError,
    > {
        use core_kernel::bounded_rational::{BoundedRationalError, StackRational};
        if weights.len() != reading.len() || reading.len() != exact_part.len() {
            return Err(BoundedRationalError::Overflow);
        }
        let mut value = StackRational::ZERO;
        for ((weight, x), repair) in weights.iter().zip(reading).zip(exact_part) {
            let term = Self::weighted_representative_term(weight, x, repair)?;
            value = value.add(term)?;
        }
        Ok(value)
    }
}

/// Bounded binary quotient evaluation. A capped search is only an upper bound.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BinaryPhi1Evaluation {
    pub weight: usize,
    pub representative: Vec<u8>,
    pub alpha: Vec<u8>,
    pub exact: bool,
    pub searched: u64,
    pub coset_size: u64,
}

impl Phi1Functional {
    fn build_binary_image_basis(rows: &[Vec<u8>], columns: usize) -> Vec<(Vec<u8>, Vec<u8>)> {
        let mut pivots: Vec<Option<(Vec<u8>, Vec<u8>)>> = vec![None; rows.len()];
        let mut basis = Vec::new();
        for column in 0..columns {
            let mut image: Vec<_> = rows.iter().map(|row| row[column] % 2).collect();
            let mut source = vec![0; columns];
            source[column] = 1;
            Self::insert_binary_pivot(&mut pivots, &mut basis, &mut image, &mut source);
        }
        basis
    }

    fn insert_binary_pivot(
        pivots: &mut [Option<(Vec<u8>, Vec<u8>)>],
        basis: &mut Vec<(Vec<u8>, Vec<u8>)>,
        image: &mut Vec<u8>,
        source: &mut Vec<u8>,
    ) {
        for high in (0..pivots.len()).rev() {
            if image[high] == 0 {
                continue;
            }
            if let Some((pivot, witness)) = &pivots[high] {
                for (x, y) in image.iter_mut().zip(pivot) {
                    *x ^= y;
                }
                for (x, y) in source.iter_mut().zip(witness) {
                    *x ^= y;
                }
            } else {
                pivots[high] = Some((image.clone(), source.clone()));
                basis.push((std::mem::take(image), std::mem::take(source)));
                break;
            }
        }
    }

    fn is_better_binary_rep(
        weight: usize,
        best_weight: usize,
        current: &[u8],
        best: &[u8],
    ) -> bool {
        if weight != best_weight {
            return weight < best_weight;
        }
        current.iter().rev().cmp(best.iter().rev()).is_lt()
    }

    /// Evaluate a binary coset by an independent image basis and Gray enumeration.
    /// The finite budget is explicit; no partial enumeration certifies a minimum.
    pub fn binary_coset_projection(
        rows: &[Vec<u8>],
        columns: usize,
        residual: &[u8],
        budget: u64,
    ) -> Result<BinaryPhi1Evaluation, String> {
        if budget == 0 {
            return Err("budget must be >= 1".into());
        }
        if rows.len() != residual.len() || rows.iter().any(|row| row.len() != columns) {
            return Err("binary coset dimensions differ".into());
        }
        let basis = Self::build_binary_image_basis(rows, columns);
        let rank = basis.len();
        let coset_size = if rank < 64 { 1u64 << rank } else { u64::MAX };
        let limit = coset_size.min(budget);
        let mut current: Vec<_> = residual.iter().map(|x| x % 2).collect();
        let mut alpha = vec![0u8; columns];
        let mut best = current.clone();
        let mut best_alpha = alpha.clone();
        let mass = |vector: &[u8]| vector.iter().filter(|x| **x != 0).count();
        let mut best_weight = mass(&best);
        for step in 1..limit {
            let (image, source) = &basis[step.trailing_zeros() as usize];
            for (x, y) in current.iter_mut().zip(image) {
                *x ^= y;
            }
            for (x, y) in alpha.iter_mut().zip(source) {
                *x ^= y;
            }
            let weight = mass(&current);
            if Self::is_better_binary_rep(weight, best_weight, &current, &best) {
                best_weight = weight;
                best.clone_from(&current);
                best_alpha.clone_from(&alpha);
            }
        }
        Ok(BinaryPhi1Evaluation {
            weight: best_weight,
            representative: best,
            alpha: best_alpha,
            exact: rank < 64 && coset_size <= budget,
            searched: limit,
            coset_size,
        })
    }
}

// Origin: engine/crates_rs/core_functional/src/phi1.rs
// Claim: urn:core:crates_rs:core-functional:phi1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn exact_repair_certificate() -> ExactPhi1Certificate {
        ExactPhi1Certificate {
            omega: vec![r(2)],
            d0: vec![vec![r(1)]],
            weights: vec![r(1)],
            alpha: vec![r(2)],
            primal_residual: vec![r(0)],
            dual_witness: vec![r(0)],
            reported_value: r(0),
        }
    }

    fn survivor_certificate() -> ExactPhi1Certificate {
        ExactPhi1Certificate {
            omega: vec![r(1)],
            d0: vec![vec![r(0)]],
            weights: vec![r(1)],
            alpha: vec![r(0)],
            primal_residual: vec![r(1)],
            dual_witness: vec![r(1)],
            reported_value: r(1),
        }
    }

    #[test]
    fn exact_certificate_proves_quotient_distance() {
        let verified =
            Phi1Functional::verify_exact_certificate(exact_repair_certificate()).unwrap();

        assert_eq!(verified.value(), &r(0));
    }

    #[test]
    fn certificate_export_is_read_only_and_modified_copies_need_reverification() {
        let submitted = survivor_certificate();
        let verified = Phi1Functional::verify_exact_certificate(submitted.clone()).unwrap();
        assert_eq!(verified.certificate(), &submitted);
        let mut changed = verified.certificate().clone();
        changed.reported_value = r(99);
        assert_eq!(
            Phi1Functional::verify_exact_certificate(changed),
            Err(ExactPhi1CertificateError::PrimalValueMismatch)
        );
        assert_eq!(verified.certificate(), &submitted);
    }

    #[test]
    fn zero_denominators_are_refused_in_every_certificate_field() {
        for field in 0..7 {
            let mut submitted = exact_repair_certificate();
            let invalid = BigRational::new_raw(1.into(), 0.into());
            match field {
                0 => submitted.omega[0] = invalid,
                1 => submitted.d0[0][0] = invalid,
                2 => submitted.weights[0] = invalid,
                3 => submitted.alpha[0] = invalid,
                4 => submitted.primal_residual[0] = invalid,
                5 => submitted.dual_witness[0] = invalid,
                _ => submitted.reported_value = invalid,
            }
            assert_eq!(
                Phi1Functional::verify_exact_certificate(submitted),
                Err(ExactPhi1CertificateError::ZeroRationalDenominator),
                "field {field}"
            );
        }
    }

    #[test]
    fn certificate_requires_matching_primal_residual() {
        let mut certificate = exact_repair_certificate();
        certificate.primal_residual[0] = r(2);

        assert_eq!(
            Phi1Functional::verify_exact_certificate(certificate),
            Err(ExactPhi1CertificateError::PrimalResidualMismatch { index: 0 })
        );
    }

    #[test]
    fn certificate_requires_dual_annihilator() {
        let mut certificate = exact_repair_certificate();
        certificate.dual_witness[0] = r(1);

        assert_eq!(
            Phi1Functional::verify_exact_certificate(certificate),
            Err(ExactPhi1CertificateError::DualAnnihilatorMismatch { column: 0 })
        );
    }

    #[test]
    fn certificate_requires_dual_norm_bound() {
        let mut certificate = survivor_certificate();
        certificate.dual_witness[0] = r(2);
        certificate.reported_value = r(2);

        assert_eq!(
            Phi1Functional::verify_exact_certificate(certificate),
            Err(ExactPhi1CertificateError::DualNormBoundViolation { index: 0 })
        );
    }

    #[test]
    fn certificate_requires_matching_dual_value() {
        let mut certificate = survivor_certificate();
        certificate.dual_witness[0] = r(0);

        assert_eq!(
            Phi1Functional::verify_exact_certificate(certificate),
            Err(ExactPhi1CertificateError::DualValueMismatch)
        );
    }

    #[test]
    fn certificate_rejects_missing_d0_c0_c1_data() {
        let mut missing_d0 = exact_repair_certificate();
        missing_d0.d0.clear();
        assert_eq!(
            Phi1Functional::verify_exact_certificate(missing_d0),
            Err(ExactPhi1CertificateError::D0RowMismatch {
                expected: 1,
                actual: 0
            })
        );

        let mut missing_c0 = exact_repair_certificate();
        missing_c0.alpha.clear();
        assert_eq!(
            Phi1Functional::verify_exact_certificate(missing_c0),
            Err(ExactPhi1CertificateError::D0ColumnMismatch {
                row: 0,
                expected: 0,
                actual: 1
            })
        );

        let mut missing_c1 = exact_repair_certificate();
        missing_c1.omega.clear();
        assert_eq!(
            Phi1Functional::verify_exact_certificate(missing_c1),
            Err(ExactPhi1CertificateError::CochainDimensionMismatch)
        );
    }

    #[test]
    fn certificate_rejects_negative_reported_value() {
        let mut certificate = exact_repair_certificate();
        certificate.reported_value = r(-1);
        assert_eq!(
            Phi1Functional::verify_exact_certificate(certificate),
            Err(ExactPhi1CertificateError::NegativeReportedValue)
        );
    }
}

#[cfg(test)]
mod arithmetic_tests {
    use super::*;

    #[test]
    fn integer_mass_rejects_overflow_and_mismatched_carriers() {
        assert_eq!(
            Phi1Functional::weighted_l1_i128(&[2, 3], &[-4, 5]),
            Some(23)
        );
        assert_eq!(Phi1Functional::weighted_l1_i128(&[1], &[]), None);
        assert_eq!(Phi1Functional::weighted_l1_i128(&[1], &[i128::MIN]), None);
        assert_eq!(Phi1Functional::weighted_l1_i128(&[-1], &[1]), None);
    }

    #[test]
    fn form_replay_checks_dual_gap() {
        let r = |value: i64| BigRational::from_integer(value.into());
        assert_eq!(
            Phi1Functional::replay_form(&[r(1)], &[r(2)], &[r(1)], &[]),
            Ok(r(2))
        );
        assert_eq!(
            Phi1Functional::replay_form(&[r(1)], &[r(2)], &[r(0)], &[]),
            Err(Phi1FormReplayError::DualityGapNonZero)
        );
        assert_eq!(
            Phi1Functional::replay_form(&[r(-1)], &[r(2)], &[r(0)], &[]),
            Err(Phi1FormReplayError::NegativeWeight { index: 0 })
        );
        assert_eq!(
            Phi1Functional::replay_form(
                &[r(1)],
                &[BigRational::new_raw(1.into(), 0.into())],
                &[r(0)],
                &[]
            ),
            Err(Phi1FormReplayError::ZeroRationalDenominator)
        );
    }
}

#[cfg(test)]
mod ownership_replay_tests {
    use super::*;
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }

    #[test]
    fn canonical_evaluation_builds_and_replays_the_complete_witness() {
        let measured = Phi1Functional::evaluate_exact_witness(
            &[q(2), q(0)],
            &[vec![q(1)], vec![q(1)]],
            &[q(1), q(1)],
            &[q(1)],
            &[q(1), q(-1)],
        )
        .unwrap();
        assert_eq!(measured.value(), &q(2));
        assert_eq!(measured.primal_residual(), &[q(1), q(-1)]);
        let mut altered = measured.certificate().clone();
        altered.reported_value = q(0);
        assert!(Phi1Functional::verify_exact_certificate(altered).is_err());
        assert!(Phi1Functional::evaluate_exact_witness(
            &[q(2), q(0)],
            &[vec![q(1)], vec![q(1)]],
            &[q(1), q(1)],
            &[q(1)],
            &[q(0), q(0)]
        )
        .is_err());
        assert!(Phi1Functional::weighted_l1_rational(&[q(-1)], &[q(1)]).is_none());
        assert!(Phi1Functional::weighted_l1_rational(
            &[q(1)],
            &[BigRational::new_raw(1.into(), 0.into())]
        )
        .is_none());
    }
    #[test]
    fn floating_replay_refuses_shapes_nonfinite_inputs_and_overflow() {
        use nalgebra::{DMatrix, DVector};
        let d0 = DMatrix::from_row_slice(2, 1, &[1.0, 1.0]);
        let v = |x: &[f64]| DVector::from_column_slice(x);
        let result = Phi1Functional::diagnose_primal_dual(
            &d0,
            &v(&[2.0, 0.0]),
            &v(&[1.0]),
            &v(&[1.0, -1.0]),
        )
        .unwrap();
        assert_eq!(
            (
                result.primal_mass,
                result.dual_pairing,
                result.identity_defect
            ),
            (2.0, 2.0, 0.0)
        );
        assert!(Phi1Functional::diagnose_primal_dual(
            &d0,
            &v(&[2.0]),
            &v(&[1.0]),
            &v(&[1.0, -1.0])
        )
        .is_err());
        assert!(Phi1Functional::diagnose_primal_dual(
            &d0,
            &v(&[f64::INFINITY, 0.0]),
            &v(&[1.0]),
            &v(&[1.0, -1.0])
        )
        .is_err());
        assert!(Phi1Functional::diagnose_primal_dual(
            &d0,
            &v(&[f64::MAX, f64::MAX]),
            &v(&[-f64::MAX]),
            &v(&[1.0, -1.0])
        )
        .is_err());
    }
    #[test]
    fn binary_projection_matches_independent_exhaustion_and_reports_caps() {
        let rows = vec![vec![1, 0], vec![1, 1], vec![0, 1]];
        for mask in 0..8 {
            let residual: Vec<u8> = (0..3).map(|i| (mask >> i) & 1).collect();
            let value = Phi1Functional::binary_coset_projection(&rows, 2, &residual, 4).unwrap();
            let expected = (0..4)
                .map(|a| {
                    (0..3)
                        .filter(|&i| {
                            residual[i] ^ (rows[i][0] * (a & 1)) ^ (rows[i][1] * ((a >> 1) & 1))
                                != 0
                        })
                        .count()
                })
                .min()
                .unwrap();
            assert!(value.exact);
            assert_eq!(value.weight, expected);
            for i in 0..3 {
                assert_eq!(
                    value.representative[i],
                    residual[i] ^ rows[i][0] * value.alpha[0] ^ rows[i][1] * value.alpha[1]
                );
            }
            assert!(
                !Phi1Functional::binary_coset_projection(&rows, 2, &residual, 1)
                    .unwrap()
                    .exact
            );
        }
        assert!(Phi1Functional::binary_coset_projection(&rows, 1, &[0, 0, 0], 4).is_err());
        assert!(Phi1Functional::binary_coset_projection(&rows, 2, &[0, 0, 0], 0).is_err());
    }
}
