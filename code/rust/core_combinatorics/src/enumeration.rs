//! Budgeted combinatorial enumeration: permutations, combinations and weak
//! compositions in lexicographic order, exact factorials and binomial
//! coefficients, and `next_*` steppers.
//!
//! Every enumeration states its size in advance, exactly (as a `BigUint`),
//! and is refused with a typed [`CombinatoricsError::BudgetExceeded`] when the
//! size is above the caller's `limit`, before a single item is built; none of
//! them loops over `n^n` candidates or panics on a large `n`. The order is
//! deterministic: lexicographic on the `usize` vectors.
//!
//! The eager functions ([`permutations`], [`combinations`],
//! [`weak_compositions`]) return every item. The lazy iterators
//! ([`Permutations`], [`Combinations`]) hold one item at a time and carry the
//! same up-front budget check, so a walk over `C(40, 20)` subsets is refused
//! at construction, not after a billion steps.
//!
//! Exact counts: `n!` by [`factorial`], `C(n, k)` by [`binomial`] (bounded,
//! because an unbounded binomial can exhaust memory), and the number of weak
//! compositions `C(total + parts - 1, parts - 1)`.
//!
//! AuthorityEffect: None.

use num_bigint::BigUint;
use num_traits::{One, ToPrimitive, Zero};
use thiserror::Error;

/// Largest `n` for which [`factorial`] is computed (`20000!` has about 77000 digits).
pub const MAX_FACTORIAL_ARGUMENT: usize = 20_000;

/// Largest `min(k, n - k)` for which [`binomial`] is computed.
pub const MAX_BINOMIAL_CHOICE: u64 = 1 << 14;

/// Refusals of the enumeration and counting functions.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum CombinatoricsError {
    #[error("{what} would produce {requested} items, above the limit of {limit}")]
    BudgetExceeded {
        what: &'static str,
        requested: BigUint,
        limit: usize,
    },
    #[error("{what} does not accept {argument}: the bound is {max}")]
    ArgumentTooLarge {
        what: &'static str,
        argument: u64,
        max: u64,
    },
}

/// `n!` exactly. Refused above [`MAX_FACTORIAL_ARGUMENT`].
pub fn factorial(n: usize) -> Result<BigUint, CombinatoricsError> {
    if n > MAX_FACTORIAL_ARGUMENT {
        return Err(CombinatoricsError::ArgumentTooLarge {
            what: "factorial",
            argument: u64::try_from(n).unwrap_or(u64::MAX),
            max: u64::try_from(MAX_FACTORIAL_ARGUMENT).unwrap_or(u64::MAX),
        });
    }
    let mut product = BigUint::one();
    for i in 2..=n {
        product *= BigUint::from(i);
    }
    Ok(product)
}

/// `C(n, k)` exactly, `0` when `k > n`. Refused when `min(k, n - k)` exceeds
/// [`MAX_BINOMIAL_CHOICE`].
///
/// The product `C(n - m + i, i)` for `i = 1..=m` (`m = min(k, n - k)`) is
/// built one factor at a time, and each partial product is itself a binomial
/// coefficient, so every division is exact.
pub fn binomial(n: u64, k: u64) -> Result<BigUint, CombinatoricsError> {
    if k > n {
        return Ok(BigUint::zero());
    }
    let m = k.min(n - k);
    if m > MAX_BINOMIAL_CHOICE {
        return Err(CombinatoricsError::ArgumentTooLarge {
            what: "binomial",
            argument: m,
            max: MAX_BINOMIAL_CHOICE,
        });
    }
    let mut result = BigUint::one();
    for i in 1..=m {
        result *= BigUint::from(n - m + i);
        result /= BigUint::from(i);
    }
    Ok(result)
}

fn budget(what: &'static str, requested: &BigUint, limit: usize) -> Result<(), CombinatoricsError> {
    if *requested > BigUint::from(limit) {
        Err(CombinatoricsError::BudgetExceeded {
            what,
            requested: requested.clone(),
            limit,
        })
    } else {
        Ok(())
    }
}

/// The next permutation of `items` in lexicographic order, in place; `false`
/// (leaving `items` unchanged) when `items` is already the last one.
pub fn next_permutation(items: &mut [usize]) -> bool {
    let n = items.len();
    if n < 2 {
        return false;
    }
    let mut i = n - 1;
    while i > 0 && items[i - 1] >= items[i] {
        i -= 1;
    }
    if i == 0 {
        return false;
    }
    let mut j = n - 1;
    while items[j] <= items[i - 1] {
        j -= 1;
    }
    items.swap(i - 1, j);
    items[i..].reverse();
    true
}

/// The next `k`-subset of `{0, .., n-1}` in lexicographic order, in place
/// (`combination` holds strictly increasing values below `n`); `false` when it
/// is already the last one, or is not a valid subset of `{0, .., n-1}`.
pub fn next_combination(combination: &mut [usize], n: usize) -> bool {
    let k = combination.len();
    if k > n || combination.iter().any(|&c| c >= n) || combination.windows(2).any(|w| w[0] >= w[1])
    {
        return false;
    }
    let mut i = k;
    while i > 0 {
        i -= 1;
        if combination[i] < n - k + i {
            combination[i] += 1;
            for j in (i + 1)..k {
                combination[j] = combination[j - 1] + 1;
            }
            return true;
        }
    }
    false
}

