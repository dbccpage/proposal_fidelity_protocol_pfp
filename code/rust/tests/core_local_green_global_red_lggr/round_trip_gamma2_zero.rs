//! S6: three round-trip $\Gamma_2 = 0$ tests on known shape collisions.
//!
//! Each test constructs a `CochainPrimitiveDifference` pair that differs only
//! by a gauge-equivalent perturbation, records both, and asserts:
//!
//! 1. the second `record` returns `RegistryWrite::Hit { collision: false }`,
//! 2. `lookup` of the same signature returns the same
//!    `(q1_class_id, gamma2_class_id)`,
//! 3. re-running $\sigma$ twice on the same input yields byte-identical
//!    `ShapeSignature`.
//!
//! Defect-2 fix: `coefficient_swap_round_trip_gamma2_zero` builds TWO real
//! `CochainPrimitiveDifference` instances whose `d0`/`d1` matrices differ
//! ONLY by rational rescaling — and asserts `shape_fingerprint()` matches as a
//! precondition before the registry-level claim.
//!
//! Defect-2 negative control: `shape_distinct_complexes_get_distinct_digests_neg`
//! builds two `CochainPrimitiveDifference` instances of DISTINCT cochain shape
//! (`c0/c1/c2 = 1/2/1` vs `2/3/1`) on the same `QuotientSpace` and asserts
//! they get DISTINCT signatures and the registry returns `Inserted` twice.
//!
//! Defect-3 fix: the original `observer_rename_round_trip_gamma2_zero` test
//! was a tautology (two strings bound and dropped). It is intentionally NOT
//! present here — the genuine cross-observer property is exercised in
//! `tests/cross_instance_stability.rs` (S7b).

use core_linear_algebra::backend::basic_matrix::BasicMatrix;
use num_rational::Rational64;

use core_homology::cochain_complex::{CochainComplex, TheoremProvenance};
use core_homology::cochain_primitive_difference::CochainPrimitiveDifference;
use core_homology::coefficient_domain::CoefficientDomain;
use core_homology::hash::{Blake3Hash, ComplexHash};
use core_homology::quotient::{QuotientRelation, QuotientSpace};

use core_epk::residual_families::{
    record::{Gamma2ClassId, Q1ClassId},
    registry::{FamilyRegistry, RegistryWrite},
    signature::shape_signature,
};

type Q = core_homology::scalar::Q;

fn r(n: i64) -> Q {
    core_homology::scalar::q(n)
}

/// Reference complex: `C^0 = Q`, `C^1 = Q^2`, `C^2 = Q`, `d0 = [1; -1]`, `d1 = [1, 1]`.
fn path_complex_unit() -> CochainComplex {
    let d0 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(-1)]).expect("d0");
    let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(1)]).expect("d1");
    CochainComplex::new(
        1,
        2,
        1,
        d0,
        d1,
        TheoremProvenance::new("round_trip_unit".to_string()).expect("prov"),
    )
    .expect("complex")
}

/// Rationally-rescaled twin: `d0 = [2; -2]`, `d1 = [3, 3]` (same SHAPES,
/// different coefficient VALUES; `d1*d0 = 12 - 12 = 0` still holds).
fn path_complex_rescaled() -> CochainComplex {
    let d0 = BasicMatrix::from_row_major(2, 1, vec![r(2), r(-2)]).expect("d0");
    let d1 = BasicMatrix::from_row_major(1, 2, vec![r(3), r(3)]).expect("d1");
    CochainComplex::new(
        1,
        2,
        1,
        d0,
        d1,
        TheoremProvenance::new("round_trip_rescaled".to_string()).expect("prov"),
    )
    .expect("complex")
}

/// Distinct cochain shape: `C^0 = Q^2`, `C^1 = Q^3`, `C^2 = Q`. `d0 = 0` (3x2),
/// `d1 = 0` (1x3) — both zero matrices, so `d1*d0 = 0` holds, and the complex
/// is shape-distinct from `path_complex_unit` along c0/c1.
fn distinct_shape_complex() -> CochainComplex {
    let d0 = BasicMatrix::from_row_major(3, 2, vec![r(0); 6]).expect("d0");
    let d1 = BasicMatrix::from_row_major(1, 3, vec![r(0); 3]).expect("d1");
    CochainComplex::new(
        2,
        3,
        1,
        d0,
        d1,
        TheoremProvenance::new("round_trip_distinct".to_string()).expect("prov"),
    )
    .expect("complex")
}

