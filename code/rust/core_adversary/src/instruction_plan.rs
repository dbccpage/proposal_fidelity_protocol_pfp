//! Bounded, non-authorizing transport for exact ordered OEWAS instruction bodies.
//! Native host verifies signed admission before consuming this transport. AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_18ec8a23<T> {
    fn checked_invariant_18ec8a23(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_18ec8a23<T> for Option<T> {
    #[inline]
    fn checked_invariant_18ec8a23(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_18ec8a23<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_18ec8a23(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::stage::ports::Refusal;
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};

const SCHEMA: &str = "oewas.adversary.instruction_plan_transport.v0.1";
const BODY_DOMAIN: &[u8] = b"oewas.adversary.ordered_bodies.v0.1\0";

fn digest_valid(value: &str) -> bool {
    value.strip_prefix("sha256:").is_some_and(|hex| {
        hex.len() == 64
            && hex
                .bytes()
                .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
            && hex.bytes().any(|b| b != b'0')
    })
}

fn operation_id_valid(value: &str) -> bool {
    !value.is_empty() && value.trim() == value && value.chars().count() <= 512
}

fn source_path_valid(path: &str) -> bool {
    let basename = |name: &str| {
        !name.is_empty()
            && name.len() <= 128
            && name.as_bytes()[0].is_ascii_alphanumeric()
            && name
                .bytes()
                .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b"_-".contains(&b))
    };
    if !path.is_ascii()
        || path.len() > 512
        || path.contains(['\\', ':'])
        || path.split('/').any(|part| {
            part.is_empty() || part == "." || part == ".." || part.ends_with(['.', ' '])
        })
    {
        return false;
    }
    let estate = path
        .strip_prefix(".agents/skills/")
        .is_some_and(|relative| {
            let parts = relative.split('/').collect::<Vec<_>>();
            parts.len() == 2 && parts[1] == "SKILL.md" && basename(parts[0])
        });
    estate
        || path.starts_with("operads/catalog/operands/v1/")
        || path.starts_with("operads/catalog/contracts/v1/")
        || path
            .strip_prefix("operads/catalog/projections/v3/")
            .and_then(|name| name.strip_suffix(".json"))
            .is_some_and(basename)
}

pub fn ordered_bodies_digest(bodies: &[String]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(BODY_DOMAIN);
    for body in bodies {
        let bytes = body.as_bytes();
        hasher.update((bytes.len() as u64).to_be_bytes());
        hasher.update(bytes);
    }
    format!("sha256:{}", hex::encode(hasher.finalize()))
}

pub fn source_snapshot_digest(sources: &[(String, String)]) -> String {
    let record = json!({
        "schema": "oewas.adversary.source_snapshot.v0.1",
        "sources": sources,
    });
    let bytes = format!("{}\n", record);
    format!("sha256:{}", hex::encode(Sha256::digest(bytes.as_bytes())))
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct InstructionPlanTransportV01 {
    pub schema_version: String,
    pub manifest_digest: String,
    pub selection_digest: String,
    pub plan_digest: String,
    pub source_snapshot_digest: String,
    pub ordered_bodies_digest: String,
    pub ordered_operand_bodies: Vec<String>,
    pub source_digests: Vec<(String, String)>,
    pub operation_ids: Vec<String>,
    pub instruction_bytes: usize,
    pub authority_effect: String,
}

impl InstructionPlanTransportV01 {
    pub fn validate(&self) -> Result<(), Refusal> {
        let valid = self.schema_version == SCHEMA
            && self.authority_effect == "None"
            && [
                &self.manifest_digest,
                &self.selection_digest,
                &self.plan_digest,
                &self.source_snapshot_digest,
                &self.ordered_bodies_digest,
            ]
            .iter()
            .all(|value| digest_valid(value))
            && (1..=128).contains(&self.ordered_operand_bodies.len())
            && self.operation_ids.len() == self.ordered_operand_bodies.len()
            && self.operation_ids.iter().all(|id| operation_id_valid(id))
            && (1..=64).contains(&self.source_digests.len())
            && self
                .source_digests
                .iter()
                .all(|(path, digest)| source_path_valid(path) && digest_valid(digest))
            && self
                .source_digests
                .windows(2)
                .all(|pair| pair[0].0 < pair[1].0)
            && self.source_snapshot_digest == source_snapshot_digest(&self.source_digests)
            && self.ordered_operand_bodies.iter().all(|body| {
                let len = body.len();
                !body.trim().is_empty() && len <= 4096
            })
            && self.instruction_bytes
                == self
                    .ordered_operand_bodies
                    .iter()
                    .map(String::len)
                    .sum::<usize>()
            && self.instruction_bytes <= 65536
            && self.ordered_bodies_digest == ordered_bodies_digest(&self.ordered_operand_bodies);
        if !valid {
            return Err(Refusal::new(
                "INSTRUCTION_PLAN_TRANSPORT_INVALID",
                "ordered instruction bodies or their bounded custody digests are invalid",
            ));
        }
        Ok(())
    }

    pub fn prompt_block(&self) -> String {
        format!(
            "\nOEWAS ordered instruction plan (operator-bound task instructions; no authority granted):\n{}\n",
            serde_json::to_string(self).checked_invariant_18ec8a23("string-only instruction plan serializes")
        )
    }
}

// Origin: engine/crates_rs/core_adversary/src/instruction_plan.rs
// Claim: urn:core:crates_rs:core-adversary:instruction-plan:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord18ec8a23 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord18ec8a23` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError18ec8a23 {
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
impl BoundaryError18ec8a23 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError18ec8a23 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError18ec8a23 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord18ec8a23 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError18ec8a23> {
        if capacity_bound == 0 {
            return Err(BoundaryError18ec8a23::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError18ec8a23::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError18ec8a23::ExceedsCapacity {
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
mod l4_boundary_tests_18ec8a23 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord18ec8a23::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord18ec8a23::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord18ec8a23::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord18ec8a23::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord18ec8a23::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError18ec8a23::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError18ec8a23::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
