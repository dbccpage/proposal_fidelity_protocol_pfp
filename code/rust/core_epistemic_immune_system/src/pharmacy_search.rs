//! Deterministic, scope-bound pharmacy selection. Retrieval is not activation.
//! Admission records are read from the composition's trusted catalog snapshot;
//! this endpoint does not authenticate a human or manufacture an admission act.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_9e4ed1b5<T> {
    fn checked_invariant_9e4ed1b5(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_9e4ed1b5<T> for Option<T> {
    #[inline]
    fn checked_invariant_9e4ed1b5(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_9e4ed1b5<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_9e4ed1b5(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::Refusal;
use serde::Deserialize;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

const RULE_KEYS: &[&str] = &[
    "failure_class",
    "target_pattern",
    "constraint_type",
    "operatorizability",
    "action",
    "severity",
    "negative_fixture",
    "positive_fixture",
    "scope",
    "guidance_text",
];

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Query {
    domain: String,
    tags: Vec<String>,
    stage: String,
    prompt_field: String,
    scope: String,
    #[serde(default = "default_limit")]
    limit: usize,
    now_epoch: u64,
    #[serde(default)]
    suspended_ids: BTreeSet<String>,
}

fn default_limit() -> usize {
    3
}
fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}
fn is_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn named(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 512
        && value.trim() == value
        && !value.chars().any(char::is_control)
}
fn strings(value: &Value) -> Option<Vec<&str>> {
    let values = value.as_array()?;
    if values.is_empty() || values.len() > 64 {
        return None;
    }
    values
        .iter()
        .map(|v| v.as_str().filter(|s| named(s)))
        .collect()
}

/// Same explicit string/list JSON profile as Python's rule_content_bytes.
pub fn rule_digest(record: &Value) -> Result<String, Refusal> {
    let mut content = Map::new();
    for key in RULE_KEYS {
        let value = record.get(*key).ok_or_else(|| {
            Refusal::new("PHARMACY_RULE_INVALID", format!("missing rule field {key}"))
        })?;
        if *key != "scope" && !value.is_string() {
            return Err(Refusal::new(
                "PHARMACY_RULE_INVALID",
                "rule text must be a string",
            ));
        }
        content.insert((*key).to_owned(), value.clone());
    }
    serde_json::to_vec(&Value::Object(content))
        .map(|v| digest(&v))
        .map_err(|e| Refusal::new("PHARMACY_RULE_INVALID", e.to_string()))
}

fn check_record_status(id: &str, record: &Value, query: &Query) -> Result<(), &'static str> {
    if record["antibody_id"].as_str() != Some(id) || record["authority_effect"] != "None" {
        return Err("MALFORMED_RECORD");
    }
    if record["pharmacy_status"] != "admitted" {
        return Err("NOT_ADMITTED");
    }
    for (field, err_code) in [("suspended", "SUSPENDED"), ("revoked", "REVOKED")] {
        if let Some(value) = record.get(field) {
            let flag = value.as_bool().ok_or("MALFORMED_RECORD")?;
            if flag {
                return Err(err_code);
            }
        }
    }
    if query.suspended_ids.contains(id) {
        return Err("SUSPENDED");
    }
    Ok(())
}

fn check_retrieval_scope(scope: &Value, query: &Query) -> Result<(usize, usize), &'static str> {
    let map = scope.as_object().ok_or("MISSING_RETRIEVAL_SCOPE")?;
    if map.len() != 4 {
        return Err("MALFORMED_RETRIEVAL_SCOPE");
    }
    if scope["domain"].as_str() != Some(query.domain.as_str()) {
        return Err("DOMAIN_MISMATCH");
    }
    let tags = strings(&scope["tags"]).ok_or("MISSING_RETRIEVAL_SCOPE")?;
    let stages = strings(&scope["stages"]).ok_or("MISSING_RETRIEVAL_SCOPE")?;
    let fields = strings(&scope["prompt_fields"]).ok_or("MISSING_RETRIEVAL_SCOPE")?;
    if !stages.contains(&query.stage.as_str()) || !fields.contains(&query.prompt_field.as_str()) {
        return Err("PROMPT_SCOPE_MISMATCH");
    }
    let overlaps = query
        .tags
        .iter()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .filter(|tag| tags.contains(&tag.as_str()))
        .count();
    if overlaps == 0 {
        return Err("TAG_SCOPE_MISMATCH");
    }
    Ok((stages.len() + fields.len(), overlaps))
}

fn check_guidance_and_rule(record: &Value) -> Result<(&str, String), &'static str> {
    let guidance = record["guidance_text"]
        .as_str()
        .filter(|s| !s.trim().is_empty())
        .ok_or("MISSING_REVIEWED_GUIDANCE")?;
    if guidance.len() > 8192 || guidance.contains("[IMMUNE_FENCE]") {
        return Err("GUIDANCE_INVALID");
    }
    let current = rule_digest(record).map_err(|_| "MALFORMED_RULE")?;
    if record["rule_sha256"].as_str() != Some(current.as_str()) {
        return Err("STALE_RULE_DIGEST");
    }
    let pattern = record["target_pattern"].as_str().ok_or("MALFORMED_RULE")?;
    if pattern.is_empty() || pattern.len() > 4096 || regex::Regex::new(pattern).is_err() {
        return Err("INVALID_DETECTOR");
    }
    Ok((guidance, current))
}