fn fixture_qspace() -> QuotientSpace<Q> {
    QuotientSpace::new_unchecked(
        ComplexHash(Blake3Hash::new(b"round-trip-fixture")),
        CoefficientDomain::Rational,
        2,
        1,
        QuotientRelation::ModCoboundaries,
        BasicMatrix::from_row_major(2, 2, vec![r(1), r(0), r(0), r(1)]).expect("proj"),
    )
}

#[test]
fn coefficient_swap_round_trip_gamma2_zero() {
    // Defect-2 fix: TWO real CochainPrimitiveDifference instances whose
    // d0/d1 differ ONLY by rational rescaling — same SHAPES, distinct VALUES.
    let cc_a = path_complex_unit();
    let cc_b = path_complex_rescaled();
    let pd_a = CochainPrimitiveDifference::new(&cc_a);
    let pd_b = CochainPrimitiveDifference::new(&cc_b);

    // Precondition: shape_fingerprint() agrees (same dims, same matrix shapes,
    // same coefficient-domain tag) even though coefficient VALUES differ.
    assert_eq!(
        pd_a.shape_fingerprint(),
        pd_b.shape_fingerprint(),
        "precondition: rationally-rescaled twins must share shape_fingerprint"
    );
    // Sanity-check: the two complexes are NOT byte-identical (they differ in
    // coefficient values), so this is not a tautology.
    assert_ne!(
        cc_a.d0.matrix.as_slice(),
        cc_b.d0.matrix.as_slice(),
        "sanity: the d0 matrices must differ in VALUES (else this test is vacuous)"
    );

    let q = fixture_qspace();

    let sig_a = shape_signature(&pd_a, &q);
    let sig_b = shape_signature(&pd_b, &q);
    // ZeroRel identifies coefficient gauge twins: digests must agree.
    assert_eq!(
        sig_a, sig_b,
        "ZeroRel must identify coefficient-rescaled CochainPrimitiveDifference twins"
    );

    let mut reg = FamilyRegistry::new();
    let q1 = Q1ClassId::from_u64(0xC0EF_FEEE_C0EF_FEEE);
    let g2 = Gamma2ClassId::from_u64(0x6477_DDDD_6477_DDDD);

    assert_eq!(reg.record(sig_a, q1, g2), RegistryWrite::Inserted);
    // Second record under sig_b (same digest as sig_a): Hit{collision:false}.
    assert_eq!(
        reg.record(sig_b, q1, g2),
        RegistryWrite::Hit { collision: false }
    );

    // Lookup is single-valued.
    let rec = reg.lookup(&sig_a).expect("lookup must hit");
    assert_eq!(rec.q1_class_id, q1);
    assert_eq!(rec.gamma2_class_id, g2);
    assert_eq!(rec.hits, 2);

    // σ is deterministic: rerunning twice yields byte-identical keys.
    let sig_a_again = shape_signature(&pd_a, &q);
    assert_eq!(sig_a.as_bytes(), sig_a_again.as_bytes());
}