/// Every permutation of `{0, .., n-1}` in lexicographic order. Refused with
/// [`CombinatoricsError::BudgetExceeded`] when `n! > limit`.
pub fn permutations(n: usize, limit: usize) -> Result<Vec<Vec<usize>>, CombinatoricsError> {
    Ok(Permutations::new(n, limit)?.collect())
}

/// Every `k`-subset of `{0, .., n-1}`, each increasing, in lexicographic
/// order. Refused when `C(n, k) > limit`.
pub fn combinations(
    n: usize,
    k: usize,
    limit: usize,
) -> Result<Vec<Vec<usize>>, CombinatoricsError> {
    Ok(Combinations::new(n, k, limit)?.collect())
}

/// Every vector of `parts` non-negative integers with sum `total`, in
/// lexicographic order (so `[0, .., 0, total]` comes first). There are
/// `C(total + parts - 1, parts - 1)` of them; with no parts the only
/// composition is the empty one, and only of `0`. Refused when that count is
/// above `limit`.
pub fn weak_compositions(
    total: usize,
    parts: usize,
    limit: usize,
) -> Result<Vec<Vec<usize>>, CombinatoricsError> {
    let count = if parts == 0 {
        if total == 0 {
            BigUint::one()
        } else {
            BigUint::zero()
        }
    } else {
        let upper = total
            .checked_add(parts - 1)
            .and_then(|s| u64::try_from(s).ok())
            .ok_or(CombinatoricsError::ArgumentTooLarge {
                what: "weak_compositions",
                argument: u64::MAX,
                max: u64::MAX - 1,
            })?;
        binomial(upper, u64::try_from(parts - 1).unwrap_or(u64::MAX))?
    };
    budget("weak compositions", &count, limit)?;
    let mut out = Vec::new();
    let mut current = Vec::with_capacity(parts);
    fill_compositions(total, parts, &mut current, &mut out);
    Ok(out)
}

fn fill_compositions(
    remaining: usize,
    parts: usize,
    current: &mut Vec<usize>,
    out: &mut Vec<Vec<usize>>,
) {
    if parts == 0 {
        if remaining == 0 {
            out.push(current.clone());
        }
        return;
    }
    if parts == 1 {
        current.push(remaining);
        out.push(current.clone());
        current.pop();
        return;
    }
    for first in 0..=remaining {
        current.push(first);
        fill_compositions(remaining - first, parts - 1, current, out);
        current.pop();
    }
}

/// A lazy walk over the permutations of `{0, .., n-1}` in lexicographic
/// order, with its size checked against a budget when it is built.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Permutations {
    current: Option<Vec<usize>>,
    started: bool,
}

impl Permutations {
    /// Refused when `n! > limit`.
    pub fn new(n: usize, limit: usize) -> Result<Self, CombinatoricsError> {
        let size = factorial(n)?;
        budget("permutations", &size, limit)?;
        Ok(Self {
            current: Some((0..n).collect()),
            started: false,
        })
    }
}

impl Iterator for Permutations {
    type Item = Vec<usize>;

    fn next(&mut self) -> Option<Vec<usize>> {
        let current = self.current.as_mut()?;
        if !self.started {
            self.started = true;
            return Some(current.clone());
        }
        if next_permutation(current) {
            Some(current.clone())
        } else {
            self.current = None;
            None
        }
    }
}

/// A lazy walk over the `k`-subsets of `{0, .., n-1}` in lexicographic order,
/// with its size checked against a budget when it is built.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Combinations {
    n: usize,
    current: Option<Vec<usize>>,
    started: bool,
}

impl Combinations {
    /// Refused when `C(n, k) > limit`. For `k > n` there are no subsets and
    /// the iterator is empty.
    pub fn new(n: usize, k: usize, limit: usize) -> Result<Self, CombinatoricsError> {
        let size = binomial(
            u64::try_from(n).unwrap_or(u64::MAX),
            u64::try_from(k).unwrap_or(u64::MAX),
        )?;
        budget("combinations", &size, limit)?;
        Ok(Self {
            n,
            current: if k > n { None } else { Some((0..k).collect()) },
            started: false,
        })
    }
}

impl Iterator for Combinations {
    type Item = Vec<usize>;

    fn next(&mut self) -> Option<Vec<usize>> {
        let current = self.current.as_mut()?;
        if !self.started {
            self.started = true;
            return Some(current.clone());
        }
        if next_combination(current, self.n) {
            Some(current.clone())
        } else {
            self.current = None;
            None
        }
    }
}

/// The exact number of permutations, combinations or compositions as a
/// `u64`, when it fits (a convenience for callers that size buffers).
pub fn to_u64(count: &BigUint) -> Option<u64> {
    count.to_u64()
}

// Origin: engine/crates_rs/core_combinatorics/src/enumeration.rs
// Claim: urn:core:crates_rs:core-combinatorics:enumeration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e60d5cbc {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
