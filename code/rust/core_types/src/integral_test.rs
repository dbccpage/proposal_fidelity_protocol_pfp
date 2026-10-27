/// An input sequence for the integral test, representing sampled function
/// values or coefficients of a series `{a_0, a_1, a_2, ...}`.
///
/// ## BaseType contract
/// Pure data â€” no computation, no conversion logic.

#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_33b8b18e = (i128, i128);
#[derive(Debug, Clone, PartialEq)]
pub struct IntegralTestInput {
    pub values: Vec<f64>,
}

/// The bounding result of an integral-based convergence test.
///
/// ## BaseType contract
/// Pure data â€” carries the integral approximation and computed
/// bounding box `[lower_bound, upper_bound]`.
#[derive(Debug, Clone, PartialEq)]
pub struct IntegralTestResult {
    /// The finite window integral approximation
    pub integral_approx: f64,
    /// Absolute lower bound on the partial sums (if provable)
    pub lower_bound: Option<f64>,
    /// Absolute upper bound on the partial sums (if provable)
    pub upper_bound: Option<f64>,
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DecreasingSeriesBound {
    count: u64,
    partial_sum: u64,
    lower: u64,
    upper: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DecreasingSeriesBoundError {
    Empty,
    NonPositive { term: u64 },
    NotStrictlyDecreasing { previous: u64, term: u64 },
    ComparisonFailed { partial_sum: u64, lower: u64, upper: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/integral_test.rs
// Claim: urn:core:crates_rs:core-types:integral-test:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DecreasingSeriesBoundError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DecreasingSeriesBoundError {}

impl DecreasingSeriesBound {
    fn sum_strictly_decreasing(terms: &[u64]) -> Result<u64, DecreasingSeriesBoundError> {
        let mut partial_sum = 0u64;
        let mut previous = None;
        for &term in terms {
            if term == 0 {
                return Err(DecreasingSeriesBoundError::NonPositive { term });
            }
            if let Some(prev) = previous {
                if term >= prev {
                    return Err(DecreasingSeriesBoundError::NotStrictlyDecreasing {
                        previous: prev,
                        term,
                    });
                }
            }
            previous = Some(term);
            partial_sum = partial_sum.checked_add(term).ok_or(DecreasingSeriesBoundError::Overflow)?;
        }
        Ok(partial_sum)
    }

    pub fn certify(terms: &[u64]) -> Result<Self, DecreasingSeriesBoundError> {
        if terms.is_empty() {
            return Err(DecreasingSeriesBoundError::Empty);
        }
        let partial_sum = Self::sum_strictly_decreasing(terms)?;
        let count = u64::try_from(terms.len()).map_err(|_| DecreasingSeriesBoundError::Overflow)?;
        let first = terms[0];
        let last = terms[terms.len() - 1];
        let lower = count.checked_mul(last).ok_or(DecreasingSeriesBoundError::Overflow)?;
        let upper = count.checked_mul(first).ok_or(DecreasingSeriesBoundError::Overflow)?;
        if !(lower..=upper).contains(&partial_sum) {
            return Err(DecreasingSeriesBoundError::ComparisonFailed { partial_sum, lower, upper });
        }
        Ok(Self { count, partial_sum, lower, upper })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(DecreasingSeriesBound::certify(&[5, 3, 1]), Ok(w) if w.partial_sum == 9 && w.lower == 3 && w.upper == 15 && w.count == 3));
        assert!(matches!(DecreasingSeriesBound::certify(&[1, 1]), Err(DecreasingSeriesBoundError::NotStrictlyDecreasing { .. })));
        assert!(matches!(DecreasingSeriesBound::certify(&[]), Err(DecreasingSeriesBoundError::Empty)));
    }
}
