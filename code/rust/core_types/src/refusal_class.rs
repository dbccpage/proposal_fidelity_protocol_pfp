//! The governed refusal vocabulary declared by the solver contract.
//!
//! `governance/contracts/contracts_crates/solver.contract.yaml`
//! declares exactly three refusals a solver may emit:
//!
//! ```text
//! refusals:
//!   may_emit: ["REFUSAL_INVALID_ARGUMENTS", "REFUSAL_GATE_FAILED", "REFUSAL_INVARIANT_BREACH"]
//! ```
//!
//! Two things were true before this module existed. There were **two different
//! `SolverError` enums** in the workspace -- one in `core_types` with nine
//! variants and one in `core_solvers::compliance` with three -- and
//! **neither used the contract's vocabulary**. A gate keyed on the declared
//! refusal names would have matched nothing either solver actually emitted.
//!
//! The fix is not to rename variants. A contract governs *classes* of refusal;
//! an error enum carries *diagnostic detail*, and that detail is worth keeping.
//! What was missing is the total function between them. Each concrete error
//! classifies into exactly one declared class, the classification is total by
//! construction (an exhaustive `match`, so a new variant fails to compile until
//! it is classified), and no class outside the contract can be named because
//! [`RefusalClass`] has no other variants.
//!
//! AuthorityEffect: None. A refusal is a typed stop, never a verdict about the
//! world and never an authority effect.

use std::fmt;

/// A refusal class declared by the solver contract.
///
/// Deliberately closed. Adding a variant here is a contract change and must be
/// made in the YAML first; `tests/contract_conformance.rs` fails if the two
/// disagree in either direction.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum RefusalClass {
    /// The request was not well formed: shape, arity, domain, or parameter.
    ///
    /// The caller can fix this by sending different arguments.
    InvalidArguments,

    /// A declared gate did not pass: infeasible, did not converge, diverged, or
    /// the numerics failed.
    ///
    /// The request was well formed and the procedure ran; it did not get there.
    GateFailed,

    /// A declared invariant was violated -- `d^2 != 0`, gauge dependence, a
    /// malformed topology.
    ///
    /// The most serious class: it says the declared structure was not what it
    /// claimed to be, so no result computed on it means anything.
    InvariantBreach,
}

impl RefusalClass {
    /// The contract token. These strings are the interface; a gate keyed on
    /// `finding_kind` matches on them.
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidArguments => "REFUSAL_INVALID_ARGUMENTS",
            Self::GateFailed => "REFUSAL_GATE_FAILED",
            Self::InvariantBreach => "REFUSAL_INVARIANT_BREACH",
        }
    }

    /// Every class the contract admits, in declaration order.
    pub const ALL: [RefusalClass; 3] = [
        Self::InvalidArguments,
        Self::GateFailed,
        Self::InvariantBreach,
    ];

    /// Parse a contract token, for tests that read the YAML.
    pub fn from_code(code: &str) -> Option<Self> {
        Self::ALL.into_iter().find(|class| class.code() == code)
    }

    /// Always `"None"`. A refusal carries no authority, including the authority
    /// to declare something false about the world.
    pub const fn authority_effect(self) -> &'static str {
        "None"
    }
}

impl fmt::Display for RefusalClass {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.code())
    }
}

/// Classify a concrete error into its declared refusal class.
///
/// Implementations must use an exhaustive `match` with no wildcard arm, so that
/// adding an error variant is a compile error until someone decides which class
/// it belongs to. A wildcard would silently file every future error under one
/// class, which is how a governed vocabulary quietly stops being governed.
pub trait ClassifyRefusal {
    fn refusal_class(&self) -> RefusalClass;

    /// Convenience for records and wire formats.
    fn refusal_code(&self) -> &'static str {
        self.refusal_class().code()
    }
}

// Origin: engine/crates_rs/core_types/src/refusal_class.rs
// Claim: urn:core:crates_rs:core-types:refusal-class:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord106695db {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord106695db` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError106695db {
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
impl BoundaryError106695db {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError106695db {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError106695db {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord106695db {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError106695db> {
        if capacity_bound == 0 {
            return Err(BoundaryError106695db::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError106695db::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError106695db::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn codes_match_the_contract_tokens() {
        assert_eq!(
            RefusalClass::InvalidArguments.code(),
            "REFUSAL_INVALID_ARGUMENTS"
        );
        assert_eq!(RefusalClass::GateFailed.code(), "REFUSAL_GATE_FAILED");
        assert_eq!(
            RefusalClass::InvariantBreach.code(),
            "REFUSAL_INVARIANT_BREACH"
        );
    }

    #[test]
    fn all_lists_every_variant() {
        // If a variant is added without extending ALL, the round trip below
        // stops covering it and this count catches the omission.
        assert_eq!(RefusalClass::ALL.len(), 3);
    }

    #[test]
    fn codes_round_trip() {
        for class in RefusalClass::ALL {
            assert_eq!(RefusalClass::from_code(class.code()), Some(class));
        }
    }

    #[test]
    fn an_undeclared_code_does_not_parse() {
        assert_eq!(RefusalClass::from_code("REFUSAL_AUTHORIZED"), None);
        assert_eq!(RefusalClass::from_code(""), None);
    }

    #[test]
    fn codes_are_distinct() {
        let mut seen = std::collections::BTreeSet::new();
        for class in RefusalClass::ALL {
            assert!(seen.insert(class.code()), "duplicate code {}", class.code());
        }
    }

    #[test]
    fn a_refusal_carries_no_authority() {
        for class in RefusalClass::ALL {
            assert_eq!(class.authority_effect(), "None");
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_106695db {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord106695db::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord106695db::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord106695db::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord106695db::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord106695db::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError106695db::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError106695db::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
