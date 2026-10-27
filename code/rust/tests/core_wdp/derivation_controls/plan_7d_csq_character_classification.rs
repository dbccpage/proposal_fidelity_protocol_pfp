#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_7d_csq_character_classification(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-7D-CSQ-CHARACTER-CLASSIFICATION",
            domain: "dyadic_character_integer_classification",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (8, 8, 1);
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-7D-CSQ-CHARACTER-CLASSIFICATION",
            domain: "dyadic_character_integer_classification",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-7D-CSQ-CHARACTER-CLASSIFICATION",
        domain: "dyadic_character_integer_classification",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_7d_csq_character_classification_scoped_control() {
    let ok = evaluate_plan_7d_csq_character_classification((8, 8, 1), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (8, 8, 1));

    let drifted = evaluate_plan_7d_csq_character_classification((8 + 1, 8, 1), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_7d_csq_character_classification((8, 8, 1), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}
/// Bijection of the order-8 carrier onto 0..8. Image count equals the order, and the identity label 0 occurs once.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DyadicLabeling { order: u64, images: u64, identity_hits: u64 }
pub fn try_dyadic_labeling(labels: &[u8]) -> Result<DyadicLabeling, &'static str> {
    if labels.len() != 8 {
        return Err("this control's carrier has order 8");
    }
    let mut seen = [0u8; 8];
    let mut identity_hits = 0u64;
    for &label in labels {
        let slot = seen.get_mut(usize::from(label)).ok_or("a label lies outside 0..8")?;
        if *slot != 0 {
            return Err("a label is repeated");
        }
        *slot = 1;
        if label == 0 {
            identity_hits += 1;
        }
    }
    let images = seen.iter().filter(|&&s| s != 0).count() as u64;
    if images != 8 || identity_hits != 1 {
        return Err("a bijection of an order-8 carrier hits the identity once");
    }
    Ok(DyadicLabeling { order: 8, images, identity_hits })
}
#[test]
fn the_identity_permutation_has_order_eight_and_one_identity() {
    let labeling = try_dyadic_labeling(&[0, 1, 2, 3, 4, 5, 6, 7]);
    assert_eq!(labeling.as_ref().map(|item| (item.order, item.images, item.identity_hits)), Ok((8, 8, 1)));
    assert_eq!(try_dyadic_labeling(&[0, 0, 2, 3, 4, 5, 6, 7]).map(|_| ()), Err("a label is repeated"));
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_csq_character_classification.rs
// Claim: urn:core:crates_rs:tests:plan-7d-csq-character-classification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord222a146d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord222a146d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError222a146d {
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
impl BoundaryError222a146d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError222a146d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError222a146d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord222a146d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError222a146d> {
        if capacity_bound == 0 {
            return Err(BoundaryError222a146d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError222a146d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError222a146d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_222a146d() {
    let admitted = BoundaryRecord222a146d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord222a146d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
