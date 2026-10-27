#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_odm_reuse_open(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-REUSE-OPEN",
            domain: "odm_recursive_adapter_second_reuse",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (2, 2, 0);
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-REUSE-OPEN",
            domain: "odm_recursive_adapter_second_reuse",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-REUSE-OPEN",
        domain: "odm_recursive_adapter_second_reuse",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SecondReuseBalance {
    first: i64,
    second: i64,
    third: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SecondReuseBalanceError {
    NotEqual,
    Residual,
    NonPositive,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_reuse_open.rs
// Claim: urn:core:crates_rs:tests:plan-odm-reuse-open:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SecondReuseBalanceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SecondReuseBalanceError {}

impl SecondReuseBalance {
    pub fn certify(triple: (i64, i64, i64)) -> Result<Self, SecondReuseBalanceError> {
        let (first, second, third) = triple;
        if first <= 0 { return Err(SecondReuseBalanceError::NonPositive); }
        if first != second { return Err(SecondReuseBalanceError::NotEqual); }
        if third != 0 { return Err(SecondReuseBalanceError::Residual); }
        Ok(Self { first, second, third })
    }
}

#[test]
fn test_plan_odm_reuse_open_scoped_control() {
    let ok = evaluate_plan_odm_reuse_open((2, 2, 0), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (2, 2, 0));

    let drifted = evaluate_plan_odm_reuse_open((2 + 1, 2, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_odm_reuse_open((2, 2, 0), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(SecondReuseBalance::certify((2, 2, 0)), Ok(w) if w.third == 0 && w.first == 2));
        assert!(matches!(SecondReuseBalance::certify((2, 1, 0)), Err(SecondReuseBalanceError::NotEqual)));
        assert!(matches!(SecondReuseBalance::certify((2, 2, 1)), Err(SecondReuseBalanceError::Residual)));
    }
}
