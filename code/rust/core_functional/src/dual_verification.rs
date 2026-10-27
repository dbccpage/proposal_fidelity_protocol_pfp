//! Exact unweighted L1 dual feasibility and pairing, not primal optimality.
//!
//! A boundary-annihilating vector of infinity norm at most one proves a lower
//! bound on inf_alpha ||h - B alpha||_1. Equality with a submitted scalar does
//! NOT prove equality with the infimum. Full Phi1 verification separately needs
//! a matching primal witness. These immutable results grant no actor authority.
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum RationalLocation {
    Boundary { row: usize, column: usize },
    Dual { index: usize },
    Residual { index: usize },
    ClaimedValue,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DualVerificationError {
    #[error("DUAL_EMPTY_INPUT")]
    EmptyInput,
    #[error("DUAL_DIMENSION_MISMATCH")]
    DimensionMismatch,
    #[error("DUAL_BOUNDARY_ROW_MISMATCH: expected {expected}, observed {actual}")]
    BoundaryRowMismatch { expected: usize, actual: usize },
    #[error("DUAL_RAGGED_BOUNDARY: row {row}")]
    RaggedBoundary { row: usize },
    #[error("DUAL_ZERO_DENOMINATOR: {location:?}")]
    ZeroDenominator { location: RationalLocation },
    #[error("DUAL_NEGATIVE_CLAIMED_VALUE")]
    NegativeClaimedValue,
    #[error("DUAL_ANNIHILATOR_MISMATCH: column {column}")]
    AnnihilatorMismatch { column: usize },
    #[error("DUAL_UNIT_BOUND_VIOLATION: index {index}")]
    UnitBoundViolation { index: usize },
    #[error("DUAL_PAIRING_MISMATCH")]
    PairingMismatch,
}

/// A replayed dual lower bound, not a certificate of the optimum or of authority.
///
/// There is no unchecked constructor or deserializer. Inputs remain available
/// read-only, and cloned inputs must be verified again after modification.
///
/// ~~~compile_fail
/// use core_functional::dual_verification::VerifiedDualLowerBound;
/// let forged = VerifiedDualLowerBound {
///     boundary: vec![], dual: vec![], residual: vec![],
///     value: num_rational::BigRational::from_integer(1.into()),
/// };
/// ~~~
///
/// A feasible lower bound cannot stand in for the separately verified optimum:
///
/// ~~~compile_fail
/// use num_rational::BigRational;
/// use core_functional::dual_verification::verify_dual_witness;
/// fn needs_optimum(_: core_functional::phi1::VerifiedExactPhi1) {}
/// let one = BigRational::from_integer(1.into());
/// let lower = verify_dual_witness(
///     &[vec![]], std::slice::from_ref(&one),
///     std::slice::from_ref(&one), &one,
/// ).unwrap();
/// needs_optimum(lower);
/// ~~~
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedDualLowerBound {
    boundary: Vec<Vec<BigRational>>,
    dual: Vec<BigRational>,
    residual: Vec<BigRational>,
    value: BigRational,
}

impl VerifiedDualLowerBound {
    pub fn value(&self) -> &BigRational {
        &self.value
    }

    pub fn boundary(&self) -> &[Vec<BigRational>] {
        &self.boundary
    }

    pub fn dual(&self) -> &[BigRational] {
        &self.dual
    }

    pub fn residual(&self) -> &[BigRational] {
        &self.residual
    }
}

fn canonical(
    value: &BigRational,
    location: RationalLocation,
) -> Result<BigRational, DualVerificationError> {
    if value.denom().is_zero() {
        return Err(DualVerificationError::ZeroDenominator { location });
    }
    Ok(BigRational::new(
        value.numer().clone(),
        value.denom().clone(),
    ))
}

fn validate_and_canonicalize_dual_inputs(
    boundary: &[Vec<BigRational>],
    dual: &[BigRational],
    residual: &[BigRational],
    claimed_value: &BigRational,
) -> Result<
    (
        usize,
        Vec<Vec<BigRational>>,
        Vec<BigRational>,
        Vec<BigRational>,
        BigRational,
    ),
    DualVerificationError,
> {
    if residual.is_empty() {
        return Err(DualVerificationError::EmptyInput);
    }
    if dual.len() != residual.len() {
        return Err(DualVerificationError::DimensionMismatch);
    }
    if boundary.len() != residual.len() {
        return Err(DualVerificationError::BoundaryRowMismatch {
            expected: residual.len(),
            actual: boundary.len(),
        });
    }
    let columns = boundary[0].len();
    for (row, coefficients) in boundary.iter().enumerate() {
        if coefficients.len() != columns {
            return Err(DualVerificationError::RaggedBoundary { row });
        }
    }

    // new_raw can bypass rational invariants in typed callers. Validate and
    // canonicalize every input before signs, bounds, products or comparisons.
    let boundary = boundary
        .iter()
        .enumerate()
        .map(|(row, values)| {
            values
                .iter()
                .enumerate()
                .map(|(column, value)| canonical(value, RationalLocation::Boundary { row, column }))
                .collect::<Result<Vec<_>, _>>()
        })
        .collect::<Result<Vec<_>, _>>()?;
    let dual = dual
        .iter()
        .enumerate()
        .map(|(index, value)| canonical(value, RationalLocation::Dual { index }))
        .collect::<Result<Vec<_>, _>>()?;
    let residual = residual
        .iter()
        .enumerate()
        .map(|(index, value)| canonical(value, RationalLocation::Residual { index }))
        .collect::<Result<Vec<_>, _>>()?;
    let value = canonical(claimed_value, RationalLocation::ClaimedValue)?;
    Ok((columns, boundary, dual, residual, value))
}

/// Verify B^T dual = 0, |dual_i| <= 1 and <dual, residual> = claimed >= 0.
///
/// Uses exact finite rationals, no floating tolerance, and a nonempty residual.
/// Zero-column boundaries represent the legitimate zero repair subspace. The
/// matrix need not be a graph incidence matrix: only its declared linear image
/// is used here. Neither source identity nor an external graph is authenticated.
pub fn verify_dual_witness(
    boundary: &[Vec<BigRational>],
    dual: &[BigRational],
    residual: &[BigRational],
    claimed_value: &BigRational,
) -> Result<VerifiedDualLowerBound, DualVerificationError> {
    let (columns, boundary, dual, residual, value) =
        validate_and_canonicalize_dual_inputs(boundary, dual, residual, claimed_value)?;

    if value.is_negative() {
        return Err(DualVerificationError::NegativeClaimedValue);
    }
    for column in 0..columns {
        let annihilator = boundary
            .iter()
            .zip(&dual)
            .map(|(row, coefficient)| &row[column] * coefficient)
            .sum::<BigRational>();
        if !annihilator.is_zero() {
            return Err(DualVerificationError::AnnihilatorMismatch { column });
        }
    }
    for (index, coefficient) in dual.iter().enumerate() {
        if coefficient.abs() > BigRational::one() {
            return Err(DualVerificationError::UnitBoundViolation { index });
        }
    }
    let pairing = dual
        .iter()
        .zip(&residual)
        .map(|(d, r)| d * r)
        .sum::<BigRational>();
    if pairing != value {
        return Err(DualVerificationError::PairingMismatch);
    }

    Ok(VerifiedDualLowerBound {
        boundary,
        dual,
        residual,
        value,
    })
}

// Origin: engine/crates_rs/core_functional/src/dual_verification.rs
// Claim: urn:core:crates_rs:core-functional:dual-verification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(value.into())
    }

    #[test]
    fn a_strict_lower_bound_is_valid_without_claiming_primal_optimality() {
        // im(B) is the first coordinate axis. The exact distance of (3,4)
        // is 4, while dual=(0,1/2) proves only the strict lower bound 2.
        let boundary = vec![vec![r(1)], vec![r(0)]];
        let dual = vec![r(0), BigRational::new(1.into(), 2.into())];
        let residual = vec![r(3), r(4)];
        let verified = verify_dual_witness(&boundary, &dual, &residual, &r(2)).unwrap();
        assert_eq!(verified.value(), &r(2));
        assert!(verified.value() < &residual[1].abs());
        assert_eq!(verified.boundary(), boundary);
        assert_eq!(verified.dual(), dual);
        assert_eq!(verified.residual(), residual);
    }

    #[test]
    fn signed_unreduced_inputs_are_canonicalized_before_checks() {
        let unreduced = BigRational::new_raw((-2).into(), (-2).into());
        let verified = verify_dual_witness(
            &[vec![]],
            std::slice::from_ref(&unreduced),
            std::slice::from_ref(&unreduced),
            &unreduced,
        )
        .unwrap();
        assert_eq!(verified.value(), &r(1));
        assert_eq!(verified.dual(), &[r(1)]);
        assert_eq!(verified.residual(), &[r(1)]);
        let zero = verify_dual_witness(&[vec![]], &[r(0)], &[r(99)], &r(0)).unwrap();
        assert_eq!(zero.value(), &r(0)); // zero lower bound is not zero optimum
    }

    #[test]
    fn empty_mismatched_and_ragged_inputs_have_named_refusals() {
        assert_eq!(
            verify_dual_witness(&[], &[], &[], &r(0)),
            Err(DualVerificationError::EmptyInput)
        );
        assert_eq!(
            verify_dual_witness(&[vec![]], &[], &[r(1)], &r(0)),
            Err(DualVerificationError::DimensionMismatch)
        );
        assert_eq!(
            verify_dual_witness(&[], &[r(1)], &[r(1)], &r(1)),
            Err(DualVerificationError::BoundaryRowMismatch {
                expected: 1,
                actual: 0
            })
        );
        assert_eq!(
            verify_dual_witness(&[vec![], vec![r(0)]], &[r(0), r(0)], &[r(1), r(1)], &r(0)),
            Err(DualVerificationError::RaggedBoundary { row: 1 })
        );
    }

    #[test]
    fn zero_denominators_are_refused_in_every_input_family() {
        let bad = BigRational::new_raw(1.into(), 0.into());
        for (boundary, dual, residual, claim, location) in [
            (
                vec![vec![bad.clone()]],
                vec![r(0)],
                vec![r(1)],
                r(0),
                RationalLocation::Boundary { row: 0, column: 0 },
            ),
            (
                vec![vec![r(0)]],
                vec![bad.clone()],
                vec![r(1)],
                r(1),
                RationalLocation::Dual { index: 0 },
            ),
            (
                vec![vec![r(0)]],
                vec![r(1)],
                vec![bad.clone()],
                r(1),
                RationalLocation::Residual { index: 0 },
            ),
            (
                vec![vec![r(0)]],
                vec![r(1)],
                vec![r(1)],
                bad.clone(),
                RationalLocation::ClaimedValue,
            ),
        ] {
            assert_eq!(
                verify_dual_witness(&boundary, &dual, &residual, &claim),
                Err(DualVerificationError::ZeroDenominator { location })
            );
        }
    }

    #[test]
    fn a_dual_that_does_not_annihilate_the_boundary_is_refused() {
        assert_eq!(
            verify_dual_witness(&[vec![r(1)]], &[r(1)], &[r(1)], &r(1)),
            Err(DualVerificationError::AnnihilatorMismatch { column: 0 })
        );
        assert_eq!(
            verify_dual_witness(
                &[vec![r(0), r(1)], vec![r(0), r(0)]],
                &[r(1), r(0)],
                &[r(1), r(0)],
                &r(1)
            ),
            Err(DualVerificationError::AnnihilatorMismatch { column: 1 })
        );
        let valid = verify_dual_witness(
            &[vec![r(1)], vec![r(1)]],
            &[r(1), r(-1)],
            &[r(5), r(2)],
            &r(3),
        )
        .unwrap();
        assert_eq!(valid.value(), &r(3));
    }

    #[test]
    fn a_dual_outside_the_unit_bound_is_refused() {
        for value in [r(2), r(-2)] {
            assert_eq!(
                verify_dual_witness(
                    &[vec![r(0)]],
                    std::slice::from_ref(&value),
                    std::slice::from_ref(&value),
                    &r(4)
                ),
                Err(DualVerificationError::UnitBoundViolation { index: 0 })
            );
        }
        assert!(verify_dual_witness(&[vec![r(0)]], &[r(-1)], &[r(-2)], &r(2)).is_ok());
        assert_eq!(
            verify_dual_witness(&[vec![], vec![]], &[r(0), r(2)], &[r(0), r(1)], &r(2)),
            Err(DualVerificationError::UnitBoundViolation { index: 1 })
        );
    }

    #[test]
    fn negative_claims_and_incorrect_pairings_are_distinct_refusals() {
        assert_eq!(
            verify_dual_witness(&[vec![]], &[r(0)], &[r(1)], &r(-1)),
            Err(DualVerificationError::NegativeClaimedValue)
        );
        assert_eq!(
            verify_dual_witness(&[vec![]], &[r(1)], &[r(2)], &r(1)),
            Err(DualVerificationError::PairingMismatch)
        );
        assert_eq!(
            verify_dual_witness(&[vec![]], &[r(1)], &[r(2)], &r(2))
                .unwrap()
                .value(),
            &r(2)
        );
    }

    #[test]
    fn exact_large_pairings_and_modified_input_replay_do_not_round_or_reuse_trust() {
        let huge = BigRational::from_integer(num_bigint::BigInt::one() << 4096);
        let verified =
            verify_dual_witness(&[vec![]], &[r(1)], std::slice::from_ref(&huge), &huge).unwrap();
        assert_eq!(verified.value(), &huge);
        let mut changed = verified.dual().to_vec();
        changed[0] = r(0);
        assert_eq!(
            verify_dual_witness(
                verified.boundary(),
                &changed,
                verified.residual(),
                verified.value()
            ),
            Err(DualVerificationError::PairingMismatch)
        );
        assert_eq!(verified.dual(), &[r(1)]);
    }
}
