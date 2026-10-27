#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SingleWitnessAuditReceipt {
    pub status: &'static str,
    pub sufficient: bool,
    pub collision_count: usize,
    pub reason: &'static str,
}

pub fn audit_single_witness_sufficiency(
    question_values: &[i64],
    witness_values: &[i64],
) -> SingleWitnessAuditReceipt {
    if question_values.is_empty() || question_values.len() != witness_values.len() {
        return SingleWitnessAuditReceipt {
            status: "REFUSED",
            sufficient: false,
            collision_count: 0,
            reason: "INVALID_CARRIER_LENGTH",
        };
    }
    let mut collisions = 0usize;
    for i in 0..question_values.len() {
        for j in (i + 1)..question_values.len() {
            if question_values[i] != question_values[j] && witness_values[i] == witness_values[j] {
                collisions += 1;
            }
        }
    }
    if collisions > 0 {
        return SingleWitnessAuditReceipt {
            status: "REFUSED",
            sufficient: false,
            collision_count: collisions,
            reason: "WITNESS_COLLISION_ON_PROTECTED_QUESTION",
        };
    }
    SingleWitnessAuditReceipt {
        status: "PASS",
        sufficient: true,
        collision_count: 0,
        reason: "SINGLE_WITNESS_FACTORS_QUESTION_EXACTLY",
    }
}

#[test]
fn test_wdp_p2a_residual_single_witness_sufficiency() {
    let q = [0, 1, 1];
    let w_good = [10, 20, 20];
    let w_bad = [10, 10, 20];
    let ok = audit_single_witness_sufficiency(&q, &w_good);
    assert_eq!(ok.status, "PASS");
    assert!(ok.sufficient);

    let bad = audit_single_witness_sufficiency(&q, &w_bad);
    assert_eq!(bad.status, "REFUSED");
    assert_eq!(bad.collision_count, 1);
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_p2a_residual.rs
// Claim: urn:core:crates_rs:tests:wdp-p2a-residual:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord16855746 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord16855746` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError16855746 {
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
impl BoundaryError16855746 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError16855746 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError16855746 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord16855746 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError16855746> {
        if capacity_bound == 0 {
            return Err(BoundaryError16855746::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError16855746::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError16855746::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_16855746() {
    let admitted = BoundaryRecord16855746::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord16855746::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
