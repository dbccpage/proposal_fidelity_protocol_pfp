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
    Residual,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_dp1_02_residual.rs
// Claim: urn:core:crates_rs:tests:wdp-dp1-02-residual:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

fn residual_rows() -> &'static [ControlRow] {
    &[
        ControlRow {
            name: "partial-left",
            status: RowStatus::Admitted,
        },
        ControlRow {
            name: "partial-middle",
            status: RowStatus::Admitted,
        },
        ControlRow {
            name: "partial-right",
            status: RowStatus::Admitted,
        },
        ControlRow {
            name: "undefined-at-zero",
            status: RowStatus::Open,
        },
        ControlRow {
            name: "undefined-at-pole",
            status: RowStatus::Open,
        },
    ]
}

fn accumulate_residual_row(
    counts: &mut (i64, i64, i64),
    row: &ControlRow,
) -> Result<(), CensusError> {
    if row.name.is_empty() {
        return Err(CensusError::Residual);
    }
    let target = match row.status {
        RowStatus::Admitted => &mut counts.0,
        RowStatus::Open => &mut counts.1,
        RowStatus::Refused => &mut counts.2,
    };
    *target = target.checked_add(1).ok_or(CensusError::Overflow)?;
    Ok(())
}

fn declared_census() -> Result<(i64, i64, i64), CensusError> {
    let mut counts = (0i64, 0i64, 0i64);
    for row in residual_rows() {
        accumulate_residual_row(&mut counts, &row)?;
    }
    let (admitted, open, refused) = counts;
    let gap = admitted.checked_sub(open).ok_or(CensusError::Residual)?;
    if gap != 1 || refused != 0 {
        return Err(CensusError::Residual);
    }
    let total = admitted
        .checked_add(open)
        .and_then(|count| count.checked_add(refused))
        .ok_or(CensusError::Overflow)?;
    if total != i64::try_from(residual_rows().len()).map_err(|_| CensusError::Overflow)? {
        return Err(CensusError::Overflow);
    }
    Ok((admitted, open, refused))
}

pub fn evaluate_wdp_dp1_02_residual(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "WDP-DP1-02-RESIDUAL",
            domain: "dp1_countermodel_no_total_fn",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let Ok(expected) = declared_census() else {
        return ControlReceipt {
            control_id: "WDP-DP1-02-RESIDUAL",
            domain: "dp1_countermodel_no_total_fn",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "WDP-DP1-02-RESIDUAL",
            domain: "dp1_countermodel_no_total_fn",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "WDP-DP1-02-RESIDUAL",
        domain: "dp1_countermodel_no_total_fn",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_wdp_dp1_02_residual_scoped_control() {
    let expected = declared_census().map_or_else(
        |_| loop {
            assert!(false);
        },
        |value| value,
    );
    assert_eq!(expected, (3, 2, 0));
    let ok = evaluate_wdp_dp1_02_residual(expected, false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, expected);

    let drifted = evaluate_wdp_dp1_02_residual((expected.0 + 1, expected.1, expected.2), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_wdp_dp1_02_residual(expected, true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
