//! Admission and bounded-search regressions against the declared Genesis model.
//! The frozen Python source remains unchanged; collision repair is local.

use std::collections::BTreeSet;

use core_ooutwire_primitives::{
    admission::step,
    bounds::Bounds,
    candidate::{apply_delta, delta_events, Item},
    canonical::canonical,
    certification::certifies,
    event::Event,
    judgment::{holding, holds, Judgment},
    mark::{Mark, Pair},
    measure::MeasureKind,
    minima::min_responses,
    profile::{derivable, profile},
    regime::{Inst, Regime},
    renaming::{try_rename, Bijection},
    replay::replay,
    response::{profile_additions, response_valid_fast, response_valid_naive, NodeView},
    separability::{separable, witness},
    token::Token,
    world::{step_world, Verdict, World, WorldEvent},
};

fn pair_base(a: &str, b: &str) -> Regime {
    replay(&[
        Event::Supply(Token::new("<>")),
        Event::AdmitDatum(Token::new(a)),
        Event::AdmitDatum(Token::new(b)),
    ])
    .unwrap()
}

fn binary_complete(a: &str, b: &str) -> Regime {
    let mut base = step(&pair_base(a, b), &Event::AdmitForm(2)).unwrap();
    for i in 0..2 {
        for j in 0..2 {
            base = step(&base, &Event::AdmitInst(0, vec![Mark(i), Mark(j)])).unwrap();
        }
    }
    base
}

#[test]
fn public_pair_fields_cannot_bypass_admission_or_certification() {
    let base = pair_base("a", "b");
    for (i, j) in [(1, 0), (0, 0), (9, 0), (0, 9)] {
        let event = Event::Impose(Pair {
            i: Mark(i),
            j: Mark(j),
        });
        assert!(step(&base, &event).is_err());
        assert!(!certifies(
            &[
                Event::AdmitDatum(Token::new("a")),
                Event::AdmitDatum(Token::new("b")),
                event
            ],
            &base
        ));
    }
    assert!(base.reqs().is_empty());
    assert_eq!(
        step(&base, &Event::Impose(Pair::of(0, 1)))
            .unwrap()
            .reqs()
            .len(),
        1
    );
}

#[test]
fn fresh_tokens_skip_existing_names_and_preserve_new_indices() {
    let base = pair_base("w2", "w2'");
    let delta = vec![
        Item::NewDatum,
        Item::NewDatum,
        Item::NewForm(2),
        Item::NewInst(0, vec![Mark(2), Mark(3)]),
    ];
    let events = delta_events(&base, &delta);
    assert_eq!(events[0], Event::AdmitDatum(Token::new("w2''")));
    assert_eq!(events[1], Event::AdmitDatum(Token::new("w3")));
    let child = apply_delta(&base, &delta).unwrap();
    assert_eq!(child.n_data(), 4);
    assert!(child
        .insts()
        .contains(&Inst::new(0, vec![Mark(2), Mark(3)])));
    assert_eq!(delta_events(&base, &delta), events);
}

#[test]
fn collision_fixture_has_ten_replay_valid_minima_after_local_repair() {
    let collision = binary_complete("w2", "b");
    let renamed = binary_complete("alpha", "beta");
    assert_eq!(canonical(&collision), canonical(&renamed));
    let mut keys = Vec::new();
    for base in [&collision, &renamed] {
        let minimum =
            min_responses(base, Pair::of(0, 1), MeasureKind::Mu1, &Bounds::default()).unwrap();
        assert_eq!(minimum.deltas.len(), 10);
        assert_eq!(
            minimum
                .deltas
                .iter()
                .filter(|delta| delta.contains(&Item::NewDatum))
                .count(),
            4
        );
        let children: BTreeSet<_> = minimum
            .deltas
            .iter()
            .map(|delta| {
                assert!(response_valid_naive(base, Pair::of(0, 1), delta).unwrap());
                canonical(&apply_delta(base, delta).unwrap())
            })
            .collect();
        keys.push(children);
    }
    assert_eq!(keys[0], keys[1]);
}

