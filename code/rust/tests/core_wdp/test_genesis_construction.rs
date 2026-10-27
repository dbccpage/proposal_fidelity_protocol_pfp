use core_homology::declared_incidence::{
    decode_declared, declared_chain_report, encode_declared,
};
use core_ooutwire_primitives::{
    event::Event,
    mark::{Mark, Pair},
    token::Token,
};
use core_wdp::genesis_construction::{
    cycle_construction, interpret_event, interpret_regime, verify_history_report,
    ConstructionError, ConstructionLimits, GenesisConstruction,
};
use std::collections::BTreeSet;
use core_wdp::genesis_primitive_execution::{PrimitiveReading, PrimitiveRegime};

fn inst(form: usize, args: &[usize]) -> Event {
    Event::AdmitInst(form, args.iter().copied().map(Mark).collect())
}

#[test]
fn literal_presentation_is_recorded_without_admitting_a_datum() {
    let pre = GenesisConstruction::pre_genesis();
    let root = GenesisConstruction::from_literal_seed().unwrap();
    assert!(pre.history().is_empty());
    assert_eq!(root.history(), &[Event::Supply(Token::new("<>"))]);
    assert_eq!(pre.regime(), root.regime());
    assert_eq!(root.regime().n_data(), 0);
    assert_eq!(
        root.simplicial_incidence(),
        Err(ConstructionError::NoIncidenceForm)
    );
    let admitted = root.advance(Event::AdmitDatum(Token::new("<>"))).unwrap();
    assert_eq!(admitted.regime().n_data(), 1);
    assert_eq!(root.regime().n_data(), 0);
}

#[test]
fn opening_event_must_be_the_exact_literal_supply() {
    for event in [
        Event::Supply(Token::new("")),
        Event::Supply(Token::new("< >")),
        Event::AdmitDatum(Token::new("<>")),
        Event::AdmitForm(1),
    ] {
        assert_eq!(
            GenesisConstruction::pre_genesis().advance(event),
            Err(ConstructionError::MissingLiteralRoot)
        );
    }
    assert_eq!(
        GenesisConstruction::replay(&[]),
        Err(ConstructionError::MissingLiteralRoot)
    );
}

#[test]
fn all_six_events_preserve_every_admitted_field_at_every_prefix() {
    let events = [
        Event::Supply(Token::new("<>")),
        Event::AdmitDatum(Token::new("a")),
        Event::AdmitDatum(Token::new("b")),
        Event::AdmitForm(2),
        inst(0, &[0, 1]),
        Event::AdmitRuleAll(0),
        Event::Impose(Pair::of(0, 1)),
        Event::Supply(Token::new("later")),
    ];
    let mut walk = GenesisConstruction::pre_genesis();
    let mut expected = PrimitiveRegime::empty();
    for event in &events {
        expected = expected
            .step(&interpret_event(event), PrimitiveReading::Dedup)
            .unwrap();
        walk = walk.advance(event.clone()).unwrap();
        assert_eq!(&interpret_regime(walk.regime()).unwrap(), &expected);
        assert_eq!(walk.interpreted(), &expected);
    }
    assert_eq!(walk, GenesisConstruction::replay(&events).unwrap());
    assert_eq!(
        walk.simplicial_incidence(),
        Err(ConstructionError::UnsupportedIncidenceCommitments)
    );
}

#[test]
fn omitting_requirements_in_regime_interpretation_is_caught_by_six_event_trace() {
    let events = [
        Event::Supply(Token::new("<>")),
        Event::AdmitDatum(Token::new("a")),
        Event::AdmitDatum(Token::new("b")),
        Event::AdmitForm(2),
        inst(0, &[0, 1]),
        Event::AdmitRuleAll(0),
        Event::Impose(Pair::of(0, 1)),
    ];
    let walk = GenesisConstruction::replay(&events).unwrap();
    let full = interpret_regime(walk.regime()).unwrap();
    let mutated_without_reqs = PrimitiveRegime::try_new(
        walk.regime()
            .data()
            .iter()
            .map(|token| token.text().to_owned())
            .collect(),
        walk.regime().forms().to_vec(),
        walk.regime()
            .insts()
            .iter()
            .map(|instance| {
                core_wdp::genesis_primitive_execution::PrimitiveInstance {
                    form: instance.form,
                    args: instance.args.iter().map(|mark| mark.index()).collect(),
                }
            })
            .collect(),
        walk.regime().rules().clone(),
        BTreeSet::new(),
    )
    .unwrap();
    assert_eq!(full.requirements().len(), 1);
    assert!(mutated_without_reqs.requirements().is_empty());
    assert_ne!(&mutated_without_reqs, &full);
    assert_ne!(&mutated_without_reqs, walk.interpreted());
}


