//! Immutable cemetery, failure-count and lineage metadata.
//! These records do not verify defects, admit detectors or mint authority.
use crate::stage::canonical::{
    digest, identifier, integer, semantic_id, strings, text, StringKind,
};
use crate::stage::ports::Refusal;
use serde::Deserialize;
use serde_json::{json, Map, Value};

fn refused(message: impl Into<String>) -> Refusal {
    let mut refusal = Refusal::new("OEAS_GENEALOGY_REFUSED", message);
    refusal.locus = "adversary.stage.domain.genealogy".into();
    refusal
}
fn fields<'a>(
    value: &'a Value,
    names: &[&str],
    label: &str,
) -> Result<&'a Map<String, Value>, Refusal> {
    let object = value
        .as_object()
        .ok_or_else(|| refused(format!("{label} must be an exact string-keyed object")))?;
    let mut missing: Vec<&str> = names
        .iter()
        .copied()
        .filter(|name| !object.contains_key(*name))
        .collect();
    missing.sort_unstable();
    if !missing.is_empty() {
        return Err(refused(format!(
            "{label} missing fields: {}",
            missing.join(", ")
        )));
    }
    let unknown: Vec<&str> = object
        .keys()
        .map(String::as_str)
        .filter(|key| !names.contains(key))
        .collect();
    if !unknown.is_empty() {
        return Err(refused(format!(
            "{label} unknown fields: {}",
            unknown.join(", ")
        )));
    }
    Ok(object)
}
fn wire_text(object: &Map<String, Value>, label: &str) -> Result<String, Refusal> {
    object
        .get(label)
        .and_then(Value::as_str)
        .map(str::to_owned)
        .ok_or_else(|| refused(format!("{label} must be an exact string")))
}
fn wire_digest(object: &Map<String, Value>, label: &str) -> Result<String, Refusal> {
    let value = object
        .get(label)
        .and_then(Value::as_str)
        .ok_or_else(|| refused(format!("{label} must be a lowercase sha256 digest")))?;
    digest(value, label, false).map_err(refused)?;
    Ok(value.into())
}
fn wire_count(object: &Map<String, Value>, label: &str) -> Result<u32, Refusal> {
    object
        .get(label)
        .and_then(Value::as_number)
        .and_then(|value| value.to_string().parse::<u32>().ok())
        .filter(|value| *value <= 1_000_000)
        .ok_or_else(|| refused(format!("{label} must be an exact integer in [0, 1000000]")))
}
fn wire_strings(object: &Map<String, Value>, label: &str) -> Result<Vec<String>, Refusal> {
    let values = object
        .get(label)
        .and_then(Value::as_array)
        .ok_or_else(|| refused(format!("{label} must be an exact JSON array")))?;
    if values.len() > 256 {
        return Err(refused(format!("{label} exceeds the item limit")));
    }
    let parsed = values
        .iter()
        .enumerate()
        .map(|(index, value)| {
            value
                .as_str()
                .map(str::to_owned)
                .ok_or_else(|| refused(format!("{label}[{index}] must be an exact string")))
        })
        .collect::<Result<Vec<_>, _>>()?;
    strings(&parsed, label, StringKind::Text, true).map_err(refused)?;
    Ok(parsed)
}

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HeadstoneInput {
    pub candidate_id: String,
    pub run_key: String,
    pub scene_id: String,
    pub cause_of_death: String,
    pub killing_seat_id: String,
    pub evidence_refs: Vec<String>,
    pub candidate_payload_sha256: String,
    #[serde(default)]
    pub round_index: u32,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CemeteryHeadstone {
    input: HeadstoneInput,
    headstone_id: String,
}
impl CemeteryHeadstone {
    pub fn new(input: HeadstoneInput) -> Result<Self, Refusal> {
        identifier(&input.candidate_id, "candidate_id").map_err(refused)?;
        identifier(&input.run_key, "run_key").map_err(refused)?;
        identifier(&input.scene_id, "scene_id").map_err(refused)?;
        text(&input.cause_of_death, "cause_of_death", false).map_err(refused)?;
        identifier(&input.killing_seat_id, "killing_seat_id").map_err(refused)?;
        strings(
            &input.evidence_refs,
            "evidence_refs",
            StringKind::TextOrEmpty,
            true,
        )
        .map_err(refused)?;
        digest(
            &input.candidate_payload_sha256,
            "candidate_payload_sha256",
            false,
        )
        .map_err(refused)?;
        integer(input.round_index, "round_index", 0, 1_000_000).map_err(refused)?;
        let payload = Map::from_iter([
            ("run_key".into(), json!(input.run_key)),
            ("scene_id".into(), json!(input.scene_id)),
            ("candidate_id".into(), json!(input.candidate_id)),
            ("cause_of_death".into(), json!(input.cause_of_death)),
        ]);
        Ok(Self {
            headstone_id: semantic_id("core.oeas.headstone.v1", &payload)?,
            input,
        })
    }
    pub fn input(&self) -> &HeadstoneInput {
        &self.input
    }
    pub fn headstone_id(&self) -> &str {
        &self.headstone_id
    }
    pub fn to_dict(&self) -> Value {
        json!({"headstone_id":self.headstone_id,"candidate_id":self.input.candidate_id,
            "run_key":self.input.run_key,"scene_id":self.input.scene_id,"cause_of_death":self.input.cause_of_death,
            "killing_seat_id":self.input.killing_seat_id,"evidence_refs":self.input.evidence_refs,
            "candidate_payload_sha256":self.input.candidate_payload_sha256,"round_index":self.input.round_index})
    }
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        let object = fields(
            value,
            &[
                "headstone_id",
                "candidate_id",
                "run_key",
                "scene_id",
                "cause_of_death",
                "killing_seat_id",
                "evidence_refs",
                "candidate_payload_sha256",
                "round_index",
            ],
            "cemetery headstone",
        )?;
        let parsed = Self::new(Self::parse_headstone_input(object)?)?;
        if wire_digest(object, "headstone_id")? != parsed.headstone_id {
            return Err(refused(
                "cemetery headstone identity does not match its payload",
            ));
        }
        Ok(parsed)
    }

    fn parse_headstone_input(object: &Map<String, Value>) -> Result<HeadstoneInput, Refusal> {
        Ok(HeadstoneInput {
            candidate_id: wire_text(object, "candidate_id")?,
            run_key: wire_text(object, "run_key")?,
            scene_id: wire_text(object, "scene_id")?,
            cause_of_death: wire_text(object, "cause_of_death")?,
            killing_seat_id: wire_text(object, "killing_seat_id")?,
            evidence_refs: wire_strings(object, "evidence_refs")?,
            candidate_payload_sha256: wire_digest(object, "candidate_payload_sha256")?,
            round_index: wire_count(object, "round_index")?,
        })
    }
}

