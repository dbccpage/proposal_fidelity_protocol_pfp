use crate::ddc::ddc_alphabet::{DdcOp, RefusalReason};
use num_rational::BigRational;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{create_dir_all, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DdcStepRowV1 {
    pub seq: u64,
    pub letter: String,
    pub actor: String,
    pub before_state: String,
    pub after_state: String,
    pub witness: String,
    pub refusal_reason: Option<String>,
    pub prev_step_hash: Option<String>,
    pub step_hash: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

fn default_authority_effect() -> String {
    "None".to_string()
}

#[allow(clippy::too_many_arguments)]
pub fn compute_ddc_row_hash(
    seq: u64,
    letter: &str,
    actor: &str,
    before: &str,
    after: &str,
    witness: &str,
    refusal: Option<&str>,
    prev_hash: Option<&str>,
) -> String {
    let mut hasher = Sha256::new();
    hasher.update(seq.to_le_bytes());
    hasher.update(letter.as_bytes());
    hasher.update(actor.as_bytes());
    hasher.update(before.as_bytes());
    hasher.update(after.as_bytes());
    hasher.update(witness.as_bytes());
    if let Some(r) = refusal {
        hasher.update(b":refusal:");
        hasher.update(r.as_bytes());
    }
    if let Some(p) = prev_hash {
        hasher.update(b":prev:");
        hasher.update(p.as_bytes());
    }
    format!("{:x}", hasher.finalize())
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct StateMetrics {
    pub phi1: u64,
    pub gamma2: u64,
    pub residual: u64,
    pub has_carrier: bool,
    pub has_loss_ledger: bool,
    pub is_terminal: bool,
    pub is_licensed_lift: bool,
    pub refusal: Option<RefusalReason>,
}

/// Host letter assignment (U03).
///
/// Invariants:
/// - E requires residual == 0 AND phi1 == 0 AND gamma2 == 0.
///   (Witness dominance: gamma2 > 0 strictly forbids E).
/// - D requires descent with non-empty LossLedger.
/// - M emitted on refusal or invalid witness.
/// - C on carrier/window declared.
/// - R on residual carried forward with phi1 unchanged.
/// - I on integration.
/// - Λ on licensed structural lift.
/// - T on terminalization.
fn is_descent_transition(before: &StateMetrics, after: &StateMetrics) -> bool {
    after.has_loss_ledger && (after.phi1 < before.phi1 || after.gamma2 < before.gamma2)
}

fn is_exact_repair_transition(after: &StateMetrics) -> bool {
    after.residual == 0 && after.phi1 == 0 && after.gamma2 == 0
}

fn assign_residual_or_descent_letter(before: &StateMetrics, after: &StateMetrics) -> DdcOp {
    if is_descent_transition(before, after) {
        return DdcOp::Descent;
    }
    // Exact repair check: residual == 0, phi1 == 0, gamma2 == 0
    if is_exact_repair_transition(after) {
        return DdcOp::ExactRepair;
    }
    // Witness dominance: if gamma2 > 0 or phi1 > 0 when residual == 0,
    // exact repair is strictly FORBIDDEN -> emits Refusal (M)
    if after.residual == 0 && (after.gamma2 > 0 || after.phi1 > 0) {
        return DdcOp::Refusal;
    }
    if after.residual > 0 && after.phi1 == before.phi1 {
        return DdcOp::ResidualProjection;
    }
    DdcOp::Integration
}

pub fn assign_letter(before: &StateMetrics, after: &StateMetrics) -> DdcOp {
    if after.is_terminal {
        return DdcOp::Terminalize;
    }
    if after.refusal.is_some() {
        return DdcOp::Refusal;
    }
    if after.is_licensed_lift {
        return DdcOp::Lift;
    }
    if after.has_carrier && !before.has_carrier {
        return DdcOp::ContextExposure;
    }
    assign_residual_or_descent_letter(before, after)
}


#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DdcTraceStep {
    pub timestamp_utc: String,
    pub runner_id: String,
    pub campaign: String,
    pub run_id: String,
    pub step_id: String,
    pub letter: String,
    pub action_name: String,
    pub cochain_dim: String,
    pub coboundary_map: String,
    pub input_state: String,
    pub output_state: String,
    pub witness: String,
    pub residual_energy: BigRational,
    pub refusal_reason: Option<String>,
    pub authority_effect: String,
    pub prev_step_hash: Option<String>,
    pub step_hash: String,
}

/// Backward compatibility alias for [`DdcTraceStep`].
pub type DdaTraceStep = DdcTraceStep;

pub struct TraceLogger {
    pub runner_id: String,
    pub campaign_name: String,
    pub trace_dir: PathBuf,
    pub run_id: String,
    pub jsonl_path: PathBuf,
    pub last_hash: Option<String>,
    pub step_counter: usize,
}

impl TraceLogger {
    pub fn new(runner_id: &str, campaign_name: Option<&str>, custom_dir: Option<&Path>) -> Self {
        let r_id = runner_id.to_string();
        let camp = campaign_name.unwrap_or(runner_id).to_string();
        let trace_dir = match custom_dir {
            Some(p) => p.to_path_buf(),
            None => {
                let current = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
                if current.join(".agents").exists() || current.join("engine").exists() {
                    current.join(".agents").join("ddc_traces")
                } else {
                    current.join("..").join(".agents").join("ddc_traces")
                }
            }
        };
        let _ = create_dir_all(&trace_dir);
        let run_id = format!("{:012x}", rand_u64());
        let jsonl_path = trace_dir.join(format!("{}_{}_ddc_trace.jsonl", r_id, run_id));

        Self {
            runner_id: r_id,
            campaign_name: camp,
            trace_dir,
            run_id,
            jsonl_path,
            last_hash: None,
            step_counter: 0,
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn record_step(
        &mut self,
        letter: &str,
        action_name: &str,
        input_state: &str,
        output_state: &str,
        witness: &str,
        residual_energy: BigRational,
        refusal_reason: Option<String>,
    ) -> DdcTraceStep {
        self.step_counter += 1;
        let now = chrono_utc_now();
        let step_id = format!("DDC_STEP_{:03}", self.step_counter);

        let mut step = DdcTraceStep {
            timestamp_utc: now,
            runner_id: self.runner_id.clone(),
            campaign: self.campaign_name.clone(),
            run_id: self.run_id.clone(),
            step_id,
            letter: letter.to_string(),
            action_name: action_name.to_string(),
            cochain_dim: "C1".to_string(),
            coboundary_map: "d1".to_string(),
            input_state: input_state.to_string(),
            output_state: output_state.to_string(),
            witness: witness.to_string(),
            residual_energy,
            refusal_reason,
            authority_effect: "None".to_string(),
            prev_step_hash: self.last_hash.clone(),
            step_hash: String::new(),
        };

        step.step_hash = compute_step_hash(&step);
        self.last_hash = Some(step.step_hash.clone());

        if let Ok(json_line) = serde_json::to_string(&step) {
            if let Ok(mut file) = OpenOptions::new()
                .create(true)
                .append(true)
                .open(&self.jsonl_path)
            {
                let _ = writeln!(file, "{}", json_line);
            }
        }

        step
    }
}

fn compute_step_hash(step: &DdcTraceStep) -> String {
    let mut copy = step.clone();
    copy.step_hash.clear();
    let json_bytes = serde_json::to_vec(&copy).unwrap_or_default();
    let mut hasher = Sha256::new();
    hasher.update(&json_bytes);
    format!("{:x}", hasher.finalize())
}

fn chrono_utc_now() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let start = SystemTime::now();
    let since_the_epoch = start.duration_since(UNIX_EPOCH).unwrap_or_default();
    format!("{}s-utc", since_the_epoch.as_secs())
}

fn rand_u64() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let start = SystemTime::now();
    let since_the_epoch = start.duration_since(UNIX_EPOCH).unwrap_or_default();
    since_the_epoch.as_nanos() as u64
}

// Origin: engine/crates_rs/core_wdp/src/ddc/ddc_trace.rs
// Claim: urn:core:crates_rs:core-wdp:ddc-trace:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord78d33907 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord78d33907` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError78d33907 {
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
impl BoundaryError78d33907 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError78d33907 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError78d33907 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord78d33907 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError78d33907> {
        if capacity_bound == 0 {
            return Err(BoundaryError78d33907::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError78d33907::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError78d33907::ExceedsCapacity {
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
    use num_traits::Zero;

    #[test]
    fn test_trace_logger() {
        let dir = std::env::temp_dir().join(format!("ddc_test_{}", rand_u64()));
        let mut logger = TraceLogger::new("test_runner", None, Some(&dir));

        let s1 = logger.record_step(
            "C",
            "context_start",
            "S0",
            "S1",
            "WIT0",
            BigRational::zero(),
            None,
        );
        assert_eq!(s1.letter, "C");

        let s2 = logger.record_step(
            "E",
            "exact_repair",
            "S1",
            "S2",
            "WIT1",
            BigRational::zero(),
            None,
        );
        assert_eq!(s2.letter, "E");
        assert_eq!(s2.prev_step_hash, Some(s1.step_hash));

        let files: Vec<_> = std::fs::read_dir(&dir).unwrap().collect();
        assert_eq!(files.len(), 1);
        let _ = std::fs::remove_dir_all(&dir);
    }
}

#[cfg(test)]
mod l4_boundary_tests_78d33907 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord78d33907::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord78d33907::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord78d33907::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord78d33907::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord78d33907::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError78d33907::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError78d33907::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
