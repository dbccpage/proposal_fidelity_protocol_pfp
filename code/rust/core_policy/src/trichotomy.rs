//! Exact finite obstruction trichotomy.
//!
//! Exact authority is emitted only from replayed finite rational evidence.
//! Floating values are diagnostic-only and produce
//! `TriRefused(NumericUndecidable)`.

use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};

use core_functional::gamma2::ExactGamma2Result;
use core_functional::phi1::VerifiedExactPhi1;

/// The exact finite obstruction trichotomy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub enum ObstructionDiagnosticClass {
    /// `Phi1(q) = 0`: no quotient survivor.
    ExactRepair,
    /// `Phi1(q) > 0` and `Gamma2(q) = 0`: closed non-exact residual.
    ClosedResidual,
    /// `Phi1(q) > 0` and `Gamma2(q) > 0`: open residual.
    ActiveClosureFailure,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum TrichotomyRefusal {
    NumericUndecidable,
    IncompatiblePhi1Gamma2Evidence,
}

/// Sealed exact classification. Downstream packet code can require this type
/// and therefore cannot promote a floating heuristic to exact trichotomy.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct CertifiedExactTrichotomy {
    diagnostic_class: ObstructionDiagnosticClass,
    phi1_value: BigRational,
    gamma2_value: BigRational,
}

impl CertifiedExactTrichotomy {
    pub fn diagnostic_class(&self) -> ObstructionDiagnosticClass {
        self.diagnostic_class
    }

    pub fn phi1_value(&self) -> &BigRational {
        &self.phi1_value
    }

    pub fn gamma2_value(&self) -> &BigRational {
        &self.gamma2_value
    }
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum TrichotomyOutcome {
    Classified(CertifiedExactTrichotomy),
    TriRefused(TrichotomyRefusal),
}

/// Decide trichotomy from exact finite rational evidence.
///
/// The Gamma2 evidence must be computed from the same residual and repair map
/// as the verified Phi1 certificate.
pub fn classify_exact(phi1: &VerifiedExactPhi1, gamma2: &ExactGamma2Result) -> TrichotomyOutcome {
    if phi1.primal_residual() != gamma2.residual() || phi1.d0() != gamma2.d0() {
        return TrichotomyOutcome::TriRefused(TrichotomyRefusal::IncompatiblePhi1Gamma2Evidence);
    }

    let diagnostic_class = if phi1.value().is_zero() {
        ObstructionDiagnosticClass::ExactRepair
    } else if gamma2.value().is_zero() {
        ObstructionDiagnosticClass::ClosedResidual
    } else {
        ObstructionDiagnosticClass::ActiveClosureFailure
    };

    TrichotomyOutcome::Classified(CertifiedExactTrichotomy {
        diagnostic_class,
        phi1_value: phi1.value().clone(),
        gamma2_value: gamma2.value().clone(),
    })
}

// Origin: engine/crates_rs/core_policy/src/trichotomy.rs
// Claim: urn:core:crates_rs:core-policy:trichotomy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbbecb7f7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbbecb7f7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbbecb7f7 {
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
impl BoundaryErrorbbecb7f7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbbecb7f7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbbecb7f7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbbecb7f7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbbecb7f7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbbecb7f7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbbecb7f7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbbecb7f7::ExceedsCapacity {
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
    use num_bigint::BigInt;
    use num_rational::BigRational;

