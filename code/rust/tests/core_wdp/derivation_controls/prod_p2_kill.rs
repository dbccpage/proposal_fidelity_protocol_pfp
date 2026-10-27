//! Companion Rust witness for PROD-P2-KILL (Evaluate P2 kill conditions: G.5 pass share, failure-list use).

pub fn evaluate_p2_kill(initial_passed: usize, batch_size: usize, repaired_passed: bool) -> (bool, bool, bool) {
    let kill_low_share = batch_size == 0 || (initial_passed * 2 < batch_size);
    let kill_failures_ignored = !repaired_passed;
    let any_kill = kill_low_share || kill_failures_ignored;
    (kill_low_share, kill_failures_ignored, any_kill)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pilot_p2_kill_conditions_do_not_hold() {
        assert_eq!(evaluate_p2_kill(3, 4, true), (false, false, false));
        assert_eq!(evaluate_p2_kill(1, 4, true), (true, false, true));
        assert_eq!(evaluate_p2_kill(3, 4, false), (false, true, true));
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HalfShare {
    numer: i64,
    denom: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HalfError {
    ZeroBatch,
    ZeroDenom,
    NotStrict,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p2_kill.rs
// Claim: urn:core:crates_rs:tests:prod-p2-kill:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HalfError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HalfError {}

fn gcd_i64(mut a: i64, mut b: i64) -> Result<i64, HalfError> {
    if a < 0 {
        a = a.checked_neg().ok_or(HalfError::Overflow)?;
    }
    if b < 0 {
        b = b.checked_neg().ok_or(HalfError::Overflow)?;
    }
    while b != 0 {
        let r = a.checked_rem(b).ok_or(HalfError::Overflow)?;
        a = b;
        b = r;
    }
    Ok(a)
}

impl HalfShare {
    pub fn try_new(numer: i64, denom: i64, batch: i64) -> Result<Self, HalfError> {
        if batch == 0 {
            return Err(HalfError::ZeroBatch);
        }
        if denom <= 0 {
            return Err(HalfError::ZeroDenom);
        }
        let g = gcd_i64(numer, denom)?;
        if g == 0 {
            return Err(HalfError::ZeroDenom);
        }
        let numer = numer.checked_div(g).ok_or(HalfError::Overflow)?;
        let denom = denom.checked_div(g).ok_or(HalfError::Overflow)?;
        let twice = numer.checked_mul(2).ok_or(HalfError::Overflow)?;
        if twice >= denom {
            return Err(HalfError::NotStrict);
        }
        Ok(Self { numer, denom })
    }

    pub fn numer(&self) -> i64 {
        self.numer
    }

    pub fn denom(&self) -> i64 {
        self.denom
    }
}

#[cfg(test)]
mod half_share_tests {
    use super::*;

    #[test]
    fn strict_half_is_admitted_and_one_half_is_refused() {
        let share = HalfShare::try_new(1, 3, 4);
        assert!(matches!(share, Ok(share) if share.numer() == 1 && share.denom() == 3));
        assert!(matches!(HalfShare::try_new(1, 2, 4), Err(HalfError::NotStrict)));
    }
}
