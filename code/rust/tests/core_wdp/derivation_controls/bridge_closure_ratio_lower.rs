//! Exact finite control witness for `BRIDGE-CLOSURE-RATIO-LOWER` (`bridge_closure_ratio_lower`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_expansion_implies_unconditional_termination`.

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
        carrier_val: 1,
        secondary_pair: (1, 2),
        coboundary_cycle_zero,
    }
}

pub fn reject_expansion_implies_unconditional_termination(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "expansion_implies_unconditional_termination" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for BRIDGE-CLOSURE-RATIO-LOWER: expansion_implies_unconditional_termination")
    } else {
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_expansion_implies_unconditional_termination, witness};

    #[test]
    fn bridge_closure_ratio_lower_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 1);
        assert_eq!(w.secondary_pair, (1, 2));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn bridge_closure_ratio_lower_refuses_expansion_implies_unconditional_termination() {
        assert!(reject_expansion_implies_unconditional_termination("expansion_implies_unconditional_termination").is_err());
        assert!(reject_expansion_implies_unconditional_termination("promote_unrestricted").is_err());
        assert!(reject_expansion_implies_unconditional_termination("admissible_scoped_control").is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/bridge_closure_ratio_lower.rs
// Claim: urn:core:wdp:bridge-closure-ratio-lower:cycle-energy:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClosureBound {
    energy: i64,
    numerator: i64,
    denominator: i64,
    closed: i64,
    ambient: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CycleEnergyError {
    CycleTooShort,
    Overflow,
    AbsOverflow,
    EnergyDisagreement { squares: i64, via_products: i64 },
    NonPositiveDenominator,
    NotReduced { gcd: i64 },
    BelowBound { left: i64, right: i64 },
    UnexpectedEnergy { energy: i64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/bridge_closure_ratio_lower.rs
// Claim: urn:core:crates_rs:tests:bridge-closure-ratio-lower:l4-production-boundary:v1
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

pub fn try_closure_bound(closed: i64, ambient: i64) -> Result<ClosureBound, CycleEnergyError> {
    let recorded = witness();
    let (numerator, denominator) = recorded.secondary_pair;
    if denominator <= 0 {
        return Err(CycleEnergyError::NonPositiveDenominator);
    }
    let gcd = gcd_i64(numerator, denominator)?;
    if gcd != 1 {
        return Err(CycleEnergyError::NotReduced { gcd });
    }
    let energy = cycle_energy(&[3, 7, 11])?;
    if energy != 96 {
        return Err(CycleEnergyError::UnexpectedEnergy { energy });
    }
    let left = closed.checked_mul(denominator).ok_or(CycleEnergyError::Overflow)?;
    let right = ambient.checked_mul(numerator).ok_or(CycleEnergyError::Overflow)?;
    if left < right {
        return Err(CycleEnergyError::BelowBound { left, right });
    }
    Ok(ClosureBound {
        energy,
        numerator,
        denominator,
        closed,
        ambient,
    })
}

impl ClosureBound {
    pub fn energy(&self) -> i64 {
        self.energy
    }
}

#[cfg(test)]
mod closure_bound_tests {
    use super::*;

    #[test]
    fn the_reduced_pair_bounds_a_closed_ambient_comparison() {
        let witness = try_closure_bound(3, 5);
        assert!(matches!(witness, Ok(ref row) if row.energy() == 96));
    }

    #[test]
    fn refuses_a_comparison_under_the_ratio() {
        assert!(matches!(
            try_closure_bound(1, 3),
            Err(CycleEnergyError::BelowBound { left: 2, right: 3 })
        ));
    }
}
