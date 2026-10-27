//! LGGR V — Soundness check and unsoundness witness.
//!
//! # Soundness Invariant
//!
//! Let $D$ be the carrier difference operator ($m \times n$) and $Q$ be the observer
//! quotient projection ($p \times m$).
//! Soundness holds iff $\operatorname{im}(D) \cap \ker(Q) = \{0\}$.
//! By the dimension formula, this is algebraically equivalent to:
//!
//! \[
//! \operatorname{rank}(Q \cdot D) = \operatorname{rank}(D)
//! \]
//!
//! Over $\mathbb{Q}$, this rank equality is computed exactly via Bareiss / Gauss–Jordan
//! exact row reduction without any numerical tolerance or floating-point approximations.
//!
//! # Unsoundness Witness
//!
//! When $\operatorname{rank}(Q \cdot D) < \operatorname{rank}(D)$, the system is unsound.
//! There exists an unsoundness witness vector $v \in \mathbb{Q}^n$ such that:
//!
//! \[
//! D v \neq 0 \quad \text{and} \quad Q D v = 0
//! \]
//!
//! That is, $v \in \ker(Q \cdot D)$ but $v \notin \ker(D)$, proving that the unobservable
//! non-trivial state $D v$ is invisible to the observer $Q$.
//!
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::{One, Zero};
use core_linear_algebra::backend::basic_matrix::BasicMatrix;
use core_linear_algebra::linear_algebra::image_kernel::{ExactRowReduction, RankRref};
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Maximum cells in each input and in the declared QD product profile.
/// This bounds element counts, not rational bit sizes or total runtime.
pub const MAX_LGGR_CELLS: usize = 4096;

/// Canonical schema for LGGR V soundness report.
pub const LGGR_SOUNDNESS_SCHEMA: &str = "core.epk.lggr-soundness.v1";

/// Errors encountered during the LGGR V soundness check.
#[derive(Debug, Clone, PartialEq, Eq, Error, Serialize, Deserialize)]
pub enum LggrSoundnessError {
    #[error("BUDGET_UNKNOWN: matrix cell count exceeds limit {limit} (got {cells})")]
    BudgetUnknown { cells: usize, limit: usize },
    #[error("dimension mismatch: Q cols ({q_cols}) must match D rows ({d_rows})")]
    DimensionMismatch { q_cols: usize, d_rows: usize },
    #[error("empty matrix")]
    EmptyMatrix,
    #[error("linear algebra computation error: {0}")]
    LinearAlgebra(String),
}

/// The exact soundness verdict report for LGGR V.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LggrSoundnessReport {
    /// True iff rank(Q·D) == rank(D).
    pub sound: bool,
    /// Exact rank of D over ℚ.
    pub d_rank: usize,
    /// Exact rank of Q·D over ℚ.
    pub qd_rank: usize,
    /// If unsound, an exact witness vector v in ℚ^n with D v != 0 and Q D v == 0.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub witness: Option<Vec<BigRational>>,
    /// Canonical authority effect: None.
    pub authority_effect: String,
}

impl LggrSoundnessReport {
    pub fn is_sound(&self) -> bool {
        self.sound
    }

    pub fn witness(&self) -> Option<&[BigRational]> {
        self.witness.as_deref()
    }
}

fn matrix_cells(rows: usize, cols: usize) -> Result<usize, LggrSoundnessError> {
    if rows == 0 || cols == 0 {
        return Err(LggrSoundnessError::EmptyMatrix);
    }
    rows.checked_mul(cols).ok_or_else(|| {
        LggrSoundnessError::LinearAlgebra("matrix cell count overflows usize".into())
    })
}

fn require_cell_budget(cells: usize) -> Result<(), LggrSoundnessError> {
    if cells > MAX_LGGR_CELLS {
        return Err(LggrSoundnessError::BudgetUnknown {
            cells,
            limit: MAX_LGGR_CELLS,
        });
    }
    Ok(())
}

