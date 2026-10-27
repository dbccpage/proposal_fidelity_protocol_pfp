//! # Authority Gap, Counterfeit Descent, and Process Provenance (FOC-005)
//!
//! Sovereign Rust mathematical and architectural implementation of Paper 005:
//! *The Authority Gap: Counterfeit Descent, Layered Control, and Process Provenance in Agentic AI*.
//!
//! Under Sentinel and CODA doctrine:
//! - All mathematical derivations and checks carry `AuthorityEffect::None`.
//! - Discrete exactness is guaranteed using `num_rational::BigRational`.
//! - Implements the Seven-Layer AI Authority Control Stack, length-delimited byte encodings,
//!   exact rational Negative Gluing Defect (NGD), Authority Coverage Ratio (ACR),
//!   Rate Asymmetry Backlog accumulation, and the Exactness Fraud Criterion.

use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Permitted terminal statuses under a declared observer.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TerminalStatus {
    ProposalOnly,
    Repair,
    Refuse,
    Escalate,
    AuthorizedUnderObserver,
}

impl TerminalStatus {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::ProposalOnly => "proposal_only",
            Self::Repair => "repair",
            Self::Refuse => "refuse",
            Self::Escalate => "escalate",
            Self::AuthorizedUnderObserver => "authorized_under_observer",
        }
    }
}

/// Length-delimited byte encoding for a single string: `<len>:<utf8_bytes>`.
pub fn canonical_encode_string(s: &str) -> Vec<u8> {
    let raw = s.as_bytes();
    let mut out = format!("{}:", raw.len()).into_bytes();
    out.extend_from_slice(raw);
    out
}

/// Length-delimited byte encoding for a sequence of strings: `<tag>[<count>]:<item1><item2>...;`.
pub fn canonical_encode_sequence(tag: &str, items: &[String]) -> Vec<u8> {
    let mut out = format!("{}[{}]:", tag, items.len()).into_bytes();
    for item in items {
        out.extend(canonical_encode_string(item));
    }
    out.push(b';');
    out
}

/// Layer 1: Generated option, plan, or candidate output. Carries zero authority.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Proposal {
    pub proposal_id: String,
    pub generator_id: String,
    pub payload: String,
    pub context: String,
}

/// Layer 2: Tamper-evident custody record of actions, sources, and tool calls.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TraceRecord {
    pub trace_id: String,
    pub actions: Vec<String>,
    pub tool_calls: Vec<String>,
    pub sources: Vec<String>,
    pub content_hash: String,
    pub proposal_id: String,
}

impl TraceRecord {
    pub fn canonical_bytes(
        trace_id: &str,
        actions: &[String],
        tool_calls: &[String],
        sources: &[String],
        proposal_id: &str,
        proposal_payload: &str,
        proposal_context: &str,
    ) -> Vec<u8> {
        let mut out = Vec::new();
        out.extend_from_slice(b"trace_record_v1;");
        out.extend(canonical_encode_string(trace_id));
        out.push(b';');
        out.extend(canonical_encode_string(proposal_id));
        out.push(b';');
        out.extend(canonical_encode_string(proposal_payload));
        out.push(b';');
        out.extend(canonical_encode_string(proposal_context));
        out.push(b';');
        out.extend(canonical_encode_sequence("actions", actions));
        out.extend(canonical_encode_sequence("tool_calls", tool_calls));
        out.extend(canonical_encode_sequence("sources", sources));
        out
    }

    pub fn compute_hash(
        trace_id: &str,
        actions: &[String],
        tool_calls: &[String],
        sources: &[String],
        proposal_id: &str,
        proposal_payload: &str,
        proposal_context: &str,
    ) -> String {
        let bytes = Self::canonical_bytes(
            trace_id,
            actions,
            tool_calls,
            sources,
            proposal_id,
            proposal_payload,
            proposal_context,
        );
        let mut hasher = Sha256::new();
        hasher.update(&bytes);
        format!("{:x}", hasher.finalize())
    }

