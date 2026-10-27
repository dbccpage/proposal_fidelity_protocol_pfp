//! Shared exact quotient-L1 optimization and independent functional replay.
//!
//! The solver proposes primal/dual witnesses. core_functional alone verifies
//! feasibility, dual circulation, capacities and zero duality gap. A pivot budget
//! bounds search and exhaustion is a typed refusal. AuthorityEffect: None.

use crate::solver_lp_exact_simplex::{solve_weighted_l1_projection, L1LpError};
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional};
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional, VerifiedExactPhi1};
use core_policy::trichotomy::{classify_exact, ObstructionDiagnosticClass, TrichotomyOutcome};

/// Dense exact simplex and quotient replay are supported on these finite axes.
pub const MAX_COCHAIN_DIMENSION: usize = 256;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CertifiedPhi1Error {
    #[error("cochain dimensions ({c0}, {c1}) exceed the finite limit {maximum}")]
    SizeLimit {
        c0: usize,
        c1: usize,
        maximum: usize,
    },
    #[error("a rational input has a zero denominator")]
    InvalidRational,
    #[error("map, cochain and weight shapes differ")]
    Shape,
    #[error("weight {edge} is not positive")]
    NonPositiveWeight { edge: usize },
    #[error(transparent)]
    Solver(#[from] L1LpError),
    #[error("independent exact replay refused: {0}")]
    Replay(String),
}

fn check_carrier(c0: usize, c1: usize) -> Result<(), CertifiedPhi1Error> {
    if c0 > MAX_COCHAIN_DIMENSION || c1 > MAX_COCHAIN_DIMENSION {
        return Err(CertifiedPhi1Error::SizeLimit {
            c0,
            c1,
            maximum: MAX_COCHAIN_DIMENSION,
        });
    }
    Ok(())
}

pub fn certified_phi1(
    c0: usize,
    d0: &[Vec<BigRational>],
    x: &[BigRational],
    weights: &[BigRational],
    pivot_budget: usize,
) -> Result<VerifiedExactPhi1, CertifiedPhi1Error> {
    check_carrier(c0, x.len())?;
    if d0.len() != x.len() || weights.len() != x.len() || d0.iter().any(|r| r.len() != c0) {
        return Err(CertifiedPhi1Error::Shape);
    }
    if d0
        .iter()
        .flatten()
        .chain(x)
        .chain(weights)
        .any(|q| q.denom().is_zero())
    {
        return Err(CertifiedPhi1Error::InvalidRational);
    }
    if let Some(edge) = weights.iter().position(|w| !w.is_positive()) {
        return Err(CertifiedPhi1Error::NonPositiveWeight { edge });
    }
    let (alpha, residual, dual, value) = if x.is_empty() {
        (
            vec![BigRational::zero(); c0],
            vec![],
            vec![],
            BigRational::zero(),
        )
    } else {
        let proposed = solve_weighted_l1_projection(x, weights, d0, pivot_budget)?;
        (
            proposed.coefficients,
            proposed.residual,
            proposed.dual,
            proposed.value,
        )
    };
    Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
        omega: x.to_vec(),
        d0: d0.to_vec(),
        weights: weights.to_vec(),
        alpha,
        primal_residual: residual,
        dual_witness: dual,
        reported_value: value,
    })
    .map_err(|e| CertifiedPhi1Error::Replay(e.to_string()))
}

fn classify(
    c0: usize,
    d0: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
    x: &[BigRational],
    weights: &[BigRational],
    budget: usize,
) -> Result<ObstructionDiagnosticClass, CertifiedPhi1Error> {
    let phi = certified_phi1(c0, d0, x, weights, budget)?;
    let complex = ExactCochainComplexQ::try_new(c0, x.len(), d1.len(), d0.to_vec(), d1.to_vec())
        .map_err(|e| CertifiedPhi1Error::Replay(e.to_string()))?;
    let residual = DegreeOneResidualQ::try_new(&complex, phi.primal_residual().to_vec())
        .map_err(|e| CertifiedPhi1Error::Replay(e.to_string()))?;
    let gamma = Gamma2Functional::try_compute_exact_quotient(&residual)
        .map_err(|e| CertifiedPhi1Error::Replay(e.to_string()))?;
    match classify_exact(&phi, &gamma) {
        TrichotomyOutcome::Classified(result) => Ok(result.diagnostic_class()),
        TrichotomyOutcome::TriRefused(reason) => {
            Err(CertifiedPhi1Error::Replay(format!("{reason:?}")))
        }
    }
}

/// Equal orientation-blind local masses with unequal independently verified classes.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LocalGreenGlobalRed {
    pub first_class: ObstructionDiagnosticClass,
    pub second_class: ObstructionDiagnosticClass,
}

