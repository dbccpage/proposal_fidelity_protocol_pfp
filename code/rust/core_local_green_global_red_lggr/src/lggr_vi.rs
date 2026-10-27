//! LGGR VI — Nonlinear aggregation, postprocessing monotonicity, and adjoint Gram probing.
//!
//! Checks over exact $\mathbb{Q}$ arithmetic that:
//! 1. Postprocessing an observation map $Q$ ($p \times n$) by $F$ ($r \times p$) satisfies
//!    $\operatorname{rank}(F \cdot Q) \le \operatorname{rank}(Q)$ ($\ker(Q) \subseteq \ker(F \cdot Q)$).
//! 2. The rational Gram matrix $G = Q^T Q$ has $\operatorname{rank}(G) = \operatorname{rank}(Q)$.
//! 3. Recovering a target linear query $H x$ ($\ker(F \cdot Q) \subseteq \ker(H)$) is distinct
//!    from recovering the full state $x$ ($\operatorname{rank}(F \cdot Q) = n$).
//!
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::Zero;
use core_linear_algebra::backend::basic_matrix::BasicMatrix;
use core_linear_algebra::linear_algebra::image_kernel::ExactRowReduction;
use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::lggr_v::MAX_LGGR_CELLS;

/// Canonical schema for LGGR VI postprocessing and Gram probing reports.
pub const LGGR_VI_PROBING_SCHEMA: &str = "core.epk.lggr-vi-probing.v1";

/// Errors encountered during LGGR VI postprocessing and Gram probing checks.
#[derive(Debug, Clone, PartialEq, Eq, Error, Serialize, Deserialize)]
pub enum LggrViError {
    #[error("BUDGET_UNKNOWN: matrix cell count exceeds limit {limit} (got {cells})")]
    BudgetUnknown { cells: usize, limit: usize },
    #[error("dimension mismatch: {detail}")]
    DimensionMismatch { detail: String },
    #[error("empty matrix")]
    EmptyMatrix,
    #[error("linear algebra computation error: {0}")]
    LinearAlgebra(String),
}

/// Report for LGGR VI postprocessing monotonicity, Gram radical rank, and query recovery.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LggrViProbingReport {
    /// Schema identifier.
    pub schema: String,
    /// Domain dimension $n$ (number of columns of $Q$ and $H$).
    pub state_dim: usize,
    /// Exact rank of $Q$ over $\mathbb{Q}$.
    pub q_rank: usize,
    /// Exact rank of $F \cdot Q$ over $\mathbb{Q}$.
    pub fq_rank: usize,
    /// Exact rank of the Gram matrix $G = Q^T Q$ over $\mathbb{Q}$.
    pub gram_rank: usize,
    /// Exact rank of the target query matrix $H$ over $\mathbb{Q}$.
    pub h_rank: usize,
    /// True iff $\operatorname{rank}(F \cdot Q) \le \operatorname{rank}(Q)$.
    pub postprocessing_rank_monotone: bool,
    /// True iff $\operatorname{rank}(Q^T Q) == \operatorname{rank}(Q)$.
    pub gram_rank_matches_q: bool,
    /// True iff $\ker(F \cdot Q) \subseteq \ker(H)$, so $H x$ is uniquely determined by $F Q x$.
    pub target_query_recoverable: bool,
    /// True iff $\operatorname{rank}(F \cdot Q) == n$, so $x$ itself is uniquely determined by $F Q x$.
    pub full_state_recoverable: bool,
    /// Canonical authority effect: None.
    pub authority_effect: String,
}

fn transpose_rational(m: &BasicMatrix<BigRational>) -> Result<BasicMatrix<BigRational>, LggrViError> {
    let slice = m.as_slice();
    let cols = m.cols();
    BasicMatrix::try_from_fn(m.cols(), m.rows(), |r, c| slice[c * cols + r].clone())
        .map_err(|e| LggrViError::LinearAlgebra(e.to_string()))
}

fn preflight_lggr_vi(
    q: &BasicMatrix<BigRational>,
    f: &BasicMatrix<BigRational>,
    h: &BasicMatrix<BigRational>,
) -> Result<(), LggrViError> {
    if [q, f, h].iter().any(|m| m.rows() == 0 || m.cols() == 0) {
        return Err(LggrViError::EmptyMatrix);
    }
    for cells in [
        q.rows().saturating_mul(q.cols()),
        f.rows().saturating_mul(f.cols()),
        h.rows().saturating_mul(h.cols()),
        q.cols().saturating_mul(q.cols()),
    ] {
        if cells > MAX_LGGR_CELLS {
            return Err(LggrViError::BudgetUnknown {
                cells,
                limit: MAX_LGGR_CELLS,
            });
        }
    }
    if f.cols() != q.rows() {
        return Err(LggrViError::DimensionMismatch {
            detail: format!("F cols ({}) must equal Q rows ({})", f.cols(), q.rows()),
        });
    }
    if h.cols() != q.cols() {
        return Err(LggrViError::DimensionMismatch {
            detail: format!("H cols ({}) must equal Q cols ({})", h.cols(), q.cols()),
        });
    }
    Ok(())
}

