#[path = "runtime_subsystem.rs"]
pub mod subsystem;

pub use subsystem::*;
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RuntimeBudgetError { kind: &'static str, left: u128, right: u128 }
impl RuntimeBudgetError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Spent cost stays inside a finite runtime limit, and the remainder restores it.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RuntimeBudget { limit: u64, spent: u64, remaining: u64 }
impl RuntimeBudget {
    pub fn try_new(limit: u64, spent: u64) -> Result<Self, RuntimeBudgetError> {
        if spent > limit {
            return Err(RuntimeBudgetError::new("spent cost exceeds the limit", u128::from(spent), u128::from(limit)));
        }
        let remaining = limit.checked_sub(spent).ok_or_else(|| RuntimeBudgetError::new("remaining underflow", u128::from(limit), u128::from(spent)))?;
        let restored = remaining.checked_add(spent).ok_or_else(|| RuntimeBudgetError::new("budget did not restore the limit", u128::from(remaining), u128::from(spent)))?;
        if restored != limit {
            return Err(RuntimeBudgetError::new("budget did not restore the limit", u128::from(restored), u128::from(limit)));
        }
        Ok(Self { limit, spent, remaining })
    }
    pub fn try_spend(&self, cost: u64) -> Result<Self, RuntimeBudgetError> {
        let spent = self.spent.checked_add(cost).ok_or_else(|| RuntimeBudgetError::new("spend overflow", u128::from(self.spent), u128::from(cost)))?;
        Self::try_new(self.limit, spent)
    }
    pub const fn remaining(&self) -> u64 { self.remaining }
}

// Origin: engine/crates_rs/core_contracts/src/runtime.rs
// Claim: urn:core:crates_rs:core-contracts:runtime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd935251a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd935251a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord935251a {
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
impl BoundaryErrord935251a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord935251a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord935251a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd935251a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord935251a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord935251a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord935251a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord935251a::ExceedsCapacity {
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
mod runtime_budget_checks {
    use super::RuntimeBudget;
    #[test]
    fn a_spend_preserves_the_limit() {
        let budget = RuntimeBudget::try_new(10, 3).and_then(|budget| budget.try_spend(4));
        assert_eq!(budget.as_ref().map(RuntimeBudget::remaining), Ok(3));
    }
    #[test]
    fn a_spend_past_the_limit_is_refused() {
        assert_eq!(RuntimeBudget::try_new(2, 0).and_then(|budget| budget.try_spend(3)).map(|_| ()).map_err(|e| e.kind()), Err("spent cost exceeds the limit"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_d935251a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd935251a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd935251a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd935251a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd935251a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd935251a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord935251a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord935251a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