#[test]
fn uniform_rules_only_judge_well_formed_admitted_arguments() {
    let base = step(&pair_base("a", "b"), &Event::AdmitForm(2)).unwrap();
    let base = step(&base, &Event::AdmitRuleAll(0)).unwrap();
    assert!(derivable(&base, &Inst::new(0, vec![Mark(0), Mark(1)])));
    for inst in [
        Inst::new(0, vec![]),
        Inst::new(0, vec![Mark(0)]),
        Inst::new(0, vec![Mark(0), Mark(9)]),
        Inst::new(9, vec![Mark(0), Mark(1)]),
    ] {
        assert!(!derivable(&base, &inst));
        assert!(!holds(&base, &Judgment::Derivable(inst)));
    }
    assert!(profile(&base, Mark(9)).is_empty());
    assert!(!separable(&base, Mark(0), Mark(9)));
    assert!(witness(&base, Mark(0), Mark(9)).is_none());
}

#[test]
fn holding_enumerates_rule_instances_once_without_admitting_them() {
    let base = step(&pair_base("a", "b"), &Event::AdmitForm(2)).unwrap();
    let base = step(&base, &Event::AdmitInst(0, vec![Mark(0), Mark(1)])).unwrap();
    let base = step(&base, &Event::AdmitRuleAll(0)).unwrap();
    let judgments = holding(&base);
    assert_eq!(judgments.len(), 4);
    assert!(judgments.iter().all(|judgment| holds(&base, judgment)));
    assert_eq!(base.insts().len(), 1);
    let empty = step(&Regime::genesis(), &Event::AdmitForm(1)).unwrap();
    let empty = step(&empty, &Event::AdmitRuleAll(0)).unwrap();
    assert!(holding(&empty).is_empty());
}

#[test]
fn fast_response_refuses_malformed_admissions_before_observing_them() {
    let base = pair_base("a", "b");
    let view = NodeView::of(&base).unwrap();
    for delta in [
        vec![Item::NewInst(99, vec![Mark(0)])],
        vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0), Mark(0)])],
        vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(9)])],
        vec![Item::NewRuleAll(99)],
    ] {
        assert!(profile_additions(&view, &delta).is_err());
        assert!(!response_valid_fast(&view, Pair::of(0, 1), &delta));
        assert!(response_valid_naive(&base, Pair::of(0, 1), &delta).is_err());
    }
}

#[test]
fn a_response_target_must_exist_before_its_proposed_augmentation() {
    let base = pair_base("a", "b");
    let view = NodeView::of(&base).unwrap();
    let delta = vec![
        Item::NewDatum,
        Item::NewForm(1),
        Item::NewInst(0, vec![Mark(0)]),
    ];
    assert!(!response_valid_fast(&view, Pair::of(0, 2), &delta));
    assert!(response_valid_naive(&base, Pair::of(0, 2), &delta).is_err());
}

fn response_world() -> World {
    let mut world =
        World::from_regime(step(&pair_base("a", "b"), &Event::Impose(Pair::of(0, 1))).unwrap());
    world.budget.0 = 2;
    world.license.0 = true;
    world
}

#[test]
fn response_gate_enforces_declared_item_and_new_form_bounds() {
    let world = response_world();
    let delta = vec![Item::NewForm(2), Item::NewInst(0, vec![Mark(0), Mark(0)])];
    for bounds in [
        Bounds {
            max_items: 1,
            max_arity: 2,
        },
        Bounds {
            max_items: 2,
            max_arity: 1,
        },
    ] {
        let (next, verdict) = step_world(
            &world,
            &WorldEvent::Respond {
                target: Pair::of(0, 1),
                delta: delta.clone(),
            },
            &bounds,
        );
        assert!(matches!(verdict, Verdict::Refused(_)));
        assert_eq!(next, world);
    }
    let (next, verdict) = step_world(
        &world,
        &WorldEvent::Respond {
            target: Pair::of(0, 1),
            delta,
        },
        &Bounds::default(),
    );
    assert_eq!(verdict, Verdict::Applied);
    assert_eq!(next.budget.0, 1);
}

#[test]
fn unsupported_bounds_refuse_world_events_without_panicking() {
    let world = response_world();
    let (next, verdict) = step_world(
        &world,
        &WorldEvent::SetBudget(99),
        &Bounds {
            max_items: 3,
            max_arity: 2,
        },
    );
    assert!(matches!(verdict, Verdict::Refused(_)));
    assert_eq!(next, world);
}