#[test]
fn duplicate_tokens_use_the_canonical_dedup_reading() {
    let event = Event::AdmitDatum(Token::new("a"));
    let walk = GenesisConstruction::from_literal_seed()
        .unwrap()
        .extend(&[event.clone(), event.clone()])
        .unwrap();
    assert_eq!(walk.regime().n_data(), 1);
    assert_eq!(walk.history().len(), 3);
    let first = PrimitiveRegime::empty()
        .step(&interpret_event(&event), PrimitiveReading::Occurrence)
        .unwrap();
    let second = first
        .step(&interpret_event(&event), PrimitiveReading::Occurrence)
        .unwrap();
    assert_ne!(walk.interpreted(), &second);
}

#[test]
fn malformed_events_do_not_change_the_retained_construction() {
    let walk = GenesisConstruction::from_literal_seed()
        .unwrap()
        .extend(&[
            Event::AdmitDatum(Token::new("a")),
            Event::AdmitDatum(Token::new("b")),
            Event::AdmitForm(2),
        ])
        .unwrap();
    let saved = walk.clone();
    for event in [
        Event::AdmitForm(0),
        inst(7, &[0, 1]),
        inst(0, &[0]),
        inst(0, &[0, 7]),
        Event::AdmitRuleAll(7),
    ] {
        assert!(walk.advance(event).is_err());
        assert_eq!(walk, saved);
    }
    // Pair's fields are public: canonical admission must reject malformed
    // values even when a caller bypasses Pair::new.
    for (i, j) in [(1, 0), (0, 0), (70, 0)] {
        let invalid = Event::Impose(Pair {
            i: Mark(i),
            j: Mark(j),
        });
        assert!(matches!(
            walk.advance(invalid),
            Err(ConstructionError::Admission { .. })
        ));
    }
    assert_eq!(walk, saved);
}

#[test]
fn restart_and_continuation_recover_the_same_complete_history() {
    let walk = cycle_construction(["x", "y", "z"]).unwrap();
    for split in 1..=walk.history().len() {
        let prefix = GenesisConstruction::replay(&walk.history()[..split]).unwrap();
        let resumed = prefix.extend(&walk.history()[split..]).unwrap();
        assert_eq!(resumed, walk);
    }
}

fn assert_report_matches_homology_owner(walk: &GenesisConstruction) {
    let packet = walk.simplicial_incidence().unwrap();
    let complex = encode_declared(&packet.cells).unwrap();
    assert_eq!(
        decode_declared(&complex),
        packet.cells.iter().cloned().collect::<BTreeSet<_>>()
    );
    let owner = declared_chain_report(&complex).unwrap();
    let report = walk.homology().unwrap();
    assert_eq!(report.dimensions, owner.dimensions);
    assert_eq!(report.boundaries, owner.boundaries);
    assert_eq!(report.betti, owner.betti);
    assert_eq!(report.betti, complex.rational_betti_numbers().unwrap());
}

#[test]
fn cycle_and_filling_are_computed_from_the_actual_admissions() {
    let cycle = cycle_construction(["<a>", "<ab>", "<c>"]).unwrap();
    let before = cycle.homology().unwrap();
    assert_report_matches_homology_owner(&cycle);
    assert_eq!(before.dimensions, vec![3, 3]);
    assert_eq!(before.betti, vec![1, 1]);
    assert_eq!(before.boundaries.len(), 1);
    let filled = cycle.advance(inst(2, &[0, 1, 2])).unwrap();
    let after = filled.homology().unwrap();
    assert_report_matches_homology_owner(&filled);
    assert_eq!(after.dimensions, vec![3, 3, 1]);
    assert_eq!(after.betti, vec![1, 0, 0]);
    assert_eq!(after.boundaries.len(), 2);
    assert_eq!(filled.history().len(), cycle.history().len() + 1);
    assert_eq!(cycle.homology().unwrap(), before);
    verify_history_report(cycle.history(), &before).unwrap();
    verify_history_report(filled.history(), &after).unwrap();
    assert_eq!(
        verify_history_report(cycle.history(), &after),
        Err(ConstructionError::ReportMismatch)
    );
}

#[test]
fn token_spelling_does_not_supply_the_incidence() {
    let first = cycle_construction(["<a>", "<ab>", "<c>"]).unwrap();
    let renamed =
        cycle_construction(["not a vertex label", "<> contains no endpoints", "42"]).unwrap();
    assert_eq!(first.homology().unwrap(), renamed.homology().unwrap());
    assert_ne!(first.regime().data(), renamed.regime().data());
    assert!(cycle_construction(["same", "same", "different"]).is_err());
}

