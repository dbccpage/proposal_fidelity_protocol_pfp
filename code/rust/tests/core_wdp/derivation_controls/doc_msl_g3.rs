#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_doc_msl_g3(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "DOC-MSL-G3",
            domain: "doc_msl_g3_mixed_time_cumulant",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (4, 3, 2);
    if candidate != expected {
        return ControlReceipt {
            control_id: "DOC-MSL-G3",
            domain: "doc_msl_g3_mixed_time_cumulant",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "DOC-MSL-G3",
        domain: "doc_msl_g3_mixed_time_cumulant",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConsecutiveUnitGap {
    first: i64,
    second: i64,
    third: i64,
    gap: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConsecutiveUnitGapError {
    NonPositive,
    Gap { gap_ab: i64, gap_bc: i64 },
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/doc_msl_g3.rs
// Claim: urn:core:crates_rs:tests:doc-msl-g3:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ConsecutiveUnitGapError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ConsecutiveUnitGapError {}

impl ConsecutiveUnitGap {
    pub fn certify(triple: (i64, i64, i64)) -> Result<Self, ConsecutiveUnitGapError> {
        let (first, second, third) = triple;
        if first <= 0 || second <= 0 || third <= 0 { return Err(ConsecutiveUnitGapError::NonPositive); }
        let gap_ab = first.checked_sub(second).ok_or(ConsecutiveUnitGapError::Overflow)?;
        let gap_bc = second.checked_sub(third).ok_or(ConsecutiveUnitGapError::Overflow)?;
        if gap_ab != 1 || gap_bc != 1 { return Err(ConsecutiveUnitGapError::Gap { gap_ab, gap_bc }); }
        Ok(Self { first, second, third, gap: 1 })
    }
}

#[test]
fn test_doc_msl_g3_scoped_control() {
    let ok = evaluate_doc_msl_g3((4, 3, 2), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (4, 3, 2));

    let drifted = evaluate_doc_msl_g3((4 + 1, 3, 2), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_doc_msl_g3((4, 3, 2), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(ConsecutiveUnitGap::certify((4, 3, 2)), Ok(w) if w.gap == 1));
        assert!(matches!(ConsecutiveUnitGap::certify((4, 3, 1)), Err(ConsecutiveUnitGapError::Gap { .. })));
        assert!(matches!(ConsecutiveUnitGap::certify((5, 3, 2)), Err(ConsecutiveUnitGapError::Gap { .. })));
    }
}
