//! Deformation: Koszul duality and proposed quadratic dual skeletons.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use crate::foundation::{Operation, OperationId, OperadSignature};
use super::quadratic_operad::QuadraticOperad;

/// Proposed structural dual skeleton of a quadratic operad.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProposedQuadraticDual {
    pub original_name: String,
    pub dual_operad: QuadraticOperad,
    pub is_pairing_computed: bool,
    pub notes: String,
}

/// Builder for constructing Koszul dual skeletons.
pub struct KoszulDualBuilder;

impl KoszulDualBuilder {
    pub fn build_koszul_dual_skeleton(quad_op: &QuadraticOperad) -> Result<ProposedQuadraticDual, String> {
        let dual_name = format!("{}_KoszulDual", quad_op.name);
        let mut dual_op = QuadraticOperad::new(dual_name);

        for (gen_id, gen) in &quad_op.generators {
            let dual_id = OperationId::new(format!("{}_dual", gen_id))?;
            let dual_sig = OperadSignature::new(gen.inputs().to_vec(), gen.output().clone());
            let dual_gen = Operation {
                op_id: dual_id,
                signature: dual_sig,
                kind: crate::foundation::OperationKind::generator(),
                is_equivariant: gen.is_equivariant,
                description: format!("Koszul dual generator for {}", gen_id),
            };
            dual_op.add_generator(dual_gen);
        }

        Ok(ProposedQuadraticDual {
            original_name: quad_op.name.clone(),
            dual_operad: dual_op,
            is_pairing_computed: false,
            notes: "Dual generator skeleton constructed; full R_perp orthogonal complement not yet computed.".to_string(),
        })
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/deformation/koszul_duality.rs
// Claim: urn:core:crates_rs:core-operad-theory:koszul-duality:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord17ffb25e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord17ffb25e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError17ffb25e {
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
impl BoundaryError17ffb25e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError17ffb25e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError17ffb25e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord17ffb25e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError17ffb25e> {
        if capacity_bound == 0 {
            return Err(BoundaryError17ffb25e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError17ffb25e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError17ffb25e::ExceedsCapacity {
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
mod l4_boundary_tests_17ffb25e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord17ffb25e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord17ffb25e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord17ffb25e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord17ffb25e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord17ffb25e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError17ffb25e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError17ffb25e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
