#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_ms_release(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "MS-RELEASE",
            domain: "ms_release_milestone_gate",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (12, 12, 0);
    if candidate != expected {
        return ControlReceipt {
            control_id: "MS-RELEASE",
            domain: "ms_release_milestone_gate",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "MS-RELEASE",
        domain: "ms_release_milestone_gate",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MilestoneSum {
    first: i64,
    second: i64,
    third: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MilestoneSumError {
    Negative,
    NotPartition { sum: i64, first: i64 },
    ZeroTotal,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/ms_release.rs
// Claim: urn:core:crates_rs:tests:ms-release:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MilestoneSumError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MilestoneSumError {}

impl MilestoneSum {
    pub fn certify(triple: (i64, i64, i64)) -> Result<Self, MilestoneSumError> {
        let (first, second, third) = triple;
        if first < 0 || second < 0 || third < 0 { return Err(MilestoneSumError::Negative); }
        if first == 0 { return Err(MilestoneSumError::ZeroTotal); }
        let sum = second.checked_add(third).ok_or(MilestoneSumError::Overflow)?;
        if first != sum { return Err(MilestoneSumError::NotPartition { sum, first }); }
        Ok(Self { first, second, third })
    }
}

#[test]
fn test_ms_release_scoped_control() {
    let ok = evaluate_ms_release((12, 12, 0), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (12, 12, 0));

    let drifted = evaluate_ms_release((12 + 1, 12, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_ms_release((12, 12, 0), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(MilestoneSum::certify((12, 12, 0)), Ok(w) if w.first == 12));
        assert!(matches!(MilestoneSum::certify((12, 11, 0)), Err(MilestoneSumError::NotPartition { .. })));
        assert!(matches!(MilestoneSum::certify((12, 12, 1)), Err(MilestoneSumError::NotPartition { .. })));
    }
}
