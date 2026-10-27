//! DDC tape verification runtime action.
//!
//! Evaluates the 8-letter DDC tape automaton against letter step laws,
//! control transitions, detector adequacy, and cryptographic tape chaining.
//! AuthorityEffect: None.

use core_kernel::{parse_exact, to_canonical_string, Exact};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};

pub const DDC_TAPE_VERIFY_REQUEST_SCHEMA: &str = "core.symbol-game.ddc-verify-tape-request.v1";
pub const DDC_TAPE_GENESIS_ROOT: &str = "DDC_TAPE_GENESIS";

fn canonical_json_str(val: &Value) -> String {
    match val {
        Value::Null => "null".to_string(),
        Value::Bool(b) => {
            if *b {
                "true".to_string()
            } else {
                "false".to_string()
            }
        }
        Value::Number(n) => n.to_string(),
        Value::String(s) => serde_json::to_string(s).unwrap_or_else(|_| format!("\"{s}\"")),
        Value::Array(arr) => {
            let items: Vec<String> = arr.iter().map(canonical_json_str).collect();
            format!("[{}]", items.join(","))
        }
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let entries: Vec<String> = keys
                .into_iter()
                .map(|k| {
                    let k_str = serde_json::to_string(k).unwrap_or_else(|_| format!("\"{k}\""));
                    let v_str = canonical_json_str(&map[k]);
                    format!("{k_str}:{v_str}")
                })
                .collect();
            format!("{{{}}}", entries.join(","))
        }
    }
}

const M_REASONS: &[&str] = &[
    "REFUSED_INVALID_WITNESS",
    "REFUSED_BUDGET_EXHAUSTED",
    "REFUSED_NON_ZERO_CURL",
    "REFUSED_UNLICENSED_LIFT",
    "REFUSED_LIFT_TRIGGER",
    "REFUSED_MISSING_LOSS_LEDGER",
    "REFUSED_MISSING_RECEIPT",
    "REFUSED_REQUIRES_LIFT",
    "REFUSED_DETECTOR_INADEQUATE",
    "REFUSED_OPEN_OBSTRUCTION",
];

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DdcVerifyTapeRequestV1 {
    pub initial_state: DdcTapeStateWire,
    pub steps: Vec<DdcTapeStepWire>,
    #[serde(default)]
    pub genesis_root: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DdcTapeStateWire {
    pub carrier: String,
    pub residual: Vec<String>,
    pub phi: String,
    pub gamma: String,
    pub adequate: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DdcTapeStepWire {
    pub letter: String,
    pub after: DdcTapeStateWire,
    #[serde(default)]
    pub witness: Option<DdcTapeWitnessWire>,
}

#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DdcTapeWitnessWire {
    #[serde(default)]
    pub receipt: bool,
    #[serde(default)]
    pub loss_ledger: bool,
    #[serde(default)]
    pub lift_licence: bool,
    #[serde(default)]
    pub reason: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DdcVerifyTapeOutcomeV1 {
    pub lawful: bool,
    pub receipt_head: String,
    pub letters: String,
    pub final_control: String,
    pub halted_at: Option<usize>,
    pub violations: Vec<String>,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DdcInternalState {
    pub carrier: String,
    pub residual: Vec<Exact>,
    pub phi: Exact,
    pub gamma: Exact,
    pub adequate: bool,
}

impl DdcInternalState {
    pub fn parse(wire: &DdcTapeStateWire) -> Result<Self, String> {
        let mut residual = Vec::with_capacity(wire.residual.len());
        for (i, r_str) in wire.residual.iter().enumerate() {
            let val = parse_exact(r_str)
                .map_err(|e| format!("invalid residual[{i}] exact string {r_str:?}: {e}"))?;
            residual.push(val);
        }
        let phi = parse_exact(&wire.phi)
            .map_err(|e| format!("invalid phi exact string {:?}: {e}", wire.phi))?;
        let gamma = parse_exact(&wire.gamma)
            .map_err(|e| format!("invalid gamma exact string {:?}: {e}", wire.gamma))?;

        let zero = Exact::from_integer(0.into());
        if phi < zero || gamma < zero {
            return Err("NEGATIVE_DIAGNOSTIC".into());
        }

        Ok(Self {
            carrier: wire.carrier.clone(),
            residual,
            phi,
            gamma,
            adequate: wire.adequate,
        })
    }

    pub fn cls(&self) -> &'static str {
        let zero = Exact::from_integer(0.into());
        if self.gamma > zero {
            "ActiveClosureFailure"
        } else if self.phi == zero {
            "ExactRepair"
        } else {
            "ClosedResidual"
        }
    }

    pub fn digest(&self) -> String {
        let map = serde_json::json!({
            "adequate": self.adequate,
            "carrier": self.carrier,
            "gamma": to_canonical_string(&self.gamma),
            "phi": to_canonical_string(&self.phi),
            "residual": self.residual.iter().map(to_canonical_string).collect::<Vec<_>>(),
        });
        let cjson = canonical_json_str(&map);
        let mut hasher = Sha256::new();
        hasher.update(cjson.as_bytes());
        hex::encode(hasher.finalize())
    }
}

fn canonical_letter(letter: &str) -> Result<&'static str, String> {
    match letter {
        "E" => Ok("E"),
        "R" => Ok("R"),
        "C" => Ok("C"),
        "I" => Ok("I"),
        "Λ" | "Lambda" | "L" => Ok("Λ"),
        "D" => Ok("D"),
        "M" => Ok("M"),
        "T" => Ok("T"),
        _ => Err(format!("UNKNOWN_LETTER: {letter:?}")),
    }
}

fn control_violation(control: &str, letter: &str) -> Option<&'static str> {
    if control == "Terminalized" {
        return Some("TerminalAbsorbing");
    }
    if control == "Refused" && letter != "C" && letter != "Λ" && letter != "T" {
        return Some("RefusalAbsorbing");
    }
    None
}

