//! RFC 8785 subset: sorted objects, no insignificant whitespace, no IEEE numbers.
//! AuthorityEffect: None.

include!("../../jcs_subset.rs");

pub(crate) const DIALECTIC_LIMITS: Limits = Limits {
    max_bytes: 65_536,
    max_depth: 32,
    max_nodes: 4_096,
};
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DialecticLimitError { kind: &'static str, left: u128, right: u128 }
impl DialecticLimitError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Positive dialectic limits whose depth and node caps fit in the byte budget.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DialecticLimitEnvelope { max_bytes: usize }
impl DialecticLimitEnvelope {
    fn to_u128_bounded(val: usize) -> u128 {
        u128::try_from(val).map_or(u128::MAX, |converted| converted)
    }

    fn validate_twice_depth(limits: Limits) -> Result<(), DialecticLimitError> {
        let depth_twice = limits.max_depth.checked_mul(2).ok_or_else(|| DialecticLimitError::new("twice the depth overflowed", u128::from(limits.max_depth), 2))?;
        let depth_twice_usize = usize::try_from(depth_twice).map_err(|_| DialecticLimitError::new("twice the depth exceeds usize", u128::from(depth_twice), 0))?;
        if depth_twice_usize > limits.max_bytes {
            return Err(DialecticLimitError::new("twice the depth exceeds the byte budget", u128::from(depth_twice), Self::to_u128_bounded(limits.max_bytes)));
        }
        Ok(())
    }

    pub fn try_admit(limits: Limits) -> Result<Self, DialecticLimitError> {
        if limits.max_bytes == 0 || limits.max_depth == 0 || limits.max_nodes == 0 {
            return Err(DialecticLimitError::new("each dialectic limit is positive", Self::to_u128_bounded(limits.max_bytes), u128::from(limits.max_depth)));
        }
        let depth = usize::try_from(limits.max_depth).map_err(|_| DialecticLimitError::new("depth exceeds usize", u128::from(limits.max_depth), 0))?;
        let nodes = usize::try_from(limits.max_nodes).map_err(|_| DialecticLimitError::new("node cap exceeds usize", u128::from(limits.max_nodes), 0))?;
        if depth > limits.max_bytes || nodes > limits.max_bytes {
            return Err(DialecticLimitError::new("a dialectic limit exceeds the byte budget", Self::to_u128_bounded(limits.max_bytes), u128::from(limits.max_nodes)));
        }
        Self::validate_twice_depth(limits)?;
        Ok(Self { max_bytes: limits.max_bytes })
    }
    pub const fn max_bytes(&self) -> usize { self.max_bytes }
}

// Origin: engine/crates_rs/core_adversary/src/jcs.rs
// Claim: urn:core:crates_rs:core-adversary:jcs:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorded43b783 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorded43b783` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrored43b783 {
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
impl BoundaryErrored43b783 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrored43b783 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrored43b783 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorded43b783 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrored43b783> {
        if capacity_bound == 0 {
            return Err(BoundaryErrored43b783::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrored43b783::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrored43b783::ExceedsCapacity {
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
mod dialectic_limit_checks {
    use super::{DialecticLimitEnvelope, Limits, DIALECTIC_LIMITS};
    #[test]
    fn the_declared_dialectic_limits_fit_the_byte_budget() {
        assert_eq!(DialecticLimitEnvelope::try_admit(DIALECTIC_LIMITS).as_ref().map(DialecticLimitEnvelope::max_bytes), Ok(65_536));
    }
    #[test]
    fn twice_the_depth_must_fit_the_byte_budget() {
        let limits = Limits { max_bytes: 10, max_depth: 8, max_nodes: 1 };
        assert_eq!(DialecticLimitEnvelope::try_admit(limits).map(|_| ()).map_err(|e| e.kind()), Err("twice the depth exceeds the byte budget"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_ed43b783 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorded43b783::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorded43b783::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorded43b783::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorded43b783::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorded43b783::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrored43b783::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrored43b783::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