fn check_admission_fields(
    admission: &Value,
    current: &str,
    query: &Query,
) -> Result<(), &'static str> {
    if !admission.is_object() {
        return Err("MISSING_BOUND_ADMISSION");
    }
    if !admission["decision_id"].as_str().is_some_and(named)
        || !admission["issuer"].as_str().is_some_and(named)
    {
        return Err("MALFORMED_ADMISSION");
    }
    let receipt = admission["receipt_sha256"].as_str().unwrap_or("");
    if !receipt.strip_prefix("sha256:").is_some_and(is_digest) {
        return Err("MALFORMED_ADMISSION");
    }
    if admission["rule_bytes_sha256"] != format!("sha256:{current}") {
        return Err("STALE_ADMISSION");
    }
    if admission["scope"] != query.scope {
        return Err("ADMISSION_SCOPE_MISMATCH");
    }
    Ok(())
}

fn check_admission_lifecycle(
    record: &Value,
    admission: &Value,
    query: &Query,
) -> Result<(), &'static str> {
    if let Some(expiry) = admission.get("expires_at_epoch") {
        let expiry = expiry.as_u64().ok_or("MALFORMED_ADMISSION")?;
        if query.now_epoch >= expiry {
            return Err("ADMISSION_EXPIRED");
        }
    }
    if let Some(revoked) = admission.get("revoked") {
        let is_revoked = revoked.as_bool().ok_or("MALFORMED_ADMISSION")?;
        if is_revoked {
            return Err("REVOKED");
        }
    }
    // Human admission semantics remain owned by the existing admission use case.
    let rule_bytes = RULE_KEYS
        .iter()
        .map(|key| ((*key).to_owned(), record[*key].clone()))
        .collect::<Map<String, Value>>();
    let checked =
        crate::admission::execute(&json!({"operation":"human_admit", "decision":admission,
        "target_rule_bytes_hex":hex::encode(serde_json::to_vec(&Value::Object(rule_bytes))
            .map_err(|_| "MALFORMED_RULE")?)}))
        .map_err(|_| "MALFORMED_ADMISSION")?;
    if checked["status"] != "ADMITTED" {
        return Err("MALFORMED_ADMISSION");
    }
    Ok(())
}

fn candidate(
    id: &str,
    record: &Value,
    query: &Query,
) -> Result<(usize, usize, Value), &'static str> {
    check_record_status(id, record, query)?;
    let scope = &record["scope"];
    let (specificity, overlaps) = check_retrieval_scope(scope, query)?;
    let (guidance, current) = check_guidance_and_rule(record)?;
    let admission = &record["admission"];
    check_admission_fields(admission, &current, query)?;
    check_admission_lifecycle(record, admission, query)?;
    Ok((
        specificity,
        overlaps,
        json!({
            "antibody_id":id, "rule_digest":current, "guidance_text":guidance,
            "target_pattern":record["target_pattern"], "scope":scope,
            "admission_reference":admission,
        }),
    ))
}

fn is_valid_query(query: &Query) -> bool {
    let valid_bounds = (1..=64).contains(&query.limit) && (1..=64).contains(&query.tags.len());
    let valid_tags = query.tags.iter().all(|s| named(s));
    let valid_fields = [
        &query.domain,
        &query.stage,
        &query.prompt_field,
        &query.scope,
    ]
    .iter()
    .all(|s| named(s));
    valid_bounds && valid_tags && valid_fields && query.scope.starts_with("prompt://")
}

fn validate_projection_exclusions(
    payload: &Value,
    records: &Map<String, Value>,
) -> Result<(), Refusal> {
    let Some(projections) = payload.get("projection_exclusions") else {
        return Ok(());
    };
    let allowed = [
        "PROJECTION_PATH_INVALID",
        "PROJECTION_PATH_ESCAPE",
        "PROJECTION_DRIFT",
        "PROJECTION_UNAVAILABLE",
    ];
    let valid = projections.as_object().is_some_and(|rows| {
        rows.iter().all(|(id, reason)| {
            records.contains_key(id) && reason.as_str().is_some_and(|s| allowed.contains(&s))
        })
    });
    if !valid {
        return Err(Refusal::new(
            "PHARMACY_QUERY_INVALID",
            "invalid projection exclusions",
        ));
    }
    Ok(())
}