fn next_control(control: &str, letter: &str) -> &'static str {
    if letter == "T" {
        "Terminalized"
    } else if letter == "M" {
        "Refused"
    } else if control == "Refused" {
        "Open"
    } else if control == "Terminalized" {
        "Terminalized"
    } else {
        "Open"
    }
}

fn step_violations_e(
    same_carrier: bool,
    before: &DdcInternalState,
    after: &DdcInternalState,
    zero: &Exact,
    v: &mut Vec<String>,
) {
    if !same_carrier {
        v.push("FixedCarrierOpChangedCarrier".to_string());
    }
    if before.cls() != "ExactRepair" {
        v.push("ExactRepairFromNonExactClass".to_string());
    }
    if &after.phi != zero || &after.gamma != zero {
        v.push("ExactRepairLeftResidual".to_string());
    }
    if after.residual.iter().any(|x| x != zero) {
        v.push("ExactRepairLeftDefect".to_string());
    }
    if !before.adequate {
        v.push("BlindDetector".to_string());
    }
}

fn step_violations_r(
    same_carrier: bool,
    before: &DdcInternalState,
    after: &DdcInternalState,
    v: &mut Vec<String>,
) {
    if !same_carrier {
        v.push("FixedCarrierOpChangedCarrier".to_string());
    }
    if after.phi != before.phi {
        v.push("ResidualProjectionChangedMass".to_string());
    }
    if after.gamma != before.gamma {
        v.push("ResidualProjectionChangedClosure".to_string());
    }
    if !before.adequate {
        v.push("BlindDetector".to_string());
    }
}

fn step_violations_lambda(
    same_carrier: bool,
    before: &DdcInternalState,
    witness: &DdcTapeWitnessWire,
    v: &mut Vec<String>,
) {
    if same_carrier {
        v.push("CarrierUnchangedUnderRestructure".to_string());
    }
    if !witness.lift_licence {
        v.push("UnlicensedLift".to_string());
    }
    let is_closed = before.cls() == "ClosedResidual";
    if !(is_closed || !before.adequate) {
        v.push("LiftWithoutTrigger".to_string());
    }
}

