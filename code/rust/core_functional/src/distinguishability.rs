//! Bounded trace-distance diagnostics on numerically admitted state inputs.
//!
//! Admission checks the submitted floating representation: exact Hermitian
//! symmetry, trace within a selected tolerance of one, and computed eigenvalues
//! at least minus that tolerance, with independently checked spectral residuals.
//! This is not exact positivity, a rounding certificate, physical-state proof,
//! a primary obstruction score, actor licensing or a workload verdict.

use linear_algebra::hermitian_eigen::{
    hermitian_eigen_checked, HermitianSpectrum, SpectrumError, SpectrumPolicy,
};
use nalgebra::{DMatrix, DVector};
use num_complex::Complex64;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum DistinguishabilityError {
    #[error("DIST_INVALID_STATE_TOLERANCE: {value}")]
    InvalidStateTolerance { value: f64 },
    #[error("DIST_SPECTRUM_{phase}: {error}")]
    Spectrum {
        phase: &'static str,
        error: SpectrumError,
    },
    #[error("DIST_TRACE_ARITHMETIC")]
    TraceArithmetic,
    #[error("DIST_TRACE_MISMATCH: {observed}, tolerance {tolerance}")]
    TraceMismatch { observed: f64, tolerance: f64 },
    #[error("DIST_NEGATIVE_EIGENVALUE: index {index}, value {value}, tolerance {tolerance}")]
    NegativeEigenvalue {
        index: usize,
        value: f64,
        tolerance: f64,
    },
    #[error("DIST_EMPTY_VECTOR")]
    EmptyVector,
    #[error("DIST_VECTOR_DIMENSION: {actual} exceeds {limit}")]
    VectorDimension { actual: usize, limit: usize },
    #[error("DIST_NONFINITE_VECTOR: index {index}")]
    NonFiniteVector { index: usize },
    #[error("DIST_VECTOR_NORM_ARITHMETIC")]
    VectorNormArithmetic,
    #[error("DIST_VECTOR_NORM_MISMATCH: {observed}, tolerance {tolerance}")]
    VectorNormMismatch { observed: f64, tolerance: f64 },
    #[error("DIST_OUTER_PRODUCT_UNDERFLOW: row {row}, column {column}")]
    OuterProductUnderflow { row: usize, column: usize },
    #[error("DIST_POLICY_BINDING: {side}")]
    PolicyBinding { side: &'static str },
    #[error("DIST_DIMENSION_BINDING: {left} versus {right}")]
    DimensionBinding { left: usize, right: usize },
    #[error("DIST_CONTRIBUTION_UNDERFLOW: index {index}")]
    ContributionUnderflow { index: usize },
    #[error("DIST_DISTANCE_ARITHMETIC")]
    DistanceArithmetic,
}

/// Immutable numerical policy; a large tolerance cannot make admission vacuous.
///
/// ~~~compile_fail
/// use core_functional::distinguishability::DistinguishabilityPolicy;
/// let forged: DistinguishabilityPolicy = serde_json::from_str("{}").unwrap();
/// ~~~
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct DistinguishabilityPolicy {
    spectrum: SpectrumPolicy,
    state_tolerance: f64,
}

impl DistinguishabilityPolicy {
    pub fn new(
        spectrum: SpectrumPolicy,
        state_tolerance: f64,
    ) -> Result<Self, DistinguishabilityError> {
        if !state_tolerance.is_finite() || !(f64::EPSILON..=1e-8).contains(&state_tolerance) {
            return Err(DistinguishabilityError::InvalidStateTolerance {
                value: state_tolerance,
            });
        }
        Ok(Self {
            spectrum,
            state_tolerance,
        })
    }
    pub fn spectrum(&self) -> SpectrumPolicy {
        self.spectrum
    }
    pub fn state_tolerance(&self) -> f64 {
        self.state_tolerance
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum DistinguishabilityAuthorityEffect {
    None,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
enum DensityOrigin {
    Matrix,
    PureVector {
        vector: DVector<Complex64>,
        norm_squared: f64,
    },
}

/// Numerically admitted representation, not an exact density or physical proof.
/// The original matrix/vector and observed defects are retained, not normalized.
/// No mutable getter or unchecked deserialization can change an admitted input.
///
/// ~~~compile_fail
/// use core_functional::distinguishability::DensityAdmission;
/// let forged: DensityAdmission = serde_json::from_str("{}").unwrap();
/// ~~~
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DensityAdmission {
    policy: DistinguishabilityPolicy,
    spectrum: HermitianSpectrum,
    origin: DensityOrigin,
    trace: f64,
    maximum_negative_eigenvalue_magnitude: f64,
}

impl DensityAdmission {
    pub fn policy(&self) -> DistinguishabilityPolicy {
        self.policy
    }
    pub fn spectrum(&self) -> &HermitianSpectrum {
        &self.spectrum
    }
    pub fn matrix(&self) -> &DMatrix<Complex64> {
        self.spectrum.matrix()
    }
    pub fn trace(&self) -> f64 {
        self.trace
    }
    pub fn maximum_negative_eigenvalue_magnitude(&self) -> f64 {
        self.maximum_negative_eigenvalue_magnitude
    }
    pub fn original_vector(&self) -> Option<&DVector<Complex64>> {
        match &self.origin {
            DensityOrigin::Matrix => None,
            DensityOrigin::PureVector { vector, .. } => Some(vector),
        }
    }
    pub fn original_vector_norm_squared(&self) -> Option<f64> {
        match self.origin {
            DensityOrigin::Matrix => None,
            DensityOrigin::PureVector { norm_squared, .. } => Some(norm_squared),
        }
    }
}

/// Half the sum of absolute eigenvalues of the full Hermitian difference.
/// Every contribution and both original admissions remain independently visible.
/// No overlap clamping, probability interpretation or successful-task flag exists.
///
/// ~~~compile_fail
/// use core_functional::distinguishability::TraceDistanceDiagnostic;
/// let forged: TraceDistanceDiagnostic = serde_json::from_str("{}").unwrap();
/// ~~~
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct TraceDistanceDiagnostic {
    authority_effect: DistinguishabilityAuthorityEffect,
    policy: DistinguishabilityPolicy,
    left: DensityAdmission,
    right: DensityAdmission,
    difference: HermitianSpectrum,
    half_absolute_eigenvalues: Vec<f64>,
    trace_distance: f64,
}

impl TraceDistanceDiagnostic {
    pub fn authority_effect(&self) -> DistinguishabilityAuthorityEffect {
        self.authority_effect
    }
    pub fn policy(&self) -> DistinguishabilityPolicy {
        self.policy
    }
    pub fn left(&self) -> &DensityAdmission {
        &self.left
    }
    pub fn right(&self) -> &DensityAdmission {
        &self.right
    }
    pub fn difference(&self) -> &HermitianSpectrum {
        &self.difference
    }
    pub fn half_absolute_eigenvalues(&self) -> &[f64] {
        &self.half_absolute_eigenvalues
    }
    pub fn trace_distance(&self) -> f64 {
        self.trace_distance
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct DistinguishabilityFunctional {
    policy: DistinguishabilityPolicy,
}

impl DistinguishabilityFunctional {
    /// Total variation of two declared rational coordinate lists.
    pub fn rational_total_variation(
        left: &[num_rational::BigRational],
        right: &[num_rational::BigRational],
    ) -> Option<num_rational::BigRational> {
        use num_traits::Zero;
        if left.len() != right.len() || left.iter().chain(right).any(|x| x.denom().is_zero()) {
            return None;
        }
        let delta: Vec<_> = left.iter().zip(right).map(|(a, b)| a - b).collect();
        Some(
            crate::Phi1Functional::unweighted_l1_rational(&delta)?
                / num_rational::BigRational::from_integer(2.into()),
        )
    }

    /// Exact squared trace distance of real rational qubit densities.
    pub fn qubit_trace_distance_squared(
        left: &[Vec<num_rational::BigRational>],
        right: &[Vec<num_rational::BigRational>],
    ) -> Result<num_rational::BigRational, &'static str> {
        use num_rational::BigRational;
        use num_traits::{One, Signed, Zero};
        for matrix in [left, right] {
            if matrix.len() != 2 || matrix.iter().any(|row| row.len() != 2) {
                return Err("trace_distance_2x2 is specialized for dimension 2");
            }
            if matrix.iter().flatten().any(|x| x.denom().is_zero()) {
                return Err("invalid rational density entry");
            }
            if matrix[0][1] != matrix[1][0]
                || &matrix[0][0] + &matrix[1][1] != BigRational::one()
                || matrix[0][0].is_negative()
                || matrix[1][1].is_negative()
                || &matrix[0][0] * &matrix[1][1] - &matrix[0][1] * &matrix[1][0]
                    < BigRational::zero()
            {
                return Err("Trace distance requires valid density matrices");
            }
        }
        let a = &left[0][0] - &right[0][0];
        let b = &left[0][1] - &right[0][1];
        Ok(&a * &a + &b * &b)
    }

    /// Rational distance only when its square has an exact rational root.
    pub fn qubit_trace_distance(
        left: &[Vec<num_rational::BigRational>],
        right: &[Vec<num_rational::BigRational>],
    ) -> Result<num_rational::BigRational, &'static str> {
        let squared = Self::qubit_trace_distance_squared(left, right)?;
        let numerator = squared.numer().sqrt();
        let denominator = squared.denom().sqrt();
        if &numerator * &numerator != *squared.numer()
            || &denominator * &denominator != *squared.denom()
        {
            return Err("Trace distance is irrational; use trace_distance_squared_2x2");
        }
        Ok(num_rational::BigRational::new(numerator, denominator))
    }

    /// Exact loss of squared distinguishability under the diagonal shadow.
    pub fn qubit_shadow_contraction_slack(
        left: &[Vec<num_rational::BigRational>],
        right: &[Vec<num_rational::BigRational>],
    ) -> Result<num_rational::BigRational, &'static str> {
        let squared = Self::qubit_trace_distance_squared(left, right)?;
        let a = &left[0][0] - &right[0][0];
        Ok(squared - &a * &a)
    }

    pub fn new(policy: DistinguishabilityPolicy) -> Self {
        Self { policy }
    }
    pub fn policy(&self) -> DistinguishabilityPolicy {
        self.policy
    }

    pub fn admit_matrix(
        &self,
        matrix: &DMatrix<Complex64>,
    ) -> Result<DensityAdmission, DistinguishabilityError> {
        let spectrum = hermitian_eigen_checked(matrix, self.policy.spectrum).map_err(|error| {
            DistinguishabilityError::Spectrum {
                phase: "ADMISSION",
                error,
            }
        })?;
        let trace = (0..matrix.nrows()).map(|i| matrix[(i, i)].re).sum::<f64>();
        if !trace.is_finite() {
            return Err(DistinguishabilityError::TraceArithmetic);
        }
        if (trace - 1.0).abs() > self.policy.state_tolerance {
            return Err(DistinguishabilityError::TraceMismatch {
                observed: trace,
                tolerance: self.policy.state_tolerance,
            });
        }
        let mut maximum_negative_eigenvalue_magnitude = 0.0_f64;
        for (index, &value) in spectrum.eigenvalues().iter().enumerate() {
            if value < -self.policy.state_tolerance {
                return Err(DistinguishabilityError::NegativeEigenvalue {
                    index,
                    value,
                    tolerance: self.policy.state_tolerance,
                });
            }
            // Positive part is the explicitly named negativity defect, not a
            // repair or clamp of the matrix or the computed eigenvalues.
            maximum_negative_eigenvalue_magnitude =
                maximum_negative_eigenvalue_magnitude.max(-value);
        }
        Ok(DensityAdmission {
            policy: self.policy,
            spectrum,
            origin: DensityOrigin::Matrix,
            trace,
            maximum_negative_eigenvalue_magnitude,
        })
    }

    fn validate_unit_vector(
        &self,
        vector: &DVector<Complex64>,
    ) -> Result<(usize, f64), DistinguishabilityError> {
        let dimension = vector.len();
        if dimension == 0 {
            return Err(DistinguishabilityError::EmptyVector);
        }
        if dimension > self.policy.spectrum.max_dimension() {
            return Err(DistinguishabilityError::VectorDimension {
                actual: dimension,
                limit: self.policy.spectrum.max_dimension(),
            });
        }
        // Validate the bounded vector before allocating a dense outer product.
        for (index, value) in vector.iter().enumerate() {
            if !value.re.is_finite() || !value.im.is_finite() {
                return Err(DistinguishabilityError::NonFiniteVector { index });
            }
        }
        let norm_squared = vector.iter().map(|v| v.norm_sqr()).sum::<f64>();
        if !norm_squared.is_finite() {
            return Err(DistinguishabilityError::VectorNormArithmetic);
        }
        if (norm_squared - 1.0).abs() > self.policy.state_tolerance {
            return Err(DistinguishabilityError::VectorNormMismatch {
                observed: norm_squared,
                tolerance: self.policy.state_tolerance,
            });
        }
        Ok((dimension, norm_squared))
    }

    fn build_pure_state_matrix(
        vector: &DVector<Complex64>,
        dimension: usize,
    ) -> Result<DMatrix<Complex64>, DistinguishabilityError> {
        let mut matrix = DMatrix::zeros(dimension, dimension);
        let zero = Complex64::new(0.0, 0.0);
        for row in 0..dimension {
            for column in 0..=row {
                let product = vector[row] * vector[column].conj();
                let non_zero_inputs = vector[row] != zero && vector[column] != zero;
                if product == zero && non_zero_inputs {
                    return Err(DistinguishabilityError::OuterProductUnderflow { row, column });
                }
                matrix[(row, column)] = product;
                matrix[(column, row)] = product.conj();
            }
        }
        Ok(matrix)
    }

    pub fn admit_pure_vector(
        &self,
        vector: &DVector<Complex64>,
    ) -> Result<DensityAdmission, DistinguishabilityError> {
        let (dimension, norm_squared) = self.validate_unit_vector(vector)?;
        let matrix = Self::build_pure_state_matrix(vector, dimension)?;
        let mut admitted = self.admit_matrix(&matrix)?;
        admitted.origin = DensityOrigin::PureVector {
            vector: vector.clone(),
            norm_squared,
        };
        Ok(admitted)
    }

    pub fn trace_distance(
        &self,
        left: &DensityAdmission,
        right: &DensityAdmission,
    ) -> Result<TraceDistanceDiagnostic, DistinguishabilityError> {
        // Bind both selected policies and dimensions before subtraction/cloning.
        if left.policy != self.policy {
            return Err(DistinguishabilityError::PolicyBinding { side: "left" });
        }
        if right.policy != self.policy {
            return Err(DistinguishabilityError::PolicyBinding { side: "right" });
        }
        if left.matrix().nrows() != right.matrix().nrows() {
            return Err(DistinguishabilityError::DimensionBinding {
                left: left.matrix().nrows(),
                right: right.matrix().nrows(),
            });
        }
        let matrix = left.matrix() - right.matrix();
        let difference =
            hermitian_eigen_checked(&matrix, self.policy.spectrum).map_err(|error| {
                DistinguishabilityError::Spectrum {
                    phase: "DIFFERENCE",
                    error,
                }
            })?;
        let (contributions, sum) = checked_trace_contributions(difference.eigenvalues())?;
        Ok(TraceDistanceDiagnostic {
            authority_effect: DistinguishabilityAuthorityEffect::None,
            policy: self.policy,
            left: left.clone(),
            right: right.clone(),
            difference,
            half_absolute_eigenvalues: contributions,
            trace_distance: sum,
        })
    }
}

// This private arithmetic kernel is also exercised directly with finite values
// whose sum overflows, without forging an admitted state or spectral result.
fn checked_trace_contributions(values: &[f64]) -> Result<(Vec<f64>, f64), DistinguishabilityError> {
    let mut contributions = Vec::with_capacity(values.len());
    let mut sum = 0.0_f64;
    let mut compensation = 0.0_f64;
    for (index, &value) in values.iter().enumerate() {
        let contribution = value.abs() * 0.5;
        if value != 0.0 && contribution == 0.0 {
            return Err(DistinguishabilityError::ContributionUnderflow { index });
        }
        contributions.push(contribution);
        let corrected = contribution - compensation;
        let next = sum + corrected;
        compensation = (next - sum) - corrected;
        sum = next;
    }
    if !sum.is_finite() {
        return Err(DistinguishabilityError::DistanceArithmetic);
    }
    Ok((contributions, sum))
}

// Origin: engine/crates_rs/core_functional/src/distinguishability.rs
// Claim: urn:core:crates_rs:core-functional:distinguishability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn arithmetic_accumulator_refuses_finite_overflow_and_nonfinite_input() {
        for values in [
            vec![f64::MAX; 3],
            vec![f64::INFINITY],
            vec![f64::NEG_INFINITY],
            vec![f64::NAN],
        ] {
            assert_eq!(
                checked_trace_contributions(&values).unwrap_err(),
                DistinguishabilityError::DistanceArithmetic
            );
        }
        assert_eq!(
            checked_trace_contributions(&[-2.0, 4.0]).unwrap(),
            (vec![1.0, 2.0], 3.0)
        );
    }

    #[test]
    fn compensated_half_sum_preserves_a_three_quarter_ulp_tail() {
        // Each small half-contribution is exactly a quarter ULP at one.
        // Naive sequential addition rounds every small term away. Three such
        // terms must instead round the aggregate to the next f64 above one.
        let small = f64::EPSILON / 2.0;
        let values = [-2.0, -small, -small, -small];
        let (contributions, sum) = checked_trace_contributions(&values).unwrap();
        assert_eq!(
            contributions,
            vec![1.0, small / 2.0, small / 2.0, small / 2.0]
        );
        assert_eq!(sum, 1.0 + f64::EPSILON);
        assert_eq!(contributions.iter().copied().sum::<f64>(), 1.0);
    }

    fn c(re: f64, im: f64) -> Complex64 {
        Complex64::new(re, im)
    }

    #[test]
    fn finite_spectrum_does_not_authorize_an_overflowed_trace() {
        let matrix = diagonal(&[f64::MAX / 2.0; 4]);
        hermitian_eigen_checked(&matrix, policy().spectrum()).unwrap();
        assert_eq!(
            owner().admit_matrix(&matrix).unwrap_err(),
            DistinguishabilityError::TraceArithmetic
        );
    }

    #[test]
    fn admitted_inputs_do_not_authorize_exceeding_the_difference_solver_budget() {
        let make_owner = |budget| {
            DistinguishabilityFunctional::new(
                DistinguishabilityPolicy::new(
                    SpectrumPolicy::new(4, budget, f64::EPSILON, 1e-12).unwrap(),
                    1e-10,
                )
                .unwrap(),
            )
        };
        let left = DVector::from_vec(vec![c(0.0, 0.0), c(1.0, 0.0), c(0.0, 0.0), c(0.0, 0.0)]);
        let right = DVector::from_element(4, c(0.5, 0.0));
        let owner = make_owner(2);
        let admitted_left = owner.admit_pure_vector(&left).unwrap();
        let admitted_right = owner.admit_pure_vector(&right).unwrap();
        assert_eq!(
            owner
                .trace_distance(&admitted_left, &admitted_right)
                .unwrap_err(),
            DistinguishabilityError::Spectrum {
                phase: "DIFFERENCE",
                error: SpectrumError::IterationLimit { limit: 2 }
            }
        );
        // Independent rank-one formula: overlap magnitude squared is 1/4.
        let owner = make_owner(100);
        let result = owner
            .trace_distance(
                &owner.admit_pure_vector(&left).unwrap(),
                &owner.admit_pure_vector(&right).unwrap(),
            )
            .unwrap();
        close(result.trace_distance(), 0.75_f64.sqrt());
    }
    fn policy() -> DistinguishabilityPolicy {
        DistinguishabilityPolicy::new(
            SpectrumPolicy::new(16, 10_000, 1e-14, 1e-12).unwrap(),
            1e-10,
        )
        .unwrap()
    }
    fn owner() -> DistinguishabilityFunctional {
        DistinguishabilityFunctional::new(policy())
    }
    fn diagonal(values: &[f64]) -> DMatrix<Complex64> {
        DMatrix::from_diagonal(&DVector::from_iterator(
            values.len(),
            values.iter().map(|&v| c(v, 0.0)),
        ))
    }
    fn close(actual: f64, expected: f64) {
        assert!((actual - expected).abs() <= 2e-12, "{actual} != {expected}");
    }
    fn ratio(value: [i64; 2]) -> f64 {
        assert!(value[1] > 0);
        value[0] as f64 / value[1] as f64
    }

    #[test]
    fn independent_rational_fixtures_cover_mixed_complex_and_degenerate_states() {
        #[derive(serde::Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Fixtures {
            schema: String,
            authority_effect: String,
            diagonal_cases: Vec<DiagonalCase>,
            pure_cases: Vec<PureCase>,
        }
        #[derive(serde::Deserialize)]
        #[serde(deny_unknown_fields)]
        struct DiagonalCase {
            name: String,
            left: Vec<[i64; 2]>,
            right: Vec<[i64; 2]>,
            eigenvalues: Vec<[i64; 2]>,
            distance: [i64; 2],
        }
        #[derive(serde::Deserialize)]
        #[serde(deny_unknown_fields)]
        struct PureCase {
            name: String,
            left: Vec<[[i64; 2]; 2]>,
            right: Vec<[[i64; 2]; 2]>,
            eigenvalues: Vec<[i64; 2]>,
            distance: [i64; 2],
        }
        let fixtures: Fixtures = serde_json::from_str(include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../tests/core_functional/fixtures/state_trace_distance.json"
        )))
        .unwrap();
        assert_eq!(fixtures.schema, "core.state-trace-distance.fixtures.v1");
        assert_eq!(fixtures.authority_effect, "None");
        assert_eq!(fixtures.diagonal_cases.len(), 5);
        assert_eq!(fixtures.pure_cases.len(), 2);
        let mut names = std::collections::BTreeSet::new();
        let owner = owner();
        for case in fixtures.diagonal_cases {
            assert!(names.insert(case.name));
            let left = diagonal(&case.left.into_iter().map(ratio).collect::<Vec<_>>());
            let right = diagonal(&case.right.into_iter().map(ratio).collect::<Vec<_>>());
            let result = owner
                .trace_distance(
                    &owner.admit_matrix(&left).unwrap(),
                    &owner.admit_matrix(&right).unwrap(),
                )
                .unwrap();
            check_result(&result, &case.eigenvalues, case.distance);
        }
        for case in fixtures.pure_cases {
            assert!(names.insert(case.name));
            let make = |v: Vec<[[i64; 2]; 2]>| {
                DVector::from_iterator(
                    v.len(),
                    v.into_iter().map(|[re, im]| c(ratio(re), ratio(im))),
                )
            };
            let left = make(case.left);
            let right = make(case.right);
            let result = owner
                .trace_distance(
                    &owner.admit_pure_vector(&left).unwrap(),
                    &owner.admit_pure_vector(&right).unwrap(),
                )
                .unwrap();
            check_result(&result, &case.eigenvalues, case.distance);
            assert_eq!(result.left().original_vector(), Some(&left));
            assert_eq!(result.right().original_vector(), Some(&right));
        }
        assert_eq!(names.len(), 7);
    }

    fn check_result(result: &TraceDistanceDiagnostic, values: &[[i64; 2]], distance: [i64; 2]) {
        assert_eq!(result.difference().eigenvalues().len(), values.len());
        assert_eq!(result.half_absolute_eigenvalues().len(), values.len());
        for (index, &expected) in values.iter().enumerate() {
            close(result.difference().eigenvalues()[index], ratio(expected));
            close(
                result.half_absolute_eigenvalues()[index],
                ratio(expected).abs() * 0.5,
            );
        }
        close(result.trace_distance(), ratio(distance));
        assert_eq!(
            result.authority_effect(),
            DistinguishabilityAuthorityEffect::None
        );
        assert_eq!(result.policy(), policy());
        assert_eq!(result.left().spectrum().policy(), policy().spectrum());
        assert_eq!(result.right().spectrum().policy(), policy().spectrum());
        assert_eq!(result.difference().policy(), policy().spectrum());
        assert_eq!(
            result.difference().matrix(),
            &(result.left().matrix() - result.right().matrix())
        );
    }

    #[test]
    fn selected_policy_rejects_nonfinite_or_vacuous_state_tolerances() {
        for value in [
            f64::NAN,
            f64::INFINITY,
            f64::NEG_INFINITY,
            -1.0,
            0.0,
            f64::EPSILON / 2.0,
            1.0001e-8,
        ] {
            let error = DistinguishabilityPolicy::new(policy().spectrum(), value).unwrap_err();
            assert!(
                matches!(error,DistinguishabilityError::InvalidStateTolerance{value: actual} if actual.to_bits()==value.to_bits())
            );
        }
        for value in [f64::EPSILON, 1e-8] {
            assert_eq!(
                DistinguishabilityPolicy::new(policy().spectrum(), value)
                    .unwrap()
                    .state_tolerance(),
                value
            );
        }
    }

    #[test]
    fn matrix_shape_empty_and_dimension_refusals_preserve_the_native_mechanism() {
        let owner = owner();
        for (matrix, error) in [
            (
                DMatrix::zeros(2, 3),
                SpectrumError::NotSquare {
                    rows: 2,
                    columns: 3,
                },
            ),
            (DMatrix::zeros(0, 0), SpectrumError::EmptyMatrix),
            (
                DMatrix::from_element(17, 17, c(f64::NAN, 0.0)),
                SpectrumError::DimensionLimit {
                    actual: 17,
                    limit: 16,
                },
            ),
        ] {
            assert_eq!(
                owner.admit_matrix(&matrix).unwrap_err(),
                DistinguishabilityError::Spectrum {
                    phase: "ADMISSION",
                    error
                }
            );
        }
    }

    #[test]
    fn every_input_triangle_and_imaginary_component_remains_checked() {
        let owner = owner();
        for value in [c(f64::NAN, 0.0), c(0.0, f64::INFINITY)] {
            let mut matrix = diagonal(&[0.5, 0.5]);
            matrix[(0, 1)] = value;
            assert_eq!(
                owner.admit_matrix(&matrix).unwrap_err(),
                DistinguishabilityError::Spectrum {
                    phase: "ADMISSION",
                    error: SpectrumError::NonFiniteInput { row: 0, column: 1 }
                }
            );
        }
        let mut matrix = diagonal(&[0.5, 0.5]);
        matrix[(0, 1)] = c(0.1, 0.0);
        assert_eq!(
            owner.admit_matrix(&matrix).unwrap_err(),
            DistinguishabilityError::Spectrum {
                phase: "ADMISSION",
                error: SpectrumError::NotHermitian { row: 1, column: 0 }
            }
        );
        matrix = diagonal(&[0.5, 0.5]);
        matrix[(1, 1)].im = 0.001;
        assert_eq!(
            owner.admit_matrix(&matrix).unwrap_err(),
            DistinguishabilityError::Spectrum {
                phase: "ADMISSION",
                error: SpectrumError::NotHermitian { row: 1, column: 1 }
            }
        );
    }

    #[test]
    fn trace_mismatch_is_not_normalized_into_an_admitted_state() {
        let owner = owner();
        for trace in [0.0, 0.5, 1.0 + 1e-6, 2.0] {
            assert_eq!(
                owner.admit_matrix(&diagonal(&[trace, 0.0])).unwrap_err(),
                DistinguishabilityError::TraceMismatch {
                    observed: trace,
                    tolerance: policy().state_tolerance()
                }
            );
        }
        let admitted = owner.admit_matrix(&diagonal(&[0.25, 0.75])).unwrap();
        assert_eq!(admitted.trace(), 1.0);
        assert_eq!(admitted.original_vector(), None);
        assert_eq!(admitted.original_vector_norm_squared(), None);
    }

    #[test]
    fn positive_diagonal_does_not_hide_a_negative_eigenvalue() {
        let matrix =
            DMatrix::from_row_slice(2, 2, &[c(0.5, 0.0), c(1.0, 0.0), c(1.0, 0.0), c(0.5, 0.0)]);
        let error = owner().admit_matrix(&matrix).unwrap_err();
        match error {
            DistinguishabilityError::NegativeEigenvalue {
                index,
                value,
                tolerance,
            } => {
                assert_eq!(index, 0);
                close(value, -0.5);
                assert_eq!(tolerance, policy().state_tolerance());
            }
            other => panic!("wrong refusal: {other}"),
        }
    }

    #[test]
    fn near_unit_vector_slack_is_recorded_without_renormalizing() {
        let owner = owner();
        let amplitude = 1.0 + 2.0_f64.powi(-36);
        let vector = DVector::from_vec(vec![c(amplitude, 0.0), c(0.0, 0.0)]);
        let norm_squared = amplitude * amplitude;
        let admitted = owner.admit_pure_vector(&vector).unwrap();
        assert!(norm_squared > 1.0 && norm_squared - 1.0 < policy().state_tolerance());
        assert_eq!(admitted.original_vector(), Some(&vector));
        assert_eq!(admitted.original_vector_norm_squared(), Some(norm_squared));
        assert_eq!(admitted.matrix()[(0, 0)], c(norm_squared, 0.0));
        assert_eq!(admitted.trace(), norm_squared);
        let basis = owner.admit_matrix(&diagonal(&[1.0, 0.0])).unwrap();
        let result = owner.trace_distance(&admitted, &basis).unwrap();
        assert_eq!(result.trace_distance(), 0.5 * (norm_squared - 1.0));
        assert!(result.trace_distance() > 0.0);
    }

    #[test]
    fn approximate_admission_retains_negativity_and_does_not_clamp_distance() {
        let tolerance = 1e-8;
        let delta = 2.0_f64.powi(-30);
        let policy = DistinguishabilityPolicy::new(policy().spectrum(), tolerance).unwrap();
        let owner = DistinguishabilityFunctional::new(policy);
        let left = diagonal(&[1.0 + delta, -delta]);
        let right = diagonal(&[-delta, 1.0 + delta]);
        let admitted = owner.admit_matrix(&left).unwrap();
        assert_eq!(admitted.matrix(), &left);
        assert_eq!(admitted.maximum_negative_eigenvalue_magnitude(), delta);
        assert_eq!(admitted.spectrum().eigenvalues()[0], -delta);
        let result = owner
            .trace_distance(&admitted, &owner.admit_matrix(&right).unwrap())
            .unwrap();
        // Near-density input is not exact PSD; this is not a probability.
        assert_eq!(result.trace_distance(), 1.0 + 2.0 * delta);
        assert!(result.trace_distance() > 1.0);
        assert_eq!(result.policy().state_tolerance(), tolerance);
    }

    #[test]
    fn vector_dimension_limits_precede_dense_allocation_and_nonfinite_admission() {
        let owner = owner();
        assert_eq!(
            owner.admit_pure_vector(&DVector::zeros(0)).unwrap_err(),
            DistinguishabilityError::EmptyVector
        );
        assert_eq!(
            owner
                .admit_pure_vector(&DVector::from_element(17, c(f64::NAN, 0.0)))
                .unwrap_err(),
            DistinguishabilityError::VectorDimension {
                actual: 17,
                limit: 16
            }
        );
    }

    #[test]
    fn all_pure_vector_components_are_checked_before_norm_arithmetic() {
        for value in [c(f64::NAN, 0.0), c(0.0, f64::INFINITY)] {
            let vector = DVector::from_vec(vec![c(f64::MAX, 0.0), value]);
            assert_eq!(
                owner().admit_pure_vector(&vector).unwrap_err(),
                DistinguishabilityError::NonFiniteVector { index: 1 }
            );
        }
    }

    #[test]
    fn finite_overflowing_vector_norm_is_a_typed_arithmetic_refusal() {
        assert_eq!(
            owner()
                .admit_pure_vector(&DVector::from_element(2, c(f64::MAX, 0.0)))
                .unwrap_err(),
            DistinguishabilityError::VectorNormArithmetic
        );
    }

    #[test]
    fn zero_and_unnormalized_vectors_are_not_silently_repaired() {
        for (vector, observed) in [
            (vec![c(0.0, 0.0), c(0.0, 0.0)], 0.0),
            (vec![c(1.0, 0.0), c(1.0, 0.0)], 2.0),
            (vec![c(2.0, 0.0), c(0.0, 0.0)], 4.0),
        ] {
            assert_eq!(
                owner()
                    .admit_pure_vector(&DVector::from_vec(vector))
                    .unwrap_err(),
                DistinguishabilityError::VectorNormMismatch {
                    observed,
                    tolerance: policy().state_tolerance()
                }
            );
        }
    }

    #[test]
    fn nonzero_outer_products_cannot_disappear_under_floating_underflow() {
        let vector = DVector::from_vec(vec![c(1.0, 0.0), c(f64::from_bits(1), 0.0)]);
        assert_eq!(
            owner().admit_pure_vector(&vector).unwrap_err(),
            DistinguishabilityError::OuterProductUnderflow { row: 1, column: 1 }
        );
    }

    #[test]
    fn original_pure_vectors_norms_and_complex_phases_are_retained() {
        let vector = DVector::from_vec(vec![c(0.6, 0.0), c(0.0, 0.8)]);
        let admitted = owner().admit_pure_vector(&vector).unwrap();
        assert_eq!(admitted.original_vector(), Some(&vector));
        close(admitted.original_vector_norm_squared().unwrap(), 1.0);
        close(admitted.matrix()[(0, 1)].im, -0.48);
        close(admitted.matrix()[(1, 0)].im, 0.48);
        assert_eq!(admitted.policy(), policy());
    }

    #[test]
    fn both_admissions_must_match_the_selected_numerical_policy() {
        let first = owner();
        let other = DistinguishabilityFunctional::new(
            DistinguishabilityPolicy::new(policy().spectrum(), 1e-8).unwrap(),
        );
        let same = first.admit_matrix(&diagonal(&[1.0, 0.0])).unwrap();
        let different = other.admit_matrix(&diagonal(&[1.0, 0.0])).unwrap();
        assert_eq!(
            first.trace_distance(&different, &same).unwrap_err(),
            DistinguishabilityError::PolicyBinding { side: "left" }
        );
        assert_eq!(
            first.trace_distance(&same, &different).unwrap_err(),
            DistinguishabilityError::PolicyBinding { side: "right" }
        );
    }

    #[test]
    fn mismatched_dimensions_refuse_instead_of_truncating_or_panicking() {
        let owner = owner();
        let left = owner.admit_matrix(&diagonal(&[1.0, 0.0])).unwrap();
        let right = owner.admit_matrix(&diagonal(&[1.0, 0.0, 0.0])).unwrap();
        assert_eq!(
            owner.trace_distance(&left, &right).unwrap_err(),
            DistinguishabilityError::DimensionBinding { left: 2, right: 3 }
        );
    }

    #[test]
    fn a_nonzero_half_eigenvalue_cannot_be_reported_as_zero_distance() {
        let owner = owner();
        let left = owner.admit_matrix(&diagonal(&[1.0, 0.0])).unwrap();
        let right = owner
            .admit_matrix(&diagonal(&[1.0, f64::from_bits(1)]))
            .unwrap();
        assert_eq!(
            owner.trace_distance(&left, &right).unwrap_err(),
            DistinguishabilityError::ContributionUnderflow { index: 0 }
        );
    }

    #[test]
    fn result_retains_all_contributions_and_owns_its_original_inputs() {
        let owner = owner();
        let mut matrix = diagonal(&[0.5, 0.25, 0.125, 0.125]);
        let left = owner.admit_matrix(&matrix).unwrap();
        matrix[(0, 0)] = c(7.0, 0.0);
        let right = owner
            .admit_matrix(&diagonal(&[0.125, 0.125, 0.25, 0.5]))
            .unwrap();
        let result = owner.trace_distance(&left, &right).unwrap();
        assert_eq!(result.left(), &left);
        assert_eq!(result.right(), &right);
        assert_eq!(result.left().matrix()[(0, 0)], c(0.5, 0.0));
        assert_eq!(
            result.half_absolute_eigenvalues(),
            &[0.1875, 0.0625, 0.0625, 0.1875]
        );
        assert_eq!(result.trace_distance(), 0.5);
        assert_eq!(
            result.authority_effect(),
            DistinguishabilityAuthorityEffect::None
        );
    }

    #[test]
    fn exhausted_native_spectral_budget_cannot_become_state_admission() {
        let policy = DistinguishabilityPolicy::new(
            SpectrumPolicy::new(4, 1, f64::EPSILON, 1e-12).unwrap(),
            1e-10,
        )
        .unwrap();
        let matrix = DMatrix::from_fn(4, 4, |r, c_| {
            c(
                if r == c_ {
                    0.25
                } else if r.abs_diff(c_) == 1 {
                    0.125
                } else {
                    0.0
                },
                0.0,
            )
        });
        assert_eq!(
            DistinguishabilityFunctional::new(policy)
                .admit_matrix(&matrix)
                .unwrap_err(),
            DistinguishabilityError::Spectrum {
                phase: "ADMISSION",
                error: SpectrumError::IterationLimit { limit: 1 }
            }
        );
    }
}
