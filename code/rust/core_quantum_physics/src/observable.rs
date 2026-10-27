//! Observables: Hermitian operators `A = A*` with expectation values
//! `<psi|A|psi>` and `Tr(A rho)`, as an exact operator over `Q(i)` and as an `f64`
//! diagnostic.
//!
//! **[`ExactObservable`]** is a Hermitian `n x n` matrix over `Q(i)`, accepted only by
//! exact Hermiticity. Every scalar it produces is an exact rational:
//!
//! - the expectation value in a ray or a density operator, and the variance
//!   `Delta A^2 = <A^2> - <A>^2`;
//! - the commutator `[A, B]` (anti-Hermitian) and anticommutator `{A, B}` (Hermitian);
//! - the **Robertson-Schroedinger relation**
//!   `Delta A^2 Delta B^2 >= 1/4 |<[A,B]>|^2 + 1/4 (<{A,B}> - 2<A><B>)^2`, both sides
//!   computed exactly, so equality (a minimum-uncertainty state) and strictness are
//!   decided, not estimated;
//! - the exact real spectrum ([`crate::exact_operator::ExactSpectrum`]) and, for a
//!   declared rational spectrum, the verified spectral projectors
//!   ([`crate::exact_hermitian::spectral_resolution`]);
//! - the Pauli observables, from [`crate::pauli`].
//!
//! **[`Observable`]** is the `f64` face: a complex `nalgebra` matrix checked to be
//! Hermitian within a named construction tolerance (`Diagnostic`). Each expectation
//! revalidates its public matrix at [`DEFAULT_HERMITIAN_TOL`], independently of that
//! construction tolerance. A further realness check refuses an imaginary part above
//! `DEFAULT_HERMITIAN_TOL * (1 + ||A||_F)` instead of dropping it.
//!
//! AuthorityEffect: None.

use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
use core_number_theory::rational::{ri, Rational};

use crate::density_matrix::{ExactDensityError, ExactDensityMatrix};
use crate::exact_hermitian::{self, SpectralResolution, SpectrumError};
use crate::exact_operator::{ExactOperator, ExactSpectrum, OperatorError};
use crate::pauli::Pauli;
use crate::quantum_state::{QuantumState, RayError, RayVector};
use linear_algebra::linear_algebra::density::NumericalDensityMatrix as LinAlgDensityMatrix;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite observable face.";

/// Default Hermiticity tolerance for operation replay and the base of its scaled
/// realness tolerance. A constructor's supplied tolerance applies only to admission.
/// These diagnostic thresholds are not certificates.
pub const DEFAULT_HERMITIAN_TOL: f64 = 1e-7;

// ---------------------------------------------------------------------------
// Exact observables
// ---------------------------------------------------------------------------

/// Refusals of the exact observable constructors and products.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ExactObservableError {
    #[error("operator: {0}")]
    Operator(OperatorError),
    #[error("an observable is square, got {rows}x{cols}")]
    NotSquare { rows: usize, cols: usize },
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("ray: {0}")]
    Ray(RayError),
    #[error("state: {0}")]
    State(ExactDensityError),
    #[error("declared spectrum refused: {0:?}")]
    Spectrum(SpectrumError),
}

impl From<OperatorError> for ExactObservableError {
    fn from(e: OperatorError) -> Self {
        ExactObservableError::Operator(e)
    }
}

/// A Hermitian operator over `Q(i)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactObservable {
    op: ExactOperator,
}

/// The two sides of the Robertson-Schroedinger relation, exactly.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UncertaintyRelation {
    /// `Delta A^2 * Delta B^2`.
    pub variance_product: Rational,
    /// `1/4 |<[A,B]>|^2 + 1/4 (<{A,B}> - 2 <A><B>)^2`.
    pub lower_bound: Rational,
}

impl UncertaintyRelation {
    /// `variance_product >= lower_bound`: the relation, which holds for every state.
    pub fn holds(&self) -> bool {
        self.variance_product >= self.lower_bound
    }

