//! Exact tests for the foundations movement of the finite quantum mechanics
//! programme: primitive difference, finite cochain packets, and the carriers
//! built on them. One submodule per retired source paper; the paper-to-module
//! map lives in `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

mod descent_census;
mod hilbert_cochain_admission;
mod quantum_carrier_primitive_difference;
mod repair_cofiber_banach_shadow;
mod state_effect_pairing_audit;

#[derive(Clone, Debug, PartialEq, Eq)]
enum DifferenceError {
    Overflow { left: i64, right: i64 },
}

// Origin: engine/crates_rs/tests/core_quantum_physics/foundations/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DifferenceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DifferenceError {}

fn primitive_difference(left: i64, right: i64) -> Result<i64, DifferenceError> {
    right
        .checked_sub(left)
        .ok_or(DifferenceError::Overflow { left, right })
}

#[test]
fn primitive_differences_telescope() {
    let left = primitive_difference(-3, 4);
    let middle = primitive_difference(4, 11);
    let whole = primitive_difference(-3, 11);
    assert!(left.is_ok() && middle.is_ok() && whole.is_ok());
    if let (Ok(left), Ok(middle), Ok(whole)) = (left, middle, whole) {
        assert_eq!(left.checked_add(middle), Some(whole));
    }
}

#[test]
fn primitive_difference_refuses_overflow() {
    assert!(matches!(
        primitive_difference(i64::MIN, 1),
        Err(DifferenceError::Overflow { .. })
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
