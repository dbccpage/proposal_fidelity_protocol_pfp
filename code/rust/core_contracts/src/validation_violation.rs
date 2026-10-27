pub trait ValidationViolation:
    core::fmt::Debug + Send + Sync + erased_serde::Serialize + 'static
{
    fn code(&self) -> &'static str;
}

erased_serde::serialize_trait_object!(ValidationViolation);
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MeasuredViolationError { kind: &'static str, left: u128, right: u128 }
impl MeasuredViolationError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// A violation records a positive gap between an expected count and an observed count.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MeasuredViolation { gap: u64 }
impl MeasuredViolation {
    pub fn try_new(code: &str, expected: u64, observed: u64) -> Result<Self, MeasuredViolationError> {
        if code.is_empty() {
            return Err(MeasuredViolationError::new("a violation code is nonempty", 0, 0));
        }
        if expected == observed {
            return Err(MeasuredViolationError::new("a violation requires a positive gap", u128::from(expected), u128::from(observed)));
        }
        let (low, high) = if expected < observed { (expected, observed) } else { (observed, expected) };
        let gap = high.checked_sub(low).ok_or_else(|| MeasuredViolationError::new("gap underflow", u128::from(high), u128::from(low)))?;
        if gap == 0 {
            return Err(MeasuredViolationError::new("a violation requires a positive gap", u128::from(high), u128::from(low)));
        }
        Ok(Self { gap })
    }
    pub const fn gap(&self) -> u64 { self.gap }
}

// Origin: engine/crates_rs/core_contracts/src/validation_violation.rs
// Claim: urn:core:crates_rs:core-contracts:validation-violation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf65f8581 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf65f8581` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf65f8581 {
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
impl BoundaryErrorf65f8581 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf65f8581 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf65f8581 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf65f8581 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf65f8581> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf65f8581::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf65f8581::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf65f8581::ExceedsCapacity {
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
mod measured_violation_checks {
    use super::MeasuredViolation;
    #[test]
    fn the_gap_is_the_absolute_difference() {
        assert_eq!(MeasuredViolation::try_new("count", 2, 7).as_ref().map(MeasuredViolation::gap), Ok(5));
    }
    #[test]
    fn a_zero_gap_is_refused() {
        assert_eq!(MeasuredViolation::try_new("count", 4, 4).map(|_| ()).map_err(|e| e.kind()), Err("a violation requires a positive gap"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_f65f8581 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf65f8581::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf65f8581::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf65f8581::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf65f8581::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf65f8581::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf65f8581::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf65f8581::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
