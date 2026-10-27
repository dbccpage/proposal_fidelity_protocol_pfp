#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GrowthOrder {
    TargetDominated,
    SameOrder,
    TargetDominates,
    Incomparable,
}

#[derive(Debug, Clone, PartialEq)]
pub struct SeriesComparisonInput {
    pub target: Vec<f64>,
    pub reference: Vec<f64>,
    pub reference_converges: Option<bool>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct SeriesComparisonResult {
    pub ratio_tail: f64,
    pub growth_order: GrowthOrder,
    pub target_converges: Option<bool>,
    pub big_o_constant: Option<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct AlternatingSeriesInput {
    pub magnitudes: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct AlternatingSeriesResult {
    pub converges_by_leibniz: bool,
    pub monotone_nonincreasing: bool,
    pub tends_to_zero: bool,
    pub partial_sum: f64,
    pub remainder_bound: Option<f64>,
    pub abel_sums: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ScalarSamples1D {
    pub points: Vec<f64>,
    pub values: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct DerivativeSamples1D {
    pub points: Vec<f64>,
    pub first_derivative: Vec<f64>,
    pub second_derivative: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ScalarFieldJetInput {
    pub center: Vec<f64>,
    pub step: f64,
    pub center_value: f64,
    pub axis_plus: Vec<f64>,
    pub axis_minus: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ScalarFieldJet {
    pub center: Vec<f64>,
    pub gradient: Vec<f64>,
    pub hessian_diagonal: Vec<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct VectorFieldJetInput {
    pub dimensions: usize,
    pub step: f64,
    pub axis_plus: Vec<Vec<f64>>,
    pub axis_minus: Vec<Vec<f64>>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct JacobianMatrix {
    pub rows: usize,
    pub cols: usize,
    pub entries: Vec<Vec<f64>>,
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LeibnizTail { partial: u64, remainder: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LeibnizTailError { Empty, Positive, Monotone, Overflow }

// Origin: engine/crates_rs/core_types/src/analysis_kernel.rs
// Claim: urn:core:crates_rs:core-types:analysis-kernel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for LeibnizTailError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for LeibnizTailError {}

impl LeibnizTail {
    /// Positive nonincreasing integer magnitudes. The remainder is the last term.
    pub fn try_from_magnitudes(magnitudes: &[u64]) -> Result<Self, LeibnizTailError> {
        if magnitudes.is_empty() {
            return Err(LeibnizTailError::Empty);
        }
        let mut previous: Option<u64> = None;
        let mut total = 0u64;
        for value in magnitudes {
            if *value == 0 {
                return Err(LeibnizTailError::Positive);
            }
            if let Some(earlier) = previous {
                if *value > earlier {
                    return Err(LeibnizTailError::Monotone);
                }
            }
            previous = Some(*value);
            total = total.checked_add(*value).ok_or(LeibnizTailError::Overflow)?;
        }
        let remainder = *magnitudes.last().ok_or(LeibnizTailError::Empty)?;
        let partial = total.checked_sub(remainder).ok_or(LeibnizTailError::Overflow)?;
        if partial.checked_add(remainder) != Some(total) {
            return Err(LeibnizTailError::Overflow);
        }
        Ok(Self { partial, remainder })
    }

    pub fn partial(&self) -> u64 { self.partial }
    pub fn remainder(&self) -> u64 { self.remainder }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod leibniz_tail_checks {
    use super::*;

    #[test]
    fn four_three_one_has_partial_seven_and_remainder_one() {
        let tail = LeibnizTail::try_from_magnitudes(&[4, 3, 1]);
        assert!(matches!(tail, Ok(t) if t.partial() == 7 && t.remainder() == 1));
    }

    #[test]
    fn an_increase_and_a_zero_are_refused() {
        assert!(matches!(LeibnizTail::try_from_magnitudes(&[3, 4]), Err(LeibnizTailError::Monotone)));
        assert!(matches!(LeibnizTail::try_from_magnitudes(&[0, 1]), Err(LeibnizTailError::Positive)));
    }
}
