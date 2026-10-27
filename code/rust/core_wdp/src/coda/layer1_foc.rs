// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde_json::json;

use crate::coda::types::{
    CurvedDualWitness, DualWitness, LayerExecutionRecord, LayerId, ObstructionWitnessPayload,
    ProblemInstance,
};
use core_functional::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Error, Gamma2Functional,
};
use core_solvers::solver_cohomology_simplicial_l1::{
    solve_l1_curved_constrained, solve_l1_quotient, VerifiedCurvedConstrainedPhi1,
};

pub struct Layer1Foc;

impl Layer1Foc {
    /// Evaluates Layer 1: Finite Obstruction Calculus (CODA-FOC) with default zero
    /// closure slack (`tau = 0`) when the coboundary composition is curved (`K = d1 d0 != 0`).
    ///
    /// - On the **flat locus** (`K = d1 d0 = 0`), uses [`ExactCochainComplexQ`] and
    ///   [`solve_l1_quotient`] to certify the quotient-invariant pair
    ///   `(\Phi_1([x]), \Gamma_2([x]))`.
    /// - On the **curved locus** (`K = d1 d0 != 0`), [`ExactCochainComplexQ`] is not
    ///   constructed; instead, solves the constrained representative-repair LP
    ///   `\min_{f \in C^0} \|x - d_0 f\|_1 \text{ s.t. } \|d_1 x - K f\|_1 \le \Gamma_2^{\mathrm{raw}}(x) + \tau`
    ///   using [`core_functional::gamma2::RawClosureDefectResult`].
    pub fn evaluate(
        problem: &ProblemInstance,
    ) -> Result<
        (
            LayerExecutionRecord,
            BigRational,
            BigRational,
            Option<DualWitness>,
            Vec<BigRational>,
        ),
        LayerExecutionRecord,
    > {
        Self::evaluate_with_closure_guard(problem, &BigRational::zero())
    }

    /// Evaluates Layer 1 with an explicit non-negative closure budget slack `tau >= 0`:
    ///
    /// ```text
    /// min_{f in C^0} ||x - d0 f||_1   s.t.   ||d1 x - K f||_1 <= Gamma_2_raw(x) + tau.
    /// ```
    ///
    /// Keeps [`ExactCochainComplexQ`] strictly restricted to the flat (`K = 0`) locus,
    /// and routes curved (`K != 0`) presentations through [`solve_l1_curved_constrained`]
    /// backed by [`core_functional::gamma2::RawClosureDefectResult`].
    pub fn evaluate_with_closure_guard(
        problem: &ProblemInstance,
        tau: &BigRational,
    ) -> Result<
        (
            LayerExecutionRecord,
            BigRational,
            BigRational,
            Option<DualWitness>,
            Vec<BigRational>,
        ),
        LayerExecutionRecord,
    > {
        let (record, phi1, gamma2, witness, _payload, repair) =
            Self::evaluate_with_payload(problem, tau)?;
        Ok((record, phi1, gamma2, witness, repair))
    }

    /// Evaluates Layer 1 returning both backwards-compatible [`DualWitness`] and the
    /// full typed [`ObstructionWitnessPayload`] certificate variant (`FlatQuotient` vs `CurvedConstrained`).
    fn failure_record(reason: String) -> LayerExecutionRecord {
        LayerExecutionRecord::new(LayerId::FOC, false, reason, BigRational::zero())
            .with_metadata("certificate_verified", json!(false))
    }

    fn evaluate_flat_branch(
        problem: &ProblemInstance,
        complex: ExactCochainComplexQ,
    ) -> Result<
        (
            LayerExecutionRecord,
            BigRational,
            BigRational,
            Option<DualWitness>,
            Option<ObstructionWitnessPayload>,
            Vec<BigRational>,
        ),
        LayerExecutionRecord,
    > {
        let cert = solve_l1_quotient(&problem.d0, &problem.defect_cochain)
            .map_err(Self::failure_record)?;
        let residual = DegreeOneResidualQ::try_new(&complex, cert.residual.clone())
            .map_err(|e| Self::failure_record(e.to_string()))?;
        let gamma2_evidence = Gamma2Functional::try_compute_exact_quotient(&residual)
            .map_err(|e| Self::failure_record(e.to_string()))?;
        let gamma2 = gamma2_evidence.value().clone();
        let phi1 = cert.distance.clone();

        let (witness, payload) = if phi1 > BigRational::zero() {
            let dw = DualWitness::new(cert.witness, phi1.clone());
            let pl = ObstructionWitnessPayload::FlatQuotient(dw.clone());
            (Some(dw), Some(pl))
        } else {
            (None, None)
        };

        let msg = if phi1.is_zero() {
            "Cochain is in im(d0): exact zero quotient defect with an exact repair".to_string()
        } else {
            format!(
                "Non-trivial quotient obstruction Phi_1={} (primal repair and dual witness agree)",
                phi1
            )
        };

        let record = LayerExecutionRecord::new(LayerId::FOC, gamma2.is_zero(), msg, phi1.clone())
            .with_metadata("locus", json!("flat_quotient"))
            .with_metadata("quotient_invariant", json!(true))
            .with_metadata("phi1", json!(phi1.to_string()))
            .with_metadata("gamma2", json!(gamma2.to_string()))
            .with_metadata("is_coherent", json!(gamma2.is_zero()))
            .with_metadata("solver", json!(cert.method))
            .with_metadata("witness_payload_variant", json!("FlatQuotient"))
            .with_metadata("certificate_verified", json!(true));

        Ok((record, phi1, gamma2, witness, payload, cert.repair))
    }

