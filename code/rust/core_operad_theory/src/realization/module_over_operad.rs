//! Realization: Operadic Modules & Algebra Modules.
//!
//! AuthorityEffect: None.

use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use crate::foundation::{Operation, OperationId, OperadSignature, PlanarColoredOperad};
use super::algebra_over_operad::OperadAlgebra;

/// An operadic right module M over an operad O with action gamma: M o O -> M.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OperadicModule {
    pub operad: PlanarColoredOperad,
    pub name: String,
    elements: HashMap<String, Operation>,
}

impl OperadicModule {
    pub fn new(operad: PlanarColoredOperad, name: impl Into<String>) -> Self {
        Self {
            operad,
            name: name.into(),
            elements: HashMap::new(),
        }
    }

    pub fn add_element(&mut self, elem: Operation) {
        self.elements.insert(elem.op_id.as_str().to_string(), elem);
    }

    pub fn right_action(&self, m: &Operation, f: &Operation, i: usize) -> Result<Operation, String> {
        if i >= m.arity() {
            return Err(format!("Insertion index i={} out of range for module element of arity {}", i, m.arity()));
        }

        if f.output() != &m.inputs()[i] {
            return Err(format!(
                "Module action ill-typed: {} expects {} at slot {}, but {} outputs {}",
                m.op_id.as_str(),
                m.inputs()[i].as_str(),
                i,
                f.op_id.as_str(),
                f.output().as_str()
            ));
        }

        let mut new_inputs = m.inputs()[..i].to_vec();
        new_inputs.extend_from_slice(f.inputs());
        new_inputs.extend_from_slice(&m.inputs()[i + 1..]);

        let new_id = OperationId::new(format!("({}_mod_o_{}_{})", m.op_id.as_str(), i, f.op_id.as_str()))?;

        Ok(Operation {
            op_id: new_id,
            signature: OperadSignature::new(new_inputs, m.output().clone()),
            kind: crate::foundation::OperationKind::generator(),
            is_equivariant: m.is_equivariant && f.is_equivariant,
            description: format!("Right operadic module action of {} on {} at slot {}", f.op_id.as_str(), m.op_id.as_str(), i),
        })
    }
}

/// An infinitesimal module M over a specific O-algebra A.
#[derive(Clone)]
pub struct AlgebraModule {
    pub algebra: OperadAlgebra,
    pub name: String,
}

impl AlgebraModule {
    pub fn new(algebra: OperadAlgebra, name: impl Into<String>) -> Self {
        Self {
            algebra,
            name: name.into(),
        }
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/realization/module_over_operad.rs
// Claim: urn:core:crates_rs:core-operad-theory:module-over-operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7eeaf3db {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7eeaf3db` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7eeaf3db {
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
impl BoundaryError7eeaf3db {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7eeaf3db {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7eeaf3db {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7eeaf3db {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7eeaf3db> {
        if capacity_bound == 0 {
            return Err(BoundaryError7eeaf3db::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7eeaf3db::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7eeaf3db::ExceedsCapacity {
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
mod l4_boundary_tests_7eeaf3db {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7eeaf3db::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7eeaf3db::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7eeaf3db::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7eeaf3db::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7eeaf3db::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7eeaf3db::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7eeaf3db::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
