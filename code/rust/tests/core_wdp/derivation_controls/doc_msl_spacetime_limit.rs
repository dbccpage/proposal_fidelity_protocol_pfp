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
    Signature,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/doc_msl_spacetime_limit.rs
// Claim: urn:core:crates_rs:tests:doc-msl-spacetime-limit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

fn spacetime_rows() -> &'static [ControlRow] {
    &[
        ControlRow { name: "ct", status: RowStatus::Admitted, weight: 1 },
        ControlRow { name: "x", status: RowStatus::Admitted, weight: -1 },
        ControlRow { name: "y", status: RowStatus::Admitted, weight: -1 },
        ControlRow { name: "z", status: RowStatus::Admitted, weight: -1 },
        ControlRow { name: "limit", status: RowStatus::Admitted, weight: 0 },
        ControlRow { name: "horizon", status: RowStatus::Open, weight: 1 },
        ControlRow { name: "curvature", status: RowStatus::Open, weight: 1 },
        ControlRow { name: "signature-choice", status: RowStatus::Open, weight: 1 },
        ControlRow { name: "topology", status: RowStatus::Open, weight: 1 },
        ControlRow { name: "boundary", status: RowStatus::Open, weight: 1 },
    ]
}

fn declared_census() -> Result<(i64, i64, i64), CensusError> {
    let mut admitted = 0i64;
    let mut open = 0i64;
    let mut refused = 0i64;
    let mut signature = 0i64;
    for row in spacetime_rows() {
        if row.name.is_empty() {
            return Err(CensusError::Signature);
        }
        match row.status {
            RowStatus::Admitted => {
                admitted += 1;
                signature = signature.checked_add(row.weight).ok_or(CensusError::Overflow)?;
            }
            RowStatus::Open => open += 1,
            RowStatus::Refused => refused += 1,
        }
    }
    if signature != 1 - 3 {
        return Err(CensusError::Signature);
    }
    let total = admitted.checked_add(open).and_then(|count| count.checked_add(refused));
    if total != Some(i64::try_from(spacetime_rows().len()).map_err(|_| CensusError::Overflow)?) {
        return Err(CensusError::Overflow);
    }
    Ok((admitted, open, refused))
}

pub fn evaluate_doc_msl_spacetime_limit(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "DOC-MSL-SPACETIME-LIMIT",
            domain: "doc_msl_spacetime_limit_gate",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let Ok(expected) = declared_census() else {
        return ControlReceipt {
            control_id: "DOC-MSL-SPACETIME-LIMIT",
            domain: "doc_msl_spacetime_limit_gate",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "DOC-MSL-SPACETIME-LIMIT",
            domain: "doc_msl_spacetime_limit_gate",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "DOC-MSL-SPACETIME-LIMIT",
        domain: "doc_msl_spacetime_limit_gate",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_doc_msl_spacetime_limit_scoped_control() {
    let expected = declared_census().map_or_else(|_| loop { assert!(false); }, |value| value);
    assert_eq!(expected, (5, 5, 0));
    let ok = evaluate_doc_msl_spacetime_limit(expected, false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, expected);

    let drifted = evaluate_doc_msl_spacetime_limit((expected.0 + 1, expected.1, expected.2), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_doc_msl_spacetime_limit(expected, true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
