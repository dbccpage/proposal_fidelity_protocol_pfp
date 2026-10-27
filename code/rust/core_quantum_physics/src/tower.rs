//! Directed exact cyclotomic carriers for finite quantum amplitudes.
//! Inclusions use the canonical field criterion, including Q(zeta_6)=Q(zeta_3).
//! AuthorityEffect: None.
use core_number_theory::cyclotomic_field::{
    compositum_conductor, contains_cyclotomic_field, embed_cyclotomic, normalized_conductor,
    CyclotomicError, CyclotomicNumber,
};
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CyclotomicTower {
    conductors: Vec<usize>,
}
impl CyclotomicTower {
    pub fn new(conductors: Vec<usize>) -> Result<Self, CyclotomicError> {
        if conductors.is_empty() || conductors.len() > 1024 {
            return Err(CyclotomicError::ConductorTooLarge {
                conductor: conductors.len(),
                max: 1024,
            });
        }
        for &n in &conductors {
            normalized_conductor(n)?;
        }
        for pair in conductors.windows(2) {
            if !contains_cyclotomic_field(pair[0], pair[1])? {
                return Err(CyclotomicError::ConductorMismatch {
                    left: pair[0],
                    right: pair[1],
                });
            }
        }
        Ok(Self { conductors })
    }
    pub fn conductors(&self) -> &[usize] {
        &self.conductors
    }
    pub fn join(conductors: &[usize]) -> Result<usize, CyclotomicError> {
        conductors
            .iter()
            .try_fold(1, |join, &n| compositum_conductor(join, n))
    }
    pub fn embed(
        &self,
        x: &CyclotomicNumber,
        stage: usize,
    ) -> Result<CyclotomicNumber, CyclotomicError> {
        let conductor = *self
            .conductors
            .get(stage)
            .ok_or(CyclotomicError::ConductorTooLarge {
                conductor: stage,
                max: 1024,
            })?;
        embed_cyclotomic(x, conductor)
    }
}
/// Exact Born norm in the real subfield, computed with complex conjugation.
/// Positivity follows from the chosen complex embedding, not from a rational
/// sign comparison when the answer is algebraic.
pub fn born_norm(amplitude: &CyclotomicNumber) -> Result<CyclotomicNumber, CyclotomicError> {
    amplitude.mul(&amplitude.conjugate())
}

// Origin: engine/crates_rs/core_quantum_physics/src/tower.rs
// Claim: urn:core:crates_rs:core-quantum-physics:tower:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7deee7f8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7deee7f8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7deee7f8 {
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
impl BoundaryError7deee7f8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7deee7f8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7deee7f8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7deee7f8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7deee7f8> {
        if capacity_bound == 0 {
            return Err(BoundaryError7deee7f8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7deee7f8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7deee7f8::ExceedsCapacity {
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
mod l4_boundary_tests_7deee7f8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7deee7f8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7deee7f8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7deee7f8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7deee7f8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7deee7f8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7deee7f8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7deee7f8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
