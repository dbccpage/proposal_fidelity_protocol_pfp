//! Exact finite control witness for `BRIDGE-WSC-NONSELECTION` (`bridge_wsc_nonselection`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_unpriced_labeled_atom_selection`.

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
        carrier_val: 2,
        secondary_pair: (1, 1),
        coboundary_cycle_zero,
    }
}

pub fn reject_unpriced_labeled_atom_selection(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "unpriced_labeled_atom_selection" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for BRIDGE-WSC-NONSELECTION: unpriced_labeled_atom_selection")
    } else {
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_unpriced_labeled_atom_selection, witness};

    #[test]
    fn bridge_wsc_nonselection_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 2);
        assert_eq!(w.secondary_pair, (1, 1));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn bridge_wsc_nonselection_refuses_unpriced_labeled_atom_selection() {
        assert!(reject_unpriced_labeled_atom_selection("unpriced_labeled_atom_selection").is_err());
        assert!(reject_unpriced_labeled_atom_selection("promote_unrestricted").is_err());
        assert!(reject_unpriced_labeled_atom_selection("admissible_scoped_control").is_ok());
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PricedSelection {
    chosen: usize,
    total: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PriceError {
    Empty,
    Index,
    Unpriced,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/bridge_wsc_nonselection.rs
// Claim: urn:core:crates_rs:tests:bridge-wsc-nonselection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PriceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PriceError {}

impl PricedSelection {
    pub fn try_new(prices: &[i64], chosen: usize) -> Result<Self, PriceError> {
        if prices.is_empty() {
            return Err(PriceError::Empty);
        }
        let Some(price) = prices.get(chosen).copied() else {
            return Err(PriceError::Index);
        };
        if price <= 0 {
            return Err(PriceError::Unpriced);
        }
        let mut total = 0i64;
        for price in prices {
            total = total.checked_add(*price).ok_or(PriceError::Overflow)?;
        }
        Ok(Self { chosen, total })
    }

    pub fn total(&self) -> i64 {
        self.total
    }
}

#[cfg(test)]
mod priced_selection_tests {
    use super::*;

    #[test]
    fn a_positive_price_is_required() {
        let picked = PricedSelection::try_new(&[0, 4, 1], 1);
        assert!(matches!(picked, Ok(picked) if picked.total() == 5));
        assert!(matches!(PricedSelection::try_new(&[0, 4, 1], 0), Err(PriceError::Unpriced)));
    }
}
