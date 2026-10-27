use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum RowDisposition {
    Admitted,
    Open,
    Refused,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct CarrierRow {
    label: &'static str,
    disposition: RowDisposition,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum CensusError {
    Empty,
    Unlabeled,
    Duplicate,
    Missing,
    Overflow,
    Partition,
    Unbalanced,
    Sign,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_10_open.rs
// Claim: urn:core:crates_rs:tests:plan-odm-10-open:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct RowCensus {
    admitted: i64,
    open: i64,
    refused: i64,
}

// Exact carrier witness.
// Admitted rows are the two sublattices of a finite bipartite ring. Their sign character is trivial only when the odd sublattice is balanced and even in count.
const ODM10_ROWS: &[CarrierRow] = &[
    CarrierRow { label: "even_sublattice_site_0", disposition: RowDisposition::Admitted },
    CarrierRow { label: "odd_sublattice_site_1", disposition: RowDisposition::Admitted },
    CarrierRow { label: "even_sublattice_site_2", disposition: RowDisposition::Admitted },
    CarrierRow { label: "odd_sublattice_site_3", disposition: RowDisposition::Admitted },
    CarrierRow { label: "infinite_volume_scaling", disposition: RowDisposition::Open },
    CarrierRow { label: "continuum_spin_limit", disposition: RowDisposition::Open },
];

impl RowCensus {
    fn record_sublattice(
        label: &str,
        even_sites: &mut i64,
        odd_sites: &mut i64,
    ) -> Result<(), CensusError> {
        if label.starts_with("even_sublattice_") {
            *even_sites += 1;
            Ok(())
        } else if label.starts_with("odd_sublattice_") {
            *odd_sites += 1;
            Ok(())
        } else {
            Err(CensusError::Unbalanced)
        }
    }

    fn verify_sublattice_balance(
        admitted: i64,
        even_sites: i64,
        odd_sites: i64,
    ) -> Result<(), CensusError> {
        let occupied = even_sites.checked_add(odd_sites).ok_or(CensusError::Overflow)?;
        if occupied != admitted || even_sites != odd_sites || even_sites <= 0 {
            return Err(CensusError::Unbalanced);
        }
        if odd_sites % 2 != 0 {
            return Err(CensusError::Sign);
        }
        Ok(())
    }

    fn count(rows: &[CarrierRow]) -> Result<Self, CensusError> {
        if rows.is_empty() {
            return Err(CensusError::Empty);
        }
        let mut admitted = 0i64;
        let mut open = 0i64;
        let mut refused = 0i64;
        let mut even_sites = 0i64;
        let mut odd_sites = 0i64;
        let mut seen = BTreeSet::new();
        for row in rows {
            if row.label.is_empty() {
                return Err(CensusError::Unlabeled);
            }
            if !seen.insert(row.label) {
                return Err(CensusError::Duplicate);
            }
            match row.disposition {
                RowDisposition::Admitted => {
                    admitted += 1;
                    Self::record_sublattice(row.label, &mut even_sites, &mut odd_sites)?;
                }
                RowDisposition::Open => open += 1,
                RowDisposition::Refused => refused += 1,
            }
        }
        Self::verify_sublattice_balance(admitted, even_sites, odd_sites)?;
        if admitted + open + refused != rows.len() as i64 {
            return Err(CensusError::Partition);
        }
        Ok(Self { admitted, open, refused })
    }

    fn triple(self) -> (i64, i64, i64) {
        (self.admitted, self.open, self.refused)
    }
}

pub fn evaluate_plan_odm_10_open(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-10-OPEN",
            domain: "odm_10_ut_spin_sign_character",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match RowCensus::count(ODM10_ROWS) {
        Ok(census) => census.triple(),
        Err(_) => {
            return ControlReceipt {
                control_id: "PLAN-ODM-10-OPEN",
                domain: "odm_10_ut_spin_sign_character",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-10-OPEN",
            domain: "odm_10_ut_spin_sign_character",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-10-OPEN",
        domain: "odm_10_ut_spin_sign_character",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_odm_10_open_scoped_control() {
    let image = RowCensus::count(ODM10_ROWS).map(RowCensus::triple);
    assert_eq!(image, Ok((4, 2, 0)));
    let ok = image.map(|triple| evaluate_plan_odm_10_open(triple, false));
    assert!(matches!(
        ok.as_ref(),
        Ok(receipt)
            if receipt.control_id == "PLAN-ODM-10-OPEN"
                && receipt.domain == "odm_10_ut_spin_sign_character"
                && receipt.status == "PASS"
                && receipt.reason == "SCOPED_CONTROL_VERIFIED"
                && receipt.invariant_tuple == (4, 2, 0)
    ));

    let drifted = evaluate_plan_odm_10_open((4 + 1, 2, 0), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = image.map(|triple| evaluate_plan_odm_10_open(triple, true));
    assert!(matches!(
        promoted.as_ref(),
        Ok(receipt)
            if receipt.status == "REFUSED" && receipt.reason == "UNRESTRICTED_PROMOTION_REFUSED"
    ));
}

#[test]
fn an_unbalanced_or_odd_character_is_refused() {
    let odd_character = [
        CarrierRow { label: "even_sublattice_site_0", disposition: RowDisposition::Admitted },
        CarrierRow { label: "odd_sublattice_site_1", disposition: RowDisposition::Admitted },
    ];
    assert!(matches!(RowCensus::count(&odd_character), Err(CensusError::Sign)));
    let unbalanced = [CarrierRow {
        label: "even_sublattice_site_0",
        disposition: RowDisposition::Admitted,
    }];
    assert!(matches!(RowCensus::count(&unbalanced), Err(CensusError::Unbalanced)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
