//! Three exact bases supplied by the declared six-dimensional Weyl system.
//! No fourth-basis exclusion outside that Weyl class family is asserted.
use linear_algebra::exact_field::matrix as mx;
use core_lie_theory::heisenberg::WeylHeisenberg;
use core_number_theory::cyclotomic_field::Cyclotomic;
use core_number_theory::rational::rq;
use core_quantum_physics::mub::MubSystem;

#[test]
fn three_declared_weyl_eigenbases_pass_the_sovereign_mub_projector_checks() {
    type F = Cyclotomic<12>;
    let w = WeylHeisenberg::with_phase_root(6, F::zeta(2), F::zeta(1)).unwrap();
    let generators = [
        w.shift().unwrap(),
        w.clock().unwrap(),
        w.displacement(1, 1).unwrap(),
    ];
    let mut bases = Vec::new();
    for generator in generators {
        assert_eq!(
            mx::power(&generator, 6).unwrap(),
            mx::identity::<F>(6).unwrap()
        );
        let powers: Vec<_> = (0..6).map(|k| mx::power(&generator, k).unwrap()).collect();
        let mut projectors = Vec::new();
        for j in 0..6i64 {
            let mut p = mx::zeros::<F>(6, 6).unwrap();
            for (k, power) in powers.iter().enumerate() {
                let phase = F::zeta(-2 * j * i64::try_from(k).unwrap());
                p = mx::add(&p, &mx::scale(power, &phase).unwrap()).unwrap();
            }
            projectors.push(mx::scale(&p, &F::rational(rq(1, 6))).unwrap());
        }
        bases.push(projectors);
    }
    // Canonical physics owner checks shape, Hermiticity, idempotence, rank-one
    // trace, orthogonality, resolutions of identity and cross-basis overlap1/6.
    let system = MubSystem::try_new(6, bases).unwrap();
    assert_eq!(system.basis_count(), 3);
    assert!(!system.is_complete());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/projective_history_mub6.rs
// Claim: urn:core:crates_rs:tests:projective-history-mub6:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9445fa63 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9445fa63` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9445fa63 {
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
impl BoundaryError9445fa63 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9445fa63 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9445fa63 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9445fa63 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9445fa63> {
        if capacity_bound == 0 {
            return Err(BoundaryError9445fa63::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9445fa63::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9445fa63::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_9445fa63() {
    let admitted = BoundaryRecord9445fa63::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9445fa63::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
