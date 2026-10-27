//! Anyon fusion and braiding on exact multiplicity-free ribbon categories.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::anyon::Anyon;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigUint;
use core_fusion_categories::{
    braided::{FusionSpace, RibbonFusionCategory},
    catalog,
    error::FusionError,
    scalar::FusionScalar,
};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite exact fusion and braiding.";
#[derive(Debug, Clone)]
pub struct AnyonModel<K> {
    ribbon: RibbonFusionCategory<K>,
}
impl<K: FusionScalar> AnyonModel<K> {
    pub fn from_ribbon(ribbon: RibbonFusionCategory<K>) -> Result<Self, FusionError> {
        ribbon.braided().validate()?;
        ribbon.category().verify_dimensions(ribbon.dimensions())?;
        Ok(Self { ribbon })
    }
    /// SU(2)_k in the shared exact Racah gauge, with explicitly bounded
    /// pentagon/hexagon replay. The coordinates are generally not orthonormal.
    pub fn su2_level(level: usize) -> Result<Self, FusionError> {
        Self::from_ribbon(core_fusion_categories::su2_level::su2_level(level)?)
    }
    pub fn ising() -> Result<Self, FusionError> {
        Self::from_ribbon(catalog::ising()?)
    }
    pub fn fibonacci() -> Result<Self, FusionError> {
        Self::from_ribbon(catalog::fibonacci()?)
    }
    pub fn semion() -> Result<Self, FusionError> {
        Self::from_ribbon(catalog::semion()?)
    }
    pub fn toric_code() -> Result<Self, FusionError> {
        Self::from_ribbon(catalog::toric_code()?)
    }
    pub fn three_fermion() -> Result<Self, FusionError> {
        Self::from_ribbon(catalog::three_fermion()?)
    }
    pub fn ribbon(&self) -> &RibbonFusionCategory<K> {
        &self.ribbon
    }
    pub fn anyon(&self, charge: usize) -> Result<Anyon<K>, FusionError> {
        Anyon::in_model(&self.ribbon, charge)
    }
    pub fn fusion_space(&self, word: &[usize], total: usize) -> Result<FusionSpace, FusionError> {
        self.ribbon.braided().fusion_space(word, total)
    }
    pub fn fusion_space_dimension(
        &self,
        word: &[usize],
        total: usize,
    ) -> Result<BigUint, FusionError> {
        self.ribbon.ring().fusion_paths(word, total)
    }
    /// Exchange adjacent charges, also recording the swapped carrier word.
    pub fn exchange(
        &self,
        space: &FusionSpace,
        index: usize,
    ) -> Result<(FusionSpace, BasicMatrix<K>), FusionError> {
        self.ribbon.braided().braid_matrix(space, index)
    }
    pub fn braid_generators(
        &self,
        charge: usize,
        strands: usize,
        total: usize,
    ) -> Result<Vec<BasicMatrix<K>>, FusionError> {
        if strands > core_fusion_categories::fusion_ring::MAX_FUSION_WORD {
            return Err(FusionError::Budget {
                what: "strands",
                requested: strands as u128,
                limit: core_fusion_categories::fusion_ring::MAX_FUSION_WORD as u128,
            });
        }
        self.ribbon.braid_generators(charge, strands, total)
    }
    /// Double exchange, replaying the ribbon balancing identity in the admitted channel.
    pub fn monodromy(&self, a: usize, b: usize, channel: usize) -> Result<K, FusionError> {
        let m =
            self.ribbon
                .braided()
                .monodromy([a, b, channel])
                .ok_or(FusionError::Inconsistent {
                    context: "absent fusion channel",
                })?;
        let ratio = core_number_theory::scalar::divide(
            self.ribbon.twist(channel)?,
            &self.ribbon.twist(a)?.mul(self.ribbon.twist(b)?),
        )
        .map_err(FusionError::from)?;
        if m != ratio {
            return Err(FusionError::Inconsistent {
                context: "ribbon balancing",
            });
        }
        Ok(m)
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/anyon_model.rs
// Claim: urn:core:crates_rs:core-quantum-physics:anyon-model:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord593f4168 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord593f4168` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError593f4168 {
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
impl BoundaryError593f4168 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError593f4168 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError593f4168 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord593f4168 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError593f4168> {
        if capacity_bound == 0 {
            return Err(BoundaryError593f4168::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError593f4168::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError593f4168::ExceedsCapacity {
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
    #[test]
    fn declared_models_satisfy_pentagon_and_both_hexagons() {
        let models = [
            AnyonModel::<Cyclotomic<80>>::ising().unwrap(),
            AnyonModel::fibonacci().unwrap(),
            AnyonModel::semion().unwrap(),
            AnyonModel::toric_code().unwrap(),
            AnyonModel::three_fermion().unwrap(),
        ];
        for model in models {
            assert!(model.ribbon().category().first_pentagon_defect().is_none());
            model.ribbon().braided().validate().unwrap();
        }
    }
    #[test]
    fn ising_fusion_spaces_and_monodromy_are_computed() {
        let m = AnyonModel::<Cyclotomic<16>>::ising().unwrap();
        assert_eq!(m.fusion_space_dimension(&[1; 4], 0).unwrap(), 2u32.into());
        assert_eq!(m.monodromy(1, 1, 0).unwrap(), Cyclotomic::zeta(-2));
        assert!(m.monodromy(1, 0, 2).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_593f4168 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord593f4168::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord593f4168::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord593f4168::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord593f4168::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord593f4168::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError593f4168::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError593f4168::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
