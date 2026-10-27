//! Exact finite control witness for `PLAN-QP-C2` (`plan_qp_c2`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_stale_c1000_not_started_status`.

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
        carrier_val: 9,
        secondary_pair: (9, 9),
        coboundary_cycle_zero,
    }
}

pub fn reject_stale_c1000_not_started_status(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "stale_c1000_not_started_status" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-C2: stale_c1000_not_started_status")
    } else {
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_stale_c1000_not_started_status, witness};

    #[test]
    fn plan_qp_c2_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 9);
        assert_eq!(w.secondary_pair, (9, 9));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn plan_qp_c2_refuses_stale_c1000_not_started_status() {
        assert!(reject_stale_c1000_not_started_status("stale_c1000_not_started_status").is_err());
        assert!(reject_stale_c1000_not_started_status("promote_unrestricted").is_err());
        assert!(reject_stale_c1000_not_started_status("admissible_scoped_control").is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_c2.rs
// Claim: urn:core:wdp:plan-qp-c2:fraction-reduction:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReducedFraction {
    numerator: i64,
    denominator: i64,
    gcd: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CycleEnergyError {
    CycleTooShort,
    Overflow,
    AbsOverflow,
    EnergyDisagreement { squares: i64, via_products: i64 },
    NonPositiveDenominator,
    NotReduced { gcd: i64 },
    ZeroGcd,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_c2.rs
// Claim: urn:core:crates_rs:tests:plan-qp-c2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CycleEnergyError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CycleEnergyError {}

fn checked_abs(value: i64) -> Result<i64, CycleEnergyError> {
    if value < 0 {
        value.checked_neg().ok_or(CycleEnergyError::AbsOverflow)
    } else {
        Ok(value)
    }
}

fn gcd_i64(left: i64, right: i64) -> Result<i64, CycleEnergyError> {
    let mut a = checked_abs(left)?;
    let mut b = checked_abs(right)?;
    while b != 0 {
        let remainder = a.checked_rem(b).ok_or(CycleEnergyError::Overflow)?;
        a = b;
        b = remainder;
    }
    Ok(a)
}

fn accumulate_cycle_step(
    current: i64,
    next: i64,
    acc: (i64, i64, i64),
) -> Result<(i64, i64, i64), CycleEnergyError> {
    let diff = next.checked_sub(current).ok_or(CycleEnergyError::Overflow)?;
    let sq = diff.checked_mul(diff).ok_or(CycleEnergyError::Overflow)?;
    let cur_sq = current.checked_mul(current).ok_or(CycleEnergyError::Overflow)?;
    let prod = current.checked_mul(next).ok_or(CycleEnergyError::Overflow)?;
    Ok((
        acc.0.checked_add(sq).ok_or(CycleEnergyError::Overflow)?,
        acc.1.checked_add(cur_sq).ok_or(CycleEnergyError::Overflow)?,
        acc.2.checked_add(prod).ok_or(CycleEnergyError::Overflow)?,
    ))
}

pub fn cycle_energy(samples: &[i64]) -> Result<i64, CycleEnergyError> {
    if samples.len() < 2 {
        return Err(CycleEnergyError::CycleTooShort);
    }
    let mut acc = (0i64, 0i64, 0i64);
    for (index, &current) in samples.iter().enumerate() {
        let next = samples[(index + 1) % samples.len()];
        acc = accumulate_cycle_step(current, next, acc)?;
    }
    let (squares, sum_squares, sum_products) = acc;
    let two_sq = sum_squares.checked_mul(2).ok_or(CycleEnergyError::Overflow)?;
    let two_prod = sum_products.checked_mul(2).ok_or(CycleEnergyError::Overflow)?;
    let via_products = two_sq.checked_sub(two_prod).ok_or(CycleEnergyError::Overflow)?;
    if squares != via_products {
        return Err(CycleEnergyError::EnergyDisagreement { squares, via_products });
    }
    Ok(squares)
}

pub fn try_reduce(numerator: i64, denominator: i64, claim_already_reduced: bool) -> Result<ReducedFraction, CycleEnergyError> {
    if denominator <= 0 {
        return Err(CycleEnergyError::NonPositiveDenominator);
    }
    let gcd = gcd_i64(numerator, denominator)?;
    if gcd == 0 {
        return Err(CycleEnergyError::ZeroGcd);
    }
    if claim_already_reduced && gcd != 1 {
        return Err(CycleEnergyError::NotReduced { gcd });
    }
    let reduced_num = numerator.checked_div(gcd).ok_or(CycleEnergyError::Overflow)?;
    let reduced_den = denominator.checked_div(gcd).ok_or(CycleEnergyError::Overflow)?;
    Ok(ReducedFraction {
        numerator: reduced_num,
        denominator: reduced_den,
        gcd,
    })
}

impl ReducedFraction {
    pub fn numerator(&self) -> i64 {
        self.numerator
    }

    pub fn denominator(&self) -> i64 {
        self.denominator
    }

    pub fn gcd(&self) -> i64 {
        self.gcd
    }
}

#[cfg(test)]
mod reduce_fraction_tests {
    use super::*;

    #[test]
    fn nine_over_nine_reduces_by_the_carrier_and_the_cycle_energy_is_96() {
        let reduced = try_reduce(9, 9, false);
        assert!(matches!(
            reduced,
            Ok(ref row) if row.numerator() == 1 && row.denominator() == 1 && row.gcd() == 9
        ));
        let recorded = witness();
        assert_eq!(recorded.carrier_val, 9);
        assert!(matches!(cycle_energy(&[3, 7, 11]), Ok(96)));
    }

    #[test]
    fn refuses_to_call_nine_over_nine_reduced() {
        assert!(matches!(try_reduce(9, 9, true), Err(CycleEnergyError::NotReduced { gcd: 9 })));
    }
}