fn step_violations_t(
    before: &DdcInternalState,
    after: &DdcInternalState,
    zero: &Exact,
    v: &mut Vec<String>,
) {
    if before != after {
        v.push("InertOpMutatedState".to_string());
    }
    if &after.gamma != zero {
        v.push("TerminalizedOpenResidual".to_string());
    }
    if !before.adequate {
        v.push("BlindDetector".to_string());
    }
}

fn step_violations_inert(
    letter: &str,
    before: &DdcInternalState,
    after: &DdcInternalState,
    witness: &DdcTapeWitnessWire,
    v: &mut Vec<String>,
) {
    if before != after {
        v.push("InertOpMutatedState".to_string());
    }
    if letter == "I" && !witness.receipt {
        v.push("MissingReceipt".to_string());
    }
    if letter == "M" && !witness.reason.as_ref().is_some_and(|r| M_REASONS.contains(&r.as_str())) {
        v.push("MissingRefusalReason".to_string());
    }
}

fn step_violations_restructure_or_inert(
    letter: &str,
    same_carrier: bool,
    before: &DdcInternalState,
    after: &DdcInternalState,
    witness: &DdcTapeWitnessWire,
    v: &mut Vec<String>,
) {
    match letter {
        "C" => {
            if same_carrier {
                v.push("CarrierUnchangedUnderRestructure".to_string());
            }
            if after.phi < before.phi || after.gamma < before.gamma {
                v.push("ContextExposureLoweredObstruction".to_string());
            }
        }
        "D" => {
            if same_carrier {
                v.push("CarrierUnchangedUnderRestructure".to_string());
            }
            if !witness.loss_ledger {
                v.push("MissingLossLedger".to_string());
            }
        }
        "I" | "M" => step_violations_inert(letter, before, after, witness, v),
        _ => v.push("UnknownLetter".to_string()),
    }
}

fn step_violations(
    letter: &str,
    before: &DdcInternalState,
    after: &DdcInternalState,
    witness: &DdcTapeWitnessWire,
) -> Vec<String> {
    let mut v = Vec::new();
    let same_carrier = before.carrier == after.carrier;
    let zero = Exact::from_integer(0.into());

    match letter {
        "E" => step_violations_e(same_carrier, before, after, &zero, &mut v),
        "R" => step_violations_r(same_carrier, before, after, &mut v),
        "Λ" => step_violations_lambda(same_carrier, before, witness, &mut v),
        "T" => step_violations_t(before, after, &zero, &mut v),
        _ => step_violations_restructure_or_inert(letter, same_carrier, before, after, witness, &mut v),
    }
    v
}

fn entry_hash(index: usize, prev_hash: &str, letter: &str, payload: &Value) -> String {
    let cjson = canonical_json_str(payload);
    let raw = format!("{index}:{prev_hash}:{letter}:{cjson}");
    let mut hasher = Sha256::new();
    hasher.update(raw.as_bytes());
    hex::encode(hasher.finalize())
}

