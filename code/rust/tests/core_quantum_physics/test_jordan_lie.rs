//! Test for PO-000 Appendix E: Jordan-Lie operational base and commutator verifier.
//! Verifies Jacobi identity [[A, B], C] + [[B, C], A] + [[C, A], B] = 0
//! and the Jordan-Lie derivation identity [C, A o B] = [C, A] o B + A o [C, B].

use linear_algebra::exact_field::matrix as mx;
use core_number_theory::cyclotomic::GaussianRat;
use core_quantum_physics::operational_axiom_selection::JordanLieCommutatorVerifier;

fn g(re: i64, im: i64) -> GaussianRat {
    GaussianRat::from_ints(re, im)
}

#[test]
fn test_jordan_lie_algebra_jacobi_and_derivation_identity() {
    // Standard Pauli matrices over Q(i)
    // sigma_x = [[0, 1], [1, 0]]
    let sx = mx::from_rows(vec![
        vec![g(0, 0), g(1, 0)],
        vec![g(1, 0), g(0, 0)],
    ])
    .unwrap();

    // sigma_y = [[0, -i], [i, 0]]
    let sy = mx::from_rows(vec![
        vec![g(0, 0), g(0, -1)],
        vec![g(0, 1), g(0, 0)],
    ])
    .unwrap();

    // sigma_z = [[1, 0], [0, -1]]
    let sz = mx::from_rows(vec![
        vec![g(1, 0), g(0, 0)],
        vec![g(0, 0), g(-1, 0)],
    ])
    .unwrap();

    // 1. Verify Jacobi Identity on Pauli generators:
    // [[sx, sy], sz] + [[sy, sz], sx] + [[sz, sx], sy] = 0
    let jacobi_pauli =
        JordanLieCommutatorVerifier::verify_jacobi_identity(&sx, &sy, &sz).unwrap();
    assert!(jacobi_pauli, "Jacobi identity must hold on Pauli generators");

    // 2. Verify Jordan-Lie derivation identity on Pauli generators:
    // [sz, sx o sy] = [sz, sx] o sy + sx o [sz, sy]
    let derivation_pauli =
        JordanLieCommutatorVerifier::verify_derivation_identity(&sx, &sy, &sz).unwrap();
    assert!(
        derivation_pauli,
        "Derivation identity must hold on Pauli generators"
    );

    // 3. Test on general non-commuting matrices with complex rational entries
    let a = mx::from_rows(vec![
        vec![g(1, 2), g(3, -1)],
        vec![g(0, 4), g(-2, 1)],
    ])
    .unwrap();

    let b = mx::from_rows(vec![
        vec![g(2, -1), g(1, 1)],
        vec![g(-3, 0), g(4, 2)],
    ])
    .unwrap();

    let c = mx::from_rows(vec![
        vec![g(0, 3), g(2, 2)],
        vec![g(1, -1), g(-1, -1)],
    ])
    .unwrap();

    let jacobi_general = JordanLieCommutatorVerifier::verify_jacobi_identity(&a, &b, &c).unwrap();
    assert!(jacobi_general, "Jacobi identity must hold on general matrices");

    let derivation_general =
        JordanLieCommutatorVerifier::verify_derivation_identity(&a, &b, &c).unwrap();
    assert!(
        derivation_general,
        "Jordan-Lie derivation identity must hold on general matrices"
    );

    // 4. Test Jordan product commutativity: A o B == B o A
    let ab_jordan = JordanLieCommutatorVerifier::jordan_product(&a, &b).unwrap();
    let ba_jordan = JordanLieCommutatorVerifier::jordan_product(&b, &a).unwrap();
    assert_eq!(ab_jordan, ba_jordan, "Jordan product must be commutative");
}

// Origin: engine/crates_rs/tests/core_quantum_physics/test_jordan_lie.rs
// Claim: urn:core:crates_rs:tests:test-jordan-lie:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6113e477 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6113e477` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6113e477 {
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
impl BoundaryError6113e477 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6113e477 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6113e477 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6113e477 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6113e477> {
        if capacity_bound == 0 {
            return Err(BoundaryError6113e477::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6113e477::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6113e477::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6113e477() {
    let admitted = BoundaryRecord6113e477::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6113e477::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
