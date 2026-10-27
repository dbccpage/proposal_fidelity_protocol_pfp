//! Exact tests for the superposition, interference and phase movement of the
//! finite quantum mechanics programme: the phase-blind quotient and its fibers,
//! interference against the diagonal layer, the U(1)-selector checks, and
//! holonomy-structured interference. One submodule per retired source paper;
//! the paper-to-module map lives in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

mod support;

mod superposition_as_the_quotient_fiber;
mod interference_as_the_non_l1_resource;
mod the_u1_selector;
mod holonomy_structured_superposition;

#[derive(Clone, Debug, PartialEq, Eq)]
struct GaussianAmplitude {
    re: i64,
    im: i64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
enum AmplitudeError {
    NormOverflow,
}

// Origin: engine/crates_rs/tests/core_quantum_physics/superposition/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for AmplitudeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for AmplitudeError {}

impl GaussianAmplitude {
    fn try_new(re: i64, im: i64) -> Result<Self, AmplitudeError> {
        let amplitude = Self { re, im };
        let _norm = amplitude.norm_sq()?;
        Ok(amplitude)
    }

    fn norm_sq(&self) -> Result<i64, AmplitudeError> {
        let real = self.re.checked_mul(self.re).ok_or(AmplitudeError::NormOverflow)?;
        let imag = self.im.checked_mul(self.im).ok_or(AmplitudeError::NormOverflow)?;
        real.checked_add(imag).ok_or(AmplitudeError::NormOverflow)
    }
}

fn same_phase_blind_fiber(
    left: &GaussianAmplitude,
    right: &GaussianAmplitude,
) -> Result<bool, AmplitudeError> {
    Ok(left.norm_sq()? == right.norm_sq()?)
}

#[test]
fn equal_norms_share_a_phase_blind_fiber() {
    let left = GaussianAmplitude::try_new(3, 4);
    let right = GaussianAmplitude::try_new(-4, 3);
    assert!(left.is_ok() && right.is_ok());
    if let (Ok(left), Ok(right)) = (left, right) {
        assert_eq!(left.norm_sq(), Ok(25));
        assert_eq!(same_phase_blind_fiber(&left, &right), Ok(true));
    }
}

#[test]
fn unequal_norms_are_distinct_fibers() {
    let left = GaussianAmplitude::try_new(1, 0);
    let right = GaussianAmplitude::try_new(1, 1);
    assert!(left.is_ok() && right.is_ok());
    if let (Ok(left), Ok(right)) = (left, right) {
        assert_eq!(same_phase_blind_fiber(&left, &right), Ok(false));
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
