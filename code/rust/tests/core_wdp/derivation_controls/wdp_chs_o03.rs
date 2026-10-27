#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_wdp_chs_o03(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "WDP-CHS-O03",
            domain: "appendix_s_game_checker_parity",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match census() {
        Ok(triple) => triple,
        Err(_) => {
            return ControlReceipt {
                control_id: "WDP-CHS-O03",
                domain: "appendix_s_game_checker_parity",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "CENSUS_REFUSED",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "WDP-CHS-O03",
            domain: "appendix_s_game_checker_parity",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "WDP-CHS-O03",
        domain: "appendix_s_game_checker_parity",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_wdp_chs_o03_scoped_control() {
    let ok = evaluate_wdp_chs_o03((2, 1, 4), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (2, 1, 4));

    let drifted = evaluate_wdp_chs_o03((2 + 1, 1, 4), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_wdp_chs_o03((2, 1, 4), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_chs_o03.rs
// Claim: urn:core:wdp:chs-o03:checker-parity:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
enum CensusError {
    Empty,
    Duplicate { index: usize },
    Status { index: usize },
    Overflow,
    Law { admitted: i64, open: i64, refused: i64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_chs_o03.rs
// Claim: urn:core:crates_rs:tests:wdp-chs-o03:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

fn tally_row(
    counts: &mut (i64, i64, i64),
    rows: &[(String, u8)],
    index: usize,
    id: &str,
    status: u8,
) -> Result<(), CensusError> {
    if id.is_empty() {
        return Err(CensusError::Status { index });
    }
    if rows[..index].iter().any(|(earlier, _)| earlier == id) {
        return Err(CensusError::Duplicate { index });
    }
    let target = match status {
        0 => &mut counts.0,
        1 => &mut counts.1,
        2 => &mut counts.2,
        _ => return Err(CensusError::Status { index }),
    };
    *target = target.checked_add(1).ok_or(CensusError::Overflow)?;
    Ok(())
}

fn tally(rows: &[(String, u8)]) -> Result<(i64, i64, i64), CensusError> {
    if rows.is_empty() {
        return Err(CensusError::Empty);
    }
    let mut counts = (0i64, 0i64, 0i64);
    for (index, (id, status)) in rows.iter().enumerate() {
        tally_row(&mut counts, rows, index, id, *status)?;
    }
    Ok(counts)
}

fn parity(admitted: i64, open: i64, refused: i64) -> Result<(i64, i64, i64), CensusError> {
    if admitted <= 0 || open < 0 || refused < 0 {
        return Err(CensusError::Law {
            admitted,
            open,
            refused,
        });
    }
    let width = open.checked_add(1).ok_or(CensusError::Overflow)?;
    let expected = admitted.checked_mul(width).ok_or(CensusError::Overflow)?;
    if refused != expected {
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
    for id in ["even-parity", "odd-parity"] {
        rows.push((id.to_string(), 0));
    }
    rows.push(("objective".to_string(), 1));
    for id in ["illegal-move-0", "illegal-move-1", "illegal-move-2", "illegal-move-3"] {
        rows.push((id.to_string(), 2));
    }
    rows
}

fn census() -> Result<(i64, i64, i64), CensusError> {
    let rows = schedule_rows();
    let (admitted, open, refused) = tally(&rows)?;
    parity(admitted, open, refused)
}

#[test]
fn checker_parity_census_matches_the_illegal_move_width() {
    let counted = census();
    assert!(counted.is_ok());
    if let Ok(triple) = counted {
        assert_eq!(
            evaluate_wdp_chs_o03(triple, false).reason,
            "SCOPED_CONTROL_VERIFIED"
        );
    }
    assert!(parity(2, 1, 3).is_err());
}

#[test]
fn checker_parity_refuses_a_repeated_class() {
    let mut rows = schedule_rows();
    rows.push(("even-parity".to_string(), 0));
    assert!(matches!(
        tally(&rows),
        Err(CensusError::Duplicate { index: 7 })
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
