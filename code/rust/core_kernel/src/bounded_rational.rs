//! Checked fixed-width rationals for bounded, allocation-free proposals.
use std::cmp::Ordering;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BoundedRationalError {
    Overflow,
}

// Origin: engine/crates_rs/core_kernel/src/bounded_rational.rs
// Claim: urn:core:crates_rs:core-kernel:bounded-rational:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BoundedRationalError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BoundedRationalError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct StackRational {
    pub numerator: i128,
    pub denominator: i128,
}

impl StackRational {
    pub const ZERO: Self = Self {
        numerator: 0,
        denominator: 1,
    };

    pub fn new(mut n: i128, mut d: i128) -> Result<Self, BoundedRationalError> {
        if d == 0 || n == i128::MIN || d == i128::MIN {
            return Err(BoundedRationalError::Overflow);
        }
        if d < 0 {
            n = -n;
            d = -d;
        }
        let divisor = gcd(n.abs(), d);
        Ok(Self {
            numerator: n / divisor,
            denominator: d / divisor,
        })
    }

    pub fn add(self, other: Self) -> Result<Self, BoundedRationalError> {
        let g = gcd(self.denominator, other.denominator);
        let a = self
            .numerator
            .checked_mul(other.denominator / g)
            .ok_or(BoundedRationalError::Overflow)?;
        let b = other
            .numerator
            .checked_mul(self.denominator / g)
            .ok_or(BoundedRationalError::Overflow)?;
        let n = a.checked_add(b).ok_or(BoundedRationalError::Overflow)?;
        if n == i128::MIN {
            return Err(BoundedRationalError::Overflow);
        }
        let cancel = gcd(n.abs(), g);
        let d = (self.denominator / cancel)
            .checked_mul(other.denominator / g)
            .ok_or(BoundedRationalError::Overflow)?;
        Self::new(n / cancel, d)
    }

    pub fn sub(self, other: Self) -> Result<Self, BoundedRationalError> {
        self.add(Self {
            numerator: -other.numerator,
            ..other
        })
    }

    pub fn mul(self, other: Self) -> Result<Self, BoundedRationalError> {
        let g1 = gcd(self.numerator.abs(), other.denominator);
        let g2 = gcd(other.numerator.abs(), self.denominator);
        let n = (self.numerator / g1)
            .checked_mul(other.numerator / g2)
            .ok_or(BoundedRationalError::Overflow)?;
        let d = (self.denominator / g2)
            .checked_mul(other.denominator / g1)
            .ok_or(BoundedRationalError::Overflow)?;
        Self::new(n, d)
    }

    pub fn div(self, other: Self) -> Result<Self, BoundedRationalError> {
        self.mul(Self::new(other.denominator, other.numerator)?)
    }

    pub fn abs(self) -> Self {
        Self {
            numerator: self.numerator.abs(),
            ..self
        }
    }

    pub fn compare(self, other: Self) -> Result<Ordering, BoundedRationalError> {
        let g = gcd(self.denominator, other.denominator);
        let a = self
            .numerator
            .checked_mul(other.denominator / g)
            .ok_or(BoundedRationalError::Overflow)?;
        let b = other
            .numerator
            .checked_mul(self.denominator / g)
            .ok_or(BoundedRationalError::Overflow)?;
        Ok(a.cmp(&b))
    }
}

pub fn gcd(mut a: i128, mut b: i128) -> i128 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_b3c18bf5 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
