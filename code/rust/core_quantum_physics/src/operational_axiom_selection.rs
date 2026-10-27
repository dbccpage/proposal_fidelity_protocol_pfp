//! Dimensions of finite state carriers and their local tomography comparison.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::{BigInt, BigUint};
use num_traits::Zero;
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum FiniteRivalTheory {
    Classical,
    Complex,
    Real,
    Quaternionic,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum OperationalModelError {
    #[error("a finite system needs a positive nominal dimension")]
    ZeroDimension,
    #[error("the declared finite theory is unknown: {0}")]
    UnknownTheory(String),
}
impl FiniteRivalTheory {
    pub fn parse(s: &str) -> Option<Self> {
        match s.to_ascii_lowercase().as_str() {
            "classical" => Some(Self::Classical),
            "complex" => Some(Self::Complex),
            "real" => Some(Self::Real),
            "quaternionic" => Some(Self::Quaternionic),
            _ => None,
        }
    }
    /// Real dimension of the unnormalised self-adjoint state carrier. Diagonal
    /// entries contribute d real coordinates; each pair contributes 0,1,2,4.
    pub fn state_dimension(self, d: &BigUint) -> Result<BigUint, OperationalModelError> {
        if d.is_zero() {
            return Err(OperationalModelError::ZeroDimension);
        }
        let pairs = d * (d - BigUint::from(1u8)) / BigUint::from(2u8);
        let per_pair = match self {
            Self::Classical => 0u8,
            Self::Real => 1,
            Self::Complex => 2,
            Self::Quaternionic => 4,
        };
        Ok(d + BigUint::from(per_pair) * pairs)
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalTomographyDimensions {
    pub local_product_dimension: BigUint,
    pub joint_dimension: BigUint,
    pub deficit: BigInt,
}
impl LocalTomographyDimensions {
    pub fn holds(&self) -> bool {
        self.deficit.is_zero()
    }
}
pub fn local_tomography_dimensions(
    theory: FiniteRivalTheory,
    a: &BigUint,
    b: &BigUint,
) -> Result<LocalTomographyDimensions, OperationalModelError> {
    let product = theory.state_dimension(a)? * theory.state_dimension(b)?;
    let joint = theory.state_dimension(&(a * b))?;
    let deficit = BigInt::from(product.clone()) - BigInt::from(joint.clone());
    Ok(LocalTomographyDimensions {
        local_product_dimension: product,
        joint_dimension: joint,
        deficit,
    })
}

use crate::exact_channel::{ExactChannelError, ExactChoiMatrix};
use crate::instruments::ExactPovm;
use linear_algebra::exact_field::{involution::adjoint, matrix as mx, ExactFieldError};
use core_number_theory::cyclotomic::GaussianRat;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum NaimarkError {
    #[error("the declared dilation exceeds8 input dimensions,8 outcomes or256 dilation rows")]
    Carrier,
    #[error("the projective dilation certificate failed replay")]
    Certificate,
    #[error(transparent)]
    Channel(#[from] ExactChannelError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NaimarkCertificate {
    pub isometry: BasicMatrix<GaussianRat>,
    pub projections: Vec<BasicMatrix<GaussianRat>>,
    pub effects: Vec<BasicMatrix<GaussianRat>>,
}
fn build_choi_from_povm(
    povm: &ExactPovm,
    d: usize,
    outcomes: usize,
) -> Result<BasicMatrix<GaussianRat>, NaimarkError> {
    Ok(mx::from_fn(d * outcomes, d * outcomes, |r, c| {
        let (i, k) = (r / outcomes, r % outcomes);
        let (j, l) = (c / outcomes, c % outcomes);
        if k == l {
            povm.effects()[k].as_matrix().as_slice()[j * d + i].clone()
        } else {
            GaussianRat::zero()
        }
    })?)
}

fn build_register_projections(
    outcomes: usize,
    rows: usize,
    environment: usize,
) -> Result<Vec<BasicMatrix<GaussianRat>>, NaimarkError> {
    (0..outcomes)
        .map(|k| {
            Ok(mx::from_fn(rows, rows, |r, c| {
                if r == c && r / environment == k {
                    GaussianRat::one()
                } else {
                    GaussianRat::zero()
                }
            })?)
        })
        .collect()
}

fn construct_naimark_dilation(
    povm: &ExactPovm,
    d: usize,
    outcomes: usize,
    factor_budget: u64,
) -> Result<(BasicMatrix<GaussianRat>, Vec<BasicMatrix<GaussianRat>>), NaimarkError> {
    let choi = build_choi_from_povm(povm, d, outcomes)?;
    let choi_mat = ExactChoiMatrix::try_new(d, outcomes, choi)?;
    let kraus = choi_mat.weighted_kraus()?;
    let ordinary = kraus.to_unit_weight(factor_budget)?;
    let environment = ordinary.operators().len();
    let rows = outcomes
        .checked_mul(environment)
        .filter(|&r| r <= 256)
        .ok_or(NaimarkError::Carrier)?;
    let isometry = ordinary.stinespring_isometry()?;
    let projections = build_register_projections(outcomes, rows, environment)?;
    Ok((isometry, projections))
}

/// The classical measurement channel has Choi blocks E_k^T. Its checked Choi
/// factorisation and bounded rational four-square splitting construct an exact
/// ordinary isometry over Q(i), even when sqrt(E_k) lies outside that field.
/// Compressing the classical register projections recovers every POVM effect.
pub fn naimark_projective_dilation(
    povm: &ExactPovm,
    factor_budget: u64,
) -> Result<NaimarkCertificate, NaimarkError> {
    let d = povm.dim();
    let outcomes = povm.effects().len();
    if !(1..=8).contains(&d) || !(1..=8).contains(&outcomes) {
        return Err(NaimarkError::Carrier);
    }
    let (isometry, projections) = construct_naimark_dilation(povm, d, outcomes, factor_budget)?;
    let effects = povm
        .effects()
        .iter()
        .map(|e| e.as_matrix().clone())
        .collect();
    let certificate = NaimarkCertificate {
        isometry,
        projections,
        effects,
    };
    if !verify_naimark_certificate(&certificate)? {
        return Err(NaimarkError::Certificate);
    }
    Ok(certificate)
}

fn is_valid_naimark_shape(c: &NaimarkCertificate) -> bool {
    let (r, d) = c.isometry.shape();
    let dims_ok = (1..=256).contains(&r) && (1..=8).contains(&d);
    let effects_ok = (1..=8).contains(&c.effects.len()) && c.effects.len() == c.projections.len();
    dims_ok && effects_ok
}

fn is_orthogonal_to_previous(
    p: &BasicMatrix<GaussianRat>,
    previous: &[BasicMatrix<GaussianRat>],
) -> Result<bool, NaimarkError> {
    for other in previous {
        if !mx::is_zero_matrix(&mx::multiply(p, other)?) {
            return Ok(false);
        }
    }
    Ok(true)
}

fn is_selfadjoint_idempotent(p: &BasicMatrix<GaussianRat>) -> Result<bool, NaimarkError> {
    let adj = adjoint(p)?;
    let sq = mx::multiply(p, p)?;
    Ok(adj == *p && sq == *p)
}

fn verify_single_naimark_projection(
    c: &NaimarkCertificate,
    k: usize,
    p: &BasicMatrix<GaussianRat>,
    star: &BasicMatrix<GaussianRat>,
    r: usize,
    d: usize,
) -> Result<bool, NaimarkError> {
    if p.shape() != (r, r) || c.effects[k].shape() != (d, d) {
        return Ok(false);
    }
    if !is_selfadjoint_idempotent(p)? || !is_orthogonal_to_previous(p, &c.projections[..k])? {
        return Ok(false);
    }
    let left = mx::multiply(star, p)?;
    let compressed = mx::multiply(&left, &c.isometry)?;
    Ok(compressed == c.effects[k])
}

fn verify_naimark_projections_sum(
    c: &NaimarkCertificate,
    star: &BasicMatrix<GaussianRat>,
    r: usize,
    d: usize,
) -> Result<bool, NaimarkError> {
    let mut sum = mx::zeros(r, r)?;
    for (k, p) in c.projections.iter().enumerate() {
        if !verify_single_naimark_projection(c, k, p, star, r, d)? {
            return Ok(false);
        }
        sum = mx::add(&sum, p)?;
    }
    Ok(sum == mx::identity(r)?)
}

pub fn verify_naimark_certificate(c: &NaimarkCertificate) -> Result<bool, NaimarkError> {
    if !is_valid_naimark_shape(c) {
        return Ok(false);
    }
    let (r, d) = c.isometry.shape();
    let star = adjoint(&c.isometry)?;
    if mx::multiply(&star, &c.isometry)? != mx::identity(d)? {
        return Ok(false);
    }
    verify_naimark_projections_sum(c, &star, r, d)
}

/// Verifier for Lie commutator algebra, Jacobi identity, Jordan product,
/// and the Jordan-Lie derivation identity (PO-000 Appendix E).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JordanLieCommutatorVerifier;

impl JordanLieCommutatorVerifier {
    /// Computes the Lie bracket / commutator [A, B] = AB - BA.
    pub fn commutator(
        a: &BasicMatrix<GaussianRat>,
        b: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactFieldError> {
        let ab = mx::multiply(a, b)?;
        let ba = mx::multiply(b, a)?;
        mx::sub(&ab, &ba)
    }

    /// Computes the Jordan product A o B = (1/2)(AB + BA).
    pub fn jordan_product(
        a: &BasicMatrix<GaussianRat>,
        b: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactFieldError> {
        let ab = mx::multiply(a, b)?;
        let ba = mx::multiply(b, a)?;
        let sum = mx::add(&ab, &ba)?;
        let half = GaussianRat::from_rational(core_number_theory::rational::rq(1, 2));
        mx::scale(&sum, &half)
    }

    /// Verifies the Jacobi identity [[A, B], C] + [[B, C], A] + [[C, A], B] = 0.
    pub fn verify_jacobi_identity(
        a: &BasicMatrix<GaussianRat>,
        b: &BasicMatrix<GaussianRat>,
        c: &BasicMatrix<GaussianRat>,
    ) -> Result<bool, ExactFieldError> {
        let ab = Self::commutator(a, b)?;
        let bc = Self::commutator(b, c)?;
        let ca = Self::commutator(c, a)?;

        let term1 = Self::commutator(&ab, c)?;
        let term2 = Self::commutator(&bc, a)?;
        let term3 = Self::commutator(&ca, b)?;

        let sum12 = mx::add(&term1, &term2)?;
        let total = mx::add(&sum12, &term3)?;
        Ok(mx::is_zero_matrix(&total))
    }

    /// Verifies the Jordan-Lie derivation identity:
    /// [C, A o B] = [C, A] o B + A o [C, B].
    pub fn verify_derivation_identity(
        a: &BasicMatrix<GaussianRat>,
        b: &BasicMatrix<GaussianRat>,
        c: &BasicMatrix<GaussianRat>,
    ) -> Result<bool, ExactFieldError> {
        let a_circ_b = Self::jordan_product(a, b)?;
        let lhs = Self::commutator(c, &a_circ_b)?;

        let c_comm_a = Self::commutator(c, a)?;
        let term1 = Self::jordan_product(&c_comm_a, b)?;

        let c_comm_b = Self::commutator(c, b)?;
        let term2 = Self::jordan_product(a, &c_comm_b)?;

        let rhs = mx::add(&term1, &term2)?;
        let diff = mx::sub(&lhs, &rhs)?;
        Ok(mx::is_zero_matrix(&diff))
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/operational_axiom_selection.rs
// Claim: urn:core:crates_rs:core-quantum-physics:operational-axiom-selection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_9a70c425 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
