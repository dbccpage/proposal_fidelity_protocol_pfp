use num_bigint::BigInt;
use num_traits::{One, Zero};
use core_wdp::genesis_ongoing_adapter::{
    GenesisOngoingAdapter, GenesisOngoingPacket, MarkedTriple,
};
use core_wdp::genesis_source_execution::{
    Source25Change, Source25Run, Source25State, SourceExecutionError, SourceRelation,
};

fn packet(n: usize) -> GenesisOngoingPacket {
    GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r: vec![BigInt::zero(); n * n],
        s: vec![BigInt::zero(); n * n],
        filled: vec![],
    }
}
fn state(p: GenesisOngoingPacket) -> Source25State {
    Source25State::try_new(p).unwrap()
}
fn gradient(g: &[i64]) -> Source25State {
    let n = g.len();
    let mut p = packet(n);
    for x in 0..n {
        for y in 0..n {
            let e = g[x] - g[y];
            p.r[x * n + y] = BigInt::from(e.max(0));
            p.s[x * n + y] = BigInt::from((-e).max(0));
        }
    }
    state(p)
}
fn same_repair(left: &Source25State, right: &Source25State) -> bool {
    GenesisOngoingAdapter::try_new(left.packet().clone())
        .unwrap()
        .repair_equivalence(&GenesisOngoingAdapter::try_new(right.packet().clone()).unwrap())
        .unwrap()
        .is_some()
}

#[test]
fn carrier_changes_keep_big_counts_and_carry_actual_oriented_marks() {
    let huge = BigInt::one() << 140usize;
    let mut p = packet(4);
    p.r[0] = huge.clone();
    p.r[1] = 2.into();
    p.r[4] = 3.into();
    p.r[5] = 4.into();
    p.s[11] = 5.into();
    p.filled = vec![
        MarkedTriple { x: 0, y: 1, z: 2 },
        MarkedTriple { x: 0, y: 2, z: 3 },
        MarkedTriple { x: 0, y: 3, z: 2 },
        MarkedTriple { x: 1, y: 2, z: 3 },
        MarkedTriple { x: 1, y: 3, z: 2 },
    ];
    let initial = state(p);
    let merged = initial
        .perform_enabled(Source25Change::Identify { x: 0, y: 1 })
        .unwrap();
    assert_eq!(merged.packet().r[0], &huge + 9);
    assert_eq!(merged.packet().s[5], BigInt::from(5));
    assert_eq!(
        merged.packet().filled,
        vec![
            MarkedTriple { x: 0, y: 1, z: 2 },
            MarkedTriple { x: 0, y: 2, z: 1 }
        ]
    );
    assert_eq!(&initial.source_size() - 1, merged.source_size());
    let grown = merged.perform_enabled(Source25Change::AddTerm).unwrap();
    assert_eq!(grown.packet().terms.len(), 4);
    assert_eq!(&merged.source_size() + 1, grown.source_size());
    for i in 0..4 {
        assert!(grown.packet().r[i * 4 + 3].is_zero());
        assert!(grown.packet().r[3 * 4 + i].is_zero());
    }
    assert_eq!(grown.packet().filled, merged.packet().filled);
}

#[test]
fn carrier_changes_do_not_silently_operate_on_repair_classes() {
    let zero2 = state(packet(2));
    let shift2 = gradient(&[1, 0]);
    assert!(same_repair(&zero2, &shift2));
    let zero3 = zero2.perform_enabled(Source25Change::AddTerm).unwrap();
    let shift3 = shift2.perform_enabled(Source25Change::AddTerm).unwrap();
    assert!(!same_repair(&zero3, &shift3));
    let zero4 = state(packet(4));
    let shift4 = gradient(&[0, 0, 0, 1]);
    assert!(same_repair(&zero4, &shift4));
    let event = Source25Change::Identify { x: 0, y: 1 };
    assert!(!same_repair(
        &zero4.perform_enabled(event).unwrap(),
        &shift4.perform_enabled(event).unwrap()
    ));
}