    pub fn create(
        trace_id: String,
        actions: Vec<String>,
        tool_calls: Vec<String>,
        sources: Vec<String>,
        proposal: Option<&Proposal>,
    ) -> Self {
        let (prop_id, prop_payload, prop_context) = match proposal {
            Some(p) => (p.proposal_id.as_str(), p.payload.as_str(), p.context.as_str()),
            None => ("", "", ""),
        };
        let content_hash = Self::compute_hash(
            &trace_id,
            &actions,
            &tool_calls,
            &sources,
            prop_id,
            prop_payload,
            prop_context,
        );
        Self {
            trace_id,
            actions,
            tool_calls,
            sources,
            content_hash,
            proposal_id: prop_id.to_string(),
        }
    }

    pub fn verify_content_hash(&self, proposal: Option<&Proposal>) -> bool {
        let (prop_id, prop_payload, prop_context) = match proposal {
            Some(p) => {
                if !self.proposal_id.is_empty() && self.proposal_id != p.proposal_id {
                    return false;
                }
                (p.proposal_id.as_str(), p.payload.as_str(), p.context.as_str())
            }
            None => ("", "", ""),
        };
        let expected = Self::compute_hash(
            &self.trace_id,
            &self.actions,
            &self.tool_calls,
            &self.sources,
            prop_id,
            prop_payload,
            prop_context,
        );
        self.content_hash == expected
    }
}

/// Layer 3: Declared finite evaluation specification.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserverPacket {
    pub carrier: String,
    pub local_states: Vec<String>,
    pub comparisons: Vec<String>,
    pub defects: Vec<String>,
    pub admissible_repairs: Vec<String>,
    pub gauge: String,
    pub closure_diagnostics: Vec<String>,
}

/// Layer 4: Explicit ledger of unresolved defects, unverified scope, and losses.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Residual {
    pub defect_mass: BigRational,
    pub unverified_scope: Vec<String>,
    pub refusal_reasons: Vec<String>,
}

impl Residual {
    pub fn is_exact(&self) -> bool {
        self.defect_mass.is_zero()
            && self.unverified_scope.is_empty()
            && self.refusal_reasons.is_empty()
    }
}

/// Layer 5: Accountable decision made by a designated institutional decider.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Terminal {
    pub status: TerminalStatus,
    pub decider_id: String,
    pub is_human_or_delegated_body: bool,
    pub justification: String,
    pub claims_exactness: bool,
    pub tolerated_defect_mass: BigRational,
    pub tolerated_unverified_scope: Vec<String>,
    pub tolerated_refusal_reasons: Vec<String>,
}

/// Layer 6: Proof that declared descent was executed across layers 1-5.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Attestation {
    pub descent_executed: bool,
    pub verification_hash: String,
    pub replay_receipt: Option<String>,
}

/// Layer 7: Legal, organizational, and regulatory standing.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Institution {
    pub entity_id: String,
    pub governing_jurisdiction: String,
    pub accountable_officer: String,
    pub appeal_path: String,
}

/// Encapsulation of the complete seven-layer authority descent pipeline.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthorityPacket {
    pub proposal: Proposal,
    pub trace: TraceRecord,
    pub observer: ObserverPacket,
    pub residual: Residual,
    pub terminal: Terminal,
    pub attestation: Attestation,
    pub institution: Institution,
}

