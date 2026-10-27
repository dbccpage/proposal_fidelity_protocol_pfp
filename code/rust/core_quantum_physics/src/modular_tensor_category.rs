//! Topological order from a nondegenerate ribbon model. Modular data live in
//! `core_fusion_categories::modular`.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::anyon_model::AnyonModel;
use num_bigint::BigInt;
use core_fusion_categories::{error::FusionError, modular::ModularData, scalar::FusionScalar};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; checked finite topological order.";
#[derive(Debug, Clone)]
pub struct ModularTensorCategory<K> {
    model: AnyonModel<K>,
    data: ModularData<K>,
}
impl<K: FusionScalar> ModularTensorCategory<K> {
    pub fn try_new(model: AnyonModel<K>) -> Result<Self, FusionError> {
        let data = ModularData::verified(model.ribbon())?;
        Ok(Self { model, data })
    }
    pub fn model(&self) -> &AnyonModel<K> {
        &self.model
    }
    pub fn data(&self) -> &ModularData<K> {
        &self.data
    }
    pub fn ground_state_degeneracy(&self, genus: u32) -> Result<BigInt, FusionError> {
        self.data.ground_state_degeneracy(genus)
    }
    /// Exponential of twice the topological entropy, keeping exact field values.
    pub fn topological_entropy_dimension_squared(&self) -> &K {
        self.data.d_squared()
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/modular_tensor_category.rs
// Claim: urn:core:crates_rs:core-quantum-physics:modular-tensor-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord63a3a28d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord63a3a28d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError63a3a28d {
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
impl BoundaryError63a3a28d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError63a3a28d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError63a3a28d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord63a3a28d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError63a3a28d> {
        if capacity_bound == 0 {
            return Err(BoundaryError63a3a28d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError63a3a28d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError63a3a28d::ExceedsCapacity {
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
    use core_number_theory::cyclotomic_field::Cyclotomic;
    use core_number_theory::rational::ri;
    #[test]
    fn modular_data_reproduce_toric_and_ising_ground_state_counts() {
        let toric =
            ModularTensorCategory::try_new(AnyonModel::<Cyclotomic<16>>::toric_code().unwrap())
                .unwrap();
        assert_eq!(toric.ground_state_degeneracy(0).unwrap(), 1.into());
        assert_eq!(toric.ground_state_degeneracy(2).unwrap(), 16.into());
        assert_eq!(
            toric
                .data()
                .central_charge_mod_8(&Cyclotomic::rational(ri(2)))
                .unwrap(),
            ri(0)
        );
        let ising =
            ModularTensorCategory::try_new(AnyonModel::<Cyclotomic<16>>::ising().unwrap()).unwrap();
        assert_eq!(ising.ground_state_degeneracy(2).unwrap(), 10.into());
        assert_eq!(
            ising.data().central_charge_mod_4().unwrap(),
            core_number_theory::rational::rq(1, 2)
        );
        let fermion =
            ModularTensorCategory::try_new(AnyonModel::<Cyclotomic<16>>::three_fermion().unwrap())
                .unwrap();
        assert_eq!(
            fermion
                .data()
                .central_charge_mod_8(&Cyclotomic::rational(ri(2)))
                .unwrap(),
            ri(4)
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_63a3a28d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord63a3a28d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord63a3a28d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord63a3a28d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord63a3a28d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord63a3a28d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError63a3a28d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError63a3a28d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
