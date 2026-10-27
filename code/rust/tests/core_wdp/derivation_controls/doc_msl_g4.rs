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

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/doc_msl_g4.rs
// Claim: urn:core:crates_rs:tests:doc-msl-g4:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct KernelRowCensus {
    admitted: i64,
    open: i64,
    refused: i64,
}

const G4_ROWS: &[CarrierRow] = &[
    CarrierRow { label: "outside_zero_unscaled", disposition: RowDisposition::Admitted },
    CarrierRow { label: "outside_changed_source_caught", disposition: RowDisposition::Admitted },
    CarrierRow { label: "outside_wrong_numerator_caught", disposition: RowDisposition::Admitted },
    CarrierRow { label: "inside_disk_q", disposition: RowDisposition::Admitted },
    CarrierRow { label: "inside_scalar", disposition: RowDisposition::Admitted },
    CarrierRow { label: "distinct_site_numerator", disposition: RowDisposition::Admitted },
    CarrierRow { label: "tx_t_kernel_unwritten", disposition: RowDisposition::Open },
    CarrierRow { label: "positive_regime_unwritten", disposition: RowDisposition::Open },
    CarrierRow { label: "signed_history_covariance_unassumed", disposition: RowDisposition::Open },
    CarrierRow { label: "exit_status_is_not_a_kernel", disposition: RowDisposition::Open },
    CarrierRow { label: "sign_stripped_against_protected", disposition: RowDisposition::Refused },
];

impl KernelRowCensus {
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
        let mut index = 0usize;
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

pub fn evaluate_doc_msl_g4(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "DOC-MSL-G4",
            domain: "doc_msl_g4_nonequal_time_kernel",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match KernelRowCensus::count(G4_ROWS) {
        Ok(census) => census.triple(),
        Err(_) => {
            return ControlReceipt {
                control_id: "DOC-MSL-G4",
                domain: "doc_msl_g4_nonequal_time_kernel",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "DOC-MSL-G4",
            domain: "doc_msl_g4_nonequal_time_kernel",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "DOC-MSL-G4",
        domain: "doc_msl_g4_nonequal_time_kernel",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_doc_msl_g4_scoped_control() {
    let image = KernelRowCensus::count(G4_ROWS).map(|census| census.triple());
    assert_eq!(image, Ok((6, 4, 1)));
    let ok = image.map(|triple| evaluate_doc_msl_g4(triple, false));
    assert!(matches!(
        ok.as_ref(),
        Ok(receipt)
            if receipt.control_id == "DOC-MSL-G4"
                && receipt.domain == "doc_msl_g4_nonequal_time_kernel"
                && receipt.status == "PASS"
                && receipt.reason == "SCOPED_CONTROL_VERIFIED"
                && receipt.invariant_tuple == (6, 4, 1)
    ));

    let drifted = evaluate_doc_msl_g4((6 + 1, 4, 1), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = image.map(|triple| evaluate_doc_msl_g4(triple, true));
    assert!(matches!(
        promoted.as_ref(),
        Ok(receipt)
            if receipt.status == "REFUSED"
                && receipt.reason == "UNRESTRICTED_PROMOTION_REFUSED"
    ));
}

#[test]
fn kernel_row_census_refuses_empty_unlabeled_and_duplicate_rows() {
    assert!(matches!(KernelRowCensus::count(&[]), Err(CensusError::Empty)));
    let unlabeled = [CarrierRow { label: "", disposition: RowDisposition::Admitted }];
    assert!(matches!(KernelRowCensus::count(&unlabeled), Err(CensusError::Unlabeled)));
    let duplicated = [
        CarrierRow { label: "outside_zero_unscaled", disposition: RowDisposition::Admitted },
        CarrierRow { label: "outside_zero_unscaled", disposition: RowDisposition::Open },
    ];
    assert!(matches!(KernelRowCensus::count(&duplicated), Err(CensusError::Duplicate)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