fn exact_rank(m: &BasicMatrix<BigRational>) -> Result<usize, LggrViError> {
    m.rank().map_err(|e| LggrViError::LinearAlgebra(e.to_string()))
}

fn is_target_query_recoverable(
    fq: &BasicMatrix<BigRational>,
    h: &BasicMatrix<BigRational>,
) -> Result<bool, LggrViError> {
    // Check ker(F Q) subseteq ker(H) by verifying H v == 0 for every basis vector v of ker(F Q).
    let fq_null = fq
        .kernel_basis()
        .map_err(|e| LggrViError::LinearAlgebra(e.to_string()))?;
    for basis_vec in fq_null.vectors() {
        let hv = h
            .mul_vec(basis_vec)
            .map_err(|e| LggrViError::LinearAlgebra(e.to_string()))?;
        if hv.iter().any(|val| !val.is_zero()) {
            return Ok(false);
        }
    }
    Ok(true)
}

/// Evaluate LGGR VI postprocessing monotonicity, Gram rank, and target-vs-state recoverability.
pub fn check_postprocessing_and_probing(
    q: &BasicMatrix<BigRational>,
    f: &BasicMatrix<BigRational>,
    h: &BasicMatrix<BigRational>,
) -> Result<LggrViProbingReport, LggrViError> {
    preflight_lggr_vi(q, f, h)?;

    let fq = f
        .mul(q)
        .map_err(|e| LggrViError::LinearAlgebra(e.to_string()))?;
    let qt = transpose_rational(q)?;
    let gram = qt
        .mul(q)
        .map_err(|e| LggrViError::LinearAlgebra(e.to_string()))?;

    let q_rank = exact_rank(q)?;
    let fq_rank = exact_rank(&fq)?;
    let gram_rank = exact_rank(&gram)?;
    let h_rank = exact_rank(h)?;
    let target_query_recoverable = is_target_query_recoverable(&fq, h)?;

    let state_dim = q.cols();
    Ok(LggrViProbingReport {
        schema: LGGR_VI_PROBING_SCHEMA.to_owned(),
        state_dim,
        q_rank,
        fq_rank,
        gram_rank,
        h_rank,
        postprocessing_rank_monotone: fq_rank <= q_rank,
        gram_rank_matches_q: gram_rank == q_rank,
        target_query_recoverable,
        full_state_recoverable: fq_rank == state_dim,
        authority_effect: "None".to_owned(),
    })
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/lggr_vi.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:lggr-vi:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn r(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }

    #[test]
    fn recovering_hx_does_not_imply_recovering_full_state_x() {
        // State x in Q^2. Observation Q = [[1, 0], [0, 0]] observes only x_1.
        // Postprocessing F = [[1, 0]] retains x_1.
        // Target query H_1 = [[1, 0]] (asking for x_1) is recoverable from F Q x,
        // even though full state x in Q^2 is NOT recoverable (fq_rank = 1 < 2).
        let q = BasicMatrix::from_row_major(2, 2, vec![r(1), r(0), r(0), r(0)]).unwrap();
        let f = BasicMatrix::from_row_major(1, 2, vec![r(1), r(0)]).unwrap();
        let h1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(0)]).unwrap();

        let rep1 = check_postprocessing_and_probing(&q, &f, &h1).unwrap();
        assert!(rep1.postprocessing_rank_monotone);
        assert!(rep1.gram_rank_matches_q);
        assert_eq!(rep1.q_rank, 1);
        assert_eq!(rep1.fq_rank, 1);
        assert_eq!(rep1.gram_rank, 1);
        assert!(rep1.target_query_recoverable);
        assert!(!rep1.full_state_recoverable);
        assert_eq!(rep1.authority_effect, "None");

        // Target query H_2 = [[0, 1]] (asking for hidden coordinate x_2) is NOT recoverable.
        let h2 = BasicMatrix::from_row_major(1, 2, vec![r(0), r(1)]).unwrap();
        let rep2 = check_postprocessing_and_probing(&q, &f, &h2).unwrap();
        assert!(!rep2.target_query_recoverable);
        assert!(!rep2.full_state_recoverable);
    }
}
