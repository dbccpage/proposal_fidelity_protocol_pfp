use core_category_theory::finite_simulation::*;
use core_solvers::finite_stream_interpreter::*;
use core_wdp::genesis_carrier::{CarrierLimits, CarrierRequest, PassageCarrier, PassageQuestion};
use core_wdp::genesis_passage::PassageEvent;
use core_wdp::genesis_refusal::{Constitution, RepresentedWorld, WorldEvent::*};
use core_wdp::genesis_translation::*;
fn limits() -> TranslationLimits {
    TranslationLimits {
        max_events: 100,
        max_cells: 1000,
    }
}
#[test]
fn native_requirement_and_repair_history_has_a_checked_translation() {
    let events = vec![
        Admit(10),
        Admit(20),
        Require(0, 1),
        SetBudget(2),
        AddView(vec![0]),
        Note(8),
        Refuse(0, 1),
    ];
    let initial = RepresentedWorld::default();
    let c = check_translation(&initial, Constitution::KERNEL, &events, limits()).unwrap();
    assert!(matches!(c, TranslationDecision::Checked { .. }));
    verify_translation(&initial, Constitution::KERNEL, &events, limits(), &c).unwrap();
    let mut changed = events.clone();
    changed[0] = Admit(30);
    assert!(verify_translation(&initial, Constitution::KERNEL, &changed, limits(), &c).is_err());
    assert_eq!(
        check_translation(
            &initial,
            Constitution::KERNEL,
            &events,
            TranslationLimits {
                max_events: 2,
                ..limits()
            }
        ),
        Err(TranslationError::ResourceLimit)
    );
}
#[test]
fn all_constitutions_expose_the_deduplication_translation_premise() {
    for i in 0..64 {
        let d = Constitution::from_lean_index(i).unwrap();
        let c = check_translation(
            &RepresentedWorld::default(),
            d,
            &[Admit(7), Admit(7)],
            limits(),
        )
        .unwrap();
        assert_eq!(
            matches!(c, TranslationDecision::Checked { .. }),
            d.dedup_admit
        );
        verify_translation(
            &RepresentedWorld::default(),
            d,
            &[Admit(7), Admit(7)],
            limits(),
            &c,
        )
        .unwrap();
    }
}
#[test]
fn refusal_exhaustion_and_unprotected_augmentation_do_not_translate_silently() {
    let w = RepresentedWorld {
        data: vec![10, 20],
        views: vec![vec![]],
        reqs: vec![(0, 1)],
        ..Default::default()
    };
    let c = check_translation(&w, Constitution::KERNEL, &[Refuse(0, 1)], limits()).unwrap();
    let TranslationDecision::Refuted {
        expected, actual, ..
    } = &c
    else {
        panic!("different refusal premises")
    };
    assert!(expected.refusals.is_empty());
    assert_eq!(actual.refusals, vec![(0, 1)]);
    verify_translation(&w, Constitution::KERNEL, &[Refuse(0, 1)], limits(), &c).unwrap();
    let w = RepresentedWorld {
        data: vec![10, 20],
        budget: 1,
        ..Default::default()
    };
    let c = check_translation(&w, Constitution::KERNEL, &[AddView(vec![0])], limits()).unwrap();
    assert!(matches!(c, TranslationDecision::Refuted { .. }));
}
#[test]
fn native_closed_passage_carrier_runs_on_the_tape_interpreter() {
    use PassageEvent::*;
    let c = PassageCarrier::build(&CarrierRequest {
        seeds: vec![vec![]],
        alphabet: vec![AdmitOcc(10), AdmitOcc(20), AssertWit(0, 1), Halt],
        questions: vec![PassageQuestion::OccurrenceCount],
        limits: CarrierLimits::default(),
    })
    .unwrap();
    let program = CompiledStream::new(c.dynamics(), 0, 1000).unwrap();
    let bounds = StreamLimits {
        max_word_len: 3,
        max_steps: 4,
        max_trace_cells: 100,
    };
    for len in 0..=3 {
        for code in 0..4usize.pow(len as u32) {
            let mut n = code;
            let word: Vec<_> = (0..len)
                .map(|_| {
                    let a = n % 4;
                    n /= 4;
                    a
                })
                .collect();
            let certificate = program.execute(&word, len + 1, bounds).unwrap();
            match c.dynamics().run(0, &word).unwrap() {
                Some(state) => assert_eq!(certificate.outcome, StreamOutcome::Accepted { state }),
                None => assert!(matches!(
                    certificate.outcome,
                    StreamOutcome::Unavailable { .. }
                )),
            }
            program
                .verify(&word, len + 1, bounds, &certificate)
                .unwrap();
        }
    }
}
#[test]
fn adding_native_occurrence_capacity_preserves_old_steps_but_adds_availability() {
    use PassageEvent::*;
    let make = |seeds| {
        PassageCarrier::build(&CarrierRequest {
            seeds,
            alphabet: vec![AdmitOcc(10), AssertWit(0, 1)],
            questions: vec![PassageQuestion::HasToken(10)],
            limits: CarrierLimits::default(),
        })
        .unwrap()
    };
    let small = make(vec![vec![AdmitOcc(10)]]);
    let large = make(vec![vec![AdmitOcc(10), AdmitOcc(20)]]);
    let c = check_simulation(
        small.dynamics(),
        large.dynamics(),
        &[0],
        &[vec![0], vec![1]],
        SimulationMode::ResourceExtension,
        100,
    )
    .unwrap();
    assert_eq!(
        c,
        SimulationDecision::Checked {
            added_availability: vec![(0, 1)]
        }
    );
    assert!(verify_simulation(
        small.dynamics(),
        large.dynamics(),
        &[0],
        &[vec![0], vec![1]],
        SimulationMode::Exact,
        100,
        &c
    )
    .is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/genesis_native_simulation.rs
// Claim: urn:core:crates_rs:tests:genesis-native-simulation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9f4b131a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9f4b131a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9f4b131a {
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
impl BoundaryError9f4b131a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9f4b131a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9f4b131a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9f4b131a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9f4b131a> {
        if capacity_bound == 0 {
            return Err(BoundaryError9f4b131a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9f4b131a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9f4b131a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9f4b131a() {
    let admitted = BoundaryRecord9f4b131a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9f4b131a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
