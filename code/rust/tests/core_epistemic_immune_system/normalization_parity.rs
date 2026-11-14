//! Parity integration tests for Charpoly Wire normalization, Normalized Matcher central tolerance,
//! and Ab09 CHSH range verification.
//!
//! AuthorityEffect: None.

use core_epistemic_immune_system::host_checks::{
    check_ab09_chsh_bound_range, verify_ab09_chsh_bound_range,
};
use core_epistemic_immune_system::normalization::{
    normalize_candidate, NormalizedMatcher, PRESERVATION_SCOPE, SCHEMA,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

fn candidate(terms: Option<Vec<Value>>, leading: &str) -> String {
    let terms = terms.unwrap_or_default();
    let val = json!({
        "coefficients": [
            terms,
            [],
            [],
            [],
            [{"powers": [0, 0, 0], "q": leading}]
        ]
    });
    serde_json::to_string(&val).unwrap()
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    hex::encode(hasher.finalize())
}

#[test]
fn test_wf52_charpoly_wire_parity_reduction_and_zero_omission() {
    let val = candidate(
        Some(vec![
            json!({"powers": [2, 0, 1], "q": "-4/1"}),
            json!({"powers": [0, 0, 0], "q": "+6/8"}),
            json!({"powers": [1, 2, 3], "q": "-0/7"}),
        ]),
        "2/2",
    );
    let result = normalize_candidate(&val);
    assert!(result.accepted);
    assert_eq!(result.status, "NORMALIZED");
    assert_eq!(result.schema, SCHEMA);
    assert_eq!(result.scope, PRESERVATION_SCOPE);

    let norm: Value = serde_json::from_str(result.normalized_json.as_ref().unwrap()).unwrap();
    let coeff0 = &norm["coefficients"][0];
    assert_eq!(coeff0.as_array().unwrap().len(), 2);
    assert_eq!(coeff0[0]["powers"], json!([0, 0, 0]));
    assert_eq!(coeff0[0]["q"], "3/4");
    assert_eq!(coeff0[1]["powers"], json!([2, 0, 1]));
    assert_eq!(coeff0[1]["q"], "-4");

    let coeff4 = &norm["coefficients"][4];
    assert_eq!(coeff4[0]["powers"], json!([0, 0, 0]));
    assert_eq!(coeff4[0]["q"], "1");

    assert_eq!(result.original_sha256.unwrap(), sha256_hex(val.as_bytes()));
    assert_eq!(
        result.normalized_sha256.unwrap(),
        sha256_hex(result.normalized_json.as_ref().unwrap().as_bytes())
    );

    let operations: BTreeSet<String> = result
        .transformations
        .iter()
        .map(|t| t["operation"].as_str().unwrap().to_string())
        .collect();
    assert!(operations.contains("reduce_rational"));
    assert!(operations.contains("omit_explicit_zero"));
    assert!(operations.contains("sort_monomials"));
    assert!(operations.contains("canonical_json_serialization"));
}

#[test]
fn test_wf52_bounded_rational_panel_cross_multiplication() {
    for numerator in -9..=9 {
        for denominator in 1..=9 {
            let text = format!("{numerator}/{denominator}");
            let val = candidate(Some(vec![json!({"powers": [2, 1, 0], "q": text})]), "3/3");
            let result = normalize_candidate(&val);
            assert!(result.accepted, "Rational {text} must be accepted");
            let norm: Value =
                serde_json::from_str(result.normalized_json.as_ref().unwrap()).unwrap();
            let coeff0 = &norm["coefficients"][0];
            if numerator == 0 {
                assert_eq!(coeff0.as_array().unwrap().len(), 0);
            } else {
                assert_eq!(coeff0.as_array().unwrap().len(), 1);
                let q_str = coeff0[0]["q"].as_str().unwrap();
                let (r_num, r_den) = match q_str.split_once('/') {
                    Some((n, d)) => (n.parse::<i64>().unwrap(), d.parse::<i64>().unwrap()),
                    None => (q_str.parse::<i64>().unwrap(), 1i64),
                };
                assert_eq!(
                    r_num * (denominator as i64),
                    (numerator as i64) * r_den,
                    "Cross multiplication must hold for {text}"
                );
            }
        }
    }
}

#[test]
fn test_wf52_normalized_matcher_prevents_false_autoimmune_apoptosis() {
    let matcher = NormalizedMatcher::default();
    let pattern = r#""q":\s*"[0-9]{1,5}/[0-9]{1,5}""#;

    let healthy_self_panel = [
        r#"{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "1"}]]}"#,
        r#"{"coefficients": [[{"powers": [0, 0, 0], "q": "+0"}], [], [], [], [{"powers": [0, 0, 0], "q": "2/2"}]]}"#,
        r#"{"coefficients": [[{"powers": [2, 0, 0], "q": "1"}, {"powers": [0, 2, 0], "q": "1"}], [], [], [], [{"powers": [0, 0, 0], "q": "1/1"}]]}"#,
        "{\n  \"coefficients\": [\n    [],\n    [{\"powers\": [1, 1, 0], \"q\": \"+4/2\"}],\n    [],\n    [],\n    [{\"powers\": [0, 0, 0], \"q\": \"1\"}]\n  ]\n}",
    ];

    for fixture in healthy_self_panel {
        let is_match = matcher.matches(pattern, fixture).unwrap();
        assert!(
            !is_match,
            "Healthy fixture with representation variants must not trigger autoimmune match: {fixture}"
        );
    }

    // Genuine malformed antigen must still be caught
    let defective_pattern = r#""powers":\s*\[[5-9]"#;
    let bad_antigen = r#"{"coefficients": [[], [], [], [], [{"powers": [5, 0, 0], "q": "1"}]]}"#;
    let is_bad_match = matcher.matches(defective_pattern, bad_antigen).unwrap();
    assert!(
        is_bad_match,
        "Defective antigen must be caught by normalized matcher"
    );
}

#[test]
fn test_wf52_ab09_chsh_range_parity() {
    // Physical claims within Tsirelson ceiling 2*sqrt(2)
    let physical = [
        "CHSH = 0",
        "CHSH = 2",
        "CHSH = 2*sqrt(2)",
        "CHSH = -2*sqrt(2)",
        "CHSH >= -2*sqrt(2)",
        "Maximal CHSH = 1.5.",
        "Bell expectation = 2.5",
    ];
    for text in physical {
        let finding = check_ab09_chsh_bound_range(text);
        assert!(
            finding.passed,
            "Physical claim '{text}' must pass Tsirelson check"
        );
        assert!(verify_ab09_chsh_bound_range(text).is_ok());
    }

    // Claims exceeding Tsirelson ceiling 2*sqrt(2)
    let unphysical = [
        "CHSH = 2.83",
        "CHSH = 4",
        "CHSH = -4",
        "CHSH > 2*sqrt(2)",
        "CHSH < -2*sqrt(2)",
        "CHSH < -3",
        "CHSH <= -2.9",
        "CHSH = 2.5*sqrt(2)",
        "CHSH = 2*sqrt(3)",
        "Maximal CHSH = 2.95.",
        "CHSH |S| = 3",
        "CHSH |S| = -1",
    ];
    for text in unphysical {
        let finding = check_ab09_chsh_bound_range(text);
        assert!(
            !finding.passed,
            "Unphysical claim '{text}' must fail Tsirelson check"
        );
        assert!(finding.evidence.contains("Tsirelson ceiling"));
        let err = verify_ab09_chsh_bound_range(text).unwrap_err();
        assert_eq!(err.code, "CHSH_RANGE_VIOLATION");
    }

    // Benign text without CHSH claim must not fire
    let benign = [
        "The energy expectation = 3.5 for this state.",
        "The <H> expectation = 6 meV here.",
        "Campbell = 5 in the dataset.",
        "Under maximal measurement angles, expectation = 4.",
    ];
    for text in benign {
        let finding = check_ab09_chsh_bound_range(text);
        assert!(finding.passed);
        assert_eq!(finding.evidence, "No CHSH claim exceeds 2*sqrt(2).");
    }
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/normalization_parity.rs
// Claim: urn:core:crates_rs:tests:normalization-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordae0cf69c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordae0cf69c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorae0cf69c {
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
impl BoundaryErrorae0cf69c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorae0cf69c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorae0cf69c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordae0cf69c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorae0cf69c> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorae0cf69c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorae0cf69c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorae0cf69c::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ae0cf69c() {
    let record = BoundaryRecordae0cf69c::try_admit(2, 5).unwrap();
    assert_eq!(record.admitted_items(), 2);
    assert_eq!(record.capacity_bound(), 5);
    assert_eq!(record.remaining_capacity(), 3);

    assert_eq!(
        BoundaryRecordae0cf69c::try_admit(0, 5).unwrap_err(),
        BoundaryErrorae0cf69c::EmptyAdmission
    );
    assert_eq!(
        BoundaryRecordae0cf69c::try_admit(2, 0).unwrap_err(),
        BoundaryErrorae0cf69c::CapacityZero
    );
    assert_eq!(
        BoundaryRecordae0cf69c::try_admit(6, 5).unwrap_err(),
        BoundaryErrorae0cf69c::ExceedsCapacity {
            admitted_items: 6,
            capacity_bound: 5
        }
    );
}
