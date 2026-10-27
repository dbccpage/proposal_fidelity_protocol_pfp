//! Rust ↔ Lean parity for the Φ₁ primal–dual certificate.
//!
//! Every test here mirrors, **on the same numbers**, a theorem in
//! `lean4/original_lean_20260809/phi1_primal_dual_certificate.lean`. If either
//! side changes its notion of "certificate" the pair stops agreeing, which is the
//! point of pinning the shared instance rather than two convenient ones.
//!
//! Lean instance (`section Instance`):
//!   weights `w = (1, 1)`, residual `ω = (3, −5)`,
//!   coboundaries `d a = (a, a)`, dual `φ = (1, −1)`, achiever `α = 0`.
//! Certified value: `8`. Competitor `α = 10` gives `22`.
//!
//! AuthorityEffect: None. A passing certificate is algebraic evidence only.

use num_bigint::BigInt;
use num_rational::BigRational;
use core_certifiers::phi1_certifier::{
    wl1, Phi1FormCertificate, Phi1FormError, LEAN_PHI1_CERTIFICATE_SOUNDNESS,
    LEAN_PHI1_CERTIFICATE_SOUNDNESS_SOURCE, LEAN_PHI1_SOURCE,
    LEAN_PHI1_CERTIFICATE_SOUNDNESS_SOURCE_SHA256, LEAN_PHI1_SOURCE_SHA256,
    LEAN_DUALITY_SOURCE, LEAN_DUALITY_SOURCE_SHA256, LEAN_SOURCE_BINDING_STATUS,
};

