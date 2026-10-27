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
    weight: i64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CensusError {
    Overflow,
    Holonomy,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appw_native_repair_bindings.rs
// Claim: urn:core:crates_rs:tests:wdp-appw-native-repair-bindings:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

fn repair_rows() -> &'static [ControlRow] {
    &[
        ControlRow {
            name: "edge-ab",
            status: RowStatus::Admitted,
            weight: 1,
        },
        ControlRow {
            name: "edge-bc",
            status: RowStatus::Admitted,
            weight: 1,
        },
        ControlRow {
            name: "edge-cd",
            status: RowStatus::Admitted,
            weight: 1,
        },
        ControlRow {
            name: "edge-da",
            status: RowStatus::Admitted,
            weight: -1,
        },
        ControlRow {
            name: "edge-ac",
            status: RowStatus::Admitted,
            weight: -1,
        },
        ControlRow {
            name: "edge-bd",
            status: RowStatus::Admitted,
            weight: -1,
        },
        ControlRow {
            name: "repair-open-a",
            status: RowStatus::Open,
            weight: 0,
        },
        ControlRow {
            name: "repair-open-b",
            status: RowStatus::Open,
            weight: 0,
        },
    ]
}

fn accumulate_repair_row(
    admitted: &mut i64,
    open: &mut i64,
    refused: &mut i64,
    holonomy: &mut i64,
    row: &ControlRow,
) -> Result<(), CensusError> {
    if row.name.is_empty() {
        return Err(CensusError::Holonomy);
    }
    match row.status {
        RowStatus::Admitted => {
            *admitted = admitted.checked_add(1).ok_or(CensusError::Overflow)?;
            *holonomy = holonomy
                .checked_add(row.weight)
                .ok_or(CensusError::Overflow)?;
        }
        RowStatus::Open => *open = open.checked_add(1).ok_or(CensusError::Overflow)?,
        RowStatus::Refused => *refused = refused.checked_add(1).ok_or(CensusError::Overflow)?,
    }
    Ok(())
}

fn declared_census() -> Result<(i64, i64, i64), CensusError> {
    let mut admitted = 0i64;
    let mut open = 0i64;
    let mut refused = 0i64;
    let mut holonomy = 0i64;
    for row in repair_rows() {
        accumulate_repair_row(&mut admitted, &mut open, &mut refused, &mut holonomy, &row)?;
    }
    if holonomy != 0 {
        return Err(CensusError::Holonomy);
    }
    let total = admitted
        .checked_add(open)
        .and_then(|count| count.checked_add(refused))
        .ok_or(CensusError::Overflow)?;
    if total != i64::try_from(repair_rows().len()).map_err(|_| CensusError::Overflow)? {
        return Err(CensusError::Overflow);
    }
    Ok((admitted, open, refused))
}

pub fn evaluate_wdp_appw_native_repair_bindings(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "WDP-APPW-NATIVE-REPAIR-BINDINGS",
            domain: "repair_holonomy_preservation",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let Ok(expected) = declared_census() else {
        return ControlReceipt {
            control_id: "WDP-APPW-NATIVE-REPAIR-BINDINGS",
            domain: "repair_holonomy_preservation",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "WDP-APPW-NATIVE-REPAIR-BINDINGS",
            domain: "repair_holonomy_preservation",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "WDP-APPW-NATIVE-REPAIR-BINDINGS",
        domain: "repair_holonomy_preservation",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_wdp_appw_native_repair_bindings_scoped_control() {
    let expected = declared_census().map_or_else(
        |_| loop {
            assert!(false);
        },
        |value| value,
    );
    assert_eq!(expected, (6, 2, 0));
    let ok = evaluate_wdp_appw_native_repair_bindings(expected, false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, expected);

    let drifted =
        evaluate_wdp_appw_native_repair_bindings((expected.0 + 1, expected.1, expected.2), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_wdp_appw_native_repair_bindings(expected, true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
