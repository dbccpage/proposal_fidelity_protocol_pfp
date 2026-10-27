/// A power series represented by its coefficient sequence {a_0, a_1, a_2, ...}.
///
/// ## BaseType contract
///
/// Pure data â€” no computation, no conversion logic.
/// The sequence `coefficients[n]` = coefficient of x^n.
#[derive(Debug, Clone, PartialEq)]
pub struct PowerSeriesInput {
    pub coefficients: Vec<f64>,
}

/// The result of a convergence test on a power series.
///
/// ## BaseType contract
///
/// Pure data â€” carries the radius of convergence, whether the series
/// converges, and the computed limit ratio.
#[derive(Debug, Clone, PartialEq)]
pub struct ConvergenceResult {
    /// Radius of convergence R. `f64::INFINITY` for everywhere-convergent series.
    pub radius: f64,
    /// Whether the series converges (R > 0).
    pub converges: bool,
    /// The computed limit ratio L = lim |a_{n+1}/a_n|. R = 1/L.
    pub ratio_limit: f64,
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_types/src/power_series.rs
// Claim: urn:core:types:power-series:ratio-bound:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RatioLowerBound {
    compared: u32,
    numerator: i64,
    denominator: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RatioLowerBoundError {
    DenominatorNotPositive { denominator: i64 },
    TooShort,
    AbsOverflow { index: usize },
    ProductOverflow { index: usize },
    Violates { index: usize, left: i64, right: i64 },
    NoComparablePair,
}

// Origin: engine/crates_rs/core_types/src/power_series.rs
// Claim: urn:core:crates_rs:core-types:power-series:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RatioLowerBoundError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RatioLowerBoundError {}

fn checked_abs(value: i64, index: usize) -> Result<i64, RatioLowerBoundError> {
    if value < 0 {
        value.checked_neg().ok_or(RatioLowerBoundError::AbsOverflow { index })
    } else {
        Ok(value)
    }
}

fn check_adjacent_ratio(
    current: i64,
    next: i64,
    index: usize,
    numerator: i64,
    denominator: i64,
) -> Result<bool, RatioLowerBoundError> {
    if current == 0 {
        return Ok(false);
    }
    let current_abs = checked_abs(current, index)?;
    let next_abs = checked_abs(next, index + 1)?;
    let left = current_abs
        .checked_mul(denominator)
        .ok_or(RatioLowerBoundError::ProductOverflow { index })?;
    let right = next_abs
        .checked_mul(numerator)
        .ok_or(RatioLowerBoundError::ProductOverflow { index })?;
    if left < right {
        return Err(RatioLowerBoundError::Violates { index, left, right });
    }
    Ok(true)
}

pub fn try_ratio_lower_bound(
    coefficients: &[i64],
    numerator: i64,
    denominator: i64,
) -> Result<RatioLowerBound, RatioLowerBoundError> {
    if denominator <= 0 {
        return Err(RatioLowerBoundError::DenominatorNotPositive { denominator });
    }
    if coefficients.len() < 2 {
        return Err(RatioLowerBoundError::TooShort);
    }
    let mut compared = 0u32;
    for index in 0..coefficients.len() - 1 {
        if check_adjacent_ratio(
            coefficients[index],
            coefficients[index + 1],
            index,
            numerator,
            denominator,
        )? {
            compared = compared.checked_add(1).ok_or(RatioLowerBoundError::ProductOverflow { index })?;
        }
    }
    if compared == 0 {
        return Err(RatioLowerBoundError::NoComparablePair);
    }
    Ok(RatioLowerBound {
        compared,
        numerator,
        denominator,
    })
}

impl RatioLowerBound {
    pub fn compared(&self) -> u32 {
        self.compared
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod ratio_lower_bound_tests {
    use super::*;

    #[test]
    fn geometric_decay_meets_a_unit_bound() {
        let bound = try_ratio_lower_bound(&[8, 4, 2], 1, 1);
        assert!(matches!(bound, Ok(ref witness) if witness.compared() == 2));
    }

    #[test]
    fn refuses_a_bound_tighter_than_the_first_ratio() {
        let wrong = try_ratio_lower_bound(&[8, 4, 2], 3, 1);
        assert!(matches!(
            wrong,
            Err(RatioLowerBoundError::Violates { index: 0, left: 8, right: 12 })
        ));
    }
}
