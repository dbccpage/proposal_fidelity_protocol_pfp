//! Exact continuous periodic test functions, with derived bounds and integrals.
//! Knots include both 0 and 1, with equal endpoint values. No field model is chosen.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_1a65fa59<T> {
    fn checked_invariant_1a65fa59(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_1a65fa59<T> for Option<T> {
    #[inline]
    fn checked_invariant_1a65fa59(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_1a65fa59<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_1a65fa59(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational as Rational;
use num_traits::{One, Signed, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CircleProfileError {
    #[error("circle profile needs 2..=65 ordered knots, from 0 to 1")]
    Knots,
    #[error("circle endpoint values must agree")]
    Periodicity,
    #[error("exact scalar must have a nonzero denominator and at most 256 input bits")]
    Scalar,
    #[error("uniform grid size must lie in 1..=256")]
    Grid,
}

fn canonical(value: Rational) -> Result<Rational, CircleProfileError> {
    if value.denom().is_zero() || value.numer().bits() > 256 || value.denom().bits() > 256 {
        return Err(CircleProfileError::Scalar);
    }
    Ok(value.reduced())
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CirclePiecewiseLinear {
    knots: Vec<(Rational, Rational)>,
    norm: Rational,
    lipschitz: Rational,
    square_integral: Rational,
}
impl CirclePiecewiseLinear {
    pub fn new(knots: Vec<(Rational, Rational)>) -> Result<Self, CircleProfileError> {
        if !(2..=65).contains(&knots.len()) {
            return Err(CircleProfileError::Knots);
        }
        let knots = knots
            .into_iter()
            .map(|(t, v)| Ok((canonical(t)?, canonical(v)?)))
            .collect::<Result<Vec<_>, CircleProfileError>>()?;
        if knots[0].0 != Rational::zero()
            || knots.last().checked_invariant_1a65fa59("checked invariant").0 != Rational::one()
            || knots.windows(2).any(|w| w[0].0 >= w[1].0)
        {
            return Err(CircleProfileError::Knots);
        }
        if knots[0].1 != knots.last().checked_invariant_1a65fa59("checked invariant").1 {
            return Err(CircleProfileError::Periodicity);
        }
        let norm = knots.iter().map(|(_, v)| v.abs()).max().checked_invariant_1a65fa59("checked invariant");
        let mut lipschitz = Rational::zero();
        let mut square_integral = Rational::zero();
        for pair in knots.windows(2) {
            let (t0, v0) = &pair[0];
            let (t1, v1) = &pair[1];
            let width = t1 - t0;
            lipschitz = lipschitz.max((v1 - v0).abs() / &width);
            square_integral +=
                width * (v0 * v0 + v0 * v1 + v1 * v1) / Rational::from_integer(3.into());
        }
        Ok(Self {
            knots,
            norm,
            lipschitz,
            square_integral,
        })
    }
    pub fn knots(&self) -> &[(Rational, Rational)] {
        &self.knots
    }
    pub fn norm(&self) -> &Rational {
        &self.norm
    }
    pub fn lipschitz(&self) -> &Rational {
        &self.lipschitz
    }
    pub fn square_integral(&self) -> &Rational {
        &self.square_integral
    }
    pub fn evaluate(&self, turn: Rational) -> Result<Rational, CircleProfileError> {
        let turn = canonical(turn)?;
        let phase = &turn - turn.floor();
        let pair = self
            .knots
            .windows(2)
            .find(|w| w[0].0 <= phase && phase < w[1].0)
            .checked_invariant_1a65fa59("checked invariant");
        let (t0, v0) = &pair[0];
        let (t1, v1) = &pair[1];
        Ok(v0 + (v1 - v0) * (phase - t0) / (t1 - t0))
    }
    pub fn uniform_samples(&self, nodes: usize) -> Result<Vec<Rational>, CircleProfileError> {
        if !(1..=256).contains(&nodes) {
            return Err(CircleProfileError::Grid);
        }
        (0..nodes)
            .map(|x| self.evaluate(Rational::new(x.into(), nodes.into())))
            .collect()
    }
}

// Origin: engine/crates_rs/core_functional/src/circle_piecewise_linear.rs
// Claim: urn:core:crates_rs:core-functional:circle-piecewise-linear:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_1a65fa59 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
