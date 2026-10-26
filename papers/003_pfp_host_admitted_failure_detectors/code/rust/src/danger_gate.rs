//! Two-signal decision table for PFP Paper 003 (Rust port of `code/danger_gate.py`).
//!
//! The name "danger gate" is a component name only. Signal 1 (a pattern match)
//! alone is diagnostic; a supplied Signal 2 defect alone refuses only when its
//! severity is high or critical; both signals refuse; neither is tolerated.
//! The table does not check that a supplied defect is real.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DangerDecision {
    #[serde(rename = "TOLERATED")]
    Tolerated,
    #[serde(rename = "DIAGNOSTIC_ONLY")]
    DiagnosticOnly,
    #[serde(rename = "DEFENSIVE_LOCKDOWN")]
    DefensiveLockdown,
    #[serde(rename = "QUARANTINED")]
    Quarantined,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DangerSeverity {
    #[serde(rename = "LOW")]
    Low,
    #[serde(rename = "MEDIUM")]
    Medium,
    #[serde(rename = "HIGH")]
    High,
    #[serde(rename = "CRITICAL")]
    Critical,
}

impl DangerSeverity {
    /// Wire name, identical to the serde representation and to the Python string.
    pub fn wire_name(self) -> &'static str {
        match self {
            DangerSeverity::Low => "LOW",
            DangerSeverity::Medium => "MEDIUM",
            DangerSeverity::High => "HIGH",
            DangerSeverity::Critical => "CRITICAL",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Signal1Match {
    pub epitope_name: String,
    pub pattern_matched: String,
    pub confidence_num: u64,
    pub confidence_den: u64,
    pub offset: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Signal2Danger {
    pub danger_type: String,
    pub severity: DangerSeverity,
    pub defect_count: usize,
    pub evidence_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TwoSignalDecision {
    pub decision: DangerDecision,
    pub is_refusal: bool,
    pub disposition: String,
    pub signal1_count: usize,
    pub signal2_severity: Option<DangerSeverity>,
    pub is_suppressed: bool,
    pub rationale: String,
}

pub fn evaluate_two_signal_gate(
    signal1_matches: &[Signal1Match],
    signal2: Option<&Signal2Danger>,
) -> TwoSignalDecision {
    let s1_count = signal1_matches.len();
    let has_s1 = s1_count > 0;

    match (has_s1, signal2) {
        // Conjunction of both signals -> Immediate refusal and quarantine
        (true, Some(s2)) => TwoSignalDecision {
            decision: DangerDecision::Quarantined,
            is_refusal: true,
            disposition: "REFUSED_DUAL_SIGNAL_CORROBORATION".to_string(),
            signal1_count: s1_count,
            signal2_severity: Some(s2.severity),
            is_suppressed: true,
            rationale: format!(
                "Both Signal 1 (syntax pattern: {}) and Signal 2 (structural damage: {}) detected.",
                signal1_matches[0].epitope_name,
                s2.severity.wire_name()
            ),
        },
        // Signal 2 alone -> Lockdown if severe, diagnostic if low/medium
        (false, Some(s2)) => match s2.severity {
            DangerSeverity::High | DangerSeverity::Critical => TwoSignalDecision {
                decision: DangerDecision::DefensiveLockdown,
                is_refusal: true,
                disposition: "REFUSED_CRITICAL_STRUCTURAL_DEFECT".to_string(),
                signal1_count: 0,
                signal2_severity: Some(s2.severity),
                is_suppressed: true,
                rationale: format!(
                    "High/Critical Signal 2 defect ({}) without Signal 1 match triggers defensive lockdown.",
                    s2.danger_type
                ),
            },
            DangerSeverity::Low | DangerSeverity::Medium => TwoSignalDecision {
                decision: DangerDecision::DiagnosticOnly,
                is_refusal: false,
                disposition: "DIAGNOSTIC_LOW_SEVERITY_DEFECT".to_string(),
                signal1_count: 0,
                signal2_severity: Some(s2.severity),
                is_suppressed: false,
                rationale: format!(
                    "Low/Medium Signal 2 defect ({}) retained as diagnostic observation without refusal.",
                    s2.danger_type
                ),
            },
        },
        // Signal 1 alone -> Diagnostic observation only (never confuses mention with execution)
        (true, None) => TwoSignalDecision {
            decision: DangerDecision::DiagnosticOnly,
            is_refusal: false,
            disposition: "DIAGNOSTIC_SYNTAX_MATCH_ONLY".to_string(),
            signal1_count: s1_count,
            signal2_severity: None,
            is_suppressed: false,
            rationale: format!(
                "Signal 1 pattern match ({}) without Signal 2 structural damage is diagnostic only.",
                signal1_matches[0].epitope_name
            ),
        },
        // Neither signal -> Clean execution tolerated
        (false, None) => TwoSignalDecision {
            decision: DangerDecision::Tolerated,
            is_refusal: false,
            disposition: "TOLERATED_CLEAN_PROPOSAL".to_string(),
            signal1_count: 0,
            signal2_severity: None,
            is_suppressed: false,
            rationale: "Neither syntactic violation nor structural defect detected.".to_string(),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_gate_tolerated() {
        let dec = evaluate_two_signal_gate(&[], None);
        assert_eq!(dec.decision, DangerDecision::Tolerated);
        assert!(!dec.is_refusal);
    }

    #[test]
    fn test_gate_signal1_alone() {
        let s1 = vec![Signal1Match {
            epitope_name: "AM-FSP-8".to_string(),
            pattern_matched: "Troyer-Wiese".to_string(),
            confidence_num: 1,
            confidence_den: 1,
            offset: 0,
        }];
        let dec = evaluate_two_signal_gate(&s1, None);
        assert_eq!(dec.decision, DangerDecision::DiagnosticOnly);
        assert!(!dec.is_refusal);
    }

    #[test]
    fn test_gate_conjunction_refused() {
        let s1 = vec![Signal1Match {
            epitope_name: "AM-FSP-2".to_string(),
            pattern_matched: "particle-hole on triangle".to_string(),
            confidence_num: 1,
            confidence_den: 1,
            offset: 0,
        }];
        let s2 = Signal2Danger {
            danger_type: "PROTECTED_FIELD_MUTATION".to_string(),
            severity: DangerSeverity::Medium,
            defect_count: 1,
            evidence_digest: "abcd1234".to_string(),
        };
        let dec = evaluate_two_signal_gate(&s1, Some(&s2));
        assert_eq!(dec.decision, DangerDecision::Quarantined);
        assert!(dec.is_refusal);
        assert!(dec.is_suppressed);
    }
}
