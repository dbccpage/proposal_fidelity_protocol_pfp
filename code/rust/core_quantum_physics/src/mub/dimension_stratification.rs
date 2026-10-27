//! Dimension-stratified MUB authority and tensor lower-bound gate.
//!
//! This is a structural gate for the all-N request. It records what follows
//! from the exact finite controls this crate verifies, and what does not
//! follow for composite non-prime-power dimensions.
//!
//! A prime-power factor counts as controlled only if its control runs and
//! verifies in this crate; see [`verified_prime_power_controls`]. The set used
//! to be a hard-coded list. It is now derived from the controls themselves, so
//! a control that stops verifying stops granting `ExactCompleteControlPresent`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_e86642d9<T> {
    fn checked_invariant_e86642d9(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_e86642d9<T> for Option<T> {
    #[inline]
    fn checked_invariant_e86642d9(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_e86642d9<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_e86642d9(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeSet;
use std::sync::OnceLock;

use serde::{Deserialize, Serialize};

use crate::mub::d10_controls::{verify_d5_complete_control, Cyclotomic120Status};
use crate::mub::finite_projector_control::{
    verify_current_finite_projector_controls, FiniteProjectorControlReport,
    FiniteProjectorControlStatus,
};
use crate::mub::odd_prime_power_controls::{
    verify_current_odd_prime_power_controls, OddPrimePowerControlStatus,
};
use crate::mub::prime_controls::{
    verify_prime_controls, verify_prime_power_controls, BenchmarkStatus,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DimensionClass {
    PrimePower,
    CompositePrimePowerProduct,
    Degenerate,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FactorControlStatus {
    ExactCompleteControlPresent,
    MissingExactControl,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PrimePowerFactor {
    pub prime: usize,
    pub exponent: usize,
    pub value: usize,
    pub complete_basis_count: usize,
    pub control_status: FactorControlStatus,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DimensionAuthorityStatus {
    ExactCompleteControl,
    ExactTensorLowerControl,
    MissingFactorControl,
    UnsupportedDimension,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DimensionStratificationReport {
    pub dimension: usize,
    pub class: DimensionClass,
    pub factors: Vec<PrimePowerFactor>,
    pub status: DimensionAuthorityStatus,
    pub guaranteed_basis_count: Option<usize>,
    pub complete_basis_count: Option<usize>,
    pub construction: &'static str,
    pub boundary: &'static str,
    pub missing_obligations: Vec<&'static str>,
}

/// The prime powers whose exact control verifies in this crate, computed once
/// per process by running each control:
///
/// - `prime_controls`: d = 2, 3, 7, 11, 13 and 4, at `ExactCompleteSet`;
/// - `d10_controls::verify_d5_complete_control`: d = 5, at `ExactCompleteSet`;
/// - `odd_prime_power_controls`: d = 9, 25, 27, 49, at `ExactCompleteSet`;
/// - `finite_projector_control`: d = 4, 8, 16, 32, at
///   `CompleteProjectorMubVerified`, after exact Hilbert transport and the
///   finite projector ledger verify. A board schema alone grants no control.
pub fn verified_prime_power_controls() -> &'static BTreeSet<usize> {
    static VERIFIED: OnceLock<BTreeSet<usize>> = OnceLock::new();
    VERIFIED.get_or_init(|| {
        let mut verified = BTreeSet::new();
        for report in verify_prime_controls()
            .into_iter()
            .chain(verify_prime_power_controls())
        {
            if report.status == BenchmarkStatus::ExactCompleteSet {
                verified.insert(report.dimension);
            }
        }
        let d5 = verify_d5_complete_control();
        if d5.status == Cyclotomic120Status::ExactCompleteSet {
            verified.insert(d5.dimension);
        }
        for report in verify_current_odd_prime_power_controls() {
            if report.status == OddPrimePowerControlStatus::ExactCompleteSet {
                verified.insert(report.dimension);
            }
        }
        verified.extend(verified_char_two_dimensions(
            &verify_current_finite_projector_controls(),
        ));
        verified
    })
}

fn verified_char_two_dimensions(reports: &[FiniteProjectorControlReport]) -> BTreeSet<usize> {
    reports
        .iter()
        .filter(|report| {
            report.status == FiniteProjectorControlStatus::CompleteProjectorMubVerified
        })
        .map(|report| report.dimension)
        .collect()
}

/// The dimensions the MUB deep run reports on.
pub fn current_dimension_stratification_reports() -> Vec<DimensionStratificationReport> {
    [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 16, 25, 26, 27, 32, 49]
        .into_iter()
        .map(stratify_dimension)
        .collect()
}

/// Stratifies `dimension` against the prime powers this crate verifies.
pub fn stratify_dimension(dimension: usize) -> DimensionStratificationReport {
    stratify_dimension_with(dimension, verified_prime_power_controls())
}

/// Stratifies `dimension`, counting a prime-power factor as controlled exactly
/// when it is in `controlled`.
pub fn stratify_dimension_with(
    dimension: usize,
    controlled: &BTreeSet<usize>,
) -> DimensionStratificationReport {
    if dimension < 2 {
        return DimensionStratificationReport {
            dimension,
            class: DimensionClass::Degenerate,
            factors: vec![],
            status: DimensionAuthorityStatus::UnsupportedDimension,
            guaranteed_basis_count: None,
            complete_basis_count: None,
            construction: "none",
            boundary: "MUB dimension must be at least 2",
            missing_obligations: vec!["nondegenerate Hilbert-space dimension"],
        };
    }

    let factors = prime_power_factors(dimension, controlled);
    let class = if factors.len() == 1 {
        DimensionClass::PrimePower
    } else {
        DimensionClass::CompositePrimePowerProduct
    };
    let all_supported = factors
        .iter()
        .all(|factor| factor.control_status == FactorControlStatus::ExactCompleteControlPresent);
    let complete_basis_count = Some(dimension + 1);

    match (class, all_supported) {
        (DimensionClass::PrimePower, true) => DimensionStratificationReport {
            dimension,
            class,
            factors,
            status: DimensionAuthorityStatus::ExactCompleteControl,
            guaranteed_basis_count: complete_basis_count,
            complete_basis_count,
            construction:
                "exact complete prime-power control present in the local finite-control corpus",
            boundary: "declared-dimension complete control only; not an all-N theorem",
            missing_obligations: vec![],
        },
        (DimensionClass::PrimePower, false) => DimensionStratificationReport {
            dimension,
            class,
            factors,
            status: DimensionAuthorityStatus::MissingFactorControl,
            guaranteed_basis_count: None,
            complete_basis_count,
            construction:
                "prime-power dimension without a local exact complete-control implementation",
            boundary:
                "known prime-power pattern is not authority until represented and replayed locally",
            missing_obligations: vec![
                "local exact coefficient field for this prime power",
                "local exact complete MUB construction or certificate replay",
            ],
        },
        (DimensionClass::CompositePrimePowerProduct, true) => {
            let lower_bound = factors
                .iter()
                .map(|factor| factor.complete_basis_count)
                .min()
                .checked_invariant_e86642d9("composite factor list is nonempty");
            DimensionStratificationReport {
                dimension,
                class,
                factors,
                status: DimensionAuthorityStatus::ExactTensorLowerControl,
                guaranteed_basis_count: Some(lower_bound),
                complete_basis_count,
                construction: "tensor product of exact complete controls on prime-power factors",
                boundary: "tensor lower-control only; complete authority still requires n+1 bases or a no-go certificate",
                missing_obligations: vec![
                    "complete dimension carrier or no-go target",
                    "proof-carrying complete-set construction or obstruction",
                    "transport from tensor lower-control to the complete query",
                ],
            }
        }
        (DimensionClass::CompositePrimePowerProduct, false) => DimensionStratificationReport {
            dimension,
            class,
            factors,
            status: DimensionAuthorityStatus::MissingFactorControl,
            guaranteed_basis_count: None,
            complete_basis_count,
            construction:
                "tensor product lower-control requires exact controls for every prime-power factor",
            boundary: "unsupported factor blocks local exact tensor lower-control replay",
            missing_obligations: vec![
                "local exact complete controls for every prime-power factor",
                "tensor-product replay over a declared common coefficient field",
            ],
        },
        (DimensionClass::Degenerate, _) => unreachable!("handled above"),
    }
}

/// The prime-power factorisation of `n`, each factor marked controlled when
/// its value is in `controlled`.
pub fn prime_power_factors(mut n: usize, controlled: &BTreeSet<usize>) -> Vec<PrimePowerFactor> {
    let mut factors = Vec::new();
    let mut p = 2;
    while p <= n / p {
        if n % p == 0 {
            let mut exponent = 0;
            let mut value = 1;
            while n % p == 0 {
                n /= p;
                exponent += 1;
                value *= p;
            }
            factors.push(build_factor(p, exponent, value, controlled));
        }
        p += if p == 2 { 1 } else { 2 };
    }
    if n > 1 {
        factors.push(build_factor(n, 1, n, controlled));
    }
    factors
}

fn build_factor(
    prime: usize,
    exponent: usize,
    value: usize,
    controlled: &BTreeSet<usize>,
) -> PrimePowerFactor {
    PrimePowerFactor {
        prime,
        exponent,
        value,
        complete_basis_count: value + 1,
        control_status: if controlled.contains(&value) {
            FactorControlStatus::ExactCompleteControlPresent
        } else {
            FactorControlStatus::MissingExactControl
        },
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/dimension_stratification.rs
// Claim: urn:core:crates_rs:core-quantum-physics:dimension-stratification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde86642d9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde86642d9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore86642d9 {
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
impl BoundaryErrore86642d9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore86642d9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore86642d9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde86642d9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore86642d9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore86642d9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore86642d9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore86642d9::ExceedsCapacity {
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

    /// The set the hard-coded list used to grant.
    fn former_list() -> BTreeSet<usize> {
        [2, 3, 4, 5, 7, 8, 9, 11, 13, 16, 25, 27, 32, 49]
            .into_iter()
            .collect()
    }

    #[test]
    fn the_computed_controls_reproduce_the_former_hard_coded_list() {
        assert_eq!(verified_prime_power_controls(), &former_list());
    }

    #[test]
    fn a_board_without_complete_projector_control_grants_no_dimension() {
        let mut reports = verify_current_finite_projector_controls();
        let d8 = reports
            .iter_mut()
            .find(|report| report.dimension == 8)
            .unwrap();
        assert_eq!(
            d8.status,
            FiniteProjectorControlStatus::CompleteProjectorMubVerified
        );
        d8.status = FiniteProjectorControlStatus::MissingHilbertTransport;
        assert!(!verified_char_two_dimensions(&reports).contains(&8));
    }

    #[test]
    fn prime_power_controls_are_complete_only_for_supported_dimensions() {
        let controlled = former_list();
        for dimension in [2, 3, 4, 5, 7, 8, 9, 11, 13, 16, 25, 27, 32, 49] {
            let report = stratify_dimension_with(dimension, &controlled);
            assert_eq!(report.class, DimensionClass::PrimePower);
            assert_eq!(
                report.status,
                DimensionAuthorityStatus::ExactCompleteControl
            );
            assert_eq!(report.guaranteed_basis_count, Some(dimension + 1));
        }
    }

    #[test]
    fn d6_and_d10_get_tensor_lower_bounds_not_complete_authority() {
        let controlled = former_list();
        for dimension in [6, 10] {
            let report = stratify_dimension_with(dimension, &controlled);
            assert_eq!(report.class, DimensionClass::CompositePrimePowerProduct);
            assert_eq!(
                report.status,
                DimensionAuthorityStatus::ExactTensorLowerControl
            );
            // min(2+1, 3+1) = 3 for d = 6, and min(2+1, 5+1) = 3 for d = 10.
            assert_eq!(report.guaranteed_basis_count, Some(3));
            assert_eq!(report.complete_basis_count, Some(dimension + 1));
            assert!(report
                .missing_obligations
                .iter()
                .any(|obligation| obligation.contains("complete")));
        }
    }

    #[test]
    fn unsupported_prime_power_remains_missing_local_control() {
        let report = stratify_dimension_with(81, &former_list());
        assert_eq!(report.class, DimensionClass::PrimePower);
        assert_eq!(
            report.status,
            DimensionAuthorityStatus::MissingFactorControl
        );
        assert_eq!(report.complete_basis_count, Some(82));
        assert!(report.guaranteed_basis_count.is_none());
    }

    #[test]
    fn unsupported_composite_factor_blocks_tensor_replay() {
        let report = stratify_dimension_with(34, &former_list());
        assert_eq!(report.class, DimensionClass::CompositePrimePowerProduct);
        assert_eq!(
            report.status,
            DimensionAuthorityStatus::MissingFactorControl
        );
        assert!(report.factors.iter().any(|factor| factor.value == 17
            && factor.control_status == FactorControlStatus::MissingExactControl));
    }

    #[test]
    fn a_control_that_stops_verifying_stops_granting_authority() {
        let mut controlled = former_list();
        controlled.remove(&3);
        let d3 = stratify_dimension_with(3, &controlled);
        assert_eq!(d3.status, DimensionAuthorityStatus::MissingFactorControl);
        // d = 6 = 2 * 3 loses its tensor lower control with it.
        let d6 = stratify_dimension_with(6, &controlled);
        assert_eq!(d6.status, DimensionAuthorityStatus::MissingFactorControl);
    }
}

#[cfg(test)]
mod l4_boundary_tests_e86642d9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde86642d9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde86642d9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde86642d9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde86642d9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde86642d9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore86642d9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore86642d9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
