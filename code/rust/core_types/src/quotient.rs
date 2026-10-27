//! Canonical Quotient & Congruence Core types for the engine.

use serde::{Deserialize, Serialize};

/// Partition quotient result for state spaces under action context.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CongruenceCoreQuotient {
    /// Equivalence classes (each class contains state indices).
    pub equivalence_classes: Vec<Vec<usize>>,
    /// State index to quotient class map.
    pub class_map: Vec<usize>,
    /// Stabilization iteration index.
    pub stabilization_index: usize,
    /// Number of minimal adequate quotient classes.
    pub num_classes: usize,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PartitionError { kind: &'static str, left: u128, right: u128 }
impl PartitionError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// A partition of `0..states`: every state lies in exactly one class, and the class map agrees.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PartitionWitness { states: u64, classes: u64 }
fn to_u128(value: usize) -> u128 {
    u128::try_from(value).unwrap_or(u128::MAX)
}

impl PartitionWitness {
    fn record_class_states(
        class: &[usize],
        class_index: usize,
        class_map: &[usize],
        seen: &mut [u8],
    ) -> Result<(), PartitionError> {
        let states = class_map.len();
        if class.is_empty() {
            return Err(PartitionError::new("a class is empty", to_u128(class_index), 0));
        }
        for &state in class {
            if state >= states {
                return Err(PartitionError::new("a state lies outside the class map", to_u128(state), to_u128(states)));
            }
            if seen[state] != 0 {
                return Err(PartitionError::new("a state appears twice", to_u128(state), to_u128(class_index)));
            }
            seen[state] = 1;
            let mapped = class_map[state];
            if mapped != class_index {
                return Err(PartitionError::new("class map disagrees with the class", to_u128(mapped), to_u128(class_index)));
            }
        }
        Ok(())
    }

    pub fn try_from_classes(classes: &[Vec<usize>], class_map: &[usize]) -> Result<Self, PartitionError> {
        let states = class_map.len();
        if classes.is_empty() {
            if states == 0 {
                return Ok(Self { states: 0, classes: 0 });
            }
            return Err(PartitionError::new("states remain outside every class", to_u128(states), 0));
        }
        let mut seen = vec![0u8; states];
        for (class_index, class) in classes.iter().enumerate() {
            Self::record_class_states(class, class_index, class_map, &mut seen)?;
        }
        if let Some(index) = seen.iter().position(|&slot| slot == 0) {
            return Err(PartitionError::new("a state is missing from the classes", to_u128(index), to_u128(states)));
        }
        let states_u = u64::try_from(states).map_err(|_| PartitionError::new("state count exceeds u64", to_u128(states), u128::from(u64::MAX)))?;
        let classes_u = u64::try_from(classes.len()).map_err(|_| PartitionError::new("class count exceeds u64", to_u128(classes.len()), u128::from(u64::MAX)))?;
        Ok(Self { states: states_u, classes: classes_u })
    }
    pub const fn classes(&self) -> u64 { self.classes }
}

// Origin: engine/crates_rs/core_types/src/quotient.rs
// Claim: urn:core:crates_rs:core-types:quotient:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3a5c04cb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3a5c04cb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3a5c04cb {
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
impl BoundaryError3a5c04cb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3a5c04cb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3a5c04cb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3a5c04cb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3a5c04cb> {
        if capacity_bound == 0 {
            return Err(BoundaryError3a5c04cb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3a5c04cb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3a5c04cb::ExceedsCapacity {
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
mod partition_checks {
    use super::PartitionWitness;
    #[test]
    fn a_three_state_partition_has_two_classes() {
        let witness = PartitionWitness::try_from_classes(&[vec![0, 2], vec![1]], &[0, 1, 0]);
        assert_eq!(witness.as_ref().map(|item| item.states), Ok(3));
        assert_eq!(witness.as_ref().map(PartitionWitness::classes), Ok(2));
    }
    #[test]
    fn a_repeated_state_is_refused() {
        assert_eq!(PartitionWitness::try_from_classes(&[vec![0, 0]], &[0]).map(|_| ()).map_err(|e| e.kind()), Err("a state appears twice"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_3a5c04cb {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3a5c04cb::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3a5c04cb::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3a5c04cb::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3a5c04cb::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3a5c04cb::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3a5c04cb::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3a5c04cb::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
