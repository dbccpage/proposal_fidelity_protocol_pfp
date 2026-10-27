//! Canonical finite exact MUB systems and Wootters–Fields linear inversion.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_f0237f04;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_f0237f04<T> = std::result::Result<T, BoundaryError_f0237f04>;
pub mod algebra;
pub mod carrier;
pub mod char_two;
pub mod char_two_weyl_board;
pub mod composite;
pub mod composite_completion_gate;
pub mod odd_prime;
pub mod odd_prime_power_controls;
pub mod odd_prime_power_weyl;
pub mod prime_controls;
pub mod odd_prime_weyl;
pub mod odd_prime_gauss_certificate_gate;
pub mod odd_prime_power_field_theorem_gate;
pub mod odd_prime_power_parametric_gate;
pub mod projector_algebra;
pub mod spectral_lift;
pub mod hilbert_transport;
pub mod gtmur_projector_ledger;
pub mod d10_controls;
pub mod finite_projector_control;
pub mod dimension_stratification;
pub mod composite_controls;
pub mod composite_tensor_family_gate;
pub mod prime_power_gtmur_boundary;
pub mod non_cyclic_falser;
use algebra::{verify_mub_projector_algebra, ProjectorAlgebraReport, ProjectorAlgebraStatus};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    involution::{adjoint, Involution},
    matrix,
};
use core_number_theory::cyclotomic::Cyc24;
use core_number_theory::rational::{rq, Rational};
use core_number_theory::scalar::RationalEmbedding;
use serde::{Deserialize, Serialize};
/// Error returned when linear inversion state tomography cannot be performed.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum MubTomographyError {
    /// Full state tomography requires a complete MUB system with d + 1 bases.
    IncompleteBasisSystem {
        dimension: usize,
        bases_count: usize,
        expected: usize,
    },
    /// The number of probability distributions does not match the number of bases.
    BasisCountMismatch {
        bases_count: usize,
        probs_count: usize,
    },
    /// Outcome count in a basis does not match state dimension d.
    OutcomeCountMismatch {
        basis_index: usize,
        dimension: usize,
        outcomes_count: usize,
    },
}

impl std::fmt::Display for MubTomographyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::IncompleteBasisSystem {
                dimension,
                bases_count,
                expected,
            } => {
                write!(
                    f,
                    "Incomplete basis system: full-state tomography in d={} requires {} bases, got {}",
                    dimension, expected, bases_count
                )
            }
            Self::BasisCountMismatch {
                bases_count,
                probs_count,
            } => {
                write!(
                    f,
                    "Basis count mismatch: MUB system has {} bases, but received {} probability vectors",
                    bases_count, probs_count
                )
            }
            Self::OutcomeCountMismatch {
                basis_index,
                dimension,
                outcomes_count,
            } => {
                write!(
                    f,
                    "Outcome count mismatch: basis {} has {} outcomes, expected dimension {}",
                    basis_index, outcomes_count, dimension
                )
            }
        }
    }
}

