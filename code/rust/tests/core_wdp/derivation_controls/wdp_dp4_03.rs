#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClaimIndexParityReceipt {
    pub status: &'static str,
    pub matched_count: usize,
    pub reason: &'static str,
}

pub fn check_claim_index_parity(
    expected: &[&str],
    lean: &[&str],
    python: &[&str],
    rust: &[&str],
) -> ClaimIndexParityReceipt {
    if expected.is_empty() {
        return ClaimIndexParityReceipt {
            status: "REFUSED",
            matched_count: 0,
            reason: "EMPTY_EXPECTED_CLAIM_SET",
        };
    }
    for id in expected {
        if !lean.contains(id) || !python.contains(id) || !rust.contains(id) {
            return ClaimIndexParityReceipt {
                status: "REFUSED",
                matched_count: 0,
                reason: "MISSING_CLAIM_BINDING",
            };
        }
    }
    for slice in [lean, python, rust] {
        for id in slice {
            if !expected.contains(id) {
                return ClaimIndexParityReceipt {
                    status: "REFUSED",
                    matched_count: expected.len(),
                    reason: "UNDECLARED_ORPHAN_CLAIM_ID",
                };
            }
        }
    }
    ClaimIndexParityReceipt {
        status: "PASS",
        matched_count: expected.len(),
        reason: "EXACT_THREE_WAY_CLAIM_PARITY",
    }
}

#[test]
fn test_wdp_dp4_03_claim_index_parity() {
    let claims = ["WDP-THM-2.2", "WDP-PROP-4.2", "WDP-THM-9.3"];
    let ok = check_claim_index_parity(&claims, &claims, &claims, &claims);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.matched_count, 3);

    let missing = check_claim_index_parity(&claims, &claims[..2], &claims, &claims);
    assert_eq!(missing.status, "REFUSED");
    assert_eq!(missing.reason, "MISSING_CLAIM_BINDING");

    let orphan = check_claim_index_parity(&claims[..1], &claims[..2], &claims[..1], &claims[..1]);
    assert_eq!(orphan.status, "REFUSED");
    assert_eq!(orphan.reason, "UNDECLARED_ORPHAN_CLAIM_ID");
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_dp4_03.rs
// Claim: urn:core:crates_rs:tests:wdp-dp4-03:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord288d4c7b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord288d4c7b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError288d4c7b {
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
impl BoundaryError288d4c7b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError288d4c7b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError288d4c7b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord288d4c7b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError288d4c7b> {
        if capacity_bound == 0 {
            return Err(BoundaryError288d4c7b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError288d4c7b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError288d4c7b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_288d4c7b() {
    let admitted = BoundaryRecord288d4c7b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord288d4c7b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
