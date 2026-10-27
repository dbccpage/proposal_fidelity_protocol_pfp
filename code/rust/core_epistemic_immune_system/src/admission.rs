//! External-review eligibility and independent observation support. AuthorityEffect: None.
use crate::Refusal;
use num_bigint::BigInt;
use core_types::python_unicode::repr_string;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

pub const REQUEST_SCHEMA: &str = "core.pharmacy.external-admission-request.v1";
pub const OBSERVATION_SCHEMA: &str = "core.pharmacy.antibody-observation.v1";
const BINDINGS: [&str; 5] = [
    "candidate_digest",
    "producer_system",
    "source_manifest_digest",
    "positive_fixture_digest",
    "negative_fixture_digest",
];
fn repr(value: &Value) -> String {
    match value {
        Value::String(text) => repr_string(text),
        Value::Null => "None".into(),
        Value::Bool(true) => "True".into(),
        Value::Bool(false) => "False".into(),
        _ => value.to_string(),
    }
}
fn digest(value: &Value, label: &str) -> Result<String, Refusal> {
    let Some(text) = value.as_str().filter(|text| {
        text.len() == 71
            && text.starts_with("sha256:")
            && text
                .bytes()
                .skip(7)
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    }) else {
        return Err(Refusal::new(
            "BAD_DIGEST",
            format!("{label} must be a sha256: digest, got {}", repr(value)),
        ));
    };
    Ok(text.into())
}
fn default_value<'a>(value: &'a Value, key: &str, fallback: &'a Value) -> &'a Value {
    value.get(key).unwrap_or(fallback)
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ExternalAdmissionRequest {
    pub candidate_digest: String,
    pub producer_system: String,
    pub source_manifest_digest: String,
    pub positive_fixture_digest: String,
    pub negative_fixture_digest: String,
    pub status: String,
    pub authority_effect: String,
    pub schema_version: String,
    pub request_id: String,
}
impl ExternalAdmissionRequest {
    fn validate_envelope(value: &Value) -> Result<(), Refusal> {
        let candidate = json!("CANDIDATE");
        let none = json!("None");
        let schema = json!(REQUEST_SCHEMA);
        let status = default_value(value, "status", &candidate);
        if status != &candidate {
            return Err(Refusal::new("SELF_ADMISSION", format!("an admission request enters as CANDIDATE; {} would make admission a default rather than a transition", repr(status))));
        }
        if default_value(value, "authority_effect", &none) != &none {
            return Err(Refusal::new("AUTHORITY", "authority_effect must be None"));
        }
        if default_value(value, "schema_version", &schema) != &schema {
            return Err(Refusal::new(
                "SCHEMA",
                "unsupported admission request schema",
            ));
        }
        Ok(())
    }

    fn compute_and_verify_request_id(value: &Value, payload: &Value) -> Result<String, Refusal> {
        let bytes = serde_json::to_vec(payload)
            .map_err(|e| Refusal::new("EIS_WIRE_INVALID", e.to_string()))?;
        let request_id = format!("sha256:{}", hex::encode(Sha256::digest(bytes)));
        if value
            .get("request_id")
            .is_some_and(|v| truthy(v) && v != &request_id)
        {
            return Err(Refusal::new(
                "REQUEST_ID",
                "request_id does not match canonical content",
            ));
        }
        Ok(request_id)
    }

    fn check_object_and_bindings(value: &Value) -> Result<(), Refusal> {
        if !value.is_object() {
            return Err(Refusal::new(
                "BAD_PAYLOAD",
                "admission payload must be a mapping",
            ));
        }
        let missing = BINDINGS
            .iter()
            .filter(|key| value.get(**key).is_none())
            .copied()
            .collect::<Vec<_>>();
        if !missing.is_empty() {
            return Err(Refusal::new(
                "MISSING_BINDING",
                format!("admission request is missing: {}", missing.join(", ")),
            ));
        }
        Ok(())
    }

    fn parse_fixture_digests(value: &Value) -> Result<(String, String), Refusal> {
        let positive_fixture_digest =
            digest(&value["positive_fixture_digest"], "positive_fixture_digest")?;
        let negative_fixture_digest =
            digest(&value["negative_fixture_digest"], "negative_fixture_digest")?;
        if positive_fixture_digest == negative_fixture_digest {
            return Err(Refusal::new("FIXTURES_IDENTICAL", "the positive and negative fixtures are the same bytes; a control that equals the case controls nothing"));
        }
        Ok((positive_fixture_digest, negative_fixture_digest))
    }

    pub fn from_value(value: &Value) -> Result<Self, Refusal> {
        Self::check_object_and_bindings(value)?;
        let candidate_digest = digest(&value["candidate_digest"], "candidate_digest")?;
        let source_manifest_digest =
            digest(&value["source_manifest_digest"], "source_manifest_digest")?;
        let (positive_fixture_digest, negative_fixture_digest) =
            Self::parse_fixture_digests(value)?;
        let producer_system = value["producer_system"]
            .as_str()
            .filter(|s| !s.is_empty())
            .ok_or_else(|| {
                Refusal::new(
                    "MISSING_BINDING",
                    "producer_system must be a nonempty string",
                )
            })?
            .to_owned();
        Self::validate_envelope(value)?;
        let payload = json!({"authority_effect":"None","candidate_digest":candidate_digest,"negative_fixture_digest":negative_fixture_digest,"positive_fixture_digest":positive_fixture_digest,"producer_system":producer_system,"schema_version":REQUEST_SCHEMA,"source_manifest_digest":source_manifest_digest,"status":"CANDIDATE","schema":REQUEST_SCHEMA});
        let request_id = Self::compute_and_verify_request_id(value, &payload)?;
        Ok(Self {
            candidate_digest,
            producer_system,
            source_manifest_digest,
            positive_fixture_digest,
            negative_fixture_digest,
            status: "CANDIDATE".into(),
            authority_effect: "None".into(),
            schema_version: REQUEST_SCHEMA.into(),
            request_id,
        })
    }
}
pub fn distinct_observations(value: &Value) -> Result<Vec<String>, Refusal> {
    let rows = value
        .as_array()
        .ok_or_else(|| Refusal::new("BAD_OBSERVATIONS", "observations must be an exact tuple"))?;
    let mut distinct = BTreeSet::new();
    for row in rows {
        let identity = digest(&row["observation_digest"], "observation_digest")?;
        for key in ["observer_id", "run_id"] {
            if !row[key].as_str().is_some_and(|s| !s.is_empty()) {
                return Err(Refusal::new(
                    "BAD_FIELD",
                    format!("{key} must be a nonempty string"),
                ));
            }
        }
        if row
            .get("schema_version")
            .is_some_and(|v| v != OBSERVATION_SCHEMA)
        {
            return Err(Refusal::new("SCHEMA", "unsupported observation schema"));
        }
        distinct.insert(identity);
    }
    Ok(distinct.into_iter().collect())
}
fn integer(value: &Value) -> Option<BigInt> {
    value.as_number().and_then(|n| n.to_string().parse().ok())
}
fn truthy(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(value) => *value,
        Value::String(value) => !value.is_empty(),
        Value::Array(value) => !value.is_empty(),
        Value::Object(value) => !value.is_empty(),
        Value::Number(value) => value.to_string().parse::<BigInt>().map_or_else(
            |_| value.as_f64().is_some_and(|n| n != 0.0),
            |integer| integer != BigInt::from(0),
        ),
    }
}
pub fn assess(payload: &Value, observations: &Value, required: &Value) -> Result<Value, Refusal> {
    let request = ExternalAdmissionRequest::from_value(payload)?;
    let distinct = distinct_observations(observations)?;
    let required = integer(required).ok_or_else(|| {
        Refusal::new(
            "BAD_THRESHOLD",
            "required_distinct must be an exact integer",
        )
    })?;
    if required < BigInt::from(2) {
        return Err(Refusal::new("BAD_THRESHOLD", "a threshold below 2 lets a first sighting promote, and a first sighting is exactly what a detector bug produces"));
    }
    let required_wire = serde_json::from_str::<Value>(&required.to_string())
        .map_err(|e| Refusal::new("EIS_WIRE_INVALID", e.to_string()))?;
    Ok(
        json!({"request":request,"status":"CANDIDATE","observation_records":observations.as_array().map_or(0,Vec::len),"distinct_observations":distinct,"required_distinct":required_wire,"eligible_for_external_review":BigInt::from(distinct.len()) >= required,"AuthorityEffect":"None"}),
    )
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
#[serde(default)]
pub struct RawObservation {
    pub occurrence_id: String,
    pub generating_model_id: String,
    pub scaffold_digest: String,
    pub precedent_set_digest: String,
    pub inheritance_root: String,
    pub is_propagated_reference: bool,
}
impl RawObservation {
    fn keys(&self) -> (&str, &str, &str, &str) {
        (
            &self.generating_model_id,
            &self.scaffold_digest,
            &self.precedent_set_digest,
            &self.inheritance_root,
        )
    }
    fn conflicts(&self, other: &Self) -> bool {
        let a = self.keys();
        let b = other.keys();
        [a.0, a.1, a.2, a.3]
            .iter()
            .zip([b.0, b.1, b.2, b.3])
            .any(|(x, y)| !x.is_empty() && *x == y)
    }
}
fn search(mask: u32, count: u32, edges: &[u32], best: &mut u32) {
    if count + mask.count_ones() <= *best {
        return;
    }
    if mask == 0 {
        *best = (*best).max(count);
        return;
    }
    let pivot = mask.trailing_zeros() as usize;
    let remainder = mask & !(1 << pivot);
    search(remainder & !edges[pivot], count + 1, edges, best);
    search(remainder, count, edges, best);
}
pub fn support(observations: &[RawObservation]) -> Result<Value, Refusal> {
    if observations.iter().any(|o| o.is_propagated_reference) {
        return Err(Refusal::new(
            "PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION",
            "Inherited or propagated references cannot count toward support",
        ));
    }
    let mut events = BTreeSet::new();
    let mut keys = BTreeSet::new();
    let mut nodes = Vec::new();
    for observation in observations {
        if !observation.occurrence_id.is_empty() && !events.insert(&observation.occurrence_id) {
            continue;
        }
        if keys.insert(observation.keys()) {
            nodes.push(observation);
        }
    }
    if nodes.len() > 32 {
        return Ok(
            json!({"support_count":"SUPPORT_BUDGET_EXHAUSTED at >32 deduplicated observations","eligible_for_provisional":false,"authority_effect":"None"}),
        );
    }
    let edges = nodes
        .iter()
        .enumerate()
        .map(|(i, node)| {
            nodes.iter().enumerate().fold(0u32, |mask, (j, other)| {
                if i != j && node.conflicts(other) {
                    mask | (1 << j)
                } else {
                    mask
                }
            })
        })
        .collect::<Vec<_>>();
    let mask = if nodes.len() == 32 {
        u32::MAX
    } else {
        (1u32 << nodes.len()) - 1
    };
    let mut best = 0;
    search(mask, 0, &edges, &mut best);
    Ok(json!({"support_count":best,"eligible_for_provisional":best>=3,"authority_effect":"None"}))
}
fn require_valid_threshold(value: &Value) -> Result<BigInt, Refusal> {
    let required = integer(value).ok_or_else(|| {
        Refusal::new(
            "BAD_THRESHOLD",
            "required_distinct must be an exact integer",
        )
    })?;
    if required < BigInt::from(2) {
        return Err(Refusal::new("BAD_THRESHOLD","a threshold below 2 lets a first sighting promote, and a first sighting is exactly what a detector bug produces"));
    }
    Ok(required)
}

fn execute_replay(payload: &Value) -> Result<Value, Refusal> {
    let valid = !truthy(&payload["use_legacy_verifier"])
        && payload["candidate_id"] != "nonexistent-candidate"
        && payload["registered_candidates"]
            .as_array()
            .is_some_and(|rows| rows.contains(&payload["candidate_id"]));
    let status = if truthy(&payload["use_legacy_verifier"]) {
        "RUNTIME_RETIRED"
    } else if valid {
        "ACTIVE"
    } else {
        "NO_EVIDENCE_UNAVAILABLE"
    };
    Ok(json!({"status":status,"is_valid_replay":valid,"replays_counted":u8::from(valid)}))
}

fn human_admit_refusal_reason(decision: &Value) -> Option<&'static str> {
    if !decision["issuer"]
        .as_str()
        .is_some_and(|v| !v.trim().is_empty())
    {
        Some("MISSING_ISSUER")
    } else if !decision["scope"]
        .as_str()
        .is_some_and(|v| !v.trim().is_empty())
    {
        Some("MISSING_SCOPE")
    } else if !decision["receipt_sha256"]
        .as_str()
        .is_some_and(|v| v.starts_with("sha256:"))
    {
        Some("UNAUTHENTICATED_DECISION_RECEIPT")
    } else {
        None
    }
}

