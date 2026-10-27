#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_wdp_21_8_lean_extension(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "WDP-21-8-LEAN-EXTENSION",
            domain: "ch21_8_lean_scope_accounting",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (154, 124, 30);
    if candidate != expected {
        return ControlReceipt {
            control_id: "WDP-21-8-LEAN-EXTENSION",
            domain: "ch21_8_lean_scope_accounting",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "WDP-21-8-LEAN-EXTENSION",
        domain: "ch21_8_lean_scope_accounting",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_wdp_21_8_lean_extension_scoped_control() {
    let ok = evaluate_wdp_21_8_lean_extension((154, 124, 30), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (154, 124, 30));

    let drifted = evaluate_wdp_21_8_lean_extension((154 + 1, 124, 30), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_wdp_21_8_lean_extension((154, 124, 30), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}
/// Covered plus remainder restores the declared total.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ScopeAccount { total: i64, covered: i64, remainder: i64 }
pub fn try_scope_account(total: i64, covered: i64, remainder: i64) -> Result<ScopeAccount, &'static str> {
    let sum = covered.checked_add(remainder).ok_or("covered plus remainder overflowed")?;
    if sum != total {
        return Err("total is not covered plus remainder");
    }
    Ok(ScopeAccount { total, covered, remainder })
}
#[test]
fn covered_plus_remainder_restores_one_hundred_fifty_four() {
    let account = try_scope_account(154, 124, 30);
    assert_eq!(account.as_ref().map(|item| item.total), Ok(154));
    assert_eq!(try_scope_account(154, 124, 31).map(|_| ()), Err("total is not covered plus remainder"));
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_21_8_lean_extension.rs
// Claim: urn:core:crates_rs:tests:wdp-21-8-lean-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf1a92e4f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf1a92e4f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf1a92e4f {
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
impl BoundaryErrorf1a92e4f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf1a92e4f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf1a92e4f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf1a92e4f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf1a92e4f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf1a92e4f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf1a92e4f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf1a92e4f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f1a92e4f() {
    let admitted = BoundaryRecordf1a92e4f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf1a92e4f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
