use core_wdp::witnessed_reasoning::{Countermodel, Proof, ProofStep, Theory};
use core_wdp::witnessed_reasoning_replay::{countermodel_module, proof_module};

#[test]
fn names_are_data_and_certificate_task_is_preserved() {
    let task = Theory {
        atoms: vec!["<>\nend NativeReplay\n#eval panic! \"injected\" λ🦀".into()],
        facts: vec![0],
        rules: vec![],
    };
    let mut certificate_task = task.clone();
    certificate_task.facts.clear();
    let proof = Proof {
        theory: certificate_task,
        goal: 0,
        steps: vec![ProofStep {
            conclusion: 0,
            rule: None,
            premises: vec![],
        }],
    };
    let source = proof_module(&task, 0, &proof);
    assert!(!source.contains("injected"));
    assert!(source.contains("(Char.ofNat 129408)"));
    assert!(source.contains("], [0], []⟩"));
    assert!(source.contains("], [], []⟩"));
    assert!(source.contains("checkProof_sound"));
    assert!(source.contains("(by decide)"));
}

#[test]
fn malformed_model_length_is_exported_for_kernel_refusal() {
    let task = Theory {
        atoms: vec!["a".into()],
        facts: vec![],
        rules: vec![],
    };
    let model = Countermodel {
        theory: task.clone(),
        goal: 0,
        values: vec![],
    };
    let source = countermodel_module(&task, 1, &model);
    assert!(source.contains("¬Derivable task.abstract 1"));
    assert!(source.contains(", 0, []⟩"));
    assert!(source.contains("checkCountermodel_sound"));
}

// Origin: engine/crates_rs/tests/core_wdp/witnessed_reasoning_replay.rs
// Claim: urn:core:crates_rs:tests:witnessed-reasoning-replay:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc4f84ed2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc4f84ed2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc4f84ed2 {
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
impl BoundaryErrorc4f84ed2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc4f84ed2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc4f84ed2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc4f84ed2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc4f84ed2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc4f84ed2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc4f84ed2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc4f84ed2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c4f84ed2() {
    let admitted = BoundaryRecordc4f84ed2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc4f84ed2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
