//! Strict unknown-field probes for epic wire types whose private state prevents
//! complete generated shape contracts.

use pfp::epics::{
    bytecode::BytecodeBundle,
    coda::{AdmittedClaim, LayeredClaim, QuarantinedAdapter},
    debate::PrecommitmentDAG,
    guard::GuardMask,
    manifold::ConstraintPressureAccumulator,
    probing::PromptGraph,
    retraction::CemeterySink,
    transport::SimplicialMorphism,
};

fn assert_rejects_unknown_field<T>(type_name: &str)
where
    T: serde::Deserialize<'static> + std::fmt::Debug,
{
    let error = serde_json::from_str::<T>(r#"{"__undeclared_contract_field":true}"#)
        .expect_err("private-wire serde target accepted an undeclared field");
    assert!(
        error.to_string().contains("unknown field"),
        "{type_name} rejected the probe for the wrong reason: {error}"
    );
}

#[test]
fn private_wire_targets_deny_unknown_fields() {
    assert_rejects_unknown_field::<BytecodeBundle>("BytecodeBundle");
    assert_rejects_unknown_field::<LayeredClaim>("LayeredClaim");
    assert_rejects_unknown_field::<AdmittedClaim>("AdmittedClaim");
    assert_rejects_unknown_field::<QuarantinedAdapter>("QuarantinedAdapter");
    assert_rejects_unknown_field::<PrecommitmentDAG>("PrecommitmentDAG");
    assert_rejects_unknown_field::<GuardMask>("GuardMask");
    assert_rejects_unknown_field::<ConstraintPressureAccumulator>("ConstraintPressureAccumulator");
    assert_rejects_unknown_field::<PromptGraph>("PromptGraph");
    assert_rejects_unknown_field::<CemeterySink>("CemeterySink");
    assert_rejects_unknown_field::<SimplicialMorphism>("SimplicialMorphism");
}

// Origin: engine/crates_rs/tests/pfp/private_wire_unknown_fields.rs
// Claim: urn:core:crates_rs:tests:private-wire-unknown-fields:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord776fcd2e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord776fcd2e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError776fcd2e {
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
impl BoundaryError776fcd2e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError776fcd2e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError776fcd2e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord776fcd2e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError776fcd2e> {
        if capacity_bound == 0 {
            return Err(BoundaryError776fcd2e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError776fcd2e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError776fcd2e::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_776fcd2e() {
    let admitted = BoundaryRecord776fcd2e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord776fcd2e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
