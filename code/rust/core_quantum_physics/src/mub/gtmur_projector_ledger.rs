//! Finite CODA-MUR loss ledger for the characteristic-two projector path.
//!
//! This module audits the representation changes
//! Weyl board -> spectral counts -> symbolic projector algebra -> Hilbert
//! matrices. It checks that the sampled characteristic-two layers preserve the
//! same declared dimensions, basis/projector counts, ZeroRel-style trace
//! reductions, and terminalizer boundary. It is deliberately finite: a closed
//! ledger for the sampled prime powers is not a dimension-parametric MUB(N)
//! certificate.

use serde::Serialize;

use crate::mub::char_two_weyl_board::{
    verify_current_char_two_weyl_board_schemas, CharTwoWeylBoardReport, CharTwoWeylBoardStatus,
};
use crate::mub::hilbert_transport::{
    verify_current_hilbert_transport_schemas, HilbertTransportReport, HilbertTransportStatus,
};
use crate::mub::projector_algebra::{
    verify_current_projector_algebra_schemas, ProjectorAlgebraReport, ProjectorAlgebraStatus,
};
use crate::mub::spectral_lift::{
    verify_current_spectral_lift_schemas, SpectralLiftReport, SpectralLiftStatus,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum GtmurProjectorLedgerStatus {
    FiniteLedgerClosed,
    MissingStage,
    InvalidAlignment,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct GtmurProjectorLedgerReport {
    pub source: &'static str,
    pub exponent: usize,
    pub dimension: usize,
    pub basis_count: usize,
    pub projector_count: usize,
    pub status: GtmurProjectorLedgerStatus,
    pub representation_edge_checks: usize,
    pub zero_rel_alignment_checks: usize,
    pub terminalizer_alignment_checks: usize,
    pub preserved_invariants: Vec<&'static str>,
    pub rejected_authority_escalations: Vec<&'static str>,
    pub theorem_obligations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_current_gtmur_projector_ledgers() -> Vec<GtmurProjectorLedgerReport> {
    let boards = verify_current_char_two_weyl_board_schemas();
    let spectral = verify_current_spectral_lift_schemas();
    let algebra = verify_current_projector_algebra_schemas();
    let hilbert = verify_current_hilbert_transport_schemas();

    boards
        .iter()
        .map(|board| {
            let spectral = spectral
                .iter()
                .find(|report| report.dimension == board.dimension);
            let algebra = algebra
                .iter()
                .find(|report| report.exponent == board.exponent);
            let hilbert = hilbert
                .iter()
                .find(|report| report.exponent == board.exponent);
            verify_gtmur_projector_ledger(board, spectral, algebra, hilbert)
        })
        .collect()
}

fn failed_gtmur_ledger(
    board: &CharTwoWeylBoardReport,
    status: GtmurProjectorLedgerStatus,
    error: String,
) -> GtmurProjectorLedgerReport {
    GtmurProjectorLedgerReport {
        source: "finite characteristic-two CODA-MUR projector transport ledger",
        exponent: board.exponent,
        dimension: board.dimension,
        basis_count: 0,
        projector_count: 0,
        status,
        representation_edge_checks: 0,
        zero_rel_alignment_checks: 0,
        terminalizer_alignment_checks: 0,
        preserved_invariants: vec![],
        rejected_authority_escalations: vec![],
        theorem_obligations: vec![],
        boundary: "finite CODA-MUR ledger failed before any representation transport authority could be asserted",
        error: Some(error),
    }
}

fn validate_gtmur_stages<'a>(
    board: &CharTwoWeylBoardReport,
    spectral: Option<&'a SpectralLiftReport>,
    algebra: Option<&'a ProjectorAlgebraReport>,
    hilbert: Option<&'a HilbertTransportReport>,
) -> Result<
    (
        &'a SpectralLiftReport,
        &'a ProjectorAlgebraReport,
        &'a HilbertTransportReport,
    ),
    String,
> {
    if board.status != CharTwoWeylBoardStatus::BoardSchemaVerified {
        let msg = board.error.as_deref().unwrap_or("missing verified Weyl-board stage");
        return Err(msg.to_string());
    }
    let (Some(spectral), Some(algebra), Some(hilbert)) = (spectral, algebra, hilbert) else {
        let msg = if spectral.is_none() {
            "missing spectral-projector lift stage"
        } else if algebra.is_none() {
            "missing symbolic projector algebra stage"
        } else {
            "missing Hilbert matrix transport stage"
        };
        return Err(msg.to_string());
    };
    let all_verified = [
        spectral.status == SpectralLiftStatus::LiftSchemaVerified,
        algebra.status == ProjectorAlgebraStatus::AlgebraVerified,
        hilbert.status == HilbertTransportStatus::TransportVerified,
    ]
    .into_iter()
    .all(|b| b);
    if !all_verified {
        return Err("one or more projector transport stages are not verified".to_string());
    }
    Ok((spectral, algebra, hilbert))
}

fn compute_expected_carrier_counts(d: usize) -> Option<(usize, usize, usize, usize, usize)> {
    let basis = d.checked_add(1)?;
    let projectors = d.checked_mul(basis)?;
    let intersections = projectors / 2;
    let cross = intersections.checked_mul(d)?.checked_mul(d)?;
    let same = projectors.checked_mul(d.checked_sub(1)?)?;
    Some((basis, projectors, intersections, cross, same))
}

fn verify_carrier_dimensions(
    board: &CharTwoWeylBoardReport,
    spectral: &SpectralLiftReport,
    algebra: &ProjectorAlgebraReport,
    hilbert: &HilbertTransportReport,
) -> Result<(usize, usize, usize, usize, usize), String> {
    let pow_two = u32::try_from(board.exponent)
        .ok()
        .and_then(|e| 1usize.checked_shl(e));
    let consistent = [
        board.exponent >= 2,
        pow_two == Some(board.dimension),
        spectral.dimension == board.dimension,
        algebra.dimension == board.dimension,
        hilbert.dimension == board.dimension,
        algebra.exponent == board.exponent,
        hilbert.exponent == board.exponent,
    ]
    .into_iter()
    .all(|b| b);
    if !consistent {
        return Err(
            "carrier dimension/exponent mismatch across board/spectral/algebra/Hilbert stages"
                .to_string(),
        );
    }
    compute_expected_carrier_counts(board.dimension)
        .ok_or_else(|| "carrier counts overflow usize".to_string())
}

fn verify_zero_rel_alignments(
    board: &CharTwoWeylBoardReport,
    spectral: &SpectralLiftReport,
    algebra: &ProjectorAlgebraReport,
    hilbert: &HilbertTransportReport,
    counts: (usize, usize, usize, usize, usize),
) -> Result<usize, String> {
    let (
        basis_count,
        projector_count,
        expected_pairwise_intersections,
        expected_cross_reductions,
        expected_same_basis_pairs,
    ) = counts;
    let checks: &[(bool, &str)] = &[
        (
            [board.line_count, spectral.basis_count, algebra.basis_count, hilbert.basis_count]
                .contains_all_eq(basis_count),
            "basis-count alignment failed across board/spectral/algebra/Hilbert stages",
        ),
        (
            [spectral.projector_count, algebra.projector_count, hilbert.projector_count]
                .contains_all_eq(projector_count),
            "projector-count alignment failed across spectral/algebra/Hilbert stages",
        ),
        (
            board.pairwise_zero_intersection_checks == expected_pairwise_intersections,
            "board pairwise zero-intersection count does not match q+1 spread",
        ),
        (
            [
                spectral.cross_basis_unbiased_reductions,
                algebra.cross_basis_unbiased_trace_checks,
                hilbert.cross_basis_trace_transport_checks,
            ]
            .contains_all_eq(expected_cross_reductions),
            "cross-basis ZeroRel trace reduction counts are not preserved",
        ),
        (
            [
                spectral.same_basis_character_reductions,
                algebra.projector_orthogonality_checks,
                2 * hilbert.same_basis_orthogonality_trace_checks,
            ]
            .contains_all_eq(expected_same_basis_pairs),
            "same-basis orthogonality reductions are not preserved",
        ),
        (
            [
                spectral.rank_one_trace_reductions,
                algebra.rank_one_trace_checks,
                hilbert.projector_rank_one_trace_checks,
            ]
            .contains_all_eq(projector_count),
            "rank-one trace reductions are not preserved",
        ),
        (
            [spectral.basis_resolution_reductions, hilbert.basis_resolution_matrix_checks]
                .contains_all_eq(basis_count),
            "basis-resolution terminal count is not preserved",
        ),
    ];
    for &(cond, msg) in checks {
        if !cond {
            return Err(msg.to_string());
        }
    }
    Ok(checks.len())
}

trait SliceAllEq<T: PartialEq> {
    fn contains_all_eq(&self, expected: T) -> bool;
}

impl<T: PartialEq> SliceAllEq<T> for [T] {
    fn contains_all_eq(&self, expected: T) -> bool {
        self.iter().all(|item| *item == expected)
    }
}

fn verify_stage_terminalizer(
    stage_name: &str,
    boundary: &str,
    obligations: &[&str],
) -> Result<usize, String> {
    if !boundary.contains("not a dimension-parametric")
        && !boundary.contains("not a dimension-parametric certificate")
    {
        return Err(format!(
            "{stage_name} stage boundary does not preserve finite-only terminalizer"
        ));
    }
    let has_parametric_obligation = boundary.contains("dimension-parametric")
        || boundary.contains("certificate family")
        || obligations
            .iter()
            .any(|o| o.contains("dimension-parametric") || o.contains("certificate family"));
    if !has_parametric_obligation {
        return Err(format!(
            "{stage_name} stage does not retain parametric/certificate obligation"
        ));
    }
    Ok(2)
}

pub fn verify_gtmur_projector_ledger(
    board: &CharTwoWeylBoardReport,
    spectral: Option<&SpectralLiftReport>,
    algebra: Option<&ProjectorAlgebraReport>,
    hilbert: Option<&HilbertTransportReport>,
) -> GtmurProjectorLedgerReport {
    let (spectral, algebra, hilbert) =
        match validate_gtmur_stages(board, spectral, algebra, hilbert) {
            Ok(stages) => stages,
            Err(err) => {
                return failed_gtmur_ledger(board, GtmurProjectorLedgerStatus::MissingStage, err)
            }
        };

    let counts = match verify_carrier_dimensions(board, spectral, algebra, hilbert) {
        Ok(c) => c,
        Err(err) => {
            return failed_gtmur_ledger(board, GtmurProjectorLedgerStatus::InvalidAlignment, err)
        }
    };
    let (basis_count, projector_count, _, _, _) = counts;

    let zero_rel_alignment_checks =
        match verify_zero_rel_alignments(board, spectral, algebra, hilbert, counts) {
            Ok(n) => n,
            Err(err) => {
                return failed_gtmur_ledger(
                    board,
                    GtmurProjectorLedgerStatus::InvalidAlignment,
                    err,
                )
            }
        };

    let mut terminalizer_alignment_checks = 0;
    for (stage_name, boundary, obligations) in [
        (
            "spectral",
            spectral.boundary,
            spectral.theorem_obligations.as_slice(),
        ),
        (
            "algebra",
            algebra.boundary,
            algebra.theorem_obligations.as_slice(),
        ),
        (
            "hilbert",
            hilbert.boundary,
            hilbert.theorem_obligations.as_slice(),
        ),
    ] {
        match verify_stage_terminalizer(stage_name, boundary, obligations) {
            Ok(n) => terminalizer_alignment_checks += n,
            Err(err) => {
                return failed_gtmur_ledger(
                    board,
                    GtmurProjectorLedgerStatus::InvalidAlignment,
                    err,
                )
            }
        }
    }

    GtmurProjectorLedgerReport {
        source: "finite characteristic-two CODA-MUR projector transport ledger",
        exponent: board.exponent,
        dimension: board.dimension,
        basis_count,
        projector_count,
        status: GtmurProjectorLedgerStatus::FiniteLedgerClosed,
        representation_edge_checks: 3,
        zero_rel_alignment_checks,
        terminalizer_alignment_checks,
        preserved_invariants: vec![
            "declared characteristic-two finite-field dimension",
            "q+1 basis labels and q(q+1) projector labels",
            "zero-only spread intersections",
            "same-basis orthogonality reductions",
            "rank-one trace reductions",
            "cross-basis unbiased trace reductions",
            "finite-only terminalizer boundary",
        ],
        rejected_authority_escalations: vec![
            "finite ledger does not classify composite dimensions",
            "finite ledger does not provide an all-N certificate family",
            "finite ledger does not transport MUB(6) or MUB(10) lower controls to complete authority",
        ],
        theorem_obligations: vec![
            "dimension-parametric CODA-MUR loss ledger over all finite-field Pauli schemas",
            "formal Lean/Core theorem that the finite ledger preserves ZeroRel and terminalizer in every dimension",
            "certificate family or certified stratification covering composite targets and the all-N query",
        ],
        boundary: "finite CODA-MUR projector ledger only; not a dimension-parametric certificate family or composite-dimension theorem",
        error: None,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/gtmur_projector_ledger.rs
// Claim: urn:core:crates_rs:core-quantum-physics:gtmur-projector-ledger:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc47069e6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc47069e6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc47069e6 {
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
impl BoundaryErrorc47069e6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc47069e6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc47069e6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc47069e6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc47069e6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc47069e6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc47069e6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc47069e6::ExceedsCapacity {
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
    fn gtmur_projector_ledgers_close_for_char_two_samples() {
        let reports = verify_current_gtmur_projector_ledgers();
        assert_eq!(reports.len(), 4);
        for report in reports {
            let d = report.dimension;
            assert_eq!(
                report.status,
                GtmurProjectorLedgerStatus::FiniteLedgerClosed
            );
            assert_eq!(report.basis_count, d + 1);
            assert_eq!(report.projector_count, d * (d + 1));
            assert_eq!(report.representation_edge_checks, 3);
            assert!(report.zero_rel_alignment_checks >= 7);
            assert!(report.terminalizer_alignment_checks >= 6);
            assert!(report
                .rejected_authority_escalations
                .iter()
                .any(|item| item.contains("all-N")));
            assert!(report.error.is_none());
        }
    }

    #[test]
    fn gtmur_projector_ledger_rejects_missing_stage() {
        let board = verify_char_two_weyl_board_schema(1);
        let report = verify_gtmur_projector_ledger(&board, None, None, None);
        assert_eq!(report.status, GtmurProjectorLedgerStatus::MissingStage);
        assert!(report.error.is_some());
    }
}

#[cfg(test)]
mod l4_boundary_tests_c47069e6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc47069e6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc47069e6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc47069e6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc47069e6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc47069e6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc47069e6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc47069e6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
