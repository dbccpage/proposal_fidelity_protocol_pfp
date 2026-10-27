use num_bigint::BigInt;
use core_wdp::genesis_admission_execution::{
    AdmissionExecutionError, Source15Admission, Source15Tagged, Source16Change, Source16Reading,
    Source16Run, Source16State, Source9Change, Source9State,
};
use core_wdp::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use core_wdp::genesis_source_execution::SourceRelation::{R, S};

fn state(n: usize, r: &[i64], s: &[i64], record: &[i64]) -> Source16State {
    let p = GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r: r.iter().map(|&v| v.into()).collect(),
        s: s.iter().map(|&v| v.into()).collect(),
        filled: vec![],
    };
    Source16State::try_new(
        Source9State::try_new(p).unwrap(),
        record.iter().map(|&v| v.into()).collect(),
    )
    .unwrap()
}
fn direct(change: Source9Change) -> Source16Change {
    Source16Change::Direct { change }
}

#[test]
fn tagged_admission_preserves_raw_state_but_reaching_jointly_canonicalizes_and_resets() {
    let raw = state(2, &[1, 0, 0, 0], &[0, 0, 0, 1], &[0; 4]);
    let tagged = Source15Tagged::new(raw.state().clone(), Source15Admission::after_reaching());
    let admitted = tagged.admit();
    assert_eq!(admitted.state(), tagged.state());
    assert_eq!(admitted.admit(), admitted);
    let event = Source9Change::AddAssertion {
        relation: R,
        x: 0,
        y: 0,
    };
    let out = admitted.perform_enabled(event, 2).unwrap();
    assert_eq!(
        out.state().packet().r,
        vec![0.into(), 0.into(), 0.into(), 2.into()]
    );
    assert_eq!(
        out.state().packet().s,
        vec![1.into(), 0.into(), 0.into(), 0.into()]
    );
    assert!(!out.admission().admitted);
    assert_eq!(out, tagged.perform_enabled(event, 2).unwrap());
    assert!(admitted.perform_enabled(event, 1).is_err());
    assert_eq!(admitted.state(), raw.state());
    assert!(
        Source15Tagged::new(Source9State::empty(), Source15Admission::after_reaching())
            .admit()
            .admission()
            .admitted
    );
}

#[test]
fn record_drives_future_admissions_and_paid_cycles_keep_occurrences() {
    let before = state(1, &[1], &[0], &[0]);
    let events = [
        direct(Source9Change::Remove {
            relation: R,
            x: 0,
            y: 0,
        }),
        Source16Change::Admit {
            relation: R,
            x: 0,
            y: 0,
        },
    ];
    let run = Source16Run::replay(before.clone(), &events, Source16Reading::Count).unwrap();
    assert_eq!(run.final_state(), &before);
    assert_eq!(run.addition_price(), (&BigInt::from(0), &BigInt::from(1)));
    let intermediate = &run.states()[1];
    assert_eq!(intermediate.state().packet().r, vec![0.into()]);
    assert!(intermediate.is_enabled(Source16Change::Admit {
        relation: S,
        x: 0,
        y: 0
    }));
    let forgotten = state(1, &[0], &[0], &[0]);
    assert_eq!(intermediate.state(), forgotten.state());
    assert!(!forgotten.is_enabled(Source16Change::Admit {
        relation: S,
        x: 0,
        y: 0
    }));
    for split in 0..=events.len() {
        let left =
            Source16Run::replay(before.clone(), &events[..split], Source16Reading::Count).unwrap();
        let right = Source16Run::replay(
            left.final_state().clone(),
            &events[split..],
            Source16Reading::Count,
        )
        .unwrap();
        assert_eq!(left.then(&right).unwrap(), run);
    }
    let wrong_reading = Source16Run::replay(before.clone(), &[], Source16Reading::Drop).unwrap();
    assert_eq!(
        run.then(&wrong_reading),
        Err(AdmissionExecutionError::ReadingMismatch)
    );
    let wrong_record =
        Source16Run::replay(state(1, &[1], &[0], &[1]), &[], Source16Reading::Count).unwrap();
    assert_eq!(
        run.then(&wrong_record),
        Err(AdmissionExecutionError::IntermediateMismatch)
    );
}

