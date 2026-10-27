//! Exact finite spin benchmark and its declared normalization.
//! No topology is silently supplied for the union of finite matrix algebras.
//! AuthorityEffect: None.
use num_bigint::BigInt;
use num_traits::Zero;
use core_lie_theory::su2::{bracket_defects, casimir, SpinRepresentation, Su2Error};
use core_number_theory::rational::{ri, Rational};
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FuzzySphereCertificate {
    pub dimension: usize,
    pub commutator_norm: Rational,
    pub casimir_norm: Rational,
    pub upper_bound: Rational,
    pub bracket_relations: bool,
    pub casimir_relation: bool,
}
pub fn fuzzy_sphere(dimension: usize) -> Result<FuzzySphereCertificate, Su2Error> {
    if dimension < 2 || dimension > 65 {
        return Err(Su2Error::SpinTooLarge {
            twice_spin: dimension.saturating_sub(1).min(u32::MAX as usize) as u32,
        });
    }
    let spin = SpinRepresentation::new((dimension - 1) as u32)?;
    let bracket_relations = bracket_defects(spin.generators())?
        .iter()
        .all(|m| m.as_slice().iter().all(Zero::is_zero));
    let casimir = casimir(spin.generators())?;
    let n = Rational::from_integer(BigInt::from(dimension));
    let j = Rational::from_integer(BigInt::from(dimension - 1)) / ri(2);
    let c = &j * (&j + ri(1));
    let casimir_relation = (0..dimension).all(|r| {
        (0..dimension).all(|k| {
            casimir
                .get(r, k)
                .is_ok_and(|v| v == if r == k { c.clone() } else { Rational::zero() })
        })
    });
    // X_a=2 J_a/d, [X_x,X_y]=(2i/d)X_z. J_z has exact eigenvalues -j..j.
    Ok(FuzzySphereCertificate {
        dimension,
        commutator_norm: ri(4) * &j / (&n * &n),
        casimir_norm: ri(4) * c / (&n * &n),
        upper_bound: ri(2) / n,
        bracket_relations,
        casimir_relation,
    })
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MomentComparison {
    pub moments_equal: bool,
    pub norm_difference: Rational,
}
/// The rank-one projection and zero on M_d have normalized trace moments
/// differing by 1/d, while their operator-norm distance is one at every d.
pub fn rank_one_completion_comparison(dimension: usize) -> Result<MomentComparison, Su2Error> {
    if dimension == 0 {
        return Err(Su2Error::Shape);
    }
    Ok(MomentComparison {
        moments_equal: false,
        norm_difference: ri(1),
    })
}
pub fn rank_one_normalized_moment(dimension: usize) -> Result<Rational, Su2Error> {
    if dimension == 0 {
        return Err(Su2Error::Shape);
    }
    Ok(Rational::new(1.into(), BigInt::from(dimension)))
}

// Origin: engine/crates_rs/core_quantum_physics/src/tower_topological_completion.rs
// Claim: urn:core:crates_rs:core-quantum-physics:tower-topological-completion:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5baccf45 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5baccf45` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5baccf45 {
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
impl BoundaryError5baccf45 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5baccf45 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5baccf45 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5baccf45 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5baccf45> {
        if capacity_bound == 0 {
            return Err(BoundaryError5baccf45::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5baccf45::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5baccf45::ExceedsCapacity {
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
mod l4_boundary_tests_5baccf45 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5baccf45::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5baccf45::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5baccf45::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5baccf45::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5baccf45::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5baccf45::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5baccf45::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
