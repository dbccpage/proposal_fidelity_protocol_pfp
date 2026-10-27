//! Exact finite deterministic labelled systems and their minimal report quotient.
//!
//! This is finite coalgebra mathematics, independent of WDP naming/retention.
//! Reports and input labels are caller-interned identifiers: report equality is
//! literal equality, not a tolerance or an undeclared equivalence closure.
//! No initial state or chronological total order is required.
//! Exact finite deterministic labelled systems and their minimal report quotient.
//!
//! This is finite coalgebra mathematics, independent of WDP naming/retention.
//! Reports and input labels are caller-interned identifiers: report equality is
//! literal equality, not a tolerance or an undeclared equivalence closure.
//! No initial state or chronological total order is required.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_ac1d936f<T> {
    fn checked_invariant_ac1d936f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_ac1d936f<T> for Option<T> {
    #[inline]
    fn checked_invariant_ac1d936f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_ac1d936f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_ac1d936f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MooreError {
    EmptyCarrier,
    TransitionShape,
    TransitionOutsideCarrier,
    InvalidPartition,
    InvalidQuotientMap,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_moore.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-moore:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MooreError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MooreError {}

/// A total finite Moore system: `transitions[m][i] = u(m,i)`.
/// A total finite Moore system: `transitions[m][i] = u(m,i)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteMoore {
    reports: Vec<usize>,
    transitions: Vec<Vec<usize>>,
    input_count: usize,
}

/// Replayable refinement chain, beginning at the readout kernel and ending at
/// its greatest transition-stable refinement. IDs use first-state order.
/// Replayable refinement chain, beginning at the readout kernel and ending at
/// its greatest transition-stable refinement. IDs use first-state order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MooreQuotient {
    pub partitions: Vec<Vec<usize>>,
    pub state_to_block: Vec<usize>,
    pub quotient: FiniteMoore,
}

fn normalize<T: Ord>(signatures: impl IntoIterator<Item = T>) -> Vec<usize> {
    let mut ids = BTreeMap::new();
    signatures
        .into_iter()
        .map(|signature| {
            let fresh = ids.len();
            *ids.entry(signature).or_insert(fresh)
        })
        .collect()
}

// Reuse the scan's scratch signature;only a fresh stored map key owns a copy.
fn intern_signature(ids: &mut BTreeMap<Vec<usize>, usize>, signature: &[usize]) -> usize {
    if let Some(&existing) = ids.get(signature) {
        return existing;
    }
    let fresh = ids.len();
    ids.insert(signature.to_vec(), fresh);
    fresh
}

impl FiniteMoore {
    pub fn new(
        reports: Vec<usize>,
        transitions: Vec<Vec<usize>>,
        input_count: usize,
    ) -> Result<Self, MooreError> {
        if reports.is_empty() {
            return Err(MooreError::EmptyCarrier);
        }
        if transitions.len() != reports.len()
            || transitions.iter().any(|row| row.len() != input_count)
        {
            return Err(MooreError::TransitionShape);
        }
        if transitions
            .iter()
            .flatten()
            .any(|&state| state >= reports.len())
        {
            return Err(MooreError::TransitionOutsideCarrier);
        }
        Ok(Self {
            reports,
            transitions,
            input_count,
        })
    }

    pub fn reports(&self) -> &[usize] {
        &self.reports
    }
    pub fn transitions(&self) -> &[Vec<usize>] {
        &self.transitions
    }
    pub fn input_count(&self) -> usize {
        self.input_count
    }
    pub fn state_count(&self) -> usize {
        self.reports.len()
    }

    fn initial_partition(&self) -> Vec<usize> {
        normalize(self.reports.iter().copied())
    }

    fn refine(&self, partition: &[usize]) -> Vec<usize> {
        let mut ids = BTreeMap::new();
        let mut signature = Vec::new();
        let mut refined = Vec::with_capacity(self.state_count());
        for state in 0..self.state_count() {
            signature.clear();
            signature.push(partition[state]);
            signature.extend(self.transitions[state].iter().map(|&next| partition[next]));
            refined.push(intern_signature(&mut ids, &signature));
        }
        refined
    }