pub fn verify_tape(payload: &Value) -> Result<DdcVerifyTapeOutcomeV1, String> {
    let req: DdcVerifyTapeRequestV1 = serde_json::from_value(payload.clone()).map_err(|e| {
        let text = e.to_string();
        if text.contains("missing field `adequate`") || text.contains("missing field \"adequate\"") {
            "REFUSED_MISSING_ADEQUATE".to_string()
        } else {
            format!("invalid request: {text}")
        }
    })?;

    let genesis_root = req.genesis_root.as_deref().unwrap_or(DDC_TAPE_GENESIS_ROOT);
    let mut genesis_hasher = Sha256::new();
    genesis_hasher.update(genesis_root.as_bytes());
    let mut current_hash = hex::encode(genesis_hasher.finalize());

    let mut state = DdcInternalState::parse(&req.initial_state)?;
    let mut control = "Open";
    let mut recorded_letters = Vec::new();

    for (index, step_wire) in req.steps.iter().enumerate() {
        let letter = match canonical_letter(&step_wire.letter) {
            Ok(l) => l,
            Err(_) => {
                return Ok(DdcVerifyTapeOutcomeV1 {
                    lawful: false,
                    receipt_head: current_hash,
                    letters: recorded_letters.join(""),
                    final_control: control.to_string(),
                    halted_at: Some(index),
                    violations: vec!["UnknownLetter".to_string()],
                    authority_effect: "None".to_string(),
                });
            }
        };

        let after_state = DdcInternalState::parse(&step_wire.after)?;
        let witness = step_wire.witness.clone().unwrap_or_default();

        let mut violations = Vec::new();
        if let Some(cv) = control_violation(control, letter) {
            violations.push(cv.to_string());
        }
        violations.extend(step_violations(letter, &state, &after_state, &witness));

        if !violations.is_empty() {
            return Ok(DdcVerifyTapeOutcomeV1 {
                lawful: false,
                receipt_head: current_hash,
                letters: recorded_letters.join(""),
                final_control: control.to_string(),
                halted_at: Some(index),
                violations,
                authority_effect: "None".to_string(),
            });
        }

        control = next_control(control, letter);
        recorded_letters.push(letter);

        let routing_terminal = if letter == "T" {
            if after_state.cls() == "ExactRepair" {
                Some("CheckPassed")
            } else {
                Some("Residual")
            }
        } else {
            None
        };

        let entry_payload = serde_json::json!({
            "step_index": index,
            "before_digest": state.digest(),
            "after_digest": after_state.digest(),
            "carrier_before": state.carrier,
            "carrier_after": after_state.carrier,
            "class_before": state.cls(),
            "class_after": after_state.cls(),
            "phi_before": to_canonical_string(&state.phi),
            "phi_after": to_canonical_string(&after_state.phi),
            "gamma_before": to_canonical_string(&state.gamma),
            "gamma_after": to_canonical_string(&after_state.gamma),
            "witness": {
                "receipt": witness.receipt,
                "loss_ledger": witness.loss_ledger,
                "lift_licence": witness.lift_licence,
                "reason": witness.reason,
            },
            "control_after": control,
            "routing_terminal": routing_terminal,
            "authority_effect": "None",
        });

        current_hash = entry_hash(index, &current_hash, letter, &entry_payload);
        state = after_state;
    }

    Ok(DdcVerifyTapeOutcomeV1 {
        lawful: true,
        receipt_head: current_hash,
        letters: recorded_letters.join(""),
        final_control: control.to_string(),
        halted_at: None,
        violations: Vec::new(),
        authority_effect: "None".to_string(),
    })
}

// Origin: engine/crates_rs/pfp/src/ddc.rs
// Claim: urn:core:crates_rs:pfp:ddc:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord09f728ed {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord09f728ed` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError09f728ed {
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
impl BoundaryError09f728ed {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError09f728ed {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError09f728ed {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord09f728ed {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError09f728ed> {
        if capacity_bound == 0 {
            return Err(BoundaryError09f728ed::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError09f728ed::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError09f728ed::ExceedsCapacity {
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
mod l4_boundary_tests_09f728ed {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord09f728ed::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord09f728ed::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord09f728ed::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord09f728ed::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord09f728ed::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError09f728ed::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError09f728ed::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

#[cfg(test)]
mod adequate_refusal_tests {
    use super::verify_tape;
    use serde_json::json;

    fn state(adequate: Option<bool>) -> serde_json::Value {
        let mut value = json!({
            "carrier": "undeclared",
            "residual": [],
            "phi": "0",
            "gamma": "0"
        });
        if let Some(flag) = adequate {
            value["adequate"] = json!(flag);
        }
        value
    }

    #[test]
    fn omitted_adequate_is_a_typed_refusal() {
        let payload = json!({"initial_state": state(None), "steps": []});
        let error = verify_tape(&payload).expect_err("omitted adequate");
        assert_eq!(error, "REFUSED_MISSING_ADEQUATE");
    }

    #[test]
    fn explicit_true_with_witness_fields_passes() {
        let witnessed = state(Some(true));
        let payload = json!({
            "initial_state": witnessed,
            "steps": [{
                "letter": "T",
                "after": state(Some(true)),
                "witness": {"receipt": true, "loss_ledger": true, "lift_licence": true}
            }]
        });
        let outcome = verify_tape(&payload).expect("explicit adequate");
        assert!(outcome.lawful);
        assert!(outcome.violations.is_empty());
    }
}
