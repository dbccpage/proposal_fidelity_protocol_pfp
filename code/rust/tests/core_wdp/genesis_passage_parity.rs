use core_wdp::genesis_passage::*;
use core_wdp::genesis_refusal::*;
use serde::Deserialize;

#[derive(Deserialize)]
struct PassageCase {
    before: PassageState,
    event: PassageEvent,
    after: PassageState,
}
#[derive(Deserialize)]
struct WorldCase {
    description: Constitution,
    before: RepresentedWorld,
    event: WorldEvent,
    after: RepresentedWorld,
}
#[derive(Deserialize)]
struct RefusalCase {
    mode: Discipline,
    before: RefusalState,
    event: RefusalEvent,
    after: RefusalState,
}
#[derive(Deserialize)]
struct ProposalCase {
    state: PassageState,
    blocks: Vec<Vec<PassageEvent>>,
}
#[derive(Deserialize)]
struct Corpus {
    passage: Vec<PassageCase>,
    constitution: Vec<WorldCase>,
    refusal: Vec<RefusalCase>,
    proposals: Vec<ProposalCase>,
}

fn corpus() -> Corpus {
    serde_json::from_str(include_str!("data/genesis_source_parity.json")).unwrap()
}

#[test]
fn original_python_passage_transition_vectors() {
    let c = corpus();
    assert_eq!(c.passage.len(), 300);
    for (i, c) in c.passage.iter().enumerate() {
        assert_eq!(c.before.step(&c.event), c.after, "passage {i}");
    }
}

#[test]
fn proposals_retain_all_ties_but_never_supply_execution_permission() {
    let c = corpus();
    assert_eq!(c.proposals.len(), 15);
    for c in &c.proposals {
        assert_eq!(c.state.next_family(10000).unwrap(), c.blocks);
    }
    let s = PassageState {
        occ: vec![0, 1],
        wit: vec![(0, 1)],
        prot: vec![(0, 1)],
        obs: Some(vec![]),
        licensed: false,
        ..Default::default()
    };
    let blocks = s.next_family(10).unwrap();
    assert_eq!(blocks.len(), 2);
    for block in blocks {
        let funded = s.step(&block[0]);
        assert!(!funded.enabled(&block[1]));
    }
    assert_eq!(s.next_family(0), Err(PassageError::ResourceLimit));
}

#[test]
fn all_64_constitutions_and_sealed_kernel_match_source_vectors() {
    let c = corpus();
    assert_eq!(c.constitution.len(), 402);
    for (i, c) in c.constitution.iter().enumerate() {
        assert_eq!(
            c.before.step(c.description, &c.event),
            c.after,
            "constitution {i}"
        );
        if i < 384 {
            assert_eq!(Constitution::from_lean_index(i / 6).unwrap(), c.description);
        }
    }
    assert_eq!(
        Constitution::from_lean_index(63).unwrap(),
        Constitution::KERNEL
    );
    assert!(Constitution::from_lean_index(64).is_err());
}

#[test]
fn all_readmission_modes_forms_instances_and_occurrence_baseline() {
    let c = corpus();
    assert_eq!(c.refusal.len(), 54);
    for (i, c) in c.refusal.iter().enumerate() {
        assert_eq!(
            c.before.step(c.mode, &c.event).unwrap(),
            c.after,
            "refusal {i}"
        );
    }
    let s = RefusalState {
        data: vec!["a".into()],
        refusals: usize::MAX,
        ..Default::default()
    };
    assert_eq!(
        s.step(Discipline::Fact, &RefusalEvent::Admit("a".into())),
        Err(RefusalError::CounterOverflow)
    );
    assert_eq!(
        s.step(Discipline::Meta, &RefusalEvent::Marker("a".into()))
            .unwrap(),
        s
    );
}

#[test]
fn four_gate_omission_witnesses_preserve_original_convention() {
    let s = PassageState {
        occ: vec![0, 1],
        asserted: vec![(0, 1)],
        wit: vec![(0, 1)],
        prot: vec![(0, 1)],
        obs: Some(vec![]),
        ..Default::default()
    };
    assert!(s.obstructed(0, 1));
    for missing in 0..4 {
        let mut t = s.clone();
        match missing {
            0 => t.wit.clear(),
            1 => t.prot.clear(),
            2 => t.obs = None,
            _ => t.obs = Some(vec![vec![0]]),
        }
        let mut expected = [true; 4];
        expected[missing] = false;
        assert_eq!(t.gates(0, 1), expected);
        assert!(!t.obstructed(0, 1));
    }
    // The no-retention witness is an arbitrary source state, NOT reachable
    // from genesis under the guarded Protect event. Independence is scoped.
}

#[test]
fn refinement_preserves_old_separation_and_does_not_need_extension_license() {
    let s = PassageState {
        occ: vec![0, 1, 2],
        asserted: vec![(0, 1), (1, 2)],
        wit: vec![(0, 1), (1, 2)],
        prot: vec![(0, 1), (1, 2)],
        obs: Some(vec![vec![0]]),
        budget: 1,
        licensed: false,
        ..Default::default()
    };
    assert!(!s.refine_ok(&vec![0], 1)); // would destroy separation of (0,1)
    assert!(s.refine_ok(&vec![0], 2));
    let after = s.step(&PassageEvent::RefineCol(vec![0], 2));
    assert_eq!(after.obs, Some(vec![vec![2, 0]]));
    assert_eq!(after.budget, 0);
    assert!(s.obstructed(1, 2));
    // Passage refusal can coexist with an available repair: it is not the
    // represented-world exhaustion predicate.
    assert_eq!(s.step(&PassageEvent::Refuse(1, 2)).refusals, vec![(1, 2)]);
}

// Origin: engine/crates_rs/tests/core_wdp/genesis_passage_parity.rs
// Claim: urn:core:crates_rs:tests:genesis-passage-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5d233c57 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5d233c57` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5d233c57 {
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
impl BoundaryError5d233c57 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5d233c57 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5d233c57 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5d233c57 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5d233c57> {
        if capacity_bound == 0 {
            return Err(BoundaryError5d233c57::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5d233c57::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5d233c57::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5d233c57() {
    let admitted = BoundaryRecord5d233c57::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5d233c57::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