    fn pair_preserves(&self, partition: &[usize], left: usize, right: usize) -> bool {
        partition[left] != partition[right]
            || (self.reports[left] == self.reports[right]
                && (0..self.input_count).all(|input| {
                    partition[self.transitions[left][input]] == partition[self.transitions[right][input]]
                }))
    }

    /// A congruence is an equivalence partition whose related states have equal
    /// reports and related successors for every label.
    /// A congruence is an equivalence partition whose related states have equal
    /// reports and related successors for every label.
    pub fn is_report_congruence(&self, partition: &[usize]) -> bool {
        if partition.len() != self.state_count() {
            return false;
        }
        (0..self.state_count()).all(|state| {
            (0..state).all(|previous| self.pair_preserves(partition, state, previous))
        })
    }

    /// R0 = ker(report), R(k+1) = Rk intersect all labelled inverse images of Rk.
    /// Strict refinement increases block count, so at most |M|-1 strict splits
    /// occur. At a fixed point the relation is a bisimulation/congruence. Every
    /// readout-respecting congruence is contained in every Rk by induction, so
    /// the fixed point is the greatest one. Equivalently it compares all finite
    /// input-tree paths, including the empty path.
    /// R0 = ker(report), R(k+1) = Rk intersect all labelled inverse images of Rk.
    /// Strict refinement increases block count, so at most |M|-1 strict splits
    /// occur. At a fixed point the relation is a bisimulation/congruence. Every
    /// readout-respecting congruence is contained in every Rk by induction, so
    /// the fixed point is the greatest one. Equivalently it compares all finite
    /// input-tree paths, including the empty path.
    pub fn behavioral_quotient(&self) -> MooreQuotient {
        let mut partitions = vec![self.initial_partition()];
        loop {
            let next = self.refine(partitions.last().checked_invariant_ac1d936f("checked invariant"));
            if next == *partitions.last().checked_invariant_ac1d936f("checked invariant") {
                break;
            }
            partitions.push(next);
        }
        let state_to_block = partitions.last().checked_invariant_ac1d936f("checked invariant").clone();
        let count = state_to_block.iter().copied().max().checked_invariant_ac1d936f("checked invariant") + 1;
        let mut representatives = vec![None; count];
        for (state, &block) in state_to_block.iter().enumerate() {
            if representatives[block].is_none() {
                representatives[block] = Some(state);
            }
        }
        let representatives: Vec<_> = representatives.into_iter().map(Option::unwrap).collect();
        let quotient = Self::new(
            representatives.iter().map(|&s| self.reports[s]).collect(),
            representatives
                .iter()
                .map(|&s| {
                    self.transitions[s]
                        .iter()
                        .map(|&t| state_to_block[t])
                        .collect()
                })
                .collect(),
            self.input_count,
        )
        .checked_invariant_ac1d936f("stable partition defines a total quotient");
        MooreQuotient {
            partitions,
            state_to_block,
            quotient,
        }
    }

    /// Verify the entire submitted chain against this problem, including its
    /// origin, exact refinement steps, stabilization and quotient operations.
    /// Comparing only a stable partition would certify an arbitrary overrefinement.
    /// Verify the entire submitted chain against this problem, including its
    /// origin, exact refinement steps, stabilization and quotient operations.
    /// Comparing only a stable partition would certify an arbitrary overrefinement.
    pub fn verify_quotient(&self, receipt: &MooreQuotient) -> bool {
        if receipt.partitions.first() != Some(&self.initial_partition()) {
            return false;
        }
        for pair in receipt.partitions.windows(2) {
            if pair[0].len() != self.state_count()
                || self.refine(&pair[0]) != pair[1]
                || pair[0] == pair[1]
            {
                return false;
            }
        }
        let Some(last) = receipt.partitions.last() else {
            return false;
        };
        if last.len() != self.state_count()
            || self.refine(last) != *last
            || receipt.state_to_block != *last
        {
            return false;
        }
        // Reconstructing checks report labels, quotient typing and all labels.
        // Reconstructing checks report labels, quotient typing and all labels.
        let checked = self.behavioral_quotient();
        receipt.quotient == checked.quotient
    }

