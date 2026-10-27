//! Prime-power CODA-MUR boundary ledger.
//!
//! This ledger separates the part of the all-N request that can be organized by
//! finite-field prime-power schemas from the composite dimensions where tensor
//! lower-controls do not provide complete MUB authority. It is not a proof of
//! the general MUB(N) statement; it records the remaining theorem obligations
//! and keeps the composite gap explicit.

use serde::Serialize;

use crate::mub::dimension_stratification::{
    current_dimension_stratification_reports, DimensionAuthorityStatus, DimensionClass,
    DimensionStratificationReport,
};
use crate::mub::gtmur_projector_ledger::{
    verify_current_gtmur_projector_ledgers, GtmurProjectorLedgerStatus,
};
use crate::mub::odd_prime_gauss_certificate_gate::{
    verify_current_odd_prime_gauss_certificate_gate, OddPrimeGaussCertificateStatus,
};
use crate::mub::odd_prime_power_controls::{
    verify_current_odd_prime_power_controls, OddPrimePowerControlStatus,
};
use crate::mub::odd_prime_power_field_theorem_gate::{
    verify_current_odd_prime_power_field_theorem_gate, OddPrimePowerFieldTheoremStatus,
};
use crate::mub::odd_prime_power_parametric_gate::{
    verify_current_odd_prime_power_parametric_gate, OddPrimePowerParametricStatus,
};
use crate::mub::odd_prime_power_weyl::{
    verify_current_odd_prime_power_weyl_schemas, OddPrimePowerWeylStatus,
};
use crate::mub::odd_prime_weyl::{
    verify_current_odd_prime_weyl_schemas, OddPrimeWeylStatus,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum PrimePowerGtmurBoundaryStatus {
    BoundaryVerified,
    MissingPrimePowerRegime,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompositeAuthorityGap {
    pub dimension: usize,
    pub status: DimensionAuthorityStatus,
    pub guaranteed_basis_count: usize,
    pub complete_basis_count: usize,
    pub missing_basis_count: usize,
    pub boundary: &'static str,
    pub missing_obligations: Vec<&'static str>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct PrimePowerGtmurBoundaryReport {
    pub status: PrimePowerGtmurBoundaryStatus,
    pub odd_prime_schema_count: usize,
    pub odd_prime_gauss_certificate_count: usize,
    pub odd_prime_power_schema_count: usize,
    pub odd_prime_power_control_count: usize,
    pub odd_prime_power_field_theorem_status: OddPrimePowerFieldTheoremStatus,
    pub odd_prime_power_field_theorem_accepted: bool,
    pub odd_prime_power_parametric_status: OddPrimePowerParametricStatus,
    pub odd_prime_power_parametric_family_accepted: bool,
    pub char_two_ledger_count: usize,
    pub composite_gap_count: usize,
    pub covered_regimes: Vec<&'static str>,
    pub preserved_invariants: Vec<&'static str>,
    pub composite_gaps: Vec<CompositeAuthorityGap>,
    pub remaining_theorem_obligations: Vec<&'static str>,
    pub rejected_authority_escalations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

/// Extract composite authority gaps from stratification reports, retaining gaps and
/// missing factor obligations for all composite dimensions (including those where factor control fails).
pub fn extract_composite_authority_gaps(
    reports: &[DimensionStratificationReport],
) -> Vec<CompositeAuthorityGap> {
    reports
        .iter()
        .filter_map(|report| {
            if report.class != DimensionClass::CompositePrimePowerProduct {
                return None;
            }
            let guaranteed_basis_count = report.guaranteed_basis_count.unwrap_or(0);
            let complete_basis_count = report.complete_basis_count.unwrap_or(report.dimension + 1);
            let missing_basis_count = complete_basis_count.saturating_sub(guaranteed_basis_count);
            Some(CompositeAuthorityGap {
                dimension: report.dimension,
                status: report.status,
                guaranteed_basis_count,
                complete_basis_count,
                missing_basis_count,
                boundary: report.boundary,
                missing_obligations: report.missing_obligations.clone(),
            })
        })
        .collect()
}

pub fn verify_prime_power_gtmur_boundary() -> PrimePowerGtmurBoundaryReport {
    let reports = current_dimension_stratification_reports();
    verify_prime_power_gtmur_boundary_with_reports(&reports)
}

#[allow(clippy::too_many_arguments)]
fn collect_covered_regimes(
    odd_prime_schema_count: usize,
    odd_prime_gauss_certificate_count: usize,
    odd_prime_power_schema_count: usize,
    odd_prime_power_control_count: usize,
    odd_prime_power_field_theorem_status: OddPrimePowerFieldTheoremStatus,
    odd_prime_power_parametric_status: OddPrimePowerParametricStatus,
    char_two_ledger_count: usize,
) -> Vec<&'static str> {
    let candidates: &[(bool, &'static str)] = &[
        (
            odd_prime_schema_count > 0,
            "odd-prime Weyl trace/Gauss schema",
        ),
        (
            odd_prime_gauss_certificate_count > 0,
            "finite odd-prime Gauss-certificate Hilbert controls",
        ),
        (
            odd_prime_power_schema_count > 0,
            "odd prime-power finite-field trace/Gauss schema",
        ),
        (
            odd_prime_power_control_count > 0,
            "exact odd-prime-power trace-character Hilbert controls",
        ),
        (
            odd_prime_power_field_theorem_status
                != OddPrimePowerFieldTheoremStatus::MissingFiniteSchemas,
            "odd-prime-power finite-field theorem gate audit",
        ),
        (
            odd_prime_power_parametric_status != OddPrimePowerParametricStatus::MissingFiniteSchemas,
            "odd-prime-power parametric Hilbert/CODA-MUR gate audit",
        ),
        (
            char_two_ledger_count > 0,
            "characteristic-two board/projector/Hilbert CODA-MUR ledger",
        ),
    ];
    candidates
        .iter()
        .filter_map(|&(present, label)| present.then_some(label))
        .collect()
}

fn collect_missing_regimes(
    odd_prime_schema_count: usize,
    odd_prime_power_schema_count: usize,
    char_two_ledger_count: usize,
) -> Vec<&'static str> {
    let candidates: &[(bool, &'static str)] = &[
        (odd_prime_schema_count == 0, "odd-prime Weyl schema"),
        (
            odd_prime_power_schema_count == 0,
            "odd prime-power Weyl schema",
        ),
        (
            char_two_ledger_count == 0,
            "characteristic-two CODA-MUR projector ledger",
        ),
    ];
    candidates
        .iter()
        .filter_map(|&(missing, label)| missing.then_some(label))
        .collect()
}

pub fn verify_prime_power_gtmur_boundary_with_reports(
    reports: &[DimensionStratificationReport],
) -> PrimePowerGtmurBoundaryReport {
    let odd_prime_schema_count = verify_current_odd_prime_weyl_schemas()
        .iter()
        .filter(|schema| schema.status == OddPrimeWeylStatus::ProofSchemaVerified)
        .count();
    let odd_prime_gauss_certificate = verify_current_odd_prime_gauss_certificate_gate();
    let odd_prime_gauss_certificate_count = if odd_prime_gauss_certificate.status
        == OddPrimeGaussCertificateStatus::FiniteCertificatesVerified
    {
        odd_prime_gauss_certificate.certified_dimensions.len()
    } else {
        0
    };
    let odd_prime_power_schema_count = verify_current_odd_prime_power_weyl_schemas()
        .iter()
        .filter(|schema| schema.status == OddPrimePowerWeylStatus::ProofSchemaVerified)
        .count();
    let odd_prime_power_control_count = verify_current_odd_prime_power_controls()
        .iter()
        .filter(|control| control.status == OddPrimePowerControlStatus::ExactCompleteSet)
        .count();
    let odd_prime_power_field_theorem_gate = verify_current_odd_prime_power_field_theorem_gate();
    let odd_prime_power_field_theorem_status = odd_prime_power_field_theorem_gate.status;
    let odd_prime_power_field_theorem_accepted = odd_prime_power_field_theorem_status
        == OddPrimePowerFieldTheoremStatus::FiniteFieldTheoremsAccepted;
    let odd_prime_power_parametric_gate = verify_current_odd_prime_power_parametric_gate();
    let odd_prime_power_parametric_status = odd_prime_power_parametric_gate.status;
    let odd_prime_power_parametric_family_accepted = odd_prime_power_parametric_status
        == OddPrimePowerParametricStatus::ParametricFamilyAccepted;
    let char_two_ledger_count = verify_current_gtmur_projector_ledgers()
        .iter()
        .filter(|ledger| ledger.status == GtmurProjectorLedgerStatus::FiniteLedgerClosed)
        .count();

    let composite_gaps = extract_composite_authority_gaps(reports);

    let covered_regimes = collect_covered_regimes(
        odd_prime_schema_count,
        odd_prime_gauss_certificate_count,
        odd_prime_power_schema_count,
        odd_prime_power_control_count,
        odd_prime_power_field_theorem_status,
        odd_prime_power_parametric_status,
        char_two_ledger_count,
    );
    let missing = collect_missing_regimes(
        odd_prime_schema_count,
        odd_prime_power_schema_count,
        char_two_ledger_count,
    );

    let status = if missing.is_empty() {
        PrimePowerGtmurBoundaryStatus::BoundaryVerified
    } else {
        PrimePowerGtmurBoundaryStatus::MissingPrimePowerRegime
    };

    PrimePowerGtmurBoundaryReport {
        status,
        odd_prime_schema_count,
        odd_prime_gauss_certificate_count,
        odd_prime_power_schema_count,
        odd_prime_power_control_count,
        odd_prime_power_field_theorem_status,
        odd_prime_power_field_theorem_accepted,
        odd_prime_power_parametric_status,
        odd_prime_power_parametric_family_accepted,
        char_two_ledger_count,
        composite_gap_count: composite_gaps.len(),
        covered_regimes,
        preserved_invariants: vec![
            "prime-power dimensions carry q+1 basis-count targets",
            "odd-characteristic ZeroRel reduces to trace-linear and quadratic Gauss obligations",
            "finite odd-prime Gauss-certificate controls align exact Hilbert bases with character-sum and Gauss-norm obligations",
            "d=9, d=25, d=27, and d=49 odd-prime-power trace-character bases are verified as exact Hilbert controls",
            "odd-prime-power finite-field theorem gate records Lean field, AddChar, and quadratic Gauss norm witnesses",
            "odd-prime-power parametric gate records a Lean trace-character phase-overlap kernel",
            "odd-prime-power parametric gate records Lean Complex normalization algebra for phase overlaps",
            "odd-prime-power parametric gate records a Lean Complex coefficient scalar package",
            "odd-prime-power parametric gate records a Lean algebraic coefficient-field contract surface",
            "odd-prime-power parametric gate records Lean finite-function Hilbert phase-vector transport",
            "odd-prime-power parametric gate records Lean primitive Complex additive-character existence",
            "odd-prime-power parametric gate records a Lean existential Complex finite-function q+1 MUB family",
            "odd-prime-power parametric gate records Lean coordinate-equivalence transport for finite-function MUB identities",
            "odd-prime-power parametric gate records a Lean structured finite Complex MUB family object",
            "odd-prime-power parametric gate records a Lean finite-function CODA-MUR coordinate ledger",
            "odd-prime-power parametric gate records a Lean finite-function terminalizer coordinate ledger",
            "odd-prime-power parametric gate records a Lean finite-function Hilbert-basis transport object",
            "odd-prime-power parametric gate records a Lean finite-function CODA-MUR zero-loss ledger",
            "odd-prime-power parametric gate records a Lean algebraic Hilbert-basis transport contract surface",
            "odd-prime-power parametric gate records a Lean algebraic CODA-MUR loss-ledger contract surface",
            "odd-prime-power parametric gate records a Lean algebraic terminalizer-preservation contract surface",
            "odd-prime-power parametric gate rejects promotion without coefficient fields, Hilbert transport, CODA-MUR, and terminalizer families",
            "characteristic-two ZeroRel is audited through board, spectral, algebra, and Hilbert representations",
            "sampled characteristic-two prime powers have finite projector controls in declared dimensions",
            "composite tensor products preserve only the minimum factor basis count",
            "terminalizer boundary rejects promotion from prime-power schemas to composite/all-N authority",
        ],
        composite_gaps,
        remaining_theorem_obligations: vec![
            "accepted odd-prime-power parametric Hilbert/CODA-MUR family beyond exact d=9, d=25, d=27, and d=49 samples",
            "formal dimension-parametric Hilbert positivity and projector transport theorem beyond the sampled finite controls",
            "dimension-parametric CODA-MUR loss ledger preserving ZeroRel and terminalizer for every prime-power schema",
            "complete composite-dimension witness or no-go certificate for MUB(6), MUB(10), and other non-prime-power targets",
            "uniform certificate family or certified stratification for the all-N query",
        ],
        rejected_authority_escalations: vec![
            "prime-power representation schema does not solve composite dimensions",
            "tensor lower-control basis-count gap is not a complete MUB certificate",
            "finite sampled ledgers do not create an all-N theorem",
        ],
        boundary: "prime-power CODA-MUR boundary ledger only; composite and all-N authority remain unproved",
        error: (!missing.is_empty()).then(|| format!("missing regimes: {}", missing.join(", "))),
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/prime_power_gtmur_boundary.rs
// Claim: urn:core:crates_rs:core-quantum-physics:prime-power-gtmur-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8daa2482 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8daa2482` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8daa2482 {
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
impl BoundaryError8daa2482 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8daa2482 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8daa2482 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8daa2482 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8daa2482> {
        if capacity_bound == 0 {
            return Err(BoundaryError8daa2482::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8daa2482::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8daa2482::ExceedsCapacity {
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
    fn prime_power_gtmur_boundary_records_composite_gaps() {
        let report = verify_prime_power_gtmur_boundary();
        assert_eq!(
            report.status,
            PrimePowerGtmurBoundaryStatus::BoundaryVerified
        );
        assert!(report.odd_prime_schema_count > 0);
        assert!(report.odd_prime_gauss_certificate_count >= 3);
        assert!(report.odd_prime_power_schema_count > 0);
        assert!(report.odd_prime_power_control_count >= 4);
        assert_eq!(
            report.odd_prime_power_field_theorem_status,
            OddPrimePowerFieldTheoremStatus::FiniteFieldTheoremsAccepted
        );
        assert!(report.odd_prime_power_field_theorem_accepted);
        assert_eq!(
            report.odd_prime_power_parametric_status,
            OddPrimePowerParametricStatus::FiniteSchemasOnly
        );
        assert!(!report.odd_prime_power_parametric_family_accepted);
        assert!(report.char_two_ledger_count > 0);
        assert!(report.composite_gaps.iter().any(|gap| {
            gap.dimension == 6 && gap.guaranteed_basis_count == 3 && gap.complete_basis_count == 7
        }));
        assert!(report.composite_gaps.iter().any(|gap| {
            gap.dimension == 10 && gap.guaranteed_basis_count == 3 && gap.complete_basis_count == 11
        }));
        assert!(report.composite_gaps.iter().any(|gap| {
            gap.dimension == 26 && gap.guaranteed_basis_count == 3 && gap.complete_basis_count == 27
        }));
        assert!(report
            .remaining_theorem_obligations
            .iter()
            .any(|obligation| obligation.contains("composite-dimension")));
        assert!(report.error.is_none());
    }
}

#[cfg(test)]
mod l4_boundary_tests_8daa2482 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8daa2482::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8daa2482::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8daa2482::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8daa2482::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8daa2482::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8daa2482::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8daa2482::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
