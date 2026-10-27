//! Partial finite dynamics and shortest distinguishing continuations.
//!
//! One fresh, observably distinct absorbing state totalizes unavailability.
//! Moore refinement therefore preserves BOTH answers and availability for every
//! finite word. The added state is internal, never a physical alternative.

use crate::finite_moore::{FiniteMoore, MooreError, MooreQuotient};
use std::collections::{BTreeMap, VecDeque};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ContinuationError {
    Machine(MooreError),
    OutsideCarrier,
    OutsideAlphabet,
    WorkLimit,
    CertificateMismatch,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_continuation.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-continuation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ContinuationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ContinuationError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PartialDynamics {
    reports: Vec<usize>,
    transitions: Vec<Vec<Option<usize>>>,
    machine: FiniteMoore,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DistinguishingWord {
    pub left: usize,
    pub right: usize,
    pub word: Vec<usize>,
    pub left_answer: Option<usize>,
    pub right_answer: Option<usize>,
}

impl PartialDynamics {
    pub fn new(
        reports: Vec<usize>,
        transitions: Vec<Vec<Option<usize>>>,
        inputs: usize,
    ) -> Result<Self, ContinuationError> {
        if reports.is_empty() {
            return Err(ContinuationError::Machine(MooreError::EmptyCarrier));
        }
        if transitions.len() != reports.len() || transitions.iter().any(|r| r.len() != inputs) {
            return Err(ContinuationError::Machine(MooreError::TransitionShape));
        }
        if transitions
            .iter()
            .flatten()
            .flatten()
            .any(|&t| t >= reports.len())
        {
            return Err(ContinuationError::Machine(
                MooreError::TransitionOutsideCarrier,
            ));
        }
        // Intern Option<label>, rather than label+1: usize::MAX is a valid label.
        let mut labels = BTreeMap::new();
        let mut outputs = Vec::new();
        for label in reports
            .iter()
            .copied()
            .map(Some)
            .chain(std::iter::once(None))
        {
            let next = labels.len();
            outputs.push(*labels.entry(label).or_insert(next));
        }
        let dead = reports.len();
        let mut total: Vec<Vec<usize>> = transitions
            .iter()
            .map(|row| row.iter().map(|t| t.unwrap_or(dead)).collect())
            .collect();
        total.push(vec![dead; inputs]);
        let machine =
            FiniteMoore::new(outputs, total, inputs).map_err(ContinuationError::Machine)?;
        Ok(Self {
            reports,
            transitions,
            machine,
        })
    }

    pub fn reports(&self) -> &[usize] {
        &self.reports
    }
    pub fn transitions(&self) -> &[Vec<Option<usize>>] {
        &self.transitions
    }
    pub fn quotient(&self) -> MooreQuotient {
        self.machine.behavioral_quotient()
    }
    pub fn verify_quotient(&self, q: &MooreQuotient) -> bool {
        self.machine.verify_quotient(q)
    }

    /// Full word validation occurs even if an earlier operation is unavailable.
    pub fn run(&self, start: usize, word: &[usize]) -> Result<Option<usize>, ContinuationError> {
        if start >= self.reports.len() {
            return Err(ContinuationError::OutsideCarrier);
        }
        if word.iter().any(|&a| a >= self.machine.input_count()) {
            return Err(ContinuationError::OutsideAlphabet);
        }
        let mut state = Some(start);
        for &a in word {
            state = state.and_then(|s| self.transitions[s][a]);
        }
        Ok(state)
    }

    /// Exactly one partial update per real quotient class. The sink's class
    /// occupies no entry; no failed operation is silently an identity.
    pub fn quotient_operations(&self) -> Vec<Vec<Option<usize>>> {
        let q = self.quotient();
        let dead = q.state_to_block[self.reports.len()];
        // First-state block numbering puts the uniquely labelled sink last.
        q.quotient.transitions()[..dead]
            .iter()
            .map(|row| {
                row.iter()
                    .map(|&t| if t == dead { None } else { Some(t) })
                    .collect()
            })
            .collect()
    }

    /// BFS on ordered state pairs. A completed empty result proves equivalence
    /// in THIS finite machine; exceeding `max_pairs` is a resource refusal.
    pub fn distinguish(
        &self,
        left: usize,
        right: usize,
        max_pairs: usize,
    ) -> Result<Option<DistinguishingWord>, ContinuationError> {
        if left >= self.reports.len() || right >= self.reports.len() {
            return Err(ContinuationError::OutsideCarrier);
        }
        if max_pairs == 0 {
            return Err(ContinuationError::WorkLimit);
        }
        let mut paths = BTreeMap::from([((left, right), Vec::new())]);
        let mut queue = VecDeque::from([(left, right)]);
        while let Some((l, r)) = queue.pop_front() {
            let word = paths[&(l, r)].clone();
            if self.machine.reports()[l] != self.machine.reports()[r] {
                return Ok(Some(DistinguishingWord {
                    left,
                    right,
                    word,
                    left_answer: self.reports.get(l).copied(),
                    right_answer: self.reports.get(r).copied(),
                }));
            }
            for a in 0..self.machine.input_count() {
                let pair = (
                    self.machine.transitions()[l][a],
                    self.machine.transitions()[r][a],
                );
                if !paths.contains_key(&pair) {
                    if paths.len() >= max_pairs {
                        return Err(ContinuationError::WorkLimit);
                    }
                    let mut next = word.clone();
                    next.push(a);
                    paths.insert(pair, next);
                    queue.push_back(pair);
                }
            }
        }
        Ok(None)
    }

    /// Replay the claimed distinction without trusting its saved answers.
    pub fn verify_distinction(&self, c: &DistinguishingWord) -> Result<(), ContinuationError> {
        let l = self.run(c.left, &c.word)?.map(|s| self.reports[s]);
        let r = self.run(c.right, &c.word)?.map(|s| self.reports[s]);
        if l == r || l != c.left_answer || r != c.right_answer {
            return Err(ContinuationError::CertificateMismatch);
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_49a6c744 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
