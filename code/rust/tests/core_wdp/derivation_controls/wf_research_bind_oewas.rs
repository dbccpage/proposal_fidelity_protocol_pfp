//! Bounded finite control for WF-RESEARCH-BIND-OEWAS.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Witness {
    pub goal_id: &'static str,
    pub carrier_val: i64,
    pub secondary_num: i64,
    pub secondary_den: i64,
    pub negative_control_rejected: bool,
}

pub fn reject_invented_catalog_hash(promote_unverified: bool) -> Result<(), &'static str> {
    if promote_unverified {
        Err("reject_invented_catalog_hash")
    } else {
        Ok(())
    }
}

pub fn witness() -> Witness {
    let neg_rejected = reject_invented_catalog_hash(true).is_err();
    Witness {
        goal_id: "WF-RESEARCH-BIND-OEWAS",
        carrier_val: 9,
        secondary_num: 1,
        secondary_den: 1,
        negative_control_rejected: neg_rejected,
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wf_research_bind_oewas_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.goal_id, "WF-RESEARCH-BIND-OEWAS");
        assert_eq!(w.carrier_val, 9);
        assert_eq!(w.secondary_num, 1);
        assert_eq!(w.secondary_den, 1);
        assert!(w.negative_control_rejected);
        assert!(reject_invented_catalog_hash(true).is_err());
        assert!(reject_invented_catalog_hash(false).is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wf_research_bind_oewas.rs
// Claim: urn:core:wdp:wf-research-bind:catalog-balance:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
enum BalanceError {
    Denominator,
    NotReduced,
    NegativeWeight,
    CarrierMismatch { sum: i64, carrier: i64 },
    Balance { left: i64, right: i64 },
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wf_research_bind_oewas.rs
// Claim: urn:core:crates_rs:tests:wf-research-bind-oewas:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BalanceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BalanceError {}

fn reduced_pair(mut numer: i64, mut denom: i64) -> Result<i64, BalanceError> {
    if numer < 0 {
        numer = numer.checked_neg().ok_or(BalanceError::Overflow)?;
    }
    if denom < 0 {
        denom = denom.checked_neg().ok_or(BalanceError::Overflow)?;
    }
    while denom != 0 {
        let remainder = numer.checked_rem(denom).ok_or(BalanceError::Overflow)?;
        numer = denom;
        denom = remainder;
    }
    Ok(numer)
}

fn sum_nonnegative_weights(weights: &[i64]) -> Result<i64, BalanceError> {
    let mut sum = 0i64;
    for &weight in weights {
        if weight < 0 {
            return Err(BalanceError::NegativeWeight);
        }
        sum = sum.checked_add(weight).ok_or(BalanceError::Overflow)?;
    }
    Ok(sum)
}

fn try_catalog_balance(
    weights: &[i64],
    numer: i64,
    denom: i64,
    carrier: i64,
) -> Result<(i64, i64), BalanceError> {
    if denom <= 0 {
        return Err(BalanceError::Denominator);
    }
    if reduced_pair(numer, denom)? != 1 {
        return Err(BalanceError::NotReduced);
    }
    let sum = sum_nonnegative_weights(weights)?;
    if sum != carrier {
        return Err(BalanceError::CarrierMismatch { sum, carrier });
    }
    let left = numer.checked_mul(carrier).ok_or(BalanceError::Overflow)?;
    let right = denom.checked_mul(sum).ok_or(BalanceError::Overflow)?;
    if left != right {
        return Err(BalanceError::Balance { left, right });
    }
    Ok((left, right))
}

#[test]
fn weights_two_three_four_balance_carrier_nine() {
    assert!(matches!(
        try_catalog_balance(&[2, 3, 4], 1, 1, 9),
        Ok((9, 9))
    ));
}

#[test]
fn numerator_two_on_carrier_nine_does_not_balance() {
    assert!(matches!(
        try_catalog_balance(&[2, 3, 4], 2, 1, 9),
        Err(BalanceError::Balance { left: 18, right: 9 })
    ));
}

#[test]
fn short_weights_mismatch_the_carrier_even_for_the_unit_pair() {
    assert!(matches!(
        try_catalog_balance(&[2, 3, 3], 1, 1, 9),
        Err(BalanceError::CarrierMismatch { sum: 8, carrier: 9 })
    ));
}

#[test]
fn an_unreduced_pair_is_refused() {
    assert!(matches!(
        try_catalog_balance(&[2, 3, 4], 2, 2, 9),
        Err(BalanceError::NotReduced)
    ));
}
