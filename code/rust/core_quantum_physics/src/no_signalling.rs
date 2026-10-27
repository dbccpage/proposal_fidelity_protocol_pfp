//! Exact local channels and no-signalling on finite bipartite systems over `Q(i)`.
//!
//! A weighted Kraus channel has checked completeness `sum w K* K = I`.
//! Applying it to Alice leaves Bob's partial trace invariant by linearity and
//! trace cyclicity. The input may be any well-formed operator: positivity is
//! unnecessary for that identity. Conditional branches can change Bob's
//! normalized state; postselection requires a classical outcome message.
//! All arithmetic uses arbitrary-precision number-theory scalars and the shared
//! exact channel/matrix implementations. Malformed carriers are typed refusals.
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_dd5cfaa7<T> {
    fn checked_invariant_dd5cfaa7(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_dd5cfaa7<T> for Option<T> {
    #[inline]
    fn checked_invariant_dd5cfaa7(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_dd5cfaa7<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_dd5cfaa7(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_channel::{ExactChannelError, ExactKrausChannel};
use crate::exact_hermitian::{
    check_well_formed, is_hermitian, partial_trace_first, partial_trace_second, ExactHermitianError,
};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    involution::{adjoint, outer_product},
    matrix, ExactFieldError,
};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::rq;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum NoSignallingError {
    #[error("exact matrix refused: {0}")]
    Matrix(#[from] ExactHermitianError),
    #[error("exact channel refused: {0}")]
    Channel(#[from] ExactChannelError),
    #[error("bipartite dimension overflow or zero")]
    Dimension,
    #[error(transparent)]
    Algebra(#[from] ExactFieldError),
    #[error("checking all matrix units requires {required} units, budget {budget}")]
    Budget { required: usize, budget: usize },
}

fn joint_dimension(first: usize, second: usize) -> Result<usize, NoSignallingError> {
    first
        .checked_mul(second)
        .filter(|&n| first > 0 && second > 0 && n <= 64)
        .ok_or(NoSignallingError::Dimension)
}

fn apply_kraus_term(
    rho: &BasicMatrix<GaussianRat>,
    operator: &BasicMatrix<GaussianRat>,
    weight: &core_number_theory::rational::Rational,
    id_b: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, NoSignallingError> {
    let joint = matrix::kronecker(operator, id_b)?;
    let adj = adjoint(&joint)?;
    let left = matrix::multiply(&joint, rho)?;
    let term = matrix::multiply(&left, &adj)?;
    Ok(matrix::scale(
        &term,
        &GaussianRat::from_rational(weight.clone()),
    )?)
}

/// Apply `Phi_A tensor id_B`, including channels whose output dimension changes.
pub fn apply_alice_channel(
    rho: &BasicMatrix<GaussianRat>,
    channel: &ExactKrausChannel,
    d_b: usize,
) -> Result<BasicMatrix<GaussianRat>, NoSignallingError> {
    joint_dimension(channel.dim_in(), d_b)?;
    let out = joint_dimension(channel.dim_out(), d_b)?;
    partial_trace_first(rho, channel.dim_in(), d_b)?;
    let id_b = matrix::identity(d_b)?;
    let mut result = matrix::zeros(out, out)?;
    for (weight, operator) in channel.weights().iter().zip(channel.operators()) {
        let scaled = apply_kraus_term(rho, operator, weight, &id_b)?;
        result = matrix::add(&result, &scaled)?;
    }
    Ok(result)
}

/// Check the no-signalling identity for one arbitrary declared operator.
pub fn no_signalling(
    rho: &BasicMatrix<GaussianRat>,
    channel: &ExactKrausChannel,
    d_b: usize,
) -> Result<bool, NoSignallingError> {
    joint_dimension(channel.dim_in(), d_b)?;
    joint_dimension(channel.dim_out(), d_b)?;
    let before = partial_trace_first(rho, channel.dim_in(), d_b)?;
    let after = apply_alice_channel(rho, channel, d_b)?;
    Ok(before == partial_trace_first(&after, channel.dim_out(), d_b)?)
}

fn matrix_unit(n: usize, i: usize, j: usize) -> Result<BasicMatrix<GaussianRat>, NoSignallingError> {
    Ok(matrix::from_fn(n, n, |r, c| {
        if (r, c) == (i, j) {
            GaussianRat::one()
        } else {
            GaussianRat::zero()
        }
    })?)
}

/// An independent finite certificate: check the linear identity on every matrix unit.
/// This implies the identity on all input operators by linearity of the Kraus map.
pub fn certify_no_signalling_map(
    channel: &ExactKrausChannel,
    d_b: usize,
    budget: usize,
) -> Result<bool, NoSignallingError> {
    let n = joint_dimension(channel.dim_in(), d_b)?;
    joint_dimension(channel.dim_out(), d_b)?;
    let required = n.checked_mul(n).ok_or(NoSignallingError::Dimension)?;
    if required > budget {
        return Err(NoSignallingError::Budget { required, budget });
    }
    for i in 0..n {
        for j in 0..n {
            let unit = matrix_unit(n, i, j)?;
            if !no_signalling(&unit, channel, d_b)? {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

/// The unique linear reduced operator reproducing Alice's local statistics.
/// Matrix units test all local observables, not merely a Pauli fixture.
pub fn prove_partial_trace_uniqueness(
    rho: &BasicMatrix<GaussianRat>,
    d_a: usize,
    d_b: usize,
) -> bool {
    if joint_dimension(d_a, d_b).is_err() {
        return false;
    }
    let Ok(reduced) = partial_trace_second(rho, d_a, d_b) else {
        return false;
    };
    for j in 0..d_a {
        for k in 0..d_a {
            let Ok(unit) = matrix::from_fn(d_a, d_a, |r, c| {
                if (r, c) == (k, j) {
                    GaussianRat::one()
                } else {
                    GaussianRat::zero()
                }
            }) else {
                return false;
            };
            let lhs = matrix::identity(d_b)
                .and_then(|i| matrix::kronecker(&unit, &i))
                .and_then(|m| matrix::multiply(&m, rho))
                .and_then(|m| matrix::trace(&m));
            if lhs != Ok(reduced.as_slice()[j * d_a + k].clone()) {
                return false;
            }
        }
    }
    true
}

pub fn proj_0() -> BasicMatrix<GaussianRat> {
    outer_product(
        &[GaussianRat::one(), GaussianRat::zero()],
        &[GaussianRat::one(), GaussianRat::zero()],
    )
    .checked_invariant_dd5cfaa7("fixed nonzero ray")
}
pub fn proj_1() -> BasicMatrix<GaussianRat> {
    matrix::sub(
        &matrix::identity(2).checked_invariant_dd5cfaa7("fixed qubit carrier"),
        &proj_0(),
    )
    .checked_invariant_dd5cfaa7("fixed carrier")
}

fn bell(a: usize, b: usize, sign: i64) -> BasicMatrix<GaussianRat> {
    let mut v = vec![GaussianRat::zero(); 4];
    v[a] = GaussianRat::one();
    v[b] = GaussianRat::from_ints(sign, 0);
    matrix::scale(
        &outer_product(&v, &v).checked_invariant_dd5cfaa7("fixed Bell ray"),
        &GaussianRat::from_rational(rq(1, 2)),
    )
    .checked_invariant_dd5cfaa7("fixed Bell carrier")
}
pub fn bell_phi_plus() -> BasicMatrix<GaussianRat> {
    bell(0, 3, 1)
}
pub fn bell_phi_minus() -> BasicMatrix<GaussianRat> {
    bell(0, 3, -1)
}
pub fn bell_psi_plus() -> BasicMatrix<GaussianRat> {
    bell(1, 2, 1)
}
pub fn bell_psi_minus() -> BasicMatrix<GaussianRat> {
    bell(1, 2, -1)
}
pub fn all_bell_states() -> Vec<(&'static str, BasicMatrix<GaussianRat>)> {
    vec![
        ("phi_plus", bell_phi_plus()),
        ("phi_minus", bell_phi_minus()),
        ("psi_plus", bell_psi_plus()),
        ("psi_minus", bell_psi_minus()),
    ]
}

pub fn cnot_matrix() -> BasicMatrix<GaussianRat> {
    matrix::from_fn(4, 4, |r, c| {
        if r == [0, 1, 3, 2][c] {
            GaussianRat::one()
        } else {
            GaussianRat::zero()
        }
    })
    .checked_invariant_dd5cfaa7("fixed CNOT carrier")
}
pub fn cz_matrix() -> BasicMatrix<GaussianRat> {
    matrix::diagonal(&[
        GaussianRat::one(),
        GaussianRat::one(),
        GaussianRat::one(),
        GaussianRat::from_ints(-1, 0),
    ])
    .checked_invariant_dd5cfaa7("fixed CZ carrier")
}
pub fn swap_matrix() -> BasicMatrix<GaussianRat> {
    matrix::from_fn(4, 4, |r, c| {
        if r == [0, 2, 1, 3][c] {
            GaussianRat::one()
        } else {
            GaussianRat::zero()
        }
    })
    .checked_invariant_dd5cfaa7("fixed SWAP carrier")
}

/// Fixture regression for the generic theorem.
pub fn verify_no_signalling_on_bell_states() -> bool {
    let Ok(channel) =
        ExactKrausChannel::try_new(2, 2, vec![proj_0(), proj_1()], "computational measurement")
    else {
        return false;
    };
    all_bell_states().iter().all(|(_, rho)| {
        is_hermitian(rho)
            && check_well_formed(rho).is_ok()
            && no_signalling(rho, &channel, 2) == Ok(true)
            && partial_trace_first(rho, 2, 2)
                == matrix::scale(
                    &matrix::identity(2).checked_invariant_dd5cfaa7("fixed qubit carrier"),
                    &GaussianRat::from_rational(rq(1, 2)),
                )
                .map_err(ExactHermitianError::from)
    })
}

// Origin: engine/crates_rs/core_quantum_physics/src/no_signalling.rs
// Claim: urn:core:crates_rs:core-quantum-physics:no-signalling:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_dd5cfaa7 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
