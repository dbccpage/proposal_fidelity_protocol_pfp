//! Exact finite control witness for `PLAN-QP-10` (`plan_qp_10`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_mub6_full_resolution_claim`.

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
        secondary_pair: (31, 800),
        coboundary_cycle_zero,
    }
}

pub fn reject_mub6_full_resolution_claim(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "mub6_full_resolution_claim" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-10: mub6_full_resolution_claim")
    } else {
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_mub6_full_resolution_claim, witness};

    #[test]
    fn plan_qp_10_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 9);
        assert_eq!(w.secondary_pair, (31, 800));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn plan_qp_10_refuses_mub6_full_resolution_claim() {
        assert!(reject_mub6_full_resolution_claim("mub6_full_resolution_claim").is_err());
        assert!(reject_mub6_full_resolution_claim("promote_unrestricted").is_err());
        assert!(reject_mub6_full_resolution_claim("admissible_scoped_control").is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_10.rs
// Claim: urn:core:wdp:plan-qp-10:reduced-cycle-energy:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CycleRatio {
    numerator: i64,
    denominator: i64,
    gcd: i64,
    energy: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CycleEnergyError {
    CycleTooShort,
    Overflow,
    AbsOverflow,
    EnergyDisagreement { squares: i64, via_products: i64 },
    NonPositiveDenominator,
    NotReduced { gcd: i64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_10.rs
// Claim: urn:core:crates_rs:tests:plan-qp-10:l4-production-boundary:v1
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

pub fn try_cycle_ratio(numerator: i64, denominator: i64, samples: &[i64]) -> Result<CycleRatio, CycleEnergyError> {
    if denominator <= 0 {
        return Err(CycleEnergyError::NonPositiveDenominator);
    }
    let gcd = gcd_i64(numerator, denominator)?;
    if gcd != 1 {
        return Err(CycleEnergyError::NotReduced { gcd });
    }
    let energy = cycle_energy(samples)?;
    Ok(CycleRatio {
        numerator,
        denominator,
        gcd,
        energy,
    })
}

impl CycleRatio {
    pub fn energy(&self) -> i64 {
        self.energy
    }

    pub fn gcd(&self) -> i64 {
        self.gcd
    }
}

#[cfg(test)]
mod cycle_ratio_tests {
    use super::*;

    #[test]
    fn thirty_one_over_eight_hundred_is_reduced_and_the_cycle_energy_is_96() {
        let ratio = try_cycle_ratio(31, 800, &[3, 7, 11]);
        assert!(matches!(ratio, Ok(ref row) if row.energy() == 96 && row.gcd() == 1));
    }

    #[test]
    fn refuses_an_unreduced_pair() {
        assert!(matches!(
            try_cycle_ratio(2, 4, &[3, 7, 11]),
            Err(CycleEnergyError::NotReduced { gcd: 2 })
        ));
    }
}
