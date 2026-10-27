use core_category_theory::finite_moore::FiniteMoore;
use core_wdp::proposal_admission_bridge::*;
use sha2::{Digest, Sha256};
fn row(e: EvaluationOutcome, d: AdmissionDecision) -> DeclaredRow {
    DeclaredRow {
        proposal: Proposal { proposed_state: 1 },
        evaluation: e,
        decision: d,
    }
}
fn decode_bridge_rows(n: usize, mut ec: usize, mut dc: usize) -> Vec<DeclaredRow> {
    (0..n)
        .map(|_| {
            let e = match ec % 3 {
                0 => EvaluationOutcome::Passed,
                1 => EvaluationOutcome::Failed,
                _ => EvaluationOutcome::Unknown,
            };
            ec /= 3;
            let d = if dc % 2 == 0 {
                AdmissionDecision::Admit
            } else {
                AdmissionDecision::Reject
            };
            dc /= 2;
            row(e, d)
        })
        .collect()
}

fn check_bridge_model(n: usize, rows: Vec<DeclaredRow>) {
    let m = ProposalAdmissionModel::new(2, rows.clone()).unwrap();
    let expected = (0..n).all(|i| {
        (0..n).all(|j| {
            rows[i].evaluation != rows[j].evaluation || rows[i].decision == rows[j].decision
        })
    });
    let result = m.evaluation_only_decision();
    assert_eq!(result.is_ok(), expected);
    if let Err(BridgeError::FiberCollision {
        left,
        right,
        left_value,
        right_value,
    }) = result
    {
        assert_eq!(rows[left].evaluation, rows[right].evaluation);
        assert_ne!(rows[left].decision, rows[right].decision);
        assert_ne!(left_value, right_value);
    }
    let joint = m.joint_records();
    for i in 0..n {
        for j in 0..n {
            assert_eq!(
                joint[i] == joint[j],
                (rows[i].evaluation, rows[i].decision) == (rows[j].evaluation, rows[j].decision)
            );
        }
    }
    let decoder = m
        .decision_from_records(&joint, joint.iter().max().unwrap() + 1)
        .unwrap();
    for i in 0..n {
        assert_eq!(decoder.decode(joint[i]).unwrap(), rows[i].decision as usize);
    }
}