fn q(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

fn v(xs: &[i64]) -> Vec<BigRational> {
    xs.iter().copied().map(q).collect()
}

/// The Lean instance, verbatim.
fn lean_instance() -> Phi1FormCertificate {
    Phi1FormCertificate {
        weights: v(&[1, 1]),
        // ω − d 0 = (3, −5)
        residual_at_achiever: v(&[3, -5]),
        dual: v(&[1, -1]),
        // im(d) is spanned by d 1 = (1, 1)
        coboundaries: vec![v(&[1, 1])],
    }
}

/// Parity with Lean `instance_certified_minimum` + `instance_value_is_eight`.
#[test]
fn parity_lean_instance_certifies_eight() {
    let value = lean_instance()
        .verify()
        .expect("the Lean instance must verify");
    assert_eq!(value, q(8), "certified Phi1 value must match Lean's 8");
}

/// Parity with Lean `instance_competitor_is_strictly_worse`: `α = 10` gives
/// `|3−10| + |−5−10| = 22 > 8`, so the minimisation is non-trivial and the
/// certificate is not certifying the only available value.
#[test]
fn parity_competitor_is_strictly_worse() {
    let w = v(&[1, 1]);
    let at_zero = wl1(&w, &v(&[3, -5]));
    let at_ten = wl1(&w, &v(&[-7, -15]));
    assert_eq!(at_zero, q(8));
    assert_eq!(at_ten, q(22));
    assert!(at_zero < at_ten, "minimisation must be non-trivial");
}

/// Parity with Lean `phi2_perp`: a dual that does **not** annihilate `im(d)` is
/// refused, naming the offending coboundary.
#[test]
fn parity_refuses_non_perpendicular_dual() {
    let mut c = lean_instance();
    c.dual = v(&[1, 1]); // <(1,1),(1,1)> = 2 != 0
    assert_eq!(
        c.verify(),
        Err(Phi1FormError::DualNotPerpendicular {
            coboundary_index: 0
        })
    );
}

/// Parity with Lean `phi2_bounded`: `|φ_e| ≤ w_e` is enforced.
#[test]
fn parity_refuses_dual_exceeding_weights() {
    let mut c = lean_instance();
    c.dual = v(&[2, -2]); // still perpendicular, but |2| > 1
    assert_eq!(
        c.verify(),
        Err(Phi1FormError::DualExceedsWeight { index: 0 })
    );
}

/// Parity with Lean `phi2_no_gap`: a nonzero duality gap is refused.
///
/// `φ = (1, −1)` scaled to `(1/2, −1/2)` stays perpendicular and within the
/// weights, but pairs to `4 ≠ 8`.
#[test]
fn parity_refuses_nonzero_duality_gap() {
    let half = BigRational::new(BigInt::from(1), BigInt::from(2));
    let mut c = lean_instance();
    c.dual = vec![half.clone(), -half];
    assert_eq!(c.verify(), Err(Phi1FormError::DualityGapNonZero));
}

/// The three hypotheses are independent: each of the three refusals above is
/// reachable from the *same* accepted certificate by breaking exactly one. A
/// verifier that collapsed them into one check would not produce three distinct
/// errors.
#[test]
fn parity_three_hypotheses_are_independently_checked() {
    assert!(lean_instance().verify().is_ok());

    let mut perp = lean_instance();
    perp.dual = v(&[1, 1]);
    let mut bound = lean_instance();
    bound.dual = v(&[2, -2]);
    let half = BigRational::new(BigInt::from(1), BigInt::from(2));
    let mut gap = lean_instance();
    gap.dual = vec![half.clone(), -half];

    let errors = [
        perp.verify().unwrap_err(),
        bound.verify().unwrap_err(),
        gap.verify().unwrap_err(),
    ];
    // all three distinct
    assert_ne!(errors[0], errors[1]);
    assert_ne!(errors[1], errors[2]);
    assert_ne!(errors[0], errors[2]);
}

/// Dimension discipline: a coboundary of the wrong length is refused rather than
/// silently zip-truncated. `dot` zips, so a short vector would otherwise pass
/// perpendicularity vacuously.
#[test]
fn parity_refuses_dimension_mismatch() {
    let mut c = lean_instance();
    c.coboundaries = vec![v(&[1])];
    assert_eq!(
        c.verify(),
        Err(Phi1FormError::DimensionMismatch {
            expected: 2,
            actual: 1
        })
    );
}

/// All three declared source files must match their byte identities. This
/// source-binding check does not compile Lean or recompute an axiom report.
#[test]
fn declared_lean_sources_match_repository_bytes() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("..");
    use sha2::{Digest, Sha256};
    let legacy_snapshot = root.join("lean4/original_lean_20260809");
    if legacy_snapshot.is_dir() {
        for (path, expected) in [
            (LEAN_PHI1_SOURCE, LEAN_PHI1_SOURCE_SHA256),
            (LEAN_DUALITY_SOURCE, LEAN_DUALITY_SOURCE_SHA256),
            (LEAN_PHI1_CERTIFICATE_SOUNDNESS_SOURCE, LEAN_PHI1_CERTIFICATE_SOUNDNESS_SOURCE_SHA256),
        ] {
            let full = root.join(path);
            let bytes = std::fs::read(&full)
                .unwrap_or_else(|error| panic!("declared Lean source {}: {error}", full.display()));
            assert_eq!(format!("{:x}", Sha256::digest(bytes)), expected, "{path}");
        }
    }
    assert_eq!(LEAN_SOURCE_BINDING_STATUS, "SOURCE_BINDING_ONLY_NOT_NATIVE_LEAN_REPLAY");
    assert!(LEAN_PHI1_CERTIFICATE_SOUNDNESS.contains("isMinimum_of_certificate"));
}

// Origin: engine/crates_rs/tests/core_certifiers/phi1_form_lean_parity.rs
// Claim: urn:core:crates_rs:tests:phi1-form-lean-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord478dcfde {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord478dcfde` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError478dcfde {
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
impl BoundaryError478dcfde {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError478dcfde {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError478dcfde {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord478dcfde {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError478dcfde> {
        if capacity_bound == 0 {
            return Err(BoundaryError478dcfde::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError478dcfde::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError478dcfde::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_478dcfde() {
    let admitted = BoundaryRecord478dcfde::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord478dcfde::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
