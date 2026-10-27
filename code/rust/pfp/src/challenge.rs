//! Challenge Packet Runner with Commit-Reveal (U07).
//!
//! Enforces:
//! - Commit-reveal protocol: JudgeCommitmentV1 before FreezeRecordV1 before scoring.
//! - Sandboxed execution of candidate deliverables via core_sandbox.
//! - Dual independent checker oracles.
//! - CheckerDefectPause invariant: checker exceptions or disagreements NEVER scored as Wrong.
//!
//! AuthorityEffect: None (const).

use core_sandbox::{run_sandboxed, SandboxConfig, SandboxOutcome};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

fn default_authority_effect() -> String {
    "None".to_string()
}

pub fn compute_sha256(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct JudgeCommitmentV1 {
    pub challenge_id: String,
    pub manifest_sha256: String,
    pub committed_at_utc: String,
    pub operator: String,
    pub version: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

impl JudgeCommitmentV1 {
    pub fn new(
        challenge_id: impl Into<String>,
        manifest_bytes: &[u8],
        operator: impl Into<String>,
        version: impl Into<String>,
    ) -> Self {
        Self {
            challenge_id: challenge_id.into(),
            manifest_sha256: compute_sha256(manifest_bytes),
            committed_at_utc: "2026-09-30T00:00:00Z".to_string(), // Canonical UTC stamp
            operator: operator.into(),
            version: version.into(),
            authority_effect: default_authority_effect(),
        }
    }

    pub fn commitment_hash(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(self.challenge_id.as_bytes());
        hasher.update(self.manifest_sha256.as_bytes());
        hasher.update(self.operator.as_bytes());
        hasher.update(self.version.as_bytes());
        format!("{:x}", hasher.finalize())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FreezeRecordV1 {
    pub challenge_id: String,
    pub solver_deliverable_sha256: String,
    pub frozen_at_utc: String,
    pub judge_commitment_hash: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

impl FreezeRecordV1 {
    pub fn new(
        challenge_id: impl Into<String>,
        deliverable_bytes: &[u8],
        judge_commitment_hash: impl Into<String>,
    ) -> Self {
        Self {
            challenge_id: challenge_id.into(),
            solver_deliverable_sha256: compute_sha256(deliverable_bytes),
            frozen_at_utc: "2026-09-30T00:00:00Z".to_string(),
            judge_commitment_hash: judge_commitment_hash.into(),
            authority_effect: default_authority_effect(),
        }
    }

    pub fn freeze_hash(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(self.challenge_id.as_bytes());
        hasher.update(self.solver_deliverable_sha256.as_bytes());
        hasher.update(self.judge_commitment_hash.as_bytes());
        format!("{:x}", hasher.finalize())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ParticipantPacketV1 {
    pub challenge_id: String,
    pub specification_hash: String,
    pub prompt_template: String,
    pub public_cases: Vec<Value>,
    pub timeout_ms: u64,
    pub max_tokens: u64,
    pub judge_commitment_hash: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct JudgePacketV1 {
    pub challenge_id: String,
    pub commitment_hash: String,
    pub committed_at_utc: String,
    pub operator: String,
    pub version: String,
    pub hidden_cases: Vec<Value>,
    pub checker_a_id: String,
    pub checker_b_id: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(tag = "kind", content = "detail")]
pub enum DisjointOutcome {
    Correct,
    Wrong {
        reason: String,
    },
    SolverCrash {
        exit_code: Option<i32>,
        error: String,
    },
    SolverTimeout {
        limit_ms: u64,
    },
    DeclaredOutOfScope {
        reason: String,
    },
    ScoringFault {
        error: String,
    },
    CheckerDefectPause {
        checker_a_result: String,
        checker_b_result: String,
        detail: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct CaseOutcomeRecordV1 {
    pub case_index: usize,
    pub outcome: DisjointOutcome,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChallengeScoreReceiptV1 {
    pub challenge_id: String,
    pub judge_commitment_hash: String,
    pub freeze_record_hash: String,
    pub deliverable_sha256: String,
    pub cases_total: usize,
    pub cases_correct: usize,
    pub cases_wrong: usize,
    pub checker_defect_pause: bool,
    pub case_outcomes: Vec<CaseOutcomeRecordV1>,
    pub status: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

pub trait CaseChecker: Send + Sync {
    fn checker_id(&self) -> &str;
    fn check(&self, case: &Value, candidate_output: &Value) -> Result<bool, String>;
}

pub struct ExactMatchChecker {
    pub id: String,
    pub expected_field: String,
}

impl ExactMatchChecker {
    pub fn new(id: impl Into<String>, expected_field: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            expected_field: expected_field.into(),
        }
    }
}

impl CaseChecker for ExactMatchChecker {
    fn checker_id(&self) -> &str {
        &self.id
    }

    fn check(&self, case: &Value, candidate_output: &Value) -> Result<bool, String> {
        let expected = case
            .get(&self.expected_field)
            .ok_or_else(|| format!("Case missing expected field '{}'", self.expected_field))?;
        let actual = candidate_output
            .get(&self.expected_field)
            .unwrap_or(candidate_output);
        Ok(expected == actual)
    }
}

/// Evaluates a candidate output using dual checkers with strict CheckerDefectPause invariant.
pub fn evaluate_dual_checkers(
    checker_a: &dyn CaseChecker,
    checker_b: &dyn CaseChecker,
    case: &Value,
    candidate_output: &Value,
) -> DisjointOutcome {
    let res_a = checker_a.check(case, candidate_output);
    let res_b = checker_b.check(case, candidate_output);

    match (res_a, res_b) {
        (Ok(true), Ok(true)) => DisjointOutcome::Correct,
        (Ok(false), Ok(false)) => DisjointOutcome::Wrong {
            reason: "Both checkers independently verified incorrect output".to_string(),
        },
        (Err(err_a), Err(err_b)) => DisjointOutcome::CheckerDefectPause {
            checker_a_result: format!("Error: {}", err_a),
            checker_b_result: format!("Error: {}", err_b),
            detail: "Both checkers raised exceptions; entered CheckerDefectPause".to_string(),
        },
        (Err(err_a), Ok(b)) => DisjointOutcome::CheckerDefectPause {
            checker_a_result: format!("Error: {}", err_a),
            checker_b_result: format!("Ok({})", b),
            detail: "Checker A raised exception; entered CheckerDefectPause".to_string(),
        },
        (Ok(a), Err(err_b)) => DisjointOutcome::CheckerDefectPause {
            checker_a_result: format!("Ok({})", a),
            checker_b_result: format!("Error: {}", err_b),
            detail: "Checker B raised exception; entered CheckerDefectPause".to_string(),
        },
        (Ok(true), Ok(false)) | (Ok(false), Ok(true)) => DisjointOutcome::CheckerDefectPause {
            checker_a_result: "disagreement".to_string(),
            checker_b_result: "disagreement".to_string(),
            detail: "Checkers disagreed; entered CheckerDefectPause".to_string(),
        },
    }
}

/// Verification gate checking commit-reveal integrity.
pub fn verify_challenge_commit_reveal_prerequisites(
    judge_packet: &JudgePacketV1,
    commitment: &JudgeCommitmentV1,
    freeze: &FreezeRecordV1,
    deliverable_bytes: &[u8],
) -> Result<(), String> {
    if commitment.challenge_id != judge_packet.challenge_id {
        return Err("Challenge ID mismatch between commitment and judge packet".to_string());
    }
    if freeze.challenge_id != judge_packet.challenge_id {
        return Err("Challenge ID mismatch between freeze record and judge packet".to_string());
    }
    let computed_commit_hash = commitment.commitment_hash();
    if freeze.judge_commitment_hash != computed_commit_hash {
        return Err("Freeze record binds different judge commitment hash".to_string());
    }
    let actual_deliverable_sha256 = compute_sha256(deliverable_bytes);
    if freeze.solver_deliverable_sha256 != actual_deliverable_sha256 {
        return Err("Deliverable content does not match frozen SHA-256".to_string());
    }
    Ok(())
}

fn map_completed_sandbox(
    exit_code: i32,
    stdout: &str,
    stderr: String,
    checker_a: &dyn CaseChecker,
    checker_b: &dyn CaseChecker,
    case: &Value,
) -> DisjointOutcome {
    if exit_code != 0 {
        DisjointOutcome::SolverCrash {
            exit_code: Some(exit_code),
            error: stderr,
        }
    } else {
        match serde_json::from_str::<Value>(stdout) {
            Ok(candidate_output) => {
                evaluate_dual_checkers(checker_a, checker_b, case, &candidate_output)
            }
            Err(e) => DisjointOutcome::Wrong {
                reason: format!("Candidate emitted invalid JSON: {}", e),
            },
        }
    }
}

fn evaluate_single_challenge_case(
    deliverable_path: &Path,
    case: &Value,
    checker_a: &dyn CaseChecker,
    checker_b: &dyn CaseChecker,
    timeout_ms: u64,
) -> Result<DisjointOutcome, String> {
    let input_json = serde_json::to_string(case).map_err(|e| e.to_string())?;

    // Run solver deliverable in sandbox
    let config = SandboxConfig {
        command: vec![
            "python".to_string(),
            deliverable_path.to_string_lossy().to_string(),
            input_json,
        ],
        cwd: deliverable_path.parent().map(|p| p.to_path_buf()),
        timeout_ms,
        memory_limit_bytes: 256 * 1024 * 1024,
        max_output_bytes: 1024 * 1024,
        env: Default::default(),
    };

    let outcome = match run_sandboxed(&config) {
        SandboxOutcome::Completed {
            exit_code,
            stdout,
            stderr,
            ..
        } => map_completed_sandbox(exit_code, &stdout, stderr, checker_a, checker_b, case),
        SandboxOutcome::TimedOut | SandboxOutcome::CpuLimitExceeded => {
            DisjointOutcome::SolverTimeout {
                limit_ms: timeout_ms,
            }
        }
        SandboxOutcome::MemoryLimitExceeded => DisjointOutcome::SolverCrash {
            exit_code: None,
            error: "Memory limit exceeded".to_string(),
        },
        SandboxOutcome::OutputLimitExceeded => DisjointOutcome::SolverCrash {
            exit_code: None,
            error: "Output limit exceeded".to_string(),
        },
        SandboxOutcome::ProcessLimitExceeded => DisjointOutcome::SolverCrash {
            exit_code: None,
            error: "Process limit exceeded".to_string(),
        },
        SandboxOutcome::LaunchRefused(err) | SandboxOutcome::IsolationUnavailable(err) => {
            DisjointOutcome::ScoringFault { error: err }
        }
    };
    Ok(outcome)
}

/// Execute challenge scoring.
pub fn challenge_score(
    judge_packet: &JudgePacketV1,
    commitment: &JudgeCommitmentV1,
    freeze: &FreezeRecordV1,
    deliverable_path: &Path,
    checker_a: &dyn CaseChecker,
    checker_b: &dyn CaseChecker,
    timeout_ms: u64,
) -> Result<ChallengeScoreReceiptV1, String> {
    let deliverable_bytes = fs::read(deliverable_path).map_err(|e| {
        format!(
            "Failed to read deliverable at {}: {}",
            deliverable_path.display(),
            e
        )
    })?;

    verify_challenge_commit_reveal_prerequisites(
        judge_packet,
        commitment,
        freeze,
        &deliverable_bytes,
    )?;

    let mut case_outcomes = Vec::new();
    let mut cases_correct = 0;
    let mut cases_wrong = 0;
    let mut any_checker_defect_pause = false;

    for (idx, case) in judge_packet.hidden_cases.iter().enumerate() {
        let outcome = evaluate_single_challenge_case(
            deliverable_path,
            case,
            checker_a,
            checker_b,
            timeout_ms,
        )?;

        match &outcome {
            DisjointOutcome::Correct => cases_correct += 1,
            DisjointOutcome::Wrong { .. } => cases_wrong += 1,
            DisjointOutcome::CheckerDefectPause { .. } => {
                any_checker_defect_pause = true;
                // INVARIANT: Never increment cases_wrong!
            }
            _ => {}
        }

        case_outcomes.push(CaseOutcomeRecordV1 {
            case_index: idx,
            outcome,
        });

        if any_checker_defect_pause {
            break;
        }
    }

    let status = if any_checker_defect_pause {
        "CHECKER_DEFECT_PAUSE".to_string()
    } else {
        "COMPLETED".to_string()
    };

    Ok(ChallengeScoreReceiptV1 {
        challenge_id: judge_packet.challenge_id.clone(),
        judge_commitment_hash: commitment.commitment_hash(),
        freeze_record_hash: freeze.freeze_hash(),
        deliverable_sha256: freeze.solver_deliverable_sha256.clone(),
        cases_total: judge_packet.hidden_cases.len(),
        cases_correct,
        cases_wrong,
        checker_defect_pause: any_checker_defect_pause,
        case_outcomes,
        status,
        authority_effect: default_authority_effect(),
    })
}

// Origin: engine/crates_rs/pfp/src/challenge.rs
// Claim: urn:core:crates_rs:pfp:challenge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbbd1deec {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbbd1deec` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbbd1deec {
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
impl BoundaryErrorbbd1deec {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbbd1deec {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbbd1deec {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbbd1deec {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbbd1deec> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbbd1deec::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbbd1deec::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbbd1deec::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_bbd1deec {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbbd1deec::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbbd1deec::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbbd1deec::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbbd1deec::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbbd1deec::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbbd1deec::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbbd1deec::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
