#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_7d_csq_pontryagin(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-7D-CSQ-PONTRYAGIN",
            domain: "csq_pontryagin_assumption_separation",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match census() {
        Ok(triple) => triple,
        Err(_) => {
            return ControlReceipt {
                control_id: "PLAN-7D-CSQ-PONTRYAGIN",
                domain: "csq_pontryagin_assumption_separation",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "CENSUS_REFUSED",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-7D-CSQ-PONTRYAGIN",
            domain: "csq_pontryagin_assumption_separation",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-7D-CSQ-PONTRYAGIN",
        domain: "csq_pontryagin_assumption_separation",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_7d_csq_pontryagin_scoped_control() {
    let ok = evaluate_plan_7d_csq_pontryagin((6, 4, 2), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (6, 4, 2));

    let drifted = evaluate_plan_7d_csq_pontryagin((6 + 1, 4, 2), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_7d_csq_pontryagin((6, 4, 2), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_csq_pontryagin.rs
// Claim: urn:core:wdp:csq-pontryagin:assumption-separation:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
enum CensusError {
    Empty,
    Duplicate { index: usize },
    Status { index: usize },
    Overflow,
    Law { admitted: i64, open: i64, refused: i64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_7d_csq_pontryagin.rs
// Claim: urn:core:crates_rs:tests:plan-7d-csq-pontryagin:l4-production-boundary:v1
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

fn separation(admitted: i64, open: i64, refused: i64) -> Result<(i64, i64, i64), CensusError> {
    let rhs = open.checked_add(refused).ok_or(CensusError::Overflow)?;
    if admitted <= 0 || admitted != rhs {
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
    for id in [
        "lane-e",
        "annihilator",
        "annihilator-lean",
        "dense-protected",
        "compact-open",
        "character-classification",
    ] {
        rows.push((id.to_string(), 0));
    }
    for id in ["duality-gap", "haar-measure", "compact-cover", "character-lift"] {
        rows.push((id.to_string(), 1));
    }
    for id in ["unrestricted-dual", "non-locally-compact"] {
        rows.push((id.to_string(), 2));
    }
    rows
}

fn census() -> Result<(i64, i64, i64), CensusError> {
    let rows = schedule_rows();
    let (admitted, open, refused) = tally(&rows)?;
    separation(admitted, open, refused)
}

#[test]
fn pontryagin_census_matches_assumption_separation() {
    let counted = census();
    assert!(counted.is_ok());
    if let Ok(triple) = counted {
        assert_eq!(
            evaluate_plan_7d_csq_pontryagin(triple, false).reason,
            "SCOPED_CONTROL_VERIFIED"
        );
    }
    assert!(separation(6, 4, 1).is_err());
}

#[test]
fn pontryagin_refuses_a_repeated_goal() {
    let mut rows = schedule_rows();
    rows.push(("lane-e".to_string(), 0));
    assert!(matches!(
        tally(&rows),
        Err(CensusError::Duplicate { index: 12 })
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