    /// `variance_product = lower_bound`: a minimum-uncertainty state for the pair.
    pub fn is_saturated(&self) -> bool {
        self.variance_product == self.lower_bound
    }
}

impl ExactObservable {
    /// Accept `op` only when it is exactly Hermitian.
    pub fn try_new(op: ExactOperator) -> Result<Self, ExactObservableError> {
        if op.rows() != op.cols() {
            return Err(ExactObservableError::NotSquare {
                rows: op.rows(),
                cols: op.cols(),
            });
        }
        op.check_hermitian()?;
        Ok(Self { op })
    }

    /// The identity observable `I_n`.
    pub fn identity(n: usize) -> Result<Self, ExactObservableError> {
        Self::try_new(ExactOperator::identity(n)?)
    }

    /// The Pauli observable of one qubit.
    pub fn pauli(p: Pauli) -> Self {
        Self {
            op: p.to_operator(),
        }
    }

    /// The operator.
    pub fn as_operator(&self) -> &ExactOperator {
        &self.op
    }

    /// Dimension `n`.
    pub fn dim(&self) -> usize {
        self.op.rows()
    }

    /// `<psi, A psi> / <psi, psi>` for a ray.
    pub fn expectation_ray(&self, ray: &RayVector) -> Result<Rational, ExactObservableError> {
        self.check_dim(ray.len())?;
        ray.expectation_hermitian(&self.op)
            .map_err(ExactObservableError::Ray)
    }

    /// `Tr(A rho)` for a density operator.
    pub fn expectation_state(
        &self,
        rho: &ExactDensityMatrix,
    ) -> Result<Rational, ExactObservableError> {
        self.check_dim(rho.dim())?;
        rho.expectation(&self.op)
            .map_err(ExactObservableError::State)
    }

    fn check_dim(&self, actual: usize) -> Result<(), ExactObservableError> {
        if actual == self.dim() {
            Ok(())
        } else {
            Err(ExactObservableError::DimensionMismatch {
                expected: self.dim(),
                actual,
            })
        }
    }

    /// `A^2`, again Hermitian.
    pub fn square(&self) -> Result<Self, ExactObservableError> {
        Self::try_new(self.op.mul(&self.op)?)
    }

    /// The variance `<A^2> - <A>^2` in a ray, a nonnegative rational.
    pub fn variance_ray(&self, ray: &RayVector) -> Result<Rational, ExactObservableError> {
        let mean = self.expectation_ray(ray)?;
        let mean_square = self.square()?.expectation_ray(ray)?;
        Ok(mean_square - &mean * &mean)
    }

    /// The variance `Tr(rho A^2) - Tr(rho A)^2` in a state.
    pub fn variance_state(
        &self,
        rho: &ExactDensityMatrix,
    ) -> Result<Rational, ExactObservableError> {
        let mean = self.expectation_state(rho)?;
        let mean_square = self.square()?.expectation_state(rho)?;
        Ok(mean_square - &mean * &mean)
    }

    /// `[A, B] = AB - BA`, anti-Hermitian (`[A,B]^* = -[A,B]`).
    pub fn commutator(&self, other: &Self) -> Result<ExactOperator, ExactObservableError> {
        self.check_dim(other.dim())?;
        Ok(self.op.commutator(&other.op)?)
    }

    /// `{A, B} = AB + BA`, Hermitian.
    pub fn anticommutator(&self, other: &Self) -> Result<Self, ExactObservableError> {
        self.check_dim(other.dim())?;
        Self::try_new(self.op.anticommutator(&other.op)?)
    }

    /// `[A, B] = 0` exactly.
    pub fn commutes_with(&self, other: &Self) -> Result<bool, ExactObservableError> {
        Ok(self.commutator(other)?.is_zero())
    }

