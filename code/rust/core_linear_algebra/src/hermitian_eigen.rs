//! Checked bounded Hermitian eigenpairs in a numerical scalar representation.
//! Every input triangle is checked; normalized residuals and orthonormality replay
//! independently. These are numerical diagnostics and never exact certificates.
//! AuthorityEffect: None.
use nalgebra::{DMatrix, DVector, SymmetricEigen};
use num_complex::Complex64;
use serde::Serialize;
pub const MAX_SPECTRUM_DIMENSION: usize = 256;
pub const MAX_SPECTRUM_ITERATIONS: usize = 100_000;

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum SpectrumError {
    #[error("SPECTRUM_INVALID_POLICY: {field}")]
    InvalidPolicy { field: &'static str },
    #[error("SPECTRUM_NOT_SQUARE: {rows} by {columns}")]
    NotSquare { rows: usize, columns: usize },
    #[error("SPECTRUM_EMPTY_MATRIX")]
    EmptyMatrix,
    #[error("SPECTRUM_DIMENSION_LIMIT: {actual} exceeds {limit}")]
    DimensionLimit { actual: usize, limit: usize },
    #[error("SPECTRUM_NONFINITE_INPUT: row {row}, column {column}")]
    NonFiniteInput { row: usize, column: usize },
    #[error("SPECTRUM_NOT_HERMITIAN: row {row}, column {column}")]
    NotHermitian { row: usize, column: usize },
    #[error("SPECTRUM_ITERATION_LIMIT: {limit}")]
    IterationLimit { limit: usize },
    #[error("SPECTRUM_SCALING_UNDERFLOW: row {row}, column {column}")]
    ScalingUnderflow { row: usize, column: usize },
    #[error("SPECTRUM_INVALID_EIGENPAIR_SHAPE")]
    EigenpairShape,
    #[error("SPECTRUM_NONFINITE_EIGENPAIR")]
    NonFiniteEigenpair,
    #[error("SPECTRUM_VALIDATION_ARITHMETIC: {phase}")]
    ValidationArithmetic { phase: &'static str },
    #[error("SPECTRUM_EIGENPAIR_RESIDUAL: {observed} exceeds {limit}")]
    EigenpairResidual { observed: f64, limit: f64 },
    #[error("SPECTRUM_ORTHONORMALITY: {observed} exceeds {limit}")]
    Orthonormality { observed: f64, limit: f64 },
    #[error("SPECTRUM_UNREPRESENTABLE_EIGENVALUE: index {index}")]
    UnrepresentableEigenvalue { index: usize },
    #[error("SPECTRUM_UNREPRESENTABLE_SPACING: index {index}")]
    UnrepresentableSpacing { index: usize },
}

/// Explicit bounded numerical policy, not a proof-error or acceptance policy.
/// The dimension ceiling bounds this dense implementation, not API input bytes.
/// A zero iteration budget is rejected because the underlying library means
/// unlimited iteration by zero.
///
/// ~~~compile_fail
/// use linear_algebra::hermitian_eigen::SpectrumPolicy;
/// let forged: SpectrumPolicy = serde_json::from_str("{}").unwrap();
/// ~~~
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct SpectrumPolicy {
    max_dimension: usize,
    max_iterations: usize,
    convergence_tolerance: f64,
    validation_tolerance: f64,
}

impl SpectrumPolicy {
    pub fn new(
        max_dimension: usize,
        max_iterations: usize,
        convergence_tolerance: f64,
        validation_tolerance: f64,
    ) -> Result<Self, SpectrumError> {
        if !(1..=MAX_SPECTRUM_DIMENSION).contains(&max_dimension) {
            return Err(SpectrumError::InvalidPolicy {
                field: "max_dimension",
            });
        }
        if !(1..=MAX_SPECTRUM_ITERATIONS).contains(&max_iterations) {
            return Err(SpectrumError::InvalidPolicy {
                field: "max_iterations",
            });
        }
        for (field, value) in [
            ("convergence_tolerance", convergence_tolerance),
            ("validation_tolerance", validation_tolerance),
        ] {
            if !value.is_finite() || !(f64::EPSILON..=1e-6).contains(&value) {
                return Err(SpectrumError::InvalidPolicy { field });
            }
        }
        Ok(Self {
            max_dimension,
            max_iterations,
            convergence_tolerance,
            validation_tolerance,
        })
    }

    pub fn max_dimension(&self) -> usize {
        self.max_dimension
    }
    pub fn max_iterations(&self) -> usize {
        self.max_iterations
    }
    pub fn convergence_tolerance(&self) -> f64 {
        self.convergence_tolerance
    }
    pub fn validation_tolerance(&self) -> f64 {
        self.validation_tolerance
    }
}

/// Retained finite numerical presentation with checked eigenpairs.
/// Eigenvectors are columns paired with the sorted eigenvalues. A degenerate
/// basis has no canonical orientation or cross-toolchain byte-stability claim.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct HermitianSpectrum {
    policy: SpectrumPolicy,
    matrix: DMatrix<Complex64>,
    normalization_scale: f64,
    eigenvalues: Vec<f64>,
    eigenvectors: DMatrix<Complex64>,
    normalized_matrix_infinity_norm: f64,
    maximum_normalized_residual: f64,
    maximum_orthonormality_defect: f64,
}

impl HermitianSpectrum {
    pub fn policy(&self) -> SpectrumPolicy {
        self.policy
    }
    pub fn matrix(&self) -> &DMatrix<Complex64> {
        &self.matrix
    }
    pub fn normalization_scale(&self) -> f64 {
        self.normalization_scale
    }
    pub fn eigenvalues(&self) -> &[f64] {
        &self.eigenvalues
    }
    pub fn eigenvectors(&self) -> &DMatrix<Complex64> {
        &self.eigenvectors
    }
    pub fn normalized_matrix_infinity_norm(&self) -> f64 {
        self.normalized_matrix_infinity_norm
    }
    pub fn maximum_normalized_residual(&self) -> f64 {
        self.maximum_normalized_residual
    }
    pub fn maximum_orthonormality_defect(&self) -> f64 {
        self.maximum_orthonormality_defect
    }
}

fn finite(value: Complex64) -> bool {
    value.re.is_finite() && value.im.is_finite()
}

/// Shared numerical kernel for the owned finite Hermitian diagnostics.
/// This does not validate density positivity, trace one or a physical state.
pub fn hermitian_eigen_checked(
    matrix: &DMatrix<Complex64>,
    policy: SpectrumPolicy,
) -> Result<HermitianSpectrum, SpectrumError> {
    let rows = validate_hermitian_dimension(matrix.shape(), policy.max_dimension)?;
    let (scale, normalized) = scale_and_normalize_hermitian(matrix, rows)?;
    let decomposition = SymmetricEigen::try_new(
        normalized.clone(),
        policy.convergence_tolerance,
        policy.max_iterations,
    )
    .ok_or(SpectrumError::IterationLimit {
        limit: policy.max_iterations,
    })?;
    let checks = validate_eigenpairs(
        &normalized,
        &decomposition.eigenvalues,
        &decomposition.eigenvectors,
        policy,
    )?;
    let (eigenvalues, eigenvectors) = sort_and_rescale_eigenpairs(&decomposition, rows, scale)?;
    Ok(HermitianSpectrum {
        policy,
        matrix: matrix.clone(),
        normalization_scale: scale,
        eigenvalues,
        eigenvectors: DMatrix::from_columns(&eigenvectors),
        normalized_matrix_infinity_norm: checks.0,
        maximum_normalized_residual: checks.1,
        maximum_orthonormality_defect: checks.2,
    })
}

fn validate_hermitian_dimension(
    shape: (usize, usize),
    max_dimension: usize,
) -> Result<usize, SpectrumError> {
    let (rows, columns) = shape;
    if rows != columns {
        return Err(SpectrumError::NotSquare { rows, columns });
    }
    if rows == 0 {
        return Err(SpectrumError::EmptyMatrix);
    }
    if rows > max_dimension {
        return Err(SpectrumError::DimensionLimit {
            actual: rows,
            limit: max_dimension,
        });
    }
    Ok(rows)
}

fn scale_and_normalize_hermitian(
    matrix: &DMatrix<Complex64>,
    rows: usize,
) -> Result<(f64, DMatrix<Complex64>), SpectrumError> {
    // Check every supplied entry before Hermitian comparison or decomposition.
    // nalgebra reads only the lower triangle; accepting a bad upper one would
    // otherwise silently change the requested operator.
    let scale = max_component_abs_checked(matrix, rows)?;
    check_lower_triangle_hermitian(matrix, rows)?;
    // Componentwise real scaling avoids squared complex-divisor underflow.
    let scale = if scale == 0.0 { 1.0 } else { scale };
    let normalized = matrix.map(|z| Complex64::new(z.re / scale, z.im / scale));
    check_no_scaling_underflow(matrix, &normalized, rows)?;
    Ok((scale, normalized))
}

fn max_component_abs_checked(
    matrix: &DMatrix<Complex64>,
    rows: usize,
) -> Result<f64, SpectrumError> {
    let mut scale = 0.0_f64;
    for row in 0..rows {
        for column in 0..rows {
            let value = matrix[(row, column)];
            if !finite(value) {
                return Err(SpectrumError::NonFiniteInput { row, column });
            }
            scale = scale.max(value.re.abs()).max(value.im.abs());
        }
    }
    Ok(scale)
}

fn check_lower_triangle_hermitian(
    matrix: &DMatrix<Complex64>,
    rows: usize,
) -> Result<(), SpectrumError> {
    for row in 0..rows {
        for column in 0..=row {
            if matrix[(row, column)] != matrix[(column, row)].conj() {
                return Err(SpectrumError::NotHermitian { row, column });
            }
        }
    }
    Ok(())
}

fn check_no_scaling_underflow(
    matrix: &DMatrix<Complex64>,
    normalized: &DMatrix<Complex64>,
    rows: usize,
) -> Result<(), SpectrumError> {
    for row in 0..rows {
        for column in 0..rows {
            let original = matrix[(row, column)];
            let scaled = normalized[(row, column)];
            if (original.re != 0.0 && scaled.re == 0.0) || (original.im != 0.0 && scaled.im == 0.0)
            {
                return Err(SpectrumError::ScalingUnderflow { row, column });
            }
        }
    }
    Ok(())
}

fn sort_and_rescale_eigenpairs(
    decomposition: &SymmetricEigen<Complex64, nalgebra::Dyn>,
    rows: usize,
    scale: f64,
) -> Result<(Vec<f64>, Vec<nalgebra::DVector<Complex64>>), SpectrumError> {
    let mut order: Vec<usize> = (0..rows).collect();
    order.sort_by(|a, b| decomposition.eigenvalues[*a].total_cmp(&decomposition.eigenvalues[*b]));
    let mut eigenvalues = Vec::with_capacity(rows);
    let mut eigenvectors = Vec::with_capacity(rows);
    for (index, original) in order.into_iter().enumerate() {
        let value = decomposition.eigenvalues[original] * scale;
        if !value.is_finite() || (decomposition.eigenvalues[original] != 0.0 && value == 0.0) {
            return Err(SpectrumError::UnrepresentableEigenvalue { index });
        }
        eigenvalues.push(value);
        eigenvectors.push(decomposition.eigenvectors.column(original).into_owned());
    }
    Ok((eigenvalues, eigenvectors))
}

pub fn validate_eigenpairs(
    matrix: &DMatrix<Complex64>,
    values: &DVector<f64>,
    vectors: &DMatrix<Complex64>,
    policy: SpectrumPolicy,
) -> Result<(f64, f64, f64), SpectrumError> {
    let dimension = validate_eigenpair_inputs(matrix, values, vectors, policy)?;
    let matrix_norm = compute_infinity_norm(matrix, dimension)?;
    let (residual, orthonormality) =
        compute_residual_and_orthonormality(matrix, values, vectors, dimension)?;
    let limit = policy.validation_tolerance * matrix_norm.max(1.0);
    if residual > limit {
        return Err(SpectrumError::EigenpairResidual {
            observed: residual,
            limit,
        });
    }
    if orthonormality > policy.validation_tolerance {
        return Err(SpectrumError::Orthonormality {
            observed: orthonormality,
            limit: policy.validation_tolerance,
        });
    }
    Ok((matrix_norm, residual, orthonormality))
}

fn validate_eigenpair_inputs(
    matrix: &DMatrix<Complex64>,
    values: &DVector<f64>,
    vectors: &DMatrix<Complex64>,
    policy: SpectrumPolicy,
) -> Result<usize, SpectrumError> {
    let dimension = matrix.nrows();
    if dimension == 0 {
        return Err(SpectrumError::EmptyMatrix);
    }
    if dimension > policy.max_dimension() {
        return Err(SpectrumError::DimensionLimit {
            actual: dimension,
            limit: policy.max_dimension(),
        });
    }
    if matrix.ncols() != dimension
        || values.len() != dimension
        || vectors.shape() != (dimension, dimension)
    {
        return Err(SpectrumError::EigenpairShape);
    }
    check_full_hermitian_and_finite(matrix, dimension)?;
    if values.iter().any(|v| !v.is_finite()) || vectors.iter().any(|v| !finite(*v)) {
        return Err(SpectrumError::NonFiniteEigenpair);
    }
    Ok(dimension)
}

fn check_full_hermitian_and_finite(
    matrix: &DMatrix<Complex64>,
    dimension: usize,
) -> Result<(), SpectrumError> {
    for r in 0..dimension {
        for c in 0..dimension {
            if !finite(matrix[(r, c)]) {
                return Err(SpectrumError::NonFiniteInput { row: r, column: c });
            }
            if matrix[(r, c)] != matrix[(c, r)].conj() {
                return Err(SpectrumError::NotHermitian { row: r, column: c });
            }
        }
    }
    Ok(())
}

fn compute_infinity_norm(
    matrix: &DMatrix<Complex64>,
    dimension: usize,
) -> Result<f64, SpectrumError> {
    let matrix_norm = (0..dimension)
        .map(|row| {
            (0..dimension)
                .map(|column| matrix[(row, column)].norm())
                .sum::<f64>()
        })
        .fold(0.0_f64, f64::max);
    if !matrix_norm.is_finite() {
        return Err(SpectrumError::ValidationArithmetic {
            phase: "matrix norm",
        });
    }
    Ok(matrix_norm)
}

fn compute_residual_and_orthonormality(
    matrix: &DMatrix<Complex64>,
    values: &DVector<f64>,
    vectors: &DMatrix<Complex64>,
    dimension: usize,
) -> Result<(f64, f64), SpectrumError> {
    let mut residual = 0.0_f64;
    let mut orthonormality = 0.0_f64;
    for column in 0..dimension {
        residual = residual.max(column_residual_defect(
            matrix, values, vectors, dimension, column,
        )?);
        orthonormality = orthonormality.max(column_orthonormality_defect(
            vectors, dimension, column,
        )?);
    }
    Ok((residual, orthonormality))
}

fn column_residual_defect(
    matrix: &DMatrix<Complex64>,
    values: &DVector<f64>,
    vectors: &DMatrix<Complex64>,
    dimension: usize,
    column: usize,
) -> Result<f64, SpectrumError> {
    let mut max_defect = 0.0_f64;
    for row in 0..dimension {
        let product: Complex64 = (0..dimension)
            .map(|k| matrix[(row, k)] * vectors[(k, column)])
            .sum();
        let defect = (product - vectors[(row, column)] * values[column]).norm();
        if !defect.is_finite() {
            return Err(SpectrumError::ValidationArithmetic { phase: "residual" });
        }
        max_defect = max_defect.max(defect);
    }
    Ok(max_defect)
}

fn column_orthonormality_defect(
    vectors: &DMatrix<Complex64>,
    dimension: usize,
    column: usize,
) -> Result<f64, SpectrumError> {
    let mut max_defect = 0.0_f64;
    for other in 0..=column {
        let inner: Complex64 = (0..dimension)
            .map(|row| vectors[(row, other)].conj() * vectors[(row, column)])
            .sum();
        let expected = if column == other { 1.0 } else { 0.0 };
        let defect = (inner - Complex64::new(expected, 0.0)).norm();
        if !defect.is_finite() {
            return Err(SpectrumError::ValidationArithmetic {
                phase: "orthonormality",
            });
        }
        max_defect = max_defect.max(defect);
    }
    Ok(max_defect)
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn policy() -> SpectrumPolicy {
        SpectrumPolicy::new(16, 10_000, 1e-14, 1e-12).unwrap()
    }

    fn c(re: f64, im: f64) -> Complex64 {
        Complex64::new(re, im)
    }

    fn diagonal(values: &[f64]) -> DMatrix<Complex64> {
        DMatrix::from_diagonal(&DVector::from_iterator(
            values.len(),
            values.iter().map(|x| c(*x, 0.0)),
        ))
    }

    fn close(actual: f64, expected: f64) {
        assert!(
            actual.is_finite() && (actual - expected).abs() <= 1e-10 * expected.abs().max(1.0),
            "{actual:?} != {expected:?}"
        );
    }

    #[test]
    fn sorted_eigenvectors_remain_bound_to_their_original_matrix() {
        let matrix =
            DMatrix::from_row_slice(2, 2, &[c(2.0, 0.0), c(1.0, 1.0), c(1.0, -1.0), c(3.0, 0.0)]);
        let original = matrix.clone();
        let result = hermitian_eigen_checked(&matrix, policy()).unwrap();
        let spectrum = &result;
        assert_eq!(spectrum.matrix(), &original);
        assert_eq!(spectrum.policy(), policy());
        assert_eq!(spectrum.normalization_scale(), 3.0);
        for column in 0..2 {
            let vector = spectrum.eigenvectors().column(column);
            let residual = &matrix * vector - vector * c(spectrum.eigenvalues()[column], 0.0);
            assert!(residual.iter().all(|z| z.norm() < 1e-10));
        }
        assert!(
            spectrum.maximum_normalized_residual()
                <= policy().validation_tolerance()
                    * spectrum.normalized_matrix_infinity_norm().max(1.0)
        );
        assert!(spectrum.maximum_orthonormality_defect() <= policy().validation_tolerance());
    }

    #[test]
    fn invalid_policy_cannot_request_unbounded_work_or_vacuous_tolerances() {
        for dimension in [0, MAX_SPECTRUM_DIMENSION + 1, usize::MAX] {
            assert_eq!(
                SpectrumPolicy::new(dimension, 10, 1e-14, 1e-12),
                Err(SpectrumError::InvalidPolicy {
                    field: "max_dimension"
                })
            );
        }
        for iterations in [0, MAX_SPECTRUM_ITERATIONS + 1, usize::MAX] {
            assert_eq!(
                SpectrumPolicy::new(2, iterations, 1e-14, 1e-12),
                Err(SpectrumError::InvalidPolicy {
                    field: "max_iterations"
                })
            );
        }
        for tolerance in [
            0.0,
            -1.0,
            f64::NAN,
            f64::INFINITY,
            f64::NEG_INFINITY,
            1.0,
            f64::from_bits(1),
        ] {
            assert_eq!(
                SpectrumPolicy::new(2, 10, tolerance, 1e-12),
                Err(SpectrumError::InvalidPolicy {
                    field: "convergence_tolerance"
                })
            );
            assert_eq!(
                SpectrumPolicy::new(2, 10, 1e-14, tolerance),
                Err(SpectrumError::InvalidPolicy {
                    field: "validation_tolerance"
                })
            );
        }
        let selected = SpectrumPolicy::new(2, 10, f64::EPSILON, 1e-6).unwrap();
        assert_eq!(selected.max_dimension(), 2);
        assert_eq!(selected.max_iterations(), 10);
        assert_eq!(selected.convergence_tolerance(), f64::EPSILON);
        assert_eq!(selected.validation_tolerance(), 1e-6);
    }

    #[test]
    fn shape_empty_and_dimension_refusals_precede_decomposition() {
        let functional = |matrix: &DMatrix<Complex64>| {
            hermitian_eigen_checked(matrix, SpectrumPolicy::new(1, 10, 1e-14, 1e-12).unwrap())
        };
        assert_eq!(
            functional(&DMatrix::zeros(2, 3)),
            Err(SpectrumError::NotSquare {
                rows: 2,
                columns: 3
            })
        );
        assert_eq!(
            functional(&DMatrix::zeros(0, 0)),
            Err(SpectrumError::EmptyMatrix)
        );
        assert_eq!(
            functional(&DMatrix::zeros(2, 2)),
            Err(SpectrumError::DimensionLimit {
                actual: 2,
                limit: 1
            })
        );
    }

    #[test]
    fn every_triangle_and_imaginary_diagonal_is_checked_without_projection() {
        let functional = |matrix: &DMatrix<Complex64>| hermitian_eigen_checked(matrix, policy());
        let bad =
            DMatrix::from_row_slice(2, 2, &[c(0.0, 0.0), c(9.0, 0.0), c(0.0, 0.0), c(0.0, 0.0)]);
        assert_eq!(
            functional(&bad),
            Err(SpectrumError::NotHermitian { row: 1, column: 0 })
        );
        assert_eq!(
            functional(&DMatrix::from_element(1, 1, c(0.0, 1.0))),
            Err(SpectrumError::NotHermitian { row: 0, column: 0 })
        );
        for (row, column) in [(0, 0), (0, 1), (1, 0), (1, 1)] {
            for value in [
                c(f64::NAN, 0.0),
                c(0.0, f64::INFINITY),
                c(f64::NEG_INFINITY, 0.0),
            ] {
                let mut malformed = DMatrix::zeros(2, 2);
                malformed[(row, column)] = value;
                assert_eq!(
                    functional(&malformed),
                    Err(SpectrumError::NonFiniteInput { row, column })
                );
            }
        }
    }

    #[test]
    fn wrong_eigenvalues_fail_independent_residual_validation() {
        let matrix = diagonal(&[1.0, 2.0]);
        assert!(matches!(
            validate_eigenpairs(
                &matrix,
                &DVector::from_vec(vec![1.0, 3.0]),
                &DMatrix::identity(2, 2),
                policy()
            ),
            Err(SpectrumError::EigenpairResidual { .. })
        ));
    }

    #[test]
    fn scaling_must_not_erase_a_nonzero_input_or_unrepresentable_level() {
        let functional = |matrix: &DMatrix<Complex64>| hermitian_eigen_checked(matrix, policy());
        let tiny = f64::from_bits(1);
        assert_eq!(
            functional(&diagonal(&[f64::MAX, tiny])),
            Err(SpectrumError::ScalingUnderflow { row: 1, column: 1 })
        );
        let matrix = DMatrix::from_row_slice(
            2,
            2,
            &[c(tiny, 0.0), c(tiny, 0.0), c(tiny, 0.0), c(2.0 * tiny, 0.0)],
        );
        // The lower eigenvalue is (3-sqrt(5))/2 times tiny, below half an ulp.
        assert_eq!(
            functional(&matrix),
            Err(SpectrumError::UnrepresentableEigenvalue { index: 0 })
        );
    }

    #[test]
    fn zero_or_repeated_eigenvectors_fail_even_when_the_residual_is_zero() {
        let matrix = DMatrix::zeros(2, 2);
        let values = DVector::zeros(2);
        for vectors in [
            DMatrix::zeros(2, 2),
            DMatrix::from_row_slice(2, 2, &[c(1.0, 0.0), c(1.0, 0.0), c(0.0, 0.0), c(0.0, 0.0)]),
        ] {
            assert!(matches!(
                validate_eigenpairs(&matrix, &values, &vectors, policy()),
                Err(SpectrumError::Orthonormality { .. })
            ));
        }
    }

    #[test]
    fn malformed_and_nonfinite_decompositions_cannot_become_checked_evidence() {
        let matrix = diagonal(&[1.0, 2.0]);
        assert_eq!(
            validate_eigenpairs(
                &matrix,
                &DVector::zeros(1),
                &DMatrix::identity(2, 2),
                policy()
            ),
            Err(SpectrumError::EigenpairShape)
        );
        assert_eq!(
            validate_eigenpairs(
                &matrix,
                &DVector::zeros(2),
                &DMatrix::identity(2, 1),
                policy()
            ),
            Err(SpectrumError::EigenpairShape)
        );
        assert_eq!(
            validate_eigenpairs(
                &matrix,
                &DVector::from_vec(vec![1.0, f64::NAN]),
                &DMatrix::identity(2, 2),
                policy()
            ),
            Err(SpectrumError::NonFiniteEigenpair)
        );
        let mut vectors = DMatrix::identity(2, 2);
        vectors[(0, 1)] = c(f64::INFINITY, 0.0);
        assert_eq!(
            validate_eigenpairs(
                &matrix,
                &DVector::from_vec(vec![1.0, 2.0]),
                &vectors,
                policy()
            ),
            Err(SpectrumError::NonFiniteEigenpair)
        );
    }

    #[test]
    fn exhausted_solver_budget_is_a_typed_refusal_not_partial_success() {
        let matrix = DMatrix::from_row_slice(
            4,
            4,
            &[
                c(2.0, 0.0),
                c(1.0, 0.0),
                c(0.0, 0.0),
                c(0.0, 0.0),
                c(1.0, 0.0),
                c(3.0, 0.0),
                c(1.0, 0.0),
                c(0.0, 0.0),
                c(0.0, 0.0),
                c(1.0, 0.0),
                c(4.0, 0.0),
                c(1.0, 0.0),
                c(0.0, 0.0),
                c(0.0, 0.0),
                c(1.0, 0.0),
                c(5.0, 0.0),
            ],
        );
        let limited = |matrix: &DMatrix<Complex64>| {
            hermitian_eigen_checked(matrix, SpectrumPolicy::new(4, 1, 1e-14, 1e-12).unwrap())
        };
        assert_eq!(
            limited(&matrix),
            Err(SpectrumError::IterationLimit { limit: 1 })
        );
        let full = hermitian_eigen_checked(&matrix, policy()).unwrap();
        close(full.eigenvalues().iter().sum(), 14.0);
        assert_eq!(full.eigenvalues().len(), 4);
    }

    #[test]
    fn validation_arithmetic_refusals_are_distinct_from_nonfinite_solver_inputs() {
        let matrix = DMatrix::zeros(2, 2);
        let vectors = DMatrix::from_element(2, 2, c(f64::MAX, 0.0));
        assert_eq!(
            validate_eigenpairs(
                &matrix,
                &DVector::from_element(2, f64::MAX),
                &vectors,
                policy()
            ),
            Err(SpectrumError::ValidationArithmetic { phase: "residual" })
        );
        assert_eq!(
            validate_eigenpairs(&matrix, &DVector::zeros(2), &vectors, policy()),
            Err(SpectrumError::ValidationArithmetic {
                phase: "orthonormality"
            })
        );
    }
}
