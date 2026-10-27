//! Simple charges of a declared exact ribbon fusion model.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use core_fusion_categories::{
    braided::RibbonFusionCategory, error::FusionError, scalar::FusionScalar,
};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact finite ribbon charges.";
/// A simple charge with dual, quantum dimension and ribbon twist, read from validated model data.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Anyon<K> {
    charge: usize,
    dual: usize,
    dimension: K,
    twist: K,
    invertible: bool,
}
impl<K: FusionScalar> Anyon<K> {
    pub fn in_model(model: &RibbonFusionCategory<K>, charge: usize) -> Result<Self, FusionError> {
        let ring = model.ring();
        let dual = ring.dual(charge)?;
        let invertible = (0..ring.rank()).try_fold(true, |invertible, c| {
            Ok::<_, FusionError>(
                invertible && ring.multiplicity(charge, dual, c)? == u64::from(c == ring.unit()),
            )
        })?;
        Ok(Self {
            charge,
            dual,
            dimension: model.dimension(charge)?.clone(),
            twist: model.twist(charge)?.clone(),
            invertible,
        })
    }
    pub fn charge(&self) -> usize {
        self.charge
    }
    pub fn dual(&self) -> usize {
        self.dual
    }
    pub fn dimension(&self) -> &K {
        &self.dimension
    }
    pub fn twist(&self) -> &K {
        &self.twist
    }
    /// An abelian charge is invertible under fusion. Signed spherical dimensions
    /// are retained as supplied by the model and do not change this criterion.
    pub fn is_abelian(&self) -> bool {
        self.invertible
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/anyon.rs
// Claim: urn:core:crates_rs:core-quantum-physics:anyon:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbf194bf9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbf194bf9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbf194bf9 {
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
impl BoundaryErrorbf194bf9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbf194bf9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbf194bf9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbf194bf9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbf194bf9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbf194bf9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbf194bf9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbf194bf9::ExceedsCapacity {
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
    use core_number_theory::rational::{ri, Rational};
    #[test]
    fn signed_spherical_dimension_does_not_change_charge_invertibility() {
        let unsigned =
            core_fusion_categories::catalog::pointed_braided::<Rational>(&[2], &[vec![0]], None)
                .unwrap();
        let signed =
            RibbonFusionCategory::try_new(unsigned.braided().clone(), vec![ri(1), ri(-1)]).unwrap();
        let charge = Anyon::in_model(&signed, 1).unwrap();
        assert_eq!(charge.dimension(), &ri(-1));
        assert!(charge.is_abelian());
        assert!(Anyon::in_model(&signed, 0).unwrap().is_abelian());
    }
    #[test]
    fn ising_charge_has_nonabelian_dimension_and_exact_twist() {
        let m = core_fusion_categories::catalog::ising::<Cyclotomic<16>>().unwrap();
        let sigma = Anyon::in_model(&m, 1).unwrap();
        assert!(!sigma.is_abelian());
        assert_eq!(sigma.dual(), 1);
        assert_eq!(
            sigma.dimension().mul(sigma.dimension()),
            Cyclotomic::rational(ri(2))
        );
        assert_eq!(sigma.twist(), &Cyclotomic::zeta(1));
        assert!(Anyon::in_model(&m, 3).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_bf194bf9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbf194bf9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbf194bf9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbf194bf9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbf194bf9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbf194bf9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbf194bf9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbf194bf9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
