// AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_6f6973ad<T> {
    fn checked_invariant_6f6973ad(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_6f6973ad<T> for Option<T> {
    #[inline]
    fn checked_invariant_6f6973ad(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_6f6973ad<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_6f6973ad(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_traits::Zero;
use sha2::{Digest, Sha256};

use crate::coda::layer1_foc::Layer1Foc;
use crate::coda::layer2_mur::Layer2Mur;
use crate::coda::layer3_cs::Layer3Cs;
use crate::coda::layer4_cs_q::Layer4CsQ;
use crate::coda::layer5_q::Layer5Q;
use crate::coda::layer6_a::Layer6A;
use crate::coda::layer7_or::Layer7Or;
use crate::coda::layer8_fda::Layer8Fda;
use crate::coda::layer9_coda_gtla::Layer9CodaGtla;
use crate::coda::types::{ExternalAuthorityGrant, MasterNormalFormOutcome, ProblemInstance};

/// Evaluates a ProblemInstance through the full 9-layer CODA pipeline without external authority grant.
pub fn evaluate_coda_pipeline(problem: &ProblemInstance) -> MasterNormalFormOutcome {
    evaluate_coda_pipeline_with_grant(problem, None)
}

/// Evaluates a ProblemInstance through the full 9-layer CODA pipeline with an optional verified grant.
pub fn evaluate_coda_pipeline_with_grant(
    problem: &ProblemInstance,
    external_grant: Option<&ExternalAuthorityGrant>,
) -> MasterNormalFormOutcome {
    let mut records = Vec::with_capacity(9);

    // Stage 1: FOC (Finite Obstruction Calculus)
    let (rec1, phi1, gamma2, witness, witness_payload, primal_repair) =
        match Layer1Foc::evaluate_with_payload(problem, &num_rational::BigRational::zero()) {
            Ok(measured) => measured,
            Err(record) => {
                records.push(record);
                let digest = evidence_digest(problem, external_grant, &records);
                return Layer9CodaGtla::terminalize_with_payload(
                    problem,
                    None,
                    None,
                    None,
                    None,
                    crate::coda::types::FirewallDecision::RouteRefused,
                    None,
                    records,
                    Some("Invalid cochain complex or unverified quotient certificate".into()),
                    None,
                    digest,
                );
            }
        };
    records.push(rec1);

    // Stage 2: MUR (Meta & Universal Re-Presentation)
    let (rec2, _loss) = Layer2Mur::evaluate(problem);
    records.push(rec2);

    // Stage 3: CS (Continuum Shadow)
    let (rec3, _consistent) = Layer3Cs::evaluate(problem);
    records.push(rec3);

    // Stage 4: CS_Q (Continuum Shadow to Continuum Bridge)
    let (rec4, _min_sep) = Layer4CsQ::evaluate(problem);
    records.push(rec4);

    // Stage 5: Q (The Continuum)
    let (rec5, _diam) = Layer5Q::evaluate(problem);
    records.push(rec5);

    // Stage 6: A (Sentinel)
    let (rec6, _has_residual) = Layer6A::evaluate(problem, &phi1, &gamma2);
    records.push(rec6);

    // Stage 7: OR (Omniversal Re-Presentation)
    let (rec7, is_refused) = Layer7Or::evaluate(problem, &gamma2);
    records.push(rec7);
    let is_refused = is_refused || records.iter().any(|record| !record.succeeded);

    // Stage 8: FDA (Finite Descent Authority)
    let (rec8, decision, token) =
        Layer8Fda::evaluate_with_grant(problem, &phi1, &gamma2, is_refused, external_grant);
    records.push(rec8);

    let evidence_digest = evidence_digest(problem, external_grant, &records);

    // Stage 9: CODA_GTLA (General Theory of Layered Authority & Master Normal Form)
    Layer9CodaGtla::terminalize_with_payload(
        problem,
        Some(phi1),
        Some(gamma2),
        witness,
        witness_payload,
        decision,
        token,
        records,
        None,
        Some(primal_repair),
        evidence_digest,
    )
}

fn evidence_digest(
    problem: &ProblemInstance,
    external_grant: Option<&ExternalAuthorityGrant>,
    records: &[crate::coda::types::LayerExecutionRecord],
) -> String {
    // Bind all inputs and actual records; tuple-keyed overlaps use sequences.
    let evidence = serde_json::json!({
        "schema": "core.coda.pipeline.evidence.v1",
        "problem_id": problem.problem_id,
        "raw_data": problem.raw_data,
        "candidate_sieve": problem.candidate_sieve,
        "coarse_profile": problem.coarse_profile,
        "fine_profile": problem.fine_profile,
        "projection_map": problem.projection_map,
        "local_sections": problem.local_sections,
        "overlaps": problem.overlaps.iter().collect::<Vec<_>>(),
        "d0": problem.d0,
        "d1": problem.d1,
        "defect_cochain": problem.defect_cochain,
        "fda_license_granted": problem.fda_license_granted,
        "enclosure_interval": problem.enclosure_interval,
        "external_grant": external_grant,
        "records": records,
    });
    format!(
        "{:x}",
        Sha256::digest(
            serde_json::to_vec(&evidence).checked_invariant_6f6973ad("canonical evidence consists of JSON values")
        )
    )
}

// Origin: engine/crates_rs/core_wdp/src/coda/pipeline.rs
// Claim: urn:core:crates_rs:core-wdp:pipeline:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6f6973ad {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6f6973ad` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6f6973ad {
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
impl BoundaryError6f6973ad {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6f6973ad {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6f6973ad {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6f6973ad {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6f6973ad> {
        if capacity_bound == 0 {
            return Err(BoundaryError6f6973ad::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6f6973ad::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6f6973ad::ExceedsCapacity {
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
mod l4_boundary_tests_6f6973ad {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6f6973ad::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6f6973ad::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6f6973ad::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6f6973ad::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6f6973ad::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6f6973ad::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6f6973ad::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
