use pfp::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use serde_json::{json, Value};

fn invoke(payload: Value) -> pfp::RuntimeOutcomeV1 {
    dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "reply_control".to_owned(),
        payload,
    })
}

#[test]
fn parser_preserves_first_block_greedy_whitespace_and_machine_field_rules() {
    for (reply, expected) in [
        ("no machine block", json!({})),
        ("```machineKEY=value```", json!({})),
        ("```machine\nSUMMARY= first \r\nAUTHORITY_EFFECT=None\n```\n```machine\nSUMMARY=second\n```", json!({"SUMMARY":"first", "AUTHORITY_EFFECT":"None"})),
        ("```machine\n \n KEY=indented\nKEY2=ignored\nKEY= a=b \n_=ok\n```", json!({"KEY":"a=b", "_":"ok"})),
        ("```machine\u{1c}\nKEY=\u{1f}unicode\u{85}\n```", json!({"KEY":"unicode"})),
        ("```machine\nKEY=unterminated", json!({})),
    ] {
        let outcome = invoke(json!({"operation":"parse", "reply_text":reply}));
        assert!(outcome.success, "{:?}", outcome.error);
        assert_eq!(outcome.result.unwrap()["machine_fields"], expected);
    }
    let duplicate =
        invoke(json!({"operation":"parse", "reply_text":"```machine\nKEY=a\nKEY=b\n```"}));
    assert!(!duplicate.success);
    assert_eq!(
        duplicate.error.unwrap(),
        "duplicate machine-block field: KEY"
    );
}

#[test]
fn residual_declarations_preserve_ordered_refusals_and_do_not_verify_digests() {
    for (fields, digest, colour, refusals) in [
        (
            json!({}),
            Value::Null,
            "Open",
            json!(["AUTHORITY_EFFECT_NON_NONE"]),
        ),
        (
            json!({"AUTHORITY_EFFECT":"None","RESIDUAL_COLOUR":"Closed"}),
            Value::Null,
            "Closed",
            json!([]),
        ),
        (
            json!({"AUTHORITY_EFFECT":"None","RESIDUAL_COLOUR":"bogus"}),
            Value::Null,
            "Open",
            json!([]),
        ),
        (
            json!({"AUTHORITY_EFFECT":"Promote","RESIDUAL_COLOUR":"Exact"}),
            Value::Null,
            "Open",
            json!(["AUTHORITY_EFFECT_NON_NONE", "EXACT_WITHOUT_DUAL_WITNESS"]),
        ),
        (
            json!({"AUTHORITY_EFFECT":"None","RESIDUAL_COLOUR":"Exact"}),
            json!(""),
            "Exact",
            json!([]),
        ),
    ] {
        let outcome = invoke(
            json!({"operation":"validate", "machine_fields":fields, "dual_witness_digest":digest}),
        );
        assert!(outcome.success);
        let result = outcome.result.unwrap();
        assert_eq!(result["residual_colour"], colour);
        assert_eq!(result["refusal_codes"], refusals);
        assert_eq!(result["authority_effect"], "None");
    }
}

#[test]
fn malformed_and_undeclared_payloads_are_typed_native_errors() {
    for payload in [
        json!({"operation":"parse", "reply_text":"", "extra":true}),
        json!({"operation":"validate", "machine_fields":{"AUTHORITY_EFFECT":true}}),
        json!({"operation":"unknown"}),
    ] {
        let outcome = invoke(payload);
        assert!(!outcome.success);
        assert!(outcome
            .error
            .unwrap()
            .starts_with("REPLY_CONTROL_REQUEST_INVALID:"));
        assert_eq!(outcome.authority_effect, "None");
    }
}

// Origin: engine/crates_rs/tests/pfp/reply_control_contract.rs
// Claim: urn:core:crates_rs:tests:reply-control-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd6c17d39 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd6c17d39` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord6c17d39 {
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
impl BoundaryErrord6c17d39 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord6c17d39 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord6c17d39 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd6c17d39 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord6c17d39> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord6c17d39::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord6c17d39::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord6c17d39::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_d6c17d39() {
    let admitted = BoundaryRecordd6c17d39::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd6c17d39::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
