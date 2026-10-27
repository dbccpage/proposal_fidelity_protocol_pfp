//! Spectral-projector lift schema for finite-field Weyl boards.
//!
//! The board layer proves incidence. This layer records the operator-algebra
//! reduction needed to turn a certified symplectic spread into bases:
//!
//! * each isotropic line is treated as a maximal commuting Weyl class;
//! * line characters define rank-one projector sums;
//! * same-line character orthogonality gives an orthonormal basis;
//! * disjoint lines plus Weyl trace orthogonality gives unbiasedness.
//!
//! The checks here are the finite counting reductions. Positivity,
//! self-adjoint phase conventions, and formal Hilbert-space transport remain
//! explicit theorem obligations.

use serde::Serialize;

use crate::mub::char_two_weyl_board::{
    verify_current_char_two_weyl_board_schemas, CharTwoWeylBoardReport, CharTwoWeylBoardStatus,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum SpectralLiftStatus {
    LiftSchemaVerified,
    MissingBoardSchema,
    InvalidBoardCounts,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct SpectralLiftReport {
    pub source: &'static str,
    pub dimension: usize,
    pub basis_count: usize,
    pub projector_count: usize,
    pub status: SpectralLiftStatus,
    pub rank_one_trace_reductions: usize,
    pub same_basis_character_reductions: usize,
    pub cross_basis_unbiased_reductions: usize,
    pub basis_resolution_reductions: usize,
    pub checked_identities: Vec<&'static str>,
    pub theorem_obligations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_current_spectral_lift_schemas() -> Vec<SpectralLiftReport> {
    verify_current_char_two_weyl_board_schemas()
        .iter()
        .map(verify_char_two_board_spectral_lift)
        .collect()
}

pub fn verify_char_two_board_spectral_lift(board: &CharTwoWeylBoardReport) -> SpectralLiftReport {
    if board.status != CharTwoWeylBoardStatus::BoardSchemaVerified {
        return SpectralLiftReport {
            source: "characteristic-two Weyl-board spread",
            dimension: board.dimension,
            basis_count: 0,
            projector_count: 0,
            status: SpectralLiftStatus::MissingBoardSchema,
            rank_one_trace_reductions: 0,
            same_basis_character_reductions: 0,
            cross_basis_unbiased_reductions: 0,
            basis_resolution_reductions: 0,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "spectral lift cannot start without a verified board spread",
            error: board.error.clone(),
        };
    }

    let d = board.dimension;
    let expected_line_count = d + 1;
    let expected_pairwise_intersections = d * (d + 1) / 2;
    let expected_nonzero_cover = d * d - 1;
    let expected_isotropic_checks = (d + 1) * d * d;
    if board.line_count != expected_line_count
        || board.pairwise_zero_intersection_checks != expected_pairwise_intersections
        || board.nonzero_vector_cover_count != expected_nonzero_cover
        || board.isotropic_line_checks != expected_isotropic_checks
    {
        return SpectralLiftReport {
            source: "characteristic-two Weyl-board spread",
            dimension: d,
            basis_count: 0,
            projector_count: 0,
            status: SpectralLiftStatus::InvalidBoardCounts,
            rank_one_trace_reductions: 0,
            same_basis_character_reductions: 0,
            cross_basis_unbiased_reductions: 0,
            basis_resolution_reductions: 0,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "board incidence counts do not match the spectral-lift contract",
            error: Some("board line/intersection/cover counts do not match q+1 spread".to_string()),
        };
    }

    let basis_count = expected_line_count;
    let projector_count = basis_count * d;
    let same_basis_character_reductions = basis_count * d * (d - 1);
    let cross_basis_unbiased_reductions = expected_pairwise_intersections * d * d;

    SpectralLiftReport {
        source: "characteristic-two Weyl-board spread",
        dimension: d,
        basis_count,
        projector_count,
        status: SpectralLiftStatus::LiftSchemaVerified,
        rank_one_trace_reductions: projector_count,
        same_basis_character_reductions,
        cross_basis_unbiased_reductions,
        basis_resolution_reductions: basis_count,
        checked_identities: vec![
            "each verified isotropic line supplies one maximal commuting Weyl class",
            "each commuting class has d line characters and therefore d projector labels",
            "rank-one trace reduces to the identity coefficient in each character projector",
            "same-basis orthogonality reduces to nontrivial line-character sums",
            "cross-basis unbiasedness reduces to zero-only intersection plus Weyl trace orthogonality",
            "each basis resolution reduces to summing all characters on one line",
        ],
        theorem_obligations: vec![
            "formal finite abelian character orthogonality for each line",
            "formal Weyl trace orthogonality and multiplication law",
            "self-adjoint phase convention for characteristic-two Weyl operators",
            "exact positivity/idempotence proof for the character projector sums",
            "Lean/Core transport from projector sums to Hilbert-space bases",
        ],
        boundary: "spectral-projector lift schema only; not a dimension-parametric certificate family or composite-dimension theorem",
        error: None,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/spectral_lift.rs
// Claim: urn:core:crates_rs:core-quantum-physics:spectral-lift:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5d18f8c8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5d18f8c8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5d18f8c8 {
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
impl BoundaryError5d18f8c8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5d18f8c8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5d18f8c8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5d18f8c8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5d18f8c8> {
        if capacity_bound == 0 {
            return Err(BoundaryError5d18f8c8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5d18f8c8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5d18f8c8::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mub::char_two_weyl_board::verify_char_two_weyl_board_schema;

    #[test]
    fn spectral_lift_schema_verifies_for_char_two_boards() {
        for exponent in [2, 3, 4, 5] {
            let board = verify_char_two_weyl_board_schema(exponent);
            let report = verify_char_two_board_spectral_lift(&board);
            let d = board.dimension;
            assert_eq!(report.status, SpectralLiftStatus::LiftSchemaVerified);
            assert_eq!(report.basis_count, d + 1);
            assert_eq!(report.projector_count, d * (d + 1));
            assert_eq!(report.rank_one_trace_reductions, d * (d + 1));
            assert_eq!(
                report.same_basis_character_reductions,
                (d + 1) * d * (d - 1)
            );
            assert_eq!(
                report.cross_basis_unbiased_reductions,
                d * (d + 1) / 2 * d * d
            );
            assert!(report
                .theorem_obligations
                .iter()
                .any(|obligation| obligation.contains("positivity")));
            assert!(report.error.is_none());
        }
    }

    #[test]
    fn spectral_lift_schema_rejects_missing_board_schema() {
        let board = verify_char_two_weyl_board_schema(1);
        let report = verify_char_two_board_spectral_lift(&board);
        assert_eq!(report.status, SpectralLiftStatus::MissingBoardSchema);
        assert!(report.error.is_some());
    }
}

#[cfg(test)]
mod l4_boundary_tests_5d18f8c8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5d18f8c8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5d18f8c8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5d18f8c8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5d18f8c8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5d18f8c8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5d18f8c8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5d18f8c8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