    /// Given a surjective readout/transition-preserving map f:M->N, produce the
    /// unique map g:N->M/~ satisfying g(f(m))=[m]. Kernel(f) is a congruence,
    /// hence lies inside ~. This proves |M/~| <= |N| and the minimal quotient
    /// property. The factor also preserves every report and labelled update.
    /// Given a surjective readout/transition-preserving map f:M->N, produce the
    /// unique map g:N->M/~ satisfying g(f(m))=[m]. Kernel(f) is a congruence,
    /// hence lies inside ~. This proves |M/~| <= |N| and the minimal quotient
    /// property. The factor also preserves every report and labelled update.
    pub fn factor_surjective_quotient(
        &self,
        target: &Self,
        map: &[usize],
    ) -> Result<Vec<usize>, MooreError> {
        if !self.valid_quotient_map_shape(target, map) {
            return Err(MooreError::InvalidQuotientMap);
        }
        for state in 0..self.state_count() {
            if !self.preserves_quotient_at(target, map, state) {
                return Err(MooreError::InvalidQuotientMap);
            }
        }
        let minimal = self.behavioral_quotient();
        let mut factor = vec![None; target.state_count()];
        for m in 0..self.state_count() {
            let block = minimal.state_to_block[m];
            match factor[map[m]] {
                Some(prior) if prior != block => return Err(MooreError::InvalidQuotientMap),
                _ => factor[map[m]] = Some(block),
            }
        }
        Ok(factor.into_iter().map(Option::unwrap).collect())
    }

    fn valid_quotient_map_shape(&self, target: &Self, map: &[usize]) -> bool {
        self.input_count == target.input_count
            && map.len() == self.state_count()
            && map.iter().all(|&state| state < target.state_count())
            && map.iter().copied().collect::<BTreeSet<_>>().len() == target.state_count()
    }

    fn preserves_quotient_at(&self, target: &Self, map: &[usize], state: usize) -> bool {
        self.reports[state] == target.reports[map[state]]
            && (0..self.input_count).all(|input| {
                map[self.transitions[state][input]] == target.transitions[map[state]][input]
            })
    }

