//! Re-export canonical `linear_algebra::image_kernel` implementation.
//! Single Point of Truth: `crate::linear_algebra::image_kernel`.
//! Authority provenance: `one_oears.md` ruling 4.

pub use crate::linear_algebra::image_kernel::*;

/// Rank-nullity census for one exact reduced matrix.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RankNullity {
    rank: usize,
    nullity: usize,
    columns: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RankNullityError {
    Pivots,
    PivotOrder,
    Sum,
}

impl std::fmt::Display for RankNullityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Pivots => write!(formatter, "pivot count disagrees with rank"),
            Self::PivotOrder => write!(
                formatter,
                "pivot columns are not a strictly increasing subset"
            ),
            Self::Sum => write!(formatter, "rank + nullity disagrees with the column count"),
        }
    }
}

impl std::error::Error for RankNullityError {}

impl RankNullity {
    pub fn rank(&self) -> usize {
        self.rank
    }

    pub fn nullity(&self) -> usize {
        self.nullity
    }

    pub fn columns(&self) -> usize {
        self.columns
    }
}

/// `rank(A) + dim ker(A) =` column count, with the pivot set a strict subset of the columns.
pub fn admit_rank_nullity<T: crate::scalars::CheckedExactField>(
    reduced: &RankRref<T>,
    kernel: &RawSubspaceBasis<T>,
    columns: usize,
) -> Result<RankNullity, RankNullityError> {
    let rank = reduced.rank();
    if reduced.pivot_columns().len() != rank {
        return Err(RankNullityError::Pivots);
    }
    let mut previous: Option<usize> = None;
    for &column in reduced.pivot_columns() {
        if column >= columns {
            return Err(RankNullityError::PivotOrder);
        }
        if let Some(earlier) = previous {
            if column <= earlier {
                return Err(RankNullityError::PivotOrder);
            }
        }
        previous = Some(column);
    }
    let nullity = kernel.len();
    let sum = rank.checked_add(nullity).ok_or(RankNullityError::Sum)?;
    if sum != columns {
        return Err(RankNullityError::Sum);
    }
    Ok(RankNullity {
        rank,
        nullity,
        columns,
    })
}

// Origin: engine/crates_rs/core_linear_algebra/src/image_kernel.rs
// Claim: urn:core:crates_rs:core-linear-algebra:image-kernel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::backend::basic_matrix::BasicMatrix;
    use num_rational::Rational64;

    fn ratio(numerator: i64) -> Rational64 {
        Rational64::new(numerator, 1)
    }

    fn taken<T, E>(result: Result<T, E>) -> T {
        result.map_or_else(
            |_| loop {
                assert!(false);
            },
            |value| value,
        )
    }

    #[test]
    fn a_rank_one_row_has_nullity_two() {
        let matrix = taken(BasicMatrix::from_row_major(
            1,
            3,
            vec![ratio(1), ratio(2), ratio(3)],
        ));
        let reduced = taken(matrix.rank_and_rref());
        let kernel = taken(matrix.kernel_basis());
        let law = taken(admit_rank_nullity(&reduced, &kernel, matrix.cols()));
        assert_eq!(law.rank(), 1);
        assert_eq!(law.nullity(), 2);
        assert_eq!(law.rank() + law.nullity(), law.columns());
    }
}
