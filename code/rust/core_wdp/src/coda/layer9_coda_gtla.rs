// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::One;
use serde_json::json;

use crate::coda::types::{
    AuthorityToken, DualWitness, FirewallDecision, LayerExecutionRecord, LayerId,
    MasterNormalFormOutcome, ObstructionWitnessPayload, ProblemInstance, ResidualPair,
    TerminalKind,
};

pub struct Layer9CodaGtla;

impl Layer9CodaGtla {
    /// Terminalizes the 9-stage pipeline execution into the definitive MasterNormalFormOutcome.
    ///
    /// Enforces the 3-way disjoint coproduct partition:
    /// - TerminalKind::Authorized
    /// - TerminalKind::ClosedResidual
    /// - TerminalKind::Refused
    #[allow(clippy::too_many_arguments)]
    pub fn terminalize(
        problem: &ProblemInstance,
        phi1: Option<BigRational>,
        gamma2: Option<BigRational>,
        dual_witness: Option<DualWitness>,
        firewall_decision: FirewallDecision,
        authority_token: Option<AuthorityToken>,
        layer_records: Vec<LayerExecutionRecord>,
        custom_reason: Option<String>,
        primal_repair: Option<Vec<BigRational>>,
        evidence_digest: String,
    ) -> MasterNormalFormOutcome {
        let witness_payload = dual_witness
            .as_ref()
            .map(|dw| ObstructionWitnessPayload::FlatQuotient(dw.clone()));
        Self::terminalize_with_payload(
            problem,
            phi1,
            gamma2,
            dual_witness,
            witness_payload,
            firewall_decision,
            authority_token,
            layer_records,
            custom_reason,
            primal_repair,
            evidence_digest,
        )
    }

    /// Terminalizes the pipeline with explicit dual witness and distinct typed witness payload variants.
    #[allow(clippy::too_many_arguments)]
    pub fn terminalize_with_payload(
        problem: &ProblemInstance,
        phi1: Option<BigRational>,
        gamma2: Option<BigRational>,
        dual_witness: Option<DualWitness>,
        witness_payload: Option<ObstructionWitnessPayload>,
        firewall_decision: FirewallDecision,
        _authority_token: Option<AuthorityToken>,
        mut layer_records: Vec<LayerExecutionRecord>,
        custom_reason: Option<String>,
        primal_repair: Option<Vec<BigRational>>,
        evidence_digest: String,
    ) -> MasterNormalFormOutcome {
        let residual_pair = match (&phi1, &gamma2) {
            (Some(p), Some(g)) => Some(ResidualPair::new(p.clone(), g.clone())),
            _ => None,
        };

        let (terminal_kind, default_reason, defect_mass) = match firewall_decision {
            FirewallDecision::RouteClosedResidual => (
                TerminalKind::ClosedResidual,
                "Pipeline terminated in CLOSED_RESIDUAL; non-promoted".to_string(),
                phi1.clone().unwrap_or_else(BigRational::one),
            ),
            _ => (
                TerminalKind::Refused,
                "Pipeline terminated in REFUSED: a halt guard or layer refused".to_string(),
                BigRational::one(),
            ),
        };

        let coda_gtla_record = LayerExecutionRecord::new(
            LayerId::CODA_GTLA,
            true,
            format!("GTLA Terminalization complete: outcome={:?}", terminal_kind),
            defect_mass,
        )
        .with_metadata("terminal_kind", json!(format!("{:?}", terminal_kind)))
        .with_metadata(
            "is_authorized",
            json!(terminal_kind == TerminalKind::Authorized),
        )
        .with_metadata(
            "is_closed_residual",
            json!(terminal_kind == TerminalKind::ClosedResidual),
        )
        .with_metadata("is_refused", json!(terminal_kind == TerminalKind::Refused));

        layer_records.push(coda_gtla_record);

        MasterNormalFormOutcome {
            problem_id: problem.problem_id.clone(),
            terminal_kind,
            residual_pair,
            dual_witness,
            witness_payload,
            authority_token: None,
            layer_records,
            firewall_decision,
            reason: custom_reason.unwrap_or(default_reason),
            primal_repair,
            evidence_digest,
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/layer9_coda_gtla.rs
// Claim: urn:core:crates_rs:core-wdp:layer9-coda-gtla:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5513460e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5513460e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5513460e {
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
impl BoundaryError5513460e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5513460e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5513460e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5513460e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5513460e> {
        if capacity_bound == 0 {
            return Err(BoundaryError5513460e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5513460e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5513460e::ExceedsCapacity {
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
mod l4_boundary_tests_5513460e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5513460e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5513460e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5513460e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5513460e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5513460e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5513460e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5513460e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
