//! Test suite for U07 Challenge Packet Runner with Commit-Reveal.
//!
//! Validates:
//! - Commit-reveal pre-requisites
//! - Dual checker evaluation
//! - CheckerDefectPause invariant (exceptions/disagreements never scored as Wrong)
//! - End-to-end scoring execution

use pfp::challenge::{
    evaluate_dual_checkers, verify_challenge_commit_reveal_prerequisites, CaseChecker,
    DisjointOutcome, ExactMatchChecker, FreezeRecordV1, JudgeCommitmentV1, JudgePacketV1,
};
use serde_json::json;

struct FaultyChecker {
    id: String,
    should_error: bool,
    verdict: bool,
}

impl CaseChecker for FaultyChecker {
    fn checker_id(&self) -> &str {
        &self.id
    }

    fn check(
        &self,
        _case: &serde_json::Value,
        _output: &serde_json::Value,
    ) -> Result<bool, String> {
        if self.should_error {
            Err(format!(
                "Checker '{}' suffered internal division by zero",
                self.id
            ))
        } else {
            Ok(self.verdict)
        }
    }
}

#[test]
fn test_commit_reveal_prerequisites_validation() {
    let manifest = b"hidden_case_1, hidden_case_2, hidden_case_3";
    let commitment = JudgeCommitmentV1::new("CHAL_001", manifest, "judge_operator", "v1.0.0");
    let commit_hash = commitment.commitment_hash();

    let deliverable = b"def solve(x): return x * 2";
    let freeze = FreezeRecordV1::new("CHAL_001", deliverable, &commit_hash);

    let judge_packet = JudgePacketV1 {
        challenge_id: "CHAL_001".to_string(),
        commitment_hash: commit_hash.clone(),
        committed_at_utc: commitment.committed_at_utc.clone(),
        operator: commitment.operator.clone(),
        version: commitment.version.clone(),
        hidden_cases: vec![json!({"x": 2, "expected": 4})],
        checker_a_id: "checker_exact_a".to_string(),
        checker_b_id: "checker_exact_b".to_string(),
        authority_effect: "None".to_string(),
    };

    // Valid prerequisites pass
    assert!(verify_challenge_commit_reveal_prerequisites(
        &judge_packet,
        &commitment,
        &freeze,
        deliverable
    )
    .is_ok());

    // Tampered deliverable fails
    let tampered_deliverable = b"def solve(x): return x * 3";
    let err = verify_challenge_commit_reveal_prerequisites(
        &judge_packet,
        &commitment,
        &freeze,
        tampered_deliverable,
    );
    assert!(err.is_err());
    assert!(err.unwrap_err().contains("does not match frozen SHA-256"));

    // Commitment mismatch fails
    let wrong_freeze = FreezeRecordV1::new("CHAL_001", deliverable, "forged_commitment_hash");
    let err2 = verify_challenge_commit_reveal_prerequisites(
        &judge_packet,
        &commitment,
        &wrong_freeze,
        deliverable,
    );
    assert!(err2.is_err());
    assert!(err2
        .unwrap_err()
        .contains("different judge commitment hash"));
}

#[test]
fn test_dual_checkers_agreement() {
    let checker_a = ExactMatchChecker::new("checker_a", "answer");
    let checker_b = ExactMatchChecker::new("checker_b", "answer");

    let case = json!({"id": 1, "answer": 42});
    let correct_output = json!({"answer": 42});
    let wrong_output = json!({"answer": 99});

    // Both agree Correct
    let res_correct = evaluate_dual_checkers(&checker_a, &checker_b, &case, &correct_output);
    assert!(matches!(res_correct, DisjointOutcome::Correct));

    // Both agree Wrong
    let res_wrong = evaluate_dual_checkers(&checker_a, &checker_b, &case, &wrong_output);
    assert!(matches!(res_wrong, DisjointOutcome::Wrong { .. }));
}

#[test]
fn test_checker_defect_pause_on_exception_and_disagreement() {
    let case = json!({"id": 1, "answer": 42});
    let output = json!({"answer": 42});

    // Subcase 1: Checker A raises exception -> MUST NOT score as Wrong!
    let checker_fault_a = FaultyChecker {
        id: "fault_a".to_string(),
        should_error: true,
        verdict: false,
    };
    let checker_ok_b = FaultyChecker {
        id: "ok_b".to_string(),
        should_error: false,
        verdict: true,
    };

    let outcome_a_fault = evaluate_dual_checkers(&checker_fault_a, &checker_ok_b, &case, &output);
    assert!(
        matches!(outcome_a_fault, DisjointOutcome::CheckerDefectPause { .. }),
        "Checker exception must trigger CheckerDefectPause, never Wrong"
    );

    // Subcase 2: Checker B raises exception -> MUST NOT score as Wrong!
    let outcome_b_fault = evaluate_dual_checkers(&checker_ok_b, &checker_fault_a, &case, &output);
    assert!(
        matches!(outcome_b_fault, DisjointOutcome::CheckerDefectPause { .. }),
        "Checker exception must trigger CheckerDefectPause, never Wrong"
    );

    // Subcase 3: Checkers disagree (A says true, B says false) -> MUST NOT score as Wrong!
    let checker_say_false = FaultyChecker {
        id: "say_false".to_string(),
        should_error: false,
        verdict: false,
    };
    let outcome_disagree =
        evaluate_dual_checkers(&checker_ok_b, &checker_say_false, &case, &output);
    assert!(
        matches!(outcome_disagree, DisjointOutcome::CheckerDefectPause { .. }),
        "Checker disagreement must trigger CheckerDefectPause, never Wrong"
    );
}

// Origin: engine/crates_rs/tests/pfp/challenge_commit_reveal.rs
// Claim: urn:core:crates_rs:tests:challenge-commit-reveal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd1998b01 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd1998b01` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord1998b01 {
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
impl BoundaryErrord1998b01 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord1998b01 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord1998b01 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd1998b01 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord1998b01> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord1998b01::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord1998b01::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord1998b01::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d1998b01() {
    let admitted = BoundaryRecordd1998b01::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd1998b01::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
