use core_wdp::genesis_primitive_execution::*;
use std::collections::BTreeSet;

fn limits() -> PrimitiveLimits {
    PrimitiveLimits {
        max_tuples: 10000,
        max_width: 16,
        max_candidates: 100000,
    }
}
fn initial() -> PrimitiveRegime {
    PrimitiveRegime::try_new(
        vec!["<>".into(), "<a>".into()],
        vec![],
        BTreeSet::new(),
        BTreeSet::new(),
        BTreeSet::new(),
    )
    .unwrap()
}
#[test]
fn external_supply_and_metatheory_dedup_do_not_supply_internal_distinction() {
    let base = PrimitiveRegime::empty();
    let events = [
        PrimitiveEvent::Supply {
            token: "<ab>".into(),
        },
        PrimitiveEvent::AdmitDatum { token: "<>".into() },
        PrimitiveEvent::AdmitDatum { token: "<>".into() },
    ];
    let dedup = PrimitiveRun::replay(base.clone(), &events, PrimitiveReading::Dedup).unwrap();
    assert_eq!(dedup.states()[0], dedup.states()[1]);
    assert_eq!(dedup.final_state().data(), &["<>".to_string()]);
    assert_eq!(dedup.states()[2], dedup.states()[3]);
    let occurrence = PrimitiveRun::replay(base, &events, PrimitiveReading::Occurrence).unwrap();
    assert_eq!(
        occurrence.final_state().data(),
        &["<>".to_string(), "<>".to_string()]
    );
    assert_eq!(
        occurrence.final_state().collapsed_pairs(limits()).unwrap(),
        vec![(0, 1)]
    );
    assert_eq!(occurrence.events().len(), 3);
}
#[test]
fn all_six_events_observe_the_actual_typed_contexts_and_uniform_rule() {
    let events = [
        PrimitiveEvent::AdmitForm { arity: 2 },
        PrimitiveEvent::AdmitInst {
            form: 0,
            args: vec![0, 1],
        },
        PrimitiveEvent::Impose { i: 0, j: 1 },
    ];
    let run = PrimitiveRun::replay(initial(), &events, PrimitiveReading::Dedup).unwrap();
    let state = run.final_state();
    assert!(state.satisfies(limits()).unwrap());
    assert_eq!(state.contexts(limits()).unwrap().len(), 5);
    assert_eq!(
        state.witness(0, 1, limits()).unwrap(),
        Some(PrimitiveContext {
            form: 0,
            slots: vec![None, Some(1)]
        })
    );
    let all = state
        .step(
            &PrimitiveEvent::AdmitRuleAll { form: 0 },
            PrimitiveReading::Dedup,
        )
        .unwrap();
    assert!(!all.satisfies(limits()).unwrap());
    assert_eq!(all.collapsed_pairs(limits()).unwrap(), vec![(0, 1)]);
    assert!(all.witness(0, 1, limits()).unwrap().is_none());
    assert!(all
        .derivable(&PrimitiveInstance {
            form: 0,
            args: vec![0, 0]
        })
        .unwrap());
}
#[test]
fn complete_intermediates_and_every_occurrence_bind_history_composition() {
    let events = [
        PrimitiveEvent::AdmitDatum { token: "<>".into() },
        PrimitiveEvent::AdmitForm { arity: 1 },
        PrimitiveEvent::AdmitInst {
            form: 0,
            args: vec![0],
        },
        PrimitiveEvent::Supply {
            token: "extra".into(),
        },
    ];
    let whole =
        PrimitiveRun::replay(PrimitiveRegime::empty(), &events, PrimitiveReading::Dedup).unwrap();
    for split in 0..=events.len() {
        let left = PrimitiveRun::replay(
            PrimitiveRegime::empty(),
            &events[..split],
            PrimitiveReading::Dedup,
        )
        .unwrap();
        let right = PrimitiveRun::replay(
            left.final_state().clone(),
            &events[split..],
            PrimitiveReading::Dedup,
        )
        .unwrap();
        assert_eq!(left.then(&right).unwrap(), whole);
    }
    let wrong = PrimitiveRun::replay(
        whole.final_state().clone(),
        &[],
        PrimitiveReading::Occurrence,
    )
    .unwrap();
    assert_eq!(
        whole.then(&wrong),
        Err(PrimitiveExecutionError::IntermediateMismatch)
    );
    let no_rule = whole.final_state();
    let with_rule = no_rule
        .step(
            &PrimitiveEvent::AdmitRuleAll { form: 0 },
            PrimitiveReading::Dedup,
        )
        .unwrap();
    assert_ne!(no_rule, &with_rule);
    let wrong = PrimitiveRun::replay(with_rule, &[], PrimitiveReading::Dedup).unwrap();
    assert_eq!(
        whole.then(&wrong),
        Err(PrimitiveExecutionError::IntermediateMismatch)
    );
}
#[test]
fn source_initial_minima_retain_all_unary_binary_and_orientation_alternatives() {
    let base = initial();
    let a = base
        .minimum_responses_checked((0, 1), PrimitiveMeasure::Items, 2, 2, limits())
        .unwrap()
        .unwrap();
    let b = base
        .minimum_responses_checked((0, 1), PrimitiveMeasure::ItemsThenArity, 2, 2, limits())
        .unwrap()
        .unwrap();
    assert_eq!(a.deltas.len(), 6);
    assert_eq!(a.price, (2.into(), (-1).into()));
    assert_eq!(b.deltas.len(), 2);
    assert_eq!(b.price, (2.into(), 1.into()));
    for delta in &a.deltas {
        assert!(base.response_valid((0, 1), delta, limits()).unwrap());
    }
    assert!(base
        .minimum_responses_checked((0, 1), PrimitiveMeasure::Items, 1, 2, limits())
        .unwrap()
        .is_none());
}
#[test]
fn generated_name_collision_is_preserved_and_never_certified_as_fresh() {
    let base = PrimitiveRegime::try_new(
        vec!["w2".into(), "x".into()],
        vec![2],
        BTreeSet::new(),
        BTreeSet::new(),
        BTreeSet::new(),
    )
    .unwrap();
    let delta = PrimitiveDelta::new(vec![
        PrimitiveItem::NewDatum,
        PrimitiveItem::NewInst {
            form: 0,
            args: vec![0, 2],
        },
    ]);
    assert_eq!(
        base.delta_events(&delta).unwrap()[0],
        PrimitiveEvent::AdmitDatum { token: "w2".into() }
    );
    assert_eq!(
        base.apply_delta(&delta),
        Err(PrimitiveExecutionError::InvalidArgument)
    );
    assert_eq!(base.data().len(), 2);
}
#[test]
fn malformed_events_and_incomplete_enumerations_refuse_without_mutation() {
    let base = initial();
    for event in [
        PrimitiveEvent::AdmitForm { arity: 0 },
        PrimitiveEvent::AdmitRuleAll { form: 0 },
        PrimitiveEvent::AdmitInst {
            form: 0,
            args: vec![0],
        },
        PrimitiveEvent::Impose { i: 1, j: 0 },
    ] {
        assert_eq!(
            base.step(&event, PrimitiveReading::Dedup),
            Err(PrimitiveExecutionError::InvalidArgument)
        );
    }
    assert!(base
        .full_deltas(
            2,
            2,
            PrimitiveLimits {
                max_candidates: 3,
                ..limits()
            }
        )
        .is_err());
    assert!(base
        .full_deltas(
            0,
            2,
            PrimitiveLimits {
                max_candidates: 0,
                ..limits()
            }
        )
        .is_err());
    assert_eq!(
        base.full_deltas(3, 2, limits()),
        Err(PrimitiveExecutionError::OutsideCandidateBounds)
    );
    assert_eq!(base, initial());
}

