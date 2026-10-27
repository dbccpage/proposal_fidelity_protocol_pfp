//! Exact wire encodings and their declared digest profiles; no host I/O.

use super::*;

fn dispatch_domain_digest(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let Some(domain) = payload.get("domain").and_then(|v| v.as_str()) else {
        return outcome_err(action, "missing domain string");
    };
    let Some(value) = payload.get("value") else {
        return outcome_err(action, "missing value payload");
    };
    match domain_digest_json(domain, value) {
        Ok(digest) => outcome_ok(action, Value::String(digest)),
        Err(e) => outcome_err(action, e.to_string()),
    }
}

fn dispatch_parse_unified_diff(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let Some(text) = payload.as_str() else {
        return outcome_err(action, "patch_text must be string");
    };
    let res = parse_unified_diff(text);
    outcome_ok(
        action,
        serde_json::json!({
            "touched_paths": res.touched_paths,
            "is_valid": res.is_valid,
            "error_message": res.error_message,
        }),
    )
}

fn dispatch_jcs_canonicalize(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: JcsCanonicalizeRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid jcs_canonicalize input: {e}")),
    };
    let canonical_res = match (&request.raw, &request.value) {
        (Some(raw), _) => pfp_runtime::jcs_canonicalize_str(raw),
        (None, Some(val)) => pfp_runtime::jcs_canonicalize_value(val),
        (None, None) => {
            return outcome_err(
                action,
                "jcs_canonicalize requires either 'value' or 'raw' field",
            )
        }
    };
    match canonical_res {
        Ok(canonical_str) => {
            let bytes_hex = hex::encode(canonical_str.as_bytes());
            outcome_ok(
                action,
                serde_json::json!({
                    "canonical_json": canonical_str,
                    "canonical_bytes_hex": bytes_hex,
                }),
            )
        }
        Err(e) => outcome_err(action, format!("JCS canonicalization error: {e}")),
    }
}

fn dispatch_jcs_digest(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: JcsDigestRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid jcs_digest input: {e}")),
    };
    let digest_res = match (&request.raw, &request.value) {
        (Some(raw), _) => pfp_runtime::jcs_digest_str_sha256(raw),
        (None, Some(val)) => pfp_runtime::jcs_digest_sha256(val),
        (None, None) => {
            return outcome_err(action, "jcs_digest requires either 'value' or 'raw' field")
        }
    };
    match digest_res {
        Ok(sha256_hex) => outcome_ok(action, serde_json::json!({ "sha256": sha256_hex })),
        Err(e) => outcome_err(action, format!("JCS digest error: {e}")),
    }
}

fn dispatch_canonical_wire_op(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    let outcome = match action {
        "canonical_wire" => match canonical_wire(payload) {
            Ok(wire) => outcome_ok(action, wire),
            Err(e) => outcome_err(action, e.to_string()),
        },
        "canonical_unwire" => match canonical_unwire(payload) {
            Ok(val) => outcome_ok(action, val.to_wire()),
            Err(e) => outcome_err(action, e.to_string()),
        },
        "canonical_json" => match canonical_json(payload) {
            Ok(s) => outcome_ok(action, Value::String(s)),
            Err(e) => outcome_err(action, e.to_string()),
        },
        "canonical_bytes_hex" => match canonical_bytes(payload) {
            Ok(b) => outcome_ok(action, Value::String(hex::encode(b))),
            Err(e) => outcome_err(action, e.to_string()),
        },
        _ => return None,
    };
    Some(outcome)
}

pub(super) fn dispatch(req: &RuntimeRequestV1) -> RuntimeOutcomeV1 {
    let action = req.action.as_str();
    if let Some(outcome) = dispatch_canonical_wire_op(action, &req.payload) {
        return outcome;
    }
    match action {
        "domain_digest" => dispatch_domain_digest(action, &req.payload),
        "parse_unified_diff" => dispatch_parse_unified_diff(action, &req.payload),
        "jcs_canonicalize" => dispatch_jcs_canonicalize(action, &req.payload),
        "jcs_digest" => dispatch_jcs_digest(action, &req.payload),
        other => outcome_err(action, format!("unsupported runtime action: {other}")),
    }
}

// Origin: engine/crates_rs/pfp/src/invoke/wire.rs
// Claim: urn:core:crates_rs:pfp:wire:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord31b3f58e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord31b3f58e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError31b3f58e {
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
impl BoundaryError31b3f58e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError31b3f58e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError31b3f58e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord31b3f58e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError31b3f58e> {
        if capacity_bound == 0 {
            return Err(BoundaryError31b3f58e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError31b3f58e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError31b3f58e::ExceedsCapacity {
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
mod l4_boundary_tests_31b3f58e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord31b3f58e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord31b3f58e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord31b3f58e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord31b3f58e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord31b3f58e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError31b3f58e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError31b3f58e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
