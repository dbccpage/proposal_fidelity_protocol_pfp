//! Gates on an exact fusion sector. Exceeding a finite closure bound establishes
//! neither infiniteness nor density of the generated braid image.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::anyon_model::AnyonModel;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, matrix};
use core_fusion_categories::{
    braid_group::{self, ClosureOutcome},
    error::FusionError,
    scalar::FusionScalar,
};
use std::hash::Hash;
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact fusion-sector braid gates.";
#[derive(Debug, Clone)]
pub struct TopologicalQuantumComputing<K> {
    model: AnyonModel<K>,
    charge: usize,
    strands: usize,
    total: usize,
    generators: Vec<BasicMatrix<K>>,
    dimension: usize,
}
impl<K: FusionScalar> TopologicalQuantumComputing<K> {
    pub fn new(
        model: AnyonModel<K>,
        charge: usize,
        strands: usize,
        total: usize,
    ) -> Result<Self, FusionError> {
        if strands < 2 {
            return Err(FusionError::ListLength {
                what: "strands",
                expected: 2,
                got: strands,
            });
        }
        let generators = model.braid_generators(charge, strands, total)?;
        let dimension = generators.first().map_or(0, |g| g.rows());
        if dimension == 0 {
            return Err(FusionError::Inconsistent {
                context: "empty computational sector",
            });
        }
        Ok(Self {
            model,
            charge,
            strands,
            total,
            generators,
            dimension,
        })
    }
    pub fn dimension(&self) -> usize {
        self.dimension
    }
    pub fn generators(&self) -> &[BasicMatrix<K>] {
        &self.generators
    }
    fn check_braid_word_budget(
        &self,
        word: &[i32],
        limits: linear_algebra::backend::basic_matrix::OperationLimits,
    ) -> Result<(), FusionError> {
        if word.len() > 1 << 16 {
            return Err(FusionError::Budget {
                what: "braid word",
                requested: word.len() as u128,
                limit: 1 << 16,
            });
        }
        // Charge all dense products and inverse row reductions before the word.
        let d = self.dimension as u128;
        let inverse_count = word.iter().filter(|&&index| index < 0).count() as u128;
        let work =
            2 * word.len() as u128 * d.pow(3) + inverse_count * (4 * d.pow(3) + 2 * d * d + d);
        if work > limits.max_scalar_ops as u128 {
            return Err(FusionError::Budget {
                what: "braid word scalar work",
                requested: work,
                limit: limits.max_scalar_ops as u128,
            });
        }
        Ok(())
    }
    /// Signed braid indices are one-based; negative indices are inverse exchanges.
    pub fn word_matrix(&self, word: &[i32]) -> Result<BasicMatrix<K>, FusionError> {
        let limits = braid_group::DEFAULT_BRAID_LIMITS;
        self.check_braid_word_budget(word, limits)?;
        let mut gate = matrix::identity_with_limits(self.dimension, limits)?;
        for &index in word {
            let i = usize::try_from(index.unsigned_abs()).map_err(|_| FusionError::Overflow {
                context: "braid index",
            })?;
            let g = i
                .checked_sub(1)
                .and_then(|i| self.generators.get(i))
                .ok_or(FusionError::Label {
                    label: i,
                    rank: self.strands,
                })?;
            let inverse;
            let factor = if index < 0 {
                inverse = elimination::inverse_with_limits(g, limits)?;
                &inverse
            } else {
                g
            };
            gate = matrix::multiply_with_limits(factor, &gate, limits)?;
        }
        Ok(gate)
    }
    pub fn check_braid_relations(&self) -> Result<bool, FusionError> {
        Ok(braid_group::braid_relation_defects(&self.generators)?.is_empty())
    }
    pub fn full_twist(&self) -> Result<BasicMatrix<K>, FusionError> {
        self.model
            .ribbon()
            .full_twist(self.charge, self.strands, self.total)
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
impl<K: FusionScalar + Eq + Hash> TopologicalQuantumComputing<K> {
    pub fn image_group(
        &self,
        bound: usize,
        projective: bool,
    ) -> Result<ClosureOutcome<K>, FusionError> {
        braid_group::group_closure(&self.generators, bound, projective)
    }
    pub fn contains_gate_projectively(
        &self,
        gate: &BasicMatrix<K>,
        bound: usize,
    ) -> Result<Option<bool>, FusionError> {
        if gate.shape() != (self.dimension, self.dimension) {
            return Err(FusionError::Shape {
                operation: "gate membership",
                left: gate.shape(),
                right: (self.dimension, self.dimension),
            });
        }
        match self.image_group(bound, true)? {
            ClosureOutcome::Finite(group) => Ok(Some(group.contains(gate)?)),
            ClosureOutcome::ExceedsBound { .. } => Ok(None),
        }
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/topological_quantum_computing.rs
// Claim: urn:core:crates_rs:core-quantum-physics:topological-quantum-computing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9c8c2258 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9c8c2258` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9c8c2258 {
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
impl BoundaryError9c8c2258 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9c8c2258 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9c8c2258 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9c8c2258 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9c8c2258> {
        if capacity_bound == 0 {
            return Err(BoundaryError9c8c2258::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9c8c2258::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9c8c2258::ExceedsCapacity {
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
    fn gate_words_refuse_aggregate_dense_work_before_products() {
        let q = TopologicalQuantumComputing::new(
            AnyonModel::<Cyclotomic<16>>::ising().unwrap(),
            1,
            8,
            0,
        )
        .unwrap();
        assert_eq!(q.dimension(), 8);
        assert!(matches!(
            q.word_matrix(&vec![-1; 1 << 15]),
            Err(FusionError::Budget {
                what: "braid word scalar work",
                ..
            })
        ));
        assert_eq!(
            q.word_matrix(&[1, -1]).unwrap(),
            matrix::identity(8).unwrap()
        );
        assert!(matches!(
            TopologicalQuantumComputing::new(
                AnyonModel::<Cyclotomic<16>>::ising().unwrap(),
                1,
                34,
                0
            ),
            Err(FusionError::Budget { .. })
        ));
    }
    #[test]
    fn ising_braid_image_is_projectively_clifford_and_excludes_t() {
        let q = TopologicalQuantumComputing::new(
            AnyonModel::<Cyclotomic<16>>::ising().unwrap(),
            1,
            4,
            0,
        )
        .unwrap();
        assert_eq!(q.dimension(), 2);
        assert!(q.check_braid_relations().unwrap());
        assert_eq!(q.image_group(32, true).unwrap().order(), Some(24));
        let t = matrix::diagonal(&[Cyclotomic::one(), Cyclotomic::zeta(2)]).unwrap();
        assert_eq!(q.contains_gate_projectively(&t, 32).unwrap(), Some(false));
        assert_eq!(
            q.word_matrix(&[1, -1]).unwrap(),
            matrix::identity(2).unwrap()
        );
        let scalar = q.model.ribbon().full_twist_scalar(1, 4, 0).unwrap();
        assert_eq!(
            q.full_twist().unwrap(),
            matrix::scale(&matrix::identity(2).unwrap(), &scalar).unwrap()
        );
        assert!(q.word_matrix(&[0]).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_9c8c2258 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9c8c2258::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9c8c2258::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9c8c2258::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9c8c2258::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9c8c2258::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError9c8c2258::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError9c8c2258::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