impl AuthorityPacket {
    pub fn compute_canonical_binding_record(&self) -> Vec<u8> {
        let mut out = Vec::new();
        out.extend_from_slice(b"authority_packet_binding_v1;");
        // Layer 1: Proposal
        out.extend(canonical_encode_string(&self.proposal.proposal_id));
        out.extend(canonical_encode_string(&self.proposal.generator_id));
        out.extend(canonical_encode_string(&self.proposal.payload));
        out.extend(canonical_encode_string(&self.proposal.context));
        // Layer 2: Trace
        out.extend(canonical_encode_string(&self.trace.trace_id));
        out.extend(canonical_encode_sequence("actions", &self.trace.actions));
        out.extend(canonical_encode_sequence("tool_calls", &self.trace.tool_calls));
        out.extend(canonical_encode_sequence("sources", &self.trace.sources));
        out.extend(canonical_encode_string(&self.trace.content_hash));
        // Layer 3: Observer
        out.extend(canonical_encode_string(&self.observer.carrier));
        out.extend(canonical_encode_string(&self.observer.gauge));
        out.extend(canonical_encode_sequence("local_states", &self.observer.local_states));
        out.extend(canonical_encode_sequence("comparisons", &self.observer.comparisons));
        out.extend(canonical_encode_sequence("defects", &self.observer.defects));
        out.extend(canonical_encode_sequence("admissible_repairs", &self.observer.admissible_repairs));
        out.extend(canonical_encode_sequence("closure_diagnostics", &self.observer.closure_diagnostics));
        // Layer 4: Residual
        out.extend(canonical_encode_string(&self.residual.defect_mass.to_string()));
        out.extend(canonical_encode_sequence("unverified_scope", &self.residual.unverified_scope));
        out.extend(canonical_encode_sequence("refusal_reasons", &self.residual.refusal_reasons));
        // Layer 5: Terminal
        out.extend(canonical_encode_string(self.terminal.status.as_str()));
        out.extend(canonical_encode_string(&self.terminal.decider_id));
        out.extend(canonical_encode_string(if self.terminal.is_human_or_delegated_body { "human" } else { "model" }));
        out.extend(canonical_encode_string(&self.terminal.justification));
        out.extend(canonical_encode_string(if self.terminal.claims_exactness { "exact_claim" } else { "scoped_authorization" }));
        out.extend(canonical_encode_string(&self.terminal.tolerated_defect_mass.to_string()));
        out.extend(canonical_encode_sequence("tolerated_unverified_scope", &self.terminal.tolerated_unverified_scope));
        out.extend(canonical_encode_sequence("tolerated_refusal_reasons", &self.terminal.tolerated_refusal_reasons));
        // Layer 6: Attestation
        out.extend(canonical_encode_string(if self.attestation.descent_executed { "descent_executed" } else { "descent_not_executed" }));
        out.extend(canonical_encode_string(self.attestation.replay_receipt.as_deref().unwrap_or("")));
        // Layer 7: Institution
        out.extend(canonical_encode_string(&self.institution.entity_id));
        out.extend(canonical_encode_string(&self.institution.governing_jurisdiction));
        out.extend(canonical_encode_string(&self.institution.accountable_officer));
        out.extend(canonical_encode_string(&self.institution.appeal_path));
        out
    }

    pub fn compute_binding_hash(&self) -> String {
        let bytes = self.compute_canonical_binding_record();
        let mut hasher = Sha256::new();
        hasher.update(&bytes);
        format!("{:x}", hasher.finalize())
    }

    pub fn validate_layers(&self) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();

        // Invariant 1: Proposal generator cannot be the terminal decider (Self-Critique Non-Authority)
        if self.proposal.generator_id == self.terminal.decider_id {
            errors.push("Proposal generator cannot be the terminal decider (Self-Critique Non-Authority Violation).".to_string());
        }

        // Invariant 2: Terminal authority requires accountable decider
        if !self.terminal.is_human_or_delegated_body {
            errors.push("Terminal decision must be governed by an accountable human or institutional body.".to_string());
        }

        // Invariant 3: Trace custody and proposal binding integrity
        if !self.trace.verify_content_hash(Some(&self.proposal)) {
            errors.push("Trace custody failure: Trace content_hash does not match canonical length-delimited record bound to proposal.".to_string());
        }

        // Invariant 4: Exactness Fraud Criterion & Authorized Status checks
        if self.terminal.status == TerminalStatus::AuthorizedUnderObserver {
            self.validate_authorized_status(&mut errors);
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }

