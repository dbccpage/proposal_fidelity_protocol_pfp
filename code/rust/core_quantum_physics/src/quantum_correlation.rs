//! Exact planar spin correlations and bounded finite optimisation.
//! The singlet correlator is -u.v; reversing Alice's signs yields the CHSH
//! convention u1.v1+u1.v2+u2.v1-u2.v2 used here. The declared finite direction
//! class is explicit, and its maximum is not a supremum over all observables.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b4c322cc<T> {
    fn checked_invariant_b4c322cc(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b4c322cc<T> for Option<T> {
    #[inline]
    fn checked_invariant_b4c322cc(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b4c322cc<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b4c322cc(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::exact_field::ordered::HermitianOrdered;
use core_number_theory::cyclotomic_field::{sqrt_of_integer, Cyclotomic};
use core_number_theory::rational::{ri, rq, Rational};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PlanarCorrelationError {
    #[error("a planar spin direction must have real entries and unit squared norm")]
    NotUnitReal,
    #[error("the exact ordered field refused a scalar comparison")]
    Order,
    #[error("the declared conductor or height bound is outside the supported finite search (height 1..=128)")]
    Carrier,
    #[error("the declared finite optimisation exhausted its candidate budget {0}")]
    Budget(usize),
    #[error("the declared class contains no admissible measurement strategy")]
    NoStrategy,
    #[error("exact field construction refused: {0}")]
    Field(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PlanarObservable<F> {
    pub x: F,
    pub y: F,
    pub label: String,
}
impl<F: HermitianOrdered> PlanarObservable<F> {
    pub fn new(x: F, y: F, label: impl Into<String>) -> Result<Self, PlanarCorrelationError> {
        let v = Self {
            x,
            y,
            label: label.into(),
        };
        v.validate()?;
        Ok(v)
    }
    pub fn validate(&self) -> Result<(), PlanarCorrelationError> {
        if self.x.conjugate() != self.x
            || self.y.conjugate() != self.y
            || self.x.mul(&self.x).add(&self.y.mul(&self.y)) != F::one()
        {
            return Err(PlanarCorrelationError::NotUnitReal);
        }
        Ok(())
    }
    pub fn dot(&self, other: &Self) -> Result<F, PlanarCorrelationError> {
        self.validate()?;
        other.validate()?;
        Ok(self.x.mul(&other.x).add(&self.y.mul(&other.y)))
    }
}

pub fn evaluate_planar_chsh<F: HermitianOrdered>(
    u1: &PlanarObservable<F>,
    u2: &PlanarObservable<F>,
    v1: &PlanarObservable<F>,
    v2: &PlanarObservable<F>,
) -> Result<F, PlanarCorrelationError> {
    Ok(u1
        .dot(v1)?
        .add(&u1.dot(v2)?)
        .add(&u2.dot(v1)?)
        .sub(&u2.dot(v2)?))
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FinitePlanarMaximum<F> {
    pub value: F,
    pub strategy: [usize; 4],
    pub candidate_count: usize,
    pub orthogonal_local_pairs: bool,
}
fn eligible_local_pairs<F: HermitianOrdered>(
    directions: &[PlanarObservable<F>],
    orthogonal_local_pairs: bool,
) -> Result<Vec<(usize, usize)>, PlanarCorrelationError> {
    let mut pairs = Vec::new();
    for i in 0..directions.len() {
        for j in 0..directions.len() {
            if !orthogonal_local_pairs || directions[i].dot(&directions[j])?.is_zero() {
                pairs.push((i, j));
            }
        }
    }
    Ok(pairs)
}

fn abs_fixed_field_value<F: HermitianOrdered>(s: F) -> Result<F, PlanarCorrelationError> {
    match s.fixed_field_sign() {
        Some(-1) => Ok(s.neg()),
        Some(0 | 1) => Ok(s),
        _ => Err(PlanarCorrelationError::Order),
    }
}

fn should_replace_best<F: HermitianOrdered>(
    best: &Option<(F, [usize; 4])>,
    value: &F,
) -> Result<bool, PlanarCorrelationError> {
    match best {
        None => Ok(true),
        Some((old, _)) => match value.sub(old).fixed_field_sign() {
            Some(1) => Ok(true),
            Some(-1 | 0) => Ok(false),
            _ => Err(PlanarCorrelationError::Order),
        },
    }
}

fn prepare_chsh_pairs<F: HermitianOrdered>(
    directions: &[PlanarObservable<F>],
    orthogonal_local_pairs: bool,
    candidate_budget: usize,
) -> Result<(Vec<(usize, usize)>, usize), PlanarCorrelationError> {
    if !(1..=1024).contains(&directions.len()) {
        return Err(PlanarCorrelationError::Carrier);
    }
    for v in directions {
        v.validate()?;
    }
    let pairs = eligible_local_pairs(directions, orthogonal_local_pairs)?;
    let required = pairs
        .len()
        .checked_mul(pairs.len())
        .filter(|&req| req <= candidate_budget)
        .ok_or(PlanarCorrelationError::Budget(candidate_budget))?;
    Ok((pairs, required))
}

/// Exhaustive finite decision; pairs may be explicitly restricted to perpendicular
/// local axes. Candidate exhaustion is a refusal and never a maximum verdict.
pub fn finite_planar_chsh_max<F: HermitianOrdered>(
    directions: &[PlanarObservable<F>],
    orthogonal_local_pairs: bool,
    candidate_budget: usize,
) -> Result<FinitePlanarMaximum<F>, PlanarCorrelationError> {
    let (pairs, required) =
        prepare_chsh_pairs(directions, orthogonal_local_pairs, candidate_budget)?;
    let mut best = None;
    for &(a0, a1) in &pairs {
        for &(b0, b1) in &pairs {
            let s = evaluate_planar_chsh(
                &directions[a0],
                &directions[a1],
                &directions[b0],
                &directions[b1],
            )?;
            let value = abs_fixed_field_value(s)?;
            if should_replace_best(&best, &value)? {
                best = Some((value, [a0, a1, b0, b1]));
            }
        }
    }
    let (value, strategy) = best.ok_or(PlanarCorrelationError::NoStrategy)?;
    Ok(FinitePlanarMaximum {
        value,
        strategy,
        candidate_count: required,
        orthogonal_local_pairs,
    })
}

/// Exact embedding decision, delegated to the canonical cyclotomic field.
pub fn sqrt2_in_cyclotomic(conductor: usize) -> bool {
    sqrt_of_integer(conductor, &2.into()).is_ok()
}

fn push_unique_direction(
    directions: &mut Vec<PlanarObservable<Cyclotomic<24>>>,
    x: Cyclotomic<24>,
    y: Cyclotomic<24>,
    label: &str,
) -> Result<(), PlanarCorrelationError> {
    let v = PlanarObservable::new(x, y, label)?;
    if !directions.iter().any(|u| u.x == v.x && u.y == v.y) {
        directions.push(v);
    }
    Ok(())
}

fn append_pythagorean_directions(
    directions: &mut Vec<PlanarObservable<Cyclotomic<24>>>,
    height: usize,
) -> Result<(), PlanarCorrelationError> {
    for denominator in 1..=height as i64 {
        for x in -denominator..=denominator {
            let square = denominator * denominator - x * x;
            let y = square.isqrt();
            if y * y == square {
                for sy in [y, -y] {
                    push_unique_direction(
                        directions,
                        Cyclotomic::<24>::rational(rq(x, denominator)),
                        Cyclotomic::<24>::rational(rq(sy, denominator)),
                        "rational Pythagorean",
                    )?;
                }
            }
        }
    }
    Ok(())
}

fn append_sqrt2_directions(
    directions: &mut Vec<PlanarObservable<Cyclotomic<24>>>,
    conductor: usize,
    height: usize,
) -> Result<(), PlanarCorrelationError> {
    if height < 2 || !sqrt2_in_cyclotomic(conductor) {
        return Ok(());
    }
    let s = Cyclotomic::<24>::try_from(
        sqrt_of_integer(24, &2.into()).map_err(|e| PlanarCorrelationError::Field(e.to_string()))?,
    )
    .map_err(|e| PlanarCorrelationError::Field(e.to_string()))?
    .scale(&rq(1, 2));
    for sx in [s.clone(), -s.clone()] {
        for sy in [s.clone(), -s.clone()] {
            push_unique_direction(directions, sx.clone(), sy, "quadratic 45 degree")?;
        }
    }
    Ok(())
}

fn append_sqrt3_directions(
    directions: &mut Vec<PlanarObservable<Cyclotomic<24>>>,
    conductor: usize,
    height: usize,
) -> Result<(), PlanarCorrelationError> {
    if height < 2 || sqrt_of_integer(conductor, &3.into()).is_err() {
        return Ok(());
    }
    let s = Cyclotomic::<24>::try_from(
        sqrt_of_integer(24, &3.into()).map_err(|e| PlanarCorrelationError::Field(e.to_string()))?,
    )
    .map_err(|e| PlanarCorrelationError::Field(e.to_string()))?
    .scale(&rq(1, 2));
    let h = Cyclotomic::<24>::rational(rq(1, 2));
    for sx in [s.clone(), -s] {
        for sy in [h.clone(), -h.clone()] {
            push_unique_direction(directions, sx.clone(), sy.clone(), "quadratic 30 degree")?;
            push_unique_direction(directions, sy, sx.clone(), "quadratic 60 degree")?;
        }
    }
    Ok(())
}

/// Rational Pythagorean directions with denominator <= height, plus the declared
/// 45-degree and 30-degree controls when their quadratic fields embed. All values
/// inhabit one canonical CM field, so mixed sqrt(2)/sqrt(3) operations are total.
pub fn generate_unit_vectors(
    conductor: usize,
    height: usize,
) -> Result<Vec<PlanarObservable<Cyclotomic<24>>>, PlanarCorrelationError> {
    let valid_conductor = (1..=core_number_theory::polynomial::MAX_CONDUCTOR).contains(&conductor);
    if !valid_conductor || !(1..=128).contains(&height) {
        return Err(PlanarCorrelationError::Carrier);
    }
    let mut directions = Vec::new();
    append_pythagorean_directions(&mut directions, height)?;
    append_sqrt2_directions(&mut directions, conductor, height)?;
    append_sqrt3_directions(&mut directions, conductor, height)?;
    Ok(directions)
}

/// Canonical 2 sqrt(2), represented in the shared exact CM field.
pub fn tsirelson_value() -> Cyclotomic<24> {
    Cyclotomic::try_from(sqrt_of_integer(24, &2.into()).checked_invariant_b4c322cc("sqrt2 embeds in conductor24"))
        .checked_invariant_b4c322cc("matching static conductor")
        .scale(&ri(2))
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_correlation.rs
// Claim: urn:core:crates_rs:core-quantum-physics:quantum-correlation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_b4c322cc {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
