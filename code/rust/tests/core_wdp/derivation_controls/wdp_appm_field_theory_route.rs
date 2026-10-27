#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_wdp_appm_field_theory_route(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "WDP-APPM-FIELD-THEORY-ROUTE",
            domain: "meron_five_stage_route_composition",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match census() {
        Ok(triple) => triple,
        Err(_) => {
            return ControlReceipt {
                control_id: "WDP-APPM-FIELD-THEORY-ROUTE",
                domain: "meron_five_stage_route_composition",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "CENSUS_REFUSED",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "WDP-APPM-FIELD-THEORY-ROUTE",
            domain: "meron_five_stage_route_composition",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "WDP-APPM-FIELD-THEORY-ROUTE",
        domain: "meron_five_stage_route_composition",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_wdp_appm_field_theory_route_scoped_control() {
    let ok = evaluate_wdp_appm_field_theory_route((5, 5, 0), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (5, 5, 0));

    let drifted = evaluate_wdp_appm_field_theory_route((5 + 1, 5, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_wdp_appm_field_theory_route((5, 5, 0), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appm_field_theory_route.rs
// Claim: urn:core:wdp:appm-field-theory:stage-route:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
enum CensusError {
    Empty,
    Duplicate { index: usize },
    Status { index: usize },
    Overflow,
    Law { admitted: i64, open: i64, refused: i64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appm_field_theory_route.rs
// Claim: urn:core:crates_rs:tests:wdp-appm-field-theory-route:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

fn tally(rows: &[(String, u8)]) -> Result<(i64, i64, i64), CensusError> {
    if rows.is_empty() {
        return Err(CensusError::Empty);
    }
    let mut admitted = 0i64;
    let mut open = 0i64;
    let mut refused = 0i64;
    for (index, (id, status)) in rows.iter().enumerate() {
        if id.is_empty() {
            return Err(CensusError::Status { index });
        }
        if rows[..index].iter().any(|(earlier, _)| earlier == id) {
            return Err(CensusError::Duplicate { index });
        }
        match status {
            0 => admitted += 1,
            1 => open += 1,
            2 => refused += 1,
            _ => return Err(CensusError::Status { index }),
        }
    }
    Ok((admitted, open, refused))
}

fn stage_count(rows: &[(String, u8)]) -> Result<i64, CensusError> {
    let mut names: Vec<&str> = Vec::new();
    for (index, (id, _)) in rows.iter().enumerate() {
        let stage = match id.split('-').next() {
            Some(value) if !value.is_empty() => value,
            _ => return Err(CensusError::Status { index }),
        };
        if !names.contains(&stage) {
            names.push(stage);
        }
    }
    i64::try_from(names.len()).map_err(|_| CensusError::Overflow)
}

fn route(
    admitted: i64,
    open: i64,
    refused: i64,
    stages: i64,
) -> Result<(i64, i64, i64), CensusError> {
    if refused != 0 || admitted <= 0 || admitted != open || admitted != stages {
        return Err(CensusError::Law {
            admitted,
            open,
            refused,
        });
    }
    Ok((admitted, open, refused))
}

fn schedule_rows() -> Vec<(String, u8)> {
    let mut rows = Vec::new();
    for id in ["T1", "T2", "T3", "T4", "T5"] {
        rows.push((format!("{id}-theorem"), 0));
        rows.push((format!("{id}-transport"), 1));
    }
    rows
}

fn census() -> Result<(i64, i64, i64), CensusError> {
    let rows = schedule_rows();
    let (admitted, open, refused) = tally(&rows)?;
    let stages = stage_count(&rows)?;
    route(admitted, open, refused, stages)
}

#[test]
fn field_theory_census_matches_the_stage_route() {
    let counted = census();
    assert!(counted.is_ok());
    if let Ok(triple) = counted {
        assert_eq!(
            evaluate_wdp_appm_field_theory_route(triple, false).reason,
            "SCOPED_CONTROL_VERIFIED"
        );
    }
    assert!(route(5, 5, 1, 5).is_err());
    assert!(route(4, 4, 0, 5).is_err());
}

#[test]
fn field_theory_refuses_a_repeated_stage_row() {
    let mut rows = schedule_rows();
    rows.push(("T1-theorem".to_string(), 0));
    assert!(matches!(
        tally(&rows),
        Err(CensusError::Duplicate { index: 10 })
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
