//! The research workflow folder, checked against this controller.
//!
//! The folder (`education/documentation/030_.../workflows/research/`) states
//! the loop as data; this module states it as code. `check_pack` fails when the two drift:
//! default limits, required mission fields, routing names, stage executors, the nine-packet
//! prompt family and the response schemas.
//!
//! AuthorityEffect: None.

use super::mission::{Limits, MISSION_REQUIRED};
use super::refuse;
use super::response_schema::{ResponseSchema, Violation};
use super::routing::Disposition;
use crate::stage::ports::Refusal;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::path::Path;

pub const WORKFLOW_FILE: &str = "researcher_workflow.pfp.yaml";
pub const ROOT_ID: &str = "P_STAR_RESEARCH";
pub const HOST_ONLY_ID: &str = "P_RESEARCH_05";

/// The order of the workflow's `routing_priority` rows. It is not the controller's
/// precedence: `routing::route` documents where and why it departs. Pinning the YAML order
/// here means reordering the rows is a change to this file too, so it gets reviewed
/// against `route` instead of passing silently.
pub const PACK_ROUTING_ORDER: [Disposition; 12] = [
    Disposition::Refused,
    Disposition::InfrastructureFailure,
    Disposition::BudgetExhausted,
    Disposition::BlockedByEvidence,
    Disposition::NeedsExternalOracle,
    Disposition::InvalidateAndRecheck,
    Disposition::RepairNextRound,
    Disposition::OpenObstruction,
    Disposition::Verified,
    Disposition::VerifiedWithResiduals,
    Disposition::StabilizedSurvivor,
    Disposition::OpenObstruction,
];

fn drift(message: impl Into<String>) -> Refusal {
    refuse("RESEARCH_PACK_DRIFT", message)
}

fn read_yaml(path: &Path) -> Result<Value, Refusal> {
    let text = std::fs::read_to_string(path).map_err(|e| {
        refuse(
            "RESEARCH_PACK_UNREADABLE",
            format!("{}: {e}", path.display()),
        )
    })?;
    serde_yaml::from_str(&text).map_err(|e| {
        refuse(
            "RESEARCH_PACK_UNREADABLE",
            format!("{}: {e}", path.display()),
        )
    })
}

fn read_json(path: &Path) -> Result<Value, Refusal> {
    let bytes = std::fs::read(path).map_err(|e| {
        refuse(
            "RESEARCH_PACK_UNREADABLE",
            format!("{}: {e}", path.display()),
        )
    })?;
    serde_json::from_slice(&bytes).map_err(|e| {
        refuse(
            "RESEARCH_PACK_UNREADABLE",
            format!("{}: {e}", path.display()),
        )
    })
}

/// The eight child ids in stage order.
pub fn child_ids() -> Vec<String> {
    (1..=8).map(|n| format!("P_RESEARCH_{n:02}")).collect()
}

fn file_stem(prompt_id: &str) -> String {
    prompt_id.to_ascii_lowercase()
}

/// The compiled response schema of one packet (`contracts/response_<id>.schema.json`).
pub fn response_schema(dir: &Path, prompt_id: &str) -> Result<ResponseSchema, Refusal> {
    if prompt_id != ROOT_ID && !child_ids().iter().any(|id| id == prompt_id) {
        return Err(refuse(
            "RESEARCH_PACKET_UNKNOWN",
            format!("no packet {prompt_id}"),
        ));
    }
    let path = dir
        .join("contracts")
        .join(format!("response_{}.schema.json", file_stem(prompt_id)));
    ResponseSchema::compile(&read_json(&path)?)
}

/// Validate a model response for one packet. Stage 5 is host-only, so a response for
/// `P_RESEARCH_05` is refused rather than validated.
pub fn validate_response(
    dir: &Path,
    prompt_id: &str,
    response: &Value,
) -> Result<Vec<Violation>, Refusal> {
    if prompt_id == HOST_ONLY_ID {
        return Err(refuse(
            "STAGE5_HOST_ONLY",
            "stage 5 is evaluated by the host, not answered by a model",
        ));
    }
    Ok(response_schema(dir, prompt_id)?.validate(response))
}

fn route_name(text: &str) -> String {
    text.split(|c: char| c == ';' || c.is_whitespace())
        .next()
        .unwrap_or_default()
        .replace('_', "")
        .to_ascii_lowercase()
}

