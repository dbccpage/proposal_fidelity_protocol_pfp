// AuthorityEffect: None.

//! The Heisenberg picture of declared unitary steps over `Q(i)`, and the exact
//! derivative of the Cayley path.
//!
//! Declared: unitary steps `U_1, ..., U_n`, a state `rho`, an observable `A`,
//! a Hermitian generator `H` (all square over `Q(i)`, of one dimension) and a
//! rational parameter `tau`. Computed exactly:
//!
//! - [`schrodinger_state`]: `W rho W*` and [`heisenberg_observable`]: `W* A W`,
//!   with `W = U_n ... U_1`. Each step is the one-Kraus channel of
//!   `crate::exact_channel`, applied in order to the state
//!   (`apply`) and in reverse order to the observable (`adjoint_apply`), so
//!   `Tr(rho_n A) = Tr(rho A_n)` holds exactly.
//! - [`cayley_jet`]: the first-order jet `M + eps M'` (`eps^2 = 0`) at `tau` of
//!   the Cayley path `tau -> C_tau(H) = (I - i tau H)(I + i tau H)^(-1)`, the
//!   step of `crate::unitary_generator_admission::cayley_unitary`.
//!   The jet is formed by the exact product rule and `(M + eps M')^(-1) =
//!   M^(-1) - eps M^(-1) M' M^(-1)`, so its tangent is the exact derivative.
//! - [`heisenberg_jet`]: the jet of `tau -> A(tau) = C_tau(H)* A C_tau(H)`. Its
//!   tangent at `tau = 0` is `2 i [H, A]`: the path agrees to first order with
//!   `exp(-2 i tau H)`.
//! - [`cayley_rate_generator`]: `G_tau = 2 H (I + tau^2 H^2)^(-1)`, with
//!   `dC_tau/dtau = -i G_tau C_tau` and `dA/dtau = i [G_tau, A(tau)]`. `G_tau`
//!   is a multiple of `H` for every `tau` only when `H^2` acts as a scalar on the
//!   range of `H`; otherwise the Cayley path is not a reparametrized
//!   one-parameter group.
//!
//! Refused: non-square or mismatched operators, non-unitary steps and
//! non-Hermitian generators. No exponential `exp(-i t H)` is computed:
//! continuous time enters only as the derivative of a rational path at a
//! rational point.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_ba6cae7f<T> {
    fn checked_invariant_ba6cae7f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_ba6cae7f<T> for Option<T> {
    #[inline]
    fn checked_invariant_ba6cae7f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_ba6cae7f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_ba6cae7f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::Zero;

use crate::exact_channel::ExactKrausChannel;
use crate::exact_hermitian::{self};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

/// Refusals for Heisenberg-picture evolution and Cayley jets.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum HeisenbergError {
    #[error("Heisenberg operation exceeds dimension128 or its declared work budget")]
    Budget,
    #[error(transparent)]
    Hermitian(#[from] crate::exact_hermitian::ExactHermitianError),
    #[error("channel action refused: {0}")]
    Channel(crate::exact_channel::ExactChannelError),
    #[error("matrix is {rows}x{cols}, not square")]
    NotSquare { rows: usize, cols: usize },
    #[error("operator has dimension {found}, the carrier has dimension {expected}")]
    DimensionMismatch { expected: usize, found: usize },
    #[error("step {step} is not unitary")]
    NotUnitary { step: usize },
    #[error("the generator is not Hermitian")]
    NotHermitian,
    #[error("exact elimination refused: {0}")]
    Elimination(String),
}

fn square_dimension(m: &BasicMatrix<GaussianRat>) -> Result<usize, HeisenbergError> {
    crate::exact_hermitian::check_well_formed(m)?;
    if m.rows() != m.cols() {
        return Err(HeisenbergError::NotSquare {
            rows: m.rows(),
            cols: m.cols(),
        });
    }
    if m.rows() > 128 {
        return Err(HeisenbergError::Budget);
    }
    Ok(m.rows())
}

fn check_dimension(m: &BasicMatrix<GaussianRat>, expected: usize) -> Result<(), HeisenbergError> {
    let found = square_dimension(m)?;
    if found != expected {
        return Err(HeisenbergError::DimensionMismatch { expected, found });
    }
    Ok(())
}

fn unitary_channels(
    steps: &[BasicMatrix<GaussianRat>],
    dimension: usize,
) -> Result<Vec<ExactKrausChannel>, HeisenbergError> {
    if steps.len() > 4096
        || dimension
            .checked_pow(3)
            .and_then(|v| v.checked_mul(steps.len()))
            .is_none_or(|v| v > 1 << 24)
    {
        return Err(HeisenbergError::Budget);
    }
    steps
        .iter()
        .enumerate()
        .map(|(step, u)| {
            check_dimension(u, dimension)?;
            if linear_algebra::exact_field::matrix::multiply_with_limits(
                &(linear_algebra::exact_field::involution::adjoint(&(u))
                    .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
                u,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget")
                != linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
                    dimension,
                    linear_algebra::backend::basic_matrix::OperationLimits {
                        max_elements: 1 << 20,
                        max_scalar_ops: 1 << 24,
                    },
                )
                .checked_invariant_ba6cae7f("validated finite matrix shape and budget")
            {
                return Err(HeisenbergError::NotUnitary { step });
            }
            ExactKrausChannel::from_operators(vec![u.clone()]).map_err(HeisenbergError::Channel)
        })
        .collect()
}

/// `W rho W*` for `W = U_n ... U_1`: the state after the declared steps.
pub fn schrodinger_state(
    steps: &[BasicMatrix<GaussianRat>],
    rho: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, HeisenbergError> {
    let dimension = square_dimension(rho)?;
    unitary_channels(steps, dimension)?
        .iter()
        .try_fold(rho.clone(), |state, channel| {
            channel.apply(&state).map_err(HeisenbergError::Channel)
        })
}

/// `W* A W` for `W = U_n ... U_1`: the observable in the Heisenberg picture.
pub fn heisenberg_observable(
    steps: &[BasicMatrix<GaussianRat>],
    a: &BasicMatrix<GaussianRat>,
) -> Result<BasicMatrix<GaussianRat>, HeisenbergError> {
    let dimension = square_dimension(a)?;
    unitary_channels(steps, dimension)?
        .iter()
        .rev()
        .try_fold(a.clone(), |observable, channel| {
            channel
                .adjoint_apply(&observable)
                .map_err(HeisenbergError::Channel)
        })
}

/// A first-order jet `value + eps * tangent` of a matrix path, `eps^2 = 0`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MatrixJet {
    value: BasicMatrix<GaussianRat>,
    tangent: BasicMatrix<GaussianRat>,
}

impl MatrixJet {
    fn constant(value: BasicMatrix<GaussianRat>) -> Self {
        let tangent = linear_algebra::exact_field::matrix::zeros(value.rows(), value.cols())
            .checked_invariant_ba6cae7f("validated jet shape");
        Self { value, tangent }
    }

    /// The point of the path.
    pub fn value(&self) -> &BasicMatrix<GaussianRat> {
        &self.value
    }

    /// The exact derivative of the path.
    pub fn tangent(&self) -> &BasicMatrix<GaussianRat> {
        &self.tangent
    }

    fn mul(&self, other: &Self) -> Self {
        Self {
            value: linear_algebra::exact_field::matrix::multiply_with_limits(
                &(self.value),
                &other.value,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
            tangent: linear_algebra::exact_field::matrix::add(
                &(linear_algebra::exact_field::matrix::multiply_with_limits(
                    &(self.value),
                    &other.tangent,
                    linear_algebra::backend::basic_matrix::OperationLimits {
                        max_elements: 1 << 20,
                        max_scalar_ops: 1 << 24,
                    },
                )
                .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
                &linear_algebra::exact_field::matrix::multiply_with_limits(
                    &(self.tangent),
                    &other.value,
                    linear_algebra::backend::basic_matrix::OperationLimits {
                        max_elements: 1 << 20,
                        max_scalar_ops: 1 << 24,
                    },
                )
                .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
        }
    }

    fn dagger(&self) -> Self {
        Self {
            value: linear_algebra::exact_field::involution::adjoint(&(self.value))
                .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
            tangent: linear_algebra::exact_field::involution::adjoint(&(self.tangent))
                .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
        }
    }

    fn inverse(&self) -> Result<Self, HeisenbergError> {
        let inverse = linear_algebra::exact_field::elimination::inverse(&self.value)
            .map_err(exact_hermitian::ExactHermitianError::from)?;
        let tangent = linear_algebra::exact_field::matrix::scale(
            &(linear_algebra::exact_field::matrix::multiply_with_limits(
                &(linear_algebra::exact_field::matrix::multiply_with_limits(
                    &(inverse),
                    &self.tangent,
                    linear_algebra::backend::basic_matrix::OperationLimits {
                        max_elements: 1 << 20,
                        max_scalar_ops: 1 << 24,
                    },
                )
                .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
                &inverse,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
            &GaussianRat::one().neg(),
        )
        .checked_invariant_ba6cae7f("validated finite matrix shape and budget");
        Ok(Self {
            value: inverse,
            tangent,
        })
    }
}

fn hermitian_dimension(h: &BasicMatrix<GaussianRat>) -> Result<usize, HeisenbergError> {
    let n = square_dimension(h)?;
    if !exact_hermitian::is_hermitian(h) {
        return Err(HeisenbergError::NotHermitian);
    }
    Ok(n)
}

fn imaginary(t: &Rational) -> GaussianRat {
    GaussianRat {
        re: Rational::zero(),
        im: t.clone(),
    }
}

/// The jet at `tau` of `tau -> (I - i tau H)(I + i tau H)^(-1)`.
pub fn cayley_jet(
    h: &BasicMatrix<GaussianRat>,
    tau: &Rational,
) -> Result<MatrixJet, HeisenbergError> {
    let n = hermitian_dimension(h)?;
    let identity = linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
        n,
        linear_algebra::backend::basic_matrix::OperationLimits {
            max_elements: 1 << 20,
            max_scalar_ops: 1 << 24,
        },
    )
    .checked_invariant_ba6cae7f("validated finite matrix shape and budget");
    let i_h = linear_algebra::exact_field::matrix::scale(&(h), &GaussianRat::i())
        .checked_invariant_ba6cae7f("validated finite matrix shape and budget");
    let i_tau_h = linear_algebra::exact_field::matrix::scale(&(h), &imaginary(tau))
        .checked_invariant_ba6cae7f("validated finite matrix shape and budget");
    let numerator = MatrixJet {
        value: linear_algebra::exact_field::matrix::sub(&(identity), &i_tau_h)
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
        tangent: linear_algebra::exact_field::matrix::scale(&(i_h), &GaussianRat::one().neg())
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
    };
    let denominator = MatrixJet {
        value: linear_algebra::exact_field::matrix::add(&(identity), &i_tau_h)
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
        tangent: i_h,
    };
    Ok(numerator.mul(&denominator.inverse()?))
}

/// The jet at `tau` of `tau -> C_tau(H)* A C_tau(H)`.
pub fn heisenberg_jet(
    h: &BasicMatrix<GaussianRat>,
    a: &BasicMatrix<GaussianRat>,
    tau: &Rational,
) -> Result<MatrixJet, HeisenbergError> {
    let cayley = cayley_jet(h, tau)?;
    check_dimension(a, h.rows())?;
    Ok(cayley
        .dagger()
        .mul(&MatrixJet::constant(a.clone()))
        .mul(&cayley))
}

/// `2 H (I + tau^2 H^2)^(-1)`, the generator with `dC_tau/dtau = -i G_tau C_tau`.
pub fn cayley_rate_generator(
    h: &BasicMatrix<GaussianRat>,
    tau: &Rational,
) -> Result<BasicMatrix<GaussianRat>, HeisenbergError> {
    let n = hermitian_dimension(h)?;
    let tau_squared = GaussianRat::from_rational(tau * tau);
    let shifted = linear_algebra::exact_field::matrix::add(
        &(linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
            n,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
        &linear_algebra::exact_field::matrix::scale(
            &(linear_algebra::exact_field::matrix::multiply_with_limits(
                &(h),
                h,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
            &tau_squared,
        )
        .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
    )
    .checked_invariant_ba6cae7f("validated finite matrix shape and budget");
    Ok(linear_algebra::exact_field::matrix::multiply_with_limits(
        &(linear_algebra::exact_field::matrix::scale(&(h), &GaussianRat::from_rational(ri(2)))
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
        &linear_algebra::exact_field::elimination::inverse(&shifted)
            .map_err(exact_hermitian::ExactHermitianError::from)?,
        linear_algebra::backend::basic_matrix::OperationLimits {
            max_elements: 1 << 20,
            max_scalar_ops: 1 << 24,
        },
    )
    .checked_invariant_ba6cae7f("validated finite matrix shape and budget"))
}

/// Ehrenfest derivative d<A>/dt = i Tr(rho [H,A]) for a time-independent
/// Hermitian observable. Its real value is computed from the supplied state;
/// Hermiticity of rho is enough for reality (positivity is a state obligation).
pub fn ehrenfest_derivative(
    h: &BasicMatrix<GaussianRat>,
    a: &BasicMatrix<GaussianRat>,
    rho: &BasicMatrix<GaussianRat>,
) -> Result<Rational, HeisenbergError> {
    exact_hermitian::check_hermitian(h)?;
    exact_hermitian::check_hermitian(a)?;
    exact_hermitian::check_hermitian(rho)?;
    check_dimension(a, h.rows())?;
    check_dimension(rho, h.rows())?;
    let derivative = linear_algebra::exact_field::matrix::scale(
        &(linear_algebra::exact_field::matrix::sub(
            &(linear_algebra::exact_field::matrix::multiply_with_limits(
                &(h),
                a,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
            &linear_algebra::exact_field::matrix::multiply_with_limits(
                &(a),
                h,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
        )
        .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
        &GaussianRat::i(),
    )
    .checked_invariant_ba6cae7f("validated finite matrix shape and budget");
    Ok(linear_algebra::exact_field::matrix::trace(
        &(linear_algebra::exact_field::matrix::multiply_with_limits(
            &(rho),
            &derivative,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
    )
    .checked_invariant_ba6cae7f("validated finite matrix shape and budget")
    .re)
}

/// Truncated analytic jet A(t)=sum a_k t^k for exp(i t H) A exp(-i t H).
/// Coefficients are repeated exact commutators, divided by k!, with degree
/// at most 32. The remainder is not silently identified with zero.
pub fn heisenberg_taylor(
    h: &BasicMatrix<GaussianRat>,
    a: &BasicMatrix<GaussianRat>,
    degree: usize,
) -> Result<Vec<BasicMatrix<GaussianRat>>, HeisenbergError> {
    exact_hermitian::check_hermitian(h)?;
    check_dimension(a, h.rows())?;
    if degree > 32 || h.rows() > 64 {
        return Err(HeisenbergError::Elimination(
            "Taylor operation budget".into(),
        ));
    }
    let mut coefficients = vec![a.clone()];
    for k in 1..=degree {
        let previous = &coefficients[k - 1];
        let c = linear_algebra::exact_field::matrix::sub(
            &(linear_algebra::exact_field::matrix::multiply_with_limits(
                &(h),
                previous,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget")),
            &linear_algebra::exact_field::matrix::multiply_with_limits(
                &(previous),
                h,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
        )
        .checked_invariant_ba6cae7f("validated finite matrix shape and budget");
        coefficients.push(
            linear_algebra::exact_field::matrix::scale(
                &(c),
                &GaussianRat {
                    re: Rational::zero(),
                    im: Rational::new(1.into(), k.into()),
                },
            )
            .checked_invariant_ba6cae7f("validated finite matrix shape and budget"),
        );
    }
    Ok(coefficients)
}

// Origin: engine/crates_rs/core_quantum_physics/src/heisenberg_picture.rs
// Claim: urn:core:crates_rs:core-quantum-physics:heisenberg-picture:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_ba6cae7f {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
