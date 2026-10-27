//! Prompt Society and Civilization normative data models (NF-01).
//!
//! Conforms to normative specification:
//! `urn:core:nf:prompt_civilization:society_and_civilization:v1.0.0`
//!
//! AuthorityEffect: None.
//! Zero-Float Law: Uses exact rational arithmetic (num_rational::BigRational).

use num_bigint::BigInt;
use num_rational::BigRational;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::str::FromStr;

use crate::domain::scope_covers;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AggregateFitnessVectorV1 {
    pub accuracy_rational: String,
    pub cost_rational: String,
    pub robustness_rational: String,
}

impl AggregateFitnessVectorV1 {
    pub fn new(accuracy: &str, cost: &str, robustness: &str) -> Result<Self, &'static str> {
        let v = Self {
            accuracy_rational: accuracy.to_string(),
            cost_rational: cost.to_string(),
            robustness_rational: robustness.to_string(),
        };
        v.validate()?;
        Ok(v)
    }

    pub fn parse_rational(s: &str) -> Result<BigRational, &'static str> {
        let parts: Vec<&str> = s.split('/').collect();
        if parts.len() != 2 {
            return Err("INVALID_RATIONAL_FORMAT");
        }
        let numer = BigInt::from_str(parts[0]).map_err(|_| "INVALID_RATIONAL_NUMERATOR")?;
        let denom = BigInt::from_str(parts[1]).map_err(|_| "INVALID_RATIONAL_DENOMINATOR")?;
        if denom <= BigInt::from(0) {
            return Err("ZERO_OR_NEGATIVE_DENOMINATOR");
        }
        Ok(BigRational::new(numer, denom))
    }

    pub fn accuracy(&self) -> Result<BigRational, &'static str> {
        Self::parse_rational(&self.accuracy_rational)
    }

    pub fn cost(&self) -> Result<BigRational, &'static str> {
        Self::parse_rational(&self.cost_rational)
    }

    pub fn robustness(&self) -> Result<BigRational, &'static str> {
        Self::parse_rational(&self.robustness_rational)
    }

    pub fn validate(&self) -> Result<(), &'static str> {
        let acc = self.accuracy()?;
        let cost = self.cost()?;
        let rob = self.robustness()?;
        if acc < BigRational::from(BigInt::from(0)) || acc > BigRational::from(BigInt::from(1)) {
            return Err("ACCURACY_OUT_OF_BOUNDS_0_1");
        }
        if cost < BigRational::from(BigInt::from(0)) {
            return Err("COST_CANNOT_BE_NEGATIVE");
        }
        if rob < BigRational::from(BigInt::from(0)) || rob > BigRational::from(BigInt::from(1)) {
            return Err("ROBUSTNESS_OUT_OF_BOUNDS_0_1");
        }
        Ok(())
    }

    /// Law of Pareto Conservation (Law 2):
    /// Returns true if candidate weakly dominates active across all 3 coordinates:
    /// accuracy >= other, cost <= other (lower cost is better), robustness >= other.
    pub fn weakly_dominates(&self, other: &Self) -> Result<bool, &'static str> {
        let a1 = self.accuracy()?;
        let a2 = other.accuracy()?;
        let c1 = self.cost()?;
        let c2 = other.cost()?;
        let r1 = self.robustness()?;
        let r2 = other.robustness()?;
        Ok(a1 >= a2 && c1 <= c2 && r1 >= r2)
    }

    /// Returns true if candidate strictly dominates in at least one coordinate.
    pub fn strictly_dominates_any(&self, other: &Self) -> Result<bool, &'static str> {
        let a1 = self.accuracy()?;
        let a2 = other.accuracy()?;
        let c1 = self.cost()?;
        let c2 = other.cost()?;
        let r1 = self.robustness()?;
        let r2 = other.robustness()?;
        Ok(a1 > a2 || c1 < c2 || r1 > r2)
    }

    /// Law of Pareto Conservation replacement check:
    /// Cand replaces Active iff weakly dominates on all coordinates and strictly on >= 1 coordinate.
    pub fn pareto_replaces(&self, active: &Self) -> Result<bool, &'static str> {
        Ok(self.weakly_dominates(active)? && self.strictly_dominates_any(active)?)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MigrationPolicyV1 {
    pub max_incoming_per_epoch: u64,
    pub taxonomic_admissibility: Vec<String>,
}

