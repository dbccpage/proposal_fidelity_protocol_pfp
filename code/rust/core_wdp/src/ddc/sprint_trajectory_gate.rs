//! ORT / process NDJSON gate for `dda_sprint_trajectory` tapes.
//!
//! Schema id: `dda_sprint_trajectory.v1`
//!
//! Integrity mode requires each record to carry:
//! - `run_id`
//! - step index: `step_index` or `step_id`
//! - residual norm Φ₁: `phi1` or `residual_norm` or `residual_energy`
//! - state fingerprint: `state_vector` or `state_fingerprint` or
//!   both `input_hash` and `output_hash`
//! - `authority_effect` exactly equal to the string `"None"`
//!
//! When any record carries `step_hash`, the chain is re-derived with SHA-256
//! over the JSON object with `step_hash` excluded (same rule as Python
//! `trajectory_recorder._step_hash`).
//!
//! Historical ORT process tapes classify as `LEGACY_PROCESS_TAPE` and fail
//! integrity mode without rewriting those files.
//!
//! AuthorityEffect: None. Diagnostic gate only; mints no authority.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_54b0e905<T> {
    fn checked_invariant_54b0e905(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_54b0e905<T> for Option<T> {
    #[inline]
    fn checked_invariant_54b0e905(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_54b0e905<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_54b0e905(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

pub const SCHEMA_ID: &str = "dda_sprint_trajectory.v1";

pub const CLASS_EMPTY: &str = "EMPTY";
pub const CLASS_LEGACY: &str = "LEGACY_PROCESS_TAPE";
pub const CLASS_INTEGRITY_V1: &str = "INTEGRITY_V1";
pub const CLASS_MIXED: &str = "MIXED";
pub const CLASS_INVALID: &str = "INVALID";

const STEP_KEYS: &[&str] = &["step_index", "step_id"];
const PHI_KEYS: &[&str] = &["phi1", "residual_norm", "residual_energy"];
const STATE_SINGLE: &[&str] = &["state_vector", "state_fingerprint"];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Violation {
    pub line: Option<usize>,
    pub code: String,
    pub detail: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TrajectoryGateResult {
    pub ok: bool,
    pub classification: String,
    pub schema_id: String,
    pub record_count: usize,
    pub violations: Vec<Violation>,
    pub authority_effect: String,
}

impl TrajectoryGateResult {
    fn empty_ok() -> Self {
        Self {
            ok: true,
            classification: CLASS_EMPTY.to_string(),
            schema_id: SCHEMA_ID.to_string(),
            record_count: 0,
            violations: Vec::new(),
            authority_effect: "None".to_string(),
        }
    }
}

fn has_any(record: &Map<String, Value>, keys: &[&str]) -> bool {
    keys.iter().any(|k| match record.get(*k) {
        Some(Value::Null) | None => false,
        Some(_) => true,
    })
}

fn has_step_index(record: &Map<String, Value>) -> bool {
    has_any(record, STEP_KEYS)
}

fn has_phi1(record: &Map<String, Value>) -> bool {
    has_any(record, PHI_KEYS)
}

fn has_state_fingerprint(record: &Map<String, Value>) -> bool {
    if has_any(record, STATE_SINGLE) {
        return true;
    }
    matches!(
        (record.get("input_hash"), record.get("output_hash")),
        (Some(i), Some(o)) if !i.is_null() && !o.is_null()
    )
}

fn is_legacy_shape(record: &Map<String, Value>) -> bool {
    if has_step_index(record) || has_phi1(record) || has_state_fingerprint(record) {
        return false;
    }
    record.contains_key("stage") && record.contains_key("name")
}

fn run_id_present(record: &Map<String, Value>) -> bool {
    match record.get("run_id") {
        Some(Value::String(s)) if !s.is_empty() => true,
        Some(Value::Number(_)) => true,
        Some(v) if !v.is_null() => true,
        _ => false,
    }
}

fn record_integrity_violations(line: usize, record: &Map<String, Value>) -> Vec<Violation> {
    let mut out = Vec::new();
    if !run_id_present(record) {
        out.push(Violation {
            line: Some(line),
            code: "MISSING_RUN_ID".into(),
            detail: "run_id required".into(),
        });
    }
    if !has_step_index(record) {
        out.push(Violation {
            line: Some(line),
            code: "MISSING_STEP_INDEX".into(),
            detail: "need step_index or step_id".into(),
        });
    }
    if !has_phi1(record) {
        out.push(Violation {
            line: Some(line),
            code: "MISSING_PHI1".into(),
            detail: "need phi1 or residual_norm or residual_energy".into(),
        });
    }
    if !has_state_fingerprint(record) {
        out.push(Violation {
            line: Some(line),
            code: "MISSING_STATE_FINGERPRINT".into(),
            detail: "need state_vector or state_fingerprint or input_hash+output_hash".into(),
        });
    }
    let ae_ok = matches!(record.get("authority_effect"), Some(Value::String(s)) if s == "None");
    if !ae_ok {
        out.push(Violation {
            line: Some(line),
            code: "AUTHORITY_EFFECT_NOT_NONE".into(),
            detail: format!(
                "authority_effect must be string 'None', got {:?}",
                record.get("authority_effect")
            ),
        });
    }
    out
}

/// Canonical SHA-256 of record fields excluding `step_hash` (Python parity).
pub fn step_hash(record: &Map<String, Value>) -> String {
    let mut payload = Map::new();
    for (k, v) in record {
        if k != "step_hash" {
            payload.insert(k.clone(), v.clone());
        }
    }
    // BTreeMap ordering via serde_json::Map is insertion order; re-serialize
    // with sorted keys by rebuilding through BTreeMap.
    let ordered: std::collections::BTreeMap<_, _> = payload.into_iter().collect();
    let encoded = serde_json::to_string(&ordered).checked_invariant_54b0e905("json serialize step payload");
    // Python uses separators=(',', ':') and sort_keys=True — serde_json default
    // is compact without spaces, matching that.
    let mut hasher = Sha256::new();
    hasher.update(encoded.as_bytes());
    format!("{:x}", hasher.finalize())
}

fn verify_single_step_hash_link(
    index: usize,
    record: &Map<String, Value>,
    previous_hash: &Option<String>,
) -> Result<String, String> {
    let step_id = record
        .get("step_id")
        .or_else(|| record.get("step_index"))
        .map(|v| v.to_string())
        .unwrap_or_else(|| format!("<index {index}>"));

    let recomputed = step_hash(record);
    let declared = record
        .get("step_hash")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    if recomputed != declared {
        return Err(format!(
            "{step_id}: content does not match its step_hash (edited)"
        ));
    }

    let prev = record.get("prev_step_hash");
    let prev_matches = match (previous_hash, prev) {
        (None, None) | (None, Some(Value::Null)) => true,
        (Some(h), Some(Value::String(s))) => h == s,
        _ => false,
    };
    if !prev_matches {
        return Err(format!(
            "{step_id}: prev_step_hash does not match the preceding step (dropped or reordered)"
        ));
    }
    Ok(recomputed)
}

/// Verify step_hash chain across records (Python `verify_trajectory_chain` twin).
pub fn verify_trajectory_chain(records: &[Map<String, Value>]) -> Result<(), String> {
    if records.is_empty() {
        return Ok(());
    }
    let mut run_ids = std::collections::BTreeSet::new();
    for r in records {
        let key = r
            .get("run_id")
            .map(|v| v.to_string())
            .unwrap_or_else(|| "null".to_string());
        run_ids.insert(key);
    }
    if run_ids.len() != 1 {
        return Err(format!("records span {} runs", run_ids.len()));
    }

    let mut previous_hash: Option<String> = None;
    for (index, record) in records.iter().enumerate() {
        let recomputed = verify_single_step_hash_link(index, record, &previous_hash)?;
        previous_hash = Some(recomputed);
    }
    Ok(())
}

type NdjsonLoadResult = (Vec<Map<String, Value>>, Vec<Violation>);

fn load_ndjson_path(path: &Path) -> Result<NdjsonLoadResult, String> {
    let text = fs::read_to_string(path).map_err(|e| format!("read {}: {e}", path.display()))?;
    let mut records = Vec::new();
    let mut violations = Vec::new();
    for (i, raw) in text.lines().enumerate() {
        let line_no = i + 1;
        let line = raw.trim();
        if line.is_empty() {
            continue;
        }
        match serde_json::from_str::<Value>(line) {
            Ok(Value::Object(map)) => records.push(map),
            Ok(_) => violations.push(Violation {
                line: Some(line_no),
                code: "NOT_OBJECT".into(),
                detail: format!("line {line_no}: expected JSON object"),
            }),
            Err(exc) => violations.push(Violation {
                line: Some(line_no),
                code: "JSON_DECODE".into(),
                detail: format!("line {line_no}: {exc}"),
            }),
        }
    }
    Ok((records, violations))
}

fn collect_trajectory_record_violations(
    records: &[Map<String, Value>],
    require_integrity_v1: bool,
    violations: &mut Vec<Violation>,
) -> (usize, usize) {
    let mut legacy_count = 0usize;
    let mut integrity_count = 0usize;

    for (index, record) in records.iter().enumerate() {
        let line = index + 1;
        let line_violations = record_integrity_violations(line, record);
        if line_violations.is_empty() {
            integrity_count += 1;
            continue;
        }
        if is_legacy_shape(record) {
            legacy_count += 1;
            if require_integrity_v1 {
                violations.extend(line_violations);
            } else {
                for v in line_violations {
                    if v.code == "AUTHORITY_EFFECT_NOT_NONE" || v.code == "MISSING_RUN_ID" {
                        violations.push(v);
                    }
                }
            }
        } else {
            violations.extend(line_violations);
        }
    }
    (integrity_count, legacy_count)
}

fn classify_trajectory_tape(
    total: usize,
    integrity_count: usize,
    legacy_count: usize,
    violations: &[Violation],
) -> &'static str {
    let has_missing_or_auth = violations
        .iter()
        .any(|v| v.code.starts_with("MISSING_") || v.code == "AUTHORITY_EFFECT_NOT_NONE");
    if integrity_count == total && !has_missing_or_auth {
        CLASS_INTEGRITY_V1
    } else if legacy_count == total {
        CLASS_LEGACY
    } else if integrity_count > 0 && legacy_count > 0 {
        CLASS_MIXED
    } else if integrity_count > 0 {
        CLASS_INTEGRITY_V1
    } else if legacy_count > 0 {
        CLASS_LEGACY
    } else {
        CLASS_INVALID
    }
}

/// Validate a DDA sprint trajectory tape from in-memory records.
pub fn validate_dda_sprint_trajectory_records(
    records: &[Map<String, Value>],
    load_violations: Vec<Violation>,
    require_integrity_v1: bool,
) -> TrajectoryGateResult {
    let mut violations = load_violations;

    if records.is_empty() && violations.is_empty() {
        return TrajectoryGateResult::empty_ok();
    }
    if records.is_empty() {
        return TrajectoryGateResult {
            ok: false,
            classification: CLASS_INVALID.to_string(),
            schema_id: SCHEMA_ID.to_string(),
            record_count: 0,
            violations,
            authority_effect: "None".to_string(),
        };
    }

    let (integrity_count, legacy_count) =
        collect_trajectory_record_violations(records, require_integrity_v1, &mut violations);

    if records.iter().any(|r| r.contains_key("step_hash")) {
        if let Err(detail) = verify_trajectory_chain(records) {
            violations.push(Violation {
                line: None,
                code: "CHAIN_BROKEN".into(),
                detail,
            });
        }
    }

    let classification =
        classify_trajectory_tape(records.len(), integrity_count, legacy_count, &violations);

    let mut ok = violations.is_empty();
    let mut final_violations = violations;
    if require_integrity_v1 && classification != CLASS_INTEGRITY_V1 {
        ok = false;
        if classification == CLASS_LEGACY
            && !final_violations
                .iter()
                .any(|v| v.code.starts_with("MISSING_"))
        {
            final_violations.push(Violation {
                line: None,
                code: "LEGACY_NOT_INTEGRITY_V1".into(),
                detail: "tape is LEGACY_PROCESS_TAPE; integrity v1 fields absent".into(),
            });
        }
    }

    TrajectoryGateResult {
        ok,
        classification: classification.to_string(),
        schema_id: SCHEMA_ID.to_string(),
        record_count: records.len(),
        violations: final_violations,
        authority_effect: "None".to_string(),
    }
}

/// Validate a DDA sprint trajectory NDJSON file.
pub fn validate_dda_sprint_trajectory_path(
    path: &Path,
    require_integrity_v1: bool,
) -> Result<TrajectoryGateResult, String> {
    let (records, load_violations) = load_ndjson_path(path)?;
    Ok(validate_dda_sprint_trajectory_records(
        &records,
        load_violations,
        require_integrity_v1,
    ))
}

/// Build one INTEGRITY_V1 record map for ORT / sprint emitters (STORY-ORT-DDA-002).
///
/// When `chain` is true, `prev_step_hash` is stored and `step_hash` is derived
/// via [`step_hash`]. Authority is always the string `"None"`. `phi1` is exact
/// and is written as its canonical rational string (`"1"`, `"1/2"`), never as a
/// JSON float.
#[allow(clippy::too_many_arguments)]
pub fn emit_integrity_v1_record(
    run_id: &str,
    step_index: u64,
    phi1: &num_rational::BigRational,
    state_fingerprint: &str,
    dda_letter: &str,
    name: &str,
    prev_step_hash: Option<&str>,
    chain: bool,
) -> Map<String, Value> {
    let mut record = Map::new();
    record.insert("schema_id".into(), Value::String(SCHEMA_ID.to_string()));
    record.insert("run_id".into(), Value::String(run_id.to_string()));
    record.insert("step_index".into(), json_u64(step_index));
    record.insert(
        "phi1".into(),
        Value::String(core_kernel::to_canonical_string(phi1)),
    );
    record.insert(
        "state_fingerprint".into(),
        Value::String(state_fingerprint.to_string()),
    );
    record.insert("authority_effect".into(), Value::String("None".into()));
    record.insert("dda_letter".into(), Value::String(dda_letter.to_string()));
    record.insert("name".into(), Value::String(name.to_string()));
    if chain {
        match prev_step_hash {
            Some(h) => {
                record.insert("prev_step_hash".into(), Value::String(h.to_string()));
            }
            None => {
                record.insert("prev_step_hash".into(), Value::Null);
            }
        }
        let h = step_hash(&record);
        record.insert("step_hash".into(), Value::String(h));
    }
    record
}

fn json_u64(n: u64) -> Value {
    Value::Number(serde_json::Number::from(n))
}

// Origin: engine/crates_rs/core_wdp/src/ddc/sprint_trajectory_gate.rs
// Claim: urn:core:crates_rs:core-wdp:sprint-trajectory-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord54b0e905 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord54b0e905` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError54b0e905 {
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
impl BoundaryError54b0e905 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError54b0e905 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError54b0e905 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord54b0e905 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError54b0e905> {
        if capacity_bound == 0 {
            return Err(BoundaryError54b0e905::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError54b0e905::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError54b0e905::ExceedsCapacity {
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
    use serde_json::json;

    fn v1_map() -> Map<String, Value> {
        let v = json!({
            "run_id": "run_golden_v1",
            "step_index": 0,
            "phi1": 1.0,
            "state_fingerprint": "abc123",
            "authority_effect": "None",
            "dda_letter": "C",
            "name": "step"
        });
        v.as_object().unwrap().clone()
    }

    fn legacy_map() -> Map<String, Value> {
        let v = json!({
            "run_id": "sprint_planning_ort_003_ppos",
            "date": "2026-07-30",
            "authority_effect": "None",
            "stage": 1,
            "dda_letter": "R",
            "name": "sprint-planning",
            "note": "process tape"
        });
        v.as_object().unwrap().clone()
    }

    #[test]
    fn integrity_v1_golden_passes() {
        let result = validate_dda_sprint_trajectory_records(&[v1_map()], vec![], true);
        assert!(result.ok, "{result:?}");
        assert_eq!(result.classification, CLASS_INTEGRITY_V1);
        assert_eq!(result.schema_id, SCHEMA_ID);
    }

    #[test]
    fn strip_phi1_kills_gate() {
        let mut bad = v1_map();
        bad.remove("phi1");
        let good = validate_dda_sprint_trajectory_records(&[v1_map()], vec![], true);
        assert!(good.ok);
        let killed = validate_dda_sprint_trajectory_records(&[bad], vec![], true);
        assert!(!killed.ok);
        assert!(killed.violations.iter().any(|v| v.code == "MISSING_PHI1"));
    }

    #[test]
    fn ort_process_tape_is_legacy_and_fails_integrity() {
        let result =
            validate_dda_sprint_trajectory_records(&[legacy_map(), legacy_map()], vec![], true);
        assert!(!result.ok);
        assert_eq!(result.classification, CLASS_LEGACY);
    }

    #[test]
    fn legacy_mode_classifies_without_hard_fail() {
        let result = validate_dda_sprint_trajectory_records(&[legacy_map()], vec![], false);
        assert!(result.ok, "{result:?}");
        assert_eq!(result.classification, CLASS_LEGACY);
    }

    #[test]
    fn authority_effect_not_none_is_refused() {
        let mut bad = v1_map();
        bad.insert("authority_effect".into(), json!("Minted"));
        let result = validate_dda_sprint_trajectory_records(&[bad], vec![], true);
        assert!(!result.ok);
        assert!(result
            .violations
            .iter()
            .any(|v| v.code == "AUTHORITY_EFFECT_NOT_NONE"));
    }

    #[test]
    fn emit_integrity_v1_passes_gate() {
        let one = num_rational::BigRational::from_integer(1.into());
        let half = num_rational::BigRational::new(1.into(), 2.into());
        let r0 = emit_integrity_v1_record("r_emit", 0, &one, "fp0", "R", "plan", None, true);
        assert_eq!(r0.get("phi1"), Some(&json!("1")));
        let h0 = r0
            .get("step_hash")
            .and_then(|v| v.as_str())
            .unwrap()
            .to_string();
        let r1 = emit_integrity_v1_record("r_emit", 1, &half, "fp1", "E", "exec", Some(&h0), true);
        assert_eq!(r1.get("phi1"), Some(&json!("1/2")));
        let result = validate_dda_sprint_trajectory_records(&[r0, r1], vec![], true);
        assert!(result.ok, "{result:?}");
        assert_eq!(result.classification, CLASS_INTEGRITY_V1);
    }

    #[test]
    fn chain_break_is_detected() {
        let mut r0 = v1_map();
        r0.insert("step_index".into(), json!(0));
        r0.insert("prev_step_hash".into(), Value::Null);
        let h0 = step_hash(&r0);
        r0.insert("step_hash".into(), json!(h0.clone()));

        let mut r1 = v1_map();
        r1.insert("step_index".into(), json!(1));
        r1.insert("phi1".into(), json!(0.5));
        r1.insert("prev_step_hash".into(), json!(h0));
        let h1 = step_hash(&r1);
        r1.insert("step_hash".into(), json!(h1));

        let ok = validate_dda_sprint_trajectory_records(&[r0.clone(), r1.clone()], vec![], true);
        assert!(ok.ok, "{ok:?}");

        let mut edited = r0;
        edited.insert("phi1".into(), json!(99.0));
        // leave stale step_hash
        let broken = validate_dda_sprint_trajectory_records(&[edited, r1], vec![], true);
        assert!(!broken.ok);
        assert!(broken.violations.iter().any(|v| v.code == "CHAIN_BROKEN"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_54b0e905 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord54b0e905::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord54b0e905::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord54b0e905::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord54b0e905::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord54b0e905::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError54b0e905::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError54b0e905::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
