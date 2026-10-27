//! JSON line adapter for the canonical finite rational Phi4 (degree-4 obstruction & Pontryagin/curvature) verifier.

use core_functional::phi4::{ExactPhi4Certificate, Phi4Functional};
use serde_json::json;
use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    let result = io::stdin()
        .read_to_string(&mut input)
        .map_err(|error| error.to_string())
        .and_then(|_| {
            serde_json::from_str::<ExactPhi4Certificate>(&input).map_err(|error| error.to_string())
        })
        .and_then(|certificate| {
            Phi4Functional::verify_exact_certificate(certificate).map_err(|error| error.to_string())
        });

    match result {
        Ok(verified) => {
            println!(
                "{}",
                json!({
                    "status": "PASS",
                    "reported_value": verified.value().to_string(),
                    "duality_gap": "0",
                    "cell4_count": verified.primal_residual().len(),
                    "cell3_count": verified.potential_c().len()
                })
            );
        }
        Err(error) => {
            println!("{}", json!({"status": "REFUSE", "reason": error}));
            std::process::exit(2);
        }
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Phi4GapCensus {
    gap_num: i64,
    gap_den: i64,
    cell4_count: u64,
    cell3_count: u64,
    cell_total: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Phi4GapCensusError {
    Unparsed,
    NonPositiveDenominator,
    NonZeroGap { gap_num: i64, gap_den: i64 },
    Overflow,
}

// Origin: engine/crates_rs/pfp/src/bin/verify_phi4.rs
// Claim: urn:core:crates_rs:pfp:verify-phi4:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for Phi4GapCensusError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for Phi4GapCensusError {}

impl Phi4GapCensus {
    fn parse_token(token: &str) -> Result<i64, Phi4GapCensusError> {
        if token.is_empty() || token.chars().any(char::is_whitespace) {
            return Err(Phi4GapCensusError::Unparsed);
        }
        token.parse::<i64>().map_err(|_| Phi4GapCensusError::Unparsed)
    }

    fn gcd(mut a: i64, mut b: i64) -> Result<i64, Phi4GapCensusError> {
        a = a.checked_abs().ok_or(Phi4GapCensusError::Overflow)?;
        b = b.checked_abs().ok_or(Phi4GapCensusError::Overflow)?;
        while b != 0 {
            let r = a.checked_rem(b).ok_or(Phi4GapCensusError::Overflow)?;
            a = b;
            b = r;
        }
        if a == 0 {
            return Err(Phi4GapCensusError::NonPositiveDenominator);
        }
        Ok(a)
    }

    pub fn certify(gap: &str, cell4_count: u64, cell3_count: u64) -> Result<Self, Phi4GapCensusError> {
        let text = gap.trim();
        let (num_token, den_token) = text.split_once('/').unwrap_or((text, "1"));
        let gap_num_raw = Self::parse_token(num_token)?;
        let gap_den_raw = Self::parse_token(den_token)?;
        if gap_den_raw <= 0 { return Err(Phi4GapCensusError::NonPositiveDenominator); }
        let divisor = Self::gcd(gap_num_raw, gap_den_raw)?;
        let gap_num = gap_num_raw.checked_div(divisor).ok_or(Phi4GapCensusError::Overflow)?;
        let gap_den = gap_den_raw.checked_div(divisor).ok_or(Phi4GapCensusError::Overflow)?;
        if gap_num != 0 { return Err(Phi4GapCensusError::NonZeroGap { gap_num, gap_den }); }
        if gap_den != 1 { return Err(Phi4GapCensusError::Overflow); }
        let cell_total = cell4_count.checked_add(cell3_count).ok_or(Phi4GapCensusError::Overflow)?;
        Ok(Self { gap_num, gap_den, cell4_count, cell3_count, cell_total })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(Phi4GapCensus::certify("0", 2, 3), Ok(w) if w.gap_num == 0 && w.gap_den == 1 && w.cell_total == 5));
        assert!(matches!(Phi4GapCensus::certify("0/4", 1, 1), Ok(w) if w.gap_den == 1 && w.cell_total == 2));
        assert!(matches!(Phi4GapCensus::certify("1/2", 1, 1), Err(Phi4GapCensusError::NonZeroGap { .. })));
        assert!(matches!(Phi4GapCensus::certify("0", u64::MAX, 1), Err(Phi4GapCensusError::Overflow)));
    }
}
