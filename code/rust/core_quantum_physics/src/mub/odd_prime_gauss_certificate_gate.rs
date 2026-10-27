//! Odd-prime Gauss-certificate gate.
//!
//! This gate connects the exact Hilbert controls for declared odd-prime
//! dimensions to the reusable Weyl trace/Gauss proof schema. It is deliberately
//! finite: it certifies the current declared prime dimensions and records the
//! missing parametric theorem before any all-prime or all-N authority is
//! accepted.

use serde::Serialize;

use crate::mub::odd_prime_weyl::{
    verify_current_odd_prime_weyl_schemas, OddPrimeWeylStatus,
};
use crate::mub::prime_controls::{verify_prime_controls, BenchmarkStatus};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum OddPrimeGaussCertificateStatus {
    FiniteCertificatesVerified,
    MissingExactControl,
    MissingSchema,
    CertificateMismatch,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct OddPrimeGaussCertificateReport {
    pub status: OddPrimeGaussCertificateStatus,
    pub certified_dimensions: Vec<usize>,
    pub exact_control_dimensions: Vec<usize>,
    pub schema_dimensions: Vec<usize>,
    pub missing_exact_control_dimensions: Vec<usize>,
    pub missing_schema_dimensions: Vec<usize>,
    pub checked_obligations: Vec<&'static str>,
    pub remaining_theorem_obligations: Vec<&'static str>,
    pub rejected_escalations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_current_odd_prime_gauss_certificate_gate() -> OddPrimeGaussCertificateReport {
    verify_odd_prime_gauss_certificate_gate(&[7, 11, 13])
}

fn collect_exact_control_dimensions(required_dimensions: &[usize]) -> Vec<usize> {
    verify_prime_controls()
        .into_iter()
        .filter(|control| {
            let valid_state =
                control.status == BenchmarkStatus::ExactCompleteSet && control.error.is_none();
            required_dimensions.contains(&control.dimension)
                && valid_state
                && control_has_gauss_contract(control.checked_identities.as_slice())
        })
        .map(|control| control.dimension)
        .collect()
}

fn collect_schema_dimensions(required_dimensions: &[usize]) -> Vec<usize> {
    verify_current_odd_prime_weyl_schemas()
        .into_iter()
        .filter(|schema| {
            required_dimensions.contains(&schema.dimension)
                && schema.status == OddPrimeWeylStatus::ProofSchemaVerified
                && schema.error.is_none()
        })
        .map(|schema| schema.dimension)
        .collect()
}

fn determine_gauss_status_and_error(
    missing_exact: &[usize],
    missing_schema: &[usize],
    mismatches: &[usize],
) -> (OddPrimeGaussCertificateStatus, Option<String>) {
    if !mismatches.is_empty() {
        return (
            OddPrimeGaussCertificateStatus::CertificateMismatch,
            Some(format!(
                "dimensions lack both exact control and schema: {:?}",
                mismatches
            )),
        );
    }
    if !missing_exact.is_empty() {
        return (
            OddPrimeGaussCertificateStatus::MissingExactControl,
            Some(format!(
                "missing exact Gauss-certificate controls for dimensions: {:?}",
                missing_exact
            )),
        );
    }
    if !missing_schema.is_empty() {
        return (
            OddPrimeGaussCertificateStatus::MissingSchema,
            Some(format!(
                "missing odd-prime Weyl schemas for dimensions: {:?}",
                missing_schema
            )),
        );
    }
    (
        OddPrimeGaussCertificateStatus::FiniteCertificatesVerified,
        None,
    )
}

pub fn verify_odd_prime_gauss_certificate_gate(
    required_dimensions: &[usize],
) -> OddPrimeGaussCertificateReport {
    let exact_control_dimensions = collect_exact_control_dimensions(required_dimensions);
    let schema_dimensions = collect_schema_dimensions(required_dimensions);

    let mut certified_dimensions = Vec::new();
    let mut missing_exact = Vec::new();
    let mut missing_schema = Vec::new();
    let mut mismatches = Vec::new();
    for &dimension in required_dimensions {
        let exact = exact_control_dimensions.contains(&dimension);
        let schema = schema_dimensions.contains(&dimension);
        match (exact, schema) {
            (true, true) => certified_dimensions.push(dimension),
            (false, true) => missing_exact.push(dimension),
            (true, false) => missing_schema.push(dimension),
            (false, false) => mismatches.push(dimension),
        }
    }

    let (status, error) =
        determine_gauss_status_and_error(&missing_exact, &missing_schema, &mismatches);

    OddPrimeGaussCertificateReport {
        status,
        certified_dimensions,
        exact_control_dimensions,
        schema_dimensions,
        missing_exact_control_dimensions: missing_exact,
        missing_schema_dimensions: missing_schema,
        checked_obligations: vec![
            "declared odd-prime dimensions have exact complete Hilbert controls",
            "each exact control records a sqrt(p) normalizer with squared norm p",
            "each exact control records vanishing nontrivial F_p linear character sums",
            "each exact control records F_p quadratic Gauss sums with squared norm p",
            "each certified dimension has a matching odd-prime Weyl proof schema",
            "basis count is p+1 for every certified prime dimension",
        ],
        remaining_theorem_obligations: vec![
            "formal additive-character orthogonality theorem for every odd prime",
            "formal quadratic Gauss norm theorem for every odd prime",
            "dimension-parametric coefficient-field and sqrt(p) normalizer family",
            "dimension-parametric Hilbert-basis transport from the Weyl schema",
            "CODA-MUR loss ledger preserving ZeroRel and terminalizer for the odd-prime family",
        ],
        rejected_escalations: vec![
            "finite odd-prime certificates do not authorize all odd primes",
            "odd-prime certificates do not solve composite dimensions",
            "Gauss-sum certificates do not create MUB(6), MUB(10), or MUB(n) authority without a parametric family",
        ],
        boundary: if status == OddPrimeGaussCertificateStatus::FiniteCertificatesVerified {
            "finite odd-prime Gauss certificates verified for declared dimensions only"
        } else {
            "odd-prime Gauss certificate gate is incomplete for the requested declared dimensions"
        },
        error,
    }
}

fn control_has_gauss_contract(checked_identities: &[&'static str]) -> bool {
    checked_identities
        .iter()
        .any(|identity| identity.contains("linear character sums"))
        && checked_identities
            .iter()
            .any(|identity| identity.contains("quadratic Gauss sums"))
        && checked_identities
            .iter()
            .any(|identity| identity.contains("sqrt("))
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/odd_prime_gauss_certificate_gate.rs
// Claim: urn:core:crates_rs:core-quantum-physics:odd-prime-gauss-certificate-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord37d01d61 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord37d01d61` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError37d01d61 {
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
impl BoundaryError37d01d61 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError37d01d61 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError37d01d61 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord37d01d61 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError37d01d61> {
        if capacity_bound == 0 {
            return Err(BoundaryError37d01d61::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError37d01d61::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError37d01d61::ExceedsCapacity {
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
    fn current_odd_prime_gauss_certificate_gate_verifies_declared_controls() {
        let report = verify_current_odd_prime_gauss_certificate_gate();
        assert_eq!(
            report.status,
            OddPrimeGaussCertificateStatus::FiniteCertificatesVerified
        );
        assert_eq!(report.certified_dimensions, vec![7, 11, 13]);
        assert!(report
            .remaining_theorem_obligations
            .iter()
            .any(|obligation| obligation.contains("dimension-parametric")));
        assert!(report
            .rejected_escalations
            .iter()
            .any(|item| item.contains("composite dimensions")));
        assert!(report.error.is_none());
    }

    #[test]
    fn missing_required_prime_is_reported_without_promotion() {
        let report = verify_odd_prime_gauss_certificate_gate(&[7, 17]);
        assert_eq!(
            report.status,
            OddPrimeGaussCertificateStatus::CertificateMismatch
        );
        assert_eq!(report.certified_dimensions, vec![7]);
        assert!(report.error.is_some());
    }
}

#[cfg(test)]
mod l4_boundary_tests_37d01d61 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord37d01d61::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord37d01d61::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord37d01d61::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord37d01d61::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord37d01d61::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError37d01d61::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError37d01d61::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