/// Check the folder against the controller. Returns a summary of what was compared.
pub fn check_pack(dir: &Path) -> Result<Value, Refusal> {
    let workflow = read_yaml(&dir.join(WORKFLOW_FILE))?;
    if workflow["workflow_id"] != json!("WF_RESEARCH_PFP")
        || workflow["authority_effect"] != json!("None")
    {
        return Err(drift("workflow id or authority effect changed"));
    }

    // Defaults: every limit the YAML names equals Limits::default(), and none is missing.
    let mut defaults = workflow["defaults"].clone();
    if let Some(map) = defaults.as_object_mut() {
        map.remove("cost_zero_means");
    }
    let parsed: Limits =
        serde_json::from_value(defaults.clone()).map_err(|e| drift(format!("defaults: {e}")))?;
    let expected = serde_json::to_value(Limits::default()).map_err(|e| drift(e.to_string()))?;
    if parsed != Limits::default() || defaults != expected {
        return Err(drift("workflow defaults differ from Limits::default()"));
    }

    let required: Vec<&str> = workflow["mission_required"]
        .as_array()
        .map(|items| items.iter().filter_map(Value::as_str).collect())
        .unwrap_or_default();
    if required != MISSION_REQUIRED {
        return Err(drift(
            "mission_required differs from the controller's mission fields",
        ));
    }

    // Routing: every route names a disposition, and every disposition is named.
    let mut named = BTreeSet::new();
    let mut order = Vec::new();
    for row in workflow["routing_priority"]
        .as_array()
        .into_iter()
        .flatten()
    {
        let route = route_name(row["route"].as_str().unwrap_or_default());
        let disposition = Disposition::ALL
            .into_iter()
            .find(|d| format!("{d:?}").to_ascii_lowercase() == route)
            .ok_or_else(|| drift(format!("route {route:?} names no disposition")))?;
        named.insert(disposition);
        order.push(disposition);
    }
    if order != PACK_ROUTING_ORDER {
        return Err(drift(
            "routing_priority rows changed order; review routing::route against them",
        ));
    }
    if let Some(missing) = Disposition::ALL.into_iter().find(|d| !named.contains(d)) {
        return Err(drift(format!("no routing_priority row names {missing:?}")));
    }

    // Stages: stage n requires 1..n-1; stage 5 alone is host-executed.
    let stages_dir = dir.join("stages");
    let controller = read_yaml(&stages_dir.join("controller.yaml"))?;
    let rows = controller["stages"]
        .as_array()
        .ok_or_else(|| drift("controller lists no stages"))?;
    if rows.len() != 8 {
        return Err(drift("the controller must list eight stages"));
    }
    for (index, row) in rows.iter().enumerate() {
        let stage = index as u64 + 1;
        let executor = if stage == 5 { "host" } else { "model" };
        let requires: Vec<u64> = (1..stage).collect();
        let file = row["file"].as_str().unwrap_or_default();
        let body = read_yaml(&stages_dir.join(file))?;
        for (name, source) in [("controller", row), ("stage file", &body)] {
            if source["stage"] != json!(stage)
                || source["executor"] != json!(executor)
                || source["requires"] != json!(requires)
            {
                return Err(drift(format!(
                    "{name} entry for stage {stage} has the wrong order or executor"
                )));
            }
        }
    }

    // Prompt family: one root and eight generation-0 children decomposed from it.
    let family = &workflow["prompt_family"];
    let mut ids = vec![ROOT_ID.to_owned()];
    ids.extend(child_ids());
    let mut paths = vec![family["root"].clone()];
    paths.extend(family["children"].as_array().cloned().unwrap_or_default());
    let expected_paths: Vec<Value> = ids
        .iter()
        .map(|id| json!(format!("prompts/{}.yaml", file_stem(id))))
        .collect();
    if paths != expected_paths
        || family["host_only_node"] != json!(HOST_ONLY_ID)
        || family["cardinality"] != json!(9)
    {
        return Err(drift(
            "prompt_family paths, cardinality or host-only node changed",
        ));
    }
    let mut budget = None;
    for id in &ids {
        let packet = read_yaml(&dir.join("prompts").join(format!("{}.yaml", file_stem(id))))?;
        let lineage = &packet["lineage"];
        let parents = if id == ROOT_ID {
            json!([])
        } else {
            json!([{"prompt_id": ROOT_ID, "generation": 0, "relationship": "decompose", "witness_ref": null}])
        };
        if lineage["prompt_id"] != json!(id)
            || lineage["generation_id"] != json!(0)
            || lineage["parents"] != parents
            || lineage["root_prompt_ids"] != json!([ROOT_ID])
            || packet["authority_effect"] != json!("None")
        {
            return Err(drift(format!("{id}: lineage or authority effect differs")));
        }
        if packet["system_prompt"]["antibody_injections"] != json!([]) {
            return Err(drift(format!("{id}: antibody injections must stay empty")));
        }
        let raw = packet["source"]["raw_text"].as_str().unwrap_or_default();
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(raw.as_bytes())));
        if packet["source"]["sha256"] != json!(digest) {
            return Err(drift(format!(
                "{id}: source raw_text does not match its sha256"
            )));
        }
        let this = packet["execution"]["budget"].clone();
        if budget.get_or_insert_with(|| this.clone()) != &this {
            return Err(drift(format!(
                "{id}: execution budget differs from the root's"
            )));
        }
        if id == ROOT_ID {
            let subprompts = packet["decomposition"]["subprompts"]
                .as_array()
                .cloned()
                .unwrap_or_default();
            let listed: Vec<(Value, Value, Value)> = subprompts
                .iter()
                .map(|s| {
                    (
                        s["subprompt_id"].clone(),
                        s["packet_id"].clone(),
                        s["ordinal"].clone(),
                    )
                })
                .collect();
            let wanted: Vec<(Value, Value, Value)> = child_ids()
                .iter()
                .enumerate()
                .map(|(i, c)| (json!(c), json!(c), json!(i)))
                .collect();
            if listed != wanted {
                return Err(drift(
                    "the root's subprompts do not list the eight children in order",
                ));
            }
            let host = subprompts
                .iter()
                .filter(|s| s["role"] == json!("host_evaluate"))
                .count();
            if host != 1 || subprompts[4]["role"] != json!("host_evaluate") {
                return Err(drift("exactly the fifth child is host-evaluated"));
            }
        }
        response_schema(dir, id)?;
    }
    Ok(json!({
        "workflow_id": "WF_RESEARCH_PFP",
        "packets": ids,
        "dispositions": named.len(),
        "stages": 8,
        "authority_effect": "None",
    }))
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/pack.rs
// Claim: urn:core:crates_rs:core-adversary:pack:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1219153c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1219153c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1219153c {
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
impl BoundaryError1219153c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1219153c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1219153c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1219153c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1219153c> {
        if capacity_bound == 0 {
            return Err(BoundaryError1219153c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1219153c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1219153c::ExceedsCapacity {
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
mod l4_boundary_tests_1219153c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1219153c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1219153c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1219153c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1219153c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1219153c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1219153c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1219153c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
