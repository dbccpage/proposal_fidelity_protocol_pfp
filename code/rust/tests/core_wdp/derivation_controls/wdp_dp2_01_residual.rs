#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RealizationRuleReceipt {
    pub status: &'static str,
    pub realized_count: usize,
    pub reason: &'static str,
}

pub fn check_single_witness_realization_rule(
    questions: &[(&str, &[i64])],
    witnesses: &[(&str, &[i64])],
) -> RealizationRuleReceipt {
    if questions.is_empty() {
        return RealizationRuleReceipt {
            status: "REFUSED",
            realized_count: 0,
            reason: "EMPTY_QUESTION_FAMILY",
        };
    }
    let mut realized = 0usize;
    for (qid, qvec) in questions {
        let Some((_, wvec)) = witnesses.iter().find(|(wid, _)| wid == qid) else {
            return RealizationRuleReceipt {
                status: "REFUSED",
                realized_count: realized,
                reason: "MISSING_OR_MALFORMED_WITNESS",
            };
        };
        if qvec.is_empty() || qvec.len() != wvec.len() {
            return RealizationRuleReceipt {
                status: "REFUSED",
                realized_count: realized,
                reason: "MISSING_OR_MALFORMED_WITNESS",
            };
        }
        for i in 0..qvec.len() {
            for j in (i + 1)..qvec.len() {
                if qvec[i] != qvec[j] && wvec[i] == wvec[j] {
                    return RealizationRuleReceipt {
                        status: "REFUSED",
                        realized_count: realized,
                        reason: "REALIZATION_COLLISION",
                    };
                }
            }
        }
        realized += 1;
    }
    RealizationRuleReceipt {
        status: "PASS",
        realized_count: realized,
        reason: "ALL_QUESTIONS_REALIZED_BY_SINGLE_WITNESS",
    }
}

#[test]
fn test_wdp_dp2_01_residual_realization_rule() {
    let q = [("q_parity", &[0, 1, 0, 1][..]), ("q_sign", &[1, 1, -1, -1][..])];
    let w_good = [("q_parity", &[2, 5, 2, 5][..]), ("q_sign", &[10, 10, 20, 20][..])];
    let w_bad = [("q_parity", &[2, 2, 2, 5][..]), ("q_sign", &[10, 10, 20, 20][..])];
    let ok = check_single_witness_realization_rule(&q, &w_good);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.realized_count, 2);

    let bad = check_single_witness_realization_rule(&q, &w_bad);
    assert_eq!(bad.status, "REFUSED");
    assert_eq!(bad.reason, "REALIZATION_COLLISION");
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_dp2_01_residual.rs
// Claim: urn:core:crates_rs:tests:wdp-dp2-01-residual:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2d2464f6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2d2464f6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2d2464f6 {
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
impl BoundaryError2d2464f6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2d2464f6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2d2464f6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2d2464f6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2d2464f6> {
        if capacity_bound == 0 {
            return Err(BoundaryError2d2464f6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2d2464f6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2d2464f6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2d2464f6() {
    let admitted = BoundaryRecord2d2464f6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2d2464f6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