fn preflight_soundness(
    d: &BasicMatrix<BigRational>,
    q: &BasicMatrix<BigRational>,
) -> Result<(), LggrSoundnessError> {
    let d_cells = matrix_cells(d.rows(), d.cols())?;
    let q_cells = matrix_cells(q.rows(), q.cols())?;
    require_cell_budget(d_cells.max(q_cells))?;
    if q.cols() != d.rows() {
        return Err(LggrSoundnessError::DimensionMismatch {
            q_cols: q.cols(),
            d_rows: d.rows(),
        });
    }

    let qd_cells = matrix_cells(q.rows(), d.cols())?;
    require_cell_budget(qd_cells)
}

/// Decide LGGR V soundness: rank(Q·D) == rank(D).
///
/// Both inputs and QD's shape are admitted before arithmetic. If unsound, the
/// report carries an exact witness `v` with `D v != 0` and `Q D v == 0`.
pub fn check_soundness(
    d: &BasicMatrix<BigRational>,
    q: &BasicMatrix<BigRational>,
) -> Result<LggrSoundnessReport, LggrSoundnessError> {
    preflight_soundness(d, q)?;
    let qd = q
        .checked_mul_with_limit(d, MAX_LGGR_CELLS)
        .map_err(|e| LggrSoundnessError::LinearAlgebra(e.to_string()))?;
    let d_rank = d
        .rank()
        .map_err(|e| LggrSoundnessError::LinearAlgebra(e.to_string()))?;
    let qd_reduction = qd
        .rank_and_rref()
        .map_err(|e| LggrSoundnessError::LinearAlgebra(e.to_string()))?;
    let qd_rank = qd_reduction.rank();

    if qd_rank == d_rank {
        Ok(LggrSoundnessReport {
            sound: true,
            d_rank,
            qd_rank,
            witness: None,
            authority_effect: "None".to_string(),
        })
    } else {
        let witness = first_unsoundness_witness(d, &qd_reduction)?.ok_or_else(|| {
            LggrSoundnessError::LinearAlgebra(
                "rank(QD) < rank(D) but no basis vector of ker(QD) outside ker(D) found"
                    .to_string(),
            )
        })?;

        Ok(LggrSoundnessReport {
            sound: false,
            d_rank,
            qd_rank,
            witness: Some(witness),
            authority_effect: "None".to_string(),
        })
    }
}

fn first_unsoundness_witness(
    d: &BasicMatrix<BigRational>,
    reduction: &RankRref<BigRational>,
) -> Result<Option<Vec<BigRational>>, LggrSoundnessError> {
    let mut is_pivot = vec![false; d.cols()];
    for &pivot in reduction.pivot_columns() {
        is_pivot[pivot] = true;
    }
    // Same basis order as kernel_basis(), retaining only one candidate at a time.
    for free in 0..d.cols() {
        if is_pivot[free] {
            continue;
        }
        let mut witness = vec![BigRational::zero(); d.cols()];
        witness[free] = BigRational::one();
        for (row, &pivot) in reduction.pivot_columns().iter().enumerate() {
            witness[pivot] = -reduction
                .rref()
                .get(row, free)
                .map_err(|e| LggrSoundnessError::LinearAlgebra(e.to_string()))?;
        }
        let image = d
            .checked_mul_vec_with_limit(&witness, MAX_LGGR_CELLS)
            .map_err(|e| LggrSoundnessError::LinearAlgebra(e.to_string()))?;
        if image.iter().any(|entry| !entry.is_zero()) {
            return Ok(Some(witness));
        }
    }
    Ok(None)
}

