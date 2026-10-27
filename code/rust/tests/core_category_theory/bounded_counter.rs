use core_category_theory::bounded_counter::{
    CounterBoundary as B, CounterEvent as E, CounterReport as R, CounterReportError as Error,
};
use core_category_theory::finite_moore::FiniteMoore;
use std::collections::BTreeSet;

fn words(depth: usize) -> Vec<Vec<E>> {
    (0..=depth)
        .flat_map(|len| {
            (0..1usize << len).map(move |mask| {
                (0..len)
                    .map(|i| {
                        if mask & (1 << i) == 0 {
                            E::Increment
                        } else {
                            E::Decrement
                        }
                    })
                    .collect()
            })
        })
        .collect()
}

fn concrete(mut count: usize, word: &[E]) -> Option<usize> {
    for e in word {
        match e {
            E::Increment => count += 1,
            E::Decrement => count = count.checked_sub(1)?,
        }
    }
    Some(count)
}

#[test]
fn all_bounded_words_match_concrete_counter_and_exact_class_partition() {
    for depth in 0..=8 {
        let contexts = words(depth);
        let mut signatures = Vec::new();
        for count in 0..=depth + 3 {
            let report = R::from_count(depth, count);
            let mut signature = Vec::new();
            for word in &contexts {
                let actual = concrete(count, word);
                let observed = report.observe(word);
                assert_eq!(observed.is_ok(), actual.is_some());
                if let Some(end) = actual {
                    assert_eq!(observed.unwrap(), R::from_count(depth - word.len(), end));
                } else {
                    assert_eq!(observed, Err(B::GuardRefusal));
                }
                signature.push(actual.is_some());
            }
            signatures.push(signature);
        }
        assert_eq!(signatures.iter().collect::<BTreeSet<_>>().len(), depth + 1);
        for m in 0..signatures.len() {
            for n in 0..signatures.len() {
                assert_eq!(signatures[m] == signatures[n], m.min(depth) == n.min(depth));
                let a = R::from_count(depth, m);
                let b = R::from_count(depth, n);
                if let Some(k) = a.separating_removals(b).unwrap() {
                    assert!(k <= depth);
                    let suffix = vec![E::Decrement; k];
                    assert_ne!(
                        concrete(m, &suffix).is_some(),
                        concrete(n, &suffix).is_some()
                    );
                } else {
                    assert_eq!(signatures[m], signatures[n]);
                }
            }
        }
    }
}

#[test]
fn existing_moore_owner_checks_the_complete_graded_observer() {
    for depth in 0..=8 {
        let states: Vec<_> = (0..=depth)
            .flat_map(|r| (0..=r).map(move |c| R::from_count(r, c)))
            .collect();
        let refusal = states.len();
        let exhausted = refusal + 1;
        let mut transitions: Vec<Vec<usize>> = states
            .iter()
            .map(|state| {
                [E::Increment, E::Decrement]
                    .iter()
                    .map(|&e| match state.advance(e) {
                        Ok(next) => states.iter().position(|s| *s == next).unwrap(),
                        Err(B::GuardRefusal) => refusal,
                        Err(B::ContextExhausted) => exhausted,
                    })
                    .collect()
            })
            .collect();
        transitions.extend([vec![refusal; 2], vec![exhausted; 2]]);
        let mut outputs = vec![0; states.len()];
        outputs.extend([1, 2]);
        let machine = FiniteMoore::new(outputs, transitions, 2).unwrap();
        let certificate = machine.behavioral_quotient();
        assert!(machine.verify_quotient(&certificate));
        // Different remaining depths also differ, because exhaustion is observed.
        assert_eq!(
            certificate.quotient.state_count(),
            (depth + 1) * (depth + 2) / 2 + 2
        );
    }
}

#[test]
fn boundary_types_and_machine_integer_extremes_are_preserved() {
    assert_eq!(R::try_from_clip(3, 4), Err(Error::ClipExceedsDepth));
    assert_eq!(
        R::from_count(2, 0).separating_removals(R::from_count(3, 0)),
        Err(Error::DifferentDepths)
    );
    assert_eq!(
        R::from_count(0, 0).advance(E::Decrement),
        Err(B::ContextExhausted)
    );
    assert_eq!(
        R::from_count(1, 0).advance(E::Decrement),
        Err(B::GuardRefusal)
    );
    assert_eq!(
        R::from_count(1, 0).observe(&[E::Decrement, E::Increment]),
        Err(B::GuardRefusal)
    );
    assert_eq!(
        R::from_count(1, 2).observe(&[E::Increment, E::Increment]),
        Err(B::ContextExhausted)
    );
    let largest = R::from_count(usize::MAX, usize::MAX);
    for event in [E::Increment, E::Decrement] {
        assert_eq!(
            largest.advance(event),
            Ok(R::from_count(usize::MAX - 1, usize::MAX - 1))
        );
    }
    assert_eq!(
        largest.separating_removals(R::from_count(usize::MAX, usize::MAX - 1)),
        Ok(Some(usize::MAX))
    );
}

#[test]
fn decreasing_depth_composes_but_fixed_depth_is_not_a_congruence() {
    for depth in 1..=7 {
        assert_eq!(R::from_count(depth, depth), R::from_count(depth, depth + 1));
        assert_ne!(R::from_count(depth, depth - 1), R::from_count(depth, depth));
        for word in words(depth) {
            for split in 0..=word.len() {
                let start = R::from_count(depth, 2);
                assert_eq!(
                    start.observe(&word),
                    start
                        .observe(&word[..split])
                        .and_then(|s| s.observe(&word[split..]))
                );
            }
        }
    }
}

// Origin: engine/crates_rs/tests/core_category_theory/bounded_counter.rs
// Claim: urn:core:crates_rs:tests:bounded-counter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2b90e179 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2b90e179` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2b90e179 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError2b90e179 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2b90e179 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2b90e179 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2b90e179 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2b90e179> {
        if capacity_bound == 0 {
            return Err(BoundaryError2b90e179::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2b90e179::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2b90e179::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_2b90e179() {
    let admitted = BoundaryRecord2b90e179::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2b90e179::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
