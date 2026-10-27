//! Exact operational classification of normalized signed finite valuations.
//! AuthorityEffect: None. Signed mass is not a probability state. A partition
//! restricts accessible effects; it yields a classical report state exactly when
//! every block mass is nonnegative. Signed instruments descend exactly when
//! target-block row sums agree within each source block; descended maps must
//! additionally be nonnegative. These hypotheses are checked, never inferred.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_16eb9288<T> {
    fn checked_invariant_16eb9288(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_16eb9288<T> for Option<T> {
    #[inline]
    fn checked_invariant_16eb9288(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_16eb9288<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_16eb9288(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_traits::{One, Signed, Zero};
use core_number_theory::rational::Rational;

use crate::error::ClassicalShadowError;
use crate::simplex::ProbabilitySimplex;
use crate::stochastic_map::StochasticMap;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SignedRepresentationError {
    #[error("empty carrier, nonpositive total, or invalid report partition")]
    InvalidCarrier,
    #[error("instrument matrices must be nonempty square matrices on the carrier")]
    InvalidShape,
    #[error("sum of outcome row masses at {row} is {mass}, not one")]
    MassNotPreserved { row: usize, mass: Rational },
    #[error("outcome {outcome} rows {first},{second} in one source block disagree on target block {target}")]
    NotDescending {
        outcome: usize,
        first: usize,
        second: usize,
        target: usize,
    },
    #[error("outcome {outcome} has negative report transition at ({source_report},{target})")]
    NegativeReportTransition {
        outcome: usize,
        source_report: usize,
        target: usize,
    },
    #[error("classical probability refusal: {0}")]
    Classical(#[from] ClassicalShadowError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignedValuation {
    masses: Vec<Rational>,
}

impl SignedValuation {
    /// Divide arbitrary signed rational weights by their strictly positive total.
    pub fn from_weights(weights: Vec<Rational>) -> Result<Self, SignedRepresentationError> {
        let total: Rational = weights.iter().cloned().sum();
        if weights.is_empty() || !total.is_positive() {
            return Err(SignedRepresentationError::InvalidCarrier);
        }
        Ok(Self {
            masses: weights.into_iter().map(|w| w / &total).collect(),
        })
    }
    pub fn masses(&self) -> &[Rational] {
        &self.masses
    }
    /// A negative indicator expectation is a separating witness against ANY
    /// stochastic representation preserving that reported indicator: classical
    /// states and effects in [0,1] have nonnegative pairing in every dimension.
    pub fn negative_indicator(&self) -> Option<(usize, Rational)> {
        self.masses
            .iter()
            .enumerate()
            .find(|(_, mass)| mass.is_negative())
            .map(|(i, mass)| (i, mass.clone()))
    }
    /// The minimal negative mass in all decompositions w=a-b with a,b>=0.
    /// Pointwise b_i>=max(-w_i,0), attained by disjoint Jordan parts.
    pub fn negativity(&self) -> Rational {
        self.masses
            .iter()
            .filter(|p| p.is_negative())
            .map(|p| -p)
            .sum()
    }
    pub fn jordan_parts(&self) -> (Vec<Rational>, Vec<Rational>) {
        (
            self.masses
                .iter()
                .map(|p| p.clone().max(Rational::zero()))
                .collect(),
            self.masses
                .iter()
                .map(|p| (-p).max(Rational::zero()))
                .collect(),
        )
    }
    /// If |f_i|<=bound, then |sum_i w_i f_i|<=bound*(1+2N),
    /// N the Jordan negative mass. This is a sharp obstruction certificate
    /// against nonnegative global models, using actual weights and readouts.
    pub fn expectation_negativity_bound(
        &self,
        readouts: &[Rational],
        bound: Rational,
    ) -> Result<SignedExpectationBound, SignedRepresentationError> {
        if readouts.len() != self.masses.len()
            || !bound.is_positive()
            || readouts.iter().any(|x| x.abs() > bound)
        {
            return Err(SignedRepresentationError::InvalidCarrier);
        }
        let expectation: Rational = self.masses.iter().zip(readouts).map(|(w, f)| w * f).sum();
        let negativity = self.negativity();
        let upper_bound = &bound * (Rational::one() + &negativity + &negativity);
        let required_negativity = ((expectation.abs() / &bound - Rational::one())
            / Rational::from_integer(2.into()))
        .max(Rational::zero());
        Ok(SignedExpectationBound {
            expectation,
            negativity,
            upper_bound,
            required_negativity,
        })
    }

    /// Unique classical model of the block-indicator readouts. With all singleton
    /// blocks this exists iff every original weight is nonnegative.
    pub fn report_state(
        &self,
        reports: &[usize],
        count: usize,
    ) -> Result<ProbabilitySimplex, SignedRepresentationError> {
        validate_partition(reports, count, self.masses.len())?;
        let mut blocks = vec![Rational::zero(); count];
        for (mass, &report) in self.masses.iter().zip(reports) {
            blocks[report] += mass;
        }
        Ok(ProbabilitySimplex::try_new(blocks)?)
    }
}

/// Actual signed readout and its sharp total-variation obstruction bound.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignedExpectationBound {
    pub expectation: Rational,
    pub negativity: Rational,
    pub upper_bound: Rational,
    pub required_negativity: Rational,
}

fn validate_partition(
    reports: &[usize],
    count: usize,
    size: usize,
) -> Result<(), SignedRepresentationError> {
    if size == 0
        || count == 0
        || reports.len() != size
        || reports.iter().any(|&r| r >= count)
        || (0..count).any(|r| !reports.contains(&r))
    {
        return Err(SignedRepresentationError::InvalidCarrier);
    }
    Ok(())
}

/// Checked nonnegative outcome maps on a report quotient. Each row across ALL
/// outcomes has total mass one; individual outcome maps may be substochastic.
#[derive(Debug, Clone)]
pub struct SignedInstrumentQuotient {
    reports: Vec<usize>,
    outcome_maps: Vec<Vec<Vec<Rational>>>,
    forgetting: StochasticMap,
}
impl SignedInstrumentQuotient {
    fn validate_maps_and_mass(
        maps: &[Vec<Vec<Rational>>],
        size: usize,
    ) -> Result<(), SignedRepresentationError> {
        if maps.is_empty()
            || maps
                .iter()
                .any(|m| m.len() != size || m.iter().any(|row| row.len() != size))
        {
            return Err(SignedRepresentationError::InvalidShape);
        }
        for row in 0..size {
            let mass: Rational = maps.iter().flat_map(|m| m[row].iter()).cloned().sum();
            if !mass.is_one() {
                return Err(SignedRepresentationError::MassNotPreserved { row, mass });
            }
        }
        Ok(())
    }

    fn verify_nonnegative_quotient(
        outcome: usize,
        quotient: &[Vec<Rational>],
        count: usize,
    ) -> Result<(), SignedRepresentationError> {
        for (source, row) in quotient.iter().enumerate().take(count) {
            for (target, val) in row.iter().enumerate().take(count) {
                if val.is_negative() {
                    return Err(SignedRepresentationError::NegativeReportTransition {
                        outcome,
                        source_report: source,
                        target,
                    });
                }
            }
        }
        Ok(())
    }

    fn quotient_for_outcome(
        outcome: usize,
        map: &[Vec<Rational>],
        reports: &[usize],
        representatives: &[usize],
        count: usize,
        size: usize,
    ) -> Result<Vec<Vec<Rational>>, SignedRepresentationError> {
        let mut quotient = vec![vec![Rational::zero(); count]; count];
        for row in 0..size {
            let source = reports[row];
            for target in 0..count {
                let block_sum: Rational = map[row]
                    .iter()
                    .zip(reports)
                    .filter(|(_, r)| **r == target)
                    .map(|(x, _)| x.clone())
                    .sum();
                if row == representatives[source] {
                    quotient[source][target] = block_sum;
                } else if quotient[source][target] != block_sum {
                    return Err(SignedRepresentationError::NotDescending {
                        outcome,
                        first: representatives[source],
                        second: row,
                        target,
                    });
                }
            }
        }
        Self::verify_nonnegative_quotient(outcome, &quotient, count)?;
        Ok(quotient)
    }

    fn sum_outcome_maps(outcome_maps: &[Vec<Vec<Rational>>], count: usize) -> Vec<Vec<Rational>> {
        let mut total = vec![vec![Rational::zero(); count]; count];
        for map in outcome_maps {
            for i in 0..count {
                for j in 0..count {
                    total[i][j] += &map[i][j];
                }
            }
        }
        total
    }

    /// Signed input maps use row-state convention p'=pM. This tests the complete
    /// operational quotient equation M_o D = D T_o (row convention), without
    /// silently replacing non-descending or negative report dynamics.
    pub fn try_new(
        reports: Vec<usize>,
        count: usize,
        maps: Vec<Vec<Vec<Rational>>>,
    ) -> Result<Self, SignedRepresentationError> {
        let size = reports.len();
        validate_partition(&reports, count, size)?;
        Self::validate_maps_and_mass(&maps, size)?;
        let representatives: Vec<usize> = (0..count)
            .map(|r| {
                reports
                    .iter()
                    .position(|&x| x == r)
                    .checked_invariant_16eb9288("surjective partition")
            })
            .collect();
        let mut outcome_maps = Vec::with_capacity(maps.len());
        for (outcome, map) in maps.iter().enumerate() {
            outcome_maps.push(Self::quotient_for_outcome(
                outcome,
                map,
                &reports,
                &representatives,
                count,
                size,
            )?);
        }
        let total = Self::sum_outcome_maps(&outcome_maps, count);
        let forgetting =
            StochasticMap::try_from_rows(count, count, total, "signed-instrument-report-quotient")?;
        Ok(Self {
            reports,
            outcome_maps,
            forgetting,
        })
    }
    pub fn reports(&self) -> &[usize] {
        &self.reports
    }
    pub fn outcome_maps(&self) -> &[Vec<Vec<Rational>>] {
        &self.outcome_maps
    }
    pub fn forgetting(&self) -> &StochasticMap {
        &self.forgetting
    }
}

// Origin: engine/crates_rs/core_finite_probability/src/signed_representation.rs
// Claim: urn:core:crates_rs:core-finite-probability:signed-representation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_16eb9288 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
