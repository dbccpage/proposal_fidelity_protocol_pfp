// AuthorityEffect: None.

//! Exact convex-hull certificates for a declared finite rational family.
//!
//! A family `P = (P_1, ..., P_K)` of rational coordinate vectors is declared
//! input. A vector `w` is `P`-separable when `w = sum_k lambda_k P_k` with
//! `lambda >= 0` and `sum_k lambda_k = 1`, that is when `w` lies in the convex
//! hull `conv(P)`. Computed exactly:
//!
//! - verification of a declared convex decomposition `lambda`;
//! - verification of a declared separating witness `(phi, t)`: `phi(P_k) >= t`
//!   for every `k` and `phi(w) < t`. Soundness is the identity
//!   `phi(sum_k lambda_k P_k) = sum_k lambda_k phi(P_k) >= t`, so no vector
//!   carries both certificates;
//! - a bounded decision that returns one of the two certificates or a typed
//!   pivot-budget refusal. The
//!   weighted `l1` problem
//!   `min_lambda 2 |1 - sum lambda| + 2 ||w - P lambda||_1 + ||lambda||_1`
//!   has value at least `1 + (constraint residual)`, with value exactly one on
//!   members. It is proposed by `core_solvers::solver_lp_exact_simplex` and
//!   replayed, primal and dual, by `core_functional::phi1`. At value one the
//!   minimiser is a decomposition. Above one the dual witness
//!   `y = (y_0, y_P, y_lambda)` satisfies `y_0 + <y_P, P_k> <= 1` for every `k`,
//!   so `phi = -y_P`, `t = y_0 - 1` separates `w` with gap `value - 1`. For a
//!   finite declared family, completeness is finite linear-programming duality;
//! - transport of a decomposition through a linear map that sends every
//!   declared member into the hull of a declared target family.
//!
//! Each returned certificate is re-verified directly, independently of the
//! solver. Nothing here decides separability over all product states, which
//! do not form a finite family. Refused: empty families, coordinate-length
//! mismatches, and any solver or certificate refusal, which is reported and
//! never turned into a verdict.

use crate::solver_lp_exact_simplex::solve_weighted_l1_projection;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix, ExactFieldError};
use num_traits::{One, Signed, Zero};
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};

use num_rational::BigRational as Rational;
fn ri(n: i64) -> Rational {
    Rational::from_integer(n.into())
}

/// Refusals for declared-family separability.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ConvexHullError {
    #[error("a declared family needs at least one member")]
    EmptyFamily,
    #[error(
        "family size {members} or coordinate dimension {dimension} exceeds the finite limit 256"
    )]
    SizeLimit { members: usize, dimension: usize },
    #[error("a rational certificate entry has a zero denominator")]
    InvalidRational,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error("vector has {actual} coordinates, expected {expected}")]
    Dimension { expected: usize, actual: usize },
    #[error("{actual} coefficients for {expected} family members")]
    CoefficientCount { expected: usize, actual: usize },
    #[error("coefficient {index} is negative")]
    NegativeCoefficient { index: usize },
    #[error("coefficients sum to {sum}, not one")]
    CoefficientsNotNormalized { sum: Rational },
    #[error("the combination differs from the target at coordinate {index}")]
    DoesNotReproduce { index: usize },
    #[error("the functional falls below the threshold on member {member}")]
    MemberBelowThreshold { member: usize },
    #[error("the functional does not fall below the threshold on the target")]
    NotSeparating,
    #[error("row {row} of the map has {actual} entries, expected {expected}")]
    MapShape {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("the map sends member {member} outside the target hull")]
    MemberLeavesTargetHull { member: usize },
    #[error("exact l1 solver refused: {0}")]
    Solver(String),
    #[error("certificate replay refused: {0}")]
    Certificate(String),
}

fn dot(a: &[Rational], b: &[Rational]) -> Rational {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

/// A declared finite family of coordinate vectors of one length.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFamily {
    members: Vec<Vec<Rational>>,
    dimension: usize,
}

