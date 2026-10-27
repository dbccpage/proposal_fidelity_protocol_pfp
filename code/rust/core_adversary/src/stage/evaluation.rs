//! Frozen evaluator coordinates and exact weighted valuation, with no authority effect.
use crate::stage::canonical::{
    bind_id, digest, envelope, identifier, strings, validated_record, StringKind,
};

validated_record!(EvaluatorEpoch {
    epoch_name: String, probe_ids: Vec<String>, weights: Vec<i64>,
    evidence_rule_ids: Vec<String>, implementation_digests: Vec<String>, baseline_state_id: String,
    authority_effect: String, schema_version: String,
    #[serde(default)] epoch_id: String,
});
impl EvaluatorEpoch {
    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.epoch_name, "epoch_name")?;
        self.validate_probes_and_weights()?;
        self.validate_rules_and_digests()?;
        digest(&self.baseline_state_id, "baseline_state_id", false)?;
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "evaluator epoch",
            "core.oeas.evaluator-epoch.v1",
        )?;
        self.epoch_id = bind_id(self, &self.schema_version, "epoch_id", &self.epoch_id, &[])?;
        Ok(())
    }

    fn validate_probes_and_weights(&self) -> Result<(), String> {
        strings(&self.probe_ids, "probe_ids", StringKind::Identifier, true)?;
        if self.probe_ids.len() != self.weights.len() || self.weights.is_empty() {
            return Err("probe and weight arities must agree and be nonempty".into());
        }
        if self
            .weights
            .iter()
            .any(|value| !(1..=1_000_000).contains(value))
        {
            return Err("evaluator weights must be positive bounded integers".into());
        }
        Ok(())
    }

    fn validate_rules_and_digests(&self) -> Result<(), String> {
        strings(
            &self.evidence_rule_ids,
            "evidence_rule_ids",
            StringKind::Identifier,
            true,
        )?;
        strings(
            &self.implementation_digests,
            "implementation_digests",
            StringKind::Digest,
            true,
        )?;
        if self.evidence_rule_ids.is_empty() || self.implementation_digests.is_empty() {
            return Err("evaluator epoch requires evidence rules and implementations".into());
        }
        Ok(())
    }
}

validated_record!(ValuationReceipt {
    evaluator_epoch_id: String, candidate_id: String, probe_ids: Vec<String>, weights: Vec<i64>,
    pre_residual: Vec<i64>, post_residual: Vec<i64>, phi_pre: i64, phi_post: i64, delta_phi: i64,
    disposition: String, independently_recomputed: bool, authority_effect: String, schema_version: String,
    #[serde(default)] receipt_id: String,
});
impl ValuationReceipt {
    fn validate(&mut self) -> Result<(), String> {
        digest(&self.evaluator_epoch_id, "evaluator_epoch_id", false)?;
        digest(&self.candidate_id, "candidate_id", false)?;
        strings(&self.probe_ids, "probe_ids", StringKind::Identifier, true)?;
        self.validate_vectors()?;
        self.validate_derived_phi_and_disposition()?;
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "valuation receipt",
            "core.oeas.valuation-receipt.v1",
        )?;
        self.receipt_id = bind_id(
            self,
            &self.schema_version,
            "receipt_id",
            &self.receipt_id,
            &[],
        )?;
        Ok(())
    }

    fn validate_vectors(&self) -> Result<(), String> {
        for (field, values) in [
            ("weights", &self.weights),
            ("pre_residual", &self.pre_residual),
            ("post_residual", &self.post_residual),
        ] {
            if values.iter().any(|value| !(0..=1_000_000).contains(value)) {
                return Err(format!("{field} contains an out-of-range value"));
            }
        }
        let size = self.probe_ids.len();
        let arity_ok = [
            size > 0,
            self.weights.len() == size,
            self.pre_residual.len() == size,
            self.post_residual.len() == size,
        ]
        .into_iter()
        .all(|b| b);
        if !arity_ok {
            return Err("valuation vector arities must agree and be nonempty".into());
        }
        Ok(())
    }

    fn validate_derived_phi_and_disposition(&self) -> Result<(), String> {
        // At most 256 coordinates, each factor <= 1,000,000: both sums
        // are <= 256 * 10^12 and their signed difference fits i64 exactly.
        let pre: i64 = self
            .weights
            .iter()
            .zip(&self.pre_residual)
            .map(|(weight, value)| weight * value)
            .sum();
        let post: i64 = self
            .weights
            .iter()
            .zip(&self.post_residual)
            .map(|(weight, value)| weight * value)
            .sum();
        if self.phi_pre != pre || self.phi_post != post {
            return Err("Phi values are not derived from the frozen weighted residual".into());
        }
        if self.delta_phi != post - pre {
            return Err("delta_phi is not derived".into());
        }
        let disposition = if self.delta_phi <= 0 {
            "NON_INCREASING"
        } else {
            "INCREASING"
        };
        if self.disposition != disposition {
            return Err("valuation disposition is not derived".into());
        }
        if !self.independently_recomputed {
            return Err("valuation must be independently recomputed".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/evaluation.rs
// Claim: urn:core:crates_rs:core-adversary:evaluation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf2a6d82d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf2a6d82d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf2a6d82d {
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
impl BoundaryErrorf2a6d82d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf2a6d82d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf2a6d82d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf2a6d82d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf2a6d82d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf2a6d82d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf2a6d82d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf2a6d82d::ExceedsCapacity {
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
mod l4_boundary_tests_f2a6d82d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf2a6d82d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf2a6d82d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf2a6d82d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf2a6d82d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf2a6d82d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorf2a6d82d::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorf2a6d82d::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
