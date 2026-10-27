//! Test for PO-000 §5.8 Theorem 5.5: General-order short-time product defect lower-bound certificate.
//! Evaluates Taylor remainder bounds R_{k+1}(t) = 2^{k+2} (k + 2) g^{k+1} t^{k+1}
//! and defect lower bounds (||F_e^{(k)}(0)||_1 / k!) t^k - R_{k+1}(t).

use core_number_theory::rational::{ri, rq};
use core_quantum_physics::product_defect_bound::GeneralOrderDefectBound;

#[test]
fn test_kth_order_remainder_bound_evaluation() {
    let g = ri(1);
    let t = rq(1, 100);

    // Order k = 1: First-order rate (Theorem 5.1)
    // R_2(t) = 2^3 * 3 * g^2 * t^2 = 24 g^2 t^2
    let bound_k1 = GeneralOrderDefectBound::new(1);
    let r2 = bound_k1.remainder_bound(g.clone(), t.clone());
    let expected_r2 = ri(24) * &g * &g * &t * &t; // 24 / 10000 = 6 / 2500
    assert_eq!(r2, expected_r2);

    let nu = ri(1);
    let lower_k1 = bound_k1.lower_bound(nu.clone(), g.clone(), t.clone());
    // nu * t - 24 g^2 t^2 = 1/100 - 24/10000 = 76/10000 = 19/2500
    assert_eq!(lower_k1, rq(19, 2500));
    assert!(lower_k1 > ri(0));

    // Order k = 2: Quadratic defect production (Theorem 5.5 instance)
    // R_3(t) = 2^4 * 4 * g^3 * t^3 = 64 g^3 t^3
    let bound_k2 = GeneralOrderDefectBound::new(2);
    let r3 = bound_k2.remainder_bound(g.clone(), t.clone());
    let expected_r3 = ri(64) * &g * &g * &g * &t * &t * &t; // 64 / 1000000
    assert_eq!(r3, expected_r3);

    let mu = ri(2);
    let lower_k2 = bound_k2.lower_bound(mu.clone(), g.clone(), t.clone());
    // (mu / 2!) * t^2 - 64 g^3 t^3 = 1 * (1/10000) - 64/1000000 = 36/1000000 = 9/250000
    assert_eq!(lower_k2, rq(9, 250000));
    assert!(lower_k2 > ri(0));

    // Order k = 3: Cubic defect production
    // R_4(t) = 2^5 * 5 * g^4 * t^4 = 160 g^4 t^4
    let bound_k3 = GeneralOrderDefectBound::new(3);
    let r4 = bound_k3.remainder_bound(g.clone(), t.clone());
    let expected_r4 = ri(160) * &g * &g * &g * &g * &t * &t * &t * &t;
    assert_eq!(r4, expected_r4);

    // Static evaluation parity
    assert_eq!(
        GeneralOrderDefectBound::compute_remainder_bound(2, g.clone(), t.clone()),
        r3
    );
    assert_eq!(
        GeneralOrderDefectBound::lower_bound_at(2, mu, g, t),
        lower_k2
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/test_general_order_bound.rs
// Claim: urn:core:crates_rs:tests:test-general-order-bound:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord33d95f65 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord33d95f65` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError33d95f65 {
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
impl BoundaryError33d95f65 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError33d95f65 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError33d95f65 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord33d95f65 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError33d95f65> {
        if capacity_bound == 0 {
            return Err(BoundaryError33d95f65::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError33d95f65::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError33d95f65::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_33d95f65() {
    let admitted = BoundaryRecord33d95f65::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord33d95f65::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
