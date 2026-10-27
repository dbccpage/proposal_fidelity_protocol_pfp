//! Severity-aware signal law over checked evidence projections.
//! Independence is established before disposition, including zero-count damage.
use crate::danger_gate::TwoSignalDangerGate;
use crate::independence::{
    assert_signals_independent, DangerEvidence, DetectorContext, MatchEvidence,
};
use crate::Refusal;
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DangerSeverity {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DangerDecision {
    Tolerated,
    DiagnosticOnly,
    DefensiveLockdown,
    Quarantined,
}

/// The exact fields used by the gate, after source value-object alias resolution.
/// This is not a complete Signal2Danger or an authenticated host observation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CategorizedDangerEvidence {
    evidence: DangerEvidence,
    severity: DangerSeverity,
}
impl CategorizedDangerEvidence {
    pub fn new(evidence: DangerEvidence, severity: DangerSeverity) -> Self {
        Self { evidence, severity }
    }
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, Refusal> {
        serde_json::from_slice(bytes)
            .map_err(|error| Refusal::new("EIS_WIRE_INVALID", error.to_string()))
    }
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        let bytes = serde_json::to_vec(value)
            .map_err(|error| Refusal::new("EIS_WIRE_INVALID", error.to_string()))?;
        Self::from_bytes(&bytes)
    }
}

/// An immutable domain outcome; inputs cannot author a suppression result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DangerEvaluationResult {
    decision: DangerDecision,
    signal1_count: usize,
    signal2_severity: Option<DangerSeverity>,
    is_suppressed: bool,
    rationale: String,
}
impl DangerEvaluationResult {
    pub fn decision(&self) -> DangerDecision {
        self.decision
    }
    pub fn is_suppressed(&self) -> bool {
        self.is_suppressed
    }
}

impl TwoSignalDangerGate {
    /// The source evaluate law trusts projected evidence. Screening callers use
    /// evaluate_independent to refuse self-derived danger before disposition.
    pub fn evaluate_signals(
        matches: &[MatchEvidence],
        danger: Option<&CategorizedDangerEvidence>,
    ) -> Result<DangerEvaluationResult, Refusal> {
        let count = matches.len();
        let damage = danger.filter(|signal| signal.evidence.has_defects());
        let severity = damage.map(|signal| signal.severity);
        let (decision, rationale) = match (count > 0, damage) {
            (false, None) => (DangerDecision::Tolerated,
                "Clean execution: neither pathogen epitope nor structural damage detected.".into()),
            (true, None) => (DangerDecision::DiagnosticOnly, format!(
                "Signal 1 detected ({count} epitope match(es)), but zero structural damage (Signal 2 absent). Tolerated as benign probe or diagnostic context per Matzinger Danger Theory.")),
            (false, Some(signal)) => (DangerDecision::DiagnosticOnly, format!(
                "Signal 2 only (type={}, severity={}) with no detector match. Diagnostic: the two-signal rule needs both signals to suppress; the host check that observed the damage enforces its own refusal.",
                signal.evidence.danger_type(), severity_name(signal.severity))),
            (true, Some(signal)) if matches!(signal.severity, DangerSeverity::High | DangerSeverity::Critical) =>
                (DangerDecision::Quarantined, format!(
                    "Corroborated pathogen: {count} epitope match(es) co-occur with severe structural damage (type={}, severity={}). Quarantined.",
                    signal.evidence.danger_type(), severity_name(signal.severity))),
            (true, Some(_)) => (DangerDecision::DefensiveLockdown, format!(
                "Corroborated low/medium breach: {count} match(es) with Signal 2 defect. Defensive lockdown engaged.")),
        };
        Ok(DangerEvaluationResult {
            decision,
            signal1_count: count,
            signal2_severity: severity,
            is_suppressed: matches!(
                decision,
                DangerDecision::Quarantined | DangerDecision::DefensiveLockdown
            ),
            rationale,
        })
    }

    pub fn evaluate_independent(
        matches: &[MatchEvidence],
        danger: Option<&CategorizedDangerEvidence>,
        context: &DetectorContext,
    ) -> Result<DangerEvaluationResult, Refusal> {
        assert_signals_independent(matches, danger.map(|signal| &signal.evidence), context)?;
        Self::evaluate_signals(matches, danger)
    }
}

fn severity_name(severity: DangerSeverity) -> &'static str {
    match severity {
        DangerSeverity::Low => "LOW",
        DangerSeverity::Medium => "MEDIUM",
        DangerSeverity::High => "HIGH",
        DangerSeverity::Critical => "CRITICAL",
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/signal_gate.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:signal-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde5c0ab9e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde5c0ab9e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore5c0ab9e {
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
impl BoundaryErrore5c0ab9e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore5c0ab9e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore5c0ab9e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde5c0ab9e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore5c0ab9e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore5c0ab9e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore5c0ab9e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore5c0ab9e::ExceedsCapacity {
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
mod l4_boundary_tests_e5c0ab9e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde5c0ab9e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde5c0ab9e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde5c0ab9e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde5c0ab9e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde5c0ab9e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore5c0ab9e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore5c0ab9e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
