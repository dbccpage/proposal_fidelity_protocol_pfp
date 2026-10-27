// AuthorityEffect: None.

//! A CPTP map carrying one state difference onto another of no larger trace
//! norm, and the embedding pair that ties dimensions together.
//!
//! For trace-zero Hermitian `X != 0` and `Y` on `C^n` with `||Y||_1 <= ||X||_1`,
//! both given through a `trace_norm_certificate::SignCertificate`, put
//! `t = ||X||_1 / 2`, `s = ||Y||_1 / 2`, `P = (I + S_X) / 2`,
//! `A = (Y_+ + (t - s) I / n) / t` and `B = (Y_- + (t - s) I / n) / t`.
//! The measure-and-prepare map `Z -> Tr(PZ) A + Tr((I - P)Z) B` has Choi matrix
//! `P^T (x) A + (I - P)^T (x) B` (input factor first, as in `exact_channel`):
//! it is PSD because the four factors are, and `Tr_out` of it is `I` because
//! `A` and `B` are states. Since `P X_+ = X_+` and `P X_- = 0`, it sends `X`
//! to `tA - tB = Y`. The Choi matrix is built exactly; `exact_channel` applies
//! it and decides that it is CPTP.
//!
//! Consequence of the construction: a functional `j` on trace-zero differences
//! that never increases under CPTP maps `M_n -> M_n` has `j(Y) <= j(X)` whenever
//! `||Y||_1 <= ||X||_1`. So `j` is a nondecreasing function of the trace norm,
//! and an absolutely homogeneous `j` is `c ||.||_1`: CPTP monotonicity leaves
//! exactly one free scale, never a second norm. [`embedding_pair`] gives the
//! inclusion `C^n -> C^m` and a CPTP left inverse of it, which force one scale
//! for all dimensions.
//!
//! Refused: dimension mismatch, a matrix that is not trace-zero, `X = 0`, and
//! `||Y||_1 > ||X||_1` (no CPTP map increases the trace norm of a difference).

use crate::exact_channel::{apply_choi, ExactChannelError, ExactChoiMatrix, ExactKrausChannel};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution, matrix};
use num_traits::Zero;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

use crate::trace_norm_certificate::SignCertificate;

/// Refusals for difference transport.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DifferenceTransportError {
    #[error(transparent)]
    TraceNorm(#[from] crate::trace_norm_certificate::TraceNormError),
    #[error(transparent)]
    ExactAlgebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("source and target act on different dimensions")]
    Dimension,
    #[error("source or target is not trace-zero")]
    NotTraceZero,
    #[error("the source difference is zero")]
    ZeroSource,
    /// `(source, target)` trace norms, the target's larger.
    #[error("target trace norm exceeds source trace norm: {0:?}")]
    Expanding(Box<(Rational, Rational)>),
    #[error("embedding needs 1 <= n <= m")]
    Embedding,
    #[error("the channel construction exceeds its matrix storage budget")]
    StorageBudget,
    #[error("the constructed channel failed the exact source-to-target replay")]
    Replay,
    #[error("channel refused: {0}")]
    Channel(#[from] ExactChannelError),
}

/// The measure-and-prepare map sending a source difference to a target one.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DifferenceTransport {
    choi: BasicMatrix<GaussianRat>,
    helstrom_effect: BasicMatrix<GaussianRat>,
    dim: usize,
}

impl DifferenceTransport {
    pub fn new(
        source: &SignCertificate,
        target: &SignCertificate,
    ) -> Result<Self, DifferenceTransportError> {
        let (n, t, s) = Self::validate_certificates(source, target)?;
        let (a, b) = Self::build_slack_targets(target, n, &t, &s)?;
        let p = source.helstrom_effect()?;
        let choi = Self::build_transport_choi(n, &p, &a, &b)?;
        let verified = ExactChoiMatrix::try_new(n, n, choi)?;
        if verified.apply(source.matrix())? != *target.matrix() {
            return Err(DifferenceTransportError::Replay);
        }
        Ok(Self {
            choi: verified.matrix().clone(),
            helstrom_effect: p,
            dim: n,
        })
    }

    fn validate_certificates(
        source: &SignCertificate,
        target: &SignCertificate,
    ) -> Result<(usize, Rational, Rational), DifferenceTransportError> {
        let (x, y) = (source.matrix(), target.matrix());
        let n = x.rows();
        if n > 8 {
            return Err(DifferenceTransportError::StorageBudget);
        }
        if y.rows() != n {
            return Err(DifferenceTransportError::Dimension);
        }
        if !matrix::trace(&x)?.is_zero() || !matrix::trace(&y)?.is_zero() {
            return Err(DifferenceTransportError::NotTraceZero);
        }
        let t = source.trace_norm() / ri(2);
        let s = target.trace_norm() / ri(2);
        if t.is_zero() {
            return Err(DifferenceTransportError::ZeroSource);
        }
        if s > t {
            return Err(DifferenceTransportError::Expanding(Box::new((
                source.trace_norm(),
                target.trace_norm(),
            ))));
        }
        Ok((n, t, s))
    }

