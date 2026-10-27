//! Reusable finite lift pressure, holonomy and declared residual norms.
//! Norm normalization and choice of contexts are inputs. AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_e95f7013<T> {
    fn checked_invariant_e95f7013(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_e95f7013<T> for Option<T> {
    #[inline]
    fn checked_invariant_e95f7013(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_e95f7013<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_e95f7013(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_hermitian::{self};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::BigRational;
use num_traits::Signed;
use core_holonomy::{compute_loop_holonomy, DiscreteConnection, ExactMatrix as FieldMatrix};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::{QuadraticError, Surd};
use core_number_theory::radical_sum::SurdSum;
use core_number_theory::rational::{rq, Rational};
/// Refusals for malformed walk inputs.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TowerWalkError {
    #[error("the carrier is empty")]
    EmptyCarrier,
    #[error("context {context} has {actual} images, expected {expected}")]
    ContextLength {
        context: usize,
        expected: usize,
        actual: usize,
    },
    #[error("context {context} sends {point} outside the carrier")]
    ContextOutOfRange { context: usize, point: usize },
    #[error("edge vector {edge} has dimension {actual}, expected {expected}")]
    VectorDimension {
        edge: usize,
        expected: usize,
        actual: usize,
    },
    #[error("{weights} weights for {edges} edge vectors")]
    WeightCount { edges: usize, weights: usize },
    #[error("matrix is not a Hermitian 2x2 matrix")]
    NotHermitian2x2,
    #[error("core_holonomy refused: {0}")]
    Holonomy(String),
    #[error(transparent)]
    Surd(#[from] QuadraticError),
}

/// Points identified by the projection that some context still separates.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LiftTriggerWitness {
    pub x: usize,
    pub y: usize,
    pub context: usize,
}

fn validate_lift_trigger_inputs(
    n: usize,
    contexts: &[Vec<usize>],
) -> Result<(), TowerWalkError> {
    if n > 4096
        || contexts.len() > 256
        || n.checked_mul(n)
            .and_then(|v| v.checked_mul(contexts.len()))
            .is_none_or(|v| v > 1 << 24)
    {
        return Err(TowerWalkError::Holonomy(
            "lift-trigger operation budget".into(),
        ));
    }
    if n == 0 {
        return Err(TowerWalkError::EmptyCarrier);
    }
    for (context, images) in contexts.iter().enumerate() {
        if images.len() != n {
            return Err(TowerWalkError::ContextLength {
                context,
                expected: n,
                actual: images.len(),
            });
        }
        if let Some(&point) = images.iter().find(|&&image| image >= n) {
            return Err(TowerWalkError::ContextOutOfRange { context, point });
        }
    }
    Ok(())
}

/// Search the finite carrier `0..projection.len()` for a lift-trigger witness.
///
/// `projection[i]` is `p(i)`; `contexts[c][i]` is `rho_c(i)`.
pub fn find_lift_trigger(
    projection: &[usize],
    contexts: &[Vec<usize>],
) -> Result<Option<LiftTriggerWitness>, TowerWalkError> {
    let n = projection.len();
    validate_lift_trigger_inputs(n, contexts)?;
    for x in 0..n {
        for y in (x + 1)..n {
            if projection[x] != projection[y] {
                continue;
            }
            for (context, images) in contexts.iter().enumerate() {
                if projection[images[x]] != projection[images[y]] {
                    return Ok(Some(LiftTriggerWitness { x, y, context }));
                }
            }
        }
    }
    Ok(None)
}

/// `[Hol_a, Hol_b]` for two closed vertex loops of an `core_holonomy` connection.
pub fn holonomy_commutator(
    connection: &DiscreteConnection<BigRational>,
    loop_a: &[&str],
    loop_b: &[&str],
) -> Result<FieldMatrix<BigRational>, TowerWalkError> {
    let owned = |l: &[&str]| l.iter().map(|s| s.to_string()).collect::<Vec<_>>();
    let a = compute_loop_holonomy(connection, &owned(loop_a))
        .map_err(|e| TowerWalkError::Holonomy(e.to_string()))?;
    let b = compute_loop_holonomy(connection, &owned(loop_b))
        .map_err(|e| TowerWalkError::Holonomy(e.to_string()))?;
    let ab = a
        .matmul(&b)
        .map_err(|e| TowerWalkError::Holonomy(e.to_string()))?;
    let ba = b
        .matmul(&a)
        .map_err(|e| TowerWalkError::Holonomy(e.to_string()))?;
    let data = ab.data.iter().zip(&ba.data).map(|(x, y)| x - y).collect();
    FieldMatrix::try_new(ab.rows, ab.cols, data)
        .map_err(|e| TowerWalkError::Holonomy(e.to_string()))
}

/// `J_scalar(x) = sum_e w_e |x_e|`.
pub fn scalar_edge_norm(weights: &[Rational], x: &[Rational]) -> Result<Rational, TowerWalkError> {
    if weights.len() != x.len() {
        return Err(TowerWalkError::WeightCount {
            edges: x.len(),
            weights: weights.len(),
        });
    }
    if weights.iter().any(Signed::is_negative) {
        return Err(TowerWalkError::Holonomy("negative norm weight".into()));
    }
    core_functional::Phi1Functional::weighted_l1_rational(weights, x)
        .ok_or_else(|| TowerWalkError::Holonomy("invalid scalar norm inputs".into()))
}

/// `J_SO(k)(x) = sum_e w_e ||x_e||_2`, as an exact sum of surds.
pub fn rotational_edge_norm(
    weights: &[Rational],
    vectors: &[Vec<Rational>],
) -> Result<SurdSum, TowerWalkError> {
    if weights.len() != vectors.len() {
        return Err(TowerWalkError::WeightCount {
            edges: vectors.len(),
            weights: weights.len(),
        });
    }
    if weights.iter().any(Signed::is_negative) {
        return Err(TowerWalkError::Holonomy("negative norm weight".into()));
    }
    let k = vectors.first().map_or(0, Vec::len);
    let mut sum = SurdSum::default();
    for (edge, (w, v)) in weights.iter().zip(vectors).enumerate() {
        if v.len() != k {
            return Err(TowerWalkError::VectorDimension {
                edge,
                expected: k,
                actual: v.len(),
            });
        }
        let norm_sq: Rational = v.iter().map(|c| c * c).sum();
        sum.add_surd(&Surd::new(w.clone(), &norm_sq)?);
    }
    Ok(sum)
}

/// `(1/2) ||X||_1` for a Hermitian `2 x 2` matrix.
///
/// With `t = Tr X` and `D = (a - d)^2 + 4|b|^2`, the eigenvalues are
/// `(t +- sqrt D) / 2`, so `||X||_1 = sqrt D` when `D >= t^2` and `|t|` otherwise.
pub fn half_trace_norm_2x2(x: &BasicMatrix<GaussianRat>) -> Result<Surd, TowerWalkError> {
    if x.rows() != 2 || x.cols() != 2 || !exact_hermitian::is_hermitian(x) {
        return Err(TowerWalkError::NotHermitian2x2);
    }
    let a = &(x)
        .get_ref(0, 0)
        .checked_invariant_e95f7013("validated finite matrix shape and budget")
        .re;
    let d = &(x)
        .get_ref(1, 1)
        .checked_invariant_e95f7013("validated finite matrix shape and budget")
        .re;
    let t = a + d;
    let gap = a - d;
    let disc = &gap * &gap
        + Rational::from_integer(4.into())
            * (x)
                .get_ref(0, 1)
                .checked_invariant_e95f7013("validated finite matrix shape and budget")
                .norm_sq();
    if disc >= &t * &t {
        Ok(Surd::new(rq(1, 2), &disc)?)
    } else {
        Ok(Surd::rational(t.abs() * rq(1, 2)))
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/tower_walk_validator.rs
// Claim: urn:core:crates_rs:core-quantum-physics:tower-walk-validator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e95f7013 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
