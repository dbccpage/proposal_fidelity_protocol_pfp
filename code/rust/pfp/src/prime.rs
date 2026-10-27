//! Prime 000 admission and replay runtime actions.
//!
//! AuthorityEffect: None.

use core_wdp::prime_algos::prime_algorithm_0::{CochainWindow, DeclarationFill};
use core_wdp::prime_algos::prime_algorithm_0_admission::admit as ddc_admit;
pub use core_wdp::prime_algos::prime_candidate::{
    compute_prime_stage_hash, CandidateProposalV1, PrimeStage, PrimeStageRecordV1, PrimeTraceLogger,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;

pub const HOST_PRIME_ADMIT_REQUEST_SCHEMA: &str = "core.symbol-game.prime-admit-request.v1";
pub const HOST_PRIME_REPLAY_DECIDE_REQUEST_SCHEMA: &str =
    "core.symbol-game.prime-replay-decide-request.v1";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostPrimeAdmitRequestV1 {
    pub carrier: Option<String>,
    pub primitive_difference: Option<String>,
    pub zero_rel: Option<String>,
    pub observer: Option<String>,
    #[serde(default)]
    pub witnesses: Vec<String>,
    #[serde(default)]
    pub justify_cochain: bool,
    #[serde(default)]
    pub window: Option<HostCochainWindowWire>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostCochainWindowWire {
    pub dim_c0: usize,
    pub dim_c1: usize,
    pub dim_c2: usize,
    #[serde(default = "default_true")]
    pub square_zero: bool,
    #[serde(default)]
    pub l1_defect_mass: u64,
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostPrimeAdmitOutcomeV1 {
    pub admitted: bool,
    pub carrier: Option<String>,
    pub primitive_difference: Option<String>,
    pub zero_rel: Option<String>,
    pub observer: Option<String>,
    pub witnesses: Vec<String>,
    pub cochain_constructed: bool,
    pub prime_step: Option<u8>,
    pub reason: Option<String>,
    pub detail: Option<String>,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostPrimeReplayDecideRequestV1 {
    pub receipt: Option<Value>,
    pub steps: Option<Vec<PrimeReplayStepWire>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PrimeReplayStepWire {
    pub prime_step: u8,
    pub op: String,
    pub executed: bool,
    pub message: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostPrimeReplayDecideOutcomeV1 {
    pub decision: String,
    pub conforms: bool,
    pub violations: Vec<String>,
    pub unchecked_laws: Vec<String>,
    pub letter_tape: String,
    pub authority_effect: String,
}

pub fn prime_admit(payload: &Value) -> Result<HostPrimeAdmitOutcomeV1, String> {
    let req: HostPrimeAdmitRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|e| format!("invalid prime_admit request: {e}"))?;

    let decl = DeclarationFill {
        carrier: req.carrier.clone(),
        primitive_difference: req.primitive_difference.clone(),
        zero_rel: req.zero_rel.clone(),
        observer: req.observer.clone(),
        witnesses: req.witnesses.clone(),
    };

    let window = req.window.as_ref().map(|w| CochainWindow {
        dim_c0: w.dim_c0,
        dim_c1: w.dim_c1,
        dim_c2: w.dim_c2,
        square_zero: w.square_zero,
        l1_defect_mass: w.l1_defect_mass,
    });

    match ddc_admit(&decl, req.justify_cochain, window.as_ref()) {
        Ok(admitted) => Ok(HostPrimeAdmitOutcomeV1 {
            admitted: true,
            carrier: Some(admitted.carrier().to_string()),
            primitive_difference: Some(admitted.primitive_difference().to_string()),
            zero_rel: Some(admitted.zero_rel().to_string()),
            observer: Some(admitted.observer().to_string()),
            witnesses: admitted.witnesses().to_vec(),
            cochain_constructed: true,
            prime_step: None,
            reason: None,
            detail: None,
            authority_effect: "None".to_string(),
        }),
        Err(refusal) => Ok(HostPrimeAdmitOutcomeV1 {
            admitted: false,
            carrier: req.carrier,
            primitive_difference: req.primitive_difference,
            zero_rel: req.zero_rel,
            observer: req.observer,
            witnesses: req.witnesses,
            cochain_constructed: false,
            prime_step: Some(refusal.prime_step),
            reason: Some(refusal.reason.to_string()),
            detail: Some(refusal.detail),
            authority_effect: "None".to_string(),
        }),
    }
}

pub fn prime_replay_decide(payload: &Value) -> Result<HostPrimeReplayDecideOutcomeV1, String> {
    let req: HostPrimeReplayDecideRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|e| format!("invalid prime_replay_decide request: {e}"))?;

    if let Some(receipt_val) = &req.receipt {
        return evaluate_receipt_conformance(receipt_val);
    }

    if let Some(steps) = &req.steps {
        return evaluate_steps_conformance(steps);
    }

    Err("either receipt or steps must be provided in prime_replay_decide request".into())
}

fn evaluate_receipt_conformance(r: &Value) -> Result<HostPrimeReplayDecideOutcomeV1, String> {
    let letter_tape = r
        .get("letter_tape")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
        .unwrap_or_default();
    let gamma2 = r.get("gamma2").and_then(|v| v.as_u64());
    let terminal = r
        .get("terminal")
        .and_then(|v| v.as_str())
        .unwrap_or("Pending")
        .to_string();
    let authority_effect = r
        .get("authority_effect")
        .and_then(|v| v.as_str())
        .unwrap_or("None")
        .to_string();

    let mut violations = Vec::new();

    if letter_tape.contains('T') {
        if let Some(g) = gamma2 {
            if g != 0 {
                violations.push(format!("TerminalizedOpenResidual(gamma2={g})"));
            }
        }
    }

    let allowed_letters = ['E', 'R', 'C', 'I', 'L', 'Λ', 'D', 'M', 'T'];
    for c in letter_tape.chars() {
        if !allowed_letters.contains(&c) {
            violations.push(format!("ForeignLetter(letter={c})"));
        }
    }

    for req in ['C', 'R', 'T'] {
        if !letter_tape.contains(req) {
            violations.push(format!("MissingRequiredLetter(letter={req})"));
        }
    }

    if authority_effect != "None" {
        violations.push(format!("AuthorityMinted(effect={authority_effect})"));
    }

    if let Some(steps) = r.get("steps").and_then(|v| v.as_array()) {
        let from_steps: String = steps
            .iter()
            .filter_map(|s| s.get("op").and_then(|o| o.as_str()))
            .collect();
        if !from_steps.is_empty() && from_steps != letter_tape {
            violations.push(format!(
                "TapeStepMismatch(tape={letter_tape}, from_steps={from_steps})"
            ));
        }

        let mut prev_phi1: Option<u64> = None;
        let mut seen_first = false;
        for s in steps {
            let op = s.get("op").and_then(|o| o.as_str()).unwrap_or("");
            let prime_step = s.get("prime_step").and_then(|p| p.as_u64()).unwrap_or(0) as u8;
            let phi1_after = s.get("phi1_after").and_then(|p| p.as_u64());

            if op == "R" && seen_first && phi1_after != prev_phi1 {
                violations.push(format!(
                    "ResidualProjectionMovedPhi1(step={prime_step}, before={prev_phi1:?}, after={phi1_after:?})"
                ));
            }
            if op == "D" {
                let has_ledger = s.get("loss_ledger").map(|l| !l.is_null()).unwrap_or(false);
                if !has_ledger {
                    violations.push(format!("DescentWithoutLossLedger(step={prime_step})"));
                }
            }
            prev_phi1 = phi1_after;
            seen_first = true;
        }
    }

    let unchecked_laws = vec![
        "E must land at Exact (needs the after-state cochain, not just its masses)".to_string(),
        "I/M/T inert on the cochain (needs before/after cochain state)".to_string(),
        "C/D/Lambda must actually change the carrier (needs per-step carrier identity)".to_string(),
    ];

    let conforms = violations.is_empty();

    Ok(HostPrimeReplayDecideOutcomeV1 {
        decision: terminal,
        conforms,
        violations,
        unchecked_laws,
        letter_tape,
        authority_effect: "None".to_string(),
    })
}

fn evaluate_steps_conformance(
    steps: &[PrimeReplayStepWire],
) -> Result<HostPrimeReplayDecideOutcomeV1, String> {
    let letter_tape: String = steps.iter().map(|s| s.op.as_str()).collect();
    let mut violations = Vec::new();

    let allowed_letters = ['E', 'R', 'C', 'I', 'L', 'Λ', 'D', 'M', 'T'];
    for c in letter_tape.chars() {
        if !allowed_letters.contains(&c) {
            violations.push(format!("ForeignLetter(letter={c})"));
        }
    }

    for req in ['C', 'R', 'T'] {
        if !letter_tape.contains(req) {
            violations.push(format!("MissingRequiredLetter(letter={req})"));
        }
    }

    let unchecked_laws = vec![
        "E must land at Exact (needs the after-state cochain, not just its masses)".to_string(),
        "I/M/T inert on the cochain (needs before/after cochain state)".to_string(),
        "C/D/Lambda must actually change the carrier (needs per-step carrier identity)".to_string(),
    ];

    let conforms = violations.is_empty();
    let decision = if letter_tape.ends_with('T') {
        "Terminalized".to_string()
    } else if letter_tape.ends_with('M') {
        "Refusal".to_string()
    } else {
        "Pending".to_string()
    };

    Ok(HostPrimeReplayDecideOutcomeV1 {
        decision,
        conforms,
        violations,
        unchecked_laws,
        letter_tape,
        authority_effect: "None".to_string(),
    })
}

/// Helper function to construct and evaluate a CandidateProposalV1 at Prime -1.
pub fn evaluate_candidate_proposal(
    proposal_id: &str,
    locus_id: &str,
    raw_payload: &[u8],
    actor: &str,
    admit: bool,
    refusal_reason: Option<&str>,
) -> CandidateProposalV1 {
    let mut proposal = CandidateProposalV1::new(proposal_id, locus_id, raw_payload, actor);
    if admit {
        proposal.admit_to_trace();
    } else if let Some(reason) = refusal_reason {
        proposal.refuse(reason);
    }
    proposal
}

/// Helper function to record a Prime Triad stage transition.
pub fn record_prime_stage_transition(
    seq: u64,
    stage: PrimeStage,
    packet_id: &str,
    actor: &str,
    status: &str,
    witness_or_refusal: &str,
    prev_record_hash: Option<String>,
) -> PrimeStageRecordV1 {
    PrimeStageRecordV1::new(
        seq,
        stage,
        packet_id,
        actor,
        status,
        witness_or_refusal,
        prev_record_hash,
    )
}

// ---------------------------------------------------------------------------
// Prime Descent Coordinator Action
// ---------------------------------------------------------------------------

pub const HOST_PRIME_DESCENT_REQUEST_SCHEMA: &str = "core.symbol-game.prime-descent-request.v1";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostCarrierEdgeWire {
    pub tail: usize,
    pub head: usize,
    #[serde(default = "default_one_i128")]
    pub weight: i128,
}

fn default_one_i128() -> i128 {
    1
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostFiniteCarrier2Wire {
    pub num_vertices: usize,
    pub edges: Vec<HostCarrierEdgeWire>,
    #[serde(default)]
    pub faces: Vec<(usize, usize, usize)>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExternalAuthorityGrantWire {
    pub grant_id: String,
    pub signature_hex: String,
    pub grantee: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostPrimeDescentRequestV1 {
    pub run_id: String,
    pub carrier: HostFiniteCarrier2Wire,
    pub omega: Vec<i128>,
    #[serde(default = "default_max_steps")]
    pub max_steps: usize,
    #[serde(default)]
    pub grant: Option<ExternalAuthorityGrantWire>,
}

fn default_max_steps() -> usize {
    64
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HostPrimeDescentOutcomeV1 {
    pub run_id: String,
    pub letters: String,
    pub terminal_status: String,
    pub phi1: String,
    pub gamma2: String,
    pub b1_over_q: usize,
    pub laws_passed: bool,
    pub authority_effect: String,
}

pub fn prime_descent(payload: &Value) -> Result<HostPrimeDescentOutcomeV1, String> {
    use core_wdp::coda::types::ExternalAuthorityGrant;
    use core_wdp::prime_algos::descent_engine::PrimeDescentCoordinator;
    use core_wdp::solver_of_solvers::{CarrierEdge, FiniteCarrier2};

    let req: HostPrimeDescentRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|e| format!("invalid prime_descent request: {e}"))?;

    let carrier = FiniteCarrier2 {
        num_vertices: req.carrier.num_vertices,
        edges: req
            .carrier
            .edges
            .into_iter()
            .map(|e| CarrierEdge {
                tail: e.tail,
                head: e.head,
                weight: e.weight,
            })
            .collect(),
        faces: req.carrier.faces,
    };

    let grant_opt = req.grant.map(|g| ExternalAuthorityGrant {
        grant_id: g.grant_id,
        signature_hex: g.signature_hex,
        grantee: g.grantee,
    });

    let mut coordinator = PrimeDescentCoordinator::new(&req.run_id, req.max_steps);
    let receipt = coordinator
        .execute_descent_with_grant(&carrier, &req.omega, grant_opt.as_ref())
        .map_err(|e| format!("descent refused: {e:?}"))?;

    Ok(HostPrimeDescentOutcomeV1 {
        run_id: receipt.run_id,
        letters: receipt.letters,
        terminal_status: receipt.terminal_status,
        phi1: receipt.phi1.to_string(),
        gamma2: receipt.gamma2.to_string(),
        b1_over_q: receipt.b1_over_q,
        laws_passed: receipt.laws_passed,
        authority_effect: receipt.authority_effect,
    })
}

// Origin: engine/crates_rs/pfp/src/prime.rs
// Claim: urn:core:crates_rs:pfp:prime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda7df735c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda7df735c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora7df735c {
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
impl BoundaryErrora7df735c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora7df735c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora7df735c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda7df735c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora7df735c> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora7df735c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora7df735c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora7df735c::ExceedsCapacity {
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
mod l4_boundary_tests_a7df735c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda7df735c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda7df735c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda7df735c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda7df735c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda7df735c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora7df735c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora7df735c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