impl DeclaredFamily {
    pub fn new(members: Vec<Vec<Rational>>) -> Result<Self, ConvexHullError> {
        let dimension = members.first().ok_or(ConvexHullError::EmptyFamily)?.len();
        if members.len() > 256 || dimension > 256 {
            return Err(ConvexHullError::SizeLimit {
                members: members.len(),
                dimension,
            });
        }
        if let Some(bad) = members.iter().find(|m| m.len() != dimension) {
            return Err(ConvexHullError::Dimension {
                expected: dimension,
                actual: bad.len(),
            });
        }
        check_rationals(members.iter().flatten())?;
        Ok(Self { members, dimension })
    }

    pub fn members(&self) -> &[Vec<Rational>] {
        &self.members
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    fn check(&self, w: &[Rational]) -> Result<(), ConvexHullError> {
        if w.len() != self.dimension {
            return Err(ConvexHullError::Dimension {
                expected: self.dimension,
                actual: w.len(),
            });
        }
        check_rationals(w)
    }
}

fn check_rationals<'a>(
    values: impl IntoIterator<Item = &'a Rational>,
) -> Result<(), ConvexHullError> {
    if values.into_iter().any(|v| v.denom().is_zero()) {
        Err(ConvexHullError::InvalidRational)
    } else {
        Ok(())
    }
}

/// Convex weights `lambda`, one per family member.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConvexDecomposition {
    coefficients: Vec<Rational>,
}

impl ConvexDecomposition {
    pub fn new(coefficients: Vec<Rational>) -> Self {
        Self { coefficients }
    }

    pub fn coefficients(&self) -> &[Rational] {
        &self.coefficients
    }

    /// Check `lambda >= 0`, `sum lambda = 1` and `sum_k lambda_k P_k = w` exactly.
    pub fn verify(&self, family: &DeclaredFamily, w: &[Rational]) -> Result<(), ConvexHullError> {
        family.check(w)?;
        check_rationals(&self.coefficients)?;
        if self.coefficients.len() != family.members.len() {
            return Err(ConvexHullError::CoefficientCount {
                expected: family.members.len(),
                actual: self.coefficients.len(),
            });
        }
        if let Some(index) = self.coefficients.iter().position(Signed::is_negative) {
            return Err(ConvexHullError::NegativeCoefficient { index });
        }
        let sum: Rational = self.coefficients.iter().sum();
        if !sum.is_one() {
            return Err(ConvexHullError::CoefficientsNotNormalized { sum });
        }
        for (index, target) in w.iter().enumerate() {
            let combined: Rational = self
                .coefficients
                .iter()
                .zip(&family.members)
                .map(|(l, p)| l * &p[index])
                .sum();
            if &combined != target {
                return Err(ConvexHullError::DoesNotReproduce { index });
            }
        }
        Ok(())
    }
}

/// A linear functional `phi` and a threshold `t`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeparatingWitness {
    functional: Vec<Rational>,
    threshold: Rational,
}

impl SeparatingWitness {
    pub fn new(functional: Vec<Rational>, threshold: Rational) -> Self {
        Self {
            functional,
            threshold,
        }
    }

    pub fn functional(&self) -> &[Rational] {
        &self.functional
    }

    pub fn threshold(&self) -> &Rational {
        &self.threshold
    }

    /// `phi(v)`.
    pub fn evaluate(&self, v: &[Rational]) -> Result<Rational, ConvexHullError> {
        check_rationals(
            self.functional
                .iter()
                .chain(v)
                .chain(std::iter::once(&self.threshold)),
        )?;
        if v.len() != self.functional.len() {
            return Err(ConvexHullError::Dimension {
                expected: self.functional.len(),
                actual: v.len(),
            });
        }
        Ok(dot(&self.functional, v))
    }

