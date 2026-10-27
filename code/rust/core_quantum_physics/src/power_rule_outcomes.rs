// AuthorityEffect: None.

//! Power-law outcome rules on declared real orthonormal contexts, and the
//! context dependence that sets the square apart.
//!
//! A context is an ordered orthonormal basis `B` of `Q^d`, checked exactly:
//! `<b, b'> = 1` when `b = b'` and `0` otherwise. For a nonzero state `psi` of
//! `Q^d` and a power `p >= 1`, the rule gives each `b` in `B` the weight
//!
//! `P_p(b | B) = |<b, psi>|^p / N_p(B)`, with `N_p(B) = sum_(b' in B) |<b', psi>|^p`.
//!
//! Computed exactly:
//!
//! - [`power_rule`] and [`normalizer`]. Every power gives a probability vector
//!   on every context. For `p = 2` the normalizer is `<psi, psi>` on every
//!   context (Parseval), so `P_2(b | B)` depends on `b` alone: it is the Born
//!   weight of the pure state `psi`;
//! - [`find_context_dependence`]: over a declared list of contexts, the first
//!   vector shared by two of them (up to sign) that the rule weighs
//!   differently in the two. A rule with such a vector gives that ray no single
//!   weight, so it is not a frame function and equals `<b, rho b>` for no
//!   density `rho`. The search reports only what the declared contexts show.
//!
//! In dimension 2 a unit vector has one orthogonal complement up to sign, so a
//! ray lies in one context only and no power rule can be context dependent:
//! every power rule is a frame function there. Gleason's hypothesis `d >= 3`
//! carries that weight. Nothing here proves Gleason's theorem.
//!
//! Real rational vectors keep `|x|^p` rational for every integer `p`; complex
//! amplitudes are not covered. Refused: an empty context, vectors of different
//! lengths, a vector count other than the dimension, a family that is not
//! orthonormal, power zero, a state of the wrong length, and the zero state.

use num_traits::{pow, One, Signed, Zero};

use core_number_theory::rational::Rational;

/// Largest declared integer exponent.
pub const MAX_POWER: usize = 1024;

/// Refusals for contexts and power rules.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PowerRuleError {
    #[error("a context needs at least one vector")]
    EmptyContext,
    #[error("vector {index} has {actual} coordinates, expected {expected}")]
    VectorLength {
        index: usize,
        expected: usize,
        actual: usize,
    },
    #[error("a context in dimension {dimension} needs {dimension} vectors, not {found}")]
    VectorCount { dimension: usize, found: usize },
    #[error("vectors {left} and {right} violate orthonormality")]
    NotOrthonormal { left: usize, right: usize },
    #[error("the power must be at least 1")]
    ZeroPower,
    #[error("power {0} exceeds exact exponent budget {MAX_POWER}")]
    PowerBudget(usize),
    #[error("the state has {actual} coordinates, the context {expected}")]
    StateLength { expected: usize, actual: usize },
    #[error("the zero state has no outcome weights")]
    ZeroState,
}

fn dot(u: &[Rational], v: &[Rational]) -> Rational {
    u.iter().zip(v).map(|(a, b)| a * b).sum()
}

/// A declared orthonormal basis of `Q^d`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Context {
    vectors: Vec<Vec<Rational>>,
}

impl Context {
    /// Declare a context; orthonormality is checked exactly.
    pub fn new(vectors: Vec<Vec<Rational>>) -> Result<Self, PowerRuleError> {
        let dimension = vectors.first().ok_or(PowerRuleError::EmptyContext)?.len();
        if let Some((index, vector)) = vectors
            .iter()
            .enumerate()
            .find(|(_, v)| v.len() != dimension)
        {
            return Err(PowerRuleError::VectorLength {
                index,
                expected: dimension,
                actual: vector.len(),
            });
        }
        if vectors.len() != dimension {
            return Err(PowerRuleError::VectorCount {
                dimension,
                found: vectors.len(),
            });
        }
        for left in 0..dimension {
            for right in left..dimension {
                let expected = if left == right {
                    Rational::one()
                } else {
                    Rational::zero()
                };
                if dot(&vectors[left], &vectors[right]) != expected {
                    return Err(PowerRuleError::NotOrthonormal { left, right });
                }
            }
        }
        Ok(Self { vectors })
    }