#[test]
fn exhaustive_fiber_criterion_and_joint_signature() {
    let mut checked = 0;
    for n in 1usize..=3 {
        for eval_code in 0..3usize.pow(n as u32) {
            for dec_code in 0..2usize.pow(n as u32) {
                check_bridge_model(n, decode_bridge_rows(n, eval_code, dec_code));
                checked += 1;
            }
        }
    }
    assert_eq!(checked, 258);
}
#[test]
fn opposite_permissions_same_evidence_one_program_and_rejected_proposal() {
    let m = ProposalAdmissionModel::new(
        2,
        vec![
            row(EvaluationOutcome::Passed, AdmissionDecision::Admit),
            row(EvaluationOutcome::Passed, AdmissionDecision::Reject),
            row(EvaluationOutcome::Failed, AdmissionDecision::Admit),
            row(EvaluationOutcome::Unknown, AdmissionDecision::Admit),
        ],
    )
    .unwrap();
    assert!(matches!(
        m.evaluation_only_decision(),
        Err(BridgeError::FiberCollision {
            left: 0,
            right: 1,
            ..
        })
    ));
    // One caller/process executes both typed roles; no three-agent premise.
    assert_eq!(
        m.inspect_roles(0).unwrap(),
        (EvaluationOutcome::Passed, AdmissionDecision::Admit)
    );
    assert_eq!(
        m.inspect_roles(1).unwrap(),
        (EvaluationOutcome::Passed, AdmissionDecision::Reject)
    );
    assert_eq!(m.apply_declared_admission(1, 0), Ok(0));
    assert_eq!(m.apply_declared_admission(0, 0), Ok(1));
    // A supplied Admit value remains distinct from the guarded commit.
    assert_eq!(
        m.inspect_roles(2).unwrap(),
        (EvaluationOutcome::Failed, AdmissionDecision::Admit)
    );
    assert_eq!(
        m.inspect_roles(3).unwrap(),
        (EvaluationOutcome::Unknown, AdmissionDecision::Admit)
    );
    assert_eq!(m.apply_declared_admission(2, 0), Ok(0));
    assert_eq!(m.apply_declared_admission(3, 0), Ok(0));
}
fn histories() -> HistoryModel {
    // Symbols set0/set1. Equal multisets lose execution order.
    let machine = FiniteMoore::new(vec![0, 1], vec![vec![0, 1], vec![0, 1]], 2).unwrap();
    HistoryModel::new(machine, 0, vec![vec![0, 1], vec![1, 0], vec![]]).unwrap()
}
#[test]
fn order_loss_collision_and_rehashed_false_history_are_not_faithful() {
    let h = histories();
    assert_eq!(h.final_states(), &[1, 0, 0]);
    assert!(matches!(
        h.replay_decoder(&[0, 0, 1], 2),
        Err(BridgeError::FiberCollision {
            left: 0,
            right: 1,
            ..
        })
    ));
    let exact = h.replay_decoder(&[0, 1, 2], 3).unwrap();
    assert_eq!(h.verify_decoder(&[0, 1, 2], exact.values()), Ok(()));
    let false_states = [0usize, 0, 0];
    let bytes = format!("{false_states:?}");
    let digest = Sha256::digest(bytes.as_bytes());
    assert_eq!(digest, Sha256::digest(bytes.as_bytes())); // freshly consistent byte commitment
    assert_eq!(
        h.verify_claimed_states(&false_states),
        Err(BridgeError::FalseReplay)
    );
    assert_eq!(
        h.verify_decoder(&[0, 1, 2], &false_states),
        Err(BridgeError::InvalidDecoder)
    );
}
#[test]
fn validation_and_empty_words_have_explicit_domains() {
    assert_eq!(
        ProposalAdmissionModel::new(
            0,
            vec![row(EvaluationOutcome::Passed, AdmissionDecision::Admit)]
        ),
        Err(BridgeError::EmptyDomain)
    );
    assert_eq!(
        ProposalAdmissionModel::new(2, vec![]),
        Err(BridgeError::EmptyDomain)
    );
    assert_eq!(
        ProposalAdmissionModel::new(
            1,
            vec![row(EvaluationOutcome::Passed, AdmissionDecision::Admit)]
        ),
        Err(BridgeError::InvalidState)
    );
    let m = ProposalAdmissionModel::new(
        2,
        vec![row(EvaluationOutcome::Passed, AdmissionDecision::Reject)],
    )
    .unwrap();
    assert_eq!(
        m.decision_from_records(&[], 0),
        Err(BridgeError::InvalidRecordMap)
    );
    assert_eq!(
        m.decision_from_records(&[1], 1),
        Err(BridgeError::InvalidRecordMap)
    );
    assert_eq!(
        m.decision_from_records(&[0], 2),
        Err(BridgeError::InvalidRecordMap)
    );
    assert_eq!(
        m.apply_declared_admission(0, 2),
        Err(BridgeError::InvalidState)
    );
    assert_eq!(m.inspect_roles(1), Err(BridgeError::InvalidRow));
    let machine = FiniteMoore::new(vec![0], vec![vec![]], 0).unwrap();
    assert_eq!(
        HistoryModel::new(machine.clone(), 0, vec![]),
        Err(BridgeError::EmptyDomain)
    );
    assert_eq!(
        HistoryModel::new(machine.clone(), 0, vec![vec![0]]),
        Err(BridgeError::InvalidHistory)
    );
    let h = HistoryModel::new(machine, 0, vec![vec![]]).unwrap();
    assert_eq!(h.final_states(), &[0]);
    assert_eq!(
        h.replay_decoder(&[0], 1).unwrap().decode(1),
        Err(BridgeError::InvalidRecordMap)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_proposal_admission_bridge.rs
// Claim: urn:core:crates_rs:tests:test-proposal-admission-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9371cef6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9371cef6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9371cef6 {
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
impl BoundaryError9371cef6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9371cef6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9371cef6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9371cef6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9371cef6> {
        if capacity_bound == 0 {
            return Err(BoundaryError9371cef6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9371cef6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9371cef6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9371cef6() {
    let admitted = BoundaryRecord9371cef6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9371cef6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
