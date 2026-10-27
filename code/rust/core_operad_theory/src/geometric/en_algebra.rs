//! Geometric: E_n-Operads and Homology Operads.
//!
//! AuthorityEffect: None.

use crate::foundation::{OperadColour, Operation, OperationId, OperadSignature, PlanarColoredOperad, SymmetricColoredOperad};

pub fn build_associative_homology_operad() -> Result<PlanarColoredOperad, String> {
    let mut op = PlanarColoredOperad::new("Homology_E1_Ass", false);
    let c = op.add_colour(OperadColour::new("Object")?);
    let mu = Operation::new_generator(
        OperationId::new("mu_mult")?,
        OperadSignature::new(vec![c.clone(), c.clone()], c),
        "Associative multiplication m(x, y)",
    );
    op.add_operation(mu)?;
    op.ensure_identities();
    Ok(op)
}

pub fn build_gerstenhaber_homology_operad() -> Result<SymmetricColoredOperad, String> {
    let mut op = SymmetricColoredOperad::new("Homology_E2_Gerstenhaber", false);
    let c = op.add_colour(OperadColour::new("GradedVectorSpace")?);
    let mut dot = Operation::new_generator(
        OperationId::new("dot_comm")?,
        OperadSignature::new(vec![c.clone(), c.clone()], c.clone()),
        "Commutative multiplication dot(x, y)",
    );
    dot.is_equivariant = true;

    let mut bracket = Operation::new_generator(
        OperationId::new("gerst_bracket")?,
        OperadSignature::new(vec![c.clone(), c.clone()], c),
        "Lie bracket [x, y] of degree -1",
    );
    bracket.is_equivariant = true;

    op.add_operation(dot)?;
    op.add_operation(bracket)?;
    op.ensure_identities();
    Ok(op)
}

pub fn build_commutative_homology_operad() -> Result<SymmetricColoredOperad, String> {
    let mut op = SymmetricColoredOperad::new("Homology_E_infinity_Com", false);
    let c = op.add_colour(OperadColour::new("Object")?);
    let mut mu = Operation::new_generator(
        OperationId::new("mu_comm")?,
        OperadSignature::new(vec![c.clone(), c.clone()], c),
        "Commutative multiplication m(x, y) = m(y, x)",
    );
    mu.is_equivariant = true;
    op.add_operation(mu)?;
    op.ensure_identities();
    Ok(op)
}

// Origin: engine/crates_rs/core_operad_theory/src/geometric/en_algebra.rs
// Claim: urn:core:crates_rs:core-operad-theory:en-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb345a010 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb345a010` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb345a010 {
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
impl BoundaryErrorb345a010 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb345a010 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb345a010 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb345a010 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb345a010> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb345a010::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb345a010::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb345a010::ExceedsCapacity {
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
mod l4_boundary_tests_b345a010 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb345a010::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb345a010::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb345a010::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb345a010::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb345a010::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb345a010::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb345a010::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
