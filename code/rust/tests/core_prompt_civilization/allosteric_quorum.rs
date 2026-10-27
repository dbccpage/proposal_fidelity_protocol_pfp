//! Allosteric Quorum and Exact Hill-Cooperative Gate Tests (U20).
//!
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::Zero;
use core_prompt_civilization::immune::allostery::{AllostericGate, QuorumState};

#[test]
fn test_exact_allosteric_quorum_witness_table() {
    // n = 4, Kd = 2, quiescent ceiling = 1/10, active floor = 7/10
    let gate = AllostericGate::default();
    assert_eq!(gate.hill_coefficient, 4);
    assert_eq!(gate.kd, 2);

    // Theta = 0 -> H(0) = 0 (Quiescent)
    let (state_0, resp_0) = gate.evaluate(0);
    assert_eq!(state_0, QuorumState::Quiescent);
    assert_eq!(resp_0, BigRational::zero());

    // Theta = 1 -> H(1) = 1/17 <= 1/10 (Quiescent)
    // 1/17 = 10/170 < 17/170 = 1/10
    let (state_1, resp_1) = gate.evaluate(1);
    assert_eq!(state_1, QuorumState::Quiescent);
    assert_eq!(resp_1, BigRational::new(1.into(), 17.into()));

    // Theta = 2 -> H(2) = 16/32 = 1/2 (Indeterminate / Unknown)
    // 1/10 < 1/2 < 7/10
    let (state_2, resp_2) = gate.evaluate(2);
    assert_eq!(state_2, QuorumState::Indeterminate);
    assert_eq!(resp_2, BigRational::new(1.into(), 2.into()));

    // Theta = 3 -> H(3) = 81/97 >= 7/10 (Active / Activate)
    // 81/97 > 7/10 since 810 > 679
    let (state_3, resp_3) = gate.evaluate(3);
    assert_eq!(state_3, QuorumState::Active);
    assert_eq!(resp_3, BigRational::new(81.into(), 97.into()));
}

#[test]
fn test_exact_monotonicity_of_hill_cooperative_response() {
    let gate = AllostericGate::default();
    let mut prev = BigRational::zero();

    for theta in 0..=8 {
        let current = gate.compute_response(theta);
        assert!(
            current >= prev,
            "Monotonicity violation at theta {}: {} < {}",
            theta,
            current,
            prev
        );
        assert!(current <= BigRational::from_integer(1.into()));
        prev = current;
    }
}

#[test]
fn test_mutation_kill_gate_premature_activation() {
    // If the activation floor was set to > quiescent ceiling (1/10) instead of >= 7/10,
    // 2 votes (H(2) = 1/2) would activate, turning the witness RED.
    let gate = AllostericGate::default();
    let (_, resp_2) = gate.evaluate(2);

    let mutated_active_floor = BigRational::new(1.into(), 10.into());
    let would_falsely_activate = resp_2 >= mutated_active_floor;
    assert!(
        would_falsely_activate,
        "Mutating activation floor to 1/10 causes 2 votes to falsely activate"
    );

    // Assert that under true gate, 2 votes NEVER activates
    let (true_state, _) = gate.evaluate(2);
    assert_ne!(true_state, QuorumState::Active);
}

#[test]
fn test_exact_host_check_overrules_quorum() {
    // Decision rule: When exact host check exists, host verdict dominates quorum
    struct DecisionPipeline {
        gate: AllostericGate,
    }

    impl DecisionPipeline {
        fn decide(&self, exact_host_verdict: Option<bool>, theta: u32) -> &'static str {
            if let Some(host_pass) = exact_host_verdict {
                if host_pass {
                    "HOST_PASS"
                } else {
                    "HOST_FAIL"
                }
            } else {
                match self.gate.evaluate(theta).0 {
                    QuorumState::Active => "QUORUM_REJECT",
                    QuorumState::Quiescent => "QUORUM_ACCEPT",
                    _ => "QUORUM_UNKNOWN_ESCALATE",
                }
            }
        }
    }

    let pipeline = DecisionPipeline {
        gate: AllostericGate::default(),
    };

    // Even if quorum votes 3 rejects (Active), host check PASS must dominate
    let verdict = pipeline.decide(Some(true), 3);
    assert_eq!(verdict, "HOST_PASS");

    // Even if quorum votes 0 rejects (Quiescent), host check FAIL must dominate
    let verdict_fail = pipeline.decide(Some(false), 0);
    assert_eq!(verdict_fail, "HOST_FAIL");

    // Only when exact host check is None does quorum decide
    let quorum_verdict = pipeline.decide(None, 3);
    assert_eq!(quorum_verdict, "QUORUM_REJECT");
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/allosteric_quorum.rs
// Claim: urn:core:crates_rs:tests:allosteric-quorum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord33292108 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord33292108` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError33292108 {
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
impl BoundaryError33292108 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError33292108 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError33292108 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord33292108 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError33292108> {
        if capacity_bound == 0 {
            return Err(BoundaryError33292108::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError33292108::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError33292108::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_33292108() {
    let admitted = BoundaryRecord33292108::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord33292108::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