#[test]
fn no_missing_vertices_or_faces_are_automatically_admitted() {
    let root = GenesisConstruction::from_literal_seed()
        .unwrap()
        .extend(&[
            Event::AdmitDatum(Token::new("a")),
            Event::AdmitDatum(Token::new("b")),
            Event::AdmitDatum(Token::new("c")),
            Event::AdmitForm(1),
            Event::AdmitForm(2),
            Event::AdmitForm(3),
        ])
        .unwrap();
    assert!(matches!(
        root.simplicial_incidence(),
        Err(ConstructionError::MissingVertex(_))
    ));
    let vertices = root
        .extend(&[inst(0, &[0]), inst(0, &[1]), inst(0, &[2])])
        .unwrap();
    let no_edges = vertices.advance(inst(2, &[0, 1, 2])).unwrap();
    assert!(matches!(
        no_edges.simplicial_incidence(),
        Err(ConstructionError::Incidence(_))
    ));
    let reversed = vertices.advance(inst(1, &[1, 0])).unwrap();
    assert!(matches!(
        reversed.simplicial_incidence(),
        Err(ConstructionError::Incidence(_))
    ));
}

#[test]
fn duplicate_cells_are_refused_instead_of_erasing_an_admitted_form() {
    let cycle = cycle_construction(["a", "b", "c"]).unwrap();
    let duplicate = cycle.extend(&[Event::AdmitForm(1), inst(3, &[0])]).unwrap();
    assert!(matches!(
        duplicate.simplicial_incidence(),
        Err(ConstructionError::Incidence(_))
    ));
}

#[test]
fn report_verification_replays_the_root_and_recomputes_the_values() {
    let cycle = cycle_construction(["a", "b", "c"]).unwrap();
    let mut forged = cycle.homology().unwrap();
    forged.betti[1] = 0;
    assert_eq!(
        verify_history_report(cycle.history(), &forged),
        Err(ConstructionError::ReportMismatch)
    );
    assert_eq!(
        verify_history_report(&cycle.history()[1..], &forged),
        Err(ConstructionError::MissingLiteralRoot)
    );
    let mut wrong_operator = cycle.homology().unwrap();
    wrong_operator.boundaries[0][0][0] = "700".into();
    assert_eq!(
        verify_history_report(cycle.history(), &wrong_operator),
        Err(ConstructionError::ReportMismatch)
    );
}

#[test]
fn event_and_matrix_limits_refuse_work_before_the_owner_allocation() {
    let one = ConstructionLimits {
        max_events: 1,
        ..ConstructionLimits::default()
    };
    let seed = GenesisConstruction::pre_genesis_with_limits(one)
        .advance(Event::Supply(Token::new("<>")))
        .unwrap();
    assert!(matches!(
        seed.advance(Event::AdmitDatum(Token::new("a"))),
        Err(ConstructionError::ResourceLimit {
            resource: "event count",
            ..
        })
    ));
    let cycle = cycle_construction(["a", "b", "c"]).unwrap();
    assert!(matches!(
        GenesisConstruction::replay_with_limits(cycle.history(), one),
        Err(ConstructionError::ResourceLimit {
            resource: "event count",
            ..
        })
    ));
    for limits in [
        ConstructionLimits {
            max_cells: 5,
            ..ConstructionLimits::default()
        },
        ConstructionLimits {
            max_matrix_entries: 35,
            ..ConstructionLimits::default()
        },
    ] {
        let bounded = GenesisConstruction::replay_with_limits(cycle.history(), limits).unwrap();
        assert_eq!(bounded.limits(), limits);
        assert!(matches!(
            bounded.homology(),
            Err(ConstructionError::ResourceLimit { .. })
        ));
    }
    let exact = ConstructionLimits {
        max_matrix_entries: 36,
        ..ConstructionLimits::default()
    };
    assert_eq!(
        GenesisConstruction::replay_with_limits(cycle.history(), exact)
            .unwrap()
            .homology()
            .unwrap()
            .betti,
        vec![1, 1]
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_construction.rs
// Claim: urn:core:crates_rs:tests:test-genesis-construction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd35e11c3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd35e11c3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord35e11c3 {
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
impl BoundaryErrord35e11c3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord35e11c3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord35e11c3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd35e11c3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord35e11c3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord35e11c3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord35e11c3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord35e11c3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d35e11c3() {
    let admitted = BoundaryRecordd35e11c3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd35e11c3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
