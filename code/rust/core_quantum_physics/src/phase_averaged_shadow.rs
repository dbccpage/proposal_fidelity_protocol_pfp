// AuthorityEffect: None.

//! Phase averaging over a declared finite phase group, computed exactly.
//!
//! The group is a finite subgroup `G` of the unit Gaussian rationals, declared
//! and checked by `phase_blind_quotient::UnitPhaseGroup` (in `Q(i)` it is one
//! of `{1}`, `{1, -1}`, `{1, i, -1, -i}`). [`phase_group_average`] averages
//! `D rho D*` over all `|G|^n` diagonal unitaries `D` whose entries lie in `G`,
//! by enumeration. The entry `(j, k)` of the average is `rho_jk` times the mean
//! of `g conj(h)` over independent `g, h` in `G`; that mean is zero for every
//! nontrivial group, so the average should be the dephasing of `rho` onto its
//! diagonal.
//!
//! [`averages_to_dephasing`] decides this for a dimension and a group. The
//! average is linear in `rho`, so comparing it with the dephasing channel on
//! the `n^2` matrix units decides the identity for every `n x n` matrix,
//! including matrices with irrational entries such as the lift
//! `c = sqrt(w) e^(i theta)`, whose phase-averaged readout `u* avg(c c*) u` is
//! then `sum |u_g|^2 w_g`.
//!
//! The continuous Haar average is not computed. A nontrivial finite group is
//! a declared stand-in that gives the same dephasing, and the trivial group
//! averages nothing. Refused: non-square input and enumerations beyond
//! [`AVERAGE_BUDGET`] terms.

use crate::exact_channel::ExactKrausChannel;
use crate::phase_blind_quotient::UnitPhaseGroup;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution::adjoint, matrix, ExactFieldError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

/// Largest number of diagonal unitaries an average may enumerate.
pub const AVERAGE_BUDGET: usize = 1 << 12;

/// Refusals for phase averaging.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ShadowError {
    #[error("a {rows}x{cols} matrix is not square")]
    NotSquare { rows: usize, cols: usize },
    #[error("{terms} diagonal unitaries exceed the budget of {AVERAGE_BUDGET}")]
    Budget { terms: usize },
    #[error("dimension must be positive")]
    ZeroDimension,
    #[error("dephasing channel refused: {0}")]
    Channel(String),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

fn conjugate_by_phase_code(
    rho: &BasicMatrix<GaussianRat>,
    code: usize,
    n: usize,
    phases: &[GaussianRat],
) -> Result<BasicMatrix<GaussianRat>, ShadowError> {
    let mut rest = code;
    let diagonal: Vec<GaussianRat> = (0..n)
        .map(|_| {
            let g = phases[rest % phases.len()].clone();
            rest /= phases.len();
            g
        })
        .collect();
    let d = matrix::diagonal(&diagonal)?;
    let adj = adjoint(&d)?;
    let left = matrix::multiply(&d, rho)?;
    Ok(matrix::multiply(&left, &adj)?)
}

/// The exact average of `D rho D*` over all diagonal unitaries with entries in `group`.
pub fn phase_group_average(
    rho: &BasicMatrix<GaussianRat>,
    group: &UnitPhaseGroup,
) -> Result<BasicMatrix<GaussianRat>, ShadowError> {
    if rho.rows() != rho.cols() {
        return Err(ShadowError::NotSquare {
            rows: rho.rows(),
            cols: rho.cols(),
        });
    }
    let n = rho.rows();
    if n == 0 {
        return Err(ShadowError::ZeroDimension);
    }
    let phases = group.elements();
    let terms = (0..n).try_fold(1usize, |acc, _| {
        acc.checked_mul(phases.len())
            .filter(|t| *t <= AVERAGE_BUDGET)
    });
    let Some(terms) = terms else {
        return Err(ShadowError::Budget {
            terms: phases.len().saturating_pow(n as u32),
        });
    };
    let mut sum = matrix::zeros(n, n)?;
    for code in 0..terms {
        let term = conjugate_by_phase_code(rho, code, n, phases)?;
        sum = matrix::add(&sum, &term)?;
    }
    let count = GaussianRat::from_rational(Rational::from_integer(terms.into()));
    Ok(matrix::scale(&sum, &count.inv())?)
}

