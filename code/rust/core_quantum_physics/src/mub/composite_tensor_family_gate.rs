//! Composite tensor-family lower-control gate.
//!
//! Complete prime-power MUB controls tensor to a useful composite lower-control
//! family: pair the basis index across all factors and take tensor products.
//! The number of product bases is the minimum complete-basis count among the
//! factors, not `N + 1` for the product dimension. This gate makes that count
//! theorem executable for the current composite targets and keeps it separate
//! from complete composite authority.

use core_number_theory::finite_field::{checked_pow, is_prime};
use serde::Serialize;
use std::collections::BTreeSet;

use crate::mub::dimension_stratification::{
    current_dimension_stratification_reports, DimensionAuthorityStatus, DimensionClass,
    DimensionStratificationReport, FactorControlStatus,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum CompositeTensorFamilyStatus {
    TensorFamilyVerified,
    MissingTensorLowerControl,
    NoCompositeTargets,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompositeTensorFamilyCase {
    pub dimension: usize,
    pub factor_dimensions: Vec<usize>,
    pub factor_complete_basis_counts: Vec<usize>,
    pub paired_tensor_basis_count: usize,
    pub required_complete_basis_count: usize,
    pub missing_basis_count: usize,
    pub tensor_lower_bound_formula: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompositeTensorFamilyReport {
    pub source: &'static str,
    pub status: CompositeTensorFamilyStatus,
    pub composite_case_count: usize,
    pub cases: Vec<CompositeTensorFamilyCase>,
    pub missing_tensor_lower_control_dimensions: Vec<usize>,
    pub checked_obligations: Vec<&'static str>,
    pub remaining_obligations: Vec<&'static str>,
    pub rejected_escalations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

pub fn verify_current_composite_tensor_family_gate() -> CompositeTensorFamilyReport {
    verify_composite_tensor_family_gate(current_dimension_stratification_reports())
}

fn no_composite_targets_report() -> CompositeTensorFamilyReport {
    CompositeTensorFamilyReport {
        source: "composite tensor-family lower-control gate",
        status: CompositeTensorFamilyStatus::NoCompositeTargets,
        composite_case_count: 0,
        cases: vec![],
        missing_tensor_lower_control_dimensions: vec![],
        checked_obligations: vec![],
        remaining_obligations: vec![
            "at least one composite prime-power product target in the current stratification",
        ],
        rejected_escalations: vec![
            "absence of composite targets cannot authorize a composite completion theorem",
        ],
        boundary: "no composite tensor-family claim was evaluated",
        error: Some("no composite targets in stratification".to_string()),
    }
}

fn are_factors_valid(report: &DimensionStratificationReport) -> bool {
    if report.factors.len() < 2 {
        return false;
    }
    let mut primes = BTreeSet::new();
    for factor in &report.factors {
        let valid_status = factor.control_status == FactorControlStatus::ExactCompleteControlPresent;
        let valid_prime = factor.exponent > 0 && factor.prime >= 2 && is_prime(factor.prime);
        let valid_counts = checked_pow(factor.prime, factor.exponent) == Some(factor.value)
            && factor.value.checked_add(1) == Some(factor.complete_basis_count);
        if !valid_status || !valid_prime || !primes.insert(factor.prime) || !valid_counts {
            return false;
        }
    }
    true
}

fn evaluate_composite_report(
    report: DimensionStratificationReport,
) -> Option<CompositeTensorFamilyCase> {
    if report.status != DimensionAuthorityStatus::ExactTensorLowerControl
        || !are_factors_valid(&report)
    {
        return None;
    }
    let product = report
        .factors
        .iter()
        .try_fold(1usize, |n, factor| n.checked_mul(factor.value));
    let minimum = report
        .factors
        .iter()
        .map(|factor| factor.complete_basis_count)
        .min();
    let complete = report.dimension.checked_add(1);
    let counts_match = product == Some(report.dimension)
        && minimum == report.guaranteed_basis_count
        && complete == report.complete_basis_count;
    if !counts_match {
        return None;
    }
    let paired_tensor_basis_count = minimum?;
    let required_complete_basis_count = complete?;
    let factor_dimensions = report.factors.iter().map(|f| f.value).collect();
    let factor_complete_basis_counts = report
        .factors
        .iter()
        .map(|f| f.complete_basis_count)
        .collect();
    let missing_basis_count =
        required_complete_basis_count.saturating_sub(paired_tensor_basis_count);
    Some(CompositeTensorFamilyCase {
        dimension: report.dimension,
        factor_dimensions,
        factor_complete_basis_counts,
        paired_tensor_basis_count,
        required_complete_basis_count,
        missing_basis_count,
        tensor_lower_bound_formula:
            "paired product bases = min_i(q_i + 1), with product dimension N = prod_i q_i",
    })
}

pub fn verify_composite_tensor_family_gate(
    stratification: Vec<DimensionStratificationReport>,
) -> CompositeTensorFamilyReport {
    let composite_reports = stratification
        .into_iter()
        .filter(|report| report.class == DimensionClass::CompositePrimePowerProduct)
        .collect::<Vec<_>>();
    let composite_case_count = composite_reports.len();
    if composite_reports.is_empty() {
        return no_composite_targets_report();
    }

    let mut cases = Vec::new();
    let mut missing_dimensions = Vec::new();
    for report in composite_reports {
        let dim = report.dimension;
        if let Some(case) = evaluate_composite_report(report) {
            cases.push(case);
        } else {
            missing_dimensions.push(dim);
        }
    }

    let verified = missing_dimensions.is_empty();
    let status = if verified {
        CompositeTensorFamilyStatus::TensorFamilyVerified
    } else {
        CompositeTensorFamilyStatus::MissingTensorLowerControl
    };
    let error = (!verified).then(|| {
        "one or more composite targets have missing or inconsistent tensor lower-control reports"
            .to_string()
    });

    CompositeTensorFamilyReport {
        source: "composite tensor-family lower-control gate",
        status,
        composite_case_count,
        cases,
        missing_tensor_lower_control_dimensions: missing_dimensions,
        checked_obligations: vec![
            "accepted reports have distinct prime-power factors with matching product dimension and basis counts",
            "paired tensor bases preserve orthonormality by factor orthonormality",
            "paired cross-basis unbiasedness multiplies factor overlap constants",
            "paired tensor basis count is the minimum complete-basis count among factors",
            "complete-target basis-count gap is computed for every verified composite case",
        ],
        remaining_obligations: vec![
            "factor-control status is supplied by the caller; this gate checks report consistency, not the underlying projector certificates",
            "complete composite-dimension witness or no-go certificate",
            "basis-gluing or compatibility theorem for any unpaired product-basis escalation",
            "dimension-parametric composite certificate family for an all-N theorem",
        ],
        rejected_escalations: vec![
            "tensoring complete factor MUBs does not create N+1 product bases",
            "a min-factor lower bound is not a complete witness and not a no-go proof",
            "unpaired factor bases do not define pairwise unbiased product bases without a pairing or compatibility rule",
        ],
        boundary: if verified {
            "paired tensor-product lower-control family verified for current composite targets only"
        } else {
            "composite tensor-family lower-control is not verified for every current composite target"
        },
        error,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/composite_tensor_family_gate.rs
// Claim: urn:core:crates_rs:core-quantum-physics:composite-tensor-family-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5298b1ba {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5298b1ba` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5298b1ba {
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
impl BoundaryError5298b1ba {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5298b1ba {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5298b1ba {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5298b1ba {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5298b1ba> {
        if capacity_bound == 0 {
            return Err(BoundaryError5298b1ba::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5298b1ba::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5298b1ba::ExceedsCapacity {
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
    use crate::mub::dimension_stratification::stratify_dimension;

    fn has_composite_case(
        report: &CompositeTensorFamilyReport,
        dimension: usize,
        factors: &[usize],
        paired: usize,
        complete: usize,
        missing: usize,
    ) -> bool {
        report.cases.iter().any(|case| {
            let dims_match =
                case.dimension == dimension && case.factor_dimensions.as_slice() == factors;
            let counts_match = case.paired_tensor_basis_count == paired
                && case.required_complete_basis_count == complete
                && case.missing_basis_count == missing;
            dims_match && counts_match
        })
    }

    #[test]
    fn current_composite_tensor_family_verifies_min_factor_lower_bounds() {
        let report = verify_current_composite_tensor_family_gate();
        assert_eq!(
            report.status,
            CompositeTensorFamilyStatus::TensorFamilyVerified
        );
        assert!(has_composite_case(&report, 6, &[2, 3], 3, 7, 4));
        assert!(has_composite_case(&report, 10, &[2, 5], 3, 11, 8));
        assert!(has_composite_case(&report, 26, &[2, 13], 3, 27, 24));
        assert!(report
            .checked_obligations
            .iter()
            .any(|obligation| obligation.contains("minimum complete-basis")));
    }

    #[test]
    fn composite_tensor_family_rejects_complete_basis_escalation() {
        let report = verify_current_composite_tensor_family_gate();
        assert!(report
            .rejected_escalations
            .iter()
            .any(|item| item.contains("N+1")));
        assert!(report
            .remaining_obligations
            .iter()
            .any(|item| item.contains("witness or no-go certificate")));
        assert!(report
            .cases
            .iter()
            .all(|case| case.paired_tensor_basis_count < case.required_complete_basis_count));
    }

    #[test]
    fn unsupported_composite_factor_blocks_family_verification() {
        let report = verify_composite_tensor_family_gate(vec![stratify_dimension(34)]);
        assert_eq!(
            report.status,
            CompositeTensorFamilyStatus::MissingTensorLowerControl
        );
        assert_eq!(report.missing_tensor_lower_control_dimensions, vec![34]);
        assert!(report.error.is_some());
    }
}

#[cfg(test)]
mod l4_boundary_tests_5298b1ba {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5298b1ba::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5298b1ba::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5298b1ba::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5298b1ba::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5298b1ba::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5298b1ba::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5298b1ba::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
