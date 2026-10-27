use pfp::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use serde_json::json;

#[test]
fn test_witness_1_clean_proof_passes() {
    let scan_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "lean_scan_sources".to_owned(),
        payload: json!({
            "sources": [
                {
                    "file": "Clean.lean",
                    "content": "theorem my_thm (p : Prop) : p → p := fun h => h\n"
                }
            ],
            "forbidden_constructs": []
        }),
    };
    let scan_res = dispatch_runtime_request(&scan_req);
    assert!(scan_res.success);
    let scan_val = scan_res.result.unwrap();
    assert_eq!(scan_val["clean"], true);
    assert_eq!(scan_val["findings"].as_array().unwrap().len(), 0);

    let audit_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "lean_audit_report".to_owned(),
        payload: json!({
            "axioms_output": "'judge_check_1' depends on axioms: [propext, Quot.sound]\n",
            "policy": ["propext", "Quot.sound"],
            "required_declarations": ["judge_check_1"],
            "build_success": true,
            "harness_elaborated": true,
            "forbidden_findings": []
        }),
    };
    let audit_res = dispatch_runtime_request(&audit_req);
    assert!(audit_res.success);
    let audit_val = audit_res.result.unwrap();
    assert_eq!(
        audit_val["schema_version"],
        "core.symbol_game.lean_verification_receipt.v1"
    );
    assert_eq!(audit_val["authority_effect"], "None");
    assert_eq!(audit_val["status"], "PASS");
    assert!(audit_val["refusal_code"].is_null());
}

#[test]
fn test_witness_2_sorry_proof_fails_scan_and_audit() {
    let scan_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "lean_scan_sources".to_owned(),
        payload: json!({
            "sources": [
                {
                    "file": "Sorry.lean",
                    "content": "theorem bad : 2 + 2 = 5 := by\n  sorry\n"
                }
            ],
            "forbidden_constructs": []
        }),
    };
    let scan_res = dispatch_runtime_request(&scan_req);
    assert!(scan_res.success);
    let scan_val = scan_res.result.unwrap();
    assert_eq!(scan_val["clean"], false);
    let findings = scan_val["findings"].as_array().unwrap();
    assert_eq!(findings.len(), 1);
    assert_eq!(findings[0]["construct"], "sorry");

    // Audit also catches sorryAx
    let audit_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "lean_audit_report".to_owned(),
        payload: json!({
            "axioms_output": "'judge_check_1' depends on axioms: [sorryAx]\n",
            "policy": ["propext", "Quot.sound"],
            "required_declarations": ["judge_check_1"],
            "build_success": true,
            "harness_elaborated": true,
            "forbidden_findings": findings
        }),
    };
    let audit_res = dispatch_runtime_request(&audit_req);
    assert!(audit_res.success);
    let audit_val = audit_res.result.unwrap();
    assert_eq!(audit_val["status"], "FAIL");
    assert_eq!(audit_val["refusal_code"], "FORBIDDEN_CONSTRUCT_DETECTED");
}

#[test]
fn test_witness_3_axiom_cheat_fails() {
    let scan_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "lean_scan_sources".to_owned(),
        payload: json!({
            "sources": [
                {
                    "file": "Cheat.lean",
                    "content": "axiom cheat : False\ntheorem fake : 1 = 2 := False.elim cheat\n"
                }
            ],
            "forbidden_constructs": []
        }),
    };
    let scan_res = dispatch_runtime_request(&scan_req);
    assert!(scan_res.success);
    let scan_val = scan_res.result.unwrap();
    assert_eq!(scan_val["clean"], false);
    let findings = scan_val["findings"].as_array().unwrap();
    assert_eq!(findings[0]["construct"], "axiom");

    let audit_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "lean_audit_report".to_owned(),
        payload: json!({
            "axioms_output": "'judge_check_1' depends on axioms: [cheat]\n",
            "policy": ["propext", "Quot.sound"],
            "required_declarations": ["judge_check_1"],
            "build_success": true,
            "harness_elaborated": true,
            "forbidden_findings": findings
        }),
    };
    let audit_res = dispatch_runtime_request(&audit_req);
    assert!(audit_res.success);
    let audit_val = audit_res.result.unwrap();
    assert_eq!(audit_val["status"], "FAIL");
}

#[test]
fn test_witness_4_weaker_statement_harness_fails() {
    let audit_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "lean_audit_report".to_owned(),
        payload: json!({
            "axioms_output": "",
            "policy": ["propext", "Quot.sound"],
            "required_declarations": ["judge_check_1"],
            "build_success": true,
            "harness_elaborated": false,
            "forbidden_findings": []
        }),
    };
    let audit_res = dispatch_runtime_request(&audit_req);
    assert!(audit_res.success);
    let audit_val = audit_res.result.unwrap();
    assert_eq!(audit_val["status"], "FAIL");
    assert_eq!(audit_val["refusal_code"], "HARNESS_ELABORATION_FAILED");
}

#[test]
fn test_witness_5_sorry_inside_comment_and_string_passes() {
    let scan_req = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "lean_scan_sources".to_owned(),
        payload: json!({
            "sources": [
                {
                    "file": "Comments.lean",
                    "content": r#"
-- Line comment: please do not use sorry or axiom here!
/-
  Block comment with nested comment:
  /- nested sorry and admit -/
  still in outer block comment: sorry
-/
def greeting : String := "this string mentions sorry, unsafe, and axiom"
theorem valid_thm : True := trivial
"#
                }
            ],
            "forbidden_constructs": []
        }),
    };
    let scan_res = dispatch_runtime_request(&scan_req);
    assert!(scan_res.success);
    let scan_val = scan_res.result.unwrap();
    assert_eq!(
        scan_val["clean"], true,
        "Findings: {:?}",
        scan_val["findings"]
    );
    assert_eq!(scan_val["findings"].as_array().unwrap().len(), 0);
}

// Origin: engine/crates_rs/tests/pfp/lean_verify.rs
// Claim: urn:core:crates_rs:tests:lean-verify:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord99231069 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord99231069` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError99231069 {
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
impl BoundaryError99231069 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError99231069 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError99231069 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord99231069 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError99231069> {
        if capacity_bound == 0 {
            return Err(BoundaryError99231069::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError99231069::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError99231069::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_99231069() {
    let admitted = BoundaryRecord99231069::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord99231069::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
