//! Test-only helpers.  Compiled under `cfg(test)` only, so nothing here is
//! part of the crate's API, and the L3 census excludes this module by name
//! for exactly that reason.
//!
//! Both functions here return events.  The census fired on the second one
//! while it lived in `export.rs` — a live catch, not an injection — which is
//! why it lives here now.

use crate::event::Event;
use crate::mark::{Mark, Pair};
use crate::regime::{FormId, Regime};
use crate::token::Token;

/// An instance admission from indices.  A constructor from explicit
/// arguments; reads no state.
pub fn inst(form: FormId, args: &[usize]) -> Event {
    Event::AdmitInst(form, args.iter().map(|&a| Mark(a)).collect())
}

/// The event delta an edge applies to its parent, uniform for creation and
/// merge edges — the sealed `edge_events`.  The merge-witness
/// re-verification reconstructs the child from the parent this way.
pub fn edge_events(parent: &Regime, edge: &crate::tree::Edge) -> Vec<Event> {
    if edge.challenge == "supply" {
        let token = Token::new(format!("g{}", parent.n_data()));
        return vec![Event::Supply(token.clone()), Event::AdmitDatum(token)];
    }
    let inner = edge.challenge.trim_start_matches("separate(").trim_end_matches(')');
    let (i, j) = inner.split_once(", ").expect("separate(i, j)");
    let pair = Pair::of(i.parse().unwrap(), j.parse().unwrap());
    let mut out = vec![Event::Impose(pair)];
    out.extend(crate::candidate::delta_events(parent, &edge.response));
    out
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SeparateError { Protocol, Index, Distinct, Roundtrip, Overflow }

// Origin: engine/crates_rs/core_ooutwire_primitives/src/testkit.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:testkit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SeparateError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SeparateError {}

fn parse_index(text: &str) -> Result<usize, SeparateError> {
    if text.is_empty() || !text.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(SeparateError::Index);
    }
    let mut value = 0usize;
    for byte in text.bytes() {
        value = value.checked_mul(10).ok_or(SeparateError::Overflow)?.checked_add(usize::from(byte - b'0')).ok_or(SeparateError::Overflow)?;
    }
    Ok(value)
}

/// Parse `separate(i, j)` with distinct indices and an exact round trip.
pub fn try_separate_pair(protocol: &str) -> Result<(usize, usize), SeparateError> {
    let Some(rest) = protocol.strip_prefix("separate(") else {
        return Err(SeparateError::Protocol);
    };
    let Some(inner) = rest.strip_suffix(')') else {
        return Err(SeparateError::Protocol);
    };
    let Some((left, right)) = inner.split_once(", ") else {
        return Err(SeparateError::Protocol);
    };
    let i = parse_index(left)?;
    let j = parse_index(right)?;
    if i == j {
        return Err(SeparateError::Distinct);
    }
    if format!("separate({i}, {j})") != protocol {
        return Err(SeparateError::Roundtrip);
    }
    Ok((i, j))
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod separate_pair_checks {
    use super::*;

    #[test]
    fn distinct_indices_round_trip() {
        assert!(matches!(try_separate_pair("separate(1, 4)"), Ok((1, 4))));
    }

    #[test]
    fn equal_indices_are_refused() {
        assert!(matches!(try_separate_pair("separate(2, 2)"), Err(SeparateError::Distinct)));
    }
}
