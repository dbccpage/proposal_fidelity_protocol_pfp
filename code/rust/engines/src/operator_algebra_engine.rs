
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_1b9d10ef<T> {
    fn checked_invariant_1b9d10ef(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_1b9d10ef<T> for Option<T> {
    #[inline]
    fn checked_invariant_1b9d10ef(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_1b9d10ef<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_1b9d10ef(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::quantum::density_matrix::{CMatrix, C64};
use crate::quantum::density_matrix::{CVector, ComplexDensityMatrix};
use constants::numeric_constants::EPSILON_QUANTUM_EIGEN;
use nalgebra::{DMatrix, DVector, SymmetricEigen};
use std::fmt;

const DEFAULT_TOLERANCE: f64 = 1e-9;

#[derive(Debug, Clone, PartialEq)]
pub enum OperatorAlgebraError {
    ZeroDimension,
    EmptyGenerators,
    NonSquareMatrix { rows: usize, cols: usize },
    DimensionMismatch { expected: usize, got: usize },
    NonUnitalState { trace: f64 },
    NonPositiveState { min_eigenvalue: f64 },
    NonFaithfulState { min_eigenvalue: f64 },
    NonDiagonalState { max_off_diagonal: f64 },
    InvalidObservable(String),
}

impl fmt::Display for OperatorAlgebraError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ZeroDimension => write!(f, "operator algebra dimension must be positive"),
            Self::EmptyGenerators => write!(f, "at least one generator is required"),
            Self::NonSquareMatrix { rows, cols } => {
                write!(f, "matrix must be square, got {rows}x{cols}")
            }
            Self::DimensionMismatch { expected, got } => {
                write!(f, "dimension mismatch: expected {expected}, got {got}")
            }
            Self::NonUnitalState { trace } => write!(f, "state must satisfy omega(I)=1, got {trace}"),
            Self::NonPositiveState { min_eigenvalue } => {
                write!(f, "state density is not positive, min eigenvalue {min_eigenvalue}")
            }
            Self::NonFaithfulState { min_eigenvalue } => write!(
                f,
                "modular flow requires a faithful state, min eigenvalue {min_eigenvalue}"
            ),
            Self::NonDiagonalState { max_off_diagonal } => write!(
                f,
                "finite modular flow helper expects diagonal density, max off-diagonal {max_off_diagonal}"
            ),
            Self::InvalidObservable(msg) => write!(f, "invalid observable: {msg}"),
        }
    }
}

impl std::error::Error for OperatorAlgebraError {}

pub trait CStarAlgebra {
    fn dim(&self) -> usize;
    fn unit(&self) -> CMatrix;
    fn star(&self, a: &CMatrix) -> Result<CMatrix, OperatorAlgebraError>;
    fn multiply(&self, a: &CMatrix, b: &CMatrix) -> Result<CMatrix, OperatorAlgebraError>;
    fn norm(&self, a: &CMatrix) -> Result<f64, OperatorAlgebraError>;

    fn cstar_identity_defect(&self, a: &CMatrix) -> Result<f64, OperatorAlgebraError> {
        let a_star_a = self.multiply(&self.star(a)?, a)?;
        let lhs = self.norm(&a_star_a)?;
        let rhs = self.norm(a)?.powi(2);
        Ok((lhs - rhs).abs())
    }
}

#[derive(Clone, Debug)]
pub struct MatrixCStarAlgebra {
    dim: usize,
    tolerance: f64,
}

impl MatrixCStarAlgebra {
    pub fn new(dim: usize) -> Result<Self, OperatorAlgebraError> {
        Self::with_tolerance(dim, DEFAULT_TOLERANCE)
    }

    pub fn with_tolerance(dim: usize, tolerance: f64) -> Result<Self, OperatorAlgebraError> {
        if dim == 0 {
            return Err(OperatorAlgebraError::ZeroDimension);
        }
        Ok(Self {
            dim,
            tolerance: tolerance.max(EPSILON_QUANTUM_EIGEN),
        })
    }

    pub fn tolerance(&self) -> f64 {
        self.tolerance
    }

    fn ensure_element(&self, a: &CMatrix) -> Result<(), OperatorAlgebraError> {
        ensure_square(a)?;
        if a.nrows() != self.dim() {
            return Err(OperatorAlgebraError::DimensionMismatch {
                expected: self.dim(),
                got: a.nrows(),
            });
        }
        Ok(())
    }
}

impl CStarAlgebra for MatrixCStarAlgebra {
    fn dim(&self) -> usize {
        self.dim
    }

    fn unit(&self) -> CMatrix {
        identity(self.dim())
    }

    fn star(&self, a: &CMatrix) -> Result<CMatrix, OperatorAlgebraError> {
        self.ensure_element(a)?;
        Ok(a.adjoint())
    }

    fn multiply(&self, a: &CMatrix, b: &CMatrix) -> Result<CMatrix, OperatorAlgebraError> {
        self.ensure_element(a)?;
        self.ensure_element(b)?;
        Ok(a * b)
    }

    fn norm(&self, a: &CMatrix) -> Result<f64, OperatorAlgebraError> {
        self.ensure_element(a)?;
        Ok(operator_norm(a))
    }
}

#[derive(Clone, Debug)]
pub struct AlgebraicState {
    density: ComplexDensityMatrix,
    tolerance: f64,
}

impl AlgebraicState {
    pub fn from_density(density: ComplexDensityMatrix) -> Result<Self, OperatorAlgebraError> {
        Self::with_tolerance(density, DEFAULT_TOLERANCE)
    }

    pub fn with_tolerance(
        density: ComplexDensityMatrix,
        tolerance: f64,
    ) -> Result<Self, OperatorAlgebraError> {
        ensure_square(density.rho())?;
        if !tolerance.is_finite() || tolerance < 0.0 {
            return Err(OperatorAlgebraError::InvalidObservable(
                "tolerance is not a finite nonnegative diagnostic".into(),
            ));
        }

        let trace = density.rho().trace().re;
        if (trace - 1.0).abs() > 0.0 {
            return Err(OperatorAlgebraError::NonUnitalState { trace });
        }

        let min_eigenvalue = min_hermitian_eigenvalue(density.rho());
        if min_eigenvalue < 0.0 {
            return Err(OperatorAlgebraError::NonPositiveState { min_eigenvalue });
        }

        Ok(Self { density, tolerance })
    }

    pub fn vector_state(psi: &CVector) -> Result<Self, OperatorAlgebraError> {
        let norm = psi.iter().map(|z| z.norm_sqr()).sum::<f64>().sqrt();
        if norm <= EPSILON_QUANTUM_EIGEN || !norm.is_finite() {
            return Err(OperatorAlgebraError::InvalidObservable(
                "cyclic vector has zero or non-finite norm".to_string(),
            ));
        }
        let normalized = psi / nalgebra::Complex::new(norm, 0.0);
        let dm = ComplexDensityMatrix::from_cvector(&normalized).checked_invariant_1b9d10ef("checked invariant");
        Self::with_tolerance(dm, EPSILON_QUANTUM_EIGEN)
    }

    pub fn density(&self) -> &ComplexDensityMatrix {
        &self.density
    }

    pub fn dim(&self) -> usize {
        self.density.dim()
    }

    pub fn expectation(&self, observable: &CMatrix) -> Result<C64, OperatorAlgebraError> {
        ensure_square(observable)?;
        if observable.nrows() != self.dim() {
            return Err(OperatorAlgebraError::DimensionMismatch {
                expected: self.dim(),
                got: observable.nrows(),
            });
        }
        Ok((self.density.rho() * observable).trace())
    }

    pub fn is_positive_on_square(&self, a: &CMatrix) -> Result<bool, OperatorAlgebraError> {
        let value = self.expectation(&(a.adjoint() * a))?;
        Ok(value.re >= -self.tolerance && value.im.abs() <= self.tolerance)
    }
}

#[derive(Clone, Debug)]
pub struct GnsConstruction {
    state: AlgebraicState,
    matrix_units: Vec<CMatrix>,
    gram: CMatrix,
    quotient_dimension: usize,
}

impl GnsConstruction {
    pub fn from_state(state: AlgebraicState) -> Result<Self, OperatorAlgebraError> {
        let dim = state.dim();
        let matrix_units = matrix_unit_basis(dim);
        let mut gram = CMatrix::zeros(matrix_units.len(), matrix_units.len());
        for (i, a) in matrix_units.iter().enumerate() {
            for (j, b) in matrix_units.iter().enumerate() {
                gram[(i, j)] = state.expectation(&(a.adjoint() * b))?;
            }
        }
        let quotient_dimension = hermitian_complex_rank(&gram, state.tolerance);
        Ok(Self {
            state,
            matrix_units,
            gram,
            quotient_dimension,
        })
    }

    pub fn gram(&self) -> &CMatrix {
        &self.gram
    }

    pub fn quotient_dimension(&self) -> usize {
        self.quotient_dimension
    }

    pub fn cyclic_expectation(&self, observable: &CMatrix) -> Result<C64, OperatorAlgebraError> {
        self.state.expectation(observable)
    }

    pub fn inner_product(&self, a: &CMatrix, b: &CMatrix) -> Result<C64, OperatorAlgebraError> {
        self.state.expectation(&(a.adjoint() * b))
    }

    /// Left multiplication representation on the matrix-unit spanning set.
    ///
    /// This is the pre-quotient representation matrix. The GNS quotient is
    /// encoded separately by the Gram kernel/rank.
    pub fn left_action_matrix(&self, a: &CMatrix) -> Result<CMatrix, OperatorAlgebraError> {
        ensure_square(a)?;
        if a.nrows() != self.state.dim() {
            return Err(OperatorAlgebraError::DimensionMismatch {
                expected: self.state.dim(),
                got: a.nrows(),
            });
        }

        let dim = self.state.dim();
        let n2 = dim * dim;
        let mut action = CMatrix::zeros(n2, n2);
        for (col, basis_element) in self.matrix_units.iter().enumerate() {
            let image = a * basis_element;
            for row in 0..dim {
                for col_basis in 0..dim {
                    let row_index = row * dim + col_basis;
                    action[(row_index, col)] = image[(row, col_basis)];
                }
            }
        }
        Ok(action)
    }
}

#[derive(Clone, Debug)]
pub struct FiniteVonNeumannAlgebra {
    dim: usize,
    basis: Vec<CMatrix>,
    tolerance: f64,
}

impl FiniteVonNeumannAlgebra {
    pub fn generated_by(dim: usize, generators: &[CMatrix]) -> Result<Self, OperatorAlgebraError> {
        Self::generated_by_with_tolerance(dim, generators, DEFAULT_TOLERANCE)
    }

    pub fn generated_by_with_tolerance(
        dim: usize,
        generators: &[CMatrix],
        tolerance: f64,
    ) -> Result<Self, OperatorAlgebraError> {
        Self::validate_generators(dim, generators)?;
        let tolerance = tolerance.max(EPSILON_QUANTUM_EIGEN);

        let mut basis = Vec::new();
        add_to_complex_span(&mut basis, identity(dim), tolerance);
        for generator in generators {
            add_to_complex_span(&mut basis, generator.clone(), tolerance);
            add_to_complex_span(&mut basis, generator.adjoint(), tolerance);
        }

        Self::close_under_multiplication(&mut basis, dim * dim, tolerance);

        Ok(Self {
            dim,
            basis,
            tolerance,
        })
    }

    fn validate_generators(dim: usize, generators: &[CMatrix]) -> Result<(), OperatorAlgebraError> {
        if dim == 0 {
            return Err(OperatorAlgebraError::ZeroDimension);
        }
        if generators.is_empty() {
            return Err(OperatorAlgebraError::EmptyGenerators);
        }
        for generator in generators {
            ensure_square(generator)?;
            if generator.nrows() != dim {
                return Err(OperatorAlgebraError::DimensionMismatch {
                    expected: dim,
                    got: generator.nrows(),
                });
            }
        }
        Ok(())
    }

    fn close_under_multiplication(basis: &mut Vec<CMatrix>, max_dim: usize, tolerance: f64) {
        let mut changed = true;
        while changed && complex_span_rank(basis, tolerance) < max_dim {
            changed = false;
            let snapshot = basis.clone();
            for a in &snapshot {
                for b in &snapshot {
                    let product = a * b;
                    if add_to_complex_span(basis, product, tolerance) {
                        changed = true;
                    }
                }
            }
        }
    }

    pub fn dim(&self) -> usize {
        self.dim
    }

    pub fn algebra_dimension(&self) -> usize {
        complex_span_rank(&self.basis, self.tolerance)
    }

    pub fn basis(&self) -> &[CMatrix] {
        &self.basis
    }

    pub fn commutant_basis(&self) -> Vec<CMatrix> {
        commutant_basis(self.dim(), &self.basis, self.tolerance)
    }

    pub fn commutant_dimension(&self) -> usize {
        complex_span_rank(&self.commutant_basis(), self.tolerance)
    }

    pub fn double_commutant_diagnostic(&self) -> DoubleCommutantDiagnostic {
        let commutant = self.commutant_basis();
        let double_commutant = commutant_basis(self.dim(), &commutant, self.tolerance);
        let generated_dimension = self.algebra_dimension();
        let commutant_dimension = complex_span_rank(&commutant, self.tolerance);
        let double_commutant_dimension = complex_span_rank(&double_commutant, self.tolerance);

        DoubleCommutantDiagnostic {
            generated_dimension,
            commutant_dimension,
            double_commutant_dimension,
            is_double_commutant_closed: generated_dimension == double_commutant_dimension,
        }
    }

    pub fn is_factor(&self) -> bool {
        self.commutant_dimension() == 1
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DoubleCommutantDiagnostic {
    pub generated_dimension: usize,
    pub commutant_dimension: usize,
    pub double_commutant_dimension: usize,
    pub is_double_commutant_closed: bool,
}

pub struct ModularFlow;

impl ModularFlow {
    /// Finite-dimensional faithful-state modular automorphism.
    ///
    /// For diagonal rho with probabilities p_i > 0:
    /// sigma_t(A)_ij = exp(i t log(p_i / p_j)) A_ij.
    pub fn diagonal_state_flow(
        state: &AlgebraicState,
        observable: &CMatrix,
        t: f64,
    ) -> Result<CMatrix, OperatorAlgebraError> {
        ensure_square(observable)?;
        let dim = state.dim();
        if observable.nrows() != dim {
            return Err(OperatorAlgebraError::DimensionMismatch {
                expected: dim,
                got: observable.nrows(),
            });
        }

        let density = &state.density().rho();
        let max_off_diagonal = max_off_diagonal_norm(density);
        if max_off_diagonal > state.tolerance {
            return Err(OperatorAlgebraError::NonDiagonalState { max_off_diagonal });
        }

        let min_probability = (0..dim)
            .map(|i| density[(i, i)].re)
            .fold(f64::INFINITY, f64::min);
        if min_probability <= state.tolerance {
            return Err(OperatorAlgebraError::NonFaithfulState {
                min_eigenvalue: min_probability,
            });
        }

        let mut flowed = CMatrix::zeros(dim, dim);
        for i in 0..dim {
            for j in 0..dim {
                let ratio_log = (density[(i, i)].re / density[(j, j)].re).ln();
                let phase = C64::new(0.0, t * ratio_log).exp();
                flowed[(i, j)] = phase * observable[(i, j)];
            }
        }
        Ok(flowed)
    }
}

fn ensure_square(matrix: &CMatrix) -> Result<(), OperatorAlgebraError> {
    if matrix.nrows() != matrix.ncols() {
        return Err(OperatorAlgebraError::NonSquareMatrix {
            rows: matrix.nrows(),
            cols: matrix.ncols(),
        });
    }
    Ok(())
}

fn identity(dim: usize) -> CMatrix {
    let mut id = CMatrix::zeros(dim, dim);
    for i in 0..dim {
        id[(i, i)] = C64::new(1.0, 0.0);
    }
    id
}

fn matrix_unit(dim: usize, row: usize, col: usize) -> CMatrix {
    let mut out = CMatrix::zeros(dim, dim);
    out[(row, col)] = C64::new(1.0, 0.0);
    out
}

fn matrix_unit_basis(dim: usize) -> Vec<CMatrix> {
    (0..dim)
        .flat_map(|row| (0..dim).map(move |col| matrix_unit(dim, row, col)))
        .collect()
}

fn operator_norm(a: &CMatrix) -> f64 {
    let gram = a.adjoint() * a;
    min_max_hermitian_eigenvalue(&gram).1.max(0.0).sqrt()
}

fn min_hermitian_eigenvalue(a: &CMatrix) -> f64 {
    min_max_hermitian_eigenvalue(a).0
}

fn min_max_hermitian_eigenvalue(a: &CMatrix) -> (f64, f64) {
    let block = complex_to_real_block(a);
    let eig = SymmetricEigen::new(block);
    eig.eigenvalues
        .iter()
        .copied()
        .fold((f64::INFINITY, f64::NEG_INFINITY), |(min, max), value| {
            (min.min(value), max.max(value))
        })
}

fn hermitian_complex_rank(a: &CMatrix, tolerance: f64) -> usize {
    let block = complex_to_real_block(a);
    let eig = SymmetricEigen::new(block);
    eig.eigenvalues
        .iter()
        .filter(|&&value| value.abs() > tolerance)
        .count()
        / 2
}

fn complex_to_real_block(a: &CMatrix) -> DMatrix<f64> {
    let n = a.nrows();
    let mut block = DMatrix::zeros(2 * n, 2 * n);
    for i in 0..n {
        for j in 0..n {
            let z = a[(i, j)];
            block[(i, j)] = z.re;
            block[(i, j + n)] = -z.im;
            block[(i + n, j)] = z.im;
            block[(i + n, j + n)] = z.re;
        }
    }
    block
}

fn flatten_complex_matrix(a: &CMatrix) -> DVector<f64> {
    let n2 = a.nrows() * a.ncols();
    let mut out = DVector::zeros(2 * n2);
    for col in 0..a.ncols() {
        for row in 0..a.nrows() {
            let index = row + col * a.nrows();
            let z = a[(row, col)];
            out[index] = z.re;
            out[index + n2] = z.im;
        }
    }
    out
}

fn complex_span_columns(mats: &[CMatrix]) -> DMatrix<f64> {
    if mats.is_empty() {
        return DMatrix::zeros(0, 0);
    }

    let columns: Vec<DVector<f64>> = mats
        .iter()
        .flat_map(|matrix| {
            let v = flatten_complex_matrix(matrix);
            let iv = multiply_flattened_by_i(&v);
            [v, iv]
        })
        .collect();
    DMatrix::from_columns(&columns)
}

fn multiply_flattened_by_i(v: &DVector<f64>) -> DVector<f64> {
    let half = v.len() / 2;
    let mut out = DVector::zeros(v.len());
    for i in 0..half {
        out[i] = -v[i + half];
        out[i + half] = v[i];
    }
    out
}

fn real_rank(matrix: &DMatrix<f64>, tolerance: f64) -> usize {
    if matrix.nrows() == 0 || matrix.ncols() == 0 {
        return 0;
    }
    let svd = matrix.clone().svd(false, false);
    svd.singular_values
        .iter()
        .filter(|&&value| value > tolerance)
        .count()
}

fn complex_span_rank(mats: &[CMatrix], tolerance: f64) -> usize {
    real_rank(&complex_span_columns(mats), tolerance) / 2
}

fn add_to_complex_span(basis: &mut Vec<CMatrix>, candidate: CMatrix, tolerance: f64) -> bool {
    let before = complex_span_rank(basis, tolerance);
    let mut trial = basis.clone();
    trial.push(candidate.clone());
    let after = complex_span_rank(&trial, tolerance);
    if after > before {
        basis.push(candidate);
        true
    } else {
        false
    }
}

fn commutant_basis(dim: usize, generators: &[CMatrix], tolerance: f64) -> Vec<CMatrix> {
    let constraints = commutant_constraint_matrix(dim, generators);
    let nullspace = real_nullspace(&constraints, tolerance);
    nullspace
        .into_iter()
        .map(|v| real_vector_to_complex_matrix(dim, &v))
        .collect()
}

fn commutant_constraint_matrix(dim: usize, generators: &[CMatrix]) -> DMatrix<f64> {
    let n2 = dim * dim;
    let rows = 2 * generators.len() * n2;
    let cols = 2 * n2;
    let mut matrix = DMatrix::zeros(rows, cols);
    let mut row = 0;

    for generator in generators {
        for i in 0..dim {
            for j in 0..dim {
                for k in 0..dim {
                    add_complex_coeff(&mut matrix, row, dim, i, k, generator[(k, j)]);
                    add_complex_coeff(&mut matrix, row, dim, k, j, -generator[(i, k)]);
                }
                row += 2;
            }
        }
    }

    matrix
}

fn add_complex_coeff(
    matrix: &mut DMatrix<f64>,
    row: usize,
    dim: usize,
    var_row: usize,
    var_col: usize,
    coeff: C64,
) {
    let n2 = dim * dim;
    let index = var_row + var_col * dim;
    let re_col = index;
    let im_col = index + n2;

    matrix[(row, re_col)] += coeff.re;
    matrix[(row, im_col)] -= coeff.im;
    matrix[(row + 1, re_col)] += coeff.im;
    matrix[(row + 1, im_col)] += coeff.re;
}

fn real_nullspace(matrix: &DMatrix<f64>, tolerance: f64) -> Vec<DVector<f64>> {
    let ncols = matrix.ncols();
    if ncols == 0 {
        return Vec::new();
    }
    let svd = matrix.clone().svd(false, true);
    let rank = svd
        .singular_values
        .iter()
        .filter(|&&value| value > tolerance)
        .count();

    let Some(v_t) = svd.v_t else {
        return Vec::new();
    };

    (rank..ncols)
        .map(|row| v_t.row(row).transpose().into_owned())
        .collect()
}

fn real_vector_to_complex_matrix(dim: usize, vector: &DVector<f64>) -> CMatrix {
    let n2 = dim * dim;
    let mut out = CMatrix::zeros(dim, dim);
    for col in 0..dim {
        for row in 0..dim {
            let index = row + col * dim;
            out[(row, col)] = C64::new(vector[index], vector[index + n2]);
        }
    }
    out
}

fn max_off_diagonal_norm(matrix: &CMatrix) -> f64 {
    let mut max = 0.0_f64;
    for i in 0..matrix.nrows() {
        for j in 0..matrix.ncols() {
            if i != j {
                max = max.max(matrix[(i, j)].norm());
            }
        }
    }
    max
}

// Origin: engine/crates_rs/engines/src/operator_algebra_engine.rs
// Claim: urn:core:crates_rs:engines:operator-algebra-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn pauli_x() -> CMatrix {
        let mut x = CMatrix::zeros(2, 2);
        x[(0, 1)] = C64::new(1.0, 0.0);
        x[(1, 0)] = C64::new(1.0, 0.0);
        x
    }

    fn pauli_z() -> CMatrix {
        let mut z = CMatrix::zeros(2, 2);
        z[(0, 0)] = C64::new(1.0, 0.0);
        z[(1, 1)] = C64::new(-1.0, 0.0);
        z
    }

    fn ket(entries: &[C64]) -> CVector {
        CVector::from_column_slice(entries)
    }

    #[test]
    fn matrix_cstar_identity_holds_for_pauli_x() {
        let algebra = MatrixCStarAlgebra::new(2).unwrap();
        let defect = algebra.cstar_identity_defect(&pauli_x()).unwrap();

        assert!(defect < 1e-10, "C*-identity defect {defect}");
    }

    #[test]
    fn algebraic_state_expectation_matches_born_rule() {
        let psi = ket(&[C64::new(1.0, 0.0), C64::new(0.0, 0.0)]);
        let state = AlgebraicState::vector_state(&psi).unwrap();
        let expectation = state.expectation(&pauli_z()).unwrap();

        assert!((expectation - C64::new(1.0, 0.0)).norm() < 1e-10);
        assert!(state.is_positive_on_square(&pauli_x()).unwrap());
    }

    #[test]
    fn gns_pure_state_on_m2_has_two_dimensional_quotient() {
        let psi = ket(&[C64::new(1.0, 0.0), C64::new(0.0, 0.0)]);
        let state = AlgebraicState::vector_state(&psi).unwrap();
        let gns = GnsConstruction::from_state(state).unwrap();

        assert_eq!(gns.quotient_dimension(), 2);
        assert_eq!(gns.gram().nrows(), 4);
    }

    #[test]
    fn full_m2_double_commutant_is_closed_factor() {
        let algebra = FiniteVonNeumannAlgebra::generated_by(2, &[pauli_x(), pauli_z()]).unwrap();
        let diagnostic = algebra.double_commutant_diagnostic();

        assert_eq!(diagnostic.generated_dimension, 4);
        assert_eq!(diagnostic.commutant_dimension, 1);
        assert_eq!(diagnostic.double_commutant_dimension, 4);
        assert!(diagnostic.is_double_commutant_closed);
        assert!(algebra.is_factor());
    }

    #[test]
    fn diagonal_algebra_is_abelian_and_not_factor() {
        let algebra = FiniteVonNeumannAlgebra::generated_by(2, &[pauli_z()]).unwrap();
        let diagnostic = algebra.double_commutant_diagnostic();

        assert_eq!(diagnostic.generated_dimension, 2);
        assert_eq!(diagnostic.commutant_dimension, 2);
        assert_eq!(diagnostic.double_commutant_dimension, 2);
        assert!(diagnostic.is_double_commutant_closed);
        assert!(!algebra.is_factor());
    }

    #[test]
    fn modular_flow_for_diagonal_faithful_state_rotates_off_diagonal_phase() {
        let mut rho = CMatrix::zeros(2, 2);
        rho[(0, 0)] = C64::new(0.25, 0.0);
        rho[(1, 1)] = C64::new(0.75, 0.0);
        let state = AlgebraicState::from_density(
            ComplexDensityMatrix::from_validated(
                rho.nrows(),
                rho.as_slice().to_vec(),
                &crate::quantum::density_config::DensityMatrixConfig::default(),
            )
            .unwrap(),
        )
        .unwrap();
        let observable = matrix_unit(2, 0, 1);

        let flowed = ModularFlow::diagonal_state_flow(&state, &observable, 0.7).unwrap();
        let expected_phase = C64::new(0.0, 0.7 * (1.0_f64 / 3.0).ln()).exp();

        assert!((flowed[(0, 1)] - expected_phase).norm() < 1e-10);
        assert!(flowed[(1, 0)].norm() < 1e-10);
    }
}
