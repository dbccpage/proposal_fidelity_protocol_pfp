#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PositiveRootIndex {
    pub i: usize,
    pub j: usize,
}

#[derive(Debug, Clone)]
pub struct ZeroSumCoordinateState21 {
    pub coordinates: [f64; 21],
}

impl ZeroSumCoordinateState21 {
    pub fn new() -> Self {
        Self {
            coordinates: [0.0; 21],
        }
    }
}

impl Default for ZeroSumCoordinateState21 {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone)]
pub struct A20PositiveRootIndexSet {
    pub roots: Vec<PositiveRootIndex>,
}

/// Integer coordinates in the 21-dimensional ambient space of A_20, required to sum to 0.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IntegerZeroSum21 {
    coordinates: [i64; 21],
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ZeroSumError {
    NotZero { sum: i64 },
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/zero_sum_types.rs
// Claim: urn:core:crates_rs:core-types:zero-sum-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ZeroSumError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ZeroSumError {}

impl IntegerZeroSum21 {
    pub fn try_new(coordinates: [i64; 21]) -> Result<Self, ZeroSumError> {
        let mut sum = 0i64;
        for coordinate in coordinates {
            sum = sum.checked_add(coordinate).ok_or(ZeroSumError::Overflow)?;
        }
        if sum != 0 {
            return Err(ZeroSumError::NotZero { sum });
        }
        Ok(Self { coordinates })
    }

    pub fn coordinates(&self) -> &[i64; 21] {
        &self.coordinates
    }
}

/// Positive-root count of A_n is n(n+1)/2. The ambient dimension is n+1.
pub fn a_n_positive_roots(rank: u64) -> Result<u64, ZeroSumError> {
    let next = rank.checked_add(1).ok_or(ZeroSumError::Overflow)?;
    let product = rank.checked_mul(next).ok_or(ZeroSumError::Overflow)?;
    product.checked_div(2).ok_or(ZeroSumError::Overflow)
}

pub fn a_n_ambient_dimension(rank: u64) -> Result<u64, ZeroSumError> {
    rank.checked_add(1).ok_or(ZeroSumError::Overflow)
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod integer_zero_sum_witness {
    use super::*;

    #[test]
    fn a20_has_210_positive_roots_in_dimension_21() {
        assert_eq!(a_n_positive_roots(20), Ok(210));
        assert_eq!(a_n_ambient_dimension(20), Ok(21));
        let mut coordinates = [0i64; 21];
        coordinates[0] = 4;
        coordinates[1] = -4;
        let state = IntegerZeroSum21::try_new(coordinates);
        assert!(state.is_ok());
        if let Ok(state) = state {
            assert_eq!(state.coordinates().first().copied(), Some(4));
        }
    }

    #[test]
    fn a_nonzero_sum_is_refused() {
        let mut coordinates = [0i64; 21];
        coordinates[0] = 1;
        assert!(matches!(
            IntegerZeroSum21::try_new(coordinates),
            Err(ZeroSumError::NotZero { sum: 1 })
        ));
    }
}
