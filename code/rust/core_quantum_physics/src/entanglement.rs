//! Bipartite entanglement of pure states, and partial traces.
//!
//! For a pure state `psi` on `C^dA (x) C^dB` the coefficient matrix `Psi_ij = <i j|psi>`
//! has singular values `s_k` (the Schmidt coefficients). The Schmidt probabilities
//! `s_k^2 / <psi|psi>` sum to one, the entanglement entropy is their Shannon entropy,
//! and `psi` is a product state exactly when the Schmidt rank is 1.
//! [`Entanglement::schmidt_probabilities`], [`Entanglement::pure_state_entanglement_entropy`]
//! and [`Entanglement::is_separable_pure`] compute these in `f64` (nalgebra SVD;
//! diagnostic), and [`Entanglement::schmidt_rank_exact`] decides the rank exactly over
//! `Q(i)` by `linear_algebra::exact_field::elimination::rank` on an exact
//! [`RayVector`].
//!
//! The older [`Entanglement::entanglement_entropy`] family acts on a
//! [`DensityMatrix`] that stores only diagonal populations. It returns the Shannon
//! entropy of a marginal population vector, which equals the entanglement entropy only
//! for a pure state whose Schmidt basis is the computational basis; it is kept for its
//! callers and must not be read as an entanglement measure for general states.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::density_matrix::{DensityError, DensityMatrix, DEFAULT_TOL};
use crate::entropy::Entropy;
use crate::hilbert_space::HilbertSpace;
use crate::quantum_state::{QuantumState, RayVector};
use linear_algebra::exact_field::{elimination, matrix};
use linear_algebra::linear_algebra::complex_matrix::CMatrix;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite entanglement face.";

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum EntanglementError {
    #[error(transparent)]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("density error: {0}")]
    Density(DensityError),
    #[error("invalid subsystem dimension")]
    InvalidSubsystemDimension,
    #[error(transparent)]
    Purification(#[from] crate::purification::ExactPurificationError),
    #[error(transparent)]
    TraceNorm(#[from] crate::trace_norm_certificate::TraceNormError),
    #[error(transparent)]
    Operator(#[from] crate::exact_operator::OperatorError),
    #[error("concurrence square roots are outside the rational field")]
    IrrationalConcurrence,
    #[error("exact linear algebra refused: {0}")]
    ExactLinearAlgebra(String),
}

impl From<DensityError> for EntanglementError {
    fn from(e: DensityError) -> Self {
        EntanglementError::Density(e)
    }
}

/// Finite carrier for `entanglement`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Entanglement {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl Entanglement {
    /// Phase and normalization independent squared three-tangle from Cayley's
    /// 2x2x2 hyperdeterminant. It distinguishes GHZ (one) from W (zero).
    pub fn three_tangle_squared(ray: &RayVector) -> Result<Rational, EntanglementError> {
        use core_number_theory::rational::ri;
        if ray.len() != 8 {
            return Err(EntanglementError::DimensionMismatch {
                expected: 8,
                actual: ray.len(),
            });
        }
        let a = ray.entries();
        let product = |indices: [usize; 4]| {
            indices
                .into_iter()
                .fold(GaussianRat::one(), |p, i| p.mul(&a[i]))
        };
        let d1 = [[0, 0, 7, 7], [1, 1, 6, 6], [2, 2, 5, 5], [4, 4, 3, 3]]
            .into_iter()
            .fold(GaussianRat::zero(), |s, is| s.add(&product(is)));
        let d2 = [
            [0, 7, 3, 4],
            [0, 7, 5, 2],
            [0, 7, 6, 1],
            [3, 4, 5, 2],
            [3, 4, 6, 1],
            [5, 2, 6, 1],
        ]
        .into_iter()
        .fold(GaussianRat::zero(), |s, is| s.add(&product(is)));
        let d3 = product([0, 6, 5, 3]).add(&product([7, 1, 2, 4]));
        let determinant = d1
            .sub(&d2.mul(&GaussianRat::from_ints(2, 0)))
            .add(&d3.mul(&GaussianRat::from_ints(4, 0)));
        let norm = ray.norm_sq();
        Ok(ri(16) * determinant.norm_sq() / (&norm * &norm * &norm * &norm))
    }

    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Compute reduced density matrix on subsystem A: ρ_A = Tr_B(ρ_AB)
    /// for a composite system of dimension d_A · d_B.
    pub fn partial_trace_b(
        rho_ab: &DensityMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<DensityMatrix, EntanglementError> {
        Self::check_population_bipartition(rho_ab, dim_a, dim_b)?;
        let mut p_a = vec![0.0; dim_a];
        for i in 0..dim_a {
            let mut sum_b = 0.0;
            for j in 0..dim_b {
                let idx = i * dim_b + j;
                sum_b += rho_ab.probs[idx];
            }
            p_a[i] = sum_b;
        }
        let space_a = HilbertSpace::try_new(dim_a, "A")
            .map_err(|_| EntanglementError::InvalidSubsystemDimension)?;
        Ok(DensityMatrix::try_from_probs(
            &space_a,
            p_a,
            format!("{}_A", rho_ab.label),
            DEFAULT_TOL,
        )?)
    }

    /// Compute reduced density matrix on subsystem B: ρ_B = Tr_A(ρ_AB).
    pub fn partial_trace_a(
        rho_ab: &DensityMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<DensityMatrix, EntanglementError> {
        Self::check_population_bipartition(rho_ab, dim_a, dim_b)?;
        let mut p_b = vec![0.0; dim_b];
        for j in 0..dim_b {
            let mut sum_a = 0.0;
            for i in 0..dim_a {
                let idx = i * dim_b + j;
                sum_a += rho_ab.probs[idx];
            }
            p_b[j] = sum_a;
        }
        let space_b = HilbertSpace::try_new(dim_b, "B")
            .map_err(|_| EntanglementError::InvalidSubsystemDimension)?;
        Ok(DensityMatrix::try_from_probs(
            &space_b,
            p_b,
            format!("{}_B", rho_ab.label),
            DEFAULT_TOL,
        )?)
    }

    fn check_population_bipartition(
        rho_ab: &DensityMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<(), EntanglementError> {
        if dim_a == 0 || dim_b == 0 {
            return Err(EntanglementError::InvalidSubsystemDimension);
        }
        rho_ab.validate(DEFAULT_TOL)?;
        let total = core_kernel::resource_limits::OperationLimits::default()
            .checked_product(dim_a, dim_b)?;
        if rho_ab.dim != total {
            return Err(EntanglementError::DimensionMismatch {
                expected: total,
                actual: rho_ab.dim,
            });
        }
        Ok(())
    }

    /// Compute reduced density matrix on subsystem A for general complex matrix:
    /// (Tr_B(M))_{i_A, j_A} = \sum_{k_B=0}^{d_B-1} M_{i_A \cdot d_B + k_B, j_A \cdot d_B + k_B}.
    pub fn partial_trace_b_matrix(
        mat: &linear_algebra::linear_algebra::complex_matrix::CMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<linear_algebra::linear_algebra::complex_matrix::CMatrix, EntanglementError> {
        if dim_a == 0 || dim_b == 0 {
            return Err(EntanglementError::InvalidSubsystemDimension);
        }
        let total = core_kernel::resource_limits::OperationLimits::default()
            .checked_product(dim_a, dim_b)?;
        if mat.nrows() != total || mat.ncols() != total {
            return Err(EntanglementError::DimensionMismatch {
                expected: total,
                actual: mat.nrows(),
            });
        }
        let mut out = linear_algebra::linear_algebra::complex_matrix::CMatrix::zeros(dim_a, dim_a);
        for ia in 0..dim_a {
            for ja in 0..dim_a {
                let mut sum = linear_algebra::linear_algebra::complex_matrix::C64::new(0.0, 0.0);
                for kb in 0..dim_b {
                    let r = ia * dim_b + kb;
                    let c = ja * dim_b + kb;
                    sum += mat[(r, c)];
                }
                out[(ia, ja)] = sum;
            }
        }
        Ok(out)
    }

    /// Compute reduced density matrix on subsystem B for general complex matrix:
    /// (Tr_A(M))_{i_B, j_B} = \sum_{k_A=0}^{d_A-1} M_{k_A \cdot d_B + i_B, k_A \cdot d_B + j_B}.
    pub fn partial_trace_a_matrix(
        mat: &linear_algebra::linear_algebra::complex_matrix::CMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<linear_algebra::linear_algebra::complex_matrix::CMatrix, EntanglementError> {
        if dim_a == 0 || dim_b == 0 {
            return Err(EntanglementError::InvalidSubsystemDimension);
        }
        let total = core_kernel::resource_limits::OperationLimits::default()
            .checked_product(dim_a, dim_b)?;
        if mat.nrows() != total || mat.ncols() != total {
            return Err(EntanglementError::DimensionMismatch {
                expected: total,
                actual: mat.nrows(),
            });
        }
        let mut out = linear_algebra::linear_algebra::complex_matrix::CMatrix::zeros(dim_b, dim_b);
        for ib in 0..dim_b {
            for jb in 0..dim_b {
                let mut sum = linear_algebra::linear_algebra::complex_matrix::C64::new(0.0, 0.0);
                for ka in 0..dim_a {
                    let r = ka * dim_b + ib;
                    let c = ka * dim_b + jb;
                    sum += mat[(r, c)];
                }
                out[(ib, jb)] = sum;
            }
        }
        Ok(out)
    }

    /// Entanglement entropy E(ρ_AB) = S(ρ_A) = -Tr(ρ_A ln ρ_A).
    pub fn entanglement_entropy(
        rho_ab: &DensityMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<f64, EntanglementError> {
        let rho_a = Self::partial_trace_b(rho_ab, dim_a, dim_b)?;
        Ok(Entropy::von_neumann(&rho_a))
    }

    /// Entanglement entropy in bits (divided by ln 2).
    pub fn entanglement_entropy_bits(
        rho_ab: &DensityMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<f64, EntanglementError> {
        let e = Self::entanglement_entropy(rho_ab, dim_a, dim_b)?;
        Ok(e / std::f64::consts::LN_2)
    }

    fn check_bipartition(
        total: usize,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<(), EntanglementError> {
        if dim_a == 0 || dim_b == 0 {
            return Err(EntanglementError::InvalidSubsystemDimension);
        }
        let product = dim_a
            .checked_mul(dim_b)
            .ok_or(EntanglementError::InvalidSubsystemDimension)?;
        if product != total {
            return Err(EntanglementError::DimensionMismatch {
                expected: product,
                actual: total,
            });
        }
        Ok(())
    }

    /// The Schmidt probabilities of the pure state `psi` on `C^dim_a (x) C^dim_b`, in
    /// descending order: the squared singular values of the coefficient matrix
    /// `Psi_ij = <i j|psi>` divided by `<psi|psi>`. There are `min(dim_a, dim_b)` of them
    /// and they sum to one. `f64` diagnostic (nalgebra SVD); the phases of `psi` matter.
    pub fn schmidt_probabilities(
        psi: &QuantumState,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<Vec<f64>, EntanglementError> {
        Self::check_bipartition(psi.dim(), dim_a, dim_b)?;
        let coefficients =
            CMatrix::from_row_iterator(dim_a, dim_b, psi.amplitudes().iter().copied());
        let norm_sq = psi.norm_sq();
        let mut probabilities: Vec<f64> = coefficients
            .svd(false, false)
            .singular_values
            .iter()
            .map(|s| s * s / norm_sq)
            .collect();
        probabilities.sort_by(|x, y| y.total_cmp(x));
        Ok(probabilities)
    }

    /// Entanglement entropy `-sum p ln p` of the Schmidt probabilities of `psi`
    /// (nats; `f64` diagnostic). Zero exactly for product states, `ln min(dA, dB)` for
    /// maximally entangled ones.
    pub fn pure_state_entanglement_entropy(
        psi: &QuantumState,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<f64, EntanglementError> {
        let probabilities = Self::schmidt_probabilities(psi, dim_a, dim_b)?;
        let entropy: f64 = probabilities
            .iter()
            .filter(|p| **p > 0.0)
            .map(|p| -p * p.ln())
            .sum();
        Ok(entropy.max(0.0))
    }

    /// Whether the pure state `psi` is a product state `a (x) b`, up to `tol`: the
    /// largest Schmidt probability is at least `1 - tol`. (Earlier versions compared
    /// the entropy of the marginal populations with `tol`, which calls `|++>`
    /// entangled.) For a decision without a tolerance use
    /// [`Entanglement::schmidt_rank_exact`].
    pub fn is_separable_pure(
        psi: &QuantumState,
        dim_a: usize,
        dim_b: usize,
        tol: f64,
    ) -> Result<bool, EntanglementError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(DensityError::InvalidTolerance.into());
        }
        let probabilities = Self::schmidt_probabilities(psi, dim_a, dim_b)?;
        Ok(1.0 - probabilities[0] <= tol)
    }

    /// The exact Schmidt rank of the pure state spanned by `ray` on
    /// `C^dim_a (x) C^dim_b`: the rank over `Q(i)` of its `dim_a x dim_b` coefficient
    /// matrix. The state is a product state if and only if the rank is 1.
    pub fn schmidt_rank_exact(
        ray: &RayVector,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<usize, EntanglementError> {
        Self::check_bipartition(ray.len(), dim_a, dim_b)?;
        let rows: Vec<Vec<GaussianRat>> = ray
            .entries()
            .chunks(dim_b)
            .map(<[GaussianRat]>::to_vec)
            .collect();
        let coefficients = matrix::from_rows(rows)
            .map_err(|e| EntanglementError::ExactLinearAlgebra(e.to_string()))?;
        elimination::rank(&coefficients)
            .map_err(|e| EntanglementError::ExactLinearAlgebra(e.to_string()))
    }

    /// Exact product-state decision: Schmidt rank 1 (see [`Entanglement::schmidt_rank_exact`]).
    pub fn is_separable_pure_exact(
        ray: &RayVector,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<bool, EntanglementError> {
        Ok(Self::schmidt_rank_exact(ray, dim_a, dim_b)? == 1)
    }

    /// Degree / dimension proxy.
    pub fn degree(&self) -> usize {
        self.degree
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/entanglement.rs
// Claim: urn:core:crates_rs:core-quantum-physics:entanglement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bell_state::{BellBasis, BellState};
    use crate::hilbert_space::HilbertSpace;

    #[test]
    fn new_and_fence() {
        let x = Entanglement::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(Entanglement::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn bell_state_entanglement_entropy() {
        let bell_rho = BellState::to_population_density(BellBasis::PhiPlus);
        let e = Entanglement::entanglement_entropy(&bell_rho, 2, 2).unwrap();
        // E = ln 2 for maximally entangled 2-qubit state
        assert!((e - (2.0_f64).ln()).abs() < 1e-12);

        let e_bits = Entanglement::entanglement_entropy_bits(&bell_rho, 2, 2).unwrap();
        assert!((e_bits - 1.0).abs() < 1e-12);
    }

    /// `|++> = |+> (x) |+>` is a product state. The old check used only the diagonal
    /// populations of `|++><++|` (uniform over four outcomes), so it reported entropy
    /// `ln 2` and called the product state entangled.
    #[test]
    fn the_uniform_product_state_plus_plus_is_separable() {
        let h4 = HilbertSpace::try_new(4, "h4").unwrap();
        let pp = QuantumState::try_normalized(
            &h4,
            vec![linear_algebra::linear_algebra::complex_matrix::C64::new(1.0, 0.0); 4],
            "++",
        )
        .unwrap();
        assert!(Entanglement::is_separable_pure(&pp, 2, 2, 1e-9).unwrap());
    }

    fn ray(entries: &[(i64, i64)]) -> RayVector {
        RayVector::from_ints(entries).unwrap()
    }

    fn state_of(entries: &[(i64, i64)]) -> QuantumState {
        let space = HilbertSpace::try_new(entries.len(), "h").unwrap();
        QuantumState::from_ray(&space, &ray(entries), "s").unwrap()
    }

    #[test]
    fn a_bell_state_has_two_equal_schmidt_probabilities_and_entropy_ln_2() {
        let phi_plus = [(1, 0), (0, 0), (0, 0), (1, 0)];
        let p = Entanglement::schmidt_probabilities(&state_of(&phi_plus), 2, 2).unwrap();
        assert_eq!(p.len(), 2);
        assert!((p[0] - 0.5).abs() < 1e-12 && (p[1] - 0.5).abs() < 1e-12);
        let e = Entanglement::pure_state_entanglement_entropy(&state_of(&phi_plus), 2, 2).unwrap();
        assert!((e - 2f64.ln()).abs() < 1e-12);
        assert!(!Entanglement::is_separable_pure(&state_of(&phi_plus), 2, 2, 1e-9).unwrap());
        assert_eq!(
            Entanglement::schmidt_rank_exact(&ray(&phi_plus), 2, 2),
            Ok(2)
        );
    }

    #[test]
    fn the_schmidt_spectrum_of_the_ray_3_0_0_1_is_nine_tenths_one_tenth() {
        let amps = [(3, 0), (0, 0), (0, 0), (1, 0)];
        let p = Entanglement::schmidt_probabilities(&state_of(&amps), 2, 2).unwrap();
        assert!((p[0] - 0.9).abs() < 1e-12 && (p[1] - 0.1).abs() < 1e-12);
        let expected = -(0.9f64 * 0.9f64.ln() + 0.1f64 * 0.1f64.ln());
        let e = Entanglement::pure_state_entanglement_entropy(&state_of(&amps), 2, 2).unwrap();
        assert!((e - expected).abs() < 1e-12);
    }

    #[test]
    fn a_relative_phase_decides_entanglement_which_populations_cannot_see() {
        // (|00> + |01> + |10> + s |11>)/2 is a product state for s = 1 and maximally
        // entangled for s = -1; both have the same uniform populations.
        let product = [(1, 0), (1, 0), (1, 0), (1, 0)];
        let entangled = [(1, 0), (1, 0), (1, 0), (-1, 0)];
        assert_eq!(
            Entanglement::schmidt_rank_exact(&ray(&product), 2, 2),
            Ok(1)
        );
        assert_eq!(
            Entanglement::schmidt_rank_exact(&ray(&entangled), 2, 2),
            Ok(2)
        );
        assert!(Entanglement::is_separable_pure(&state_of(&product), 2, 2, 1e-9).unwrap());
        assert!(!Entanglement::is_separable_pure(&state_of(&entangled), 2, 2, 1e-9).unwrap());
        let e = Entanglement::pure_state_entanglement_entropy(&state_of(&entangled), 2, 2).unwrap();
        assert!((e - 2f64.ln()).abs() < 1e-12);
        // a complex phase i also entangles: (|00> + |01> + |10> + i|11>)/2 has rank 2
        let phase_i = [(1, 0), (1, 0), (1, 0), (0, 1)];
        assert_eq!(
            Entanglement::schmidt_rank_exact(&ray(&phase_i), 2, 2),
            Ok(2)
        );
    }

    #[test]
    fn the_exact_rank_agrees_with_the_number_of_nonzero_schmidt_probabilities() {
        // rows (1, 2, 3) and (2, 4, 6) are proportional, so the rank is 1; rows
        // (1, 2, 3) and (0, 1, 1) are independent, so the rank is 2.
        let rank_one = [(1, 0), (2, 0), (3, 0), (2, 0), (4, 0), (6, 0)];
        let rank_two = [(1, 0), (2, 0), (3, 0), (0, 0), (1, 0), (1, 0)];
        for (amps, rank) in [(rank_one, 1usize), (rank_two, 2usize)] {
            assert_eq!(
                Entanglement::schmidt_rank_exact(&ray(&amps), 2, 3),
                Ok(rank)
            );
            let p = Entanglement::schmidt_probabilities(&state_of(&amps), 2, 3).unwrap();
            assert_eq!(p.iter().filter(|x| **x > 1e-12).count(), rank);
            assert!((p.iter().sum::<f64>() - 1.0).abs() < 1e-12);
        }
        // the transpose cut (3 x 2) has the same rank
        assert_eq!(
            Entanglement::schmidt_rank_exact(&ray(&rank_two), 3, 2),
            Ok(2)
        );
    }

    #[test]
    fn a_wrong_bipartition_is_refused() {
        let amps = [(1, 0), (0, 0), (0, 0), (1, 0)];
        assert_eq!(
            Entanglement::schmidt_probabilities(&state_of(&amps), 3, 2),
            Err(EntanglementError::DimensionMismatch {
                expected: 6,
                actual: 4
            })
        );
        assert_eq!(
            Entanglement::schmidt_rank_exact(&ray(&amps), 0, 4),
            Err(EntanglementError::InvalidSubsystemDimension)
        );
    }

    #[test]
    fn product_state_zero_entanglement() {
        let h4 = HilbertSpace::try_new(4, "h4").unwrap();
        let prod_rho = DensityMatrix::pure_computational(&h4, 0, "00").unwrap();
        let e = Entanglement::entanglement_entropy(&prod_rho, 2, 2).unwrap();
        assert!(e < 1e-12);
    }
}

impl Entanglement {
    /// Squared pure two-qubit concurrence 4 det(rho_A), independent of phase
    /// and normalization of the submitted ray.
    pub fn concurrence_squared(ray: &RayVector) -> Result<Rational, EntanglementError> {
        if ray.len() != 4 {
            return Err(EntanglementError::DimensionMismatch {
                expected: 4,
                actual: ray.len(),
            });
        }
        let a = ray.entries();
        let determinant = a[0].mul(&a[3]).sub(&a[1].mul(&a[2]));
        let norm = ray.norm_sq();
        Ok(core_number_theory::rational::ri(4) * determinant.norm_sq() / (&norm * &norm))
    }
    /// Wootters concurrence for an arbitrary two-qubit density operator, exact
    /// when the spin-flip eigenvalue square roots are rational.
    pub fn concurrence_exact(
        rho: &crate::density_matrix::ExactDensityMatrix,
        square_budget: u64,
    ) -> Result<Rational, EntanglementError> {
        let gram = spin_flip_gram(rho, square_budget)?;
        let values = gram
            .spectrum()?
            .rational_eigenvalues()
            .ok_or(EntanglementError::IrrationalConcurrence)?;
        let mut sum = core_number_theory::rational::ri(0);
        let mut largest = core_number_theory::rational::ri(0);
        for (q, m) in values {
            let root = core_number_theory::rational::sqrt_exact(&q)
                .ok_or(EntanglementError::IrrationalConcurrence)?;
            sum += &root * Rational::from_integer(m.into());
            largest = largest.max(root);
        }
        Ok((core_number_theory::rational::ri(2) * largest - sum)
            .max(core_number_theory::rational::ri(0)))
    }
    /// Certified concurrence bounds when the roots are irrational. The Gram
    /// matrix uses an ordinary exact purification, so every eigenvalue is PSD.
    pub fn concurrence_enclosure(
        rho: &crate::density_matrix::ExactDensityMatrix,
        bits: u32,
        square_budget: u64,
    ) -> Result<core_kernel::interval::Interval, EntanglementError> {
        use core_kernel::interval::Interval;
        use core_number_theory::rational::ri;
        let gram = spin_flip_gram(rho, square_budget)?;
        let mut sum = Interval::point(ri(0));
        let mut largest = Interval::point(ri(0));
        for (range, multiplicity) in crate::trace_norm_certificate::eigenvalue_ranges(&gram, bits)?
        {
            let lo = core_kernel::elementary::sqrt_enclosure(&range.lo().clone().max(ri(0)), bits)
                .map_err(crate::trace_norm_certificate::TraceNormError::from)?;
            let hi = core_kernel::elementary::sqrt_enclosure(&range.hi().clone().max(ri(0)), bits)
                .map_err(crate::trace_norm_certificate::TraceNormError::from)?;
            largest = Interval::new(lo.lo().clone(), hi.hi().clone());
            sum = sum.add(&largest.mul_scalar(&Rational::from_integer(multiplicity.into())));
        }
        let raw = largest.mul_scalar(&ri(2)).sub(&sum);
        Ok(Interval::new(
            raw.lo().clone().max(ri(0)),
            raw.hi().clone().max(ri(0)),
        ))
    }
}
fn spin_flip_gram(
    rho: &crate::density_matrix::ExactDensityMatrix,
    budget: u64,
) -> Result<crate::exact_operator::ExactOperator, EntanglementError> {
    if rho.dim() != 4 {
        return Err(EntanglementError::DimensionMismatch {
            expected: 4,
            actual: rho.dim(),
        });
    }
    let spin_flipped = spin_flipped_operator(rho)?;
    let coefficients = crate::exact_operator::ExactOperator::try_new(
        crate::purification::WeightedPurification::of(rho)?.ordinary_coefficients(budget)?,
    )?;
    let left = coefficients.dagger()?.mul(&spin_flipped)?;
    Ok(left.mul(&coefficients)?)
}

fn spin_flipped_operator(
    rho: &crate::density_matrix::ExactDensityMatrix,
) -> Result<crate::exact_operator::ExactOperator, EntanglementError> {
    let flip = crate::pauli::Pauli::Y
        .to_operator()
        .kron(&crate::pauli::Pauli::Y.to_operator())?;
    let conjugate = crate::exact_operator::ExactOperator::try_new(
        linear_algebra::exact_field::involution::conjugate_entries(rho.matrix())
            .map_err(crate::exact_operator::OperatorError::Algebra)?,
    )?;
    let left = flip.mul(&conjugate)?;
    Ok(left.mul(&flip)?)
}
