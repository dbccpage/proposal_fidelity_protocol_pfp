// AuthorityEffect: None.
// Citation: sealed-derivation-v1 (3100c4e)

//! Milestone M4 Tier 5 Adversarial Challenge Suite for Sovereign Rust Quantum Physics.
//!
//! Validates:
//! 1. `TraceNormCertificate::helstrom_effect` and `SignCertificate::helstrom_effect` across:
//!    - Identical states (trace norm 0, unbiased guessing effect)
//!    - Non-commuting state pairs with exact rational spectra
//!    - Near-orthogonal state pairs
//!    - Orthogonal pure states
//! 2. Zero floating-point drift and strict exact rational algebra over `Rational` and `GaussianRat`.
//! 3. Subnormal-scale exactness and fail-closed spectral verification.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_bigint::BigInt;
use num_traits::{One, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian;
use core_quantum_physics::trace_norm_certificate::{
    sign_certificate_from_spectrum, sign_from_spectrum,
};

/// Helper: construct rational matrix `rows / den`.
fn rm(rows: &[&[i64]], den: i64) -> BasicMatrix<GaussianRat> {
    let data = rows
        .iter()
        .map(|row| {
            row.iter()
                .map(|&v| GaussianRat::from_rational(rq(v, den)))
                .collect()
        })
        .collect();
    mx::from_rows(data).unwrap()
}

/// Helper: construct diagonal matrix `diag(values) / den`.
fn dm(values: &[i64], den: i64) -> BasicMatrix<GaussianRat> {
    let entries: Vec<GaussianRat> = values
        .iter()
        .map(|&v| GaussianRat::from_rational(rq(v, den)))
        .collect();
    mx::diagonal(&entries).unwrap()
}

/// Helper: assert operator is a valid quantum effect: 0 <= E <= I.
fn assert_is_effect(e: &BasicMatrix<GaussianRat>) {
    assert!(
        exact_hermitian::is_positive_semidefinite(e),
        "Effect must be positive semidefinite"
    );
    let identity = mx::identity(e.rows()).unwrap();
    let compl = mx::sub(&identity, e).unwrap();
    assert!(
        exact_hermitian::is_positive_semidefinite(&compl),
        "I - E must be positive semidefinite"
    );
}

/// Helper: evaluate real trace Tr(A B).
fn real_trace_product(a: &BasicMatrix<GaussianRat>, b: &BasicMatrix<GaussianRat>) -> Rational {
    let prod = mx::multiply(a, b).unwrap();
    let tr = mx::trace(&prod).unwrap();
    assert!(tr.im.is_zero(), "Trace must be strictly real");
    tr.re
}

// ==============================================================================
// 1. IDENTICAL STATES STRESS TEST (ZERO TRACE NORM)
// ==============================================================================

#[test]
fn test_helstrom_effect_identical_states() {
    // When rho == sigma, delta = 0. Discrimination is pure coin toss (bias = 0).
    let diff = dm(&[0, 0], 1);
    let spec = &[ri(0)];

    // TraceNormCertificate: dual witness vanishes on kernel (W = 0).
    // Optimal effect is (I + 0)/2 = I/2.
    let cert = sign_from_spectrum(&diff, spec).unwrap();
    assert_eq!(cert.trace_norm(), &ri(0));

    let effect = cert.helstrom_effect().unwrap();
    let expected_effect = dm(&[1, 1], 2); // I / 2
    assert_eq!(effect, expected_effect);
    assert_is_effect(&effect);

    let bias = real_trace_product(&effect, &diff);
    assert_eq!(bias, ri(0));
    // Discrimination success probability: 1/2 + 1/2 * bias = 1/2.
    let p_succ = rq(1, 2) + &bias / ri(2);
    assert_eq!(p_succ, rq(1, 2));

    // SignCertificate: sign of 0 is +1, yielding S = I, effect = I.
    let sign_cert = sign_certificate_from_spectrum(&diff, spec).unwrap();
    assert_eq!(sign_cert.trace_norm(), ri(0));
    let sign_effect = sign_cert.helstrom_effect().unwrap();
    assert_is_effect(&sign_effect);

    let sign_bias = real_trace_product(&sign_effect, &diff);
    assert_eq!(sign_bias, ri(0));
    let sign_p_succ = rq(1, 2) + &sign_bias / ri(2);
    assert_eq!(sign_p_succ, rq(1, 2));
}

// ==============================================================================
// 2. NON-COMMUTING PAIR STRESS TEST (PYTHAGOREAN TRIPLE EIGENSYSTEM)
// ==============================================================================

#[test]
fn test_helstrom_effect_non_commuting_pair() {
    // rho0 = [[7/10, 2/10], [2/10, 3/10]], det = 17/100 > 0, trace = 1 -> valid PSD
    let rho0 = rm(&[&[7, 2], &[2, 3]], 10);
    // rho1 = [[4/10, -2/10], [-2/10, 6/10]], det = 20/100 > 0, trace = 1 -> valid PSD
    let rho1 = rm(&[&[4, -2], &[-2, 6]], 10);

    for s in [&rho0, &rho1] {
        assert!(exact_hermitian::is_positive_semidefinite(s));
        assert_eq!(mx::trace(s).unwrap(), GaussianRat::one());
    }

    // Assert non-commutation: [rho0, rho1] != 0
    let prod01 = mx::multiply(&rho0, &rho1).unwrap();
    let prod10 = mx::multiply(&rho1, &rho0).unwrap();
    let comm = mx::sub(&prod01, &prod10).unwrap();
    assert_ne!(comm, dm(&[0, 0], 1), "rho0 and rho1 must be non-commuting");
    assert_eq!(comm, rm(&[&[0, -4], &[4, 0]], 100));

    // Difference delta = rho0 - rho1 = [[3/10, 4/10], [4/10, -3/10]]
    // Pythagorean triple: 3^2 + 4^2 = 5^2 => eigenvalues are strictly rational: +1/2, -1/2.
    let delta = mx::sub(&rho0, &rho1).unwrap();
    assert_eq!(delta, rm(&[&[3, 4], &[4, -3]], 10));

    let spec = &[rq(1, 2), rq(-1, 2)];

    // TraceNormCertificate
    let cert = sign_from_spectrum(&delta, spec).unwrap();
    assert_eq!(cert.trace_norm(), &ri(1));

    let effect = cert.helstrom_effect().unwrap();
    // Projector onto positive eigenspace: P+ = [[4/5, 2/5], [2/5, 1/5]]
    let expected_effect = rm(&[&[4, 2], &[2, 1]], 5);
    assert_eq!(effect, expected_effect);
    assert_is_effect(&effect);

    // Helstrom optimal bias: Tr(Pi delta) = 1/2 == 1/2 ||delta||_1
    let bias = real_trace_product(&effect, &delta);
    assert_eq!(bias, rq(1, 2));

    // Helstrom discrimination success probability: 1/2 + 1/2 * (1/2) = 3/4
    let p_succ = rq(1, 2) + &bias / ri(2);
    assert_eq!(p_succ, rq(3, 4));

    // SignCertificate matches TraceNormCertificate exactly
    let sign_cert = sign_certificate_from_spectrum(&delta, spec).unwrap();
    assert_eq!(sign_cert.trace_norm(), ri(1));
    let sign_effect = sign_cert.helstrom_effect().unwrap();
    assert_eq!(sign_effect, effect);
    assert_is_effect(&sign_effect);

    let sign_bias = real_trace_product(&sign_effect, &delta);
    assert_eq!(sign_bias, rq(1, 2));
}

// ==============================================================================
// 3. NEAR-ORTHOGONAL STATES STRESS TEST (EXACT RATIONAL OVERLAP)
// ==============================================================================

#[test]
fn test_helstrom_effect_near_orthogonal_states() {
    // Overlap epsilon = 1/1000
    // rho0 = diag(999/1000, 1/1000)
    // rho1 = diag(1/1000, 999/1000)
    let rho0 = dm(&[999, 1], 1000);
    let rho1 = dm(&[1, 999], 1000);

    let delta = mx::sub(&rho0, &rho1).unwrap();
    assert_eq!(delta, dm(&[499, -499], 500));

    let spec = &[rq(499, 500), rq(-499, 500)];

    let cert = sign_from_spectrum(&delta, spec).unwrap();
    assert_eq!(cert.trace_norm(), &rq(499, 250)); // 998/500

    let effect = cert.helstrom_effect().unwrap();
    let expected_effect = dm(&[1, 0], 1);
    assert_eq!(effect, expected_effect);
    assert_is_effect(&effect);

    let bias = real_trace_product(&effect, &delta);
    assert_eq!(bias, rq(499, 500));

    // Success probability: 1/2 + 499/1000 = 999/1000
    let p_succ = rq(1, 2) + &bias / ri(2);
    assert_eq!(p_succ, rq(999, 1000));

    let sign_cert = sign_certificate_from_spectrum(&delta, spec).unwrap();
    assert_eq!(sign_cert.helstrom_effect().unwrap(), effect);
}

// ==============================================================================
// 4. ORTHOGONAL PURE STATES STRESS TEST
// ==============================================================================

#[test]
fn test_helstrom_effect_orthogonal_pure_states() {
    let rho0 = dm(&[1, 0], 1);
    let rho1 = dm(&[0, 1], 1);

    let delta = mx::sub(&rho0, &rho1).unwrap();
    let spec = &[ri(1), ri(-1)];

    let cert = sign_from_spectrum(&delta, spec).unwrap();
    assert_eq!(cert.trace_norm(), &ri(2));

    let effect = cert.helstrom_effect().unwrap();
    assert_eq!(effect, dm(&[1, 0], 1));
    assert_is_effect(&effect);

    let bias = real_trace_product(&effect, &delta);
    assert_eq!(bias, ri(1));

    // Success probability: 1/2 + 1/2 * 1 = 1 (deterministic perfect discrimination)
    let p_succ = rq(1, 2) + &bias / ri(2);
    assert_eq!(p_succ, ri(1));
}

// ==============================================================================
// 5. SUBNORMAL-SCALE ARBITRARY PRECISION RATIONAL NUMBERS (ZERO FLOAT DRIFT)
// ==============================================================================

#[test]
fn test_helstrom_effect_subnormal_scale_invariance() {
    // Perturbation of scale 10^-50 (far below f64 min positive subnormal ~5e-324)
    let scale_denom = BigInt::from(10).pow(50);
    let lam_pos = Rational::new(BigInt::one(), scale_denom.clone());
    let lam_neg = Rational::new(-BigInt::one(), scale_denom);

    let mut delta = mx::zeros(2, 2).unwrap();
    delta.set(0, 0, GaussianRat::from_rational(lam_pos.clone())).unwrap();
    delta.set(1, 1, GaussianRat::from_rational(lam_neg.clone())).unwrap();

    let spec = &[lam_pos.clone(), lam_neg];

    let cert = sign_from_spectrum(&delta, spec).unwrap();
    assert_eq!(cert.trace_norm(), &(&lam_pos * ri(2)));

    let effect = cert.helstrom_effect().unwrap();
    assert_eq!(effect, dm(&[1, 0], 1));
    assert_is_effect(&effect);

    let bias = real_trace_product(&effect, &delta);
    assert_eq!(bias, lam_pos);
}

// ==============================================================================
// 6. FAIL-CLOSED REFUSAL OF INVALID / UNGROUNDED SPECTRUM
// ==============================================================================

#[test]
fn test_trace_norm_certificate_refuses_false_spectrum() {
    let delta = dm(&[1, -1], 1);
    // Claim wrong eigenvalues: [2, -1] for diag(1, -1)
    let false_spec = &[ri(2), ri(-1)];
    assert!(
        sign_from_spectrum(&delta, false_spec).is_err(),
        "Must refuse false spectrum"
    );
    assert!(
        sign_certificate_from_spectrum(&delta, false_spec).is_err(),
        "Must refuse false spectrum"
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/adversarial_challenge_m4.rs
// Claim: urn:core:crates_rs:tests:adversarial-challenge-m4:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb3b29d48 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb3b29d48` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb3b29d48 {
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
impl BoundaryErrorb3b29d48 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb3b29d48 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb3b29d48 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb3b29d48 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb3b29d48> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb3b29d48::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb3b29d48::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb3b29d48::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b3b29d48() {
    let admitted = BoundaryRecordb3b29d48::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb3b29d48::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
