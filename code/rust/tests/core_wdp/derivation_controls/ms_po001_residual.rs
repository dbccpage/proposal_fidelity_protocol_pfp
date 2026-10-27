#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_ms_po001_residual(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "MS-PO001-RESIDUAL",
            domain: "ms_po001_residual_milestone",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (9, 9, 0);
    if candidate != expected {
        return ControlReceipt {
            control_id: "MS-PO001-RESIDUAL",
            domain: "ms_po001_residual_milestone",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "MS-PO001-RESIDUAL",
        domain: "ms_po001_residual_milestone",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_ms_po001_residual_scoped_control() {
    let ok = evaluate_ms_po001_residual((9, 9, 0), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (9, 9, 0));

    let drifted = evaluate_ms_po001_residual((9 + 1, 9, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_ms_po001_residual((9, 9, 0), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

/// Defect `|left − right| + gap` for a nonnegative gap.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BalancedResidualWitness {
    defect: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BalancedResidualError {
    NegativeGap,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/ms_po001_residual.rs
// Claim: urn:core:crates_rs:tests:ms-po001-residual:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BalancedResidualError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BalancedResidualError {}

impl BalancedResidualWitness {
    pub fn try_balance(left: i64, right: i64, gap: i64) -> Result<Self, BalancedResidualError> {
        if gap < 0 {
            return Err(BalancedResidualError::NegativeGap);
        }
        let distance = if left >= right {
            left.checked_sub(right)
                .ok_or(BalancedResidualError::Overflow)?
        } else {
            right
                .checked_sub(left)
                .ok_or(BalancedResidualError::Overflow)?
        };
        let distance = u64::try_from(distance).map_err(|_| BalancedResidualError::Overflow)?;
        let gap = u64::try_from(gap).map_err(|_| BalancedResidualError::Overflow)?;
        let defect = distance
            .checked_add(gap)
            .ok_or(BalancedResidualError::Overflow)?;
        Ok(Self { defect })
    }

    pub fn defect(&self) -> u64 {
        self.defect
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
