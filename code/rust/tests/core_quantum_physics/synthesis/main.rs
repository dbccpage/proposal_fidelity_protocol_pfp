//! Exact tests for the synthesis papers of the finite quantum mechanics
//! programme: the universal-boundary synthesis, the five-import series (phase
//! fiber, quadratic readout, non-commutative readouts, the Born power rule,
//! unitary dynamics). The Majorana parity algebra is owned and tested by the
//! `core_majorana` crate. One submodule per retired
//! source paper; the paper-to-module map lives in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

mod universal_boundary_synthesis;
mod quadratic_readout_interference;
mod noncommutative_readout_algebra;
mod born_power_rule_pairing;
mod unitary_dynamics_import_boundary;

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_quantum_physics/synthesis/main.rs
// Claim: urn:core:quantum:synthesis:triangle-euler:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
enum SynthesisEulerError {
    Range,
    Overflow,
    Face { empty: i64, filled: i64 },
}

// Origin: engine/crates_rs/tests/core_quantum_physics/synthesis/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SynthesisEulerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SynthesisEulerError {}

fn synthesis_euler(filled: bool) -> Result<i64, SynthesisEulerError> {
    let packet = universal_boundary_synthesis::triangle(filled);
    let vertices = i64::try_from(packet.vertex_count()).map_err(|_| SynthesisEulerError::Range)?;
    let edges = i64::try_from(packet.edge_count()).map_err(|_| SynthesisEulerError::Range)?;
    let faces = i64::try_from(packet.face_count()).map_err(|_| SynthesisEulerError::Range)?;
    vertices.checked_sub(edges).and_then(|value| value.checked_add(faces)).ok_or(SynthesisEulerError::Overflow)
}

fn require_face_gap(empty: i64, filled: i64) -> Result<i64, SynthesisEulerError> {
    let gap = filled.checked_sub(empty).ok_or(SynthesisEulerError::Overflow)?;
    if empty != 0 || gap != 1 {
        return Err(SynthesisEulerError::Face { empty, filled });
    }
    Ok(filled)
}

fn try_synthesis_face() -> Result<i64, SynthesisEulerError> {
    let empty = synthesis_euler(false)?;
    let filled = synthesis_euler(true)?;
    require_face_gap(empty, filled)
}

#[test]
fn filling_the_synthesis_triangle_raises_euler_characteristic_by_one() {
    let filled = try_synthesis_face();
    assert!(matches!(filled, Ok(1)));
}

#[test]
fn a_two_face_gap_is_refused() {
    assert!(matches!(
        require_face_gap(0, 2),
        Err(SynthesisEulerError::Face { empty: 0, filled: 2 })
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
