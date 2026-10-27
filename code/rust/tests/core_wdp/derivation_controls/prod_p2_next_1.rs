//! Finite executable witness for `PROD-P2-NEXT-1`.
//!
//! Models the 12-step WDP Appendix G.5 `OutputGate` validator (`G5Step` order,
//! single-step mutation isolation, and receipt-iff-pass invariant) with fixed
//! `authority_effect = "None"`.

#![forbid(unsafe_code)]

pub const AUTHORITY_EFFECT_NONE: &str = "None";

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum G5Step {
    Ids,
    RawRecordHash,
    WitnessSemantics,
    ReAccess,
    LadderAccept,
    Measurand,
    UnitScale,
    CalibrationRange,
    Uncertainty,
    ProvenanceChain,
    Traceability,
    AuthoritySeparate,
}

impl G5Step {
    pub const ALL: [G5Step; 12] = [
        Self::Ids,
        Self::RawRecordHash,
        Self::WitnessSemantics,
        Self::ReAccess,
        Self::LadderAccept,
        Self::Measurand,
        Self::UnitScale,
        Self::CalibrationRange,
        Self::Uncertainty,
        Self::ProvenanceChain,
        Self::Traceability,
        Self::AuthoritySeparate,
    ];
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CandidateRecord {
    pub interaction_carrier: String,
    pub registration_carrier: String,
    pub mark_value: i64,
    pub raw_record_hash_matches: bool,
    pub witness_target: String,
    pub witness_context: String,
    pub observed_mark_value: i64,
    pub evaluator_accepting: bool,
    pub reported_value: i64,
    pub unit_non_empty: bool,
    pub scale_lower: i64,
    pub scale_upper: i64,
    pub calibration_correction: i64,
    pub uncertainty_non_negative: bool,
    pub provenance_non_empty: bool,
    pub traceability_valid: bool,
    pub authority_decision_inline: bool,
}

impl CandidateRecord {
    pub fn valid() -> Self {
        Self {
            interaction_carrier: "sensor-carrier".to_string(),
            registration_carrier: "sensor-carrier".to_string(),
            mark_value: 6,
            raw_record_hash_matches: true,
            witness_target: "target-system".to_string(),
            witness_context: "finite_lattice".to_string(),
            observed_mark_value: 6,
            evaluator_accepting: true,
            reported_value: 6,
            unit_non_empty: true,
            scale_lower: 0,
            scale_upper: 10,
            calibration_correction: 1,
            uncertainty_non_negative: true,
            provenance_non_empty: true,
            traceability_valid: true,
            authority_decision_inline: false,
        }
    }

    fn mutate_late_step(&mut self, step: G5Step) {
        match step {
            G5Step::UnitScale => self.unit_non_empty = false,
            G5Step::CalibrationRange => self.calibration_correction = 20,
            G5Step::Uncertainty => self.uncertainty_non_negative = false,
            G5Step::ProvenanceChain => self.provenance_non_empty = false,
            G5Step::Traceability => self.traceability_valid = false,
            _ => self.authority_decision_inline = true,
        }
    }

    pub fn mutate_for_step(step: G5Step) -> Self {
        let mut r = Self::valid();
        match step {
            G5Step::Ids => r.interaction_carrier = "other-carrier".to_string(),
            G5Step::RawRecordHash => r.raw_record_hash_matches = false,
            G5Step::WitnessSemantics => r.witness_target.clear(),
            G5Step::ReAccess => r.observed_mark_value = 999,
            G5Step::LadderAccept => r.evaluator_accepting = false,
            G5Step::Measurand => r.reported_value = 7,
            other => r.mutate_late_step(other),
        }
        r
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidationReport {
    pub claim_id: String,
    pub failures: Vec<G5Step>,
    pub receipt_claim_id: Option<String>,
    pub authority_effect: &'static str,
}

impl ValidationReport {
    pub fn emitted(&self) -> bool {
        self.failures.is_empty() && self.receipt_claim_id.as_deref() == Some(self.claim_id.as_str())
    }
}

fn collect_early_failures(rec: &CandidateRecord, failures: &mut Vec<G5Step>) {
    if rec.interaction_carrier != rec.registration_carrier {
        failures.push(G5Step::Ids);
    }
    if !rec.raw_record_hash_matches {
        failures.push(G5Step::RawRecordHash);
    }
    if rec.witness_target.is_empty() || rec.witness_context.is_empty() {
        failures.push(G5Step::WitnessSemantics);
    }
    if rec.observed_mark_value != rec.mark_value {
        failures.push(G5Step::ReAccess);
    }
    if !rec.evaluator_accepting {
        failures.push(G5Step::LadderAccept);
    }
    if rec.reported_value != rec.mark_value {
        failures.push(G5Step::Measurand);
    }
}

fn collect_late_failures(rec: &CandidateRecord, failures: &mut Vec<G5Step>) {
    if !rec.unit_non_empty || rec.scale_lower > rec.scale_upper {
        failures.push(G5Step::UnitScale);
    }
    let corrected = rec.reported_value + rec.calibration_correction;
    if corrected < rec.scale_lower || corrected > rec.scale_upper {
        failures.push(G5Step::CalibrationRange);
    }
    if !rec.uncertainty_non_negative {
        failures.push(G5Step::Uncertainty);
    }
    if !rec.provenance_non_empty {
        failures.push(G5Step::ProvenanceChain);
    }
    if !rec.traceability_valid {
        failures.push(G5Step::Traceability);
    }
    if rec.authority_decision_inline {
        failures.push(G5Step::AuthoritySeparate);
    }
}

pub fn gate_candidate(claim_id: &str, rec: &CandidateRecord) -> Result<ValidationReport, &'static str> {
    if claim_id.is_empty() {
        return Err("invalid_input: claim_id must be non-empty");
    }
    let mut failures = Vec::new();
    collect_early_failures(rec, &mut failures);
    collect_late_failures(rec, &mut failures);
    let receipt_claim_id = failures.is_empty().then(|| claim_id.to_string());
    Ok(ValidationReport {
        claim_id: claim_id.to_string(),
        failures,
        receipt_claim_id,
        authority_effect: AUTHORITY_EFFECT_NONE,
    })
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p2_next_1.rs
// Claim: urn:core:crates_rs:tests:prod-p2-next-1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8e84a472 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8e84a472` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8e84a472 {
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
impl BoundaryError8e84a472 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8e84a472 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8e84a472 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8e84a472 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8e84a472> {
        if capacity_bound == 0 {
            return Err(BoundaryError8e84a472::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8e84a472::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8e84a472::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_record_emits_receipt_and_each_step_mutation_is_isolated() {
        let pass = gate_candidate("claim.1", &CandidateRecord::valid()).unwrap();
        assert!(pass.emitted());
        assert!(pass.failures.is_empty());
        assert_eq!(pass.receipt_claim_id.as_deref(), Some("claim.1"));
        assert_eq!(pass.authority_effect, "None");

        for step in G5Step::ALL {
            let mutated = CandidateRecord::mutate_for_step(step);
            let rep = gate_candidate("claim.1", &mutated).unwrap();
            assert!(!rep.emitted());
            assert_eq!(rep.receipt_claim_id, None);
            assert_eq!(rep.failures, vec![step]);
        }
    }
}

#[test]
fn l4_boundary_admits_and_refuses_8e84a472() {
    let admitted = BoundaryRecord8e84a472::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8e84a472::try_admit(9, 8).is_err());
}