fn validate_lggr_inputs(
    c0: usize,
    d0: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
    weights: &[BigRational],
    x: &[BigRational],
    y: &[BigRational],
) -> Result<(), CertifiedPhi1Error> {
    check_carrier(c0, x.len())?;
    check_carrier(c0, d1.len())?;
    let lengths_ok = [
        x.len() == y.len(),
        x.len() == d0.len(),
        weights.len() == x.len(),
        d1.iter().all(|row| row.len() == x.len()),
        d0.iter().all(|row| row.len() == c0),
    ]
    .into_iter()
    .all(|b| b);
    if !lengths_ok {
        return Err(CertifiedPhi1Error::Shape);
    }
    if d0
        .iter()
        .flatten()
        .chain(d1.iter().flatten())
        .chain(x)
        .chain(weights)
        .chain(y)
        .any(|q| q.denom().is_zero())
    {
        return Err(CertifiedPhi1Error::InvalidRational);
    }
    Ok(())
}

pub fn lggr_cochain_witness(
    c0: usize,
    d0: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
    weights: &[BigRational],
    x: &[BigRational],
    y: &[BigRational],
    pivot_budget: usize,
) -> Result<Option<LocalGreenGlobalRed>, CertifiedPhi1Error> {
    validate_lggr_inputs(c0, d0, d1, weights, x, y)?;
    if x.iter().zip(y).any(|(a, b)| a.abs() != b.abs()) {
        return Ok(None);
    }
    let first_class = classify(c0, d0, d1, x, weights, pivot_budget)?;
    let second_class = classify(c0, d0, d1, y, weights, pivot_budget)?;
    Ok(
        (first_class != second_class).then_some(LocalGreenGlobalRed {
            first_class,
            second_class,
        }),
    )
}

// Origin: engine/crates_rs/core_solvers/src/solver_cohomology_quotient_phi1.rs
// Claim: urn:core:crates_rs:core-solvers:solver-cohomology-quotient-phi1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(n))
    }

    #[test]
    fn triangle_quotient_mass_and_dual_circulation_are_replayed() {
        let d0 = vec![
            vec![q(-1), q(1), q(0)],
            vec![q(0), q(-1), q(1)],
            vec![q(1), q(0), q(-1)],
        ];
        let x = vec![q(1), q(1), q(1)];
        let verified = certified_phi1(3, &d0, &x, &vec![q(1); 3], 100).unwrap();
        assert_eq!(verified.value(), &q(3));
        assert_eq!(
            verified
                .primal_residual()
                .iter()
                .map(|v| v.abs())
                .sum::<BigRational>(),
            q(3)
        );
        let exact = certified_phi1(3, &d0, &[q(2), q(-1), q(-1)], &vec![q(1); 3], 100).unwrap();
        assert!(exact.value().is_zero());
    }

    #[test]
    fn local_absolute_values_do_not_determine_the_quotient_class() {
        let d0 = vec![vec![q(1)], vec![q(1)]];
        let witness = lggr_cochain_witness(
            1,
            &d0,
            &[],
            &[q(1), q(1)],
            &[q(1), q(1)],
            &[q(1), q(-1)],
            100,
        )
        .unwrap()
        .unwrap();
        assert_eq!(witness.first_class, ObstructionDiagnosticClass::ExactRepair);
        assert_eq!(
            witness.second_class,
            ObstructionDiagnosticClass::ClosedResidual
        );
    }

    #[test]
    fn malformed_weights_and_budget_exhaustion_cannot_be_certified() {
        assert_eq!(
            certified_phi1(1, &[vec![q(1)]], &[q(1)], &[], 100),
            Err(CertifiedPhi1Error::Shape)
        );
        assert!(matches!(
            certified_phi1(1, &[vec![q(1)]], &[q(1)], &[q(0)], 100),
            Err(CertifiedPhi1Error::NonPositiveWeight { .. })
        ));
        assert!(matches!(
            certified_phi1(1, &[vec![q(1)]], &[q(1)], &[q(1)], 0),
            Err(CertifiedPhi1Error::Solver(
                L1LpError::IterationBudgetExceeded { .. }
            ))
        ));
    }

    #[test]
    fn empty_cochains_keep_zero_value_and_refuse_unbounded_zero_axes() {
        for c0 in [0, 2, MAX_COCHAIN_DIMENSION] {
            let certificate = certified_phi1(c0, &[], &[], &[], 0).unwrap();
            assert!(certificate.value().is_zero());
            assert!(certificate.primal_residual().is_empty());
        }
        assert!(matches!(
            certified_phi1(usize::MAX, &[], &[], &[], 0),
            Err(CertifiedPhi1Error::SizeLimit { .. })
        ));
        assert!(matches!(
            lggr_cochain_witness(usize::MAX, &[], &[], &[], &[], &[], 0),
            Err(CertifiedPhi1Error::SizeLimit { .. })
        ));
        let bad = BigRational::new_raw(BigInt::from(1), BigInt::from(0));
        assert_eq!(
            certified_phi1(1, &[vec![q(1)]], &[bad], &[q(1)], 1),
            Err(CertifiedPhi1Error::InvalidRational)
        );
    }
}