    fn commutator_mean_norm_sq(
        &self,
        other: &Self,
        rho: &ExactDensityMatrix,
    ) -> Result<Rational, ExactObservableError> {
        let commutator = self.commutator(other)?;
        let prod = commutator.mul(rho.as_operator())?;
        Ok(prod.trace()?.norm_sq())
    }

    /// The Robertson-Schroedinger relation for the pair `(A, B)` in a state, both sides
    /// exact.
    pub fn uncertainty_relation(
        &self,
        other: &Self,
        rho: &ExactDensityMatrix,
    ) -> Result<UncertaintyRelation, ExactObservableError> {
        self.check_dim(other.dim())?;
        let va = self.variance_state(rho)?;
        let vb = other.variance_state(rho)?;
        let ma = self.expectation_state(rho)?;
        let mb = other.expectation_state(rho)?;
        // <[A,B]> = Tr([A,B] rho) is purely imaginary; |.|^2 is its squared modulus.
        let comm_norm_sq = self.commutator_mean_norm_sq(other, rho)?;
        let anticommutator = self.anticommutator(other)?;
        let anticommutator_mean = anticommutator.expectation_state(rho)?;
        let covariance = anticommutator_mean - ri(2) * &ma * &mb;
        let quarter = ri(4).recip();
        let lower_bound = &quarter * comm_norm_sq + &quarter * &covariance * &covariance;
        Ok(UncertaintyRelation {
            variance_product: va * vb,
            lower_bound,
        })
    }

    /// The exact real spectrum (found, not declared).
    pub fn spectrum(&self) -> Result<ExactSpectrum, ExactObservableError> {
        Ok(self.op.spectrum()?)
    }

    /// The spectral resolution `A = sum_j l_j P_j` for a *declared* rational spectrum,
    /// verified (`A P_j = l_j P_j`, `P_j != 0`) and refused when wrong or incomplete.
    pub fn spectral_resolution(
        &self,
        declared: &[Rational],
    ) -> Result<SpectralResolution, ExactObservableError> {
        exact_hermitian::spectral_resolution(self.op.as_matrix(), declared)
            .map_err(ExactObservableError::Spectrum)
    }
}

// ---------------------------------------------------------------------------
// f64 diagnostic face
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum ObservableError {
    #[error("invalid Hermitian diagnostic tolerance")]
    InvalidTolerance,
    #[error("nonfinite matrix or diagnostic arithmetic")]
    NonFinite,
    #[error("limits: {0}")]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("non-Hermitian operator with defect {defect}")]
    NonHermitian { defect: f64 },
    #[error("zero dimension")]
    ZeroDimension,
    /// The expectation value has an imaginary part beyond the tolerance, which a
    /// Hermitian observable cannot produce: the input is not a state or the matrix is
    /// not Hermitian enough.
    #[error("the expectation value has imaginary part {imaginary}, beyond tolerance {tol}")]
    NonRealExpectation { imaginary: f64, tol: f64 },
}

/// Quantum observable represented as a Hermitian matrix A ∈ ℂ^{n×n} (`Diagnostic`).
#[derive(Debug, Clone, PartialEq)]
pub struct Observable {
    /// Hilbert dimension n.
    pub dim: usize,
    /// Complex Hermitian matrix A = A† (within the construction tolerance).
    pub matrix: CMatrix,
    /// Stable label / object id.
    pub label: String,
}

impl Observable {
    /// Construct and validate a Hermitian observable from a sovereign `CMatrix`:
    /// `||A - A*||_F <= tol`. Expectation operations revalidate public storage at
    /// [`DEFAULT_HERMITIAN_TOL`]; a loose construction tolerance does not relax them.
    pub fn try_new(
        dim: usize,
        matrix: CMatrix,
        label: impl Into<String>,
        tol: f64,
    ) -> Result<Self, ObservableError> {
        Self::validate_matrix(dim, &matrix, tol)?;
        Ok(Self {
            dim,
            matrix,
            label: label.into(),
        })
    }

