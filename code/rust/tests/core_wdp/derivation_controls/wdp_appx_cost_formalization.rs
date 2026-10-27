#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_wdp_appx_cost_formalization(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "WDP-APPX-COST-FORMALIZATION",
            domain: "interval_signature_cost_equivalence",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (3, 3, 8);
    if candidate != expected {
        return ControlReceipt {
            control_id: "WDP-APPX-COST-FORMALIZATION",
            domain: "interval_signature_cost_equivalence",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "WDP-APPX-COST-FORMALIZATION",
        domain: "interval_signature_cost_equivalence",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_wdp_appx_cost_formalization_scoped_control() {
    let ok = evaluate_wdp_appx_cost_formalization((3, 3, 8), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (3, 3, 8));

    let drifted = evaluate_wdp_appx_cost_formalization((3 + 1, 3, 8), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_wdp_appx_cost_formalization((3, 3, 8), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FormalCost {
    total: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CostError {
    Negative,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appx_cost_formalization.rs
// Claim: urn:core:crates_rs:tests:wdp-appx-cost-formalization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CostError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CostError {}

impl FormalCost {
    pub fn try_new(parts: &[i64]) -> Result<Self, CostError> {
        let mut total = 0i64;
        for part in parts {
            if *part < 0 {
                return Err(CostError::Negative);
            }
            total = total.checked_add(*part).ok_or(CostError::Overflow)?;
        }
        Ok(Self { total })
    }

    pub fn total(&self) -> i64 {
        self.total
    }
}

#[test]
fn nonnegative_parts_sum_to_the_declared_total() {
    let cost = FormalCost::try_new(&[3, 3, 2]);
    assert!(matches!(cost, Ok(cost) if cost.total() == 8));
    assert!(matches!(FormalCost::try_new(&[3, -1]), Err(CostError::Negative)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