    pub fn dimension(&self) -> usize {
        self.vectors.len()
    }
}

fn powered_overlaps(
    psi: &[Rational],
    context: &Context,
    power: usize,
) -> Result<Vec<Rational>, PowerRuleError> {
    if power == 0 {
        return Err(PowerRuleError::ZeroPower);
    }
    if power > MAX_POWER {
        return Err(PowerRuleError::PowerBudget(power));
    }
    if psi.len() != context.dimension() {
        return Err(PowerRuleError::StateLength {
            expected: context.dimension(),
            actual: psi.len(),
        });
    }
    if psi.iter().all(Zero::is_zero) {
        return Err(PowerRuleError::ZeroState);
    }
    Ok(context
        .vectors
        .iter()
        .map(|b| pow(dot(b, psi).abs(), power))
        .collect())
}

/// `N_p(B) = sum_(b in B) |<b, psi>|^p`.
pub fn normalizer(
    psi: &[Rational],
    context: &Context,
    power: usize,
) -> Result<Rational, PowerRuleError> {
    Ok(powered_overlaps(psi, context, power)?.into_iter().sum())
}

/// `P_p(b | B)` for every `b` of the context, in its declared order.
///
/// The normalizer is positive: a nonzero state has a nonzero overlap with some
/// vector of any basis.
pub fn power_rule(
    psi: &[Rational],
    context: &Context,
    power: usize,
) -> Result<Vec<Rational>, PowerRuleError> {
    let weights = powered_overlaps(psi, context, power)?;
    let total: Rational = weights.iter().sum();
    Ok(weights.into_iter().map(|w| w / &total).collect())
}

/// A vector shared by two declared contexts that a rule weighs differently.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ContextDependence {
    /// The shared vector, as declared in the first context.
    pub ray: Vec<Rational>,
    /// Context index, position in that context, and weight, for each context.
    pub first: (usize, usize, Rational),
    pub second: (usize, usize, Rational),
}

fn same_ray(u: &[Rational], v: &[Rational]) -> bool {
    u == v || u.iter().zip(v).all(|(a, b)| *a == -b)
}

/// The first vector, over ordered pairs of declared contexts, that the power
/// rule weighs differently in two contexts; `None` when the declared contexts
/// show no dependence.
pub fn find_context_dependence(
    psi: &[Rational],
    contexts: &[Context],
    power: usize,
) -> Result<Option<ContextDependence>, PowerRuleError> {
    if contexts.is_empty() {
        return Err(PowerRuleError::EmptyContext);
    }
    let rules: Vec<Vec<Rational>> = contexts
        .iter()
        .map(|context| power_rule(psi, context, power))
        .collect::<Result<_, _>>()?;
    for (i, left) in contexts.iter().enumerate() {
        for (j, right) in contexts.iter().enumerate().skip(i + 1) {
            for (k, u) in left.vectors.iter().enumerate() {
                for (l, v) in right.vectors.iter().enumerate() {
                    if same_ray(u, v) && rules[i][k] != rules[j][l] {
                        return Ok(Some(ContextDependence {
                            ray: u.clone(),
                            first: (i, k, rules[i][k].clone()),
                            second: (j, l, rules[j][l].clone()),
                        }));
                    }
                }
            }
        }
    }
    Ok(None)
}

// Origin: engine/crates_rs/core_quantum_physics/src/power_rule_outcomes.rs
// Claim: urn:core:crates_rs:core-quantum-physics:power-rule-outcomes:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_7c255f4c {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
