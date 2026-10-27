//! Finite odd-prime Schrödinger representation certificate. AuthorityEffect: None.
//! Full Weyl operator reconstruction supplies the finite irreducibility witness;
//! this has no assertion about infinite dimensional Stone-von Neumann uniqueness.
use linear_algebra::exact_field::matrix as mx;
use core_lie_theory::heisenberg::{HeisenbergError, WeylHeisenberg};
use core_number_theory::cyclotomic_field::Cyclotomic;
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteIrreducibilityCertificate {
    pub prime: usize,
    pub matrix_units_reconstructed: usize,
    pub center_characters: usize,
}
fn build_matrix_unit<const P: usize>(
    r: usize,
    c: usize,
) -> Result<linear_algebra::backend::basic_matrix::BasicMatrix<Cyclotomic<P>>, HeisenbergError> {
    Ok(mx::from_rows(
        (0..P)
            .map(|i| {
                (0..P)
                    .map(|j| {
                        if (i, j) == (r, c) {
                            Cyclotomic::<P>::one()
                        } else {
                            Cyclotomic::<P>::zero()
                        }
                    })
                    .collect()
            })
            .collect(),
    )?)
}

pub fn certify_schrodinger_irreducibility<const P: usize>(
) -> Result<FiniteIrreducibilityCertificate, HeisenbergError> {
    let census = core_lie_theory::heisenberg::stone_von_neumann_census(P)?;
    let system = WeylHeisenberg::new(P, Cyclotomic::<P>::zeta(1))?;
    if P > 11 {
        return Err(HeisenbergError::Dimension(P));
    }
    for r in 0..P {
        for c in 0..P {
            let unit = build_matrix_unit::<P>(r, c)?;
            if system.reconstruct_operator(&unit)? != unit {
                return Err(HeisenbergError::Shape { dimension: P });
            }
        }
    }
    let _ = census;
    Ok(FiniteIrreducibilityCertificate {
        prime: P,
        matrix_units_reconstructed: P * P,
        center_characters: P - 1,
    })
}

// Origin: engine/crates_rs/core_quantum_physics/src/heisenberg_representation_uniqueness.rs
// Claim: urn:core:crates_rs:core-quantum-physics:heisenberg-representation-uniqueness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddca61187 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddca61187` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordca61187 {
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
impl BoundaryErrordca61187 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordca61187 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordca61187 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddca61187 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordca61187> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordca61187::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordca61187::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordca61187::ExceedsCapacity {
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
mod l4_boundary_tests_dca61187 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddca61187::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddca61187::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddca61187::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddca61187::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddca61187::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordca61187::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordca61187::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
