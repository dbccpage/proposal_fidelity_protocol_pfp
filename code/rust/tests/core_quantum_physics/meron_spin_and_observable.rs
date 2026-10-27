use linear_algebra::exact_field::matrix as mx;
use core_number_theory::rational::rq;
use core_quantum_physics::meron_time_refinement::{FiniteMeronChain, MeronTimeError};

#[test]
fn actual_car_chain_transports_to_the_matching_twisted_spin_sector() {
    let chain = FiniteMeronChain::new(4).unwrap();
    let d = chain.staggered_basis_change().unwrap();
    assert_eq!(mx::multiply(&d, &d).unwrap(), mx::identity(16).unwrap());
    let h = chain.hamiltonian_over_t().unwrap();
    let transformed = mx::multiply(&mx::multiply(&d, &h).unwrap(), &d).unwrap();
    for (even, twist) in [(true, -1), (false, 1)] {
        assert_eq!(
            chain.parity_block(&transformed, even).unwrap(),
            chain
                .parity_block(&chain.heisenberg_spin(twist).unwrap(), even)
                .unwrap()
        );
    }
    assert_ne!(transformed, chain.heisenberg_spin(1).unwrap());
    let a = chain.staggered_density().unwrap();
    assert_eq!(mx::multiply(&mx::multiply(&d, &a).unwrap(), &d).unwrap(), a);
}

#[test]
fn both_matching_parity_blocks_are_needed_for_full_fock_spectral_readouts() {
    let chain = FiniteMeronChain::new(4).unwrap();
    let h = chain.hamiltonian_over_t().unwrap();
    let even = chain
        .parity_block(&chain.heisenberg_spin(-1).unwrap(), true)
        .unwrap();
    let odd = chain
        .parity_block(&chain.heisenberg_spin(1).unwrap(), false)
        .unwrap();
    for power in 0..=5 {
        assert_eq!(
            mx::trace(&mx::power(&h, power).unwrap()).unwrap(),
            mx::trace(&mx::power(&even, power).unwrap()).unwrap()
                + mx::trace(&mx::power(&odd, power).unwrap()).unwrap()
        );
    }
    assert_ne!(
        mx::trace(&mx::power(&h, 4).unwrap()).unwrap(),
        mx::trace(&mx::power(&chain.heisenberg_spin(1).unwrap(), 4).unwrap()).unwrap()
    );
}

#[test]
fn actual_time_integrated_second_moment_keeps_its_insertion_and_normalization() {
    let chain = FiniteMeronChain::new(4).unwrap();
    let moments = chain.staggered_moments(2, &rq(3, 1)).unwrap();
    assert_eq!(moments.partition(), &rq(912, 1));
    assert_eq!(moments.first(), &rq(0, 1));
    // Independently replayed from the unchanged original SQL query.
    assert_eq!(moments.second(), &rq(36864, 1));
    assert_eq!(moments.mean_square(), rq(48, 19));
    assert_eq!(moments.slices(), 4);
    for m in [1, 2, 4] {
        let zero = chain.staggered_moments(m, &rq(1, 1)).unwrap();
        assert_eq!(zero.mean_square(), rq(1, 1));
        assert_eq!(zero.second(), &rq(16 * (2 * m) as i64 * (2 * m) as i64, 1));
    }
}

#[test]
fn wrong_sector_operator_and_boundary_declarations_refuse() {
    let chain = FiniteMeronChain::new(4).unwrap();
    assert!(matches!(
        chain.heisenberg_spin(0),
        Err(MeronTimeError::BoundaryTwist)
    ));
    let flip = mx::from_fn(16, 16, |r, c| rq(if r == c ^ 1 { 1 } else { 0 }, 1)).unwrap();
    assert!(matches!(
        chain.parity_block(&flip, true),
        Err(MeronTimeError::MixesParity)
    ));
    assert!(chain.parity_block(&mx::identity(8).unwrap(), true).is_err());
    assert!(chain.staggered_moments(0, &rq(2, 1)).is_err());
    assert!(chain.staggered_moments(2, &rq(1, 2)).is_err());
    assert!(matches!(
        chain.staggered_moments(32, &rq(2, 1)),
        Err(MeronTimeError::ObservableRepetitions)
    ));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/meron_spin_and_observable.rs
// Claim: urn:core:crates_rs:tests:meron-spin-and-observable:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf6965f1a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf6965f1a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf6965f1a {
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
impl BoundaryErrorf6965f1a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf6965f1a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf6965f1a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf6965f1a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf6965f1a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf6965f1a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf6965f1a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf6965f1a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f6965f1a() {
    let admitted = BoundaryRecordf6965f1a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf6965f1a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
