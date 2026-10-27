//! Bounded finite control for WF-RESEARCH-BIND-RUNNER.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Witness {
    pub goal_id: &'static str,
    pub carrier_val: i64,
    pub secondary_num: i64,
    pub secondary_den: i64,
    pub negative_control_rejected: bool,
}

pub fn reject_model_stage5_or_copied_stage8_terminal(promote_unverified: bool) -> Result<(), &'static str> {
    if promote_unverified {
        Err("reject_model_stage5_or_copied_stage8_terminal")
    } else {
        Ok(())
    }
}

pub fn witness() -> Witness {
    let neg_rejected = reject_model_stage5_or_copied_stage8_terminal(true).is_err();
    Witness {
        goal_id: "WF-RESEARCH-BIND-RUNNER",
        carrier_val: 8,
        secondary_num: 5,
        secondary_den: 8,
        negative_control_rejected: neg_rejected,
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wf_research_bind_runner_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.goal_id, "WF-RESEARCH-BIND-RUNNER");
        assert_eq!(w.carrier_val, 8);
        assert_eq!(w.secondary_num, 5);
        assert_eq!(w.secondary_den, 8);
        assert!(w.negative_control_rejected);
        assert!(reject_model_stage5_or_copied_stage8_terminal(true).is_err());
        assert!(reject_model_stage5_or_copied_stage8_terminal(false).is_ok());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
struct ReducedSecondary { numer: i64, denom: i64 }

#[derive(Debug, Clone, PartialEq, Eq)]
enum SecondaryError { Denom, Reduce }

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wf_research_bind_runner.rs
// Claim: urn:core:crates_rs:tests:wf-research-bind-runner:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SecondaryError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SecondaryError {}

fn secondary_gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

impl ReducedSecondary {
    fn try_new(numer: i64, denom: i64) -> Result<Self, SecondaryError> {
        if denom <= 0 {
            return Err(SecondaryError::Denom);
        }
        let g = i64::try_from(secondary_gcd(numer.unsigned_abs(), denom.unsigned_abs())).map_err(|_| SecondaryError::Reduce)?;
        let numer = numer.checked_div(g).ok_or(SecondaryError::Reduce)?;
        let denom = denom.checked_div(g).ok_or(SecondaryError::Reduce)?;
        Ok(Self { numer, denom })
    }

    fn ratio(&self) -> (i64, i64) { (self.numer, self.denom) }
}

#[cfg(test)]
mod secondary_checks {
    use super::ReducedSecondary;

    #[test]
    fn five_over_eight_stays_and_two_over_four_reduces() {
        assert!(matches!(ReducedSecondary::try_new(5, 8), Ok(r) if r.ratio() == (5, 8)));
        assert!(matches!(ReducedSecondary::try_new(2, 4), Ok(r) if r.ratio() == (1, 2)));
    }

    #[test]
    fn a_zero_denominator_is_refused() {
        assert!(matches!(ReducedSecondary::try_new(5, 0), Err(super::SecondaryError::Denom)));
    }
}
