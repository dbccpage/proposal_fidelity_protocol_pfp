//! Exact geodesic distances in Q/Z and nearest roots of unity.
use crate::rational::{ri, Rational};
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::ToPrimitive;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RationalCircleError {
    #[error("the root carrier must be nonempty")]
    EmptyCarrier,
    #[error("the nearest root index cannot be represented")]
    Index,
}
/// Canonical fractional part in [0,1), for arbitrarily large signed rationals.
pub fn fractional_part(theta: &Rational) -> Rational {
    Rational::new(
        theta.numer().mod_floor(theta.denom()),
        theta.denom().clone(),
    )
}
pub fn phase_distance_on_circle(a: &Rational, b: &Rational) -> Rational {
    let r = fractional_part(&(a - b));
    if &r + &r > ri(1) {
        ri(1) - r
    } else {
        r
    }
}
/// Only the two adjacent lattice points can minimize geodesic distance. Ties
/// choose the smallest residue, including the tie across the circle's cut.
pub fn nearest_root_of_unity(
    theta: &Rational,
    order: usize,
) -> Result<(usize, Rational), RationalCircleError> {
    if order == 0 {
        return Err(RationalCircleError::EmptyCarrier);
    }
    let n = BigInt::from(order);
    let t = fractional_part(theta) * Rational::from_integer(n.clone());
    let a = t.numer().div_floor(t.denom());
    let b = (&a + BigInt::from(1u8)).mod_floor(&n);
    let mut best = None;
    for k in [a, b] {
        let residue = k.to_usize().ok_or(RationalCircleError::Index)?;
        let distance = phase_distance_on_circle(theta, &Rational::new(k, n.clone()));
        if best.as_ref().is_none_or(|(old, dist): &(usize, Rational)| {
            distance < *dist || distance == *dist && residue < *old
        }) {
            best = Some((residue, distance));
        }
    }
    best.ok_or(RationalCircleError::Index)
}
// Origin: engine/crates_rs/core_number_theory/src/rational_circle.rs
// Claim: urn:core:crates_rs:core-number-theory:rational-circle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rational::rq;
    use num_traits::Zero;
    #[test]
    fn adjacent_lattice_decision_matches_exhaustion_and_handles_large_orders() {
        for d in 1..32 {
            for k in -30..31 {
                let theta = rq(k, 13);
                let exact = nearest_root_of_unity(&theta, d).unwrap();
                let brute = (0..d)
                    .map(|a| {
                        (
                            a,
                            phase_distance_on_circle(&theta, &Rational::new(a.into(), d.into())),
                        )
                    })
                    .min_by(|a, b| a.1.cmp(&b.1).then(a.0.cmp(&b.0)))
                    .unwrap();
                assert_eq!(exact, brute);
            }
        }
        let (a, dist) = nearest_root_of_unity(&ri(-7), usize::MAX).unwrap();
        assert_eq!(a, 0);
        assert!(dist.is_zero());
        assert_eq!(nearest_root_of_unity(&rq(1, 2), 1).unwrap().0, 0);
        assert!(nearest_root_of_unity(&ri(0), 0).is_err());
    }
}
