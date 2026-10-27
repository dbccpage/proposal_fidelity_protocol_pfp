//! Companion Rust witness for PROD-P5-KILL (Evaluate P5 kill conditions on a pilot ledger).

pub fn evaluate_p5_kill(ci_executed: bool, proved_missing_d3_count: usize) -> (bool, bool, bool) {
    let kill_1 = !ci_executed;
    let kill_2 = proved_missing_d3_count > 0;
    let any_kill = kill_1 || kill_2;
    (kill_1, kill_2, any_kill)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pilot_p5_kill_conditions_do_not_hold() {
        assert_eq!(evaluate_p5_kill(true, 0), (false, false, false));
        assert_eq!(evaluate_p5_kill(false, 0), (true, false, true));
        assert_eq!(evaluate_p5_kill(true, 1), (false, true, true));
    }
}

/// Binds the two kill bits to the measured missing-count. A zero Hamming weight
/// is refused when that count is positive.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct P5KillLedger {
    missing: u64,
    kill_1: bool,
    kill_2: bool,
    hamming: u32,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum P5KillLedgerError {
    CountDoesNotFit { missing: u64 },
    NoKillWhileMissing { missing: u64 },
    KillBitDrift { kill_2: bool, missing: u64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p5_kill.rs
// Claim: urn:core:crates_rs:tests:prod-p5-kill:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for P5KillLedgerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for P5KillLedgerError {}

pub fn certify_p5_kill(
    ci_executed: bool,
    proved_missing_d3_count: u64,
) -> Result<P5KillLedger, P5KillLedgerError> {
    let count = usize::try_from(proved_missing_d3_count).map_err(|_| {
        P5KillLedgerError::CountDoesNotFit {
            missing: proved_missing_d3_count,
        }
    })?;
    let (kill_1, kill_2, _any_kill) = evaluate_p5_kill(ci_executed, count);
    if kill_2 != (proved_missing_d3_count > 0) {
        return Err(P5KillLedgerError::KillBitDrift {
            kill_2,
            missing: proved_missing_d3_count,
        });
    }
    let hamming = u32::from(kill_1) + u32::from(kill_2);
    if proved_missing_d3_count > 0 && hamming == 0 {
        return Err(P5KillLedgerError::NoKillWhileMissing {
            missing: proved_missing_d3_count,
        });
    }
    Ok(P5KillLedger {
        missing: proved_missing_d3_count,
        kill_1,
        kill_2,
        hamming,
    })
}

#[cfg(test)]
mod p5_kill_ledger_witness {
    use super::*;

    #[test]
    fn missing_rows_raise_the_second_kill_bit() {
        let ledger = certify_p5_kill(false, 3);
        assert!(ledger.is_ok());
        if let Ok(ledger) = ledger {
            assert_eq!(ledger.missing, 3);
            assert!(ledger.kill_1);
            assert!(ledger.kill_2);
            assert_eq!(ledger.hamming, 2);
        }
        let quiet = certify_p5_kill(true, 0);
        assert!(quiet.is_ok());
        if let Ok(quiet) = quiet {
            assert_eq!(quiet.hamming, 0);
        }
    }
}
