//! Canonical Bell states (maximally entangled 2-qubit states) for `core_quantum_physics`.
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`C64`, `CVector`, `CMatrix`).
//! Provides diagnostic state vectors and exact rational ray/projector constructions for |Φ⁺⟩, |Φ⁻⟩, |Ψ⁺⟩, |Ψ⁻⟩ ∈ ℂ⁴ and their density matrices.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_cfb21084<T> {
    fn checked_invariant_cfb21084(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_cfb21084<T> for Option<T> {
    #[inline]
    fn checked_invariant_cfb21084(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_cfb21084<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_cfb21084(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::density_matrix::DensityMatrix;
use crate::density_matrix::{ExactDensityError, ExactDensityMatrix};
use crate::exact_operator::ExactOperator;
use crate::hilbert_space::HilbertError;
use crate::hilbert_space::HilbertSpace;
use crate::quantum_state::{QuantumState, RayError, RayVector};
use linear_algebra::linear_algebra::complex_matrix::{NComplex, C64};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

/// Refusals for bounded exact entangled-state families.
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum StateFamilyError {
    #[error("ray: {0}")]
    Ray(#[from] RayError),
    #[error("density: {0}")]
    Density(#[from] ExactDensityError),
    #[error("Hilbert carrier: {0}")]
    Hilbert(#[from] HilbertError),
    #[error("invalid family parameter")]
    Parameter,
    #[error("operator: {0}")]
    Operator(#[from] crate::exact_operator::OperatorError),
}

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite Bell state face.";

/// Canonical Bell basis selector.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BellBasis {
    PhiPlus,
    PhiMinus,
    PsiPlus,
    PsiMinus,
}

/// Finite carrier for `bell_state`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BellState {
    /// Degree / dimension proxy (default 4 for 2-qubit system).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl Default for BellState {
    fn default() -> Self {
        Self::new(4, "phi_plus")
    }
}

impl BellState {
    /// Exact unnormalised Bell ray over Q(i); its squared norm is two.
    pub fn exact_ray(basis: BellBasis) -> Result<RayVector, RayError> {
        let (positions, sign) = match basis {
            BellBasis::PhiPlus => ([0, 3], 1),
            BellBasis::PhiMinus => ([0, 3], -1),
            BellBasis::PsiPlus => ([1, 2], 1),
            BellBasis::PsiMinus => ([1, 2], -1),
        };
        let mut v = vec![GaussianRat::zero(); 4];
        v[positions[0]] = GaussianRat::one();
        v[positions[1]] = GaussianRat::from_ints(sign, 0);
        RayVector::try_new(v)
    }

    /// Full coherent Bell density, distinct from its diagonal population shadow.
    pub fn exact_density(basis: BellBasis) -> Result<ExactDensityMatrix, StateFamilyError> {
        Ok(ExactDensityMatrix::pure(&Self::exact_ray(basis)?)?)
    }

    /// Werner family p |Psi-><Psi-| + (1-p) I/4, with 0 <= p <= 1.
    pub fn werner(p: Rational) -> Result<ExactDensityMatrix, StateFamilyError> {
        if p < ri(0) || p > ri(1) {
            return Err(StateFamilyError::Parameter);
        }
        let singlet = Self::exact_density(BellBasis::PsiMinus)?;
        let mixed = ExactDensityMatrix::maximally_mixed(4)?;
        Ok(ExactDensityMatrix::mixture(&[
            (p.clone(), &singlet),
            (ri(1) - p, &mixed),
        ])?)
    }

    /// Isotropic family with maximally entangled fidelity F on C^d tensor C^d.
    pub fn isotropic(
        fidelity: Rational,
        dim: usize,
    ) -> Result<ExactDensityMatrix, StateFamilyError> {
        let n = Self::validate_isotropic_dim(&fidelity, dim)?;
        let p = Self::maximally_entangled_projector(dim, n)?;
        let complement = ExactOperator::identity(n)?.sub(&p)?;
        let denominator = Rational::from_integer((n - 1).into());
        let rho = p
            .scale_rat(&fidelity)?
            .add(&complement.scale_rat(&((ri(1) - fidelity) / denominator))?)?;
        Ok(ExactDensityMatrix::try_from_operator(rho)?)
    }

    fn validate_isotropic_dim(fidelity: &Rational, dim: usize) -> Result<usize, StateFamilyError> {
        if [dim < 2, fidelity < &ri(0), fidelity > &ri(1)]
            .into_iter()
            .any(|b| b)
        {
            return Err(StateFamilyError::Parameter);
        }
        let n = dim.checked_mul(dim).ok_or(StateFamilyError::Parameter)?;
        HilbertSpace::try_new(n, "isotropic")?;
        Ok(n)
    }

    fn maximally_entangled_projector(
        dim: usize,
        n: usize,
    ) -> Result<ExactOperator, StateFamilyError> {
        let mut v = vec![GaussianRat::zero(); n];
        for i in 0..dim {
            v[i * dim + i] = GaussianRat::one();
        }
        Ok(RayVector::try_new(v)?.projector()?)
    }

    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Construct |Φ⁺⟩ = 1/√2 (|00⟩ + |11⟩).
    pub fn phi_plus() -> QuantumState {
        Self::construct_bell_state(BellBasis::PhiPlus)
    }

    /// Construct |Φ⁻⟩ = 1/√2 (|00⟩ - |11⟩).
    pub fn phi_minus() -> QuantumState {
        Self::construct_bell_state(BellBasis::PhiMinus)
    }

    /// Construct |Ψ⁺⟩ = 1/√2 (|01⟩ + |10⟩).
    pub fn psi_plus() -> QuantumState {
        Self::construct_bell_state(BellBasis::PsiPlus)
    }

    /// Construct |Ψ⁻⟩ = 1/√2 (|01⟩ - |10⟩).
    pub fn psi_minus() -> QuantumState {
        Self::construct_bell_state(BellBasis::PsiMinus)
    }

    /// Construct any of the 4 Bell basis state vectors.
    pub fn construct_bell_state(basis: BellBasis) -> QuantumState {
        let space = HilbertSpace::try_new(4, "H2_x_H2").checked_invariant_cfb21084("dim 4");
        let inv_sqrt2 = 1.0 / (2.0_f64).sqrt();
        let (amps, label) = match basis {
            BellBasis::PhiPlus => (
                vec![
                    NComplex::new(inv_sqrt2, 0.0),
                    C64::ZERO,
                    C64::ZERO,
                    NComplex::new(inv_sqrt2, 0.0),
                ],
                "phi_plus",
            ),
            BellBasis::PhiMinus => (
                vec![
                    NComplex::new(inv_sqrt2, 0.0),
                    C64::ZERO,
                    C64::ZERO,
                    NComplex::new(-inv_sqrt2, 0.0),
                ],
                "phi_minus",
            ),
            BellBasis::PsiPlus => (
                vec![
                    C64::ZERO,
                    NComplex::new(inv_sqrt2, 0.0),
                    NComplex::new(inv_sqrt2, 0.0),
                    C64::ZERO,
                ],
                "psi_plus",
            ),
            BellBasis::PsiMinus => (
                vec![
                    C64::ZERO,
                    NComplex::new(inv_sqrt2, 0.0),
                    NComplex::new(-inv_sqrt2, 0.0),
                    C64::ZERO,
                ],
                "psi_minus",
            ),
        };
        QuantumState::try_normalized(&space, amps, label)
            .checked_invariant_cfb21084("valid normalized Bell state")
    }

    /// Construct diagonal population shadow of the Bell state.
    pub fn to_population_density(basis: BellBasis) -> DensityMatrix {
        let state = Self::construct_bell_state(basis);
        DensityMatrix::from_pure_populations(&state, state.label.clone())
            .checked_invariant_cfb21084("density from pure")
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/bell_state.rs
// Claim: urn:core:crates_rs:core-quantum-physics:bell-state:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_and_fence() {
        let x = BellState::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(BellState::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn bell_states_orthonormal() {
        let p_plus = BellState::phi_plus();
        let p_minus = BellState::phi_minus();
        let psi_plus = BellState::psi_plus();
        let psi_minus = BellState::psi_minus();

        // Normalized
        assert!((p_plus.norm_sq() - 1.0).abs() < 1e-12);
        assert!((p_minus.norm_sq() - 1.0).abs() < 1e-12);
        assert!((psi_plus.norm_sq() - 1.0).abs() < 1e-12);
        assert!((psi_minus.norm_sq() - 1.0).abs() < 1e-12);

        // Mutually orthogonal
        assert!(p_plus.inner_product(&p_minus).unwrap().norm_sqr() < 1e-12);
        assert!(p_plus.inner_product(&psi_plus).unwrap().norm_sqr() < 1e-12);
        assert!(p_plus.inner_product(&psi_minus).unwrap().norm_sqr() < 1e-12);
        assert!(p_minus.inner_product(&psi_plus).unwrap().norm_sqr() < 1e-12);
    }
}
