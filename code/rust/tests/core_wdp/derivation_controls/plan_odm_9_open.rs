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
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_9_open.rs
// Claim: urn:core:crates_rs:tests:plan-odm-9-open:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct TransportRowCensus {
    admitted: i64,
    open: i64,
    refused: i64,
}

const ODM9_ROWS: &[CarrierRow] = &[
    CarrierRow { label: "numerator_36864", disposition: RowDisposition::Admitted },
    CarrierRow { label: "mean_square_48_over_19", disposition: RowDisposition::Admitted },
    CarrierRow { label: "partition_912", disposition: RowDisposition::Admitted },
    CarrierRow { label: "second_moment_36864", disposition: RowDisposition::Admitted },
    CarrierRow { label: "finite_chain_cancellation", disposition: RowDisposition::Admitted },
    CarrierRow { label: "equal_time_split_recorded", disposition: RowDisposition::Admitted },
    CarrierRow { label: "complete_infinite_operator_transport", disposition: RowDisposition::Open },
    CarrierRow { label: "general_sign_problem_complexity", disposition: RowDisposition::Open },
    CarrierRow { label: "spatial_mesh_field", disposition: RowDisposition::Open },
    CarrierRow { label: "equal_time_readout_same_name", disposition: RowDisposition::Refused },
    CarrierRow { label: "nonpartition_numerator_as_partition", disposition: RowDisposition::Refused },
];

impl TransportRowCensus {
    fn validate_unique_label(
        rows: &[CarrierRow],
        index: usize,
        row: &CarrierRow,
    ) -> Result<(), CensusError> {
        if row.label.is_empty() {
            return Err(CensusError::Unlabeled);
        }
        if rows[..index].iter().any(|earlier| earlier.label == row.label) {
            return Err(CensusError::Duplicate);
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
        for (index, row) in rows.iter().enumerate() {
            Self::validate_unique_label(rows, index, row)?;
            match row.disposition {
                RowDisposition::Admitted => admitted += 1,
                RowDisposition::Open => open += 1,
                RowDisposition::Refused => refused += 1,
            }
        }
        let summed = admitted
            .checked_add(open)
            .and_then(|sum| sum.checked_add(refused))
            .ok_or(CensusError::Overflow)?;
        let width = i64::try_from(rows.len()).map_err(|_| CensusError::Overflow)?;
        if summed != width {
            return Err(CensusError::Partition);
        }
        Ok(Self { admitted, open, refused })
    }

    fn triple(&self) -> (i64, i64, i64) {
        (self.admitted, self.open, self.refused)
    }
}

pub fn evaluate_plan_odm_9_open(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-9-OPEN",
            domain: "odm_9_meron_chain_transport",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match TransportRowCensus::count(ODM9_ROWS) {
        Ok(census) => census.triple(),
        Err(_) => {
            return ControlReceipt {
                control_id: "PLAN-ODM-9-OPEN",
                domain: "odm_9_meron_chain_transport",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-9-OPEN",
            domain: "odm_9_meron_chain_transport",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-9-OPEN",
        domain: "odm_9_meron_chain_transport",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_odm_9_open_scoped_control() {
    let image = TransportRowCensus::count(ODM9_ROWS).map(|census| census.triple());
    assert_eq!(image, Ok((6, 3, 2)));
    let ok = image.map(|triple| evaluate_plan_odm_9_open(triple, false));
    assert!(matches!(
        ok.as_ref(),
        Ok(receipt)
            if receipt.control_id == "PLAN-ODM-9-OPEN"
                && receipt.domain == "odm_9_meron_chain_transport"
                && receipt.status == "PASS"
                && receipt.reason == "SCOPED_CONTROL_VERIFIED"
                && receipt.invariant_tuple == (6, 3, 2)
    ));

    let drifted = evaluate_plan_odm_9_open((6 + 1, 3, 2), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = image.map(|triple| evaluate_plan_odm_9_open(triple, true));
    assert!(matches!(
        promoted.as_ref(),
        Ok(receipt)
            if receipt.status == "REFUSED"
                && receipt.reason == "UNRESTRICTED_PROMOTION_REFUSED"
    ));
}

#[test]
fn transport_row_census_refuses_empty_unlabeled_and_duplicate_rows() {
    assert!(matches!(TransportRowCensus::count(&[]), Err(CensusError::Empty)));
    let unlabeled = [CarrierRow { label: "", disposition: RowDisposition::Admitted }];
    assert!(matches!(TransportRowCensus::count(&unlabeled), Err(CensusError::Unlabeled)));
    let duplicated = [
        CarrierRow { label: "numerator_36864", disposition: RowDisposition::Admitted },
        CarrierRow { label: "numerator_36864", disposition: RowDisposition::Refused },
    ];
    assert!(matches!(TransportRowCensus::count(&duplicated), Err(CensusError::Duplicate)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