/// Verify that a candidate witness satisfies the exact unsoundness condition:
/// `D·v != 0` and `Q·D·v == 0`.
///
/// Uses the decision API's input/product-shape admission profile before checking
/// witness length or value. Oversized or malformed shapes return a typed error;
/// an invalid witness on an admitted shape returns false. Q(Dv) avoids forming QD.
pub fn verify_unsoundness_witness(
    d: &BasicMatrix<BigRational>,
    q: &BasicMatrix<BigRational>,
    witness: &[BigRational],
) -> Result<bool, LggrSoundnessError> {
    preflight_soundness(d, q)?;
    if witness.len() != d.cols() {
        return Ok(false);
    }
    let dv = d
        .checked_mul_vec_with_limit(witness, MAX_LGGR_CELLS)
        .map_err(|e| LggrSoundnessError::LinearAlgebra(e.to_string()))?;
    let dv_nonzero = dv.iter().any(|v| !v.is_zero());
    if !dv_nonzero {
        return Ok(false);
    }
    let qdv = q
        .checked_mul_vec_with_limit(&dv, MAX_LGGR_CELLS)
        .map_err(|e| LggrSoundnessError::LinearAlgebra(e.to_string()))?;
    let qdv_zero = qdv.iter().all(|v| v.is_zero());
    Ok(dv_nonzero && qdv_zero)
}

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/lggr_v.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:lggr-v:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    use num_traits::One;

    fn r(n: i64, d: i64) -> BigRational {
        BigRational::new(BigInt::from(n), BigInt::from(d))
    }

    #[test]
    fn exact_soundness_sound_case() {
        // D is 2x2 identity, Q is 2x2 identity.
        // rank(D) = 2, rank(Q·D) = 2 -> sound.
        let d =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let q =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();

        let report = check_soundness(&d, &q).unwrap();
        assert!(report.is_sound());
        assert_eq!(report.d_rank, 2);
        assert_eq!(report.qd_rank, 2);
        assert!(report.witness.is_none());
    }

    #[test]
    fn exact_soundness_unsound_with_witness() {
        // D is 2x2 identity: rank(D) = 2.
        // Q is 1x2 projection [1, -1]: ker(Q) is span((1, 1)).
        // Q·D = [1, -1], rank(Q·D) = 1.
        // Unsound! Witness v in ker(Q·D) with D·v != 0.
        // (1, 1) has D·(1, 1) = (1, 1) != 0, and Q·D·(1, 1) = 0.
        let d =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let q = BasicMatrix::from_row_major(1, 2, vec![r(1, 1), r(-1, 1)]).unwrap();

        let report = check_soundness(&d, &q).unwrap();
        assert!(!report.is_sound());
        assert_eq!(report.d_rank, 2);
        assert_eq!(report.qd_rank, 1);
        let witness = report.witness.as_ref().expect("unsound must carry witness");
        assert_eq!(witness.len(), 2);

        // Verify witness satisfies D·v != 0 and Q·D·v == 0
        let valid = verify_unsoundness_witness(&d, &q, witness).unwrap();
        assert!(valid, "witness must be valid");
    }

    #[test]
    fn witness_break_floating_point_rounding() {
        // Tiny rational entry: 1 / 10^30
        // In f64, 1.0 + 1e-30 rounds to 1.0.
        // Matrix:
        // D = [[1, 0], [0, 1]] (rank 2)
        // Q = [[1, 1], [1, 1 + 1/10^30]]
        // Exactly: det(Q) = 1 + 1/10^30 - 1 = 1/10^30 != 0 -> Q is invertible!
        // rank(Q·D) = 2 == rank(D) -> SOUND.
        // Under f64, Q is [[1, 1], [1, 1]], which has rank 1 -> would incorrectly declare unsound!
        let tiny = BigRational::new(BigInt::one(), BigInt::from(10).pow(30));
        let d =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let q = BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(1, 1), r(1, 1), r(1, 1) + tiny])
            .unwrap();

        let report = check_soundness(&d, &q).unwrap();
        assert!(report.is_sound(), "exact arithmetic must recognize rank 2");
        assert_eq!(report.d_rank, 2);
        assert_eq!(report.qd_rank, 2);
    }

    #[test]
    fn oversize_matrix_returns_budget_unknown() {
        // 65 x 65 = 4225 > 4096 cells
        let rows = 65;
        let cols = 65;
        let d = BasicMatrix::zero(rows, cols).unwrap();
        let q = BasicMatrix::zero(rows, rows).unwrap();

        let err = check_soundness(&d, &q).unwrap_err();
        match err {
            LggrSoundnessError::BudgetUnknown { cells, limit } => {
                assert_eq!(cells, 4225);
                assert_eq!(limit, MAX_LGGR_CELLS);
            }
            other => panic!("expected BudgetUnknown, got {other:?}"),
        }
    }

    #[test]
    fn dimension_mismatch_refused() {
        let d =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let q = BasicMatrix::from_row_major(
            2,
            3,
            vec![r(1, 1), r(0, 1), r(0, 1), r(0, 1), r(1, 1), r(0, 1)],
        )
        .unwrap();

        let err = check_soundness(&d, &q).unwrap_err();
        assert!(matches!(err, LggrSoundnessError::DimensionMismatch { .. }));
    }

    #[test]
    fn empty_matrix_refused() {
        let d = BasicMatrix::from_row_major(0, 0, vec![]).unwrap();
        let q = BasicMatrix::from_row_major(0, 0, vec![]).unwrap();

        let err = check_soundness(&d, &q).unwrap_err();
        assert!(matches!(err, LggrSoundnessError::EmptyMatrix));
    }

    #[test]
    fn product_at_cell_limit_remains_admitted() {
        let d = BasicMatrix::from_row_major(1, 64, vec![r(1, 1); 64]).unwrap();
        let q = BasicMatrix::from_row_major(64, 1, vec![r(1, 1); 64]).unwrap();
        let report = check_soundness(&d, &q).unwrap();
        assert!(report.sound);
        assert_eq!((report.d_rank, report.qd_rank), (1, 1));
        assert!(report.witness.is_none());
        assert_eq!(report.authority_effect, "None");
    }

    #[test]
    fn witness_skips_invisible_free_column_and_nonleading_pivot() {
        let d = BasicMatrix::from_row_major(
            2,
            3,
            vec![r(0, 1), r(1, 1), r(-2, 1), r(0, 1), r(0, 1), r(1, 1)],
        )
        .unwrap();
        let q = BasicMatrix::from_row_major(1, 2, vec![r(1, 1), r(0, 1)]).unwrap();
        let report = check_soundness(&d, &q).unwrap();
        assert!(!report.sound);
        assert_eq!(
            report.witness.as_ref().unwrap(),
            &vec![r(0, 1), r(2, 1), r(1, 1)]
        );
        assert!(verify_unsoundness_witness(&d, &q, report.witness.as_ref().unwrap()).unwrap());
    }

    #[test]
    fn witness_preserves_fractional_pivot_normalization() {
        let d =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 2), r(0, 1), r(0, 1), r(1, 3)]).unwrap();
        let q = BasicMatrix::from_row_major(1, 2, vec![r(4, 3), r(12, 5)]).unwrap();
        let report = check_soundness(&d, &q).unwrap();
        assert!(!report.sound);
        let witness = report.witness.unwrap();
        assert_eq!(witness, vec![r(-6, 5), r(1, 1)]);
        assert!(verify_unsoundness_witness(&d, &q, &witness).unwrap());
    }

    #[test]
    fn admitted_invalid_witnesses_are_false_and_zero_carrier_is_sound() {
        let d =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        let q = BasicMatrix::from_row_major(1, 2, vec![r(1, 1), r(-1, 1)]).unwrap();
        for witness in [
            vec![],
            vec![r(1, 1)],
            vec![r(0, 1); 2],
            vec![r(1, 1), r(0, 1)],
        ] {
            assert!(!verify_unsoundness_witness(&d, &q, &witness).unwrap());
        }
        assert!(verify_unsoundness_witness(&d, &q, &[r(1, 1), r(1, 1)]).unwrap());
        let zero_d = BasicMatrix::zero(2, 2).unwrap();
        let report = check_soundness(&zero_d, &q).unwrap();
        assert!(report.sound && report.witness.is_none());
        assert!(!verify_unsoundness_witness(&zero_d, &q, &[r(1, 1), r(1, 1)]).unwrap());
    }

    #[test]
    fn verifier_admits_matrix_profile_before_inspecting_witness() {
        let empty = BasicMatrix::from_row_major(0, 0, vec![]).unwrap();
        assert_eq!(
            verify_unsoundness_witness(&empty, &empty, &[r(1, 1)]),
            Err(LggrSoundnessError::EmptyMatrix)
        );
        let d = BasicMatrix::from_row_major(1, 2, vec![r(1, 1); 2]).unwrap();
        let q = BasicMatrix::from_row_major(1, 2, vec![r(1, 1); 2]).unwrap();
        assert_eq!(
            verify_unsoundness_witness(&d, &q, &[]),
            Err(LggrSoundnessError::DimensionMismatch {
                q_cols: 2,
                d_rows: 1
            })
        );
        let d = BasicMatrix::zero(65, 65).unwrap();
        let q = BasicMatrix::zero(1, 65).unwrap();
        assert_eq!(
            verify_unsoundness_witness(&d, &q, &[]),
            Err(LggrSoundnessError::BudgetUnknown {
                cells: 4225,
                limit: MAX_LGGR_CELLS
            })
        );
        let d = BasicMatrix::zero(1, 65).unwrap();
        let q = BasicMatrix::zero(65, 1).unwrap();
        assert_eq!(
            verify_unsoundness_witness(&d, &q, &vec![r(0, 1); 65]),
            Err(LggrSoundnessError::BudgetUnknown {
                cells: 4225,
                limit: MAX_LGGR_CELLS
            })
        );
    }

    #[test]
    fn ternary_two_by_three_grid_matches_independent_minors_and_witness_equations() {
        // 3^6 carrier matrices and 3^2 observers. The oracle uses small integer
        // minors/direct dot products, never the production rank or kernel code.
        for encoded in 0..729 {
            let mut digits = encoded;
            let mut a = [0_i64; 6];
            for value in &mut a {
                *value = digits % 3 - 1;
                digits /= 3;
            }
            let d =
                BasicMatrix::from_row_major(2, 3, a.iter().map(|&x| r(x, 1)).collect()).unwrap();
            let nonzero_minor = a[0] * a[4] != a[1] * a[3]
                || a[0] * a[5] != a[2] * a[3]
                || a[1] * a[5] != a[2] * a[4];
            let d_rank = if nonzero_minor {
                2
            } else {
                usize::from(a.iter().any(|&x| x != 0))
            };
            for x in -1..=1 {
                for y in -1..=1 {
                    let q = BasicMatrix::from_row_major(1, 2, vec![r(x, 1), r(y, 1)]).unwrap();
                    let qd_rank = usize::from((0..3).any(|c| x * a[c] + y * a[c + 3] != 0));
                    let report = check_soundness(&d, &q).unwrap();
                    assert_eq!((report.d_rank, report.qd_rank), (d_rank, qd_rank));
                    assert_eq!(report.sound, d_rank == qd_rank);
                    assert_eq!(report.witness.is_some(), !report.sound);
                    if let Some(witness) = report.witness {
                        let image = [0, 1].map(|row| {
                            (0..3).fold(r(0, 1), |sum, c| sum + r(a[row * 3 + c], 1) * &witness[c])
                        });
                        assert!(image.iter().any(|value| !value.is_zero()));
                        assert!((r(x, 1) * &image[0] + r(y, 1) * &image[1]).is_zero());
                        assert!(verify_unsoundness_witness(&d, &q, &witness).unwrap());
                    }
                }
            }
        }
    }
}