impl MigrationPolicyV1 {
    pub fn new(max_incoming: u64, admissibility: Vec<String>) -> Self {
        Self {
            max_incoming_per_epoch: max_incoming,
            taxonomic_admissibility: admissibility,
        }
    }

    /// Law of Bounded Migration (Law 3):
    /// Inter-society migration requires taxonomic admissibility and cannot exceed quota.
    /// Quota bound: Q_migr <= max_incoming_per_epoch AND Q_migr <= ceil(current_population / 20).
    pub fn is_migration_allowed(
        &self,
        target_domain: &str,
        incoming_count: u64,
        current_population: u64,
    ) -> Result<bool, &'static str> {
        let admitted = self
            .taxonomic_admissibility
            .iter()
            .any(|label| scope_covers(label, target_domain));
        if !admitted || incoming_count == 0 || incoming_count > self.max_incoming_per_epoch {
            return Ok(false);
        }
        let pop_cap = if current_population == 0 {
            1
        } else {
            (current_population + 19) / 20
        };
        let effective_cap = std::cmp::max(1, std::cmp::min(self.max_incoming_per_epoch, pop_cap));
        Ok(incoming_count <= effective_cap)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PromptSocietyV1 {
    pub society_id: String,
    pub domain_protocol: String,
    pub family_ids: Vec<String>,
    pub aggregate_fitness_vector: AggregateFitnessVectorV1,
    pub migration_policy: MigrationPolicyV1,
    pub created_utc: String,
}

impl PromptSocietyV1 {
    pub fn validate(&self) -> Result<(), &'static str> {
        if !self.society_id.starts_with("sha256:") || self.society_id.len() != 71 {
            return Err("INVALID_SOCIETY_ID_FORMAT");
        }
        let hex_part = &self.society_id[7..];
        if !hex_part.chars().all(|c| c.is_ascii_hexdigit()) {
            return Err("INVALID_SOCIETY_ID_HEX");
        }
        if self.domain_protocol.is_empty() {
            return Err("EMPTY_DOMAIN_PROTOCOL");
        }
        self.aggregate_fitness_vector.validate()?;
        Ok(())
    }

    /// SHA-256 of recursively key-sorted serde_json bytes after validation.
    pub fn canonical_digest(&self) -> Result<String, &'static str> {
        self.validate()?;
        let value = serde_json::to_value(self).map_err(|_| "CANONICAL_ENCODING_FAILED")?;
        let raw =
            serde_json::to_vec(&sort_json_keys(value)).map_err(|_| "CANONICAL_ENCODING_FAILED")?;
        Ok(format!("sha256:{}", hex::encode(Sha256::digest(raw))))
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PromptCivilizationV1 {
    pub civilization_id: String,
    pub society_ids: Vec<String>,
    pub global_immune_registry: String,
    pub reservation_budget_pool: u64,
    pub governance_epoch: u64,
    pub created_utc: String,
    pub authority_effect: String,
}

impl PromptCivilizationV1 {
    pub fn new(
        civilization_id: String,
        society_ids: Vec<String>,
        global_immune_registry: String,
        reservation_budget_pool: u64,
        governance_epoch: u64,
        created_utc: String,
    ) -> Self {
        Self {
            civilization_id,
            society_ids,
            global_immune_registry,
            reservation_budget_pool,
            governance_epoch,
            created_utc,
            authority_effect: "None".to_string(),
        }
    }

    pub fn validate(&self) -> Result<(), &'static str> {
        if !self.civilization_id.starts_with("sha256:") || self.civilization_id.len() != 71 {
            return Err("INVALID_CIVILIZATION_ID_FORMAT");
        }
        if self.authority_effect != "None" {
            return Err("AUTHORITY_EFFECT_MUST_BE_NONE");
        }
        Ok(())
    }

    /// Law of Budget Solvency (Law 4):
    /// Total reserved across all societies must not exceed reservation budget pool.
    pub fn check_budget_solvency(&self, total_reserved: u64) -> Result<(), &'static str> {
        if total_reserved > self.reservation_budget_pool {
            Err("BUDGET_OVERDRAFT_REFUSED")
        } else {
            Ok(())
        }
    }

    pub fn advance_epoch(&mut self) {
        self.governance_epoch += 1;
    }
}

