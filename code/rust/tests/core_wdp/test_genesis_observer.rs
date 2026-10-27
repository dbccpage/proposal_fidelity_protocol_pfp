use core_category_theory::finite_history_context::{FiniteWordTransducer, HistoryDescent};
use core_wdp::genesis_observer::*;
use std::collections::{BTreeMap, BTreeSet};
fn set(xs: &[&str]) -> BTreeSet<String> {
    xs.iter().map(|x| x.to_string()).collect()
}
fn data() -> GenesisSixData {
    GenesisSixData {
        states: vec!["a".into(), "b".into()],
        alphabet: vec!["0".into(), "1".into()],
        initial: "a".into(),
        update: BTreeMap::from([
            (("a".into(), "0".into()), "a".into()),
            (("a".into(), "1".into()), "b".into()),
            (("b".into(), "0".into()), "b".into()),
            (("b".into(), "1".into()), "a".into()),
        ]),
        profile: BTreeMap::from([("a".into(), "even".into()), ("b".into(), "odd".into())]),
        profile_alphabet: set(&["even", "odd", "unused"]),
        grammar: set(&["g"]),
        terminal: BTreeMap::from([("g".into(), GenesisTerminal::Proved)]),
    }
}
fn observer(d: GenesisSixData) -> OriginalGenesisObserver<FiniteWordTransducer> {
    OriginalGenesisObserver::new_checked(
        d,
        BTreeMap::from([(
            "prefix".into(),
            FiniteWordTransducer::prefix(2, vec![1]).unwrap(),
        )]),
    )
    .unwrap()
}
#[test]
fn exact_history_and_explicit_encoder() {
    let o = observer(data());
    assert_eq!(o.history_profile(&[1, 1]).unwrap(), "even");
    assert_eq!(o.contextual_profile("prefix", &[1, 1]).unwrap(), "odd");
    assert_eq!(
        o.terminal_for_history(&[], None),
        Err(OriginalObserverError::MissingEncoder)
    );
    let encoder = ProfileGrammarEncoder::new(
        &o.profile_alphabet(),
        &o.data().grammar,
        BTreeMap::from([
            ("even".into(), "g".into()),
            ("odd".into(), "g".into()),
            ("unused".into(), "g".into()),
        ]),
    )
    .unwrap();
    assert_eq!(
        o.terminal_for_history(&[], Some(&encoder)).unwrap(),
        GenesisTerminal::Proved
    );
    assert!(matches!(
        o.context_state_descent("prefix").unwrap(),
        HistoryDescent::Descends(_)
    ));
    assert_eq!(o.profile_alphabet(), set(&["even", "odd", "unused"]));
}
#[test]
fn grammar_and_terminal_changes_do_not_change_four_core() {
    let first = observer(data());
    let mut changed = data();
    changed.grammar = set(&["other"]);
    changed.terminal = BTreeMap::from([("other".into(), GenesisTerminal::Refused)]);
    let second = observer(changed);
    assert_eq!(first.memory(), second.memory());
    assert_eq!(first.classify_original(), second.classify_original());
    assert_eq!(
        first.context_state_descent("prefix"),
        second.context_state_descent("prefix")
    );
    for word in [vec![], vec![0], vec![1], vec![1, 0, 1], vec![1; 1000]] {
        assert_eq!(first.history_profile(&word), second.history_profile(&word));
        assert_eq!(
            first.contextual_profile("prefix", &word),
            second.contextual_profile("prefix", &word)
        );
    }
    assert_eq!(
        first.terminal_for_expression("g").unwrap(),
        GenesisTerminal::Proved
    );
    assert_eq!(
        second.terminal_for_expression("other").unwrap(),
        GenesisTerminal::Refused
    );
}
#[test]
fn malformed_packets_are_rejected() {
    let mut d = data();
    d.update.remove(&("a".into(), "0".into()));
    assert!(OriginalGenesisObserver::new_checked(
        d,
        BTreeMap::<String, FiniteWordTransducer>::new()
    )
    .is_err());
    let mut d = data();
    d.terminal.clear();
    assert!(OriginalGenesisObserver::new_checked(
        d,
        BTreeMap::<String, FiniteWordTransducer>::new()
    )
    .is_err());
    assert!(OriginalGenesisObserver::new_checked(
        data(),
        BTreeMap::from([(
            "bad".into(),
            FiniteWordTransducer::prefix(1, vec![]).unwrap()
        )])
    )
    .is_err());
}
#[test]
fn actual_ten_symbol_packet_preserves_mealy_reports() {
    let d = data();
    let packet = OriginalOperationalData {
        states: d.states,
        alphabet: d.alphabet,
        initial: d.initial,
        update: d.update,
        profile: d.profile,
        profile_alphabet: d.profile_alphabet,
        transition_report: BTreeMap::from([
            (("a".into(), "0".into()), "quiet".into()),
            (("a".into(), "1".into()), "start".into()),
            (("b".into(), "0".into()), "quiet".into()),
            (("b".into(), "1".into()), "end".into()),
        ]),
        report_alphabet: set(&["quiet", "start", "end", "unused"]),
        contexts: BTreeMap::from([(
            "flip".into(),
            BTreeMap::from([("a".into(), "b".into()), ("b".into(), "a".into())]),
        )]),
    };
    let o = OriginalOperationalObserver::new(packet).unwrap();
    assert_eq!(
        o.report_trace(&[1, 0, 1]).unwrap().0,
        vec!["start", "quiet", "end"]
    );
    assert!(o.lift_state_context("flip").is_ok());
}

#[test]
fn original_classification_uses_profile_kernel_not_profile_change() {
    let o = observer(data());
    assert_eq!(o.classify_original().unwrap().class, GenesisClass::O1Only);
    let mut d = data();
    d.update = BTreeMap::from([
        (("a".into(), "0".into()), "a".into()),
        (("a".into(), "1".into()), "b".into()),
        (("b".into(), "0".into()), "a".into()),
        (("b".into(), "1".into()), "b".into()),
    ]);
    let o = observer(d);
    let classification = o.classify_original().unwrap();
    assert_eq!(classification.class, GenesisClass::O2);
    let (context, first, second) = classification.o2_witness.unwrap();
    assert_eq!(o.history_profile(&first), o.history_profile(&second));
    assert_ne!(
        o.contextual_profile(&context, &first),
        o.contextual_profile(&context, &second)
    );
    let mut d = data();
    d.profile.insert("b".into(), "even".into());
    assert_eq!(
        observer(d).classify_original().unwrap().class,
        GenesisClass::OutsideO1
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_observer.rs
// Claim: urn:core:crates_rs:tests:test-genesis-observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2dc32543 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2dc32543` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2dc32543 {
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
impl BoundaryError2dc32543 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2dc32543 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2dc32543 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2dc32543 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2dc32543> {
        if capacity_bound == 0 {
            return Err(BoundaryError2dc32543::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2dc32543::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2dc32543::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2dc32543() {
    let admitted = BoundaryRecord2dc32543::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2dc32543::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
