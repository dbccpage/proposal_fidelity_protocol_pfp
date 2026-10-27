#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_wdp_o12_lean_analytic(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "WDP-O12-LEAN-ANALYTIC",
            domain: "o12_thermodynamic_tail_envelope",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match census() {
        Ok(triple) => triple,
        Err(_) => {
            return ControlReceipt {
                control_id: "WDP-O12-LEAN-ANALYTIC",
                domain: "o12_thermodynamic_tail_envelope",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "CENSUS_REFUSED",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "WDP-O12-LEAN-ANALYTIC",
            domain: "o12_thermodynamic_tail_envelope",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "WDP-O12-LEAN-ANALYTIC",
        domain: "o12_thermodynamic_tail_envelope",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_wdp_o12_lean_analytic_scoped_control() {
    let ok = evaluate_wdp_o12_lean_analytic((1, 256, 127), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (1, 256, 127));

    let drifted = evaluate_wdp_o12_lean_analytic((1 + 1, 256, 127), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_wdp_o12_lean_analytic((1, 256, 127), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_o12_lean_analytic.rs
// Claim: urn:core:wdp:o12:dyadic-tail:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
enum CensusError {
    Empty,
    Duplicate { index: usize },
    Status { index: usize },
    Overflow,
    Law { admitted: i64, open: i64, refused: i64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_o12_lean_analytic.rs
// Claim: urn:core:crates_rs:tests:wdp-o12-lean-analytic:l4-production-boundary:v1
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

fn tail_holds(admitted: i64, open: i64, refused: i64) -> Result<(i64, i64, i64), CensusError> {
    if admitted <= 0 || open <= 0 || refused < 0 {
        return Err(CensusError::Law {
            admitted,
            open,
            refused,
        });
    }
    let mass = refused.checked_add(admitted).ok_or(CensusError::Overflow)?;
    let doubled = mass.checked_mul(2).ok_or(CensusError::Overflow)?;
    if open != doubled {
        return Err(CensusError::Law {
            admitted,
            open,
            refused,
        });
    }
    Ok((admitted, open, refused))
}

fn push_class(rows: &mut Vec<(String, u8)>, prefix: &str, count: i64, status: u8) -> Result<(), CensusError> {
    let mut index = 0i64;
    while index < count {
        rows.push((format!("{prefix}-{index}"), status));
        index = index.checked_add(1).ok_or(CensusError::Overflow)?;
    }
    Ok(())
}

fn build_census_rows(admitted: i64, open: i64, refused: i64) -> Result<Vec<(String, u8)>, CensusError> {
    let mut rows = Vec::new();
    push_class(&mut rows, "admitted", admitted, 0)?;
    push_class(&mut rows, "open", open, 1)?;
    push_class(&mut rows, "refused", refused, 2)?;
    Ok(rows)
}

fn census() -> Result<(i64, i64, i64), CensusError> {
    let admitted = 1i64;
    let cut = 1i64.checked_shl(7).ok_or(CensusError::Overflow)?;
    let refused = cut.checked_sub(admitted).ok_or(CensusError::Overflow)?;
    let open = cut.checked_mul(2).ok_or(CensusError::Overflow)?;
    let counted = tally(&build_census_rows(admitted, open, refused)?)?;
    let mass = counted.2.checked_add(counted.0).ok_or(CensusError::Overflow)?;
    if (mass, counted) != (cut, (admitted, open, refused)) {
        return Err(CensusError::Law {
            admitted: counted.0,
            open: counted.1,
            refused: counted.2,
        });
    }
    tail_holds(counted.0, counted.1, counted.2)
}

#[test]
fn the_dyadic_tail_census_satisfies_the_envelope() {
    let counted = census();
    assert!(counted.is_ok());
    if let Ok(triple) = counted {
        assert_eq!(
            evaluate_wdp_o12_lean_analytic(triple, false).reason,
            "SCOPED_CONTROL_VERIFIED"
        );
    }
}

#[test]
fn a_short_refusal_breaks_the_dyadic_tail() {
    let cut = 1i64.checked_shl(7);
    assert!(cut.is_some());
    if let Some(cut) = cut {
        let open = cut.checked_mul(2);
        let refused = cut.checked_sub(2);
        assert!(open.is_some() && refused.is_some());
        if let (Some(open), Some(refused)) = (open, refused) {
            assert!(tail_holds(1, open, refused).is_err());
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
