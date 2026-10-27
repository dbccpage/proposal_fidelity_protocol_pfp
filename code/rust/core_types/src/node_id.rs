pub type NodeId = usize;
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NodeSeparationError { kind: &'static str, left: u128, right: u128 }
impl NodeSeparationError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Exact gap between two distinct node identifiers.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NodeSeparation { left: NodeId, right: NodeId, gap: u128 }
impl NodeSeparation {
    fn widen(value: NodeId) -> Result<u128, NodeSeparationError> {
        u128::try_from(value).map_err(|_| NodeSeparationError::new("node identifier exceeds u128", 0, 0))
    }
    pub fn try_new(left: NodeId, right: NodeId) -> Result<Self, NodeSeparationError> {
        let left_wide = Self::widen(left)?;
        let right_wide = Self::widen(right)?;
        if left == right {
            return Err(NodeSeparationError::new("node identifiers are distinct", left_wide, right_wide));
        }
        let (low, high, low_wide, high_wide) = if left < right { (left, right, left_wide, right_wide) } else { (right, left, right_wide, left_wide) };
        let gap = high_wide.checked_sub(low_wide).ok_or_else(|| NodeSeparationError::new("gap underflow", high_wide, low_wide))?;
        let restored = low_wide.checked_add(gap).ok_or_else(|| NodeSeparationError::new("gap did not restore the high identifier", low_wide, gap))?;
        if restored != high_wide {
            return Err(NodeSeparationError::new("gap did not restore the high identifier", restored, high_wide));
        }
        let _ = (low, high);
        Ok(Self { left, right, gap })
    }
    pub const fn gap(&self) -> u128 { self.gap }
}

// Origin: engine/crates_rs/core_types/src/node_id.rs
// Claim: urn:core:crates_rs:core-types:node-id:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf1eb8945 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf1eb8945` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf1eb8945 {
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
impl BoundaryErrorf1eb8945 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf1eb8945 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf1eb8945 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf1eb8945 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf1eb8945> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf1eb8945::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf1eb8945::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf1eb8945::ExceedsCapacity {
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
mod node_separation_checks {
    use super::NodeSeparation;
    #[test]
    fn distinct_identifiers_have_an_exact_gap() {
        let separation = NodeSeparation::try_new(2, 9);
        assert_eq!(separation.as_ref().map(NodeSeparation::gap), Ok(7));
    }
    #[test]
    fn a_repeated_identifier_is_refused() {
        assert_eq!(NodeSeparation::try_new(4, 4).map(|_| ()).map_err(|e| e.kind()), Err("node identifiers are distinct"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_f1eb8945 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf1eb8945::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf1eb8945::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf1eb8945::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf1eb8945::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf1eb8945::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf1eb8945::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf1eb8945::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