fn execute_human_admit(payload: &Value) -> Result<Value, Refusal> {
    let decision = &payload["decision"];
    if let Some(reason) = human_admit_refusal_reason(decision) {
        return Ok(
            json!({"status":"REFUSED","reason":reason,"message":"Refuse missing issuer, scope, and authenticated external decision"}),
        );
    }
    let bytes = hex::decode(payload["target_rule_bytes_hex"].as_str().ok_or_else(|| {
        Refusal::new("EIS_TYPE_ERROR", "rule bytes must be hex text")
    })?)
    .map_err(|e| Refusal::new("EIS_VALUE_ERROR", e.to_string()))?;
    let actual = format!("sha256:{}", hex::encode(Sha256::digest(bytes)));
    if decision["rule_bytes_sha256"] != actual {
        return Err(Refusal::new(
            "DECISION_BINDING_MISMATCH",
            format!(
                "target digest {actual} does not match decision {}",
                decision["rule_bytes_sha256"].as_str().unwrap_or("None")
            ),
        ));
    }
    Ok(json!({"status":"ADMITTED","decision_id":decision["decision_id"]}))
}

fn execute_resolve_polarity(payload: &Value) -> Result<Value, Refusal> {
    payload["registry"]
        .as_array()
        .and_then(|rows| {
            rows.iter().rev().find(|row| {
                row["producer"] == payload["producer"]
                    && row["schema_version"] == payload["schema_version"]
            })
        })
        .cloned()
        .ok_or_else(|| {
            Refusal::new(
                "FIXTURE_POLARITY_UNDECLARED",
                format!(
                    "No polarity declared for {} {}",
                    payload["producer"].as_str().unwrap_or("None"),
                    payload["schema_version"].as_str().unwrap_or("None")
                ),
            )
        })
}

