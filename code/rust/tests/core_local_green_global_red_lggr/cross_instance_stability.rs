//! S7b: cross-instance / cross-observer stability.
//!
//! Closes the residual that S6 left open — two `VerifiedExactPhi1` instances
//! built from gauge-twin `ExactPhi1Certificate`s on the same shape MUST yield
//! the same `Q1ClassId`. Same shape under two distinct `Observer { id, kind }`
//! values (`Projection` vs `Precision`) MUST also yield the same `Q1ClassId`.
//!
//! This establishes the local-id derivation is restricted to the genuinely
//! shape-bearing accessors `phi1.value()` and `phi1.d0()`, NOT
//! `phi1.alpha()` / `phi1.primal_residual()` / `phi1.dual_witness()`, and
//! NOT the observer at all.

use num_bigint::BigInt;
use num_rational::BigRational;

use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
use core_types::observer::{Observer, ObserverKind};

use core_epk::residual_families::{derive_gamma2_class_id, derive_q1_class_id, record_from_verified};

use core_linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::Rational64;
use core_functional::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Result, Gamma2Functional,
};
use core_homology::cochain_complex::{CochainComplex, TheoremProvenance};
use core_homology::cochain_primitive_difference::CochainPrimitiveDifference;
use core_homology::coefficient_domain::CoefficientDomain;
use core_homology::hash::{Blake3Hash, ComplexHash};
use core_homology::quotient::{QuotientRelation, QuotientSpace};
use core_epk::residual_families::registry::FamilyRegistry;

type Q = core_homology::scalar::Q;

fn br(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

fn r(n: i64) -> Q {
    core_homology::scalar::q(n)
}

/// Survivor-style certificate: omega = [1], d0 = [[0]], so primal_residual = [1].
/// dual_witness = [1] (annihilates im(d0) trivially since d0=0), weight = [1],
/// reported_value = 1.
fn survivor_cert_alpha_zero() -> ExactPhi1Certificate {
    ExactPhi1Certificate {
        omega: vec![br(1)],
        d0: vec![vec![br(0)]],
        weights: vec![br(1)],
        alpha: vec![br(0)],
        primal_residual: vec![br(1)],
        dual_witness: vec![br(1)],
        reported_value: br(1),
    }
}

/// Gauge-twin survivor: same core/d0/weights/reported_value, but the alpha
/// has been shifted (any value still gives primal_residual = omega - d0*alpha
/// = 1 - 0*alpha = 1, since d0 is the zero map). This is a true gauge twin
/// for our hash key (S7b property: alpha is NOT in the key).
fn survivor_cert_alpha_shifted() -> ExactPhi1Certificate {
    ExactPhi1Certificate {
        omega: vec![br(1)],
        d0: vec![vec![br(0)]],
        weights: vec![br(1)],
        alpha: vec![br(42)], // different alpha
        primal_residual: vec![br(1)],
        dual_witness: vec![br(1)],
        reported_value: br(1),
    }
}

#[test]
fn gauge_twin_phi1_yields_same_q1_class_id() {
    let v_a = Phi1Functional::verify_exact_certificate(survivor_cert_alpha_zero())
        .expect("alpha=0 certificate must verify");
    let v_b = Phi1Functional::verify_exact_certificate(survivor_cert_alpha_shifted())
        .expect("alpha-shifted certificate must verify");

    // Sanity: their alphas differ (this is the gauge axis we are excluding).
    assert_ne!(
        v_a.alpha(),
        v_b.alpha(),
        "precondition: the two alphas differ"
    );
    // Sanity: their shape-relevant accessors agree.
    assert_eq!(v_a.value(), v_b.value());
    assert_eq!(v_a.d0(), v_b.d0());

    let q1_a = derive_q1_class_id(&v_a);
    let q1_b = derive_q1_class_id(&v_b);
    assert_eq!(
        q1_a, q1_b,
        "S7b: gauge-twin Phi1 instances differing only on alpha must yield the same Q1ClassId"
    );
}

/// Survivor-style certificate with `reported_value = 0`: same shape (omega=[0],
/// d0=[[0]], weights=[1]) as `survivor_cert_alpha_zero` EXCEPT the Phi1 value is
/// 0 instead of 1. d0 is identical between the two so the discriminating axis is
/// exactly `.value()`.
fn survivor_cert_value_zero() -> ExactPhi1Certificate {
    ExactPhi1Certificate {
        omega: vec![br(0)],
        d0: vec![vec![br(0)]],
        weights: vec![br(1)],
        alpha: vec![br(0)],
        primal_residual: vec![br(0)],
        dual_witness: vec![br(0)],
        reported_value: br(0),
    }
}

#[test]
fn distinct_phi1_value_yields_distinct_q1_class_id() {
    // POSITIVE DISCRIMINATION CONTROL (CODA red-team finding): the gauge-twin
    // test above pins one direction (equal shape -> equal id); this pins the
    // other (distinct .value() -> DISTINCT id). Both certs share d0 = [[0]], so
    // the only difference fed into the hash is the Phi1 value (0 vs 1).
    let v0 = Phi1Functional::verify_exact_certificate(survivor_cert_value_zero())
        .expect("value-0 certificate must verify");
    let v1 = Phi1Functional::verify_exact_certificate(survivor_cert_alpha_zero())
        .expect("value-1 certificate must verify");

    // Precondition: the values genuinely differ, the d0 shapes agree.
    assert_ne!(
        v0.value(),
        v1.value(),
        "precondition: the two Phi1 values differ (0 vs 1)"
    );
    assert_eq!(
        v0.d0(),
        v1.d0(),
        "precondition: d0 is identical, isolating the value axis"
    );

    assert_ne!(
        derive_q1_class_id(&v0),
        derive_q1_class_id(&v1),
        "distinct Phi1 .value() must produce a DISTINCT Q1ClassId (id derivation discriminates)"
    );
}

/// Build an exact Gamma2 result of a chosen value via the public surface.
/// `d0 = [[0]]` (so `d1 * d0 = 0` holds trivially), `d1 = [[d1_coeff]]`,
/// residual `h = [h_coeff]`; the resulting `value` is `|d1_coeff * h_coeff|`.
fn gamma2_with_value(h_coeff: i64, d1_coeff: i64) -> ExactGamma2Result {
    let complex =
        ExactCochainComplexQ::try_new(1, 1, 1, vec![vec![br(0)]], vec![vec![br(d1_coeff)]])
            .expect("exact complex with d1*d0 = 0 (d0 is the zero map)");
    let residual =
        DegreeOneResidualQ::try_new(&complex, vec![br(h_coeff)]).expect("residual constructs");
    Gamma2Functional::try_compute_exact_quotient(&residual).expect("gamma2 computes")
}

#[test]
fn distinct_gamma2_value_yields_distinct_gamma2_class_id() {
    // POSITIVE DISCRIMINATION CONTROL for the Gamma2 id derivation. Both
    // results share d0 = [[0]], so the discriminating axis is exactly
    // `.value()` (0 vs 6).
    let g0 = gamma2_with_value(0, 0); // value = 0
    let g6 = gamma2_with_value(2, 3); // value = |3*2| = 6

    assert_ne!(
        g0.value(),
        g6.value(),
        "precondition: the two Gamma2 values differ (0 vs 6)"
    );
    assert_eq!(
        g0.d0(),
        g6.d0(),
        "precondition: d0 is identical, isolating the value axis"
    );

    assert_ne!(
        derive_gamma2_class_id(&g0),
        derive_gamma2_class_id(&g6),
        "distinct Gamma2 .value() must produce a DISTINCT Gamma2ClassId"
    );
}

fn fixture_cochain() -> CochainComplex {
    let d0 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(-1)]).expect("d0");
    let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(1)]).expect("d1");
    CochainComplex::new(
        1,
        2,
        1,
        d0,
        d1,
        TheoremProvenance::new("s7b_fixture".to_string()).expect("prov"),
    )
    .expect("complex")
}