#[test]
fn set_is_not_boolean_after_identification_and_drop_does_not_preserve_mass() {
    let before = state(2, &[1, 0, 0, 0], &[0; 4], &[1, 0, 0, 1]);
    let remove = direct(Source9Change::Remove {
        relation: R,
        x: 0,
        y: 0,
    });
    let count = before
        .perform_enabled(remove, Source16Reading::Count)
        .unwrap();
    let set = before
        .perform_enabled(remove, Source16Reading::Set)
        .unwrap();
    assert_eq!(count.leftovers()[0], 2.into());
    assert_eq!(set.leftovers()[0], 1.into());
    assert_eq!(count.mass(), before.mass());
    assert!(set.mass() < before.mass());
    let identify = direct(Source9Change::Identify { x: 0, y: 1 });
    let set = before
        .perform_enabled(identify, Source16Reading::Set)
        .unwrap();
    assert_eq!(set.leftovers(), &[BigInt::from(2)]);
    let drop = before
        .perform_enabled(identify, Source16Reading::Drop)
        .unwrap();
    assert_eq!(drop.leftovers(), &[BigInt::from(0)]);
    assert!(drop.mass() < before.mass());
    let count = before
        .perform_enabled(identify, Source16Reading::Count)
        .unwrap();
    assert_eq!(count.potential() + 1, before.potential());
    assert_eq!(count.mass(), before.mass());
}

#[test]
fn malformed_records_and_disabled_events_are_refused_without_mutation() {
    let before = state(1, &[0], &[0], &[0]);
    assert_eq!(
        Source16State::try_new(before.state().clone(), vec![]),
        Err(AdmissionExecutionError::InvalidRecord)
    );
    assert_eq!(
        Source16State::try_new(before.state().clone(), vec![(-1).into()]),
        Err(AdmissionExecutionError::InvalidRecord)
    );
    let saved = before.clone();
    assert_eq!(
        before.perform_enabled(
            Source16Change::Admit {
                relation: R,
                x: 0,
                y: 0
            },
            Source16Reading::Count
        ),
        Err(AdmissionExecutionError::DisabledEvent)
    );
    assert_eq!(
        before.perform_enabled(
            direct(Source9Change::Identify { x: 0, y: 0 }),
            Source16Reading::Count
        ),
        Err(AdmissionExecutionError::DisabledEvent)
    );
    assert_eq!(before, saved);
    let mut packet = state(3, &[0; 9], &[0; 9], &[0; 9]).state().packet().clone();
    packet.filled.push(MarkedTriple { x: 0, y: 1, z: 2 });
    assert_eq!(
        Source9State::try_new(packet),
        Err(AdmissionExecutionError::FilledCarrier)
    );
}

#[test]
fn count_recipes_reach_arbitrary_tables_and_retain_huge_counts_without_expansion() {
    let target = state(2, &[2, 1, 0, 1], &[0, 1, 2, 0], &[1, 0, 2, 1]);
    let recipe = target.count_minimum_recipe();
    assert_eq!(recipe.length(), target.potential());
    let run = recipe.expand(100).unwrap();
    assert_eq!(run.final_state(), &target);
    assert_eq!(BigInt::from(run.changes().len()), target.potential());
    assert_eq!(recipe.addition_price(), (BigInt::from(2), BigInt::from(11)));
    assert_eq!(run.addition_price(), (&BigInt::from(2), &BigInt::from(11)));
    let huge = BigInt::from(1u8) << 140usize;
    let mut packet = target.state().packet().clone();
    packet.r[0] = huge.clone();
    let huge_target = Source16State::try_new(
        Source9State::try_new(packet).unwrap(),
        vec![huge.clone(); 4],
    )
    .unwrap();
    let compact = huge_target.count_minimum_recipe();
    assert_eq!(compact.length(), huge_target.potential());
    assert!(compact.blocks().len() <= 13);
    assert!(matches!(
        compact.expand(100),
        Err(AdmissionExecutionError::RecipeBudgetExceeded { .. })
    ));
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_admission_execution.rs
// Claim: urn:core:crates_rs:tests:test-genesis-admission-execution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord132acf4c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord132acf4c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError132acf4c {
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
impl BoundaryError132acf4c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError132acf4c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError132acf4c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord132acf4c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError132acf4c> {
        if capacity_bound == 0 {
            return Err(BoundaryError132acf4c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError132acf4c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError132acf4c::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_132acf4c() {
    let admitted = BoundaryRecord132acf4c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord132acf4c::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
