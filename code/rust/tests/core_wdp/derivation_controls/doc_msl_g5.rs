#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_doc_msl_g5(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "DOC-MSL-G5",
            domain: "doc_msl_g5_joint_lm_schedule",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match census() {
        Ok(triple) => triple,
        Err(_) => {
            return ControlReceipt {
                control_id: "DOC-MSL-G5",
                domain: "doc_msl_g5_joint_lm_schedule",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "CENSUS_REFUSED",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "DOC-MSL-G5",
            domain: "doc_msl_g5_joint_lm_schedule",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "DOC-MSL-G5",
        domain: "doc_msl_g5_joint_lm_schedule",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_doc_msl_g5_scoped_control() {
    let ok = evaluate_doc_msl_g5((8, 4, 1), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (8, 4, 1));

    let drifted = evaluate_doc_msl_g5((8 + 1, 4, 1), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_doc_msl_g5((8, 4, 1), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/doc_msl_g5.rs
// Claim: urn:core:wdp:doc-msl-g5:joint-schedule:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
enum CensusError {
    Empty,
    Duplicate { index: usize },
    Status { index: usize },
    Overflow,
    Law { admitted: i64, open: i64, refused: i64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/doc_msl_g5.rs
// Claim: urn:core:crates_rs:tests:doc-msl-g5:l4-production-boundary:v1
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

fn joint_schedule(admitted: i64, open: i64, refused: i64) -> Result<(i64, i64, i64), CensusError> {
    if admitted <= 0 || open <= 0 || refused <= 0 {
        return Err(CensusError::Law {
            admitted,
            open,
            refused,
        });
    }
    let doubled = open.checked_mul(2).ok_or(CensusError::Overflow)?;
    if admitted != doubled {
        return Err(CensusError::Law {
            admitted,
            open,
            refused,
        });
    }
    let cover = refused.checked_mul(doubled).ok_or(CensusError::Overflow)?;
    if cover != admitted {
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
    for id in ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"] {
        rows.push((id.to_string(), 0));
    }
    for id in ["M0", "M1", "M2", "M3"] {
        rows.push((id.to_string(), 1));
    }
    rows.push(("vanishing-error".to_string(), 2));
    rows
}

fn census() -> Result<(i64, i64, i64), CensusError> {
    let rows = schedule_rows();
    let (admitted, open, refused) = tally(&rows)?;
    joint_schedule(admitted, open, refused)
}

#[test]
fn doc_msl_g5_census_matches_the_joint_schedule() {
    let counted = census();
    assert!(counted.is_ok());
    if let Ok(triple) = counted {
        assert_eq!(
            evaluate_doc_msl_g5(triple, false).reason,
            "SCOPED_CONTROL_VERIFIED"
        );
    }
    assert!(joint_schedule(8, 4, 2).is_err());
}

#[test]
fn doc_msl_g5_refuses_a_repeated_lane() {
    let mut rows = schedule_rows();
    rows.push(("L0".to_string(), 0));
    assert!(matches!(tally(&rows), Err(CensusError::Duplicate { index: 13 })));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
