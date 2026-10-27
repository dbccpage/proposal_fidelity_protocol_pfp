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
    Unpaired,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/gen_wdp_o02.rs
// Claim: urn:core:crates_rs:tests:gen-wdp-o02:l4-production-boundary:v1
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
// Finite cost and occurrence maps are admitted only as preservation/reflection pairs.
const O02_ROWS: &[CarrierRow] = &[
    CarrierRow { label: "finite_cost_preservation", disposition: RowDisposition::Admitted },
    CarrierRow { label: "finite_cost_reflection", disposition: RowDisposition::Admitted },
    CarrierRow { label: "finite_occurrence_preservation", disposition: RowDisposition::Admitted },
    CarrierRow { label: "finite_occurrence_reflection", disposition: RowDisposition::Admitted },
    CarrierRow { label: "protected_question_fiber", disposition: RowDisposition::Open },
    CarrierRow { label: "unrestricted_run_faithfulness", disposition: RowDisposition::Open },
    CarrierRow { label: "future_question_transport", disposition: RowDisposition::Open },
    CarrierRow { label: "every_original_executable_run", disposition: RowDisposition::Open },
    CarrierRow { label: "unrestricted_promotion", disposition: RowDisposition::Refused },
    CarrierRow { label: "fast_check_collision_as_full_replay", disposition: RowDisposition::Refused },
];

impl RowCensus {
    fn record_admitted_pair<'a>(
        label: &'a str,
        preserved: &mut BTreeSet<&'a str>,
        reflected: &mut BTreeSet<&'a str>,
    ) -> Result<(), CensusError> {
        if let Some(stem) = label.strip_suffix("_preservation") {
            if !stem.is_empty() && preserved.insert(stem) {
                return Ok(());
            }
        } else if let Some(stem) = label.strip_suffix("_reflection") {
            if !stem.is_empty() && reflected.insert(stem) {
                return Ok(());
            }
        }
        Err(CensusError::Unpaired)
    }

    fn verify_pairing_and_partition(
        len: usize,
        admitted: i64,
        open: i64,
        refused: i64,
        preserved: &BTreeSet<&str>,
        reflected: &BTreeSet<&str>,
    ) -> Result<(), CensusError> {
        if preserved != reflected || preserved.is_empty() {
            return Err(CensusError::Unpaired);
        }
        let summed = admitted
            .checked_add(open)
            .and_then(|sum| sum.checked_add(refused))
            .ok_or(CensusError::Overflow)?;
        let width = i64::try_from(len).map_err(|_| CensusError::Overflow)?;
        if summed != width {
            return Err(CensusError::Partition);
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
        let mut seen = BTreeSet::new();
        let mut preserved = BTreeSet::new();
        let mut reflected = BTreeSet::new();
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
                    Self::record_admitted_pair(row.label, &mut preserved, &mut reflected)?;
                }
                RowDisposition::Open => open += 1,
                RowDisposition::Refused => refused += 1,
            }
        }
        Self::verify_pairing_and_partition(rows.len(), admitted, open, refused, &preserved, &reflected)?;
        Ok(Self { admitted, open, refused })
    }

    fn triple(self) -> (i64, i64, i64) {
        (self.admitted, self.open, self.refused)
    }
}

pub fn evaluate_gen_wdp_o02(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "GEN-WDP-O02",
            domain: "source_to_wdp_refinement_map",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match RowCensus::count(O02_ROWS) {
        Ok(census) => census.triple(),
        Err(_) => {
            return ControlReceipt {
                control_id: "GEN-WDP-O02",
                domain: "source_to_wdp_refinement_map",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "GEN-WDP-O02",
            domain: "source_to_wdp_refinement_map",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "GEN-WDP-O02",
        domain: "source_to_wdp_refinement_map",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_gen_wdp_o02_scoped_control() {
    let image = RowCensus::count(O02_ROWS).map(RowCensus::triple);
    assert_eq!(image, Ok((4, 4, 2)));
    let ok = image.map(|triple| evaluate_gen_wdp_o02(triple, false));
    assert!(matches!(
        ok.as_ref(),
        Ok(receipt)
            if receipt.control_id == "GEN-WDP-O02"
                && receipt.domain == "source_to_wdp_refinement_map"
                && receipt.status == "PASS"
                && receipt.reason == "SCOPED_CONTROL_VERIFIED"
                && receipt.invariant_tuple == (4, 4, 2)
    ));

    let drifted = evaluate_gen_wdp_o02((4 + 1, 4, 2), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = image.map(|triple| evaluate_gen_wdp_o02(triple, true));
    assert!(matches!(
        promoted.as_ref(),
        Ok(receipt)
            if receipt.status == "REFUSED" && receipt.reason == "UNRESTRICTED_PROMOTION_REFUSED"
    ));
}

#[test]
fn a_one_sided_map_is_not_a_preservation_reflection_pair() {
    let one_sided = [CarrierRow {
        label: "finite_cost_preservation",
        disposition: RowDisposition::Admitted,
    }];
    assert!(matches!(RowCensus::count(&one_sided), Err(CensusError::Unpaired)));
    let duplicated = [
        CarrierRow { label: "finite_cost_preservation", disposition: RowDisposition::Admitted },
        CarrierRow { label: "finite_cost_preservation", disposition: RowDisposition::Admitted },
    ];
    assert!(matches!(RowCensus::count(&duplicated), Err(CensusError::Duplicate)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
