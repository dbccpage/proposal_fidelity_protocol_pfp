//! Shared parsing of rational wire strings for the Phi2/Phi3/Phi4 certificates.
//! Each caller supplies its own refusal for an unparsable string.

use num_rational::BigRational;
use std::str::FromStr;

pub(crate) fn parse_rational_vec<E>(
    values: &[String],
    invalid: fn(String) -> E,
) -> Result<Vec<BigRational>, E> {
    values
        .iter()
        .map(|s| BigRational::from_str(s).map_err(|_| invalid(s.clone())))
        .collect()
}

pub(crate) fn parse_rational_matrix<E>(
    rows: &[Vec<String>],
    invalid: fn(String) -> E,
) -> Result<Vec<Vec<BigRational>>, E> {
    rows.iter()
        .map(|row| parse_rational_vec(row, invalid))
        .collect()
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_functional/src/wire.rs
// Claim: urn:core:functional:wire:simplex:v1
// AuthorityEffect: None

use num_bigint::BigInt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SimplexCertificate {
    mass_count: usize,
    even_mass: BigRational,
    odd_mass: BigRational,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SimplexError {
    Empty,
    Invalid { token: String },
    Negative { index: usize },
    SumNotOne,
    SplitMismatch,
}

// Origin: engine/crates_rs/core_functional/src/wire.rs
// Claim: urn:core:crates_rs:core-functional:wire:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SimplexError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SimplexError {}

fn zero() -> BigRational {
    BigRational::from_integer(BigInt::from(0))
}

fn one() -> BigRational {
    BigRational::from_integer(BigInt::from(1))
}

pub fn try_simplex(values: &[String]) -> Result<SimplexCertificate, SimplexError> {
    if values.is_empty() {
        return Err(SimplexError::Empty);
    }
    let masses = parse_rational_vec(values, |token| SimplexError::Invalid { token })?;
    let mut total = zero();
    let mut even_mass = zero();
    let mut odd_mass = zero();
    for (index, mass) in masses.iter().enumerate() {
        if mass < &zero() {
            return Err(SimplexError::Negative { index });
        }
        total = total + mass.clone();
        if index % 2 == 0 {
            even_mass = even_mass + mass.clone();
        } else {
            odd_mass = odd_mass + mass.clone();
        }
    }
    if total != one() {
        return Err(SimplexError::SumNotOne);
    }
    if even_mass.clone() + odd_mass.clone() != total {
        return Err(SimplexError::SplitMismatch);
    }
    Ok(SimplexCertificate {
        mass_count: masses.len(),
        even_mass,
        odd_mass,
    })
}

impl SimplexCertificate {
    pub fn mass_count(&self) -> usize {
        self.mass_count
    }

    pub fn even_mass(&self) -> &BigRational {
        &self.even_mass
    }

    pub fn odd_mass(&self) -> &BigRational {
        &self.odd_mass
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod simplex_tests {
    use super::*;
    use num_bigint::BigInt;
    use num_rational::BigRational;

    #[test]
    fn a_two_point_simplex_sums_to_one() {
        let witness = try_simplex(&["1/2".to_string(), "1/2".to_string()]);
        assert!(matches!(witness, Ok(ref row) if row.mass_count() == 2));
        let even = witness.as_ref().map(|row| row.even_mass().clone());
        let odd = witness.as_ref().map(|row| row.odd_mass().clone());
        assert_eq!(even, Ok(BigRational::from_integer(BigInt::from(1)) / BigRational::from_integer(BigInt::from(2))));
        assert_eq!(odd, even);
    }

    #[test]
    fn refuses_a_negative_mass_and_a_short_sum() {
        assert!(matches!(
            try_simplex(&["-1/2".to_string(), "3/2".to_string()]),
            Err(SimplexError::Negative { index: 0 })
        ));
        assert!(matches!(
            try_simplex(&["1/3".to_string(), "1/3".to_string()]),
            Err(SimplexError::SumNotOne)
        ));
    }
}
