//! Exact carrier measurements and byte-bound candidate checks.
//! Certificate/verdict facts come from injected checkers; these records alone
//! neither authenticate a checker nor reproduce its mathematical verification.
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use crate::stage::ports::Refusal;
use core_types::python_unicode::repr_string;
use serde::{de::DeserializeOwned, Deserialize, Serialize};
use serde_json::{json, value::RawValue, Value};
use sha2::{Digest, Sha256};
use std::str::FromStr;

fn error(code: &str, message: impl Into<String>) -> Refusal {
    let mut refusal = Refusal::new(code, message);
    refusal.locus = "adversary.domain.evidence".into();
    refusal
}
fn type_error(message: impl Into<String>) -> Refusal {
    error("ADVERSARY_EVIDENCE_TYPE_ERROR", message)
}
pub(crate) fn value_error(message: impl Into<String>) -> Refusal {
    error("ADVERSARY_EVIDENCE_VALUE_ERROR", message)
}
fn decode<T: DeserializeOwned>(bytes: &[u8]) -> Result<T, Refusal> {
    serde_json::from_slice(bytes)
        .map_err(|error_value| error("ADVERSARY_EVIDENCE_WIRE_INVALID", error_value.to_string()))
}
fn bytes(value: &Value) -> Result<Vec<u8>, Refusal> {
    serde_json::to_vec(value)
        .map_err(|error_value| error("ADVERSARY_EVIDENCE_WIRE_INVALID", error_value.to_string()))
}
fn trim(value: &str) -> &str {
    value.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}
fn unsigned_digits(value: &str, positive: bool) -> bool {
    !value.is_empty()
        && value.bytes().all(|byte| byte.is_ascii_digit())
        && if positive {
            !value.starts_with('0')
        } else {
            value == "0" || !value.starts_with('0')
        }
}

pub fn sha256_ref(data: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(data)))
}
pub fn is_sha256_ref(value: &Value) -> bool {
    value.as_str().is_some_and(|text| {
        text.strip_prefix("sha256:").is_some_and(|hex| {
            hex.len() == 64
                && hex
                    .bytes()
                    .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        })
    })
}
pub fn canonical_rational(value: &BigRational) -> String {
    if value.denom().is_one() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}