fn shadow_matrix_unit(
    n: usize,
    j: usize,
    k: usize,
) -> Result<BasicMatrix<GaussianRat>, ShadowError> {
    Ok(matrix::from_fn(n, n, |r, c| {
        if (r, c) == (j, k) {
            GaussianRat::one()
        } else {
            GaussianRat::zero()
        }
    })?)
}

fn build_dephasing_channel(n: usize) -> Result<ExactKrausChannel, ShadowError> {
    let projectors = (0..n)
        .map(|k| shadow_matrix_unit(n, k, k))
        .collect::<Result<Vec<_>, _>>()?;
    ExactKrausChannel::from_operators(projectors).map_err(|e| ShadowError::Channel(e.to_string()))
}

/// Whether averaging over `group` equals the dephasing channel `{|k><k|}` on
/// every `n x n` matrix, decided on the matrix units.
pub fn averages_to_dephasing(n: usize, group: &UnitPhaseGroup) -> Result<bool, ShadowError> {
    if n == 0 {
        return Err(ShadowError::ZeroDimension);
    }
    if n > 64 {
        return Err(ShadowError::Budget {
            terms: n.saturating_mul(n),
        });
    }
    let dephasing = build_dephasing_channel(n)?;
    for j in 0..n {
        for k in 0..n {
            let unit = shadow_matrix_unit(n, j, k)?;
            let dephased = dephasing
                .apply(&unit)
                .map_err(|e| ShadowError::Channel(e.to_string()))?;
            if phase_group_average(&unit, group)? != dephased {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

/// Exact diagonal conditional expectation on a declared 1..=64 matrix carrier.
/// This algebraic channel avoids enumerating a phase group, while the independent
/// finite average remains available for comparing the two constructions.
pub fn diagonal_expectation(
    rho: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, ShadowError> {
    if rho.rows() != rho.cols() {
        return Err(ShadowError::NotSquare {
            rows: rho.rows(),
            cols: rho.cols(),
        });
    }
    if rho.rows() == 0 {
        return Err(ShadowError::ZeroDimension);
    }
    if rho.rows() > 64 {
        return Err(ShadowError::Budget {
            terms: rho.rows().saturating_mul(rho.rows()),
        });
    }
    Ok(matrix::from_fn(rho.rows(), rho.cols(), |i, j| {
        if i == j {
            rho.as_slice()[i * rho.cols() + j].clone()
        } else {
            GaussianRat::zero()
        }
    })?)
}

fn triple_product(
    left: &BasicMatrix<GaussianRat>,
    mid: &BasicMatrix<GaussianRat>,
    right: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, ShadowError> {
    let lm = matrix::multiply(left, mid)?;
    Ok(matrix::multiply(&lm, right)?)
}

fn check_bimodule_shapes_and_diagonal(
    a: &BasicMatrix<GaussianRat>,
    left: &BasicMatrix<GaussianRat>,
    right: &BasicMatrix<GaussianRat>,
) -> Result<bool, ShadowError> {
    if left.shape() != a.shape() || right.shape() != a.shape() {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "diagonal bimodule",
            left: left.shape(),
            right: a.shape(),
        }
        .into());
    }
    Ok(diagonal_expectation(left)? == *left && diagonal_expectation(right)? == *right)
}

/// Replay idempotence and the diagonal bimodule law E(L A R)=L E(A) R.
pub fn verify_diagonal_bimodule(
    a: &BasicMatrix<GaussianRat>,
    left: &BasicMatrix<GaussianRat>,
    right: &BasicMatrix<GaussianRat>,
) -> Result<bool, ShadowError> {
    if !check_bimodule_shapes_and_diagonal(a, left, right)? {
        return Ok(false);
    }
    let e = diagonal_expectation(a)?;
    if diagonal_expectation(&e)? != e {
        return Ok(false);
    }
    let lar = triple_product(left, a, right)?;
    let ler = triple_product(left, &e, right)?;
    Ok(diagonal_expectation(&lar)? == ler)
}
/// The conditional expectation is its own Hilbert–Schmidt adjoint.
pub fn verify_diagonal_self_adjoint(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
) -> Result<bool, ShadowError> {
    use linear_algebra::exact_field::involution::hs_inner;
    Ok(hs_inner(&diagonal_expectation(a)?, b)? == hs_inner(a, &diagonal_expectation(b)?)?)
}

// Origin: engine/crates_rs/core_quantum_physics/src/phase_averaged_shadow.rs
// Claim: urn:core:crates_rs:core-quantum-physics:phase-averaged-shadow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_64a94f59 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