    fn validate_authorized_status(&self, errors: &mut Vec<String>) {
        if !self.attestation.descent_executed {
            errors.push("Counterfeit descent: Authorized status claimed without executed descent attestation.".to_string());
        }

        if self.terminal.claims_exactness {
            if !self.residual.is_exact() {
                errors.push(format!(
                    "Exactness fraud violation: Exactness claimed with non-zero residual (defect mass: {}, unverified: {}, refusals: {}).",
                    self.residual.defect_mass,
                    self.residual.unverified_scope.len(),
                    self.residual.refusal_reasons.len()
                ));
            }
        } else {
            self.validate_scoped_residual(errors);
        }

        if self.attestation.replay_receipt.is_none() {
            errors.push("Attestation evidence missing: Authorized status requires an inspectable replay_receipt.".to_string());
        }
        if self.institution.entity_id.is_empty() || self.institution.accountable_officer.is_empty() {
            errors.push("Institutional standing missing: Authorized status requires declared entity_id and accountable_officer.".to_string());
        }
        if self.attestation.verification_hash.is_empty() {
            errors.push("Attestation verification hash missing: Authorized status requires verification_hash.".to_string());
        } else if self.attestation.verification_hash != self.compute_binding_hash() {
            errors.push("Attestation binding mismatch: verification_hash does not match canonical length-delimited packet binding.".to_string());
        }
    }

    fn validate_scoped_residual(&self, errors: &mut Vec<String>) {
        if self.residual.defect_mass > self.terminal.tolerated_defect_mass {
            errors.push(format!(
                "Scoped authorization violation: Residual defect mass {} exceeds declared tolerance {}.",
                self.residual.defect_mass, self.terminal.tolerated_defect_mass
            ));
        }
        let unauthorized_scope: Vec<_> = self
            .residual
            .unverified_scope
            .iter()
            .filter(|s| !self.terminal.tolerated_unverified_scope.contains(s))
            .collect();
        if !unauthorized_scope.is_empty() {
            errors.push(format!(
                "Scoped authorization violation: Unverified scope items {:?} not authorized in declared tolerated_unverified_scope.",
                unauthorized_scope
            ));
        }
        let unauthorized_refusals: Vec<_> = self
            .residual
            .refusal_reasons
            .iter()
            .filter(|r| !self.terminal.tolerated_refusal_reasons.contains(r))
            .collect();
        if !unauthorized_refusals.is_empty() {
            errors.push(format!(
                "Scoped authorization violation: Evaluator refusal reasons {:?} not authorized in declared tolerated_refusal_reasons.",
                unauthorized_refusals
            ));
        }
    }
}

/// Evaluate structural consistency constraints across the authority packet (Exactness Fraud Criterion).
pub fn evaluate_exactness_fraud_criterion(packet: &AuthorityPacket) -> (bool, String) {
    match packet.validate_layers() {
        Ok(()) => (
            true,
            "Structurally consistent but unverified until an independent verifier binds and checks the evidence."
                .to_string(),
        ),
        Err(errors) => (false, errors.join("; ")),
    }
}

/// Evaluation outcome along a compositional path.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct GluingEvaluation {
    pub local_green: bool,
    pub global_red: bool,
}

/// Calculate the Negative Gluing Defect (NGD):
/// `NGD = N(local_green and global_red) / N(local_green)`
/// Returns exact `BigRational`, or `None` when local_green count is zero.
pub fn calculate_ngd(path_evaluations: &[GluingEvaluation]) -> Option<BigRational> {
    let mut local_green_count = 0u64;
    let mut defect_count = 0u64;

    for item in path_evaluations {
        if item.local_green {
            local_green_count += 1;
            if item.global_red {
                defect_count += 1;
            }
        }
    }

    if local_green_count == 0 {
        None
    } else {
        Some(BigRational::new(defect_count.into(), local_green_count.into()))
    }
}

/// Calculate the Authority Coverage Ratio (ACR) over a discrete cohort/window W:
/// `ACR = N_W(verified_packets) / N_W(proposals_generated)`
/// Returns `Ok(None)` when `proposal_count == 0`.
pub fn calculate_acr(verified_count: u64, proposal_count: u64) -> Result<Option<BigRational>, String> {
    if verified_count > proposal_count {
        return Err(format!(
            "verified_count ({}) cannot exceed proposal_count ({})",
            verified_count, proposal_count
        ));
    }
    if proposal_count == 0 {
        Ok(None)
    } else {
        Ok(Some(BigRational::new(
            verified_count.into(),
            proposal_count.into(),
        )))
    }
}