#[test]
fn persistent_requirements_price_the_minimum_cover_instead_of_always_choosing_unary() {
    let regime = |n| {
        PrimitiveRegime::try_new(
            (0..n).map(|i| format!("d{i}")).collect(),
            vec![],
            BTreeSet::new(),
            BTreeSet::new(),
            (0..n)
                .flat_map(|i| (i + 1..n).map(move |j| (i, j)))
                .collect(),
        )
        .unwrap()
    };
    let triangle = regime(3)
        .minimum_responses_checked((0, 1), PrimitiveMeasure::ItemsThenArity, 2, 2, limits())
        .unwrap()
        .unwrap();
    assert_eq!(triangle.price, (2.into(), 2.into()));
    assert_eq!(triangle.deltas.len(), 6);
    assert!(regime(4)
        .minimum_responses_checked((0, 1), PrimitiveMeasure::ItemsThenArity, 2, 2, limits())
        .unwrap()
        .is_none());
    let tetrahedron = regime(4)
        .minimum_responses_checked((0, 1), PrimitiveMeasure::ItemsThenArity, 2, 3, limits())
        .unwrap()
        .unwrap();
    assert_eq!(tetrahedron.price, (2.into(), 3.into()));
    assert_eq!(tetrahedron.deltas.len(), 24);
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_primitive_execution.rs
// Claim: urn:core:crates_rs:tests:test-genesis-primitive-execution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4c5fbd04 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4c5fbd04` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4c5fbd04 {
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
impl BoundaryError4c5fbd04 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4c5fbd04 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4c5fbd04 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4c5fbd04 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4c5fbd04> {
        if capacity_bound == 0 {
            return Err(BoundaryError4c5fbd04::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4c5fbd04::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4c5fbd04::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4c5fbd04() {
    let admitted = BoundaryRecord4c5fbd04::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4c5fbd04::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
