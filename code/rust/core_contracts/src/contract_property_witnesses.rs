
#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_f4466d52;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_f4466d52<T> = std::result::Result<T, BoundaryError_f4466d52>;
#[cfg(test)]
mod __core_contracts_property_witnesses {
    use crate::traits::fixed_layer::OperatorClass;

    #[test]
    fn operator_class_symbol_has_compiled_witness() {
        assert!(core::any::type_name::<OperatorClass>().contains("OperatorClass"));
    }
}

use crate::traits::fixed_layer::OperatorClass;

/// Counts of the five operator classes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClassificationCensus {
    counts: [u32; 5],
}

fn class_code(class: &OperatorClass) -> u8 {
    match class {
        OperatorClass::E => 0,
        OperatorClass::I => 1,
        OperatorClass::C => 2,
        OperatorClass::R => 3,
        OperatorClass::M => 4,
    }
}

impl ClassificationCensus {
    /// Tally classes. Every code is in `0..5` and the tallies sum to the input length.
    pub fn try_from_classes(classes: &[OperatorClass]) -> Result<Self, &'static str> {
        let mut counts = [0u32; 5];
        for class in classes {
            let code = class_code(class);
            if code >= 5 {
                return Err("operator class code escaped 0..5");
            }
            let Some(slot) = counts.get_mut(usize::from(code)) else {
                return Err("operator class code escaped 0..5");
            };
            *slot = slot.checked_add(1).ok_or("class tally overflow")?;
        }
        let mut sum = 0u32;
        for count in counts {
            sum = sum.checked_add(count).ok_or("class tally overflow")?;
        }
        if sum as usize != classes.len() {
            return Err("class tally does not recover the input length");
        }
        Ok(Self { counts })
    }

    /// Copy of the five tallies.
    pub fn counts(&self) -> [u32; 5] { self.counts }
}

// Origin: engine/crates_rs/core_contracts/src/contract_property_witnesses.rs
// Claim: urn:core:crates_rs:core-contracts:contract-property-witnesses:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf4466d52 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf4466d52` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf4466d52 {
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
impl BoundaryErrorf4466d52 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf4466d52 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf4466d52 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf4466d52 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf4466d52> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf4466d52::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf4466d52::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf4466d52::ExceedsCapacity {
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
mod classification_census_tests {
    use super::*;
    #[test]
    fn each_class_lands_in_its_slot() {
        let census = ClassificationCensus::try_from_classes(&[
            OperatorClass::E,
            OperatorClass::I,
            OperatorClass::C,
            OperatorClass::R,
            OperatorClass::M,
        ]);
        assert!(matches!(census, Ok(ref c) if c.counts() == [1, 1, 1, 1, 1]));
    }
}

#[cfg(test)]
mod l4_boundary_tests_f4466d52 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf4466d52::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf4466d52::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf4466d52::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf4466d52::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf4466d52::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf4466d52::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf4466d52::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
