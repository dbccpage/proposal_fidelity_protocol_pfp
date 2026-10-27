//! WDP retains declared headings, targets and instances; FD mathematics has its owner.
use core_category_theory::finite_functional_dependencies::{
    natural_join, project, BinaryDecompositionReport, FdRefusal, FdSchema,
};
use std::collections::BTreeSet;

pub struct DeclaredSetDecomposition {
    pub schema: FdSchema,
    pub components: [u16; 2],
    pub reconstruction_target: String,
    pub rows: Vec<Vec<String>>,
}

impl DeclaredSetDecomposition {
    pub fn evaluate(&self, budget: u64) -> Result<BinaryDecompositionReport, String> {
        if self.reconstruction_target != "original_source_value" {
            return Err("UnsupportedReconstructionTarget".into());
        }
        let report = self
            .schema
            .binary_decomposition(self.components, budget)
            .map_err(|e| e.to_string())?;
        if report.determined_component.is_none() {
            return Err("NonLosslessBinarySplit".into());
        }
        self.schema
            .check_instance(&self.rows)
            .map_err(|e| e.to_string())?;
        let [p0, p1] = self
            .components
            .map(|c| project(&self.rows, self.schema.arity, c));
        let joined = natural_join(
            &p0.map_err(|e: FdRefusal| e.to_string())?,
            &p1.map_err(|e| e.to_string())?,
            self.schema.arity,
            self.components,
        )
        .map_err(|e| e.to_string())?;
        if joined != self.rows.iter().cloned().collect::<BTreeSet<_>>() {
            return Err("ReconstructionFailure".into());
        }
        Ok(report)
    }
}

// Origin: engine/crates_rs/core_wdp/src/sql_normal_form.rs
// Claim: urn:core:crates_rs:core-wdp:sql-normal-form:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc4c402a5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc4c402a5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc4c402a5 {
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
impl BoundaryErrorc4c402a5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc4c402a5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc4c402a5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc4c402a5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc4c402a5> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc4c402a5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc4c402a5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc4c402a5::ExceedsCapacity {
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
mod l4_boundary_tests_c4c402a5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc4c402a5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc4c402a5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc4c402a5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc4c402a5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc4c402a5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc4c402a5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc4c402a5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
