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
    stage: i64,
    status: RowStatus,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CensusError {
    Overflow,
    Triangle,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_sg_catalog.rs
// Claim: urn:core:crates_rs:tests:plan-7d-sg-catalog:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

const OPEN_STAGES: [i64; 9] = [3, 7, 12, 18, 24, 31, 37, 44, 49];

fn catalog_rows() -> Result<Vec<ControlRow>, CensusError> {
    let mut rows = Vec::new();
    let mut stage = 1i64;
    while stage <= 50 {
        rows.push(ControlRow { stage, status: RowStatus::Admitted });
        stage = stage.checked_add(1).ok_or(CensusError::Overflow)?;
    }
    for stage in OPEN_STAGES {
        if !(1..=50).contains(&stage) {
            return Err(CensusError::Triangle);
        }
        rows.push(ControlRow { stage, status: RowStatus::Open });
    }
    Ok(rows)
}

fn verify_triangle_stage_sum(admitted: i64, stage_sum: i64) -> Result<(), CensusError> {
    let successor = admitted.checked_add(1).ok_or(CensusError::Overflow)?;
    let twice = admitted.checked_mul(successor).ok_or(CensusError::Overflow)?;
    if twice % 2 != 0 || stage_sum != twice / 2 {
        return Err(CensusError::Triangle);
    }
    Ok(())
}

fn declared_census() -> Result<(i64, i64, i64), CensusError> {
    let rows = catalog_rows()?;
    let mut admitted = 0i64;
    let mut open = 0i64;
    let mut refused = 0i64;
    let mut stage_sum = 0i64;
    for row in &rows {
        match row.status {
            RowStatus::Admitted => {
                admitted += 1;
                stage_sum = stage_sum.checked_add(row.stage).ok_or(CensusError::Overflow)?;
            }
            RowStatus::Open => open += 1,
            RowStatus::Refused => refused += 1,
        }
    }
    verify_triangle_stage_sum(admitted, stage_sum)?;
    let total = admitted
        .checked_add(open)
        .and_then(|count| count.checked_add(refused))
        .ok_or(CensusError::Overflow)?;
    if total != i64::try_from(rows.len()).map_err(|_| CensusError::Overflow)? {
        return Err(CensusError::Overflow);
    }
    Ok((admitted, open, refused))
}

pub fn evaluate_plan_7d_sg_catalog(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-7D-SG-CATALOG",
            domain: "sg50_stage_reporting_control",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let Ok(expected) = declared_census() else {
        return ControlReceipt {
            control_id: "PLAN-7D-SG-CATALOG",
            domain: "sg50_stage_reporting_control",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-7D-SG-CATALOG",
            domain: "sg50_stage_reporting_control",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-7D-SG-CATALOG",
        domain: "sg50_stage_reporting_control",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_7d_sg_catalog_scoped_control() {
    let expected = declared_census().map_or_else(|_| loop { assert!(false); }, |value| value);
    assert_eq!(expected, (50, 9, 0));
    let ok = evaluate_plan_7d_sg_catalog(expected, false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, expected);

    let drifted = evaluate_plan_7d_sg_catalog((expected.0 + 1, expected.1, expected.2), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_7d_sg_catalog(expected, true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