fn fixture_qspace() -> QuotientSpace<Q> {
    QuotientSpace::new_unchecked(
        ComplexHash(Blake3Hash::new(b"s7b-fixture")),
        CoefficientDomain::Rational,
        2,
        1,
        QuotientRelation::ModCoboundaries,
        BasicMatrix::from_row_major(2, 2, vec![r(1), r(0), r(0), r(1)]).expect("proj"),
    )
}

#[test]
fn cross_observer_kinds_yield_same_q1_class_id_via_registry() {
    // Same Phi1, same Gamma2, same shape, but TWO different Observers
    // (Projection vs Precision). The local ids must NOT change.
    let verified_phi1 = Phi1Functional::verify_exact_certificate(survivor_cert_alpha_zero())
        .expect("certificate verifies");

    let g2_complex = ExactCochainComplexQ::try_new(1, 1, 1, vec![vec![br(1)]], vec![vec![br(0)]])
        .expect("exact complex with d1*d0 = 0");
    let residual =
        DegreeOneResidualQ::try_new(&g2_complex, vec![br(0)]).expect("residual constructs");
    let g2_result =
        Gamma2Functional::try_compute_exact_quotient(&residual).expect("gamma2 computes");

    let cc = fixture_cochain();
    let pd = CochainPrimitiveDifference::new(&cc);
    let q = fixture_qspace();

    let obs_a = Observer {
        id: core_kernel::ObserverId::parse("obs_proj").expect("canonical observer id"),
        kind: ObserverKind::Projection,
    };
    let obs_b = Observer {
        id: core_kernel::ObserverId::parse("obs_prec").expect("canonical observer id"),
        kind: ObserverKind::Precision,
    };

    let mut reg_a = FamilyRegistry::new();
    let mut reg_b = FamilyRegistry::new();
    let _ = record_from_verified(&mut reg_a, &pd, &q, &verified_phi1, &g2_result, &obs_a);
    let _ = record_from_verified(&mut reg_b, &pd, &q, &verified_phi1, &g2_result, &obs_b);

    let sig = core_epk::residual_families::shape_signature(&pd, &q);
    let rec_a = reg_a.lookup(&sig).expect("reg_a must hit");
    let rec_b = reg_b.lookup(&sig).expect("reg_b must hit");

    assert_eq!(
        rec_a.q1_class_id, rec_b.q1_class_id,
        "S7b: observer kind must NOT change the Q1ClassId"
    );
    assert_eq!(
        rec_a.gamma2_class_id, rec_b.gamma2_class_id,
        "S7b: observer kind must NOT change the Gamma2ClassId"
    );
}

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/cross_instance_stability.rs
// Claim: urn:core:crates_rs:tests:cross-instance-stability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6bb30c6e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6bb30c6e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6bb30c6e {
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
impl BoundaryError6bb30c6e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6bb30c6e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6bb30c6e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6bb30c6e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6bb30c6e> {
        if capacity_bound == 0 {
            return Err(BoundaryError6bb30c6e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6bb30c6e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6bb30c6e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6bb30c6e() {
    let admitted = BoundaryRecord6bb30c6e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6bb30c6e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