impl std::error::Error for MubTomographyError {}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MubSystem<C: RationalEmbedding + Involution> {
    pub dimension: usize,
    pub bases: Vec<Vec<BasicMatrix<C>>>,
}
impl<C: RationalEmbedding + Involution> MubSystem<C> {
    /// A declaration; it carries no certificate until its laws are checked.
    pub fn new(dimension: usize, bases: Vec<Vec<BasicMatrix<C>>>) -> Self {
        Self { dimension, bases }
    }
    pub fn try_new(dimension: usize, bases: Vec<Vec<BasicMatrix<C>>>) -> Result<Self, String> {
        let s = Self::new(dimension, bases);
        let r = s.verify_projector_algebra();
        if r.status != ProjectorAlgebraStatus::AlgebraVerified {
            return Err(r
                .error
                .unwrap_or_else(|| "invalid projector algebra".into()));
        }
        Ok(s)
    }
    fn shape_is_valid(&self) -> bool {
        self.dimension > 0
            && self.dimension <= 64
            && !self.bases.is_empty()
            && self.bases.len() <= self.dimension + 1
            && self.bases.iter().all(|b| {
                b.len() == self.dimension
                    && b.iter()
                        .all(|p| p.shape() == (self.dimension, self.dimension))
            })
    }
    pub fn is_complete(&self) -> bool {
        self.shape_is_valid() && self.bases.len() == self.dimension + 1
    }
    pub fn basis_count(&self) -> usize {
        self.bases.len()
    }
    pub fn try_projector(&self, b: usize, k: usize) -> Result<&BasicMatrix<C>, String> {
        if !self.shape_is_valid() {
            return Err("malformed projector carrier".into());
        }
        self.bases
            .get(b)
            .and_then(|row| row.get(k))
            .ok_or_else(|| "projector index outside the carrier".into())
    }
    pub fn verify_projector_algebra(&self) -> ProjectorAlgebraReport {
        verify_mub_projector_algebra(&self.bases, self.dimension)
    }
    pub fn verify_idempotence(&self) -> bool {
        self.shape_is_valid()
            && self
                .bases
                .iter()
                .flatten()
                .all(|p| matrix::multiply(p, p).is_ok_and(|m| m == *p))
    }
    pub fn verify_hermiticity(&self) -> bool {
        self.shape_is_valid()
            && self
                .bases
                .iter()
                .flatten()
                .all(|p| adjoint(p).is_ok_and(|m| m == *p))
    }
    pub fn verify_rank_one_trace(&self) -> bool {
        self.shape_is_valid()
            && self.bases.iter().flatten().all(|p| {
                matrix::trace(p) == Ok(C::one())
                    && linear_algebra::exact_field::elimination::rank(p) == Ok(1)
            })
    }
    pub fn verify_same_basis_orthogonality(&self) -> bool {
        self.shape_is_valid()
            && self.bases.iter().all(|b| {
                (0..self.dimension).all(|j| {
                    (0..self.dimension).all(|k| {
                        j == k
                            || matrix::multiply(&b[j], &b[k])
                                .is_ok_and(|m| matrix::is_zero_matrix(&m))
                    })
                })
            })
    }
    pub fn verify_resolution_of_identity(&self) -> bool {
        if !self.shape_is_valid() {
            return false;
        }
        self.bases.iter().all(|b| {
            let Ok(mut sum) = matrix::zeros(self.dimension, self.dimension) else {
                return false;
            };
            for p in b {
                let Ok(next) = matrix::add(&sum, p) else {
                    return false;
                };
                sum = next;
            }
            matrix::is_identity_matrix(&sum) == Ok(true)
        })
    }
    pub fn verify_cross_basis_unbiasedness(&self) -> bool {
        if !self.shape_is_valid() {
            return false;
        }
        let overlap = C::from_rational(&rq(1, self.dimension as i64));
        (0..self.bases.len()).all(|b| {
            (b + 1..self.bases.len()).all(|c| {
                self.bases[b].iter().all(|p| {
                    self.bases[c].iter().all(|q| {
                        matrix::multiply(p, q).and_then(|m| matrix::trace(&m))
                            == Ok(overlap.clone())
                    })
                })
            })
        })
    }
    /// Measurements of an operator. State admission is a separate positivity check.
    pub fn try_measure_state(&self, rho: &BasicMatrix<C>) -> Result<Vec<Vec<C>>, String> {
        if !self.shape_is_valid() || rho.shape() != (self.dimension, self.dimension) {
            return Err("operator or projector carrier has the wrong shape".into());
        }
        self.bases
            .iter()
            .map(|b| {
                b.iter()
                    .map(|p| {
                        matrix::multiply(rho, p)
                            .and_then(|m| matrix::trace(&m))
                            .map_err(|e| e.to_string())
                    })
                    .collect()
            })
            .collect()
    }
    pub fn try_reconstruct_state(
        &self,
        probabilities: &[Vec<C>],
    ) -> Result<BasicMatrix<C>, String> {
        self.validate_reconstruction_inputs(probabilities)?;
        let mut sum = matrix::zeros(self.dimension, self.dimension).map_err(|e| e.to_string())?;
        for (b, ps) in self.bases.iter().zip(probabilities) {
            for (p, w) in b.iter().zip(ps) {
                let term = matrix::scale(p, w).map_err(|e| e.to_string())?;
                sum = matrix::add(&sum, &term).map_err(|e| e.to_string())?;
            }
        }
        matrix::sub(
            &sum,
            &matrix::identity(self.dimension).map_err(|e| e.to_string())?,
        )
        .map_err(|e| e.to_string())
    }

    fn validate_reconstruction_inputs(&self, probabilities: &[Vec<C>]) -> Result<(), String> {
        if !self.shape_is_valid() {
            return Err("malformed projector carrier".into());
        }
        if !self.is_complete() {
            return Err("full linear inversion requires an admitted complete MUB carrier".into());
        }
        if self.verify_projector_algebra().status != ProjectorAlgebraStatus::AlgebraVerified {
            return Err("invalid projector algebra".into());
        }
        if probabilities.len() != self.bases.len()
            || probabilities.iter().any(|p| p.len() != self.dimension)
        {
            return Err("probability shape does not match the complete MUB carrier".into());
        }
        Ok(())
    }

