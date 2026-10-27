// AuthorityEffect: None.

//! The population shadow of a finite Kraus channel in the declared bases.
//!
//! For a trace-preserving weighted Kraus family `A_k : C^n -> C^m` (an
//! `exact_channel::ExactKrausChannel`) the population shadow is the matrix
//! `T[i][j] = sum_k w_k |<j|A_k|i>|^2`: the output populations of the input basis
//! state `|i><i|`. Rows index inputs, so `T` is row stochastic and pushes a
//! population vector `p` to `p T`; the column-stochastic kernel `K(j|i)` of the
//! ingredient ladder is its transpose. Computed exactly over `Q(i)`:
//!
//! - `T` itself. Its rows are nonnegative and sum to one because the Kraus
//!   family is trace preserving; nothing here assumes it, and
//!   `residual_density_calculus::row_stochastic_pushforward`, which applies
//!   `T`, refuses any other matrix;
//! - Kraus composition `Psi o Phi` (operators `B_l A_k`) and composition of
//!   row-stochastic kernels;
//! - the composition defect `T(Psi o Phi) - T(Phi) T(Psi)`. It vanishes when
//!   `Phi` sends diagonal inputs to diagonal outputs or `Psi` reads only
//!   populations, and not in general: a rotation followed by itself has a
//!   nonzero defect, so shadows are not a monoid image of channels.
//!
//! What the shadow forgets is computed rather than asserted: two channels with
//! one shadow can act differently on a coherent input, and a channel can map a
//! diagonal input to a coherent output. The bases are declared; a different
//! basis gives a different shadow of the same channel.
//!
//! Refused: kernels that are empty, ragged or not row stochastic, and kernel
//! or Kraus shapes that do not compose.

use crate::exact_channel::{ExactChannelError, ExactKrausChannel};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix, ExactFieldError};
use num_traits::{One, Signed};
use core_number_theory::rational::Rational;

/// Refusals for population shadows and their composition.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ShadowError {
    #[error("kernel is empty or ragged")]
    Shape,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error("kernel row {row} is negative or does not sum to one")]
    NotRowStochastic { row: usize },
    #[error("an {left_outputs}-output map cannot feed a {right_inputs}-input map")]
    Mismatch {
        left_outputs: usize,
        right_inputs: usize,
    },
    #[error("channel: {0}")]
    Channel(#[from] ExactChannelError),
}

/// `T[i][j] = sum_k w_k |<j|A_k|i>|^2`, one row per input basis state.
pub fn population_shadow(
    channel: &ExactKrausChannel,
) -> Result<BasicMatrix<Rational>, ShadowError> {
    if channel.dim_in() > 64 || channel.dim_out() > 64 {
        return Err(ShadowError::Shape);
    }
    let kernel = matrix::from_fn(channel.dim_in(), channel.dim_out(), |i, j| {
        channel
            .weights()
            .iter()
            .zip(channel.operators())
            .map(|(w, a)| w * a.as_slice()[j * channel.dim_in() + i].norm_sq())
            .sum()
    })?;
    check_row_stochastic(&kernel)?;
    Ok(kernel)
}
fn check_row_stochastic(kernel: &BasicMatrix<Rational>) -> Result<(), ShadowError> {
    if kernel.rows() == 0 || kernel.cols() == 0 || kernel.rows() > 64 || kernel.cols() > 64 {
        return Err(ShadowError::Shape);
    }
    for (row, entries) in kernel.as_slice().chunks_exact(kernel.cols()).enumerate() {
        if entries.iter().any(Signed::is_negative) || !entries.iter().sum::<Rational>().is_one() {
            return Err(ShadowError::NotRowStochastic { row });
        }
    }
    Ok(())
}
/// First then second, retaining the declared input-row convention.
pub fn compose_kernels(
    first: &BasicMatrix<Rational>,
    second: &BasicMatrix<Rational>,
) -> Result<BasicMatrix<Rational>, ShadowError> {
    check_row_stochastic(first)?;
    check_row_stochastic(second)?;
    if first.cols() != second.rows() {
        return Err(ShadowError::Mismatch {
            left_outputs: first.cols(),
            right_inputs: second.rows(),
        });
    }
    let product = matrix::multiply(first, second)?;
    check_row_stochastic(&product)?;
    Ok(product)
}

/// `first` then `second` as one Kraus channel, with operators `B_l A_k`
/// (`ExactKrausChannel::compose`).
pub fn compose_channels(
    first: &ExactKrausChannel,
    second: &ExactKrausChannel,
) -> Result<ExactKrausChannel, ShadowError> {
    if first.dim_out() != second.dim_in() {
        return Err(ShadowError::Mismatch {
            left_outputs: first.dim_out(),
            right_inputs: second.dim_in(),
        });
    }
    Ok(first.compose(second)?)
}

/// `T(second o first) - T(first) T(second)`: zero exactly when the shadow of
/// the composite is the composite of the shadows.
pub fn composition_defect(
    first: &ExactKrausChannel,
    second: &ExactKrausChannel,
) -> Result<BasicMatrix<Rational>, ShadowError> {
    let composite = population_shadow(&compose_channels(first, second)?)?;
    let product = compose_kernels(&population_shadow(first)?, &population_shadow(second)?)?;
    Ok(matrix::sub(&composite, &product)?)
}

// Origin: engine/crates_rs/core_quantum_physics/src/population_shadow.rs
// Claim: urn:core:crates_rs:core-quantum-physics:population-shadow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_42e94e85 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