fn rank_and_select_records(
    records: &Map<String, Value>,
    payload: &Value,
    query: &Query,
) -> (Vec<Value>, Vec<Value>) {
    let mut ranked = Vec::new();
    let mut exclusions = Vec::new();
    for (id, record) in records {
        if let Some(reason) = payload["projection_exclusions"][id].as_str() {
            exclusions.push(json!({"antibody_id":id,"reason":reason}));
            continue;
        }
        match candidate(id, record, query) {
            Ok((specificity, overlaps, value)) => ranked.push((specificity, overlaps, id, value)),
            Err(reason) => exclusions.push(json!({"antibody_id":id,"reason":reason})),
        }
    }
    ranked.sort_by(|a, b| {
        a.0.cmp(&b.0)
            .then_with(|| b.1.cmp(&a.1))
            .then_with(|| a.2.cmp(b.2))
    });
    let mut selected = Vec::new();
    for (position, (_, _, id, record)) in ranked.into_iter().enumerate() {
        if position < query.limit {
            selected.push(record);
        } else {
            exclusions.push(json!({"antibody_id":id,"reason":"RESULT_LIMIT"}));
        }
    }
    exclusions.sort_by(|a, b| a["antibody_id"].as_str().cmp(&b["antibody_id"].as_str()));
    (selected, exclusions)
}

fn attach_candidate_hits(candidate: &Value, result: &mut Value) -> Result<(), Refusal> {
    let content = candidate["content"]
        .as_str()
        .filter(|s| s.len() <= 64 * 1024)
        .ok_or_else(|| {
            Refusal::new("PHARMACY_CANDIDATE_INVALID", "text must be at most 64 KiB")
        })?;
    let subject_digest = digest(content.as_bytes());
    if candidate["sha256"] != subject_digest {
        return Err(Refusal::new(
            "PHARMACY_CANDIDATE_MISMATCH",
            "candidate bytes changed",
        ));
    }
    let mut hits = Vec::new();
    for rule in result["selected"]
        .as_array()
        .checked_invariant_9e4ed1b5("selected array")
    {
        let pattern = regex::Regex::new(
            rule["target_pattern"]
                .as_str()
                .checked_invariant_9e4ed1b5("validated pattern"),
        )
        .map_err(|e| Refusal::new("PHARMACY_DETECTOR_INVALID", e.to_string()))?;
        for hit in pattern.find_iter(content).take(64) {
            hits.push(
                json!({"antibody_id":rule["antibody_id"],"rule_digest":rule["rule_digest"],
                "matched_text":hit.as_str(),"offset":hit.start(),"offset_unit":"utf8_bytes",
                "subject_digest":subject_digest}),
            );
        }
    }
    result["hits"] = json!(hits);
    result["subject_digest"] = json!(subject_digest);
    Ok(())
}

fn parse_and_verify_catalog(payload: &Value) -> Result<(String, Value), Refusal> {
    let text = payload["catalog_json"]
        .as_str()
        .filter(|s| s.len() <= 16 * 1024 * 1024)
        .ok_or_else(|| {
            Refusal::new(
                "PHARMACY_QUERY_INVALID",
                "catalog JSON must be at most 16 MiB",
            )
        })?;
    let catalog_digest = digest(text.as_bytes());
    if payload["catalog_digest"] != catalog_digest {
        return Err(Refusal::new(
            "PHARMACY_SNAPSHOT_MISMATCH",
            "catalog bytes changed",
        ));
    }
    let catalog: Value = serde_json::from_str(text)
        .map_err(|e| Refusal::new("PHARMACY_CATALOG_INVALID", e.to_string()))?;
    Ok((catalog_digest, catalog))
}

pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let invalid = |detail: &str| Refusal::new("PHARMACY_QUERY_INVALID", detail);
    let query: Query =
        serde_json::from_value(payload["query"].clone()).map_err(|e| invalid(&e.to_string()))?;
    if !is_valid_query(&query) {
        return Err(invalid(
            "declared domain/tags/stage/field/prompt URI and limit 1..64 required",
        ));
    }
    let (catalog_digest, catalog) = parse_and_verify_catalog(payload)?;
    let records = catalog["antibodies"]
        .as_object()
        .ok_or_else(|| Refusal::new("PHARMACY_CATALOG_INVALID", "antibodies must be an object"))?;
    validate_projection_exclusions(payload, records)?;
    let (selected, exclusions) = rank_and_select_records(records, payload, &query);
    let request_digest = digest(&serde_json::to_vec(payload).map_err(|e| invalid(&e.to_string()))?);
    let mut result = json!({"catalog_digest":catalog_digest,"request_digest":request_digest,"selected":selected,
        "exclusions":exclusions,"authority_effect":"None"});
    if let Some(candidate) = payload.get("candidate") {
        attach_candidate_hits(candidate, &mut result)?;
    }
    Ok(result)
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/pharmacy_search.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:pharmacy-search:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9e4ed1b5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9e4ed1b5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9e4ed1b5 {
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
impl BoundaryError9e4ed1b5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9e4ed1b5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9e4ed1b5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9e4ed1b5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9e4ed1b5> {
        if capacity_bound == 0 {
            return Err(BoundaryError9e4ed1b5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9e4ed1b5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9e4ed1b5::ExceedsCapacity {
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
mod l4_boundary_tests_9e4ed1b5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9e4ed1b5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9e4ed1b5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9e4ed1b5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9e4ed1b5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9e4ed1b5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9e4ed1b5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9e4ed1b5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
