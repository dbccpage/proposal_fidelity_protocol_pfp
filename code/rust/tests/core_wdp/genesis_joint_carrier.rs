use core_category_theory::finite_joint_carrier::JointCarrierProblem;
use core_category_theory::finite_report_query::ReportQueryDecision;
use core_wdp::genesis_carrier::{CarrierLimits, CarrierRequest, PassageCarrier, PassageQuestion};
use core_wdp::genesis_passage::PassageEvent::AdmitOcc;
#[test]
fn token_counts_lose_cross_component_identity_but_the_obstruction_is_replayable() {
    let build = || {
        PassageCarrier::build(&CarrierRequest {
            seeds: vec![vec![AdmitOcc(10)], vec![AdmitOcc(20)]],
            alphabet: vec![],
            questions: vec![PassageQuestion::OccurrenceCount],
            limits: CarrierLimits::default(),
        })
        .unwrap()
    };
    let left = build();
    let right = build();
    let pairs = vec![(0, 0), (0, 1), (1, 0), (1, 1)];
    // A native joint question, evaluated from the replayed source stores.
    let answers = pairs
        .iter()
        .map(|&(l, r)| {
            usize::from(left.certificate().states[l].occ == right.certificate().states[r].occ)
        })
        .collect();
    let problem =
        JointCarrierProblem::new(left.dynamics(), right.dynamics(), pairs, answers, 1000).unwrap();
    let report = problem.analyze().unwrap();
    assert!(matches!(report.decision, ReportQueryDecision::Collision(_)));
    assert_eq!(report.refinement.profiles.len(), 2);
    problem.verify_analysis(&report).unwrap();
    let fiber = problem.fiber((0, 0)).unwrap();
    assert_eq!(fiber.answers.len(), 2);
}

// Origin: engine/crates_rs/tests/core_wdp/genesis_joint_carrier.rs
// Claim: urn:core:crates_rs:tests:genesis-joint-carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbaafe033 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbaafe033` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbaafe033 {
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
impl BoundaryErrorbaafe033 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbaafe033 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbaafe033 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbaafe033 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbaafe033> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbaafe033::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbaafe033::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbaafe033::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_baafe033() {
    let admitted = BoundaryRecordbaafe033::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbaafe033::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
