//! Finite rational marginal compatibility and minimax L1 repair formulation.
//! Owns the probability model and LP reduction; generic solvers stay outside.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_7eeb40e4<T> {
    fn checked_invariant_7eeb40e4(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_7eeb40e4<T> for Option<T> {
    #[inline]
    fn checked_invariant_7eeb40e4(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_7eeb40e4<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_7eeb40e4(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational as Q;
use num_traits::{One, Signed, Zero};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum MarginalError {
    #[error("invalid marginal scenario, probability or radius")]
    InvalidInput,
    #[error("declared section enumeration budget exceeded")]
    BudgetExhausted,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MarginalScenario {
    measurements: usize,
    outcomes: usize,
    contexts: Vec<Vec<usize>>,
    sections: Vec<Vec<Vec<usize>>>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepairProgram {
    pub costs: Vec<Q>,
    pub matrix: Vec<Vec<Q>>,
    pub rhs: Vec<Q>,
    pub probability_count: usize,
    pub radius_column: usize,
}

fn sections(
    outcomes: usize,
    width: usize,
    budget: usize,
) -> Result<Vec<Vec<usize>>, MarginalError> {
    let mut count = 1usize;
    for _ in 0..width {
        count = count
            .checked_mul(outcomes)
            .ok_or(MarginalError::BudgetExhausted)?;
        if count > budget {
            return Err(MarginalError::BudgetExhausted);
        }
    }
    Ok((0..count)
        .map(|mut index| {
            let mut assignment = vec![0; width];
            for j in (0..width).rev() {
                assignment[j] = index % outcomes;
                index /= outcomes;
            }
            assignment
        })
        .collect())
}

fn restrict(section: &[usize], context: &[usize], overlap: &[usize]) -> Vec<usize> {
    overlap
        .iter()
        .map(|x| section[context.binary_search(x).checked_invariant_7eeb40e4("checked invariant")])
        .collect()
}

impl MarginalScenario {
    pub fn new(
        measurements: usize,
        outcomes: usize,
        contexts: Vec<Vec<usize>>,
        max_sections: usize,
    ) -> Result<Self, MarginalError> {
        if measurements == 0
            || outcomes == 0
            || contexts.is_empty()
            || contexts.iter().any(|c| {
                c.is_empty()
                    || c.windows(2).any(|p| p[0] >= p[1])
                    || c.iter().any(|&x| x >= measurements)
            })
        {
            return Err(MarginalError::InvalidInput);
        }
        let mut remaining = max_sections;
        let mut all = Vec::new();
        for context in &contexts {
            let local = sections(outcomes, context.len(), remaining)?;
            remaining -= local.len();
            all.push(local);
        }
        Ok(Self {
            measurements,
            outcomes,
            contexts,
            sections: all,
        })
    }
    pub fn measurements(&self) -> usize {
        self.measurements
    }
    pub fn outcomes(&self) -> usize {
        self.outcomes
    }
    pub fn contexts(&self) -> &[Vec<usize>] {
        &self.contexts
    }
    pub fn sections(&self) -> &[Vec<Vec<usize>>] {
        &self.sections
    }

    pub fn validate_probabilities(&self, probabilities: &[Vec<Q>]) -> Result<(), MarginalError> {
        if probabilities.len() != self.contexts.len()
            || probabilities.iter().zip(&self.sections).any(|(p, s)| {
                p.len() != s.len()
                    || p.iter()
                        .any(|q| !q.denom().is_positive() || q.is_negative())
                    || p.iter().cloned().sum::<Q>() != Q::one()
            })
        {
            return Err(MarginalError::InvalidInput);
        }
        Ok(())
    }

    pub fn compatible(&self, probabilities: &[Vec<Q>]) -> Result<bool, MarginalError> {
        self.validate_probabilities(probabilities)?;
        for i in 0..self.contexts.len() {
            for j in i + 1..self.contexts.len() {
                let overlap: Vec<usize> = self.contexts[i]
                    .iter()
                    .copied()
                    .filter(|x| self.contexts[j].contains(x))
                    .collect();
                for section in sections(self.outcomes, overlap.len(), self.sections[i].len())? {
                    let marginal = |k: usize| {
                        self.sections[k]
                            .iter()
                            .zip(&probabilities[k])
                            .filter(|(s, _)| restrict(s, &self.contexts[k], &overlap) == section)
                            .map(|(_, p)| p.clone())
                            .sum::<Q>()
                    };
                    if marginal(i) != marginal(j) {
                        return Ok(false);
                    }
                }
            }
        }
        Ok(true)
    }

    pub fn minimax_distance(&self, a: &[Vec<Q>], b: &[Vec<Q>]) -> Result<Q, MarginalError> {
        self.validate_probabilities(a)?;
        self.validate_probabilities(b)?;
        Ok(a.iter()
            .zip(b)
            .map(|(x, y)| x.iter().zip(y).map(|(u, v)| (u - v).abs()).sum::<Q>())
            .max()
            .checked_invariant_7eeb40e4("checked invariant"))
    }

    fn append_local_context_rows(
        local: &[Q],
        i: usize,
        offset: usize,
        n: usize,
        variables: usize,
        matrix: &mut Vec<Vec<Q>>,
        rhs: &mut Vec<Q>,
    ) {
        let mut row = vec![Q::zero(); variables];
        for j in 0..local.len() {
            row[offset + j] = Q::one();
        }
        matrix.push(row);
        rhs.push(Q::one());
        for (j, value) in local.iter().enumerate() {
            let at = offset + j;
            let mut positive = vec![Q::zero(); variables];
            positive[at] = Q::one();
            positive[n + at] = -Q::one();
            positive[2 * n + 1 + at] = Q::one();
            matrix.push(positive);
            rhs.push(value.clone());
            let mut negative = vec![Q::zero(); variables];
            negative[at] = -Q::one();
            negative[n + at] = -Q::one();
            negative[3 * n + 1 + at] = Q::one();
            matrix.push(negative);
            rhs.push(-value.clone());
        }
        let mut row = vec![Q::zero(); variables];
        for j in 0..local.len() {
            row[n + offset + j] = Q::one();
        }
        row[2 * n] = -Q::one();
        row[4 * n + 1 + i] = Q::one();
        matrix.push(row);
        rhs.push(Q::zero());
    }

    fn append_overlap_rows(
        &self,
        i: usize,
        j: usize,
        offsets: &[usize],
        variables: usize,
        matrix: &mut Vec<Vec<Q>>,
        rhs: &mut Vec<Q>,
    ) -> Result<(), MarginalError> {
        let overlap: Vec<usize> = self.contexts[i]
            .iter()
            .copied()
            .filter(|x| self.contexts[j].contains(x))
            .collect();
        for shared in sections(self.outcomes, overlap.len(), self.sections[i].len())? {
            let mut row = vec![Q::zero(); variables];
            for (at, s) in self.sections[i].iter().enumerate() {
                if restrict(s, &self.contexts[i], &overlap) == shared {
                    row[offsets[i] + at] = Q::one();
                }
            }
            for (at, s) in self.sections[j].iter().enumerate() {
                if restrict(s, &self.contexts[j], &overlap) == shared {
                    row[offsets[j] + at] -= Q::one();
                }
            }
            matrix.push(row);
            rhs.push(Q::zero());
        }
        Ok(())
    }

    /// Variables: repaired p, coordinate error envelopes d, radius t,
    /// positive/negative inequality slacks, and per-context radius slacks.
    pub fn repair_program(&self, source: &[Vec<Q>]) -> Result<RepairProgram, MarginalError> {
        self.validate_probabilities(source)?;
        let n: usize = self.sections.iter().map(Vec::len).sum();
        let k = self.contexts.len();
        let variables = 4 * n + 1 + k;
        let mut costs = vec![Q::zero(); variables];
        costs[2 * n] = Q::one();
        let mut matrix = Vec::new();
        let mut rhs = Vec::new();
        let mut offsets = Vec::new();
        let mut offset = 0;
        for (i, local) in source.iter().enumerate() {
            offsets.push(offset);
            Self::append_local_context_rows(local, i, offset, n, variables, &mut matrix, &mut rhs);
            offset += local.len();
        }
        for i in 0..k {
            for j in i + 1..k {
                self.append_overlap_rows(i, j, &offsets, variables, &mut matrix, &mut rhs)?;
            }
        }
        Ok(RepairProgram {
            costs,
            matrix,
            rhs,
            probability_count: n,
            radius_column: 2 * n,
        })
    }

    pub fn unpack(&self, primal: &[Q]) -> Result<Vec<Vec<Q>>, MarginalError> {
        if primal.len() < self.sections.iter().map(Vec::len).sum() {
            return Err(MarginalError::InvalidInput);
        }
        let mut offset = 0;
        let mut result = Vec::new();
        for sections in &self.sections {
            result.push(primal[offset..offset + sections.len()].to_vec());
            offset += sections.len();
        }
        self.validate_probabilities(&result)?;
        Ok(result)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SamplingBound {
    trials: usize,
    outcome_count: usize,
    l1_radius: Q,
    failure_upper: Q,
}

impl SamplingBound {
    pub fn trials(&self) -> usize {
        self.trials
    }
    pub fn outcome_count(&self) -> usize {
        self.outcome_count
    }
    pub fn l1_radius(&self) -> &Q {
        &self.l1_radius
    }
    pub fn failure_upper(&self) -> &Q {
        &self.failure_upper
    }
}

/// Under iid categorical trials: E||f-p||_1^2 <= (m-1)/n.
/// Markov gives this exact rational probability bound, uniformly in p.
/// This is a conditional theorem; data do not certify the iid premise.
pub fn iid_l1_sampling_bound(
    trials: usize,
    outcome_count: usize,
    radius: Q,
) -> Result<SamplingBound, MarginalError> {
    if trials == 0 || outcome_count == 0 || !radius.denom().is_positive() || !radius.is_positive() {
        return Err(MarginalError::InvalidInput);
    }
    let failure = if radius >= Q::from_integer(2.into()) {
        Q::zero()
    } else {
        (Q::from_integer((outcome_count - 1).into())
            / (Q::from_integer(trials.into()) * &radius * &radius))
            .min(Q::one())
    };
    Ok(SamplingBound {
        trials,
        outcome_count,
        l1_radius: radius,
        failure_upper: failure,
    })
}

/// No independence between context experiments is needed for the union bound.
pub fn joint_sampling_failure(bounds: &[SamplingBound]) -> Q {
    bounds
        .iter()
        .map(|b| b.failure_upper.clone())
        .sum::<Q>()
        .min(Q::one())
}

// Origin: engine/crates_rs/core_finite_probability/src/marginal_compatibility.rs
// Claim: urn:core:crates_rs:core-finite-probability:marginal-compatibility:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn q(n: i64) -> Q {
        Q::from_integer(n.into())
    }
    #[test]
    fn three_contexts_and_typed_distribution_checks() {
        let site = MarginalScenario::new(1, 2, vec![vec![0]; 3], 10).unwrap();
        assert!(site.compatible(&vec![vec![q(1), q(0)]; 3]).unwrap());
        assert!(!site
            .compatible(&[vec![q(1), q(0)], vec![q(0), q(1)], vec![q(1), q(0)]])
            .unwrap());
        assert!(site
            .validate_probabilities(&vec![vec![q(2), q(-1)]; 3])
            .is_err());
        assert!(MarginalScenario::new(2, 2, vec![vec![0, 1]], 3).is_err());
    }
    #[test]
    fn rational_sampling_and_cross_context_union() {
        let bound = iid_l1_sampling_bound(400, 2, Q::new(1.into(), 10.into())).unwrap();
        assert_eq!(bound.failure_upper, Q::new(1.into(), 4.into()));
        assert_eq!(
            joint_sampling_failure(&[bound.clone(), bound]),
            Q::new(1.into(), 2.into())
        );
        assert_eq!(
            iid_l1_sampling_bound(1, 100, q(2)).unwrap().failure_upper,
            q(0)
        );
        assert!(iid_l1_sampling_bound(0, 2, q(1)).is_err());
    }
}
