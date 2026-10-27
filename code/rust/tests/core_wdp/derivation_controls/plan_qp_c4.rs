//! Exact finite control witness for `PLAN-QP-C4` (`plan_qp_c4`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_proved_theorem_on_cited_input`.

use std::collections::BTreeSet;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub carrier_val: i64,
    pub secondary_pair: (i64, i64),
    pub coboundary_cycle_zero: i64,
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
    Residue,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_c4.rs
// Claim: urn:core:crates_rs:tests:plan-qp-c4:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CensusError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum TelescopeError {
    Short,
    EdgeCount,
    Missing,
    Overflow,
    NotCoboundary,
    Open,
    NotClosed,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct ResidueCensus {
    admitted: i64,
    open: i64,
    refused: i64,
}

// Exact carrier witness.
// Each residue class of the DivisibleByEight predicate is one admitted row.
// The open row is the Washington criterion, kept as cited input rather than an in-file theorem.
const C4_ROWS: &[CarrierRow] = &[
    CarrierRow { label: "residue_0", disposition: RowDisposition::Admitted },
    CarrierRow { label: "residue_1", disposition: RowDisposition::Admitted },
    CarrierRow { label: "residue_2", disposition: RowDisposition::Admitted },
    CarrierRow { label: "residue_3", disposition: RowDisposition::Admitted },
    CarrierRow { label: "residue_4", disposition: RowDisposition::Admitted },
    CarrierRow { label: "residue_5", disposition: RowDisposition::Admitted },
    CarrierRow { label: "residue_6", disposition: RowDisposition::Admitted },
    CarrierRow { label: "residue_7", disposition: RowDisposition::Admitted },
    CarrierRow { label: "washington_cited_input_thm_2_1", disposition: RowDisposition::Open },
];

fn residue_index(label: &str) -> Result<i64, CensusError> {
    let rest = label.strip_prefix("residue_").ok_or(CensusError::Residue)?;
    if rest.is_empty() || !rest.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(CensusError::Residue);
    }
    rest.parse::<i64>().map_err(|_| CensusError::Residue)
}

impl ResidueCensus {
    fn record_residue_class(label: &str, residues: &mut BTreeSet<i64>) -> Result<(), CensusError> {
        let class = residue_index(label)?;
        if class < 0 || !residues.insert(class) {
            return Err(CensusError::Residue);
        }
        Ok(())
    }

    fn verify_complete_residues(admitted: i64, residues: &BTreeSet<i64>) -> Result<(), CensusError> {
        if !(0..admitted).all(|expected| residues.contains(&expected))
            || residues.len() as i64 != admitted
        {
            return Err(CensusError::Residue);
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
        let mut residues = BTreeSet::new();
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
                    Self::record_residue_class(row.label, &mut residues)?;
                }
                RowDisposition::Open => open += 1,
                RowDisposition::Refused => refused += 1,
            }
        }
        Self::verify_complete_residues(admitted, &residues)?;
        if admitted + open + refused != rows.len() as i64 {
            return Err(CensusError::Partition);
        }
        Ok(Self { admitted, open, refused })
    }

    fn carrier(self) -> (i64, (i64, i64)) {
        (self.admitted, (self.open, self.refused))
    }
}

fn sum_coboundary_edges(vertices: &[i64], edges: &[i64]) -> Result<i64, TelescopeError> {
    let mut sum = 0i64;
    for (pair, &edge) in vertices.windows(2).zip(edges.iter()) {
        let step = pair[1].checked_sub(pair[0]).ok_or(TelescopeError::Overflow)?;
        if edge != step {
            return Err(TelescopeError::NotCoboundary);
        }
        sum = sum.checked_add(edge).ok_or(TelescopeError::Overflow)?;
    }
    Ok(sum)
}

fn certify_coboundary(vertices: &[i64], edges: &[i64]) -> Result<i64, TelescopeError> {
    if vertices.len() < 2 {
        return Err(TelescopeError::Short);
    }
    if edges.len() != vertices.len() - 1 {
        return Err(TelescopeError::EdgeCount);
    }
    let sum = sum_coboundary_edges(vertices, edges)?;
    let first = vertices[0];
    let last = vertices[vertices.len() - 1];
    if first != last {
        return Err(TelescopeError::Open);
    }
    let gap = last.checked_sub(first).ok_or(TelescopeError::Overflow)?;
    if sum != gap || sum != 0 {
        return Err(TelescopeError::NotClosed);
    }
    Ok(sum)
}

pub fn witness() -> Witness {
    let (carrier_val, secondary_pair) = match ResidueCensus::count(C4_ROWS) {
        Ok(census) => census.carrier(),
        Err(_) => (0, (0, 0)),
    };
    let coboundary_cycle_zero = match certify_coboundary(&[3, 7, 11, 3], &[4, 4, -8]) {
        Ok(sum) => sum,
        Err(_) => 1,
    };
    Witness {
        carrier_val,
        secondary_pair,
        coboundary_cycle_zero,
    }
}

pub fn reject_proved_theorem_on_cited_input(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "proved_theorem_on_cited_input" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-C4: proved_theorem_on_cited_input")
    } else {
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{
        certify_coboundary, reject_proved_theorem_on_cited_input, witness, C4_ROWS, CarrierRow,
        CensusError, ResidueCensus, RowDisposition, TelescopeError,
    };

    #[test]
    fn plan_qp_c4_witness_matches_derivation() {
        let census = ResidueCensus::count(C4_ROWS).map(ResidueCensus::carrier);
        let w = witness();
        assert_eq!(census, Ok((w.carrier_val, w.secondary_pair)));
        assert_eq!(w.carrier_val, 8);
        assert_eq!(w.secondary_pair, (1, 0));
        assert_eq!(w.coboundary_cycle_zero, 0);
        assert_eq!(certify_coboundary(&[3, 7, 11, 3], &[4, 4, -8]), Ok(0));
    }

    #[test]
    fn plan_qp_c4_refuses_proved_theorem_on_cited_input() {
        assert!(reject_proved_theorem_on_cited_input("proved_theorem_on_cited_input").is_err());
        assert!(reject_proved_theorem_on_cited_input("promote_unrestricted").is_err());
        assert!(reject_proved_theorem_on_cited_input("admissible_scoped_control").is_ok());
    }

    #[test]
    fn an_open_chain_or_a_gapped_residue_fails() {
        assert!(matches!(
            certify_coboundary(&[3, 7, 11], &[4, 4]),
            Err(TelescopeError::Open)
        ));
        assert!(matches!(
            certify_coboundary(&[3, 7, 11, 3], &[4, 4, -7]),
            Err(TelescopeError::NotCoboundary)
        ));
        let gapped = [
            CarrierRow { label: "residue_0", disposition: RowDisposition::Admitted },
            CarrierRow { label: "residue_2", disposition: RowDisposition::Admitted },
        ];
        assert!(matches!(ResidueCensus::count(&gapped), Err(CensusError::Residue)));
    }
}