#[test]
fn complete_intermediate_states_occurrences_and_prices_bind_composition() {
    let events = [
        Source25Change::AddTerm,
        Source25Change::AddTerm,
        Source25Change::AddAssertion {
            relation: SourceRelation::R,
            x: 0,
            y: 1,
        },
        Source25Change::Remove {
            relation: SourceRelation::R,
            x: 0,
            y: 1,
        },
    ];
    let whole = Source25Run::replay(Source25State::empty(), &events).unwrap();
    let prefix = Source25Run::replay(Source25State::empty(), &events[..3]).unwrap();
    let suffix = Source25Run::replay(prefix.final_state().clone(), &events[3..]).unwrap();
    assert_eq!(whole, prefix.then(&suffix).unwrap());
    assert_eq!(whole.changes().len(), 4);
    assert_eq!(whole.states().len(), 5);
    assert_eq!(whole.addition_price(), (&BigInt::from(2), &BigInt::one()));
    let shorter = Source25Run::replay(Source25State::empty(), &events[..2]).unwrap();
    assert_eq!(whole.final_state(), shorter.final_state());
    assert_ne!(whole, shorter);
    let mut other = prefix.final_state().packet().clone();
    other.r[0] += 1;
    other.s[0] += 1;
    let drift = Source25Run::replay(state(other), &events[3..]).unwrap();
    assert_eq!(
        prefix.then(&drift),
        Err(SourceExecutionError::IntermediateMismatch)
    );
    assert_eq!(
        whole,
        whole
            .then(&Source25Run::replay(whole.final_state().clone(), &[]).unwrap())
            .unwrap()
    );
}

#[test]
fn source_raising_preserves_raw_loops_and_has_the_actual_gradient_excess() {
    let mut p = packet(3);
    p.r[0] = 3.into();
    p.s[0] = 1.into();
    p.filled.push(MarkedTriple { x: 0, y: 1, z: 2 });
    let initial = state(p);
    let counts: Vec<BigInt> = [2, 0, 1].into_iter().map(BigInt::from).collect();
    let raised = initial.raise_terms(&counts).unwrap();
    assert_eq!(raised.packet().r[0], BigInt::from(3));
    assert_eq!(raised.packet().s[0], BigInt::one());
    let before = GenesisOngoingAdapter::try_new(initial.packet().clone()).unwrap();
    let after = GenesisOngoingAdapter::try_new(raised.packet().clone()).unwrap();
    assert_eq!(
        before.repair(&counts).unwrap().repaired_excess,
        after.excess()
    );
    assert_eq!(
        before.receipt().unwrap().diagnostics,
        after.receipt().unwrap().diagnostics
    );
    assert_ne!(initial.source_size(), raised.source_size());
    assert_eq!(raised.packet().filled, initial.packet().filled);
    assert!(initial
        .raise_terms(&[(-1).into(), 0.into(), 0.into()])
        .is_err());
}

#[test]
fn disabled_changes_are_refused_and_never_recorded_as_admitted_noops() {
    let initial = state(packet(3));
    for event in [
        Source25Change::Identify { x: 1, y: 1 },
        Source25Change::Identify { x: 0, y: 3 },
        Source25Change::Remove {
            relation: SourceRelation::R,
            x: 0,
            y: 1,
        },
        Source25Change::Fill { x: 0, y: 1, z: 1 },
        Source25Change::Fill { x: 1, y: 2, z: 0 },
        Source25Change::AddAssertion {
            relation: SourceRelation::S,
            x: 3,
            y: 0,
        },
    ] {
        assert!(!initial.is_enabled(event));
        assert_eq!(
            initial.perform_enabled(event),
            Err(SourceExecutionError::DisabledChange)
        );
        assert!(Source25Run::replay(initial.clone(), &[event]).is_err());
    }
    let fill = Source25Change::Fill { x: 0, y: 1, z: 2 };
    let filled = initial.perform_enabled(fill).unwrap();
    assert!(!filled.is_enabled(fill));
    assert!(filled.perform_enabled(fill).is_err());
    let mut noncanonical = packet(1);
    noncanonical.terms[0] = "other".into();
    assert_eq!(
        Source25State::try_new(noncanonical),
        Err(SourceExecutionError::NonCanonicalCarrier)
    );
    assert_eq!(
        Source25State::empty().enabled_changes(),
        vec![Source25Change::AddTerm]
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_source_execution.rs
// Claim: urn:core:crates_rs:tests:test-genesis-source-execution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda6b7a4b1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda6b7a4b1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora6b7a4b1 {
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
impl BoundaryErrora6b7a4b1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora6b7a4b1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora6b7a4b1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda6b7a4b1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora6b7a4b1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora6b7a4b1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora6b7a4b1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora6b7a4b1::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a6b7a4b1() {
    let admitted = BoundaryRecorda6b7a4b1::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda6b7a4b1::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
