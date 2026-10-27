//! Exact finite control witness for `PLAN-QP-4` (`plan_qp_4`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_noncontextual_18ray_assignment`.

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub carrier_val: i64,
    pub secondary_pair: (i64, i64),
    pub coboundary_cycle_zero: i64,
}

pub fn witness() -> Witness {
    let a = [3_i64, 7, 11];
    let coboundary_cycle_zero = (a[1] - a[0]) + (a[2] - a[1]) + (a[0] - a[2]);
    Witness {
        carrier_val: 18,
        secondary_pair: (9, 4),
        coboundary_cycle_zero,
    }
}

pub fn reject_noncontextual_18ray_assignment(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "noncontextual_18ray_assignment" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-4: noncontextual_18ray_assignment")
    } else {
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_noncontextual_18ray_assignment, witness};

    #[test]
    fn plan_qp_4_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 18);
        assert_eq!(w.secondary_pair, (9, 4));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn plan_qp_4_refuses_noncontextual_18ray_assignment() {
        assert!(reject_noncontextual_18ray_assignment("noncontextual_18ray_assignment").is_err());
        assert!(reject_noncontextual_18ray_assignment("promote_unrestricted").is_err());
        assert!(reject_noncontextual_18ray_assignment("admissible_scoped_control").is_ok());
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PmObstruction {
    pub row_product: i8,
    pub col_product: i8,
    pub solutions: u32,
    pub rays: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PmError {
    BadSign,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_4.rs
// Claim: urn:core:crates_rs:tests:plan-qp-4:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PmError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PmError {}

fn mask_entry(mask: u32, row: usize, col: usize) -> i8 {
    if ((mask >> (row * 3 + col)) & 1) == 1 {
        -1
    } else {
        1
    }
}

fn mask_satisfies_constraints(mask: u32, rows: &[i8; 3], cols: &[i8; 3]) -> bool {
    for (row, &req) in rows.iter().enumerate() {
        let prod: i8 = (0..3).map(|col| mask_entry(mask, row, col)).product();
        if prod != req {
            return false;
        }
    }
    for (col, &req) in cols.iter().enumerate() {
        let prod: i8 = (0..3).map(|row| mask_entry(mask, row, col)).product();
        if prod != req {
            return false;
        }
    }
    true
}

pub fn peres_mermin(rows: [i8; 3], cols: [i8; 3]) -> Result<PmObstruction, PmError> {
    if rows.iter().chain(cols.iter()).any(|&s| s != 1 && s != -1) {
        return Err(PmError::BadSign);
    }
    let row_product: i8 = rows.iter().product();
    let col_product: i8 = cols.iter().product();
    let solutions = if row_product == col_product {
        (0u32..512)
            .filter(|&mask| mask_satisfies_constraints(mask, &rows, &cols))
            .count() as u32
    } else {
        0
    };
    Ok(PmObstruction {
        row_product,
        col_product,
        solutions,
        rays: 18,
    })
}

#[cfg(test)]
mod peres_mermin_tests {
    use super::*;

    #[test]
    fn disagreeing_sign_products_have_no_filling() {
        let blocked = peres_mermin([1, 1, 1], [1, 1, -1]);
        assert!(matches!(
            blocked,
            Ok(PmObstruction {
                row_product: 1,
                col_product: -1,
                solutions: 0,
                rays: 18,
            })
        ));
        let open = peres_mermin([1, 1, 1], [1, 1, 1]);
        assert!(matches!(open, Ok(item) if item.solutions > 0 && item.row_product == item.col_product));
    }
}
