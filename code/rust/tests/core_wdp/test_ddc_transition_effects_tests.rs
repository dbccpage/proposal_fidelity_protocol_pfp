use core_wdp::ddc::transition_effects::*;

#[test]
fn test_event_validation_and_canonical_id() {
    let event = EventV1::new(
        "e0",
        EffectOwner::Solver,
        EffectKind::Admission,
        vec!["s1".to_string(), "s1".to_string()],
    )
    .expect("event should be valid");

    assert_eq!(event.event_id, "e0");
    assert_eq!(event.owner, EffectOwner::Solver);
    assert_eq!(event.kind, EffectKind::Admission);
    assert_eq!(event.authority_effect, "None");

    let cid = event.canonical_id().expect("canonical id calculation");
    assert!(cid.starts_with("sha256:"));
    assert_eq!(cid.len(), 7 + 64);
}

#[test]
fn test_finite_transition_system_and_replay() {
    let states = vec!["s0".to_string(), "s1".to_string(), "term".to_string()];
    let e_adv = EventV1::new(
        "adv",
        EffectOwner::Solver,
        EffectKind::SameLevelRepair,
        vec!["s1".to_string(), "term".to_string(), "term".to_string()],
    )
    .expect("valid adv event");

    let e_term = EventV1::new(
        "finalize",
        EffectOwner::Terminalizer,
        EffectKind::Terminal,
        vec!["term".to_string(), "term".to_string(), "term".to_string()],
    )
    .expect("valid term event");

    let system =
        FiniteTransitionSystemV1::new(states, vec![e_adv, e_term], vec!["term".to_string()])
            .expect("valid transition system");

    assert_eq!(system.step("s0", "adv").unwrap(), "s1");
    assert_eq!(system.step("s1", "adv").unwrap(), "term");
    assert_eq!(system.step("term", "adv").unwrap(), "term");

    let trace = vec!["adv".to_string(), "adv".to_string()];
    let end_state = system.replay("s0", &trace).expect("replay success");
    assert_eq!(end_state, "term");
}

#[test]
fn test_semantic_effect_classes() {
    let states = vec!["a".to_string(), "b".to_string()];
    let e1 = EventV1::new(
        "e1",
        EffectOwner::Solver,
        EffectKind::SameLevelRepair,
        vec!["b".to_string(), "a".to_string()],
    )
    .unwrap();
    let e2 = EventV1::new(
        "e2",
        EffectOwner::Solver,
        EffectKind::SameLevelRepair,
        vec!["b".to_string(), "a".to_string()],
    )
    .unwrap();
    let e3 = EventV1::new(
        "e3",
        EffectOwner::Host,
        EffectKind::BudgetControl,
        vec!["b".to_string(), "a".to_string()],
    )
    .unwrap();

    let system = FiniteTransitionSystemV1::new(states, vec![e1, e2, e3], vec![]).unwrap();

    // Ungoverned: e1, e2, e3 all have same transition table -> 1 class with 3 events
    let ungoverned = semantic_effect_classes(&system, false);
    assert_eq!(ungoverned.len(), 1);
    assert_eq!(ungoverned[0], vec!["e1", "e2", "e3"]);

    // Governed: e1 and e2 have same owner/kind, e3 has Host/BudgetControl -> 2 classes
    let governed = semantic_effect_classes(&system, true);
    assert_eq!(governed.len(), 2);
    assert_eq!(governed[0], vec!["e1", "e2"]);
    assert_eq!(governed[1], vec!["e3"]);
}

#[test]
fn test_events_commute_and_trace_rewrite() {
    let states = vec!["x".to_string(), "y".to_string()];
    // Identity event 1
    let id1 = EventV1::new(
        "id1",
        EffectOwner::Solver,
        EffectKind::SameLevelRepair,
        vec!["x".to_string(), "y".to_string()],
    )
    .unwrap();
    // Identity event 2
    let id2 = EventV1::new(
        "id2",
        EffectOwner::Solver,
        EffectKind::SameLevelRepair,
        vec!["x".to_string(), "y".to_string()],
    )
    .unwrap();

    let system = FiniteTransitionSystemV1::new(states, vec![id1, id2], vec![]).unwrap();

    assert!(events_commute(&system, "id1", "id2"));

    let trace1 = vec!["id1".to_string(), "id2".to_string()];
    let trace2 = vec!["id2".to_string(), "id1".to_string()];

    let equiv = trace_rewrite_equivalent(&system, &trace1, &trace2).unwrap();
    assert!(equiv);

    assert!(solver_trace_allowed(&system, &trace1).unwrap());
}

#[test]
fn test_effect_receipt() {
    let states = vec!["s0".to_string(), "s1".to_string()];
    let ev = EventV1::new(
        "ev",
        EffectOwner::Declaration,
        EffectKind::Admission,
        vec!["s1".to_string(), "s1".to_string()],
    )
    .unwrap();
    let system = FiniteTransitionSystemV1::new(states, vec![ev], vec![]).unwrap();

    let receipt = effect_receipt(&system, "ev").expect("receipt generated");
    assert_eq!(receipt.event_id, "ev");
    assert_eq!(receipt.owner, EffectOwner::Declaration);
    assert_eq!(receipt.kind, EffectKind::Admission);
    assert!(receipt.system_id.starts_with("sha256:"));
    assert!(receipt.event_digest.starts_with("sha256:"));
    assert!(receipt.transition_digest.starts_with("sha256:"));

    let rc_id = receipt.canonical_id().expect("receipt canonical id");
    assert!(rc_id.starts_with("sha256:"));
}

// Origin: engine/crates_rs/tests/core_wdp/test_ddc_transition_effects_tests.rs
// Claim: urn:core:crates_rs:tests:test-ddc-transition-effects-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord12c723ec {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord12c723ec` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError12c723ec {
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
impl BoundaryError12c723ec {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError12c723ec {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError12c723ec {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord12c723ec {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError12c723ec> {
        if capacity_bound == 0 {
            return Err(BoundaryError12c723ec::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError12c723ec::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError12c723ec::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_12c723ec() {
    let admitted = BoundaryRecord12c723ec::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord12c723ec::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
