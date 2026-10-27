//! The refusal every Symbol Game and Adversary port returns. AuthorityEffect: None.
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use unicode_normalization::UnicodeNormalization;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Refusal {
    pub code: String,
    pub message: String,
    pub locus: String,
    pub details: BTreeMap<String, String>,
}
impl Refusal {
    pub fn new(code: &str, message: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            message: message.into().trim().nfc().collect(),
            locus: String::new(),
            details: BTreeMap::new(),
        }
    }
}
impl std::fmt::Display for Refusal {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.message)
    }
}
impl std::error::Error for Refusal {}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiagnosticWeight {
    code_units: u64,
    message_chars: u64,
    detail_count: u64,
    total: u64,
    session_budget: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiagnosticWeightError {
    BadCode,
    ZeroBudget,
    OverBudget { total: u64, session_budget: u64 },
    Overflow,
}

impl DiagnosticWeight {
    pub fn certify(refusal: &Refusal, session_budget: u64) -> Result<Self, DiagnosticWeightError> {
        if refusal.code.trim().is_empty() || refusal.code.chars().any(char::is_whitespace) { return Err(DiagnosticWeightError::BadCode); }
        if session_budget == 0 { return Err(DiagnosticWeightError::ZeroBudget); }
        let code_units = u64::try_from(refusal.code.len()).map_err(|_| DiagnosticWeightError::Overflow)?;
        let message_chars = u64::try_from(refusal.message.chars().count()).map_err(|_| DiagnosticWeightError::Overflow)?;
        let detail_count = u64::try_from(refusal.details.len()).map_err(|_| DiagnosticWeightError::Overflow)?;
        let total = code_units.checked_add(message_chars).ok_or(DiagnosticWeightError::Overflow)?.checked_add(detail_count).ok_or(DiagnosticWeightError::Overflow)?;
        if total > session_budget { return Err(DiagnosticWeightError::OverBudget { total, session_budget }); }
        Ok(Self { code_units, message_chars, detail_count, total, session_budget })
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/refusal.rs
// Claim: urn:core:crates_rs:pfp-runtime:refusal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        let refusal = Refusal::new("PORT_CLOSED", "stopped");
        assert!(matches!(DiagnosticWeight::certify(&refusal, 64), Ok(w) if w.total == 18 && w.code_units == 11 && w.message_chars == 7 && w.detail_count == 0));
        assert!(matches!(DiagnosticWeight::certify(&refusal, 4), Err(DiagnosticWeightError::OverBudget { .. })));
        let spaced = Refusal::new("PORT CLOSED", "stopped");
        assert!(matches!(DiagnosticWeight::certify(&spaced, 64), Err(DiagnosticWeightError::BadCode)));
    }
}