    fn build_slack_targets(
        target: &SignCertificate,
        n: usize,
        t: &Rational,
        s: &Rational,
    ) -> Result<(BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>), DifferenceTransportError>
    {
        let slack = matrix::scale(
            &matrix::identity(n)?,
            &GaussianRat::from_rational(((t - s) / Rational::from_integer(n.into())).clone()),
        )?;
        let inverse_t = GaussianRat::from_rational(ri(1) / t);
        let a = matrix::scale(&matrix::add(&target.positive_part(), &slack)?, &inverse_t)?;
        let b = matrix::scale(&matrix::add(&target.negative_part(), &slack)?, &inverse_t)?;
        Ok((a, b))
    }

    fn build_transport_choi(
        n: usize,
        p: &BasicMatrix<GaussianRat>,
        a: &BasicMatrix<GaussianRat>,
        b: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, DifferenceTransportError> {
        let complement = matrix::sub(&matrix::identity(n)?, p)?;
        Ok(matrix::add(
            &matrix::kronecker(&matrix::transpose(p)?, a)?,
            &matrix::kronecker(&matrix::transpose(&complement)?, b)?,
        )?)
    }

    pub fn choi(&self) -> &BasicMatrix<GaussianRat> {
        &self.choi
    }

    /// The optimal two-outcome effect for the source difference. On the zero
    /// eigenspace it equals `I/2`; its achieved bias is `||X||_1/2`.
    pub fn helstrom_effect(&self) -> &BasicMatrix<GaussianRat> {
        &self.helstrom_effect
    }

    pub fn dim(&self) -> usize {
        self.dim
    }

    /// The map applied through its Choi matrix.
    pub fn apply(
        &self,
        z: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactChannelError> {
        apply_choi(&self.choi, self.dim, self.dim, z)
    }
}

/// The inclusion `V : C^n -> C^m` as the channel `Z -> V Z V*`, and the CPTP
/// left inverse with Kraus operators `V*` and `|0><k|` for `n <= k < m`.
pub fn embedding_pair(
    n: usize,
    m: usize,
) -> Result<(ExactKrausChannel, ExactKrausChannel), DifferenceTransportError> {
    check_embedding_budget(n, m)?;
    let inclusion = build_inclusion_matrix(n, m)?;
    let mut retraction = vec![involution::adjoint(&inclusion)?];
    for k in n..m {
        let mut discard =
            linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(n, m, |_, _| {
                GaussianRat::zero()
            })?;
        discard.set(0, k, GaussianRat::one())?;
        retraction.push(discard);
    }
    Ok((
        ExactKrausChannel::from_operators(vec![inclusion])?,
        ExactKrausChannel::from_operators(retraction)?,
    ))
}

fn check_embedding_budget(n: usize, m: usize) -> Result<(), DifferenceTransportError> {
    if n == 0 || n > m {
        return Err(DifferenceTransportError::Embedding);
    }
    if m > 128 {
        return Err(DifferenceTransportError::StorageBudget);
    }
    let total = m
        .checked_mul(n)
        .and_then(|entries| entries.checked_mul(m - n + 2))
        .ok_or(DifferenceTransportError::StorageBudget)?;
    if total > 1 << 20 {
        return Err(DifferenceTransportError::StorageBudget);
    }
    Ok(())
}

fn build_inclusion_matrix(
    n: usize,
    m: usize,
) -> Result<BasicMatrix<GaussianRat>, DifferenceTransportError> {
    let mut inclusion =
        linear_algebra::backend::basic_matrix::BasicMatrix::try_from_fn(m, n, |_, _| {
            GaussianRat::zero()
        })?;
    for i in 0..n {
        inclusion.set(i, i, GaussianRat::one())?;
    }
    Ok(inclusion)
}

// Origin: engine/crates_rs/core_quantum_physics/src/difference_transport_channel.rs
// Claim: urn:core:crates_rs:core-quantum-physics:difference-transport-channel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod transport_tests {
    use super::*;
    use crate::exact_hermitian::gq;
    use core_number_theory::rational::rq;
    #[test]
    fn transport_exposes_the_optimal_helstrom_effect_and_replays_the_difference() {
        let x = matrix::from_rows(vec![
            vec![gq(0, 1, 0, 1), gq(0, 1, -1, 1)],
            vec![gq(0, 1, 1, 1), gq(0, 1, 0, 1)],
        ])
        .unwrap();
        let source = SignCertificate::new(x.clone(), x.clone()).unwrap();
        let y = matrix::diagonal(&[
            GaussianRat::from_rational(rq(1, 3)),
            GaussianRat::from_rational(rq(-1, 3)),
        ])
        .unwrap();
        let sign = matrix::diagonal(&[GaussianRat::one(), -GaussianRat::one()]).unwrap();
        let target = SignCertificate::new(y.clone(), sign).unwrap();
        let transport = DifferenceTransport::new(&source, &target).unwrap();
        assert_eq!(transport.apply(&x).unwrap(), y);
        assert_eq!(
            matrix::trace(&matrix::multiply(&transport.helstrom_effect(), &x).unwrap())
                .unwrap()
                .re,
            ri(1)
        );
        assert_eq!(
            matrix::multiply(&transport.helstrom_effect(), transport.helstrom_effect()).unwrap(),
            *transport.helstrom_effect()
        );
        assert!(crate::exact_channel::choi_is_cptp(transport.choi(), 2, 2));
        assert!(matches!(
            embedding_pair(1, usize::MAX),
            Err(DifferenceTransportError::StorageBudget)
        ));
    }
}