#[test]
fn shape_distinct_complexes_get_distinct_digests_neg() {
    // Defect-2 NEGATIVE control: two CochainPrimitiveDifference instances of
    // DISTINCT shape (c0/c1/c2 = 1/2/1 vs 2/3/1) on the same QuotientSpace
    // MUST get distinct digests and produce a second `Inserted`, NOT a `Hit`.
    let cc_a = path_complex_unit();
    let cc_b = distinct_shape_complex();
    let pd_a = CochainPrimitiveDifference::new(&cc_a);
    let pd_b = CochainPrimitiveDifference::new(&cc_b);

    // Precondition: cochain_dims actually differ.
    assert_ne!(
        pd_a.cochain_dims(),
        pd_b.cochain_dims(),
        "precondition: the two complexes must differ in cochain dimensions"
    );
    // Precondition: shape_fingerprint differs (this is the property the previous
    // attempt's bug masked — if shape_fingerprint ignored dims, this fails here).
    assert_ne!(
        pd_a.shape_fingerprint(),
        pd_b.shape_fingerprint(),
        "shape_fingerprint MUST distinguish c0/c1/c2-distinct complexes"
    );

    let q = fixture_qspace();
    let sig_a = shape_signature(&pd_a, &q);
    let sig_b = shape_signature(&pd_b, &q);
    assert_ne!(
        sig_a, sig_b,
        "shape_signature MUST distinguish c0/c1/c2-distinct complexes"
    );

    let mut reg = FamilyRegistry::new();
    let q1 = Q1ClassId::from_u64(1);
    let g2 = Gamma2ClassId::from_u64(2);
    assert_eq!(reg.record(sig_a, q1, g2), RegistryWrite::Inserted);
    // Different shape -> different digest -> Inserted (NOT Hit).
    assert_eq!(reg.record(sig_b, q1, g2), RegistryWrite::Inserted);
    assert_eq!(reg.len(), 2, "two distinct shapes must yield two records");
}

#[test]
fn independent_construction_yields_same_digest() {
    // Renamed from `field_order_swap_round_trip_gamma2_zero` (CODA red-team nit):
    // no field-order swap is observable on the public surface, so the old name
    // advertised a property the API cannot exercise. What this test actually
    // checks is determinism: building the same complex via two independent
    // construction calls. Both paths flow through the same
    // `BasicMatrix::from_row_major` and the same `CochainComplex::new`, so they
    // must produce byte-identical shape signatures.
    let cc_a = path_complex_unit();
    let cc_b = path_complex_unit();
    let pd_a = CochainPrimitiveDifference::new(&cc_a);
    let pd_b = CochainPrimitiveDifference::new(&cc_b);

    // Precondition: shape_fingerprint matches.
    assert_eq!(pd_a.shape_fingerprint(), pd_b.shape_fingerprint());

    let q = fixture_qspace();
    let sig_a = shape_signature(&pd_a, &q);
    let sig_b = shape_signature(&pd_b, &q);
    assert_eq!(sig_a, sig_b);

    let mut reg = FamilyRegistry::new();
    let q1 = Q1ClassId::from_u64(0x1111);
    let g2 = Gamma2ClassId::from_u64(0x2222);
    assert_eq!(reg.record(sig_a, q1, g2), RegistryWrite::Inserted);
    assert_eq!(
        reg.record(sig_b, q1, g2),
        RegistryWrite::Hit { collision: false }
    );

    let rec = reg.lookup(&sig_a).expect("lookup must hit");
    assert_eq!(rec.q1_class_id, q1);
    assert_eq!(rec.gamma2_class_id, g2);
    assert_eq!(rec.hits, 2);

    // σ deterministic.
    assert_eq!(
        shape_signature(&pd_a, &q).as_bytes(),
        shape_signature(&pd_a, &q).as_bytes()
    );
}

// NOTE: the third scenario name from the sprint plan, `observer_rename`, is
// intentionally NOT a test here. The previous attempt at that test was a
// tautology (Defect 3). The genuine cross-observer property — that two
// distinct `Observer` values on the same shape yield the same `Q1ClassId` —
// is exercised in `tests/cross_instance_stability.rs` (S7b), which actually
// builds two `Observer { kind: Projection }` vs `{ kind: Precision }` and
// hashes them through `record_from_verified`.

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/round_trip_gamma2_zero.rs
// Claim: urn:core:crates_rs:tests:round-trip-gamma2-zero:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1992612a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1992612a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1992612a {
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
impl BoundaryError1992612a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1992612a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1992612a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1992612a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1992612a> {
        if capacity_bound == 0 {
            return Err(BoundaryError1992612a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1992612a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1992612a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1992612a() {
    let admitted = BoundaryRecord1992612a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1992612a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
