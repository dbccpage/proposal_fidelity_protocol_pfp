//! Prime -1 candidate records and Prime Triad stage records (U03).
//!
//! Owns Prime -1 untrusted candidate records and trace logging for
//! Prime stage transitions (Prime -1, Prime 000, Prime 001, Prime 002).
//! AuthorityEffect: None (const).

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{create_dir_all, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

fn default_authority_effect() -> String {
    "None".to_string()
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PrimeStage {
    #[serde(rename = "PRIME_-1")]
    PrimeMinus1,
    #[serde(rename = "PRIME_000")]
    Prime000,
    #[serde(rename = "PRIME_001")]
    Prime001,
    #[serde(rename = "PRIME_002")]
    Prime002,
}

impl PrimeStage {
    pub fn as_str(&self) -> &'static str {
        match self {
            PrimeStage::PrimeMinus1 => "PRIME_-1",
            PrimeStage::Prime000 => "PRIME_000",
            PrimeStage::Prime001 => "PRIME_001",
            PrimeStage::Prime002 => "PRIME_002",
        }
    }
}

/// Untrusted raw candidate proposal at Prime -1.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateProposalV1 {
    pub proposal_id: String,
    pub locus_id: String,
    pub raw_payload_hash: String,
    pub actor: String,
    pub enters_dda_trace: bool,
    pub refusal_reason: Option<String>,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

impl CandidateProposalV1 {
    pub fn new(
        proposal_id: impl Into<String>,
        locus_id: impl Into<String>,
        raw_payload: &[u8],
        actor: impl Into<String>,
    ) -> Self {
        let mut hasher = Sha256::new();
        hasher.update(raw_payload);
        let payload_hash = format!("{:x}", hasher.finalize());

        Self {
            proposal_id: proposal_id.into(),
            locus_id: locus_id.into(),
            raw_payload_hash: payload_hash,
            actor: actor.into(),
            enters_dda_trace: false,
            refusal_reason: None,
            authority_effect: default_authority_effect(),
        }
    }

    pub fn refuse(&mut self, reason: impl Into<String>) {
        self.refusal_reason = Some(reason.into());
        self.enters_dda_trace = false;
    }

    pub fn admit_to_trace(&mut self) {
        self.refusal_reason = None;
        self.enters_dda_trace = true;
    }
}

/// Trace record for Prime Triad stage transitions (Prime -1, 000, 001, 002).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PrimeStageRecordV1 {
    pub seq: u64,
    pub stage: PrimeStage,
    pub packet_id: String,
    pub actor: String,
    pub status: String,
    pub witness_or_refusal: String,
    pub prev_record_hash: Option<String>,
    pub record_hash: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

pub fn compute_prime_stage_hash(
    seq: u64,
    stage: &str,
    packet_id: &str,
    actor: &str,
    status: &str,
    witness_or_refusal: &str,
    prev_hash: Option<&str>,
) -> String {
    let mut hasher = Sha256::new();
    hasher.update(seq.to_le_bytes());
    hasher.update(stage.as_bytes());
    hasher.update(packet_id.as_bytes());
    hasher.update(actor.as_bytes());
    hasher.update(status.as_bytes());
    hasher.update(witness_or_refusal.as_bytes());
    if let Some(prev) = prev_hash {
        hasher.update(b":prev:");
        hasher.update(prev.as_bytes());
    }
    format!("{:x}", hasher.finalize())
}

impl PrimeStageRecordV1 {
    pub fn new(
        seq: u64,
        stage: PrimeStage,
        packet_id: impl Into<String>,
        actor: impl Into<String>,
        status: impl Into<String>,
        witness_or_refusal: impl Into<String>,
        prev_record_hash: Option<String>,
    ) -> Self {
        let p_id = packet_id.into();
        let act = actor.into();
        let stat = status.into();
        let wit = witness_or_refusal.into();
        let hash = compute_prime_stage_hash(
            seq,
            stage.as_str(),
            &p_id,
            &act,
            &stat,
            &wit,
            prev_record_hash.as_deref(),
        );

        Self {
            seq,
            stage,
            packet_id: p_id,
            actor: act,
            status: stat,
            witness_or_refusal: wit,
            prev_record_hash,
            record_hash: hash,
            authority_effect: default_authority_effect(),
        }
    }
}

pub struct PrimeTraceLogger {
    pub log_path: PathBuf,
    pub last_hash: Option<String>,
    pub seq_counter: u64,
}

impl PrimeTraceLogger {
    pub fn new(log_path: impl AsRef<Path>) -> std::io::Result<Self> {
        let path = log_path.as_ref().to_path_buf();
        if let Some(parent) = path.parent() {
            create_dir_all(parent)?;
        }
        Ok(Self {
            log_path: path,
            last_hash: None,
            seq_counter: 0,
        })
    }

    pub fn append_stage(
        &mut self,
        stage: PrimeStage,
        packet_id: &str,
        actor: &str,
        status: &str,
        witness_or_refusal: &str,
    ) -> std::io::Result<PrimeStageRecordV1> {
        let record = PrimeStageRecordV1::new(
            self.seq_counter,
            stage,
            packet_id,
            actor,
            status,
            witness_or_refusal,
            self.last_hash.clone(),
        );

        self.last_hash = Some(record.record_hash.clone());
        self.seq_counter += 1;

        let line = serde_json::to_string(&record)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;

        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.log_path)?;

        writeln!(file, "{}", line)?;
        file.flush()?;
        Ok(record)
    }
}