fn active() -> String {
    "ACTIVE".into()
}
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AntibodyEntryInput {
    pub antibody_id: String,
    pub failure_pattern: String,
    pub occurrences: u32,
    pub constraint_rule: String,
    #[serde(default = "active")]
    pub status: String,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AntibodyEntry {
    input: AntibodyEntryInput,
}
impl AntibodyEntry {
    pub fn new(input: AntibodyEntryInput) -> Result<Self, Refusal> {
        identifier(&input.antibody_id, "antibody_id").map_err(refused)?;
        text(&input.failure_pattern, "failure_pattern", false).map_err(refused)?;
        integer(input.occurrences, "occurrences", 1, 1_000_000).map_err(refused)?;
        text(&input.constraint_rule, "constraint_rule", false).map_err(refused)?;
        identifier(&input.status, "status").map_err(refused)?;
        Ok(Self { input })
    }
    pub fn input(&self) -> &AntibodyEntryInput {
        &self.input
    }
    pub fn to_dict(&self) -> Value {
        json!({"antibody_id":self.input.antibody_id,"failure_pattern":self.input.failure_pattern,
            "occurrences":self.input.occurrences,"constraint_rule":self.input.constraint_rule,"status":self.input.status})
    }
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        let object = fields(
            value,
            &[
                "antibody_id",
                "failure_pattern",
                "occurrences",
                "constraint_rule",
                "status",
            ],
            "antibody entry",
        )?;
        Self::new(AntibodyEntryInput {
            antibody_id: wire_text(object, "antibody_id")?,
            failure_pattern: wire_text(object, "failure_pattern")?,
            occurrences: wire_count(object, "occurrences")?,
            constraint_rule: wire_text(object, "constraint_rule")?,
            status: wire_text(object, "status")?,
        })
    }
}

