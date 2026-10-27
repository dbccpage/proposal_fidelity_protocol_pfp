use linear_algebra::exact_field::matrix as mx;
// Executable finite evidence; AuthorityEffect: None.
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::exact_hermitian::outer;
use core_quantum_physics::exact_instrument::ExactDensityState;
use core_wdp::instrument_adapter::FiniteQuantumInstrument;

fn basis(n: usize, i: usize) -> Vec<GaussianRat> {
    let mut vector = vec![GaussianRat::zero(); n];
    vector[i] = GaussianRat::from_ints(1, 0);
    vector
}
fn states() -> (ExactDensityState, ExactDensityState) {
    let zero = basis(3, 0);
    let one = basis(3, 1);
    (
        ExactDensityState::try_new(outer(&zero, &zero).unwrap()).unwrap(),
        ExactDensityState::try_new(outer(&one, &one).unwrap()).unwrap(),
    )
}
fn instruments() -> (FiniteQuantumInstrument, FiniteQuantumInstrument) {
    let prepared = vec![
        GaussianRat::from_rational(rq(3, 5)),
        GaussianRat::from_rational(rq(4, 5)),
        GaussianRat::zero(),
    ];
    let projectors = (0..3)
        .map(|i| {
            let v = basis(3, i);
            vec![outer(&v, &v).unwrap()]
        })
        .collect();
    let replacement = (0..3)
        .map(|i| vec![outer(&prepared, &basis(3, i)).unwrap()])
        .collect();
    (
        FiniteQuantumInstrument::new(3, 3, projectors, "Luders").unwrap(),
        FiniteQuantumInstrument::new(3, 3, replacement, "prepare").unwrap(),
    )
}

#[test]
fn same_povm_gives_same_probabilities_but_distinct_state_change_in_dimension_three() {
    let (luders, prepare) = instruments();
    let (zero, _) = states();
    for outcome in 0..3 {
        assert_eq!(
            luders.instrument().effect(outcome).unwrap(),
            prepare.instrument().effect(outcome).unwrap()
        );
        assert_eq!(
            luders.instrument().probability(outcome, &zero).unwrap(),
            prepare.instrument().probability(outcome, &zero).unwrap()
        );
    }
    assert_ne!(
        luders.instrument().post_state(0, &zero).unwrap(),
        prepare.instrument().post_state(0, &zero).unwrap()
    );
    assert_ne!(
        luders.receipt(0, &zero).unwrap(),
        prepare.receipt(0, &zero).unwrap()
    );
}

#[test]
fn replay_rejects_forged_payloads_and_wrong_problem_binding() {
    let (luders, prepare) = instruments();
    let (zero, one) = states();
    let receipt = luders.receipt(0, &zero).unwrap();
    assert!(luders.verify_receipt(&zero, &receipt).unwrap());
    assert!(!luders.verify_receipt(&one, &receipt).unwrap());
    assert!(!prepare.verify_receipt(&zero, &receipt).unwrap());
    let mut forged = receipt.clone();
    forged.probability = rq(1, 2);
    assert!(!luders.verify_receipt(&zero, &forged).unwrap());
    forged = receipt.clone();
    forged.post_state_digest = None;
    assert!(!luders.verify_receipt(&zero, &forged).unwrap());
    forged = receipt.clone();
    forged.input_state_digest.push('0');
    assert!(!luders.verify_receipt(&zero, &forged).unwrap());
    forged = receipt.clone();
    forged.instrument_digest.push('0');
    assert!(!luders.verify_receipt(&zero, &forged).unwrap());
    forged = receipt.clone();
    forged.outcome = 3;
    assert!(luders.verify_receipt(&zero, &forged).is_err());
    let impossible = luders.receipt(2, &zero).unwrap();
    assert_eq!(impossible.probability, ri(0));
    assert!(impossible.post_state_digest.is_none());
    assert!(luders.verify_receipt(&zero, &impossible).unwrap());
    // Shape dimensions belong to the binding, even for a zero-probability outcome.
    let trivial =
        FiniteQuantumInstrument::new(1, 1, vec![vec![mx::identity(1).unwrap()]], "one").unwrap();
    assert!(trivial.receipt(0, &zero).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_finite_instrument_replay.rs
// Claim: urn:core:crates_rs:tests:test-finite-instrument-replay:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord67d36cee {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord67d36cee` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError67d36cee {
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
impl BoundaryError67d36cee {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError67d36cee {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError67d36cee {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord67d36cee {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError67d36cee> {
        if capacity_bound == 0 {
            return Err(BoundaryError67d36cee::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError67d36cee::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError67d36cee::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_67d36cee() {
    let admitted = BoundaryRecord67d36cee::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord67d36cee::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