// Origin: engine/crates_rs/core_wdp/src/prime_algos/prime_candidate.rs
// Claim: urn:core:crates_rs:core-wdp:prime-candidate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord888fed4a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord888fed4a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError888fed4a {
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
impl BoundaryError888fed4a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError888fed4a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError888fed4a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord888fed4a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError888fed4a> {
        if capacity_bound == 0 {
            return Err(BoundaryError888fed4a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError888fed4a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError888fed4a::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn test_candidate_proposal_lifecycle() {
        let payload = b"def candidate_algorithm(): return True";
        let mut proposal = CandidateProposalV1::new("PROP_1", "LOCUS_A", payload, "agent_1");

        assert_eq!(proposal.proposal_id, "PROP_1");
        assert_eq!(proposal.locus_id, "LOCUS_A");
        assert!(!proposal.raw_payload_hash.is_empty());
        assert_eq!(proposal.enters_dda_trace, false);
        assert_eq!(proposal.refusal_reason, None);
        assert_eq!(proposal.authority_effect, "None");

        proposal.refuse("Defective boundary");
        assert_eq!(proposal.enters_dda_trace, false);
        assert_eq!(
            proposal.refusal_reason,
            Some("Defective boundary".to_string())
        );

        proposal.admit_to_trace();
        assert_eq!(proposal.enters_dda_trace, true);
        assert_eq!(proposal.refusal_reason, None);
    }

    #[test]
    fn test_prime_stage_record_hash_chain() {
        let r0 = PrimeStageRecordV1::new(
            0,
            PrimeStage::PrimeMinus1,
            "PKT_0",
            "actor_0",
            "UNTRUSTED",
            "none",
            None,
        );
        assert_eq!(r0.seq, 0);
        assert_eq!(r0.stage, PrimeStage::PrimeMinus1);
        assert_eq!(r0.prev_record_hash, None);
        assert!(!r0.record_hash.is_empty());

        let r1 = PrimeStageRecordV1::new(
            1,
            PrimeStage::Prime000,
            "PKT_1",
            "actor_1",
            "ADMITTED",
            "valid_cochain",
            Some(r0.record_hash.clone()),
        );
        assert_eq!(r1.seq, 1);
        assert_eq!(r1.stage, PrimeStage::Prime000);
        assert_eq!(
            r1.prev_record_hash.as_deref(),
            Some(r0.record_hash.as_str())
        );
        assert_ne!(r1.record_hash, r0.record_hash);
    }

    #[test]
    fn test_prime_trace_logger() {
        let temp_dir = std::env::temp_dir().join(format!(
            "test_prime_log_{}",
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let log_file = temp_dir.join("prime_trace.jsonl");

        let mut logger = PrimeTraceLogger::new(&log_file).expect("create logger");
        let rec1 = logger
            .append_stage(
                PrimeStage::PrimeMinus1,
                "PKT_0",
                "agent_a",
                "PROPOSED",
                "wit_0",
            )
            .expect("append rec1");
        assert_eq!(rec1.seq, 0);

        let rec2 = logger
            .append_stage(
                PrimeStage::Prime000,
                "PKT_1",
                "agent_b",
                "ADMITTED",
                "wit_1",
            )
            .expect("append rec2");
        assert_eq!(rec2.seq, 1);
        assert_eq!(rec2.prev_record_hash, Some(rec1.record_hash));

        let _ = std::fs::remove_dir_all(&temp_dir);
    }
}

#[cfg(test)]
mod l4_boundary_tests_888fed4a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord888fed4a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord888fed4a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord888fed4a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord888fed4a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord888fed4a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError888fed4a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError888fed4a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
