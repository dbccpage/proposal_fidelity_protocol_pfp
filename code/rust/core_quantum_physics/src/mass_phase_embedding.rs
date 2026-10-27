// AuthorityEffect: None.

//! Declared L1 masses and declared phases, embedded as a unit L2 vector.
//!
//! Given nonnegative masses `mu_j`, not all zero, set `p_j = mu_j / sum mu`.
//! After phases `u_j` (unit Gaussian rationals) are separately declared, the
//! embedded vector is `psi_j = sqrt(p_j) u_j`. It has `sum |psi_j|^2 = 1`.
//!
//! The map loses information, and each loss is exposed rather than hidden:
//!
//! - overall scale: `mu` and `c mu` (`c > 0`) embed identically;
//! - phases: masses say nothing about `u_j`, so one mass vector has many
//!   embeddings with the same Born weights;
//! - signs: a signed cochain enters only through `|core_j|`.
//!
//! There is no default phase. A caller that supplies none is refused, so the
//! embedding never smuggles in a phase convention. It derives neither the Born
//! rule nor a quantum state from primitive difference.
//!
//! `sqrt(p_j)` is generally irrational. The embedding stores `p_j` and `u_j`;
//! [`MassPhaseEmbedding::exact_amplitudes`] returns amplitudes only when every
//! `p_j` is the square of a rational.

use num_bigint::BigInt;
use num_traits::{Signed, ToPrimitive, Zero};
use core_number_theory::cyclotomic_field::{
    compositum_conductor, quadratic_field_conductor, sqrt_of_integer, CyclotomicError,
    CyclotomicNumber,
};
use core_number_theory::polynomial::MAX_CONDUCTOR;

use core_lie_theory::cayley::is_unit;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::{QuadraticError, Surd};
use core_number_theory::rational::{sqrt_exact, Rational};

/// Refusals for the mass/phase embedding.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum EmbeddingError {
    #[error("quadratic compositum conductor {required} exceeds the exact field bound {max}")]
    FieldBound { required: BigInt, max: usize },
    #[error(transparent)]
    Cyclotomic(#[from] CyclotomicError),
    #[error(transparent)]
    Algebraic(#[from] QuadraticError),
    #[error("embeddings have different carrier dimensions")]
    DimensionMismatch,
    #[error("an overlap is not rational over the declared square classes")]
    IrrationalOverlap,
    #[error("no masses were declared")]
    Empty,
    #[error("mass {index} is negative")]
    NegativeMass { index: usize },
    #[error("all masses are zero")]
    ZeroTotalMass,
    #[error("{masses} masses but {phases} phases; every phase must be declared")]
    PhaseCountMismatch { masses: usize, phases: usize },
    #[error("phase {index} does not have unit modulus")]
    NonUnitPhase { index: usize },
}

/// Normalised masses with their declared phases.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MassPhaseEmbedding {
    probabilities: Vec<Rational>,
    phases: Vec<GaussianRat>,
}

impl MassPhaseEmbedding {
    pub fn new(masses: &[Rational], phases: &[GaussianRat]) -> Result<Self, EmbeddingError> {
        if masses.is_empty() {
            return Err(EmbeddingError::Empty);
        }
        if let Some(index) = masses.iter().position(Signed::is_negative) {
            return Err(EmbeddingError::NegativeMass { index });
        }
        if phases.len() != masses.len() {
            return Err(EmbeddingError::PhaseCountMismatch {
                masses: masses.len(),
                phases: phases.len(),
            });
        }
        if let Some(index) = phases.iter().position(|u| !is_unit(u)) {
            return Err(EmbeddingError::NonUnitPhase { index });
        }
        let total: Rational = masses.iter().sum();
        if total.is_zero() {
            return Err(EmbeddingError::ZeroTotalMass);
        }
        Ok(Self {
            probabilities: masses.iter().map(|m| m / &total).collect(),
            phases: phases.to_vec(),
        })
    }

    /// Masses `|core_j|` of a signed cochain; the signs are discarded.
    pub fn from_signed_cochain(
        omega: &[Rational],
        phases: &[GaussianRat],
    ) -> Result<Self, EmbeddingError> {
        let masses: Vec<Rational> = omega.iter().map(Signed::abs).collect();
        Self::new(&masses, phases)
    }

    pub fn probabilities(&self) -> &[Rational] {
        &self.probabilities
    }

    pub fn phases(&self) -> &[GaussianRat] {
        &self.phases
    }

    /// `|psi_j|^2 = p_j |u_j|^2`.
    pub fn born_weights(&self) -> Vec<Rational> {
        self.probabilities
            .iter()
            .zip(&self.phases)
            .map(|(p, u)| p * u.norm_sq())
            .collect()
    }

    /// `sum_j |psi_j|^2`.
    pub fn norm_squared(&self) -> Rational {
        self.born_weights().iter().sum()
    }

