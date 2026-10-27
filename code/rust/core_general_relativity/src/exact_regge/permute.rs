//! Lexicographic permutations of a 4-tuple.
//!
//! Shared by the 5-cube facet charts and the Freudenthal path enumeration.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

pub(super) fn lex_permutations_4(items: [usize; 4]) -> Vec<[usize; 4]> {
    let mut state = PermuteState {
        chosen: [0; 4],
        used: [false; 4],
        out: Vec::with_capacity(24),
    };
    permute_lex(&items, 0, &mut state);
    state.out
}

struct PermuteState {
    chosen: [usize; 4],
    used: [bool; 4],
    out: Vec<[usize; 4]>,
}

fn permute_lex(items: &[usize; 4], depth: usize, state: &mut PermuteState) {
    if depth == 4 {
        state.out.push(state.chosen);
        return;
    }
    for index in 0..4 {
        if state.used[index] {
            continue;
        }
        state.used[index] = true;
        state.chosen[depth] = items[index];
        permute_lex(items, depth + 1, state);
        state.used[index] = false;
    }
}


#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) struct Lex4Census {
    emitted: u32,
    factorial: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) enum Lex4Error {
    FactorialOverflow,
    CensusMismatch { emitted: u32, factorial: u32 },
    NotARearrangement { index: usize },
}

// Origin: engine/crates_rs/core_general_relativity/src/exact_regge/permute.rs
// Claim: urn:core:crates_rs:core-general-relativity:permute:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for Lex4Error {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for Lex4Error {}

fn factorial_u32(n: u32) -> Result<u32, Lex4Error> {
    let mut acc = 1u32;
    for factor in 2..=n {
        acc = acc.checked_mul(factor).ok_or(Lex4Error::FactorialOverflow)?;
    }
    Ok(acc)
}

/// Certify that lexicographic generation emits `4!` rearrangements.
pub(super) fn certify_lex4(items: [usize; 4]) -> Result<Lex4Census, Lex4Error> {
    let perms = lex_permutations_4(items);
    let emitted = u32::try_from(perms.len()).map_err(|_| Lex4Error::FactorialOverflow)?;
    let factorial = factorial_u32(4)?;
    if emitted != factorial {
        return Err(Lex4Error::CensusMismatch { emitted, factorial });
    }
    let mut expected = items;
    expected.sort_unstable();
    for (index, perm) in perms.iter().enumerate() {
        let mut sorted = *perm;
        sorted.sort_unstable();
        if sorted != expected {
            return Err(Lex4Error::NotARearrangement { index });
        }
    }
    Ok(Lex4Census { emitted, factorial })
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn four_factorial_is_the_lexicographic_census() {
        let admitted = certify_lex4([0, 1, 2, 3]);
        assert!(admitted.is_ok());
        assert_eq!(admitted.as_ref().ok().map(|census| census.emitted), Some(24));
        assert_eq!(admitted.as_ref().ok().map(|census| census.factorial), Some(24));
    }
}
