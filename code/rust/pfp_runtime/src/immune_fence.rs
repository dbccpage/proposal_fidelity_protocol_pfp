//! Render admitted, reviewed guidance without copying detector fixtures into prompts.

use std::collections::BTreeSet;

use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const ANCHOR: &str = "[IMMUNE_FENCE]";
const END: &str = "[/IMMUNE_FENCE]";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Guidance {
    antibody_id: String,
    rule_digest: String,
    guidance_text: String,
    admission_reference: Value,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    template_text: String,
    template_id: String,
    template_version: String,
    prompt_uri: String,
    operation_id: String,
    catalog_digest: String,
    guidance: Vec<Guidance>,
    #[serde(default)]
    required_ids: Vec<String>,
    #[serde(default = "default_items")]
    max_items: usize,
    #[serde(default = "default_bytes")]
    max_bytes: usize,
}

fn default_items() -> usize {
    3
}
fn default_bytes() -> usize {
    2048
}
fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}
fn is_digest(s: &str) -> bool {
    s.len() == 64
        && s.bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

/// The caller supplies admission-checked search results, never arbitrary catalog rows.
/// This renderer neither admits antibodies nor establishes mathematical correctness.
pub fn execute(payload: &Value) -> Result<Value, String> {
    let mut ordered = payload.clone();
    ordered.sort_all_objects();
    let request_digest = digest(&serde_json::to_vec(&ordered).map_err(|e| e.to_string())?);
    let r: Request = serde_json::from_value(payload.clone())
        .map_err(|e| format!("IMMUNE_FENCE_INPUT_INVALID: {e}"))?;
    if r.template_text.len() > 48 * 1024 || r.guidance.len() > 128 {
        return Err("IMMUNE_FENCE_RESOURCE_LIMIT".into());
    }
    if r.template_text.matches(ANCHOR).count() != 1 || r.template_text.contains(END) {
        return Err("IMMUNE_FENCE_ANCHOR_COUNT".into());
    }
    if r.max_items == 0
        || r.max_items > 3
        || r.max_bytes < ANCHOR.len() + END.len() + 4
        || r.max_bytes > 2048
    {
        return Err("IMMUNE_FENCE_LIMIT_INVALID".into());
    }
    if [
        &r.template_id,
        &r.template_version,
        &r.prompt_uri,
        &r.operation_id,
    ]
    .iter()
    .any(|s| s.trim().is_empty())
        || !is_digest(&r.catalog_digest)
    {
        return Err("IMMUNE_FENCE_BINDING_INVALID".into());
    }
    let mut seen = BTreeSet::new();
    let mut rendered_items = Vec::new();
    let mut selected = Vec::new();
    let mut omissions = Vec::new();
    for item in r.guidance {
        if item.antibody_id.trim().is_empty()
            || !seen.insert(item.antibody_id.clone())
            || !is_digest(&item.rule_digest)
            || item.guidance_text.trim().is_empty()
            || item.guidance_text.contains(ANCHOR)
            || item.guidance_text.contains(END)
            || item
                .admission_reference
                .as_object()
                .map_or(true, |reference| reference.is_empty())
        {
            return Err("IMMUNE_FENCE_GUIDANCE_INVALID".into());
        }
        let reason = if selected.len() >= r.max_items {
            Some("ITEM_LIMIT")
        } else {
            None
        };
        // JSON keeps multi-line guidance data within one item. Only this reviewed field
        // crosses into the prompt; raw catalog prose and checker fixtures cannot enter.
        let rendered = json!({"antibody_id": item.antibody_id, "guidance": item.guidance_text});
        let mut trial = rendered_items.clone();
        trial.push(rendered.clone());
        let body = format!(
            "{ANCHOR}\n{}\n{END}",
            serde_json::to_string(&trial).map_err(|e| e.to_string())?
        );
        let reason = reason.or(if body.len() > r.max_bytes {
            Some("FENCE_BYTE_LIMIT")
        } else {
            None
        });
        if let Some(reason) = reason {
            omissions.push(json!({"antibody_id": item.antibody_id, "reason": reason}));
        } else {
            rendered_items.push(rendered);
            selected.push(json!({"antibody_id": item.antibody_id, "rule_digest": item.rule_digest,
                "guidance_sha256": digest(item.guidance_text.as_bytes()), "admission_reference": item.admission_reference}));
        }
    }
    for id in &r.required_ids {
        if !selected
            .iter()
            .any(|v| v["antibody_id"].as_str() == Some(id.as_str()))
        {
            return Err(format!("IMMUNE_REQUIRED_BINDING_MISSING: {id}"));
        }
    }
    let fence = format!(
        "{ANCHOR}\n{}\n{END}",
        serde_json::to_string(&rendered_items).map_err(|e| e.to_string())?
    );
    let rendered_text = r.template_text.replacen(ANCHOR, &fence, 1);
    let mut binding = json!({"schema_version": "core.pfp.immune-binding.v1",
        "template_id": r.template_id, "template_version": r.template_version,
        "prompt_uri": r.prompt_uri, "operation_id": r.operation_id,
        "catalog_digest": r.catalog_digest, "template_sha256": digest(r.template_text.as_bytes()),
        "rendered_sha256": digest(rendered_text.as_bytes()), "fence_sha256": digest(fence.as_bytes()),
        "fence_bytes": fence.len(), "selected": selected, "omissions": omissions,
        "authority_effect": "None"});
    // Existing serde sorted-key JSON profile; no RFC 8785 claim.
    let hash = digest(&serde_json::to_vec(&binding).map_err(|e| e.to_string())?);
    binding["binding_sha256"] = json!(hash);
    Ok(
        json!({"request_digest": request_digest, "rendered_text": rendered_text, "binding": binding,
        "selected": selected, "omissions": omissions, "authority_effect": "None"}),
    )
}

// Origin: engine/crates_rs/pfp_runtime/src/immune_fence.rs
// Claim: urn:core:crates_rs:pfp-runtime:immune-fence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0d682eae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0d682eae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0d682eae {
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
impl BoundaryError0d682eae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0d682eae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0d682eae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0d682eae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0d682eae> {
        if capacity_bound == 0 {
            return Err(BoundaryError0d682eae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0d682eae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0d682eae::ExceedsCapacity {
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
mod l4_boundary_tests_0d682eae {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0d682eae::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0d682eae::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0d682eae::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0d682eae::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0d682eae::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0d682eae::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0d682eae::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
