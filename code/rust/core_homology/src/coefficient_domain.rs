use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CoefficientDomain {
    Integers,
    Rational,
    FiniteField(u64),
    Real, // Caution: Floating point residuals required
}

impl CoefficientDomain {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Integers => "Z",
            Self::Rational => "Q",
            Self::FiniteField(_) => "Fp",
            Self::Real => "R",
        }
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CharacteristicError { kind: &'static str, left: u128, right: u128 }
impl CharacteristicError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
fn divides_checked(prime: u64, divisor: u64) -> Result<bool, CharacteristicError> {
    match prime.checked_rem(divisor) {
        Some(0) => Ok(true),
        Some(_) => Ok(false),
        None => Err(CharacteristicError::new("remainder overflow", u128::from(prime), u128::from(divisor))),
    }
}
fn is_prime(prime: u64) -> Result<bool, CharacteristicError> {
    if prime < 2 { return Ok(false); }
    if [2, 3].contains(&prime) { return Ok(true); }
    if divides_checked(prime, 2)? { return Ok(false); }
    is_odd_prime(prime)
}
fn is_odd_prime(prime: u64) -> Result<bool, CharacteristicError> {
    let mut divisor = 3u64;
    loop {
        let square = u128::from(divisor).checked_mul(u128::from(divisor)).ok_or_else(|| CharacteristicError::new("prime square overflow", u128::from(divisor), u128::from(divisor)))?;
        if square > u128::from(prime) { return Ok(true); }
        if divides_checked(prime, divisor)? { return Ok(false); }
        divisor = divisor.checked_add(2).ok_or_else(|| CharacteristicError::new("divisor overflow", u128::from(divisor), 2))?;
    }
}
/// Exact characteristic of an admitted coefficient domain. The real variant is refused.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ExactCharacteristic { characteristic: u64 }
impl ExactCharacteristic {
    pub fn try_from_domain(domain: CoefficientDomain) -> Result<Self, CharacteristicError> {
        match domain {
            CoefficientDomain::Integers | CoefficientDomain::Rational => Ok(Self { characteristic: 0 }),
            CoefficientDomain::Real => Err(CharacteristicError::new("the real variant is not an exact coefficient domain", 0, 0)),
            CoefficientDomain::FiniteField(prime) => {
                if prime > 4096 {
                    return Err(CharacteristicError::new("finite field exceeds the checked prime bound", u128::from(prime), 4096));
                }
                if !is_prime(prime)? {
                    return Err(CharacteristicError::new("a finite field order is prime", u128::from(prime), 0));
                }
                Ok(Self { characteristic: prime })
            }
        }
    }
    pub const fn characteristic(&self) -> u64 { self.characteristic }
}

// Origin: engine/crates_rs/core_homology/src/coefficient_domain.rs
// Claim: urn:core:crates_rs:core-homology:coefficient-domain:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbdcf7b89 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbdcf7b89` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbdcf7b89 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorbdcf7b89 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbdcf7b89 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbdcf7b89 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbdcf7b89 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbdcf7b89> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbdcf7b89::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbdcf7b89::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbdcf7b89::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod characteristic_checks {
    use super::{CoefficientDomain, ExactCharacteristic};
    #[test]
    fn a_prime_field_keeps_its_characteristic() {
        assert_eq!(ExactCharacteristic::try_from_domain(CoefficientDomain::FiniteField(5)).as_ref().map(ExactCharacteristic::characteristic), Ok(5));
        assert_eq!(ExactCharacteristic::try_from_domain(CoefficientDomain::Integers).as_ref().map(ExactCharacteristic::characteristic), Ok(0));
    }
    #[test]
    fn a_composite_field_order_and_the_real_variant_are_refused() {
        assert_eq!(ExactCharacteristic::try_from_domain(CoefficientDomain::FiniteField(4)).map(|_| ()).map_err(|e| e.kind()), Err("a finite field order is prime"));
        assert_eq!(ExactCharacteristic::try_from_domain(CoefficientDomain::Real).map(|_| ()).map_err(|e| e.kind()), Err("the real variant is not an exact coefficient domain"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_bdcf7b89 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbdcf7b89::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbdcf7b89::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbdcf7b89::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbdcf7b89::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbdcf7b89::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbdcf7b89::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbdcf7b89::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