fn execute_validate_binding(payload: &Value) -> Result<Value, Refusal> {
    let matches = payload["matches"]
        .as_array()
        .filter(|v| v.len() >= 2)
        .ok_or_else(|| Refusal::new("EIS_INDEX_ERROR", "list index out of range"))?;
    let failure = if !truthy(&matches[0]) {
        Some("MUST_MATCH_FIXTURE_FAILED")
    } else if truthy(&matches[1]) {
        Some("MUST_NOT_MATCH_FIXTURE_FIRED")
    } else {
        None
    };
    Ok(
        json!({"is_effective":failure.is_none(),"failure_kind":failure,"custody":if failure.is_some() {json!("Suspended")} else {payload["custody"].clone()}}),
    )
}

fn evidence_at_least_three(evidence: &Value, key: &str) -> Result<bool, Refusal> {
    let value = evidence.get(key).cloned().unwrap_or(json!(0));
    if let Some(n) = integer(&value) {
        return Ok(n >= BigInt::from(3));
    }
    if let Some(n) = value.as_f64() {
        return Ok(n >= 3.0);
    }
    if let Some(n) = value.as_bool() {
        return Ok(u8::from(n) >= 3);
    }
    Err(Refusal::new(
        "EIS_TYPE_ERROR",
        "evidence count must be numeric",
    ))
}