    /// Unpointed classification: the machines realize the same set of labelled
    /// report behaviors. Refinement of their disjoint union computes cross-model
    /// bisimulation. Every block must meet both carriers. Thus their minimal
    /// quotients are canonically isomorphic by their common behavior classes.
    /// Reports and input indices must use the same externally declared labels.
    /// Unpointed classification: the machines realize the same set of labelled
    /// report behaviors. Refinement of their disjoint union computes cross-model
    /// bisimulation. Every block must meet both carriers. Thus their minimal
    /// quotients are canonically isomorphic by their common behavior classes.
    /// Reports and input indices must use the same externally declared labels.
    pub fn same_behavior_set(&self, other: &Self) -> bool {
        if self.input_count != other.input_count {
            return false;
        }
        let offset = self.state_count();
        let mut reports = self.reports.clone();
        reports.extend_from_slice(&other.reports);
        let mut transitions = self.transitions.clone();
        transitions.extend(
            other
                .transitions
                .iter()
                .map(|row| row.iter().map(|&s| s + offset).collect()),
        );
        let union = Self::new(reports, transitions, self.input_count).checked_invariant_ac1d936f("checked invariant");
        let blocks = union.behavioral_quotient().state_to_block;
        blocks[..offset].iter().copied().collect::<BTreeSet<_>>()
            == blocks[offset..].iter().copied().collect::<BTreeSet<_>>()
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn delayed_distinctions_and_nontrivial_blocks() {
        // Three-step distinctions and equivalent duplicates: refinement must
        // preserve integer block IDs rather than collapsing them to booleans.
        // Three-step distinctions and equivalent duplicates: refinement must
        // preserve integer block IDs rather than collapsing them to booleans.
        let m = FiniteMoore::new(
            vec![0, 0, 0, 0, 1, 1],
            vec![vec![1], vec![2], vec![4], vec![4], vec![4], vec![5]],
            1,
        )
        .unwrap();
        let q = m.behavioral_quotient();
        assert_eq!(q.state_to_block, vec![0, 1, 2, 2, 3, 3]);
        assert_eq!(q.partitions.len(), 3);
        assert!(m.verify_quotient(&q));
        assert!(m.is_report_congruence(&q.state_to_block));
        assert_eq!(q.quotient.behavioral_quotient().quotient, q.quotient);
    }

    #[test]
    fn quotient_universal_factor_and_classification() {
        let m = FiniteMoore::new(vec![0, 0, 1], vec![vec![2], vec![2], vec![2]], 1).unwrap();
        let q = m.behavioral_quotient();
        assert_eq!(
            m.factor_surjective_quotient(&q.quotient, &q.state_to_block)
                .unwrap(),
            vec![0, 1]
        );
        assert_eq!(
            m.factor_surjective_quotient(&m, &[0, 1, 2]).unwrap(),
            q.state_to_block
        );
        assert!(m.same_behavior_set(&q.quotient));
        let renamed = FiniteMoore::new(vec![1, 0], vec![vec![0], vec![0]], 1).unwrap();
        assert!(m.same_behavior_set(&renamed));
        let false_target = FiniteMoore::new(vec![0], vec![vec![0]], 1).unwrap();
        assert!(m
            .factor_surjective_quotient(&false_target, &[0, 0, 0])
            .is_err());
        assert!(!m.same_behavior_set(&false_target));
    }

    #[test]
    fn receipt_rejects_stable_overrefinement_and_forged_reports() {
        let m = FiniteMoore::new(vec![7, 7], vec![vec![0], vec![1]], 1).unwrap();
        let mut q = m.behavioral_quotient();
        q.partitions = vec![vec![0, 1]];
        q.state_to_block = vec![0, 1];
        q.quotient = m.clone();
        assert!(!m.verify_quotient(&q));
        let mut q = m.behavioral_quotient();
        q.quotient = FiniteMoore::new(vec![9], vec![vec![0]], 1).unwrap();
        assert!(!m.verify_quotient(&q));
    }

    #[test]
    fn totality_and_empty_alphabet() {
        assert!(FiniteMoore::new(vec![0, 1], vec![vec![0], vec![]], 1).is_err());
        assert!(FiniteMoore::new(vec![0], vec![vec![1]], 1).is_err());
        let static_reports =
            FiniteMoore::new(vec![0, 1, 0], vec![vec![], vec![], vec![]], 0).unwrap();
        assert_eq!(
            static_reports.behavioral_quotient().state_to_block,
            vec![0, 1, 0]
        );
    }
    #[test]
    fn exhaustive_three_state_greatest_congruence() {
        let partitions = [
            vec![0, 0, 0],
            vec![0, 0, 1],
            vec![0, 1, 0],
            vec![0, 1, 1],
            vec![0, 1, 2],
        ];
        for output_bits in 0..8 {
            for transition_code in 0..27 {
                let reports = (0..3).map(|i| (output_bits >> i) & 1).collect();
                let mut digits = transition_code;
                let transitions = (0..3)
                    .map(|_| {
                        let next = digits % 3;
                        digits /= 3;
                        vec![next]
                    })
                    .collect();
                let machine = FiniteMoore::new(reports, transitions, 1).unwrap();
                let quotient = machine.behavioral_quotient();
                assert!(machine.verify_quotient(&quotient));
                assert!(quotient.partitions.len() <= machine.state_count());
                for candidate in &partitions {
                    if machine.is_report_congruence(candidate) {
                        for s in 0..3 {
                            for t in 0..3 {
                                if candidate[s] == candidate[t] {
                                    assert_eq!(
                                        quotient.state_to_block[s],
                                        quotient.state_to_block[t]
                                    );
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
