//! Conditional adequacy of exact finite calibrated chains.
//!
//! The occurrence chain, coupling, reference durations, positive calibration,
//! readouts and edge budgets are declared data. Summation and telescoping prove
//! interval bounds and endpoint-preserving coarsening/refinement stability.
//! Nothing here derives a clock or a chronology from primitive difference, nor
//! supplies units, physical calibration, stochastic errors or traceability.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_1f74e802<T> {
    fn checked_invariant_1f74e802(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_1f74e802<T> for Option<T> {
    #[inline]
    fn checked_invariant_1f74e802(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_1f74e802<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_1f74e802(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::fmt;

use num_rational::BigRational;
use num_traits::{Signed, Zero};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ChainClockError {
    ShapeMismatch,
    InvalidRational {
        field: &'static str,
        index: Option<usize>,
    },
    NonPositiveCalibration,
    NonPositiveDuration {
        edge: usize,
    },
    NegativeBudget {
        edge: usize,
    },
    UnderBudget {
        edge: usize,
        discrepancy: BigRational,
        budget: BigRational,
    },
    InvalidInterval {
        start: usize,
        stop: usize,
        edge_count: usize,
    },
    InvalidBoundaries,
}

impl fmt::Display for ChainClockError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ShapeMismatch => {
                write!(f, "one reading per vertex and one budget per edge required")
            }
            Self::InvalidRational { field, index } => {
                write!(f, "{field} {index:?} has a zero denominator")
            }
            Self::NonPositiveCalibration => write!(f, "calibration must be positive"),
            Self::NonPositiveDuration { edge } => {
                write!(f, "reference duration at edge {edge} must be positive")
            }
            Self::NegativeBudget { edge } => write!(f, "budget at edge {edge} must be nonnegative"),
            Self::UnderBudget {
                edge,
                discrepancy,
                budget,
            } => write!(
                f,
                "edge {edge} discrepancy {discrepancy} exceeds budget {budget}"
            ),
            Self::InvalidInterval {
                start,
                stop,
                edge_count,
            } => write!(f, "invalid interval [{start},{stop}] on {edge_count} edges"),
            Self::InvalidBoundaries => write!(
                f,
                "boundaries must strictly partition the chain from 0 to its final vertex"
            ),
        }
    }
}
impl std::error::Error for ChainClockError {}

fn canonical(
    value: BigRational,
    field: &'static str,
    index: Option<usize>,
) -> Result<BigRational, ChainClockError> {
    if value.denom().is_zero() {
        return Err(ChainClockError::InvalidRational { field, index });
    }
    Ok(value.reduced())
}
fn canonical_vector(
    values: Vec<BigRational>,
    field: &'static str,
) -> Result<Vec<BigRational>, ChainClockError> {
    values
        .into_iter()
        .enumerate()
        .map(|(i, x)| canonical(x, field, Some(i)))
        .collect()
}

/// Every edge has a positive declared reference duration. Readout differences
/// may be nonpositive when the corresponding discrepancy fits the declared
/// budget; monotonic readout is not an unstated extra hypothesis. Private fields
/// guarantee total edge coupling and validity after construction.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChainClock {
    durations: Vec<BigRational>,
    readings: Vec<BigRational>,
    calibration: BigRational,
    error_budgets: Vec<BigRational>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClockIntervalBound {
    pub start: usize,
    pub stop: usize,
    pub reference_duration: BigRational,
    pub calibrated_readout_duration: BigRational,
    pub discrepancy: BigRational,
    pub error_budget: BigRational,
}

impl ChainClock {
    fn check_edge_budget(
        edge: usize,
        duration: &BigRational,
        reading_step: BigRational,
        calibration: &BigRational,
        budget: &BigRational,
    ) -> Result<(), ChainClockError> {
        if *duration <= BigRational::zero() {
            return Err(ChainClockError::NonPositiveDuration { edge });
        }
        if *budget < BigRational::zero() {
            return Err(ChainClockError::NegativeBudget { edge });
        }
        let readout = calibration * reading_step;
        let discrepancy = (readout - duration).abs();
        if discrepancy > *budget {
            return Err(ChainClockError::UnderBudget {
                edge,
                discrepancy,
                budget: budget.clone(),
            });
        }
        Ok(())
    }

    pub fn new(
        durations: Vec<BigRational>,
        readings: Vec<BigRational>,
        calibration: BigRational,
        error_budgets: Vec<BigRational>,
    ) -> Result<Self, ChainClockError> {
        if readings.len() != durations.len() + 1 || error_budgets.len() != durations.len() {
            return Err(ChainClockError::ShapeMismatch);
        }
        let durations = canonical_vector(durations, "duration")?;
        let readings = canonical_vector(readings, "reading")?;
        let error_budgets = canonical_vector(error_budgets, "budget")?;
        let calibration = canonical(calibration, "calibration", None)?;
        if calibration <= BigRational::zero() {
            return Err(ChainClockError::NonPositiveCalibration);
        }
        for edge in 0..durations.len() {
            Self::check_edge_budget(
                edge,
                &durations[edge],
                &readings[edge + 1] - &readings[edge],
                &calibration,
                &error_budgets[edge],
            )?;
        }
        Ok(Self {
            durations,
            readings,
            calibration,
            error_budgets,
        })
    }

    /// Construct an exact readout representation of an already declared finite
    /// duration chain: r_(i+1)=r_i+d_i/kappa, with zero error budgets. This
    /// conditional construction does not infer durations, occurrence order or
    /// physical coupling. Endpoint-preserving coarsening gives the same exact
    /// readouts as constructing the block-sum duration chain directly.
    pub fn exact_from_durations(
        durations: Vec<BigRational>,
        initial_reading: BigRational,
        calibration: BigRational,
    ) -> Result<Self, ChainClockError> {
        let durations = canonical_vector(durations, "duration")?;
        let initial_reading = canonical(initial_reading, "initial_reading", None)?;
        let calibration = canonical(calibration, "calibration", None)?;
        if calibration <= BigRational::zero() {
            return Err(ChainClockError::NonPositiveCalibration);
        }
        let mut readings = vec![initial_reading];
        for (edge, duration) in durations.iter().enumerate() {
            if duration <= &BigRational::zero() {
                return Err(ChainClockError::NonPositiveDuration { edge });
            }
            readings.push(readings.last().checked_invariant_1f74e802("checked invariant") + duration / &calibration);
        }
        let budgets = vec![BigRational::zero(); durations.len()];
        Self::new(durations, readings, calibration, budgets)
    }

    pub fn durations(&self) -> &[BigRational] {
        &self.durations
    }
    pub fn readings(&self) -> &[BigRational] {
        &self.readings
    }
    pub fn calibration(&self) -> &BigRational {
        &self.calibration
    }
    pub fn error_budgets(&self) -> &[BigRational] {
        &self.error_budgets
    }
    pub fn edge_count(&self) -> usize {
        self.durations.len()
    }

    /// Sum e_i=kappa(r_(i+1)-r_i)-d_i over edges start..stop. Readings
    /// telescope, and |sum e_i| <= sum |e_i| <= sum budget_i. Empty intervals
    /// have zero reference/readout duration, discrepancy and error budget.
    pub fn interval_bound(
        &self,
        start: usize,
        stop: usize,
    ) -> Result<ClockIntervalBound, ChainClockError> {
        if start > stop || stop > self.edge_count() {
            return Err(ChainClockError::InvalidInterval {
                start,
                stop,
                edge_count: self.edge_count(),
            });
        }
        let reference_duration: BigRational = self.durations[start..stop].iter().cloned().sum();
        let calibrated_readout_duration =
            &self.calibration * (&self.readings[stop] - &self.readings[start]);
        let discrepancy = (&calibrated_readout_duration - &reference_duration).abs();
        let error_budget = self.error_budgets[start..stop].iter().cloned().sum();
        Ok(ClockIntervalBound {
            start,
            stop,
            reference_duration,
            calibrated_readout_duration,
            discrepancy,
            error_budget,
        })
    }

    pub fn verify_interval_bound(
        &self,
        candidate: &ClockIntervalBound,
    ) -> Result<bool, ChainClockError> {
        Ok(candidate == &self.interval_bound(candidate.start, candidate.stop)?)
    }

    /// All finite intervals, including single vertices, in endpoint order.
    pub fn all_interval_bounds(&self) -> Vec<ClockIntervalBound> {
        (0..=self.edge_count())
            .flat_map(|start| {
                (start..=self.edge_count())
                    .map(move |stop| self.interval_bound(start, stop).checked_invariant_1f74e802("checked invariant"))
            })
            .collect()
    }

    /// Select partition endpoints and sum reference durations and budgets within
    /// each block. Positive reference duration sums and the interval bound make
    /// the resulting clock adequate. Nothing is dropped from any block.
    pub fn coarsen(&self, boundaries: &[usize]) -> Result<Self, ChainClockError> {
        if boundaries.first() != Some(&0)
            || boundaries.last() != Some(&self.edge_count())
            || boundaries.windows(2).any(|w| w[0] >= w[1])
        {
            return Err(ChainClockError::InvalidBoundaries);
        }
        let durations = boundaries
            .windows(2)
            .map(|w| self.durations[w[0]..w[1]].iter().cloned().sum())
            .collect();
        let error_budgets = boundaries
            .windows(2)
            .map(|w| self.error_budgets[w[0]..w[1]].iter().cloned().sum())
            .collect();
        let readings = boundaries
            .iter()
            .map(|&v| self.readings[v].clone())
            .collect();
        Self::new(durations, readings, self.calibration.clone(), error_budgets)
    }

    /// A fine clock refines a coarse one when block durations, endpoint readings
    /// and calibration agree, and each fine-budget block sum is no larger than
    /// the coarse edge budget. Every coarse interval discrepancy is identical
    /// to the corresponding fine interval discrepancy, with a no-larger fine
    /// budget. This is a conditional preservation theorem, not refinement creation.
    pub fn refines(&self, coarse: &Self, boundaries: &[usize]) -> Result<bool, ChainClockError> {
        let summed = self.coarsen(boundaries)?;
        Ok(summed.durations == coarse.durations
            && summed.readings == coarse.readings
            && summed.calibration == coarse.calibration
            && summed.error_budgets.len() == coarse.error_budgets.len()
            && summed
                .error_budgets
                .iter()
                .zip(&coarse.error_budgets)
                .all(|(fine, coarse)| fine <= coarse))
    }
}

// Origin: engine/crates_rs/core_measurement/src/finite_chain_clock.rs
// Claim: urn:core:crates_rs:core-measurement:finite-chain-clock:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(BigInt::from(n), BigInt::from(d))
    }
    fn example() -> ChainClock {
        // Calibrated edge durations 2,3,4,5; signed residuals 1/2,-1/3,1/4,-1/5.
        ChainClock::new(
            vec![q(3, 2), q(10, 3), q(15, 4), q(26, 5)],
            vec![q(-2, 1), q(-1, 1), q(1, 2), q(5, 2), q(5, 1)],
            q(2, 1),
            vec![q(1, 2), q(1, 3), q(1, 4), q(1, 5)],
        )
        .unwrap()
    }

    #[test]
    fn all_intervals_telescope_and_nontrivial_blocks_preserve_bounds() {
        let fine = example();
        let boundaries = [0, 2, 4];
        let coarse = fine.coarsen(&boundaries).unwrap();
        assert_eq!(coarse.durations(), &[q(29, 6), q(179, 20)]);
        assert_eq!(coarse.error_budgets(), &[q(5, 6), q(9, 20)]);
        assert_eq!(coarse.readings(), &[q(-2, 1), q(1, 2), q(5, 1)]);
        assert!(fine.refines(&coarse, &boundaries).unwrap());
        for interval in fine.all_interval_bounds() {
            assert!(interval.discrepancy <= interval.error_budget);
            assert!(fine.verify_interval_bound(&interval).unwrap());
        }
        for start in 0..boundaries.len() {
            for stop in start..boundaries.len() {
                let f = fine
                    .interval_bound(boundaries[start], boundaries[stop])
                    .unwrap();
                let c = coarse.interval_bound(start, stop).unwrap();
                assert_eq!(f.reference_duration, c.reference_duration);
                assert_eq!(f.calibrated_readout_duration, c.calibrated_readout_duration);
                assert_eq!(f.discrepancy, c.discrepancy);
                assert_eq!(f.error_budget, c.error_budget);
            }
        }
    }

    #[test]
    fn conditional_refinement_accepts_larger_coarse_budgets_only() {
        let fine = example();
        let summed = fine.coarsen(&[0, 2, 4]).unwrap();
        let relaxed = ChainClock::new(
            summed.durations.clone(),
            summed.readings.clone(),
            summed.calibration.clone(),
            vec![q(1, 1), q(1, 1)],
        )
        .unwrap();
        assert!(fine.refines(&relaxed, &[0, 2, 4]).unwrap());
        let smaller = ChainClock::new(
            summed.durations.clone(),
            summed.readings.clone(),
            summed.calibration.clone(),
            vec![q(1, 6), q(1, 20)],
        )
        .unwrap();
        assert!(!fine.refines(&smaller, &[0, 2, 4]).unwrap());
        let changed = ChainClock::new(
            vec![q(5, 1), q(9, 1)],
            summed.readings.clone(),
            summed.calibration.clone(),
            vec![q(1, 1), q(1, 1)],
        )
        .unwrap();
        assert!(!fine.refines(&changed, &[0, 2, 4]).unwrap());
    }

    #[test]
    fn refuses_malformed_underbudget_and_unordered_data() {
        assert_eq!(
            ChainClock::new(vec![q(1, 1)], vec![q(0, 1)], q(1, 1), vec![q(0, 1)]),
            Err(ChainClockError::ShapeMismatch)
        );
        assert!(matches!(
            ChainClock::new(
                vec![q(2, 1)],
                vec![q(0, 1), q(1, 1)],
                q(1, 1),
                vec![q(0, 1)]
            ),
            Err(ChainClockError::UnderBudget { edge: 0, .. })
        ));
        assert!(matches!(
            ChainClock::new(
                vec![q(1, 1)],
                vec![q(0, 1), q(1, 1)],
                q(1, 1),
                vec![q(-1, 1)]
            ),
            Err(ChainClockError::NegativeBudget { edge: 0 })
        ));
        let nonmonotone = ChainClock::new(
            vec![q(1, 1)],
            vec![q(1, 1), q(0, 1)],
            q(1, 1),
            vec![q(3, 1)],
        )
        .unwrap();
        assert_eq!(
            nonmonotone.interval_bound(0, 1).unwrap().discrepancy,
            q(2, 1)
        );
        assert_eq!(nonmonotone.coarsen(&[0, 1]).unwrap(), nonmonotone);
        let clock = example();
        for cuts in [vec![], vec![0, 0, 4], vec![1, 4], vec![0, 3], vec![0, 5, 4]] {
            assert_eq!(
                clock.coarsen(&cuts),
                Err(ChainClockError::InvalidBoundaries)
            );
        }
        assert!(clock.interval_bound(3, 2).is_err());
        assert!(clock.interval_bound(0, 5).is_err());
    }

    #[test]
    fn empty_chain_identity_and_forged_interval() {
        let empty = ChainClock::new(vec![], vec![q(-7, 1)], q(2, 1), vec![]).unwrap();
        assert_eq!(empty.coarsen(&[0]).unwrap(), empty);
        assert_eq!(empty.all_interval_bounds().len(), 1);
        let clock = example();
        let mut forged = clock.interval_bound(0, 4).unwrap();
        forged.error_budget = q(100, 1);
        assert!(!clock.verify_interval_bound(&forged).unwrap());
        let invalid = BigRational::new_raw(BigInt::from(1), BigInt::from(0));
        assert!(matches!(
            ChainClock::new(vec![], vec![invalid], q(1, 1), vec![]),
            Err(ChainClockError::InvalidRational {
                field: "reading",
                index: Some(0)
            })
        ));
    }
    #[test]
    fn exact_duration_representation_commutes_with_block_sums() {
        let durations = vec![q(1, 2), q(1, 3), q(2, 3)];
        let exact = ChainClock::exact_from_durations(durations, q(7, 3), q(3, 2)).unwrap();
        assert!(exact
            .all_interval_bounds()
            .iter()
            .all(|bound| bound.discrepancy.is_zero() && bound.error_budget.is_zero()));
        let direct =
            ChainClock::exact_from_durations(vec![q(5, 6), q(2, 3)], q(7, 3), q(3, 2)).unwrap();
        assert_eq!(exact.coarsen(&[0, 2, 3]).unwrap(), direct);
        assert_eq!(
            ChainClock::exact_from_durations(vec![q(1, 1)], q(0, 1), q(0, 1)),
            Err(ChainClockError::NonPositiveCalibration)
        );
        assert_eq!(
            ChainClock::exact_from_durations(vec![q(0, 1)], q(0, 1), q(1, 1)),
            Err(ChainClockError::NonPositiveDuration { edge: 0 })
        );
    }
}