    /// Check `phi(P_k) >= t` for every member and `phi(w) < t`; return the gap `t - phi(w) > 0`.
    pub fn verify(
        &self,
        family: &DeclaredFamily,
        w: &[Rational],
    ) -> Result<Rational, ConvexHullError> {
        family.check(w)?;
        for (member, p) in family.members.iter().enumerate() {
            if self.evaluate(p)? < self.threshold {
                return Err(ConvexHullError::MemberBelowThreshold { member });
            }
        }
        let gap = &self.threshold - self.evaluate(w)?;
        if !gap.is_positive() {
            return Err(ConvexHullError::NotSeparating);
        }
        Ok(gap)
    }

    /// `sum_k lambda_k phi(P_k)`: equal to `phi(w)` whenever `lambda` decomposes `w`.
    pub fn value_on_decomposition(
        &self,
        family: &DeclaredFamily,
        decomposition: &ConvexDecomposition,
    ) -> Result<Rational, ConvexHullError> {
        check_rationals(&decomposition.coefficients)?;
        if decomposition.coefficients.len() != family.members.len() {
            return Err(ConvexHullError::CoefficientCount {
                expected: family.members.len(),
                actual: decomposition.coefficients.len(),
            });
        }
        family
            .members
            .iter()
            .zip(&decomposition.coefficients)
            .map(|(p, l)| Ok(l * self.evaluate(p)?))
            .sum()
    }
}

/// The certificate returned by [`decide_membership`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MembershipCertificate {
    /// `w` is in `conv(P)`, with these weights.
    Member(ConvexDecomposition),
    /// `w` is outside `conv(P)`, separated by this witness.
    Separated(SeparatingWitness),
}

/// Decide `w in conv(P)` exactly, returning a verified certificate or refusing
/// when the finite default pivot budget is exhausted.
pub fn decide_membership(
    family: &DeclaredFamily,
    w: &[Rational],
) -> Result<MembershipCertificate, ConvexHullError> {
    family.check(w)?;
    let (k, d) = (family.members.len(), family.dimension);
    let rows = 1 + d + k;
    let mut target = Vec::with_capacity(rows);
    let mut weights = Vec::with_capacity(rows);
    let mut map = Vec::with_capacity(rows);
    target.push(Rational::one());
    weights.push(ri(2));
    map.push(vec![Rational::one(); k]);
    for (i, value) in w.iter().enumerate() {
        target.push(value.clone());
        weights.push(ri(2));
        map.push(family.members.iter().map(|p| p[i].clone()).collect());
    }
    for j in 0..k {
        target.push(Rational::zero());
        weights.push(Rational::one());
        let mut unit = vec![Rational::zero(); k];
        unit[j] = Rational::one();
        map.push(unit);
    }
    let budget = 64 * (rows + k) + 1024;
    let solution = solve_weighted_l1_projection(&target, &weights, &map, budget)
        .map_err(|e| ConvexHullError::Solver(e.to_string()))?;
    let verified = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
        omega: target,
        d0: map,
        weights,
        alpha: solution.coefficients,
        primal_residual: solution.residual,
        dual_witness: solution.dual,
        reported_value: solution.value,
    })
    .map_err(|e| ConvexHullError::Certificate(e.to_string()))?;
    let certificate = if verified.value().is_one() {
        MembershipCertificate::Member(ConvexDecomposition::new(verified.alpha().to_vec()))
    } else {
        let y = verified.dual_witness();
        let functional = y[1..=d].iter().map(|v| -v).collect();
        MembershipCertificate::Separated(SeparatingWitness::new(
            functional,
            &y[0] - Rational::one(),
        ))
    };
    match &certificate {
        MembershipCertificate::Member(decomposition) => decomposition.verify(family, w)?,
        MembershipCertificate::Separated(witness) => {
            witness.verify(family, w)?;
        }
    }
    Ok(certificate)
}

