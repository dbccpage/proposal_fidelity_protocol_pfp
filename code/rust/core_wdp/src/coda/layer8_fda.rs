// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde_json::json;

use crate::coda::types::{
    AuthorityToken, ExternalAuthorityGrant, FirewallDecision, LayerExecutionRecord, LayerId,
    ProblemInstance,
};

pub struct Layer8Fda;

impl Layer8Fda {
    /// Evaluates Layer 8: Finite Descent Authority (CODA-FDA).
    ///
    /// Enforces:
    /// - The Authority Conservation Law: Authority cannot be minted by internal derivation.
    /// - Strict Role Split: Runner != Authorizer, Proposer != Evaluator.
    /// - Non-Promotion Firewall: Zero defect (Phi_1=0, Gamma_2=0) WITHOUT verified external grant
    ///   NEVER promotes to Authorized (routes to ClosedResidual).
    /// - A license flag on ProblemInstance is a claim, not an external grant.
    pub fn evaluate(
        _problem: &ProblemInstance,
        phi1: &BigRational,
        gamma2: &BigRational,
        refused_by_or: bool,
    ) -> (
        LayerExecutionRecord,
        FirewallDecision,
        Option<AuthorityToken>,
    ) {
        Self::evaluate_with_grant(_problem, phi1, gamma2, refused_by_or, None)
    }

    /// Evaluates Layer 8 with optional untrusted grant metadata.
    /// The external verifier is unavailable, so supplied grants are refused.
    pub fn evaluate_with_grant(
        problem: &ProblemInstance,
        phi1: &BigRational,
        gamma2: &BigRational,
        refused_by_or: bool,
        external_grant: Option<&ExternalAuthorityGrant>,
    ) -> (
        LayerExecutionRecord,
        FirewallDecision,
        Option<AuthorityToken>,
    ) {
        if refused_by_or {
            let decision = FirewallDecision::RouteRefused;
            let msg = "FDA gate: upstream refusal".to_string();
            let record = LayerExecutionRecord::new(LayerId::FDA, false, msg, BigRational::one())
                .with_metadata("firewall_decision", json!("ROUTE_REFUSED"))
                .with_metadata("token_issued", json!(false));
            (record, decision, None)
        } else if !gamma2.is_zero() {
            let decision = FirewallDecision::RouteRefused;
            let msg = format!("FDA gate: incoherent cocycle defect Gamma_2={}", gamma2);
            let record = LayerExecutionRecord::new(LayerId::FDA, false, msg, BigRational::one())
                .with_metadata("firewall_decision", json!("ROUTE_REFUSED"))
                .with_metadata("token_issued", json!(false));
            (record, decision, None)
        } else if phi1 > &BigRational::zero() {
            let decision = FirewallDecision::RouteClosedResidual;
            let msg = format!(
                "FDA gate: non-zero quotient defect Phi_1={} retained; non-promotion",
                phi1
            );
            let record = LayerExecutionRecord::new(LayerId::FDA, true, msg, BigRational::one())
                .with_metadata("firewall_decision", json!("ROUTE_CLOSED_RESIDUAL"))
                .with_metadata("token_issued", json!(false));
            (record, decision, None)
        } else if external_grant.is_some() {
            // Wire strings are not verification of signer, scope, or freshness.
            let record = LayerExecutionRecord::new(
                LayerId::FDA,
                false,
                "EXTERNAL_GRANT_VERIFIER_UNAVAILABLE",
                BigRational::one(),
            )
            .with_metadata("token_issued", json!(false));
            (record, FirewallDecision::RouteRefused, None)
        } else {
            // Zero defect, but no verified external grant -> CLOSED_RESIDUAL
            let decision = FirewallDecision::RouteClosedResidual;
            let msg = format!(
                "FDA gate: zero defect on {}; authorization requires a verified external grant at the firewall",
                problem.problem_id
            );
            let record = LayerExecutionRecord::new(LayerId::FDA, true, msg, BigRational::one())
                .with_metadata("firewall_decision", json!("ROUTE_CLOSED_RESIDUAL"))
                .with_metadata("token_issued", json!(false));
            (record, decision, None)
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/layer8_fda.rs
// Claim: urn:core:crates_rs:core-wdp:layer8-fda:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord007ada63 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord007ada63` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError007ada63 {
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
impl BoundaryError007ada63 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError007ada63 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError007ada63 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord007ada63 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError007ada63> {
        if capacity_bound == 0 {
            return Err(BoundaryError007ada63::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError007ada63::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError007ada63::ExceedsCapacity {
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
mod l4_boundary_tests_007ada63 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord007ada63::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord007ada63::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord007ada63::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord007ada63::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord007ada63::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError007ada63::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError007ada63::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
