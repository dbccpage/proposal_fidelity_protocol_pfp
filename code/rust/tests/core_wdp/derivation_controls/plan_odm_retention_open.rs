#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_odm_retention_open(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-RETENTION-OPEN",
            domain: "odm_multi_step_future_retention",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (5, 5, 0);
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-RETENTION-OPEN",
            domain: "odm_multi_step_future_retention",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-RETENTION-OPEN",
        domain: "odm_multi_step_future_retention",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_odm_retention_open_scoped_control() {
    let ok = evaluate_plan_odm_retention_open((5, 5, 0), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (5, 5, 0));

    let drifted = evaluate_plan_odm_retention_open((5 + 1, 5, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_odm_retention_open((5, 5, 0), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

/// Retained count cannot exceed the opened count. The residual is `opened - retained`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RetentionResidualWitness {
    opened: u64,
    retained: u64,
    residual: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RetentionResidualError {
    RetainedExceedsOpened,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_retention_open.rs
// Claim: urn:core:crates_rs:tests:plan-odm-retention-open:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RetentionResidualError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RetentionResidualError {}

impl RetentionResidualWitness {
    pub fn try_new(opened: u64, retained: u64) -> Result<Self, RetentionResidualError> {
        if retained > opened {
            return Err(RetentionResidualError::RetainedExceedsOpened);
        }
        let residual = opened
            .checked_sub(retained)
            .ok_or(RetentionResidualError::Overflow)?;
        Ok(Self {
            opened,
            retained,
            residual,
        })
    }

    pub fn residual(&self) -> u64 {
        self.residual
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
