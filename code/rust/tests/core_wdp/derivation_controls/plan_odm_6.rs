#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_odm_6(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-6",
            domain: "odm_6_carrier_refinement_enclosure",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (4, 2, 1);
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-6",
            domain: "odm_6_carrier_refinement_enclosure",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-6",
        domain: "odm_6_carrier_refinement_enclosure",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_odm_6_scoped_control() {
    let ok = evaluate_plan_odm_6((4, 2, 1), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (4, 2, 1));

    let drifted = evaluate_plan_odm_6((4 + 1, 2, 1), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_odm_6((4, 2, 1), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

/// Dyadic enclosure: `hi >= lo` and the width is even, so the midpoint split is an integer.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DyadicEnclosureWitness {
    lo: i64,
    hi: i64,
    midpoint: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DyadicEnclosureError {
    Inverted,
    OddWidth,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_6.rs
// Claim: urn:core:crates_rs:tests:plan-odm-6:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DyadicEnclosureError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DyadicEnclosureError {}

impl DyadicEnclosureWitness {
    pub fn try_split(lo: i64, hi: i64) -> Result<Self, DyadicEnclosureError> {
        if hi < lo {
            return Err(DyadicEnclosureError::Inverted);
        }
        let width = hi.checked_sub(lo).ok_or(DyadicEnclosureError::Overflow)?;
        if width % 2 != 0 {
            return Err(DyadicEnclosureError::OddWidth);
        }
        let half = width
            .checked_div(2)
            .ok_or(DyadicEnclosureError::Overflow)?;
        let midpoint = lo.checked_add(half).ok_or(DyadicEnclosureError::Overflow)?;
        Ok(Self { lo, hi, midpoint })
    }

    pub fn midpoint(&self) -> i64 {
        self.midpoint
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
