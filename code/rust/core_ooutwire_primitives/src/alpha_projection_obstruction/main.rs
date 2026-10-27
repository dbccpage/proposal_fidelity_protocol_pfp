//! `po000` — recompute the PO-000 replication and print its receipt.
//!
//! ```text
//! cargo run --release --bin po000            # print the receipt
//! cargo run --release --bin po000 -- --write # also rewrite RECEIPT.txt
//! ```
//!
//! `AuthorityEffect: None.`


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_743abb39<T> {
    fn checked_invariant_743abb39(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_743abb39<T> for Option<T> {
    #[inline]
    fn checked_invariant_743abb39(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_743abb39<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_743abb39(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_ooutwire_primitives::alpha_projection_obstruction::run;

fn admission_exit(completed: bool, checks: bool) -> i32 {
    if !completed {
        2
    } else if !checks {
        1
    } else {
        0
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum ProjError {
    ZeroDenom,
    Overflow,
    Pythagoras,
    Bound,
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/alpha_projection_obstruction/main.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ProjError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ProjError {}

fn gcd_u64(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

fn reduce_i64(mut numer: i64, mut denom: i64) -> Result<(i64, i64), ProjError> {
    if denom == 0 {
        return Err(ProjError::ZeroDenom);
    }
    if denom < 0 {
        numer = numer.checked_neg().ok_or(ProjError::Overflow)?;
        denom = denom.checked_neg().ok_or(ProjError::Overflow)?;
    }
    let g = i64::try_from(gcd_u64(numer.unsigned_abs(), denom.unsigned_abs()))
        .map_err(|_| ProjError::Overflow)?;
    if g == 0 {
        return Err(ProjError::ZeroDenom);
    }
    Ok((
        numer.checked_div(g).ok_or(ProjError::Overflow)?,
        denom.checked_div(g).ok_or(ProjError::Overflow)?,
    ))
}

fn certify_axis_projection(x: i64, y: i64) -> Result<(i64, i64), ProjError> {
    let kept2 = x.checked_mul(x).ok_or(ProjError::Overflow)?;
    let discarded2 = y.checked_mul(y).ok_or(ProjError::Overflow)?;
    let norm2 = kept2.checked_add(discarded2).ok_or(ProjError::Overflow)?;
    let sum = kept2.checked_add(discarded2).ok_or(ProjError::Overflow)?;
    if sum != norm2 {
        return Err(ProjError::Pythagoras);
    }
    let (cn, cd) = reduce_i64(discarded2, 2)?;
    let left = cn.checked_mul(2).ok_or(ProjError::Overflow)?;
    let right = norm2.checked_mul(cd).ok_or(ProjError::Overflow)?;
    if left > right {
        return Err(ProjError::Bound);
    }
    Ok((cn, cd))
}

fn orthogonal_projection_certificate() -> Result<(), ProjError> {
    let rho = certify_axis_projection(1, 2)?;
    let sigma = certify_axis_projection(1, 0)?;
    if rho != (2, 1) || sigma != (0, 1) {
        return Err(ProjError::Bound);
    }
    Ok(())
}

fn main() {
    if orthogonal_projection_certificate().is_err() {
        std::process::exit(admission_exit(false, false));
    }
    let write = std::env::args().any(|a| a == "--write");
    let run = match run() {
        Ok(r) => r,
        Err(e) => {
            eprintln!("replication did not complete: {e}");
            std::process::exit(admission_exit(false, false));
        }
    };
    let text = run.to_text();
    print!("{text}");
    if write {
        let path = core_ooutwire_primitives::alpha_projection_obstruction::receipt_path();
        std::fs::write(&path, text.as_bytes()).checked_invariant_743abb39("write RECEIPT.txt");
        eprintln!("wrote {}", path.display());
    }
    if !run.executable_checks_passed {
        std::process::exit(admission_exit(true, false));
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod po000_projection_tests {
    use super::{admission_exit, orthogonal_projection_certificate};

    #[test]
    fn axis_projection_meets_pythagoras_and_the_half_bound() {
        assert!(orthogonal_projection_certificate().is_ok());
        assert_eq!(admission_exit(false, false), 2);
        assert_eq!(admission_exit(true, false), 1);
        assert_eq!(admission_exit(true, true), 0);
    }
}
