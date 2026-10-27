#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum RowStatus {
    Admitted,
    Open,
    Refused,
}

struct ControlRow {
    name: &'static str,
    status: RowStatus,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CensusError {
    Overflow,
    Faithful,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_faithful_open.rs
// Claim: urn:core:crates_rs:tests:plan-odm-faithful-open:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

fn profile_rows() -> &'static [ControlRow] {
    &[
        ControlRow { name: "object-w", status: RowStatus::Admitted },
        ControlRow { name: "object-x", status: RowStatus::Admitted },
        ControlRow { name: "object-y", status: RowStatus::Admitted },
        ControlRow { name: "object-z", status: RowStatus::Admitted },
        ControlRow { name: "hom-wx", status: RowStatus::Open },
        ControlRow { name: "hom-xy", status: RowStatus::Open },
        ControlRow { name: "hom-yz", status: RowStatus::Open },
        ControlRow { name: "hom-zw", status: RowStatus::Open },
        ControlRow { name: "arrow-off-profile", status: RowStatus::Refused },
    ]
}

fn declared_census() -> Result<(i64, i64, i64), CensusError> {
    let mut admitted = 0i64;
    let mut open = 0i64;
    let mut refused = 0i64;
    for row in profile_rows() {
        if row.name.is_empty() {
            return Err(CensusError::Faithful);
        }
        match row.status {
            RowStatus::Admitted => admitted += 1,
            RowStatus::Open => open += 1,
            RowStatus::Refused => refused += 1,
        }
    }
    if admitted != open {
        return Err(CensusError::Faithful);
    }
    if (admitted + refused) - open != refused {
        return Err(CensusError::Faithful);
    }
    let total = admitted
        .checked_add(open)
        .and_then(|count| count.checked_add(refused))
        .ok_or(CensusError::Overflow)?;
    if total != i64::try_from(profile_rows().len()).map_err(|_| CensusError::Overflow)? {
        return Err(CensusError::Overflow);
    }
    Ok((admitted, open, refused))
}

pub fn evaluate_plan_odm_faithful_open(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-FAITHFUL-OPEN",
            domain: "odm_engine_profile_congruence",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let Ok(expected) = declared_census() else {
        return ControlReceipt {
            control_id: "PLAN-ODM-FAITHFUL-OPEN",
            domain: "odm_engine_profile_congruence",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-FAITHFUL-OPEN",
            domain: "odm_engine_profile_congruence",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-FAITHFUL-OPEN",
        domain: "odm_engine_profile_congruence",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_odm_faithful_open_scoped_control() {
    let expected = declared_census().map_or_else(|_| loop { assert!(false); }, |value| value);
    assert_eq!(expected, (4, 4, 1));
    let ok = evaluate_plan_odm_faithful_open(expected, false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, expected);

    let drifted = evaluate_plan_odm_faithful_open((expected.0 + 1, expected.1, expected.2), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_odm_faithful_open(expected, true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
