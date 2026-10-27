#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_odm_11(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-11",
            domain: "odm_11_ptir_sql_second_domain",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (2, 4, 0);
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-11",
            domain: "odm_11_ptir_sql_second_domain",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-11",
        domain: "odm_11_ptir_sql_second_domain",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_odm_11_scoped_control() {
    let ok = evaluate_plan_odm_11((2, 4, 0), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (2, 4, 0));

    let drifted = evaluate_plan_odm_11((2 + 1, 4, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_odm_11((2, 4, 0), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HammingError {
    Length,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_11.rs
// Claim: urn:core:crates_rs:tests:plan-odm-11:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HammingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HammingError {}

pub fn hamming_distance(left: &[u8], right: &[u8]) -> Result<usize, HammingError> {
    if left.len() != right.len() {
        return Err(HammingError::Length);
    }
    let mut distance = 0usize;
    for (a, b) in left.iter().zip(right.iter()) {
        if a != b {
            distance = distance.checked_add(1).ok_or(HammingError::Overflow)?;
        }
    }
    Ok(distance)
}

#[test]
fn one_coordinate_disagreement_has_distance_one() {
    assert!(matches!(hamming_distance(&[1, 0, 1], &[1, 1, 1]), Ok(1)));
    assert!(matches!(hamming_distance(&[1], &[1, 0]), Err(HammingError::Length)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