/// Carry a decomposition of `w` over `source` to one of `M w` over `target`.
///
/// Every image `M P_k` is decided against `target`. If one lies outside
/// `conv(target)` the transport is refused, naming that member. Otherwise the
/// result is `nu = sum_k lambda_k mu^(k)` with `mu^(k)` a decomposition of
/// `M P_k`, verified against `M w`.
fn accumulate_transported_member(
    map: &BasicMatrix<Rational>,
    target: &DeclaredFamily,
    member: usize,
    p: &[Rational],
    lambda: &Rational,
    nu: &mut [Rational],
) -> Result<(), ConvexHullError> {
    match decide_membership(target, &matrix::multiply_vector(map, p)?)? {
        MembershipCertificate::Member(mu) => {
            for (acc, m) in nu.iter_mut().zip(mu.coefficients()) {
                *acc += lambda * m;
            }
            Ok(())
        }
        MembershipCertificate::Separated(_) => {
            Err(ConvexHullError::MemberLeavesTargetHull { member })
        }
    }
}

pub fn transport_decomposition(
    map: &BasicMatrix<Rational>,
    source: &DeclaredFamily,
    target: &DeclaredFamily,
    decomposition: &ConvexDecomposition,
    w: &[Rational],
) -> Result<ConvexDecomposition, ConvexHullError> {
    if map.shape() != (target.dimension, source.dimension) {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "convex decomposition transport",
            left: map.shape(),
            right: (target.dimension, source.dimension),
        }
        .into());
    }
    check_rationals(map.as_slice())?;
    decomposition.verify(source, w)?;
    let mut nu = vec![Rational::zero(); target.members.len()];
    for (member, (p, lambda)) in source
        .members
        .iter()
        .zip(&decomposition.coefficients)
        .enumerate()
    {
        accumulate_transported_member(map, target, member, p, lambda, &mut nu)?;
    }
    let transported = ConvexDecomposition::new(nu);
    transported.verify(target, &matrix::multiply_vector(map, w)?)?;
    Ok(transported)
}

// Origin: engine/crates_rs/core_solvers/src/solver_convex_finite_hull.rs
// Claim: urn:core:crates_rs:core-solvers:solver-convex-finite-hull:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn membership_separation_and_transport_replay_both_sides() {
        let f = DeclaredFamily::new(vec![vec![ri(0)], vec![ri(2)]]).unwrap();
        let member = match decide_membership(&f, &[ri(1)]).unwrap() {
            MembershipCertificate::Member(w) => w,
            _ => panic!("declared midpoint must be a member"),
        };
        member.verify(&f, &[ri(1)]).unwrap();
        let bad = ConvexDecomposition::new(vec![ri(1), ri(1)]);
        assert!(bad.verify(&f, &[ri(1)]).is_err());
        let outside = match decide_membership(&f, &[ri(3)]).unwrap() {
            MembershipCertificate::Separated(w) => w,
            _ => panic!("outside interval must separate"),
        };
        outside.verify(&f, &[ri(3)]).unwrap();
        assert!(outside.verify(&f, &[ri(1)]).is_err());
        let target = DeclaredFamily::new(vec![vec![ri(0)], vec![ri(4)]]).unwrap();
        let map = matrix::from_rows(vec![vec![ri(2)]]).unwrap();
        transport_decomposition(&map, &f, &target, &member, &[ri(1)])
            .unwrap()
            .verify(&target, &[ri(2)])
            .unwrap();
        assert!(matches!(
            DeclaredFamily::new(vec![vec![ri(0)]; 257]),
            Err(ConvexHullError::SizeLimit { .. })
        ));
        let invalid = Rational::new_raw(1.into(), 0.into());
        assert_eq!(
            decide_membership(&f, &[invalid.clone()]),
            Err(ConvexHullError::InvalidRational)
        );
        assert_eq!(
            ConvexDecomposition::new(vec![invalid.clone(), ri(0)]).verify(&f, &[ri(1)]),
            Err(ConvexHullError::InvalidRational)
        );
        assert_eq!(
            SeparatingWitness::new(vec![ri(1)], invalid).verify(&f, &[ri(3)]),
            Err(ConvexHullError::InvalidRational)
        );
    }
}