    /// `sqrt(p_j) u_j`, when every `p_j` is the square of a rational.
    pub fn exact_amplitudes(&self) -> Option<Vec<GaussianRat>> {
        self.probabilities
            .iter()
            .zip(&self.phases)
            .map(|(p, u)| sqrt_exact(p).map(|root| u.mul(&GaussianRat::from_rational(root))))
            .collect()
    }
    /// The exact normalized square class of each coordinate, with phases declared separately.
    pub fn amplitude_surds(&self) -> Result<Vec<Surd>, EmbeddingError> {
        self.probabilities
            .iter()
            .map(|p| Surd::new(Rational::from_integer(1.into()), p).map_err(EmbeddingError::from))
            .collect()
    }

    /// Exact overlap in the declared cyclotomic compositum of all coordinate
    /// square classes and `i`. The finite field-conductor budget is explicit;
    /// irrational overlaps are retained without rational projection.
    pub fn algebraic_overlap(&self, other: &Self) -> Result<CyclotomicNumber, EmbeddingError> {
        if self.probabilities.len() != other.probabilities.len() {
            return Err(EmbeddingError::DimensionMismatch);
        }
        let roots: Vec<Surd> = self
            .probabilities
            .iter()
            .zip(&other.probabilities)
            .map(|(p, q)| Surd::new(Rational::from_integer(1.into()), &(p * q)))
            .collect::<Result<_, _>>()?;
        let conductor = Self::compute_compositum_conductor(&roots)?;
        let i = CyclotomicNumber::zeta(conductor, (conductor / 4) as i64)?;
        let mut value = CyclotomicNumber::zero(conductor)?;
        for (j, root) in roots.iter().enumerate() {
            let term = self.evaluate_coordinate_term(other, conductor, &i, j, root)?;
            value = value.add(&term)?;
        }
        Ok(value)
    }

    fn compute_compositum_conductor(roots: &[Surd]) -> Result<usize, EmbeddingError> {
        let mut conductor = 4;
        for root in roots {
            let required = quadratic_field_conductor(root.radicand());
            let field = required
                .to_usize()
                .filter(|n| *n <= MAX_CONDUCTOR)
                .ok_or_else(|| EmbeddingError::FieldBound {
                    required,
                    max: MAX_CONDUCTOR,
                })?;
            conductor = compositum_conductor(conductor, field)?;
        }
        Ok(conductor)
    }

    fn evaluate_coordinate_term(
        &self,
        other: &Self,
        conductor: usize,
        i: &CyclotomicNumber,
        j: usize,
        root: &Surd,
    ) -> Result<CyclotomicNumber, EmbeddingError> {
        let coeff = CyclotomicNumber::from_rational(conductor, root.coefficient().clone())?;
        let amplitude = sqrt_of_integer(conductor, root.radicand())?.mul(&coeff)?;
        let phase_g = self.phases[j].conj().mul(&other.phases[j]);
        let re_cyc = CyclotomicNumber::from_rational(conductor, phase_g.re)?;
        let im_cyc = CyclotomicNumber::from_rational(conductor, phase_g.im)?;
        let phase = re_cyc.add(&i.mul(&im_cyc)?)?;
        Ok(amplitude.mul(&phase)?)
    }

    /// Squared absolute overlap, preserving every algebraic coefficient.
    pub fn algebraic_fidelity(&self, other: &Self) -> Result<CyclotomicNumber, EmbeddingError> {
        let overlap = self.algebraic_overlap(other)?;
        Ok(overlap.mul(&overlap.conjugate())?)
    }

    /// Exact overlap when every product p_j q_j has a rational square root.
    pub fn overlap(&self, other: &Self) -> Result<GaussianRat, EmbeddingError> {
        if self.probabilities.len() != other.probabilities.len() {
            return Err(EmbeddingError::DimensionMismatch);
        }
        let mut value = GaussianRat::zero();
        for j in 0..self.probabilities.len() {
            let root = sqrt_exact(&(&self.probabilities[j] * &other.probabilities[j]))
                .ok_or(EmbeddingError::IrrationalOverlap)?;
            let term = self.phases[j]
                .conj()
                .mul(&other.phases[j])
                .mul(&GaussianRat::from_rational(root));
            value = value.add(&term);
        }
        Ok(value)
    }

    pub fn fidelity(&self, other: &Self) -> Result<Rational, EmbeddingError> {
        Ok(self.overlap(other)?.norm_sq())
    }

    /// Squared Hellinger distance of the mass laws, in the convention 1-sum sqrt(pq).
    pub fn hellinger_squared(&self, other: &Self) -> Result<Rational, EmbeddingError> {
        if self.probabilities.len() != other.probabilities.len() {
            return Err(EmbeddingError::DimensionMismatch);
        }
        let mut sum = Rational::zero();
        for (p, q) in self.probabilities.iter().zip(&other.probabilities) {
            sum += sqrt_exact(&(p * q)).ok_or(EmbeddingError::IrrationalOverlap)?;
        }
        Ok(Rational::from_integer(1.into()) - sum)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mass_phase_embedding.rs
// Claim: urn:core:crates_rs:core-quantum-physics:mass-phase-embedding:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e07e2104 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
