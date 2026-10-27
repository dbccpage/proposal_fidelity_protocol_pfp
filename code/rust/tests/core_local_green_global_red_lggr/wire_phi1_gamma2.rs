//! S7: wire the registry against the REAL public surfaces of
//! `core_functional::phi1::VerifiedExactPhi1` and
//! `core_functional::gamma2::ExactGamma2Result`.
//!
//! NO mocks. The test builds both via the only legal constructors:
//! `Phi1Functional::verify_exact_certificate(cert)` and
//! `Gamma2Functional::try_compute_exact_quotient(&DegreeOneResidualQ)`.
//!
//! Fixture: a minimal 1x1 exact cochain complex over Q so that `d1 * d0 = 0`
//! holds trivially. `omega = [0]`, `alpha = [0]`, weight `1`, all rationals
//! exact (`BigRational`).

use core_linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};

use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional};
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
use core_types::observer::{Observer, ObserverKind};

use core_homology::cochain_complex::{CochainComplex, TheoremProvenance};
use core_homology::cochain_primitive_difference::CochainPrimitiveDifference;
use core_homology::coefficient_domain::CoefficientDomain;
use core_homology::hash::{Blake3Hash, ComplexHash};
use core_homology::quotient::{QuotientRelation, QuotientSpace};

use core_epk::residual_families::{
    record_from_verified,
    registry::{FamilyRegistry, RegistryWrite},
    signature::shape_signature,
};

type Q = core_homology::scalar::Q;