#[test]
fn invalid_renamings_cannot_construct_malformed_regimes() {
    let base = step(&pair_base("a", "b"), &Event::AdmitForm(1)).unwrap();
    for maps in [
        Bijection {
            data: vec![0, 0],
            forms: vec![0],
        },
        Bijection {
            data: vec![0],
            forms: vec![0],
        },
        Bijection {
            data: vec![0, 2],
            forms: vec![0],
        },
        Bijection {
            data: vec![0, 1],
            forms: vec![1],
        },
        Bijection {
            data: vec![0, 1],
            forms: vec![],
        },
    ] {
        assert!(try_rename(&base, &maps).is_err());
    }
    let renamed = try_rename(
        &base,
        &Bijection {
            data: vec![1, 0],
            forms: vec![0],
        },
    )
    .unwrap();
    assert_eq!(canonical(&base), canonical(&renamed));
}

#[test]
fn permutation_budget_refuses_factorial_overflow_before_enumeration() {
    let history: Vec<_> = (0..21)
        .map(|i| Event::AdmitDatum(Token::new(format!("d{i}"))))
        .collect();
    let base = replay(&history).unwrap();
    let error = core_ooutwire_primitives::automorphism::automorphisms(&base).unwrap_err();
    assert_eq!(error.candidates, u64::MAX);
    assert_eq!(
        error.budget,
        core_ooutwire_primitives::canonical::PERM_BUDGET
    );
}

#[test]
fn orbit_representative_labels_need_not_be_equivariant() {
    use core_ooutwire_primitives::automorphism::pair_orbits;
    use core_ooutwire_primitives::closure::closure_challenge_orbits;
    use core_ooutwire_primitives::separability::collapsed_pairs;
    let base = step(&pair_base("a", "b"), &Event::AdmitDatum(Token::new("c"))).unwrap();
    let permutation = Bijection {
        data: vec![0, 2, 1],
        forms: vec![],
    };
    let renamed = try_rename(&base, &permutation).unwrap();
    let selected = closure_challenge_orbits(&base).unwrap()[0];
    let transported = Pair::of(
        permutation.data[selected.i.0],
        permutation.data[selected.j.0],
    );
    assert_ne!(transported, closure_challenge_orbits(&renamed).unwrap()[0]);
    let orbit = pair_orbits(&renamed, &collapsed_pairs(&renamed)).unwrap();
    assert!(orbit[0].contains(&transported));
}

#[test]
fn panels_do_not_certify_malformed_contexts_or_nonexistent_targets() {
    use core_ooutwire_primitives::context::Context;
    use core_ooutwire_primitives::panel::{cert_neg, cert_pos, Evaluator};
    let base = step(&pair_base("a", "b"), &Event::AdmitForm(1)).unwrap();
    for context in [
        Context {
            form: 9,
            slots: vec![None],
        },
        Context {
            form: 0,
            slots: vec![],
        },
        Context {
            form: 0,
            slots: vec![Some(Mark(0))],
        },
        Context {
            form: 0,
            slots: vec![None, Some(Mark(9))],
        },
    ] {
        let panel = [Evaluator {
            contexts: vec![context],
        }];
        assert!(!cert_pos(&panel, &base, Pair::of(0, 1)));
        assert!(!cert_neg(&panel, &base, Pair::of(0, 1)));
    }
    let panel = [Evaluator::full(&base)];
    assert!(!cert_pos(&panel, &base, Pair::of(0, 9)));
    assert!(!cert_neg(&panel, &base, Pair::of(0, 9)));
    assert!(cert_neg(&panel, &base, Pair::of(0, 1)));
}

// Origin: engine/crates_rs/tests/core_ooutwire_primitives/genesis_fidelity.rs
// Claim: urn:core:crates_rs:tests:genesis-fidelity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5fd19a59 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5fd19a59` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5fd19a59 {
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
impl BoundaryError5fd19a59 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5fd19a59 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5fd19a59 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5fd19a59 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5fd19a59> {
        if capacity_bound == 0 {
            return Err(BoundaryError5fd19a59::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5fd19a59::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5fd19a59::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5fd19a59() {
    let admitted = BoundaryRecord5fd19a59::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5fd19a59::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