    fn check_matrix_hermitian_defect(matrix: &CMatrix, tol: f64) -> Result<(), ObservableError> {
        if !matrix.iter().all(|z| z.re.is_finite() && z.im.is_finite()) {
            return Err(ObservableError::NonFinite);
        }
        let defect = (matrix - matrix.adjoint()).norm();
        if !defect.is_finite() {
            return Err(ObservableError::NonFinite);
        }
        if defect > tol {
            return Err(ObservableError::NonHermitian { defect });
        }
        Ok(())
    }

    fn validate_matrix(dim: usize, matrix: &CMatrix, tol: f64) -> Result<(), ObservableError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(ObservableError::InvalidTolerance);
        }
        if dim == 0 {
            return Err(ObservableError::ZeroDimension);
        }
        core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            dim,
            dim,
            std::mem::size_of::<C64>(),
        )?;
        if (matrix.nrows(), matrix.ncols()) != (dim, dim) {
            return Err(ObservableError::DimensionMismatch {
                expected: dim,
                actual: matrix.nrows(),
            });
        }
        Self::check_matrix_hermitian_defect(matrix, tol)
    }

    /// Identity observable I_n, `n >= 1`.
    pub fn identity(dim: usize) -> Result<Self, ObservableError> {
        if dim == 0 {
            return Err(ObservableError::ZeroDimension);
        }
        core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            dim,
            dim,
            std::mem::size_of::<C64>(),
        )?;
        Ok(Self {
            dim,
            matrix: CMatrix::identity(dim, dim),
            label: "I".into(),
        })
    }

    fn pauli(p: Pauli) -> Self {
        Self {
            dim: 2,
            matrix: p.to_cmatrix(),
            label: format!("sigma_{}", p.letter().to_ascii_lowercase()),
        }
    }

    /// Pauli-X observable σ_x, from the exact matrix of [`Pauli::X`].
    pub fn pauli_x() -> Self {
        Self::pauli(Pauli::X)
    }

    /// Pauli-Y observable σ_y.
    pub fn pauli_y() -> Self {
        Self::pauli(Pauli::Y)
    }

    /// Pauli-Z observable σ_z.
    pub fn pauli_z() -> Self {
        Self::pauli(Pauli::Z)
    }

    /// Hermiticity defect ‖A - A†‖_F.
    pub fn hermitian_defect(&self) -> f64 {
        (&self.matrix - self.matrix.adjoint()).norm()
    }

    fn real_part(&self, value: C64, scale: f64) -> Result<f64, ObservableError> {
        if !value.re.is_finite() || !value.im.is_finite() || !scale.is_finite() {
            return Err(ObservableError::NonFinite);
        }
        let tol = DEFAULT_HERMITIAN_TOL * (1.0 + scale);
        if value.im.abs() > tol {
            return Err(ObservableError::NonRealExpectation {
                imaginary: value.im,
                tol,
            });
        }
        Ok(value.re)
    }

    /// Expectation value ⟨ψ|A|ψ⟩ on a pure quantum state vector. Revalidates public
    /// matrix storage and Hermiticity at [`DEFAULT_HERMITIAN_TOL`] before the product,
    /// then refuses an imaginary part above the scaled default realness tolerance.
    pub fn expectation_value_state(&self, psi: &QuantumState) -> Result<f64, ObservableError> {
        Self::validate_matrix(self.dim, &self.matrix, DEFAULT_HERMITIAN_TOL)?;
        if psi.dim() != self.dim {
            return Err(ObservableError::DimensionMismatch {
                expected: self.dim,
                actual: psi.dim(),
            });
        }
        let v = psi.to_cvector();
        if v.len() != self.dim {
            return Err(ObservableError::DimensionMismatch {
                expected: self.dim,
                actual: v.len(),
            });
        }
        if v.iter().any(|z| !z.re.is_finite() || !z.im.is_finite()) {
            return Err(ObservableError::NonFinite);
        }
        let av = &self.matrix * &v;
        let mut exp = C64::new(0.0, 0.0);
        for i in 0..self.dim {
            exp += v[i].conj() * av[i];
        }
        self.real_part(exp, self.matrix.norm())
    }

    /// Expectation value Tr(A ρ) on a validated `f64` density operator, with the same
    /// default Hermiticity replay and scaled realness checks as the pure-state route.
    pub fn expectation_value_density(
        &self,
        rho: &LinAlgDensityMatrix,
    ) -> Result<f64, ObservableError> {
        Self::validate_matrix(self.dim, &self.matrix, DEFAULT_HERMITIAN_TOL)?;
        if rho.dim() != self.dim {
            return Err(ObservableError::DimensionMismatch {
                expected: self.dim,
                actual: rho.dim(),
            });
        }
        let tr = (&self.matrix * rho.rho()).trace();
        self.real_part(tr, self.matrix.norm())
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/observable.rs
// Claim: urn:core:crates_rs:core-quantum-physics:observable:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hilbert_space::HilbertSpace;
    use linear_algebra::linear_algebra::density::DensityMatrixConfig;
    use core_number_theory::cyclotomic::GaussianRat;
    use core_number_theory::rational::rq;

    fn ray(entries: &[(i64, i64)]) -> RayVector {
        RayVector::from_ints(entries).unwrap()
    }

    fn pure(entries: &[(i64, i64)]) -> ExactDensityMatrix {
        ExactDensityMatrix::pure(&ray(entries)).unwrap()
    }

    #[test]
    fn pauli_observables_hermitian() {
        for p in [
            Observable::pauli_x(),
            Observable::pauli_y(),
            Observable::pauli_z(),
        ] {
            assert_eq!(p.hermitian_defect(), 0.0);
        }
        assert_eq!(Observable::pauli_y().matrix[(0, 1)], C64::new(0.0, -1.0));
    }

    #[test]
    fn pauli_expectation_values() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let s0 = QuantumState::computational_basis(&h2, 0, "0").unwrap();
        let s1 = QuantumState::computational_basis(&h2, 1, "1").unwrap();
        let pz = Observable::pauli_z();
        assert!((pz.expectation_value_state(&s0).unwrap() - 1.0).abs() < 1e-12);
        assert!((pz.expectation_value_state(&s1).unwrap() - (-1.0)).abs() < 1e-12);
        let rho0 =
            LinAlgDensityMatrix::from_diagonal_probs(&[1.0, 0.0], &DensityMatrixConfig::default())
                .unwrap();
        assert!((pz.expectation_value_density(&rho0).unwrap() - 1.0).abs() < 1e-12);
    }

    #[test]
    fn rejects_non_hermitian() {
        let mut mat = CMatrix::zeros(2, 2);
        mat[(0, 1)] = C64::new(1.0, 1.0);
        mat[(1, 0)] = C64::new(1.0, 0.0); // non-Hermitian
        let err = Observable::try_new(2, mat, "bad", DEFAULT_HERMITIAN_TOL);
        assert!(matches!(err, Err(ObservableError::NonHermitian { .. })));
    }

    #[test]
    fn an_expectation_with_an_imaginary_part_is_refused_not_truncated() {
        // A non-Hermitian matrix that passed a loose tolerance: [[0, i], [0, 0]] has
        // <+| A |+> = i/2, purely imaginary. Operation replay uses the stricter
        // default Hermiticity policy before computing that product.
        let mut mat = CMatrix::zeros(2, 2);
        mat[(0, 1)] = C64::new(0.0, 1.0);
        let loose = Observable::try_new(2, mat, "loose", 10.0).unwrap();
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let plus =
            QuantumState::try_normalized(&h2, vec![C64::new(1.0, 0.0), C64::new(1.0, 0.0)], "+")
                .unwrap();
        assert!(matches!(
            loose.expectation_value_state(&plus),
            Err(ObservableError::NonHermitian { defect })
                if (defect - 2.0_f64.sqrt()).abs() < 1e-12
        ));
        let rho_plus = LinAlgDensityMatrix::from_validated(
            2,
            vec![C64::new(0.5, 0.0); 4],
            &DensityMatrixConfig::default(),
        )
        .unwrap();
        assert!(matches!(
            loose.expectation_value_density(&rho_plus),
            Err(ObservableError::NonHermitian { defect })
                if (defect - 2.0_f64.sqrt()).abs() < 1e-12
        ));
        // Independently exercise the realness boundary: i/2 must never become 0.
        assert!(matches!(
            loose.real_part(C64::new(0.0, 0.5), loose.matrix.norm()),
            Err(ObservableError::NonRealExpectation { imaginary, tol })
                if imaginary == 0.5 && tol == 2.0 * DEFAULT_HERMITIAN_TOL
        ));
        // X|+> = |+>: both coherent state routes have the real expectation 1.
        let x = Observable::pauli_x();
        assert!((x.expectation_value_state(&plus).unwrap() - 1.0).abs() < 1e-12);
        assert!((x.expectation_value_density(&rho_plus).unwrap() - 1.0).abs() < 1e-12);
        assert_eq!(x.real_part(C64::new(1.0, 1e-9), x.matrix.norm()), Ok(1.0));
    }

    #[test]
    fn exact_observables_refuse_non_hermitian_and_mismatched_operands() {
        let non_hermitian = ExactOperator::from_rows(vec![
            vec![GaussianRat::zero(), GaussianRat::one()],
            vec![GaussianRat::zero(), GaussianRat::zero()],
        ])
        .unwrap();
        assert!(matches!(
            ExactObservable::try_new(non_hermitian),
            Err(ExactObservableError::Operator(OperatorError::NotHermitian(
                _
            )))
        ));
        let rect = ExactOperator::zeros(2, 3).unwrap();
        assert_eq!(
            ExactObservable::try_new(rect),
            Err(ExactObservableError::NotSquare { rows: 2, cols: 3 })
        );
        let z = ExactObservable::pauli(Pauli::Z);
        assert_eq!(
            z.expectation_ray(&ray(&[(1, 0), (0, 0), (0, 0)])),
            Err(ExactObservableError::DimensionMismatch {
                expected: 2,
                actual: 3
            })
        );
        assert!(matches!(
            z.commutator(&ExactObservable::identity(3).unwrap()),
            Err(ExactObservableError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn expectation_and_variance_of_pauli_observables_are_exact() {
        let (x, y, z) = (
            ExactObservable::pauli(Pauli::X),
            ExactObservable::pauli(Pauli::Y),
            ExactObservable::pauli(Pauli::Z),
        );
        let plus = ray(&[(1, 0), (1, 0)]);
        assert_eq!(x.expectation_ray(&plus).unwrap(), ri(1));
        assert_eq!(z.expectation_ray(&plus).unwrap(), ri(0));
        assert_eq!(x.variance_ray(&plus).unwrap(), ri(0));
        assert_eq!(z.variance_ray(&plus).unwrap(), ri(1));
        // The same numbers in the density picture, and for the ray (3, 4).
        assert_eq!(z.variance_state(&pure(&[(1, 0), (1, 0)])).unwrap(), ri(1));
        let r = ray(&[(3, 0), (4, 0)]);
        assert_eq!(z.expectation_ray(&r).unwrap(), rq(-7, 25));
        assert_eq!(z.variance_ray(&r).unwrap(), rq(576, 625));
        assert_eq!(y.expectation_ray(&r).unwrap(), ri(0));
    }

    /// Pure qubit states saturate the relation for `(X, Y)`: for the ray (3, 4),
    /// `Delta X^2 Delta Y^2 = 49/625`, `<[X,Y]> = 2i<Z> = -14i/25` so the commutator term is
    /// `1/4 * 196/625 = 49/625`, and the covariance term is zero.
    #[test]
    fn the_robertson_schroedinger_relation_is_decided_exactly() {
        let (x, y) = (
            ExactObservable::pauli(Pauli::X),
            ExactObservable::pauli(Pauli::Y),
        );
        let rel = x
            .uncertainty_relation(&y, &pure(&[(3, 0), (4, 0)]))
            .unwrap();
        assert_eq!(rel.variance_product, rq(49, 625));
        assert_eq!(rel.lower_bound, rq(49, 625));
        assert!(rel.holds() && rel.is_saturated());
        // |0> is a minimum-uncertainty state for (X, Y): 1 * 1 = 1/4 |2i|^2.
        let rel = x
            .uncertainty_relation(&y, &pure(&[(1, 0), (0, 0)]))
            .unwrap();
        assert_eq!(
            (rel.variance_product.clone(), rel.lower_bound.clone()),
            (ri(1), ri(1))
        );
        // The maximally mixed state is strictly above the bound: 1 >= 0.
        let mixed = ExactDensityMatrix::maximally_mixed(2).unwrap();
        let rel = x.uncertainty_relation(&y, &mixed).unwrap();
        assert_eq!(
            (rel.variance_product.clone(), rel.lower_bound.clone()),
            (ri(1), ri(0))
        );
        assert!(rel.holds() && !rel.is_saturated());
        // Commuting observables have a zero commutator term: (Z, Z) on |+>.
        let z = ExactObservable::pauli(Pauli::Z);
        let rel = z
            .uncertainty_relation(&z, &pure(&[(1, 0), (1, 0)]))
            .unwrap();
        assert_eq!(
            (rel.variance_product.clone(), rel.lower_bound.clone()),
            (ri(1), ri(1))
        );
    }

    #[test]
    fn commutators_and_anticommutators_of_the_pauli_observables() {
        let (x, y, z) = (
            ExactObservable::pauli(Pauli::X),
            ExactObservable::pauli(Pauli::Y),
            ExactObservable::pauli(Pauli::Z),
        );
        assert!(!x.commutes_with(&z).unwrap());
        assert!(x.commutes_with(&x).unwrap());
        // {X, Y} = 0 and [X, Y] = 2 i Z.
        assert!(x.anticommutator(&y).unwrap().as_operator().is_zero());
        assert_eq!(
            x.commutator(&y).unwrap(),
            z.as_operator()
                .scale(&GaussianRat::from_ints(0, 2))
                .unwrap()
        );
        // The commutator is anti-Hermitian, the anticommutator Hermitian.
        let c = x.commutator(&z).unwrap();
        assert_eq!(
            c.dagger().unwrap(),
            c.scale(&GaussianRat::from_ints(-1, 0)).unwrap()
        );
    }

    #[test]
    fn a_declared_spectrum_is_verified_and_the_found_spectrum_agrees() {
        let y = ExactObservable::pauli(Pauli::Y);
        let res = y.spectral_resolution(&[ri(1), ri(-1)]).unwrap();
        assert_eq!(res.eigenvalues(), &[ri(-1), ri(1)]);
        // P_+ = (I + Y)/2.
        let expected = ExactOperator::identity(2)
            .unwrap()
            .add(y.as_operator())
            .unwrap()
            .scale_rat(&rq(1, 2))
            .unwrap();
        assert_eq!(res.projectors()[1], *expected.as_matrix());
        assert!(matches!(
            y.spectral_resolution(&[ri(1)]),
            Err(ExactObservableError::Spectrum(
                SpectrumError::SpectrumIncomplete
            ))
        ));
        assert_eq!(
            y.spectrum().unwrap().rational_eigenvalues(),
            Some(vec![(ri(-1), 1), (ri(1), 1)])
        );
    }
}
