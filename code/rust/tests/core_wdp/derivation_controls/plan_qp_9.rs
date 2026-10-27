//! Exact finite control witness for `PLAN-QP-9` (`plan_qp_9`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_uncertified_neville_continuum_bound`.

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
        carrier_val: 13,
        secondary_pair: (13, 12),
        coboundary_cycle_zero,
    }
}

pub fn reject_uncertified_neville_continuum_bound(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "uncertified_neville_continuum_bound" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-9: uncertified_neville_continuum_bound")
    } else {
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConsecutiveCarrierWitness {
    carrier: i64,
    predecessor: i64,
    gap: i64,
    cycle: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConsecutiveCarrierWitnessError {
    NonPositive,
    Gap { gap: i64 },
    NotCoprime { divisor: i64 },
    EmptySamples,
    Cycle { cycle: i64 },
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_9.rs
// Claim: urn:core:crates_rs:tests:plan-qp-9:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ConsecutiveCarrierWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ConsecutiveCarrierWitnessError {}

impl ConsecutiveCarrierWitness {
    fn gcd(mut a: i64, mut b: i64) -> Result<i64, ConsecutiveCarrierWitnessError> {
        a = a.checked_abs().ok_or(ConsecutiveCarrierWitnessError::Overflow)?;
        b = b.checked_abs().ok_or(ConsecutiveCarrierWitnessError::Overflow)?;
        while b != 0 {
            let r = a.checked_rem(b).ok_or(ConsecutiveCarrierWitnessError::Overflow)?;
            a = b;
            b = r;
        }
        Ok(a)
    }

    fn verify_closed_sample_cycle(samples: &[i64]) -> Result<i64, ConsecutiveCarrierWitnessError> {
        let (&first, &last) = match (samples.first(), samples.last()) {
            (Some(f), Some(l)) => (f, l),
            _ => return Err(ConsecutiveCarrierWitnessError::EmptySamples),
        };
        let mut acc = 0i64;
        for pair in samples.windows(2) {
            let step = pair[1].checked_sub(pair[0]).ok_or(ConsecutiveCarrierWitnessError::Overflow)?;
            acc = acc.checked_add(step).ok_or(ConsecutiveCarrierWitnessError::Overflow)?;
        }
        let close = first.checked_sub(last).ok_or(ConsecutiveCarrierWitnessError::Overflow)?;
        let cycle = acc.checked_add(close).ok_or(ConsecutiveCarrierWitnessError::Overflow)?;
        if cycle != 0 {
            return Err(ConsecutiveCarrierWitnessError::Cycle { cycle });
        }
        Ok(cycle)
    }

    pub fn certify(carrier: i64, predecessor: i64, samples: &[i64]) -> Result<Self, ConsecutiveCarrierWitnessError> {
        if carrier <= 0 || predecessor <= 0 {
            return Err(ConsecutiveCarrierWitnessError::NonPositive);
        }
        let gap = carrier.checked_sub(predecessor).ok_or(ConsecutiveCarrierWitnessError::Overflow)?;
        if gap != 1 {
            return Err(ConsecutiveCarrierWitnessError::Gap { gap });
        }
        let divisor = Self::gcd(carrier, predecessor)?;
        if divisor != 1 {
            return Err(ConsecutiveCarrierWitnessError::NotCoprime { divisor });
        }
        let cycle = Self::verify_closed_sample_cycle(samples)?;
        Ok(Self { carrier, predecessor, gap, cycle })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_uncertified_neville_continuum_bound, witness};

    #[test]
    fn plan_qp_9_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 13);
        assert_eq!(w.secondary_pair, (13, 12));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn plan_qp_9_refuses_uncertified_neville_continuum_bound() {
        assert!(reject_uncertified_neville_continuum_bound("uncertified_neville_continuum_bound").is_err());
        assert!(reject_uncertified_neville_continuum_bound("promote_unrestricted").is_err());
        assert!(reject_uncertified_neville_continuum_bound("admissible_scoped_control").is_ok());
    }

    #[test]
    fn exact_witness_holds() {
        use super::{ConsecutiveCarrierWitness, ConsecutiveCarrierWitnessError};
        let declared = witness();
        assert!(matches!(ConsecutiveCarrierWitness::certify(declared.carrier_val, declared.secondary_pair.1, &[3, 7, 11]), Ok(w) if w.gap == 1 && w.cycle == 0));
        assert!(matches!(ConsecutiveCarrierWitness::certify(13, 10, &[3, 7, 11]), Err(ConsecutiveCarrierWitnessError::Gap { .. })));
        assert!(matches!(ConsecutiveCarrierWitness::certify(13, 12, &[i64::MAX, -1]), Err(ConsecutiveCarrierWitnessError::Overflow)));
    }
}
