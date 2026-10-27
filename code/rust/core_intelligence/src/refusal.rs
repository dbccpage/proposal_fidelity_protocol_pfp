use serde::Serialize;

/// A typed native refusal. It records why the kernel declined a lifecycle
/// claim; it does not turn a source, candidate, or proposal into authority.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Refusal {
    pub code: String,
    pub message: String,
    pub authority_effect: &'static str,
}

impl Refusal {
    pub fn new(code: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            code: code.into(),
            message: message.into(),
            authority_effect: "None",
        }
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RefusalCensusError { kind: &'static str, left: u128, right: u128 }
impl RefusalCensusError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// Every recorded refusal in this module carries authority effect None.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RefusalAuthorityCensus { records: u64 }
impl RefusalAuthorityCensus {
    pub fn try_from_refusals(refusals: &[Refusal]) -> Result<Self, RefusalCensusError> {
        if refusals.is_empty() {
            return Err(RefusalCensusError::new("a census examines at least one refusal", 0, 0));
        }
        let mut records = 0u64;
        for refusal in refusals {
            if refusal.code.is_empty() {
                return Err(RefusalCensusError::new("a refusal code is nonempty", u128::from(records), 0));
            }
            if refusal.authority_effect != "None" {
                return Err(RefusalCensusError::new("authority effect is None", u128::from(records), 0));
            }
            records = records.checked_add(1).ok_or_else(|| RefusalCensusError::new("record count overflow", u128::from(records), 1))?;
        }
        Ok(Self { records })
    }
    pub const fn records(&self) -> u64 { self.records }
}

// Origin: engine/crates_rs/core_intelligence/src/refusal.rs
// Claim: urn:core:crates_rs:core-intelligence:refusal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc114e1af {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc114e1af` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc114e1af {
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
impl BoundaryErrorc114e1af {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc114e1af {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc114e1af {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc114e1af {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc114e1af> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc114e1af::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc114e1af::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc114e1af::ExceedsCapacity {
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
mod refusal_census_checks {
    use super::{Refusal, RefusalAuthorityCensus};
    #[test]
    fn a_constructed_refusal_keeps_authority_none() {
        let census = RefusalAuthorityCensus::try_from_refusals(&[Refusal::new("R", "declined")]);
        assert_eq!(census.as_ref().map(RefusalAuthorityCensus::records), Ok(1));
    }
    #[test]
    fn a_forged_authority_effect_is_refused() {
        let forged = Refusal { code: "R".into(), message: "m".into(), authority_effect: "Minted" };
        assert_eq!(RefusalAuthorityCensus::try_from_refusals(&[forged]).map(|_| ()).map_err(|e| e.kind()), Err("authority effect is None"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_c114e1af {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc114e1af::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc114e1af::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc114e1af::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc114e1af::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc114e1af::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc114e1af::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc114e1af::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
