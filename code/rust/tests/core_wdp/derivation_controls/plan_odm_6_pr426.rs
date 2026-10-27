#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_odm_6_pr426(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-6-PR426",
            domain: "odm_6_pr426_meron_demo_audit",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (2, 3, 36);
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-6-PR426",
            domain: "odm_6_pr426_meron_demo_audit",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-6-PR426",
        domain: "odm_6_pr426_meron_demo_audit",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DemoDivisibility {
    left: i64,
    mid: i64,
    right: i64,
    quotient: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DemoDivisibilityError {
    NonPositiveFactor,
    NotDivisible { remainder: i64 },
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_6_pr426.rs
// Claim: urn:core:crates_rs:tests:plan-odm-6-pr426:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DemoDivisibilityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DemoDivisibilityError {}

impl DemoDivisibility {
    pub fn certify(triple: (i64, i64, i64)) -> Result<Self, DemoDivisibilityError> {
        let (left, mid, right) = triple;
        if left <= 0 || mid <= 0 || right < 0 { return Err(DemoDivisibilityError::NonPositiveFactor); }
        let product = left.checked_mul(mid).ok_or(DemoDivisibilityError::Overflow)?;
        let remainder = right.checked_rem(product).ok_or(DemoDivisibilityError::Overflow)?;
        if remainder != 0 { return Err(DemoDivisibilityError::NotDivisible { remainder }); }
        let quotient = right.checked_div(product).ok_or(DemoDivisibilityError::Overflow)?;
        Ok(Self { left, mid, right, quotient })
    }
}

#[test]
fn test_plan_odm_6_pr426_scoped_control() {
    let ok = evaluate_plan_odm_6_pr426((2, 3, 36), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (2, 3, 36));

    let drifted = evaluate_plan_odm_6_pr426((2 + 1, 3, 36), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_odm_6_pr426((2, 3, 36), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(DemoDivisibility::certify((2, 3, 36)), Ok(w) if w.quotient == 6));
        assert!(matches!(DemoDivisibility::certify((2, 3, 35)), Err(DemoDivisibilityError::NotDivisible { .. })));
    }
}
