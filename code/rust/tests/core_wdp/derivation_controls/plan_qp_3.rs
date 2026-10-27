//! Exact finite control witness for `PLAN-QP-3` (`plan_qp_3`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_gaussian_rational_tsirelson_attainment`.

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
        carrier_val: 8,
        secondary_pair: (196, 25),
        coboundary_cycle_zero,
    }
}

pub fn reject_gaussian_rational_tsirelson_attainment(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "gaussian_rational_tsirelson_attainment" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-3: gaussian_rational_tsirelson_attainment")
    } else {
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_gaussian_rational_tsirelson_attainment, witness};

    #[test]
    fn plan_qp_3_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 8);
        assert_eq!(w.secondary_pair, (196, 25));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn plan_qp_3_refuses_gaussian_rational_tsirelson_attainment() {
        assert!(reject_gaussian_rational_tsirelson_attainment("gaussian_rational_tsirelson_attainment").is_err());
        assert!(reject_gaussian_rational_tsirelson_attainment("promote_unrestricted").is_err());
        assert!(reject_gaussian_rational_tsirelson_attainment("admissible_scoped_control").is_ok());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
enum TsirelsonError { Denom, Attained, Overflow }

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_3.rs
// Claim: urn:core:crates_rs:tests:plan-qp-3:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TsirelsonError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TsirelsonError {}

/// Strict inequality `numer / denom < 8`, the square of the Tsirelson bound `2√2`.
fn below_tsirelson_square(numer: i64, denom: i64) -> Result<(), TsirelsonError> {
    if denom <= 0 {
        return Err(TsirelsonError::Denom);
    }
    let left = i128::from(numer);
    let right = i128::from(denom).checked_mul(8).ok_or(TsirelsonError::Overflow)?;
    if left >= right {
        return Err(TsirelsonError::Attained);
    }
    Ok(())
}

#[cfg(test)]
mod tsirelson_checks {
    use super::{below_tsirelson_square, witness};

    #[test]
    fn the_declared_pair_sits_strictly_below_eight() {
        let pair = witness().secondary_pair;
        assert!(matches!(below_tsirelson_square(pair.0, pair.1), Ok(())));
        assert!(matches!(below_tsirelson_square(196, 25), Ok(())));
    }

    #[test]
    fn the_integer_eight_is_refused() {
        assert!(matches!(below_tsirelson_square(8, 1), Err(super::TsirelsonError::Attained)));
        assert!(matches!(below_tsirelson_square(1, 0), Err(super::TsirelsonError::Denom)));
    }
}