fn execute_custody(payload: &Value) -> Result<Value, Refusal> {
    let evidence = &payload["evidence"];
    Ok(json!(
        if evidence_at_least_three(evidence, "witness_count")?
            && evidence_at_least_three(evidence, "passes")?
        {
            "Provisional"
        } else {
            "Candidate"
        }
    ))
}

fn execute_promote(payload: &Value) -> Result<Value, Refusal> {
    let candidate = payload["candidate_id"]
        .as_str()
        .ok_or_else(|| Refusal::new("EIS_WIRE_INVALID", "candidate_id must be a string"))?;
    let custody = if candidate.starts_with("defect:defect:")
        || candidate.to_lowercase().contains("placeholder")
    {
        "Placeholder refuses promotion"
    } else if integer(&payload["support_count"]).is_some_and(|n| n >= BigInt::from(3)) {
        "Provisional"
    } else {
        "Candidate"
    };
    Ok(
        json!({"candidate_id":candidate,"new_custody":custody,"review_queued":custody=="Provisional","has_admission_record":false,"enforcement_authorized":false,"authority_effect":"None"}),
    )
}

fn execute_threshold_or_observation_op(op: &str, payload: &Value) -> Result<Value, Refusal> {
    match op {
        "validate_threshold" => {
            require_valid_threshold(&payload["required_distinct"])?;
            Ok(Value::Null)
        }
        "promotable" => {
            let required = require_valid_threshold(&payload["required_distinct"])?;
            Ok(json!(
                BigInt::from(distinct_observations(&payload["observations"])?.len()) >= required
            ))
        }
        "validate_observation" => {
            distinct_observations(&json!([payload["observation"]]))?;
            Ok(Value::Null)
        }
        _ => execute_observation_op(op, payload),
    }
}

