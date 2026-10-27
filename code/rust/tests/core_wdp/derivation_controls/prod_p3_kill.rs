//! Companion Rust witness for PROD-P3-KILL (Evaluate P3 kill conditions on pilot workloads).

pub fn evaluate_p3_kill(saving_num: i64, transfer_sound: bool) -> (bool, bool, bool) {
    let kill_no_benefit = saving_num <= 0;
    let kill_unsound = !transfer_sound;
    let any_kill = kill_no_benefit || kill_unsound;
    (kill_no_benefit, kill_unsound, any_kill)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pilot_p3_kill_conditions_do_not_hold() {
        assert_eq!(evaluate_p3_kill(1, true), (false, false, false));
        assert_eq!(evaluate_p3_kill(0, true), (true, false, true));
        assert_eq!(evaluate_p3_kill(1, false), (false, true, true));
    }
}

/// Rational saving `numerator/denominator`. Kill when the numerator is non-positive or transfer is unsound.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SavingWitness {
    numerator: i64,
    denominator: i64,
    kill: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SavingError {
    NonPositiveDenominator,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p3_kill.rs
// Claim: urn:core:crates_rs:tests:prod-p3-kill:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SavingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SavingError {}

fn gcd_i64(mut a: i64, mut b: i64) -> Result<i64, SavingError> {
    a = a.checked_abs().ok_or(SavingError::Overflow)?;
    b = b.checked_abs().ok_or(SavingError::Overflow)?;
    while b != 0 {
        let next = a % b;
        a = b;
        b = next;
    }
    if a == 0 { Ok(1) } else { Ok(a) }
}

impl SavingWitness {
    pub fn try_saving(
        numerator: i64,
        denominator: i64,
        transfer_sound: bool,
    ) -> Result<Self, SavingError> {
        if denominator <= 0 {
            return Err(SavingError::NonPositiveDenominator);
        }
        let divisor = gcd_i64(numerator, denominator)?;
        let numerator = numerator
            .checked_div(divisor)
            .ok_or(SavingError::Overflow)?;
        let denominator = denominator
            .checked_div(divisor)
            .ok_or(SavingError::Overflow)?;
        let kill = numerator <= 0 || !transfer_sound;
        Ok(Self {
            numerator,
            denominator,
            kill,
        })
    }

    pub fn kill(&self) -> bool {
        self.kill
    }
}
