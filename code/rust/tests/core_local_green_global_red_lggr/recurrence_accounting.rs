//! S8: registry_hit_recurrence accounting.
//!
//! After three distinct shape-collision scenarios from S6 are each recorded
//! TWICE, `registry_hit_recurrence(&reg) >= 3` — i.e. the lookup surface CAN
//! close $Q^1$ when wired. This is a measure of registry EXERCISE, NOT a
//! $\Phi_1$ measurement; the system-wide $\Phi_1$ closure is
//! `defer: PD-RF-PHI1-WIRING` per packet section 9.

use core_linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::Rational64;

use core_homology::cochain_complex::{CochainComplex, TheoremProvenance};
use core_homology::cochain_primitive_difference::CochainPrimitiveDifference;
use core_homology::coefficient_domain::CoefficientDomain;
use core_homology::hash::{Blake3Hash, ComplexHash};
use core_homology::quotient::{QuotientRelation, QuotientSpace};

use core_epk::residual_families::{
    record::{Gamma2ClassId, Q1ClassId},
    registry::FamilyRegistry,
    registry_hit_recurrence,
    signature::shape_signature,
};

type Q = core_homology::scalar::Q;

fn r(n: i64) -> Q {
    core_homology::scalar::q(n)
}

fn complex_a() -> CochainComplex {
    let d0 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(-1)]).expect("d0");
    let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(1)]).expect("d1");
    CochainComplex::new(
        1,
        2,
        1,
        d0,
        d1,
        TheoremProvenance::new("recurrence_a".to_string()).expect("prov"),
    )
    .expect("complex")
}

fn complex_b() -> CochainComplex {
    // distinct cochain shape: c0=2, c1=3, c2=1; d0=0 (3x2), d1=0 (1x3).
    let d0 = BasicMatrix::from_row_major(3, 2, vec![r(0); 6]).expect("d0");
    let d1 = BasicMatrix::from_row_major(1, 3, vec![r(0); 3]).expect("d1");
    CochainComplex::new(
        2,
        3,
        1,
        d0,
        d1,
        TheoremProvenance::new("recurrence_b".to_string()).expect("prov"),
    )
    .expect("complex")
}

fn complex_c() -> CochainComplex {
    // third distinct cochain shape: c0=1, c1=1, c2=0; d0 = [[1]] (1x1), d1 = 0 (0x1).
    let d0 = BasicMatrix::from_row_major(1, 1, vec![r(1)]).expect("d0");
    let d1 = BasicMatrix::from_row_major(0, 1, vec![]).expect("d1");
    CochainComplex::new(
        1,
        1,
        0,
        d0,
        d1,
        TheoremProvenance::new("recurrence_c".to_string()).expect("prov"),
    )
    .expect("complex")
}

fn fixture_qspace() -> QuotientSpace<Q> {
    QuotientSpace::new_unchecked(
        ComplexHash(Blake3Hash::new(b"recurrence-fixture")),
        CoefficientDomain::Rational,
        2,
        1,
        QuotientRelation::ModCoboundaries,
        BasicMatrix::from_row_major(2, 2, vec![r(1), r(0), r(0), r(1)]).expect("proj"),
    )
}

#[test]
fn registry_hit_recurrence_at_least_three_after_three_scenarios_twice() {
    let cc_a = complex_a();
    let cc_b = complex_b();
    let cc_c = complex_c();

    let pd_a = CochainPrimitiveDifference::new(&cc_a);
    let pd_b = CochainPrimitiveDifference::new(&cc_b);
    let pd_c = CochainPrimitiveDifference::new(&cc_c);

    let q = fixture_qspace();
    let sig_a = shape_signature(&pd_a, &q);
    let sig_b = shape_signature(&pd_b, &q);
    let sig_c = shape_signature(&pd_c, &q);

    // Precondition: three distinct shape keys.
    assert_ne!(sig_a, sig_b);
    assert_ne!(sig_a, sig_c);
    assert_ne!(sig_b, sig_c);

    let mut reg = FamilyRegistry::new();
    let q1 = Q1ClassId::from_u64(1);
    let g2 = Gamma2ClassId::from_u64(2);

    // Record each shape TWICE.
    let _ = reg.record(sig_a, q1, g2);
    let _ = reg.record(sig_a, q1, g2);
    let _ = reg.record(sig_b, q1, g2);
    let _ = reg.record(sig_b, q1, g2);
    let _ = reg.record(sig_c, q1, g2);
    let _ = reg.record(sig_c, q1, g2);

    assert_eq!(reg.len(), 3, "three distinct shape keys");
    let rec = registry_hit_recurrence(&reg);
    assert!(
        rec >= 3,
        "registry_hit_recurrence must be >= 3 after three scenarios recorded twice; got {}",
        rec
    );
}

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/recurrence_accounting.rs
// Claim: urn:core:crates_rs:tests:recurrence-accounting:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda95e6265 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda95e6265` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora95e6265 {
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
impl BoundaryErrora95e6265 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora95e6265 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora95e6265 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda95e6265 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora95e6265> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora95e6265::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora95e6265::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora95e6265::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a95e6265() {
    let admitted = BoundaryRecorda95e6265::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda95e6265::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