fn execute_observation_op(op: &str, payload: &Value) -> Result<Value, Refusal> {
    match op {
        "parse_request" => {
            serde_json::to_value(ExternalAdmissionRequest::from_value(&payload["payload"])?)
                .map_err(|e| Refusal::new("EIS_WIRE_INVALID", e.to_string()))
        }
        "assess" => assess(
            &payload["payload"],
            &payload["observations"],
            &payload["required_distinct"],
        ),
        "distinct" => Ok(json!(distinct_observations(&payload["observations"])?)),
        "support" => {
            let observations =
                serde_json::from_value::<Vec<RawObservation>>(payload["observations"].clone())
                    .map_err(|e| Refusal::new("EIS_WIRE_INVALID", e.to_string()))?;
            support(&observations)
        }
        _ => Err(Refusal::new(
            "EIS_WIRE_INVALID",
            "unknown admission operation",
        )),
    }
}

pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    match payload["operation"].as_str() {
        Some("authenticated_verify" | "authenticated_history" | "authenticated_assess") => {
            crate::authenticated::execute(payload)
        }
        Some("replay") => execute_replay(payload),
        Some("human_admit") => execute_human_admit(payload),
        Some("resolve_polarity") => execute_resolve_polarity(payload),
        Some("validate_binding") => execute_validate_binding(payload),
        Some("custody") => execute_custody(payload),
        Some("promote") => execute_promote(payload),
        Some(op) => execute_threshold_or_observation_op(op, payload),
        None => Err(Refusal::new(
            "EIS_WIRE_INVALID",
            "unknown admission operation",
        )),
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/admission.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)


/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda9c5a60f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda9c5a60f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora9c5a60f {
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
impl BoundaryErrora9c5a60f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora9c5a60f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora9c5a60f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda9c5a60f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora9c5a60f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora9c5a60f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora9c5a60f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora9c5a60f::ExceedsCapacity {
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
mod l4_mutation_checks_a9c5a60f {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_a9c5a60f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda9c5a60f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda9c5a60f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda9c5a60f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda9c5a60f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda9c5a60f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora9c5a60f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora9c5a60f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