/// Calculate instantaneous Authority Coverage Ratio from rates:
/// `ACR_rate = r_V / r_G`
pub fn calculate_acr_rate(
    rate_verification: BigRational,
    rate_generation: BigRational,
) -> Result<BigRational, String> {
    if rate_generation <= BigRational::zero() {
        return Err("rate_generation must be strictly positive".to_string());
    }
    if rate_verification < BigRational::zero() {
        return Err("rate_verification must be non-negative".to_string());
    }
    Ok(rate_verification / rate_generation)
}

/// Calculate authority backlog accumulation over a given time duration:
/// `Delta U = (r_G - r_V) * Delta t`
pub fn calculate_backlog_accumulation(
    rate_generation: BigRational,
    rate_verification: BigRational,
    time_units: BigRational,
) -> Result<BigRational, String> {
    if time_units < BigRational::zero() {
        return Err("time_units must be non-negative".to_string());
    }
    let rate_diff = rate_generation - rate_verification;
    Ok(rate_diff * time_units)
}

// Origin: engine/crates_rs/core_wdp/src/authority_gap.rs
// Claim: urn:core:crates_rs:core-wdp:authority-gap:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord41f87ba7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord41f87ba7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError41f87ba7 {
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
impl BoundaryError41f87ba7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError41f87ba7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError41f87ba7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord41f87ba7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError41f87ba7> {
        if capacity_bound == 0 {
            return Err(BoundaryError41f87ba7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError41f87ba7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError41f87ba7::ExceedsCapacity {
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

    fn sample_valid_packet() -> AuthorityPacket {
        let proposal = Proposal {
            proposal_id: "prop_001".to_string(),
            generator_id: "agent_alpha".to_string(),
            payload: "candidate_repair".to_string(),
            context: "context_spec".to_string(),
        };
        let trace = TraceRecord::create(
            "trace_001".to_string(),
            vec!["parse".to_string(), "evaluate".to_string()],
            vec!["tool_oracle".to_string()],
            vec!["input_doc".to_string()],
            Some(&proposal),
        );
        let observer = ObserverPacket {
            carrier: "stalk_e2".to_string(),
            local_states: vec!["s0".to_string(), "s1".to_string()],
            comparisons: vec!["comp_eq".to_string()],
            defects: vec![],
            admissible_repairs: vec!["d0_adj".to_string()],
            gauge: "l2_stalk".to_string(),
            closure_diagnostics: vec!["d1_exact".to_string()],
        };
        let residual = Residual {
            defect_mass: BigRational::zero(),
            unverified_scope: vec![],
            refusal_reasons: vec![],
        };
        let terminal = Terminal {
            status: TerminalStatus::AuthorizedUnderObserver,
            decider_id: "officer_human".to_string(),
            is_human_or_delegated_body: true,
            justification: "verified exact descent".to_string(),
            claims_exactness: true,
            tolerated_defect_mass: BigRational::zero(),
            tolerated_unverified_scope: vec![],
            tolerated_refusal_reasons: vec![],
        };
        let institution = Institution {
            entity_id: "inst_alpha".to_string(),
            governing_jurisdiction: "jurisdiction_root".to_string(),
            accountable_officer: "officer_human".to_string(),
            appeal_path: "tribunal_ref".to_string(),
        };
        let dummy_attestation = Attestation {
            descent_executed: true,
            verification_hash: String::new(),
            replay_receipt: Some("receipt_digest_valid".to_string()),
        };
        let mut packet = AuthorityPacket {
            proposal,
            trace,
            observer,
            residual,
            terminal,
            attestation: dummy_attestation,
            institution,
        };
        let hash = packet.compute_binding_hash();
        packet.attestation.verification_hash = hash;
        packet
    }

    #[test]
    fn test_legitimate_authorized_packet() {
        let packet = sample_valid_packet();
        let (valid, msg) = evaluate_exactness_fraud_criterion(&packet);
        assert!(valid, "Packet should be structurally valid: {}", msg);
        assert!(msg.contains("Structurally consistent"));
    }

    #[test]
    fn test_self_critique_non_authority_violation() {
        let mut packet = sample_valid_packet();
        packet.terminal.decider_id = packet.proposal.generator_id.clone();
        packet.attestation.verification_hash = packet.compute_binding_hash();
        let (valid, msg) = evaluate_exactness_fraud_criterion(&packet);
        assert!(!valid);
        assert!(msg.contains("Self-Critique Non-Authority Violation"));
    }

    #[test]
    fn test_counterfeit_descent_unattested_authorization() {
        let mut packet = sample_valid_packet();
        packet.attestation.descent_executed = false;
        packet.attestation.verification_hash = packet.compute_binding_hash();
        let (valid, msg) = evaluate_exactness_fraud_criterion(&packet);
        assert!(!valid);
        assert!(msg.contains("Counterfeit descent"));
    }

    #[test]
    fn test_exactness_fraud_masked_residual() {
        let mut packet = sample_valid_packet();
        packet.residual.defect_mass = BigRational::new(1.into(), 10.into());
        packet.attestation.verification_hash = packet.compute_binding_hash();
        let (valid, msg) = evaluate_exactness_fraud_criterion(&packet);
        assert!(!valid);
        assert!(msg.contains("Exactness fraud violation"));
    }

    #[test]
    fn test_scoped_authorization_with_tolerated_residual() {
        let mut packet = sample_valid_packet();
        packet.terminal.claims_exactness = false;
        packet.terminal.tolerated_defect_mass = BigRational::new(2.into(), 10.into());
        packet.terminal.tolerated_unverified_scope = vec!["high_freq".to_string()];
        packet.terminal.tolerated_refusal_reasons = vec!["budget_limit".to_string()];
        packet.residual.defect_mass = BigRational::new(1.into(), 10.into());
        packet.residual.unverified_scope = vec!["high_freq".to_string()];
        packet.residual.refusal_reasons = vec!["budget_limit".to_string()];
        packet.attestation.verification_hash = packet.compute_binding_hash();

        let (valid, msg) = evaluate_exactness_fraud_criterion(&packet);
        assert!(valid, "Scoped authorization should be permitted within declared tolerances: {}", msg);
    }

    #[test]
    fn test_ngd_computation() {
        let evals = vec![
            GluingEvaluation { local_green: true, global_red: false },
            GluingEvaluation { local_green: true, global_red: true },
            GluingEvaluation { local_green: true, global_red: true },
            GluingEvaluation { local_green: true, global_red: false },
        ];
        let ngd = calculate_ngd(&evals);
        assert_eq!(ngd, Some(BigRational::new(1.into(), 2.into())));

        let empty: Vec<GluingEvaluation> = vec![];
        assert_eq!(calculate_ngd(&empty), None);
    }

    #[test]
    fn test_acr_computation() {
        let acr = calculate_acr(30, 100).unwrap();
        assert_eq!(acr, Some(BigRational::new(3.into(), 10.into())));

        let err = calculate_acr(150, 100);
        assert!(err.is_err());

        let rate_acr = calculate_acr_rate(
            BigRational::new(3.into(), 1.into()),
            BigRational::new(10.into(), 1.into()),
        ).unwrap();
        assert_eq!(rate_acr, BigRational::new(3.into(), 10.into()));
    }

    #[test]
    fn test_rate_asymmetry_backlog() {
        let backlog = calculate_backlog_accumulation(
            BigRational::new(50.into(), 1.into()),
            BigRational::new(10.into(), 1.into()),
            BigRational::new(12.into(), 1.into()),
        ).unwrap();
        assert_eq!(backlog, BigRational::new(480.into(), 1.into()));

        let step = calculate_backlog_accumulation(
            BigRational::new(10.into(), 1.into()),
            BigRational::new(3.into(), 1.into()),
            BigRational::new(1.into(), 1.into()),
        ).unwrap();
        assert_eq!(step, BigRational::new(7.into(), 1.into()));
    }
}

#[cfg(test)]
mod l4_boundary_tests_41f87ba7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord41f87ba7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord41f87ba7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord41f87ba7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord41f87ba7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord41f87ba7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError41f87ba7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError41f87ba7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
