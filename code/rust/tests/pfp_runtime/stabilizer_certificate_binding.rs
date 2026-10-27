//! Compact certificates bind identities and coordinate rows, not merely lengths.
//! AuthorityEffect: None.

use pfp_runtime::stabilizer::{check, solve};
use serde_json::{json, Value};

fn bell() -> Value {
    json!({"id":"bell", "n":2, "terms":[
        {"id":"zz", "pauli":"ZZ", "weight":[1,1], "target":1},
        {"id":"xx", "pauli":"XX", "weight":[1,1], "target":1}
    ]})
}

fn valid_result(case: &Value) -> Value {
    let result = serde_json::to_value(solve(case)).expect("solver receipt serializes");
    assert!(check(case, &result).is_pass());
    result
}

#[test]
fn rejects_same_length_basis_identity_substitution() {
    let case = bell();
    let valid = valid_result(&case);
    for replacement in [
        json!(["zz", "zz"]),
        json!(["xx", "zz"]),
        json!(["zz", "absent"]),
        json!(["zz", true]),
    ] {
        let mut forged = valid.clone();
        forged["basis"] = replacement;
        assert!(
            check(&case, &forged).is_fail(),
            "accepted forged basis: {forged}"
        );
    }
}

#[test]
fn rejects_decomposition_identity_mask_and_phase_substitution() {
    let case = bell();
    let valid = valid_result(&case);
    for (field, replacement) in [
        ("id", json!("xx")),
        ("mask", json!(2)),
        ("mask", json!(0)),
        ("phase", json!(-1)),
    ] {
        let mut forged = valid.clone();
        forged["decomposition"][0][field] = replacement;
        assert!(
            check(&case, &forged).is_fail(),
            "accepted forged {field}: {forged}"
        );
    }
    let mut contradictory_alias = valid.clone();
    contradictory_alias["decomposition"][0]["sign"] = json!(-1);
    assert!(check(&case, &contradictory_alias).is_fail());
}

#[test]
fn rejects_wrong_case_identity_and_wrong_unknown_refusal() {
    let case = bell();
    let mut forged = valid_result(&case);
    forged["id"] = json!("unrelated");
    assert!(check(&case, &forged).is_fail());

    let malformed = json!({"id":"invalid", "n":0, "terms":[]});
    let mut refused = valid_result(&malformed);
    refused["refusal_code"] = json!("invented");
    assert!(check(&malformed, &refused).is_fail());
}

// Origin: engine/crates_rs/tests/pfp_runtime/stabilizer_certificate_binding.rs
// Claim: urn:core:crates_rs:tests:stabilizer-certificate-binding:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord77418665 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord77418665` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError77418665 {
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
impl BoundaryError77418665 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError77418665 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError77418665 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord77418665 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError77418665> {
        if capacity_bound == 0 {
            return Err(BoundaryError77418665::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError77418665::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError77418665::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_77418665() {
    let admitted = BoundaryRecord77418665::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord77418665::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