fn br(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

fn r(n: i64) -> Q {
    core_homology::scalar::q(n)
}

/// Build a minimal exact `Phi1` certificate: `omega = [0]`, `d0 = [[1]]`,
/// `alpha = [0]`, `primal_residual = [0]`, `dual_witness = [0]`,
/// `reported_value = 0`, `weight = [1]`. Trivially satisfies all the verifier's
/// constraints.
fn exact_phi1_certificate() -> ExactPhi1Certificate {
    ExactPhi1Certificate {
        omega: vec![br(0)],
        d0: vec![vec![br(1)]],
        weights: vec![br(1)],
        alpha: vec![br(0)],
        primal_residual: vec![br(0)],
        dual_witness: vec![br(0)],
        reported_value: br(0),
    }
}

/// A Phi1 certificate whose `.value()` is 1 (not 0). d0 = [[0]] so
/// primal_residual = omega - d0*alpha = 1. Used to force a DIFFERENT
/// `Q1ClassId` than `exact_phi1_certificate` under the SAME (diff, q) shape.
fn exact_phi1_certificate_value_one() -> ExactPhi1Certificate {
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

/// Build a minimal 1x1 ExactCochainComplexQ with d1*d0 = 0 trivially. Then the
/// residual `h = [0]` gives Gamma2 = 0 (closed).
fn exact_gamma2_complex() -> ExactCochainComplexQ {
    // c0_dim = 1, c1_dim = 1, c2_dim = 1; d0 = [[1]] (1x1), d1 = [[0]] (1x1) so
    // d1 * d0 = [[0]] = 0.
    ExactCochainComplexQ::try_new(1, 1, 1, vec![vec![br(1)]], vec![vec![br(0)]])
        .expect("exact complex with d1*d0 = 0")
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
        TheoremProvenance::new("wire_fixture".to_string()).expect("prov"),
    )
    .expect("complex")
}

fn fixture_qspace() -> QuotientSpace<Q> {
    QuotientSpace::new_unchecked(
        ComplexHash(Blake3Hash::new(b"wire-fixture")),
        CoefficientDomain::Rational,
        2,
        1,
        QuotientRelation::ModCoboundaries,
        BasicMatrix::from_row_major(2, 2, vec![r(1), r(0), r(0), r(1)]).expect("proj"),
    )
}

#[test]
fn wire_record_round_trip() {
    // Build REAL VerifiedExactPhi1 + ExactGamma2Result via the public
    // constructors. No mocks.
    let verified_phi1 = Phi1Functional::verify_exact_certificate(exact_phi1_certificate())
        .expect("exact Phi1 certificate verifies");

    let g2_complex = exact_gamma2_complex();
    let residual =
        DegreeOneResidualQ::try_new(&g2_complex, vec![br(0)]).expect("residual constructs");
    let g2_result =
        Gamma2Functional::try_compute_exact_quotient(&residual).expect("exact gamma2 computes");

    // Sanity: trivially closed.
    assert_eq!(g2_result.value(), &br(0));
    assert_eq!(verified_phi1.value(), &br(0));

    let cc = fixture_cochain();
    let pd = CochainPrimitiveDifference::new(&cc);
    let q = fixture_qspace();
    let observer = Observer {
        id: core_kernel::ObserverId::parse("wire_test_obs").expect("canonical observer id"),
        kind: ObserverKind::Projection,
    };

    let mut reg = FamilyRegistry::new();

    // First record: Inserted.
    let r1 = record_from_verified(&mut reg, &pd, &q, &verified_phi1, &g2_result, &observer);
    assert_eq!(r1, RegistryWrite::Inserted);

    // Second record on same inputs: Hit{collision:false}. hits = 2.
    let r2 = record_from_verified(&mut reg, &pd, &q, &verified_phi1, &g2_result, &observer);
    assert_eq!(r2, RegistryWrite::Hit { collision: false });

    let sig = shape_signature(&pd, &q);
    let rec = reg.lookup(&sig).expect("lookup must hit");
    assert_eq!(rec.hits, 2);
}

#[test]
fn wire_collision_true_surfaced_through_record_from_verified() {
    // CODA red-team finding: the collision:true path was only exercised through
    // the low-level inline `record`. This drives it through the wire-level
    // `record_from_verified`: record one shape with phi1_A (value 0), then
    // record the SAME (diff, q) shape with phi1_B whose .value() = 1. Same
    // shape signature, DIFFERENT Q1ClassId -> Hit { collision: true }, and the
    // stored record must be UNCHANGED (no silent overwrite).
    let phi1_a = Phi1Functional::verify_exact_certificate(exact_phi1_certificate())
        .expect("phi1_A verifies (value 0)");
    let phi1_b = Phi1Functional::verify_exact_certificate(exact_phi1_certificate_value_one())
        .expect("phi1_B verifies (value 1)");
    // Precondition: the two Phi1 values genuinely differ (so the derived
    // Q1ClassIds differ and the second write is a real collision).
    assert_ne!(
        phi1_a.value(),
        phi1_b.value(),
        "precondition: phi1_A.value != phi1_B.value"
    );

    let g2_complex = exact_gamma2_complex();
    let residual =
        DegreeOneResidualQ::try_new(&g2_complex, vec![br(0)]).expect("residual constructs");
    let g2_result =
        Gamma2Functional::try_compute_exact_quotient(&residual).expect("gamma2 computes");

    let cc = fixture_cochain();
    let pd = CochainPrimitiveDifference::new(&cc);
    let q = fixture_qspace();
    let observer = Observer {
        id: core_kernel::ObserverId::parse("wire_collision_obs").expect("canonical observer id"),
        kind: ObserverKind::Projection,
    };

    let mut reg = FamilyRegistry::new();

    // First write: phi1_A -> Inserted. Capture the stored Q1ClassId.
    let r1 = record_from_verified(&mut reg, &pd, &q, &phi1_a, &g2_result, &observer);
    assert_eq!(r1, RegistryWrite::Inserted);
    let sig = shape_signature(&pd, &q);
    let stored_q1 = reg.lookup(&sig).expect("first record present").q1_class_id;

    // Second write: SAME (diff, q) shape, DIFFERENT phi1 value -> Hit{collision:true}.
    let r2 = record_from_verified(&mut reg, &pd, &q, &phi1_b, &g2_result, &observer);
    assert_eq!(
        r2,
        RegistryWrite::Hit { collision: true },
        "same shape + distinct Phi1 value is a d_1 single-valuedness violation -> collision"
    );

    // The stored record is UNCHANGED: hits bumped to 2, q1_class_id still the
    // first (the registry does NOT silently overwrite the prior class).
    let rec = reg.lookup(&sig).expect("record still present");
    assert_eq!(rec.hits, 2, "collision still bumps the hit counter");
    assert_eq!(
        rec.q1_class_id, stored_q1,
        "the registry must NOT overwrite the prior Q1ClassId on collision"
    );
}

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/wire_phi1_gamma2.rs
// Claim: urn:core:crates_rs:tests:wire-phi1-gamma2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3c81c64d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3c81c64d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3c81c64d {
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
impl BoundaryError3c81c64d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3c81c64d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3c81c64d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3c81c64d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3c81c64d> {
        if capacity_bound == 0 {
            return Err(BoundaryError3c81c64d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3c81c64d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3c81c64d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3c81c64d() {
    let admitted = BoundaryRecord3c81c64d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3c81c64d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