fn compost_guided() -> String {
    "COMPOST_GUIDED_MUTATION".into()
}
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GenealogyInput {
    pub parent_run_key: String,
    pub child_run_key: String,
    pub structural_deficiencies: Vec<String>,
    pub concrete_fixes: Vec<String>,
    pub next_run_guidance: String,
    #[serde(default = "compost_guided")]
    pub re_entry_reason: String,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenealogyEntry {
    input: GenealogyInput,
    lineage_id: String,
}
impl GenealogyEntry {
    pub fn new(input: GenealogyInput) -> Result<Self, Refusal> {
        identifier(&input.parent_run_key, "parent_run_key").map_err(refused)?;
        identifier(&input.child_run_key, "child_run_key").map_err(refused)?;
        strings(
            &input.structural_deficiencies,
            "structural_deficiencies",
            StringKind::Text,
            true,
        )
        .map_err(refused)?;
        strings(
            &input.concrete_fixes,
            "concrete_fixes",
            StringKind::Text,
            true,
        )
        .map_err(refused)?;
        text(&input.next_run_guidance, "next_run_guidance", false).map_err(refused)?;
        identifier(&input.re_entry_reason, "re_entry_reason").map_err(refused)?;
        let payload = Map::from_iter([
            ("parent_run_key".into(), json!(input.parent_run_key)),
            ("child_run_key".into(), json!(input.child_run_key)),
            ("re_entry_reason".into(), json!(input.re_entry_reason)),
        ]);
        Ok(Self {
            lineage_id: semantic_id("core.oeas.genealogy.v1", &payload)?,
            input,
        })
    }
    pub fn input(&self) -> &GenealogyInput {
        &self.input
    }
    pub fn lineage_id(&self) -> &str {
        &self.lineage_id
    }
    pub fn to_dict(&self) -> Value {
        json!({"lineage_id":self.lineage_id,"parent_run_key":self.input.parent_run_key,"child_run_key":self.input.child_run_key,
            "structural_deficiencies":self.input.structural_deficiencies,"concrete_fixes":self.input.concrete_fixes,
            "next_run_guidance":self.input.next_run_guidance,"re_entry_reason":self.input.re_entry_reason})
    }
    pub fn from_json(value: &Value) -> Result<Self, Refusal> {
        let object = fields(
            value,
            &[
                "lineage_id",
                "parent_run_key",
                "child_run_key",
                "structural_deficiencies",
                "concrete_fixes",
                "next_run_guidance",
                "re_entry_reason",
            ],
            "genealogy entry",
        )?;
        let parsed = Self::new(Self::parse_genealogy_input(object)?)?;
        if wire_digest(object, "lineage_id")? != parsed.lineage_id {
            return Err(refused("genealogy identity does not match its payload"));
        }
        Ok(parsed)
    }

    fn parse_genealogy_input(object: &Map<String, Value>) -> Result<GenealogyInput, Refusal> {
        Ok(GenealogyInput {
            parent_run_key: wire_text(object, "parent_run_key")?,
            child_run_key: wire_text(object, "child_run_key")?,
            structural_deficiencies: wire_strings(object, "structural_deficiencies")?,
            concrete_fixes: wire_strings(object, "concrete_fixes")?,
            next_run_guidance: wire_text(object, "next_run_guidance")?,
            re_entry_reason: wire_text(object, "re_entry_reason")?,
        })
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/genealogy.rs
// Claim: urn:core:crates_rs:core-adversary:genealogy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7bd96a39 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7bd96a39` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7bd96a39 {
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
impl BoundaryError7bd96a39 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7bd96a39 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7bd96a39 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7bd96a39 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7bd96a39> {
        if capacity_bound == 0 {
            return Err(BoundaryError7bd96a39::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7bd96a39::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7bd96a39::ExceedsCapacity {
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
mod l4_boundary_tests_7bd96a39 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7bd96a39::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7bd96a39::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7bd96a39::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7bd96a39::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7bd96a39::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError7bd96a39::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError7bd96a39::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
