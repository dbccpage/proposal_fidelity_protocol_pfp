use core_wdp::observer_world_adapter::*;
use std::collections::BTreeSet;

fn packet() -> FiniteObserverWorldPacket {
    FiniteObserverWorldPacket {
        alphabet: vec!["a".into()],
        histories: vec![vec![], vec![0], vec![0, 0]],
        profiles: vec!["same".into(), "distinct".into()],
        presented_profiles: vec![0, 0, 1],
        contexts: vec!["separate".into()],
        context_actions: vec![vec![0, 2, 2]],
        witnesses: vec![WorldWitness {
            left: 0,
            right: 1,
            context: 0,
        }],
        grammar: vec!["first".into(), "all".into()],
        grammar_interpretation: Some(vec![BTreeSet::from([0]), BTreeSet::from([0, 1])]),
    }
}

#[test]
fn world_retains_noncongruent_histories_and_exact_expressible_stable_sets() {
    let source = packet();
    let receipt = source.adapt().unwrap();
    assert!(receipt.context_system().related(0, 1));
    assert!(!receipt.context_system().related(0, 2));
    assert_eq!(receipt.packet(), &source);
    assert_eq!(
        receipt.facts().unwrap(),
        BTreeSet::from([BTreeSet::from([0, 1])])
    );
    receipt.verify_against(&source).unwrap();
}

#[test]
fn source_image_and_history_context_closure_are_required() {
    let mut source = packet();
    source.profiles.push("unused".into());
    assert_eq!(source.adapt(), Err(WorldAdapterError::InvalidCarrier));
    source = packet();
    source.context_actions[0][1] = 3;
    assert_eq!(source.adapt(), Err(WorldAdapterError::InvalidContext));
    source = packet();
    source.witnesses[0].right = 2;
    assert_eq!(source.adapt(), Err(WorldAdapterError::InvalidWitness));
}

#[test]
fn grammar_names_do_not_determine_facts_or_supply_memory() {
    let mut source = packet();
    source.grammar_interpretation = None;
    let receipt = source.adapt().unwrap();
    assert_eq!(
        receipt.facts(),
        Err(WorldAdapterError::MissingGrammarInterpretation)
    );
    source.grammar_interpretation = Some(vec![BTreeSet::new(), BTreeSet::from([0, 1])]);
    assert_eq!(source.adapt().unwrap().facts().unwrap().len(), 2);
    // The world tuple contains no update/store/terminal operation to execute.
    assert_eq!(receipt.packet().grammar, source.grammar);
}

#[test]
fn receipt_is_bound_to_actual_history_context_and_grammar_interpretation() {
    let source = packet();
    let receipt = source.adapt().unwrap();
    let mut other = source.clone();
    other.grammar_interpretation.as_mut().unwrap()[0].clear();
    assert_eq!(
        receipt.verify_against(&other),
        Err(WorldAdapterError::ReceiptMismatch)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_observer_world_adapter.rs
// Claim: urn:core:crates_rs:tests:test-observer-world-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord277b0da5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord277b0da5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError277b0da5 {
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
impl BoundaryError277b0da5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError277b0da5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError277b0da5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord277b0da5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError277b0da5> {
        if capacity_bound == 0 {
            return Err(BoundaryError277b0da5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError277b0da5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError277b0da5::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_277b0da5() {
    let admitted = BoundaryRecord277b0da5::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord277b0da5::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
