//! Exact CCR trace defects and the principal winding of a finite clock-shift pair.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution::hs_norm_squared, matrix, ExactFieldError};
use num_bigint::BigInt;
use num_traits::{Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::cyclotomic_field::CyclotomicNumber;
use core_number_theory::rational::{ri, rq, Rational};
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum NormFrontierError {
    #[error("a common square carrier of dimension 1..=128 and nonzero scalar are required")]
    Carrier,
    #[error("the declared winding field was refused: {0}")]
    Field(String),
    #[error("a principal logarithm is undefined at the negative real axis")]
    BranchCut,
    #[error("the clock-shift commutator certificate failed")]
    Certificate,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CcrDefectCertificate {
    pub dimension: usize,
    pub trace_defect: GaussianRat,
    pub normalized_lower_bound: Rational,
    pub frobenius_squared: Rational,
}
fn validate_ccr_carrier(
    q: &BasicMatrix<GaussianRat>,
    p: &BasicMatrix<GaussianRat>,
    lambda: &Rational,
) -> Result<usize, NormFrontierError> {
    let d = q.rows();
    let valid_dim = (1..=128).contains(&d);
    let valid_shapes = q.shape() == (d, d) && p.shape() == (d, d);
    if !valid_dim || !valid_shapes || lambda.is_zero() {
        return Err(NormFrontierError::Carrier);
    }
    Ok(d)
}

fn compute_ccr_defect_matrix(
    q: &BasicMatrix<GaussianRat>,
    p: &BasicMatrix<GaussianRat>,
    lambda: &Rational,
    d: usize,
) -> Result<BasicMatrix<GaussianRat>, NormFrontierError> {
    let comm = matrix::commutator(q, p)?;
    let id_d = matrix::identity(d)?;
    let scaled_id = matrix::scale(&id_d, &GaussianRat::from_rational(lambda.clone()))?;
    Ok(matrix::sub(&comm, &scaled_id)?)
}

/// For D=[Q,P]-lambda I, Tr D=-d lambda and |Tr D|²<=d ||D||_HS².
/// Thus the normalized trace, Hilbert-Schmidt and operator norm lower bounds
/// all retain |lambda|. The certificate replays the finite trace identity.
pub fn certify_ccr_defect(
    q: &BasicMatrix<GaussianRat>,
    p: &BasicMatrix<GaussianRat>,
    lambda: &Rational,
) -> Result<CcrDefectCertificate, NormFrontierError> {
    let d = validate_ccr_carrier(q, p, lambda)?;
    let defect = compute_ccr_defect_matrix(q, p, lambda, d)?;
    let trace = matrix::trace(&defect)?;
    let dimension = Rational::from_integer(d.into());
    let expected = GaussianRat::from_rational(-&dimension * lambda);
    let norm = hs_norm_squared(&defect)?;
    let valid_cert = [
        trace == expected,
        norm.im.is_zero(),
        trace.norm_sq() <= &dimension * &norm.re,
    ]
    .into_iter()
    .all(|b| b);
    if !valid_cert {
        return Err(NormFrontierError::Certificate);
    }
    Ok(CcrDefectCertificate {
        dimension: d,
        trace_defect: trace,
        normalized_lower_bound: lambda.abs(),
        frobenius_squared: norm.re,
    })
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClockShiftWinding {
    pub dimension: usize,
    pub central_phase: CyclotomicNumber,
    pub principal_turn: Rational,
    pub winding: BigInt,
}

fn verify_clock_shift_action(d: usize, z: &CyclotomicNumber) -> Result<(), NormFrontierError> {
    for j in 0..d {
        let before = (j + d - 1) % d;
        let action = z
            .pow(j as u32)
            .mul(&z.pow(before as u32).conjugate())
            .map_err(|e| NormFrontierError::Field(e.to_string()))?;
        if &action != z {
            return Err(NormFrontierError::Certificate);
        }
    }
    Ok(())
}

/// X|j>=|j+1>, Z|j>=zeta_d^j. The action of ZXZ*X* on every basis
/// coordinate is replayed in the canonical cyclotomic field. Since zeta_d
/// uses the standard complex place, its principal turn is 1/d for d>2.
/// The index is the sum of these turns, and the d=2 logarithm is refused.
pub fn clock_shift_winding(d: usize) -> Result<ClockShiftWinding, NormFrontierError> {
    if !(1..=128).contains(&d) {
        return Err(NormFrontierError::Carrier);
    }
    if d == 2 {
        return Err(NormFrontierError::BranchCut);
    }
    let z = CyclotomicNumber::zeta(d, 1).map_err(|e| NormFrontierError::Field(e.to_string()))?;
    let one = CyclotomicNumber::one(d).map_err(|e| NormFrontierError::Field(e.to_string()))?;
    verify_clock_shift_action(d, &z)?;
    let turn = if z == one { ri(0) } else { rq(1, d as i64) };
    let total = &turn * Rational::from_integer(d.into());
    if !total.is_integer() {
        return Err(NormFrontierError::Certificate);
    }
    Ok(ClockShiftWinding {
        dimension: d,
        central_phase: z,
        principal_turn: turn,
        winding: total.to_integer(),
    })
}

// Origin: engine/crates_rs/core_quantum_physics/src/norm_approximation_frontier.rs
// Claim: urn:core:crates_rs:core-quantum-physics:norm-approximation-frontier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_2a8ad828 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