    pub fn verify_exact_reconstruction(&self, rho: &BasicMatrix<C>) -> bool {
        self.try_measure_state(rho)
            .and_then(|p| self.try_reconstruct_state(&p))
            .is_ok_and(|m| m == *rho)
    }
    pub fn verify_two_design_with_budget(&self, entry_budget: usize) -> Result<bool, String> {
        if !self.is_complete()
            || self.verify_projector_algebra().status != ProjectorAlgebraStatus::AlgebraVerified
        {
            return Err("a complete admitted MUB carrier is required".into());
        }
        let d = self.dimension;
        let count = d
            .checked_pow(4)
            .and_then(|n| n.checked_mul(d * (d + 1)))
            .ok_or("two-design budget overflow")?;
        if count > entry_budget {
            return Err("two-design replay exceeds the declared entry budget".into());
        }
        let mut sum = matrix::zeros(d * d, d * d).map_err(|e| e.to_string())?;
        for p in self.bases.iter().flatten() {
            let kron = matrix::kronecker(p, p).map_err(|e| e.to_string())?;
            sum = matrix::add(&sum, &kron).map_err(|e| e.to_string())?;
        }
        let expected = self.build_two_design_expected()?;
        Ok(sum == expected)
    }

    fn build_two_design_expected(&self) -> Result<BasicMatrix<C>, String> {
        let d = self.dimension;
        let mut expected = matrix::identity::<C>(d * d).map_err(|e| e.to_string())?;
        for i in 0..d {
            for j in 0..d {
                let old = expected
                    .get(i * d + j, j * d + i)
                    .map_err(|e| e.to_string())?;
                expected
                    .set(i * d + j, j * d + i, old.add(&C::one()))
                    .map_err(|e| e.to_string())?;
            }
        }
        Ok(expected)
    }
    pub fn verify_two_design(&self) -> bool {
        self.verify_two_design_with_budget(100_000_000) == Ok(true)
    }
    pub fn purity_from_probabilities(&self, ps: &[Vec<C>]) -> Result<C, String> {
        let rho = self.try_reconstruct_state(ps)?;
        let one = C::one();
        if adjoint(&rho).map_err(|e| e.to_string())? != rho
            || matrix::trace(&rho).map_err(|e| e.to_string())? != one
            || ps
                .iter()
                .any(|row| row.iter().fold(C::zero(), |s, p| s.add(p)) != one)
        {
            return Err("a trace-one Hermitian inversion with normalized rows is required".into());
        }
        let purity = ps
            .iter()
            .flatten()
            .fold(C::zero(), |s, p| s.add(&p.mul(p)))
            .sub(&one);
        if matrix::trace(&matrix::multiply(&rho, &rho).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?
            != purity
        {
            return Err("purity identity failed".into());
        }
        Ok(purity)
    }
    pub fn deterministic_valuation_purity(&self, outcomes: &[usize]) -> Result<C, String> {
        if !self.is_complete()
            || outcomes.len() != self.bases.len()
            || outcomes.iter().any(|&k| k >= self.dimension)
        {
            return Err("deterministic outcomes do not match the complete carrier".into());
        }
        let mut ps = vec![vec![C::zero(); self.dimension]; self.bases.len()];
        for (i, &k) in outcomes.iter().enumerate() {
            ps[i][k] = C::one();
        }
        self.purity_from_probabilities(&ps)
    }
}
impl MubSystem<Cyc24> {
    pub fn for_dimension(d: usize) -> Option<Self> {
        match d {
            2 => Some(Self::mub_d2()),
            3 => Some(Self::mub_d3()),
            4 => Some(Self::mub_d4()),
            6 => Some(Self::mub_d6()),
            _ => None,
        }
    }
    pub fn mub_d2() -> Self {
        Self::new(2, char_two::build_char_two_mub_d2())
    }
    pub fn mub_d3() -> Self {
        Self::new(3, odd_prime::build_odd_prime_mub_d3())
    }
    pub fn mub_d4() -> Self {
        Self::new(4, char_two::build_char_two_mub_d4())
    }
    pub fn mub_d6() -> Self {
        Self::new(6, composite::build_composite_mub_d6())
    }
    pub fn try_measure_state_rational(
        &self,
        rho: &BasicMatrix<Cyc24>,
    ) -> Result<Vec<Vec<Rational>>, String> {
        self.try_measure_state(rho)?
            .iter()
            .map(|b| {
                b.iter()
                    .map(|p| {
                        p.as_rational().ok_or_else(|| {
                            "the exact Born trace is nonrational; use field-valued measurements"
                                .into()
                        })
                    })
                    .collect()
            })
            .collect()
    }
    pub fn try_reconstruct_state_rational(
        &self,
        ps: &[Vec<Rational>],
    ) -> Result<BasicMatrix<Cyc24>, String> {
        let ps = ps
            .iter()
            .map(|row| row.iter().cloned().map(Cyc24::rat).collect())
            .collect::<Vec<_>>();
        self.try_reconstruct_state(&ps)
    }
    pub fn verify_clifton_kent_purity_obstruction(&self) -> bool {
        self.dimension > 1
            && self.deterministic_valuation_purity(&vec![0; self.bases.len()])
                == Ok(Cyc24::rat(rq(self.dimension as i64, 1)))
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/mub.rs
// Claim: urn:core:crates_rs:core-quantum-physics:mub:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mub_system_d2_verification() {
        let sys = MubSystem::mub_d2();
        let report = sys.verify_projector_algebra();
        assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
        assert_eq!(report.basis_count, 3);
        assert_eq!(report.dimension, 2);
    }

