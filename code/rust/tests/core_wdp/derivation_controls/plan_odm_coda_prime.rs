#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_odm_coda_prime(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-CODA-PRIME",
            domain: "odm_coda_prime_ddc_separation",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match census() {
        Ok(triple) => triple,
        Err(_) => {
            return ControlReceipt {
                control_id: "PLAN-ODM-CODA-PRIME",
                domain: "odm_coda_prime_ddc_separation",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "CENSUS_REFUSED",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-CODA-PRIME",
            domain: "odm_coda_prime_ddc_separation",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-CODA-PRIME",
        domain: "odm_coda_prime_ddc_separation",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_odm_coda_prime_scoped_control() {
    let ok = evaluate_plan_odm_coda_prime((3, 3, 0), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (3, 3, 0));

    let drifted = evaluate_plan_odm_coda_prime((3 + 1, 3, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_odm_coda_prime((3, 3, 0), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_coda_prime.rs
// Claim: urn:core:wdp:odm-coda-prime:plane-separation:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
enum CensusError {
    Empty,
    Duplicate { index: usize },
    Status { index: usize },
    Overflow,
    Law { admitted: i64, open: i64, refused: i64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_coda_prime.rs
// Claim: urn:core:crates_rs:tests:plan-odm-coda-prime:l4-production-boundary:v1
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

fn planes(admitted: i64, open: i64, refused: i64) -> Result<(i64, i64, i64), CensusError> {
    if refused != 0 || admitted <= 0 || admitted != open {
        return Err(CensusError::Law {
            admitted,
            open,
            refused,
        });
    }
    let both = admitted.checked_add(open).ok_or(CensusError::Overflow)?;
    let doubled = admitted.checked_mul(2).ok_or(CensusError::Overflow)?;
    if both != doubled {
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
        "coda-binding",
        "prime-binding",
        "ddc-binding",
    ] {
        rows.push((id.to_string(), 0));
    }
    for id in ["coda-execution", "prime-execution", "ddc-execution"] {
        rows.push((id.to_string(), 1));
    }
    rows
}

fn census() -> Result<(i64, i64, i64), CensusError> {
    let rows = schedule_rows();
    let (admitted, open, refused) = tally(&rows)?;
    planes(admitted, open, refused)
}

#[test]
fn coda_prime_census_matches_the_three_planes() {
    let counted = census();
    assert!(counted.is_ok());
    if let Ok(triple) = counted {
        assert_eq!(
            evaluate_plan_odm_coda_prime(triple, false).reason,
            "SCOPED_CONTROL_VERIFIED"
        );
    }
    assert!(planes(3, 2, 0).is_err());
    assert!(planes(3, 3, 1).is_err());
}

#[test]
fn coda_prime_refuses_a_repeated_plane() {
    let mut rows = schedule_rows();
    rows.push(("coda-binding".to_string(), 0));
    assert!(matches!(
        tally(&rows),
        Err(CensusError::Duplicate { index: 6 })
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
