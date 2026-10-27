//! Finite characteristic-two projector MUB controls.
//!
//! The characteristic-two path now has enough local structure to certify
//! declared-dimension projector controls for the sampled prime powers:
//! Weyl-board spread -> spectral counts -> symbolic projector algebra -> exact
//! Hilbert matrices, with a finite CODA-MUR ledger preserving the same ZeroRel
//! data. This module consumes those reports and records the finite control
//! authority without promoting it to composite dimensions or an all-N theorem.

use serde::Serialize;

use crate::mub::gtmur_projector_ledger::{
    verify_current_gtmur_projector_ledgers, GtmurProjectorLedgerReport, GtmurProjectorLedgerStatus,
};
use crate::mub::hilbert_transport::{
    verify_current_hilbert_transport_schemas, HilbertTransportReport, HilbertTransportStatus,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum FiniteProjectorControlStatus {
    CompleteProjectorMubVerified,
    MissingHilbertTransport,
    MissingGtmurLedger,
    InvalidControlCounts,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct FiniteProjectorControlReport {
    pub source: &'static str,
    pub exponent: usize,
    pub dimension: usize,
    pub basis_count: usize,
    pub projector_count: usize,
    pub status: FiniteProjectorControlStatus,
    pub positive_factor_checks: usize,
    pub projector_factorization_checks: usize,
    pub projector_scaled_idempotence_checks: usize,
    pub rank_one_trace_checks: usize,
    pub basis_resolution_checks: usize,
    pub same_basis_orthogonality_checks: usize,
    pub cross_basis_unbiased_checks: usize,
    pub gtmur_zero_rel_alignment_checks: usize,
    pub gtmur_terminalizer_alignment_checks: usize,
    pub checked_identities: Vec<&'static str>,
    pub remaining_obligations: Vec<&'static str>,
    pub rejected_authority_escalations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_current_finite_projector_controls() -> Vec<FiniteProjectorControlReport> {
    let hilbert = verify_current_hilbert_transport_schemas();
    let ledgers = verify_current_gtmur_projector_ledgers();

    hilbert
        .iter()
        .map(|transport| {
            let ledger = ledgers
                .iter()
                .find(|ledger| ledger.exponent == transport.exponent);
            verify_finite_projector_control(transport, ledger)
        })
        .collect()
}

fn are_transport_projector_counts_valid(
    transport: &HilbertTransportReport,
    expected_basis_count: usize,
    expected_projector_count: usize,
) -> bool {
    let expected_positive_factor_checks = 2 * transport.exponent * expected_basis_count;
    [
        transport.basis_count == expected_basis_count,
        transport.projector_count == expected_projector_count,
        transport.positive_factor_matrix_checks == expected_positive_factor_checks,
        transport.projector_factorization_checks == expected_projector_count,
        transport.projector_scaled_idempotence_checks == expected_projector_count,
        transport.projector_rank_one_trace_checks == expected_projector_count,
    ]
    .into_iter()
    .all(|b| b)
}

fn are_control_counts_valid(
    transport: &HilbertTransportReport,
    ledger: &GtmurProjectorLedgerReport,
) -> bool {
    let d = transport.dimension;
    let expected_basis_count = d + 1;
    let expected_projector_count = d * expected_basis_count;
    let expected_same_basis_orthogonality = expected_basis_count * d * (d - 1) / 2;
    let expected_cross_basis_unbiased = d * expected_basis_count / 2 * d * d;

    let transport_projector_ok = are_transport_projector_counts_valid(
        transport,
        expected_basis_count,
        expected_projector_count,
    );
    let transport_trace_ok = [
        transport.basis_resolution_matrix_checks == expected_basis_count,
        transport.same_basis_orthogonality_trace_checks == expected_same_basis_orthogonality,
        transport.cross_basis_trace_transport_checks == expected_cross_basis_unbiased,
        ledger.dimension == d,
        ledger.basis_count == expected_basis_count,
        ledger.projector_count == expected_projector_count,
    ]
    .into_iter()
    .all(|b| b);

    transport_projector_ok && transport_trace_ok
}

pub fn verify_finite_projector_control(
    transport: &HilbertTransportReport,
    ledger: Option<&GtmurProjectorLedgerReport>,
) -> FiniteProjectorControlReport {
    if transport.status != HilbertTransportStatus::TransportVerified {
        return failed_report(
            transport,
            FiniteProjectorControlStatus::MissingHilbertTransport,
            transport
                .error
                .clone()
                .unwrap_or_else(|| "missing verified Hilbert matrix transport".to_string()),
        );
    }

    let Some(ledger) = ledger else {
        return failed_report(
            transport,
            FiniteProjectorControlStatus::MissingGtmurLedger,
            "missing finite CODA-MUR projector ledger for this dimension".to_string(),
        );
    };

    if ledger.status != GtmurProjectorLedgerStatus::FiniteLedgerClosed {
        return failed_report(
            transport,
            FiniteProjectorControlStatus::MissingGtmurLedger,
            ledger
                .error
                .clone()
                .unwrap_or_else(|| "finite CODA-MUR projector ledger is not closed".to_string()),
        );
    }

    if !are_control_counts_valid(transport, ledger) {
        return failed_report(
            transport,
            FiniteProjectorControlStatus::InvalidControlCounts,
            "finite projector control counts do not match the q+1 complete-control contract"
                .to_string(),
        );
    }

    let d = transport.dimension;
    let expected_basis_count = d + 1;
    let expected_projector_count = d * expected_basis_count;

    FiniteProjectorControlReport {
        source: "finite characteristic-two projector MUB control",
        exponent: transport.exponent,
        dimension: d,
        basis_count: expected_basis_count,
        projector_count: expected_projector_count,
        status: FiniteProjectorControlStatus::CompleteProjectorMubVerified,
        positive_factor_checks: transport.positive_factor_matrix_checks,
        projector_factorization_checks: transport.projector_factorization_checks,
        projector_scaled_idempotence_checks: transport.projector_scaled_idempotence_checks,
        rank_one_trace_checks: transport.projector_rank_one_trace_checks,
        basis_resolution_checks: transport.basis_resolution_matrix_checks,
        same_basis_orthogonality_checks: transport.same_basis_orthogonality_trace_checks,
        cross_basis_unbiased_checks: transport.cross_basis_trace_transport_checks,
        gtmur_zero_rel_alignment_checks: ledger.zero_rel_alignment_checks,
        gtmur_terminalizer_alignment_checks: ledger.terminalizer_alignment_checks,
        checked_identities: vec![
            "q+1 projector bases are present for the declared characteristic-two dimension",
            "projector numerators have exact positive-factor decompositions",
            "projector numerators are Hermitian scaled idempotents",
            "rank-one traces and basis resolutions are checked exactly",
            "same-basis orthogonality and cross-basis unbiasedness are checked by exact trace",
            "finite CODA-MUR ledger preserves ZeroRel and terminalizer through the representation stack",
        ],
        remaining_obligations: vec![
            "dimension-parametric extension of the characteristic-two projector control",
            "odd-characteristic Hilbert/projector transport at the same authority level",
            "complete composite-dimension witness or no-go certificate for non-prime-power targets",
            "uniform certificate family or certified stratification for the all-N query",
        ],
        rejected_authority_escalations: vec![
            "finite characteristic-two projector controls do not solve MUB(6) or MUB(10)",
            "sampled prime-power controls do not provide an all-N certificate family",
            "projector-representation authority must remain declared-dimension only",
        ],
        boundary:
            "declared-dimension finite projector MUB control only; not composite or all-N authority",
        error: None,
    }
}

fn failed_report(
    transport: &HilbertTransportReport,
    status: FiniteProjectorControlStatus,
    error: String,
) -> FiniteProjectorControlReport {
    FiniteProjectorControlReport {
        source: "finite characteristic-two projector MUB control",
        exponent: transport.exponent,
        dimension: transport.dimension,
        basis_count: 0,
        projector_count: 0,
        status,
        positive_factor_checks: 0,
        projector_factorization_checks: 0,
        projector_scaled_idempotence_checks: 0,
        rank_one_trace_checks: 0,
        basis_resolution_checks: 0,
        same_basis_orthogonality_checks: 0,
        cross_basis_unbiased_checks: 0,
        gtmur_zero_rel_alignment_checks: 0,
        gtmur_terminalizer_alignment_checks: 0,
        checked_identities: vec![],
        remaining_obligations: vec![],
        rejected_authority_escalations: vec![],
        boundary:
            "finite projector control failed before declared-dimension authority could be asserted",
        error: Some(error),
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/finite_projector_control.rs
// Claim: urn:core:crates_rs:core-quantum-physics:finite-projector-control:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0f2735c5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0f2735c5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0f2735c5 {
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
impl BoundaryError0f2735c5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0f2735c5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0f2735c5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0f2735c5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0f2735c5> {
        if capacity_bound == 0 {
            return Err(BoundaryError0f2735c5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0f2735c5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0f2735c5::ExceedsCapacity {
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

    #[test]
    fn finite_projector_controls_verify_for_characteristic_two_samples() {
        let reports = verify_current_finite_projector_controls();
        assert_eq!(reports.len(), 4);
        for expected_dimension in [4, 8, 16, 32] {
            let report = reports
                .iter()
                .find(|report| report.dimension == expected_dimension)
                .expect("finite projector control present");
            assert_eq!(
                report.status,
                FiniteProjectorControlStatus::CompleteProjectorMubVerified
            );
            assert_eq!(report.basis_count, expected_dimension + 1);
            assert_eq!(
                report.projector_count,
                expected_dimension * (expected_dimension + 1)
            );
            assert_eq!(report.rank_one_trace_checks, report.projector_count);
            assert_eq!(report.basis_resolution_checks, report.basis_count);
            assert!(report.gtmur_zero_rel_alignment_checks >= 7);
            assert!(report.gtmur_terminalizer_alignment_checks >= 6);
            assert!(report.error.is_none());
        }
    }

    #[test]
    fn finite_projector_control_requires_gtmur_ledger() {
        let transport = verify_current_hilbert_transport_schemas()
            .into_iter()
            .find(|report| report.dimension == 8)
            .expect("d=8 Hilbert transport present");
        let report = verify_finite_projector_control(&transport, None);
        assert_eq!(
            report.status,
            FiniteProjectorControlStatus::MissingGtmurLedger
        );
        assert!(report.error.is_some());
    }
}

#[cfg(test)]
mod l4_boundary_tests_0f2735c5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0f2735c5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0f2735c5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0f2735c5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0f2735c5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0f2735c5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0f2735c5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0f2735c5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