    #[test]
    fn test_mub_system_d3_verification() {
        let sys = MubSystem::mub_d3();
        let report = sys.verify_projector_algebra();
        assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
        assert_eq!(report.basis_count, 4);
        assert_eq!(report.dimension, 3);
    }

    #[test]
    fn test_mub_system_d4_verification() {
        let sys = MubSystem::mub_d4();
        let report = sys.verify_projector_algebra();
        assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
        assert_eq!(report.basis_count, 5);
        assert_eq!(report.dimension, 4);
    }

    #[test]
    fn test_mub_system_d6_composite_verification() {
        let sys = MubSystem::mub_d6();
        let report = sys.verify_projector_algebra();
        assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
        assert_eq!(report.basis_count, 3);
        assert_eq!(report.dimension, 6);
    }

    #[test]
    fn test_mub_d3_all_projector_laws() {
        let mub = MubSystem::mub_d3();
        assert!(mub.verify_hermiticity());
        assert!(mub.verify_idempotence());
        assert!(mub.verify_rank_one_trace());
        assert!(mub.verify_same_basis_orthogonality());
        assert!(mub.verify_resolution_of_identity());
        assert!(mub.verify_cross_basis_unbiasedness());
    }

    #[test]
    fn test_mub_d4_all_projector_laws() {
        let mub4 = MubSystem::mub_d4();
        assert!(mub4.verify_hermiticity());
        assert!(mub4.verify_idempotence());
        assert!(mub4.verify_rank_one_trace());
        assert!(mub4.verify_same_basis_orthogonality());
        assert!(mub4.verify_resolution_of_identity());
        assert!(mub4.verify_cross_basis_unbiasedness());
        assert!(mub4.verify_clifton_kent_purity_obstruction());
    }

    #[test]
    fn test_mub_d6_completeness_and_reconstruction_rejection() {
        let sys = MubSystem::mub_d6();
        assert_eq!(sys.dimension, 6);
        assert_eq!(sys.bases.len(), 3);
        assert!(!sys.is_complete());

        let rho_mixed = matrix::scale(
            &matrix::identity::<Cyc24>(6).unwrap(),
            &Cyc24::rat(rq(1, 6)),
        )
        .unwrap();
        assert!(!sys.verify_exact_reconstruction(&rho_mixed));

        let probs = sys.try_measure_state_rational(&rho_mixed).unwrap();
        assert!(sys.try_reconstruct_state_rational(&probs).is_err());

        let probs_c = sys.try_measure_state(&rho_mixed).unwrap();
        assert!(sys.try_reconstruct_state(&probs_c).is_err());
    }

    #[test]
    fn test_mub_d6_reconstruction_refuses_incomplete_system() {
        let sys = MubSystem::mub_d6();
        let rho_mixed = matrix::scale(
            &matrix::identity::<Cyc24>(6).unwrap(),
            &Cyc24::rat(rq(1, 6)),
        )
        .unwrap();
        let probs = sys.try_measure_state(&rho_mixed).unwrap();
        assert!(sys.try_reconstruct_state(&probs).is_err());
    }

    #[test]
    fn test_mub_d6_rational_reconstruction_refuses_incomplete_system() {
        let sys = MubSystem::mub_d6();
        let rho_mixed = matrix::scale(
            &matrix::identity::<Cyc24>(6).unwrap(),
            &Cyc24::rat(rq(1, 6)),
        )
        .unwrap();
        let probs = sys.try_measure_state_rational(&rho_mixed).unwrap();
        assert!(sys.try_reconstruct_state_rational(&probs).is_err());
    }
}
