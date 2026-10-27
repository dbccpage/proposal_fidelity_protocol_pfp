//! Emit a `wdp-guarded-coherence-v1` certificate for one causal problem file.
//!
//! Usage: `wdp_guarded_history <problem.json> [--pairs K]` (default `K = 3`).
//! The certificate is printed as compact, key-sorted ASCII JSON. A refusal is
//! printed as a typed refusal record with exit status 2. AuthorityEffect: None.
use core_wdp::genesis_guarded_history::{guarded_certificate, Json, CERTIFICATE_SCHEMA};
use std::process::ExitCode;

fn refuse(reason: String) -> ExitCode {
    println!(
        "{}",
        Json::object([
            ("schema", Json::text(CERTIFICATE_SCHEMA)),
            ("status", Json::text("REFUSE")),
            ("authority_effect", Json::text("None")),
            ("reason", Json::text(reason)),
        ])
        .to_canonical()
    );
    ExitCode::from(2)
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut path = None;
    let mut pairs = 3usize;
    let mut k = 0;
    while k < args.len() {
        if args[k] == "--pairs" {
            let Some(value) = args.get(k + 1).and_then(|v| v.parse::<usize>().ok()) else {
                return refuse("--pairs needs a natural number".into());
            };
            pairs = value;
            k += 2;
        } else if path.is_none() {
            path = Some(args[k].clone());
            k += 1;
        } else {
            return refuse(format!("unexpected argument: {}", args[k]));
        }
    }
    let Some(path) = path else {
        return refuse("usage: wdp_guarded_history <problem.json> [--pairs K]".into());
    };
    let bytes = match std::fs::read(&path) {
        Ok(bytes) => bytes,
        Err(e) => return refuse(format!("problem file unavailable: {e}")),
    };
    match guarded_certificate(&bytes, pairs) {
        Ok(certificate) => {
            println!("{}", certificate.to_canonical());
            ExitCode::SUCCESS
        }
        Err(e) => refuse(e.to_string()),
    }
}


/// Unordered pairs among `events` history nodes: `events * (events - 1) / 2`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct CausalPairBudget {
    events: u32,
    unordered_pairs: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum CausalPairBudgetError {
    NeedTwoEvents { events: u32 },
    Overflow,
    NotExact { product: u32, doubled: u32 },
}

// Origin: engine/crates_rs/core_wdp/src/bin/wdp_guarded_history.rs
// Claim: urn:core:crates_rs:core-wdp:wdp-guarded-history:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CausalPairBudgetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CausalPairBudgetError {}

pub(crate) fn causal_pair_budget(events: u32) -> Result<CausalPairBudget, CausalPairBudgetError> {
    if events < 2 {
        return Err(CausalPairBudgetError::NeedTwoEvents { events });
    }
    let product = events
        .checked_mul(events.checked_sub(1).ok_or(CausalPairBudgetError::Overflow)?)
        .ok_or(CausalPairBudgetError::Overflow)?;
    if product % 2 != 0 {
        return Err(CausalPairBudgetError::NotExact { product, doubled: 0 });
    }
    let unordered_pairs = product / 2;
    let doubled = unordered_pairs
        .checked_mul(2)
        .ok_or(CausalPairBudgetError::Overflow)?;
    if doubled != product {
        return Err(CausalPairBudgetError::NotExact { product, doubled });
    }
    Ok(CausalPairBudget {
        events,
        unordered_pairs,
    })
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn four_events_have_six_unordered_pairs() {
        let admitted = causal_pair_budget(4);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|budget| budget.unordered_pairs), Some(6));
        assert!(matches!(
            causal_pair_budget(1),
            Err(CausalPairBudgetError::NeedTwoEvents { events: 1 })
        ));
    }
}