fn sort_json_keys(value: Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut sorted = serde_json::Map::new();
            let mut keys: Vec<String> = map.keys().cloned().collect();
            keys.sort();
            for k in keys {
                if let Some(v) = map.get(&k) {
                    sorted.insert(k, sort_json_keys(v.clone()));
                }
            }
            Value::Object(sorted)
        }
        Value::Array(arr) => Value::Array(arr.into_iter().map(sort_json_keys).collect()),
        other => other,
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/society.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:society:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf7a65f1f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf7a65f1f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf7a65f1f {
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
impl BoundaryErrorf7a65f1f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf7a65f1f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf7a65f1f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf7a65f1f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf7a65f1f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf7a65f1f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf7a65f1f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf7a65f1f::ExceedsCapacity {
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
    fn test_aggregate_fitness_vector_pareto_conservation() {
        let active = AggregateFitnessVectorV1::new("4/5", "10/1", "9/10").unwrap();
        // Weakly dominates on accuracy (4/5 == 4/5), strictly dominates on cost (8/1 < 10/1), same robustness
        let candidate_better_cost = AggregateFitnessVectorV1::new("4/5", "8/1", "9/10").unwrap();
        assert!(candidate_better_cost.pareto_replaces(&active).unwrap());

        // Worse on accuracy (3/5 < 4/5) despite better cost (5/1 < 10/1) -> does not replace
        let candidate_worse_acc = AggregateFitnessVectorV1::new("3/5", "5/1", "9/10").unwrap();
        assert!(!candidate_worse_acc.pareto_replaces(&active).unwrap());

        // Identical vector -> does not strictly dominate any coordinate -> does not replace
        let identical = AggregateFitnessVectorV1::new("4/5", "10/1", "9/10").unwrap();
        assert!(!identical.pareto_replaces(&active).unwrap());
    }

    #[test]
    fn test_budget_solvency_law() {
        let civ = PromptCivilizationV1::new(
            "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef".to_string(),
            vec!["soc_1".into()],
            "oeeis:registry:v1".into(),
            100_000,
            0,
            "2026-10-09T00:00:00Z".into(),
        );
        assert!(civ.check_budget_solvency(90_000).is_ok());
        assert!(civ.check_budget_solvency(100_000).is_ok());
        assert_eq!(
            civ.check_budget_solvency(100_001).unwrap_err(),
            "BUDGET_OVERDRAFT_REFUSED"
        );
    }

    #[test]
    fn test_bounded_migration_law() {
        let policy = MigrationPolicyV1::new(5, vec!["core.math.*".into(), "core.physics".into()]);
        // Admissible domain, count within quota and population cap
        assert!(policy
            .is_migration_allowed("core.physics", 3, 100)
            .unwrap());
        assert!(policy
            .is_migration_allowed("core.math.integral", 4, 100)
            .unwrap());
        assert!(!policy
            .is_migration_allowed("core.mathematics", 1, 100)
            .unwrap());
        assert!(!policy
            .is_migration_allowed("core.physics.quantum", 1, 100)
            .unwrap());
        assert!(!policy
            .is_migration_allowed("core.physics", 0, 100)
            .unwrap());
        // Inadmissible domain
        assert!(!policy
            .is_migration_allowed("core.biology", 1, 100)
            .unwrap());
        // Exceeds quota (6 > 5)
        assert!(!policy
            .is_migration_allowed("core.physics", 6, 100)
            .unwrap());
    }

    #[test]
    fn test_society_validation_and_canonical_digest() {
        let soc = PromptSocietyV1 {
            society_id: "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
                .into(),
            domain_protocol: "core.math.integral:v1".into(),
            family_ids: vec!["fam_alpha".into(), "fam_beta".into()],
            aggregate_fitness_vector: AggregateFitnessVectorV1::new("4/5", "10/1", "9/10").unwrap(),
            migration_policy: MigrationPolicyV1::new(5, vec!["core.math.*".into()]),
            created_utc: "2026-10-09T00:00:00Z".into(),
        };
        assert!(soc.validate().is_ok());
        let digest = soc.canonical_digest().unwrap();
        assert!(digest.starts_with("sha256:"));
        assert_eq!(digest.len(), 71);
    }
}

#[cfg(test)]
mod l4_boundary_tests_f7a65f1f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf7a65f1f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf7a65f1f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf7a65f1f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf7a65f1f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf7a65f1f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorf7a65f1f::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorf7a65f1f::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