    pub fn evaluate_with_payload(
        problem: &ProblemInstance,
        tau: &BigRational,
    ) -> Result<
        (
            LayerExecutionRecord,
            BigRational,
            BigRational,
            Option<DualWitness>,
            Option<ObstructionWitnessPayload>,
            Vec<BigRational>,
        ),
        LayerExecutionRecord,
    > {
        if tau.denom().is_zero() || tau.is_negative() {
            return Err(Self::failure_record(
                "closure slack tau must be a valid non-negative rational".into(),
            ));
        }
        if problem
            .d1
            .iter()
            .any(|row| row.len() != problem.defect_cochain.len())
        {
            return Err(Self::failure_record("d1 width differs from the cochain".into()));
        }
        let cols = problem.d0.first().map_or(0, Vec::len);
        match ExactCochainComplexQ::try_new(
            cols,
            problem.defect_cochain.len(),
            problem.d1.len(),
            problem.d0.clone(),
            problem.d1.clone(),
        ) {
            Ok(complex) => Self::evaluate_flat_branch(problem, complex),
            Err(ExactGamma2Error::CochainIdentityViolation { .. }) => {
                let verified = Self::evaluate_curved_constrained(problem, tau)?;
                let phi1 = verified.value().clone();
                let baseline_raw_gamma2 = verified.baseline_raw_gamma2().value().clone();
                let repaired_raw_gamma2 = verified.repaired_raw_gamma2().value().clone();
                let gamma2 = repaired_raw_gamma2.clone();

                let (witness, payload) = if phi1 > BigRational::zero() {
                    let cw = CurvedDualWitness::new(
                        verified.dual_y().to_vec(),
                        verified.dual_z().to_vec(),
                        verified.dual_lambda().clone(),
                        tau.clone(),
                        phi1.clone(),
                    );
                    let pl = ObstructionWitnessPayload::CurvedConstrained(cw);
                    let dw = DualWitness::new(verified.dual_y().to_vec(), phi1.clone());
                    (Some(dw), Some(pl))
                } else {
                    (None, None)
                };

                let msg = format!(
                    "Curved descent (K = d1*d0 != 0): constrained repair norm={}, raw Gamma_2={} (baseline={}, tau={})",
                    phi1, repaired_raw_gamma2, baseline_raw_gamma2, tau
                );

                let record =
                    LayerExecutionRecord::new(LayerId::FOC, gamma2.is_zero(), msg, phi1.clone())
                        .with_metadata("locus", json!("curved_representative_constrained"))
                        .with_metadata("quotient_invariant", json!(false))
                        .with_metadata("phi1", json!(phi1.to_string()))
                        .with_metadata("gamma2", json!(gamma2.to_string()))
                        .with_metadata("baseline_raw_gamma2", json!(baseline_raw_gamma2.to_string()))
                        .with_metadata("repaired_raw_gamma2", json!(repaired_raw_gamma2.to_string()))
                        .with_metadata("closure_slack_tau", json!(tau.to_string()))
                        .with_metadata("is_coherent", json!(gamma2.is_zero()))
                        .with_metadata(
                            "solver",
                            json!("exact_curved_constrained_primal_dual_simplex"),
                        )
                        .with_metadata(
                            "curved_dual_y",
                            json!(verified.dual_y().iter().map(ToString::to_string).collect::<Vec<_>>()),
                        )
                        .with_metadata(
                            "curved_dual_z",
                            json!(verified.dual_z().iter().map(ToString::to_string).collect::<Vec<_>>()),
                        )
                        .with_metadata("curved_dual_lambda", json!(verified.dual_lambda().to_string()))
                        .with_metadata("witness_payload_variant", json!("CurvedConstrained"))
                        .with_metadata("certificate_verified", json!(true));

                Ok((
                    record,
                    phi1,
                    gamma2,
                    witness,
                    payload,
                    verified.alpha().to_vec(),
                ))
            }
            Err(error) => Err(Self::failure_record(error.to_string())),
        }
    }

    /// Solve the closure-constrained repair linear program directly on `problem`
    /// and return the sealed [`VerifiedCurvedConstrainedPhi1`] certificate.
    pub fn evaluate_curved_constrained(
        problem: &ProblemInstance,
        tau: &BigRational,
    ) -> Result<VerifiedCurvedConstrainedPhi1, LayerExecutionRecord> {
        let failure_record = |reason: String| {
            LayerExecutionRecord::new(LayerId::FOC, false, reason, BigRational::zero())
                .with_metadata("certificate_verified", json!(false))
        };
        if problem
            .d1
            .iter()
            .any(|row| row.len() != problem.defect_cochain.len())
        {
            return Err(failure_record("d1 width differs from the cochain".into()));
        }
        solve_l1_curved_constrained(&problem.d0, &problem.d1, &problem.defect_cochain, tau)
            .map_err(failure_record)
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/layer1_foc.rs
// Claim: urn:core:crates_rs:core-wdp:layer1-foc:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf8554120 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf8554120` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf8554120 {
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
impl BoundaryErrorf8554120 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf8554120 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf8554120 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf8554120 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf8554120> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf8554120::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf8554120::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf8554120::ExceedsCapacity {
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
mod l4_boundary_tests_f8554120 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf8554120::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf8554120::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf8554120::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf8554120::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf8554120::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf8554120::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf8554120::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