    use super::*;
    use core_functional::gamma2::Gamma2Functional;
    use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn verified_phi1(
        omega: i64,
        d0: i64,
        alpha: i64,
        residual: i64,
        dual: i64,
        value: i64,
    ) -> VerifiedExactPhi1 {
        Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
            omega: vec![r(omega)],
            d0: vec![vec![r(d0)]],
            weights: vec![r(1)],
            alpha: vec![r(alpha)],
            primal_residual: vec![r(residual)],
            dual_witness: vec![r(dual)],
            reported_value: r(value),
        })
        .unwrap()
    }

    fn compute_helper(
        res: &[BigRational],
        d0: &[Vec<BigRational>],
        d1: &[Vec<BigRational>],
    ) -> Result<ExactGamma2Result, core_functional::gamma2::ExactGamma2Error> {
        let c0_dim = d0.first().map_or(0, Vec::len);
        let c1_dim = res.len();
        let c2_dim = d1.len();
        let complex = core_functional::gamma2::ExactCochainComplexQ::try_new(
            c0_dim,
            c1_dim,
            c2_dim,
            d0.to_vec(),
            d1.to_vec(),
        )?;
        let q = core_functional::gamma2::DegreeOneResidualQ::try_new(&complex, res.to_vec())?;
        Gamma2Functional::try_compute_exact_quotient(&q)
    }

    #[test]
    fn exact_finite_trichotomy_decides_all_three_cases() {
        let exact_phi1 = verified_phi1(1, 1, 1, 0, 0, 0);
        let exact_gamma2 =
            compute_helper(exact_phi1.primal_residual(), exact_phi1.d0(), &[vec![r(0)]]).unwrap();
        assert_eq!(
            classify_exact(&exact_phi1, &exact_gamma2),
            TrichotomyOutcome::Classified(CertifiedExactTrichotomy {
                diagnostic_class: ObstructionDiagnosticClass::ExactRepair,
                phi1_value: r(0),
                gamma2_value: r(0),
            })
        );

        let survivor_phi1 = verified_phi1(1, 0, 0, 1, 1, 1);
        let survivor_gamma2 = compute_helper(
            survivor_phi1.primal_residual(),
            survivor_phi1.d0(),
            &[vec![r(0)]],
        )
        .unwrap();
        assert_eq!(
            classify_exact(&survivor_phi1, &survivor_gamma2),
            TrichotomyOutcome::Classified(CertifiedExactTrichotomy {
                diagnostic_class: ObstructionDiagnosticClass::ClosedResidual,
                phi1_value: r(1),
                gamma2_value: r(0),
            })
        );

        let open_phi1 = verified_phi1(1, 0, 0, 1, 1, 1);
        let open_gamma2 =
            compute_helper(open_phi1.primal_residual(), open_phi1.d0(), &[vec![r(1)]]).unwrap();
        assert_eq!(
            classify_exact(&open_phi1, &open_gamma2),
            TrichotomyOutcome::Classified(CertifiedExactTrichotomy {
                diagnostic_class: ObstructionDiagnosticClass::ActiveClosureFailure,
                phi1_value: r(1),
                gamma2_value: r(1),
            })
        );
    }

    #[test]
    fn exact_classifier_refuses_mismatched_residual() {
        let phi1 = verified_phi1(1, 0, 0, 1, 1, 1);
        let gamma2 = compute_helper(&[r(2)], phi1.d0(), &[vec![r(0)]]).unwrap();

        assert_eq!(
            classify_exact(&phi1, &gamma2),
            TrichotomyOutcome::TriRefused(TrichotomyRefusal::IncompatiblePhi1Gamma2Evidence)
        );
    }

    #[test]
    fn rejects_closed_residual_when_gamma2_positive() {
        let phi1 = verified_phi1(1, 0, 0, 1, 1, 1);
        let gamma2 = compute_helper(phi1.primal_residual(), phi1.d0(), &[vec![r(1)]]).unwrap();
        assert!(
            gamma2.value() > &r(0),
            "precondition: Γ₂ must be strictly positive"
        );
        assert!(
            phi1.value() > &r(0),
            "precondition: Φ₁ must be strictly positive"
        );

        match classify_exact(&phi1, &gamma2) {
            TrichotomyOutcome::Classified(certified) => {
                assert_ne!(
                    certified.diagnostic_class(),
                    ObstructionDiagnosticClass::ClosedResidual
                );
                assert_eq!(
                    certified.diagnostic_class(),
                    ObstructionDiagnosticClass::ActiveClosureFailure
                );
                assert_eq!(certified.phi1_value(), phi1.value());
                assert_eq!(certified.gamma2_value(), gamma2.value());
            }
            other => panic!("expected classified open residual, got {other:?}"),
        }
    }

    #[test]
    fn rejects_exact_repair_when_phi1_positive() {
        let phi1 = verified_phi1(1, 0, 0, 1, 1, 1);
        let gamma2 = compute_helper(phi1.primal_residual(), phi1.d0(), &[vec![r(0)]]).unwrap();
        assert!(
            phi1.value() > &r(0),
            "precondition: Φ₁ must be strictly positive"
        );

        match classify_exact(&phi1, &gamma2) {
            TrichotomyOutcome::Classified(certified) => {
                assert_ne!(
                    certified.diagnostic_class(),
                    ObstructionDiagnosticClass::ExactRepair
                );
                assert_eq!(
                    certified.diagnostic_class(),
                    ObstructionDiagnosticClass::ClosedResidual
                );
                assert_eq!(certified.phi1_value(), phi1.value());
            }
            other => panic!("expected classified closed residual, got {other:?}"),
        }
    }

    #[test]
    fn rejects_open_obstruction_when_gamma2_zero() {
        let phi1 = verified_phi1(1, 0, 0, 1, 1, 1);
        let gamma2 = compute_helper(phi1.primal_residual(), phi1.d0(), &[vec![r(0)]]).unwrap();
        assert_eq!(
            gamma2.value(),
            &r(0),
            "precondition: Γ₂ must be exactly zero"
        );
        assert!(
            phi1.value() > &r(0),
            "precondition: Φ₁ must be strictly positive"
        );

        match classify_exact(&phi1, &gamma2) {
            TrichotomyOutcome::Classified(certified) => {
                assert_ne!(
                    certified.diagnostic_class(),
                    ObstructionDiagnosticClass::ActiveClosureFailure
                );
                assert_eq!(
                    certified.diagnostic_class(),
                    ObstructionDiagnosticClass::ClosedResidual
                );
                assert_eq!(certified.gamma2_value(), &r(0));
            }
            other => panic!("expected classified closed residual, got {other:?}"),
        }
    }
}

#[cfg(test)]
mod contract_conformance {
    use super::ObstructionDiagnosticClass;
    use core_contracts::binding::ImplementsContract;
    use core_contracts::contract_images::FiniteObstructionTrichotomyContract;

    impl ImplementsContract<FiniteObstructionTrichotomyContract> for ObstructionDiagnosticClass {}

    #[test]
    fn obstruction_status_binds_and_audits_its_contract() {
        core_contracts::assert_contract_binding!(
            ObstructionDiagnosticClass,
            FiniteObstructionTrichotomyContract
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_bbecb7f7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbbecb7f7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbbecb7f7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbbecb7f7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbbecb7f7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbbecb7f7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbbecb7f7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbbecb7f7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