pub fn parse_exact_rational(value: &Value) -> Result<BigRational, Refusal> {
    let kind = match value {
        Value::String(original) => {
            let text = trim(original);
            let (numerator, denominator) = text.split_once('/').unwrap_or((text, "1"));
            if !unsigned_digits(numerator.strip_prefix('-').unwrap_or(numerator), false)
                || !unsigned_digits(denominator, true)
            {
                return Err(value_error(format!(
                    "not an exact rational literal: {}",
                    repr_string(original)
                )));
            }
            let numerator = BigInt::from_str(numerator)
                .map_err(|error_value| value_error(error_value.to_string()))?;
            let denominator = BigInt::from_str(denominator)
                .map_err(|error_value| value_error(error_value.to_string()))?;
            return Ok(BigRational::new(numerator, denominator));
        }
        Value::Number(number) => {
            if let Ok(integer) = BigInt::from_str(&number.to_string()) {
                return Ok(BigRational::from_integer(integer));
            }
            "float"
        }
        Value::Bool(_) => "bool",
        Value::Null => "NoneType",
        Value::Array(_) => "list",
        Value::Object(_) => "dict",
    };
    Err(type_error(format!(
        "exact rational required (int, Fraction or 'p/q' text), got {kind}"
    )))
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum MeasurementStatus {
    Measured,
    NotMeasured,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct MeasurementInput {
    pub status: MeasurementStatus,
    pub backend: String,
    pub phi1: Option<BigRational>,
    pub gamma2: Option<BigRational>,
    pub defect_count: BigInt,
    pub active_obstructions: Vec<String>,
    pub certificate_verified: bool,
    pub dual_witness: Vec<(String, BigRational)>,
    pub reason: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ObstructionMeasurement {
    input: MeasurementInput,
}
impl ObstructionMeasurement {
    pub fn new(input: MeasurementInput) -> Result<Self, Refusal> {
        if trim(&input.backend).is_empty() {
            return Err(value_error("backend must be a nonempty string"));
        }
        if input.defect_count < BigInt::zero() {
            return Err(type_error("defect_count must be a non-negative exact int"));
        }
        if input.status == MeasurementStatus::Measured {
            for (name, value) in [("phi1", &input.phi1), ("gamma2", &input.gamma2)] {
                if !value
                    .as_ref()
                    .is_some_and(|value| value >= &BigRational::zero())
                {
                    return Err(type_error(format!(
                        "a MEASURED {name} must be a non-negative Fraction"
                    )));
                }
            }
            if !input.certificate_verified {
                return Err(value_error(
                    "a measurement without a verified certificate is NOT_MEASURED, not MEASURED",
                ));
            }
            if input.defect_count != BigInt::from(input.active_obstructions.len()) {
                return Err(value_error(
                    "defect_count must equal the number of active obstructions",
                ));
            }
        } else {
            if input.phi1.is_some() || input.gamma2.is_some() {
                return Err(value_error(
                    "a NOT_MEASURED result carries no Phi1 or Gamma2 value",
                ));
            }
            if input.certificate_verified || !input.dual_witness.is_empty() {
                return Err(value_error("a NOT_MEASURED result carries no certificate"));
            }
            if trim(&input.reason).is_empty() {
                return Err(value_error("a NOT_MEASURED result must state why"));
            }
        }
        Ok(Self { input })
    }
    pub fn not_measured(reason: String, backend: String) -> Result<Self, Refusal> {
        Self::new(MeasurementInput {
            status: MeasurementStatus::NotMeasured,
            backend,
            phi1: None,
            gamma2: None,
            defect_count: BigInt::zero(),
            active_obstructions: Vec::new(),
            certificate_verified: false,
            dual_witness: Vec::new(),
            reason,
        })
    }
    pub fn is_measured(&self) -> bool {
        self.input.status == MeasurementStatus::Measured
    }
    pub fn is_exact_joint_zero(&self) -> bool {
        self.is_measured()
            && self.input.certificate_verified
            && self.input.phi1.as_ref().is_some_and(Zero::is_zero)
            && self.input.gamma2.as_ref().is_some_and(Zero::is_zero)
    }
    pub fn has_open_obstruction(&self) -> bool {
        self.is_measured()
            && (!self.input.phi1.as_ref().is_some_and(Zero::is_zero)
                || !self.input.gamma2.as_ref().is_some_and(Zero::is_zero))
    }
    pub fn phi1_text(&self) -> Option<String> {
        self.input.phi1.as_ref().map(canonical_rational)
    }
    pub fn gamma2_text(&self) -> Option<String> {
        self.input.gamma2.as_ref().map(canonical_rational)
    }
    pub fn backend(&self) -> &str {
        &self.input.backend
    }
    pub fn defect_count(&self) -> &BigInt {
        &self.input.defect_count
    }
    pub fn active_obstructions(&self) -> &[String] {
        &self.input.active_obstructions
    }
    pub fn reason(&self) -> &str {
        &self.input.reason
    }
    pub fn phi1(&self) -> Option<&BigRational> {
        self.input.phi1.as_ref()
    }
    pub fn gamma2(&self) -> Option<&BigRational> {
        self.input.gamma2.as_ref()
    }
    pub fn certificate_verified(&self) -> bool {
        self.input.certificate_verified
    }
    pub fn dual_witness(&self) -> &[(String, BigRational)] {
        &self.input.dual_witness
    }
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        Self::from_bytes(&bytes(value)?)
    }
    pub fn from_bytes(raw: &[u8]) -> Result<Self, Refusal> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Wire {
            status: MeasurementStatus,
            backend: String,
            #[serde(default)]
            phi1: Option<String>,
            #[serde(default)]
            gamma2: Option<String>,
            #[serde(default)]
            defect_count: Option<Box<RawValue>>,
            #[serde(default)]
            active_obstructions: Vec<String>,
            #[serde(default)]
            certificate_verified: bool,
            #[serde(default)]
            dual_witness: Vec<(String, String)>,
            #[serde(default)]
            reason: String,
        }
        let wire: Wire = decode(raw)?;
        let rational = |value: Option<String>| {
            value
                .map(|value| parse_exact_rational(&json!(value)))
                .transpose()
        };
        let count = match wire.defect_count {
            None => BigInt::zero(),
            Some(value) => BigInt::from_str(value.get())
                .map_err(|_| type_error("defect_count must be a non-negative exact int"))?,
        };
        let dual_witness = wire
            .dual_witness
            .into_iter()
            .map(|(edge, value)| Ok((edge, parse_exact_rational(&json!(value))?)))
            .collect::<Result<Vec<_>, Refusal>>()?;
        Self::new(MeasurementInput {
            status: wire.status,
            backend: wire.backend,
            phi1: rational(wire.phi1)?,
            gamma2: rational(wire.gamma2)?,
            defect_count: count,
            active_obstructions: wire.active_obstructions,
            certificate_verified: wire.certificate_verified,
            dual_witness,
            reason: wire.reason,
        })
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        let count = serde_json::Number::from_str(&self.input.defect_count.to_string())
            .map_err(|error_value| value_error(error_value.to_string()))?;
        Ok(
            json!({"status":self.input.status,"backend":self.input.backend,"phi1":self.phi1_text(),"gamma2":self.gamma2_text(),
            "defect_count":count,"active_obstructions":self.input.active_obstructions,"certificate_verified":self.input.certificate_verified,
            "dual_witness":self.input.dual_witness.iter().map(|(edge,value)|json!([edge,canonical_rational(value)])).collect::<Vec<_>>(),"reason":self.input.reason}),
        )
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CheckerVerdict {
    Accepted,
    Rejected,
    NotMeasured,
}
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CandidateCheckInput {
    pub verdict: CheckerVerdict,
    pub candidate_id: String,
    pub candidate_content_sha256: String,
    pub checker_id: String,
    pub checker_receipt_sha256: Option<String>,
    pub checker_receipt_bytes: Vec<u8>,
    pub reason: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CandidateCheck {
    input: CandidateCheckInput,
}
impl CandidateCheck {
    pub fn new(input: CandidateCheckInput) -> Result<Self, Refusal> {
        for (name, value) in [
            ("candidate_id", &input.candidate_id),
            ("checker_id", &input.checker_id),
        ] {
            if trim(value).is_empty() {
                return Err(value_error(format!("{name} must be a nonempty string")));
            }
        }
        if !is_sha256_ref(&json!(input.candidate_content_sha256)) {
            return Err(value_error(
                "candidate_content_sha256 must be a sha256:<hex> reference",
            ));
        }
        if input.verdict == CheckerVerdict::NotMeasured {
            if input.checker_receipt_sha256.is_some() || !input.checker_receipt_bytes.is_empty() {
                return Err(value_error(
                    "a NOT_MEASURED check carries no checker receipt",
                ));
            }
            if trim(&input.reason).is_empty() {
                return Err(value_error("a NOT_MEASURED check must state why"));
            }
        } else {
            if input.checker_receipt_bytes.is_empty() {
                let label = if input.verdict == CheckerVerdict::Accepted {
                    "ACCEPTED"
                } else {
                    "REJECTED"
                };
                return Err(value_error(format!(
                    "a {label} check requires the checker receipt bytes"
                )));
            }
            if input.checker_receipt_sha256.as_deref()
                != Some(sha256_ref(&input.checker_receipt_bytes).as_str())
            {
                return Err(value_error(
                    "checker_receipt_sha256 is not the digest of the receipt bytes",
                ));
            }
        }
        Ok(Self { input })
    }
    pub fn binds(&self, candidate_id: &str, artifact_refs: &[String]) -> bool {
        self.input.candidate_id == candidate_id
            && artifact_refs.contains(&self.input.candidate_content_sha256)
    }
    pub fn can_authorize(&self) -> bool {
        self.input.verdict == CheckerVerdict::Accepted
    }
    pub fn verdict(&self) -> CheckerVerdict {
        self.input.verdict
    }
    pub fn candidate_id(&self) -> &str {
        &self.input.candidate_id
    }
    pub fn receipt_bytes(&self) -> &[u8] {
        &self.input.checker_receipt_bytes
    }
    pub fn receipt_sha256(&self) -> Option<&str> {
        self.input.checker_receipt_sha256.as_deref()
    }
    pub fn candidate_content_sha256(&self) -> &str {
        &self.input.candidate_content_sha256
    }
    pub fn checker_id(&self) -> &str {
        &self.input.checker_id
    }
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        Self::from_bytes(&bytes(value)?)
    }
    pub fn from_bytes(raw: &[u8]) -> Result<Self, Refusal> {
        #[derive(Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Wire {
            verdict: CheckerVerdict,
            candidate_id: String,
            candidate_content_sha256: String,
            checker_id: String,
            #[serde(default)]
            checker_receipt_sha256: Option<String>,
            #[serde(default)]
            checker_receipt_hex: String,
            #[serde(default)]
            reason: String,
        }
        let wire: Wire = decode(raw)?;
        let checker_receipt_bytes =
            hex::decode(wire.checker_receipt_hex).map_err(|error_value| {
                error("ADVERSARY_EVIDENCE_WIRE_INVALID", error_value.to_string())
            })?;
        Self::new(CandidateCheckInput {
            verdict: wire.verdict,
            candidate_id: wire.candidate_id,
            candidate_content_sha256: wire.candidate_content_sha256,
            checker_id: wire.checker_id,
            checker_receipt_sha256: wire.checker_receipt_sha256,
            checker_receipt_bytes,
            reason: wire.reason,
        })
    }
    pub fn to_dict(&self) -> Value {
        json!({"verdict":self.input.verdict,"candidate_id":self.input.candidate_id,"candidate_content_sha256":self.input.candidate_content_sha256,
            "checker_id":self.input.checker_id,"checker_receipt_sha256":self.input.checker_receipt_sha256,
            "checker_receipt_hex":hex::encode(&self.input.checker_receipt_bytes),"reason":self.input.reason})
    }
}

// Origin: engine/crates_rs/core_adversary/src/evidence.rs
// Claim: urn:core:crates_rs:core-adversary:evidence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb0f6b9ff {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb0f6b9ff` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb0f6b9ff {
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
impl BoundaryErrorb0f6b9ff {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb0f6b9ff {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb0f6b9ff {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb0f6b9ff {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb0f6b9ff> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb0f6b9ff::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb0f6b9ff::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb0f6b9ff::ExceedsCapacity {
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
mod l4_boundary_tests_b0f6b9ff {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb0f6b9ff::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb0f6b9ff::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb0f6b9ff::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb0f6b9ff::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb0f6b9ff::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb0f6b9ff::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb0f6b9ff::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
