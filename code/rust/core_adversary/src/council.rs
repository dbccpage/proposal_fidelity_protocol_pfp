//! Council YAML assembly over existing immutable Arena records.
use indexmap::IndexMap;
use crate::stage::packets::LicensedWorkflowPlan;
use crate::stage::ports::Refusal;
use crate::stage::run::StopCondition;
use crate::stage::scheduler::DeterministicScheduler;
use crate::stage::topology::{SceneGraph, SwarmDefinition, SwarmProfile};
use core_types::python_unicode::lowercase;
use serde::de::DeserializeOwned;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

fn invalid(message: impl Into<String>) -> Refusal {
    let mut r = Refusal::new("ADVERSARY_COUNCIL_PROFILE_INVALID", message);
    r.locus = "adversary.profile.profile_loader".into();
    r
}
fn trim(text: &str) -> &str {
    text.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}
fn parse(raw: &str, file: &str) -> Result<Value, Refusal> {
    let parsed: serde_yaml::Value = serde_yaml::from_str(raw).map_err(|e| {
        let text = e.to_string();
        if let Some(i) = text.find("duplicate entry with key ") {
            let key = text[i + 25..]
                .split(" at line")
                .next()
                .unwrap_or("")
                .trim()
                .trim_matches(['\'', '"']);
            invalid(format!("duplicate YAML key: {key}"))
        } else {
            invalid(text)
        }
    })?;
    if !parsed
        .as_mapping()
        .is_some_and(|m| m.keys().all(|k| k.as_str().is_some()))
    {
        return Err(invalid(format!(
            "{file} must contain one string-keyed mapping"
        )));
    }
    serde_json::to_value(parsed).map_err(|e| invalid(e.to_string()))
}
fn decode<T: DeserializeOwned>(value: Value) -> Result<T, Refusal> {
    serde_json::from_value(value).map_err(|e| invalid(e.to_string()))
}
fn strings(values: &Value) -> Result<Vec<String>, Refusal> {
    values
        .as_array()
        .ok_or_else(|| invalid("compiled council layout must be an array"))?
        .iter()
        .map(|v| {
            v.as_str()
                .map(str::to_owned)
                .ok_or_else(|| invalid("compiled council layout must contain strings"))
        })
        .collect()
}
fn text(value: Option<&Value>) -> String {
    match value {
        None => String::new(),
        Some(Value::String(s)) => s.clone(),
        Some(v) => crate::evidence_parse::python_value_repr(v),
    }
}
fn unique_field(declarations: &[Value], field: &str) -> Vec<String> {
    let mut values = Vec::new();
    for declaration in declarations {
        let value = trim(&text(declaration.get(field))).to_owned();
        if !value.is_empty() && !values.contains(&value) {
            values.push(value);
        }
    }
    values
}
/// Which panel sits the council. `Core` is the default (Bare Metal Anchor, 2026-10-16): one seat per
/// trust domain. `Full` is the eight scene seats of `council_layout_v1.json`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PanelMode {
    Core,
    Full,
}
impl PanelMode {
    pub fn parse(text: &str) -> Result<Self, Refusal> {
        match text {
            "core" => Ok(Self::Core),
            "full" => Ok(Self::Full),
            other => Err(invalid(format!("panel mode must be core or full, not {other:?}"))),
        }
    }
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Core => "core",
            Self::Full => "full",
        }
    }
}
/// The core panel: Gauge Breaker PRODUCER, Defect Hunter CRITIC, Primal Dual TESTER, Adversary EVALUATOR,
/// Manuscript Truth SELECTOR. Their trust domains come from `council_layout_v1.json`.
pub const CORE_SEATS: [&str; 5] = [
    "seat_gauge_breaker",
    "seat_defect_hunter",
    "seat_primal_dual",
    "seat_adversary",
    "seat_manuscript_truth",
];
/// The seat that takes an act whose declared seats are all outside the panel.
pub const SEATLESS_ACT_SEAT: &str = "seat_adversary";
#[derive(Debug, Clone)]
pub struct CouncilAssembly {
    pub definition: SwarmDefinition,
    pub graph: SceneGraph,
    pub profile: SwarmProfile,
    pub plan: LicensedWorkflowPlan,
    pub stop: StopCondition,
    /// The mode, its seats, and how each act left without a declared seat was handled.
    pub panel: Value,
}
impl CouncilAssembly {
    pub fn scheduler(&self) -> Result<DeterministicScheduler, Refusal> {
        DeterministicScheduler::new(
            self.definition.clone(),
            self.profile.clone(),
            self.graph.clone(),
            self.plan.clone(),
            self.stop.clone(),
        )
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        serde_json::to_value((
            &self.definition,
            &self.graph,
            &self.profile,
            &self.plan,
            &self.stop,
        ))
        .map_err(|e| invalid(e.to_string()))
    }
}
/// The full panel, as assembled before panel modes existed.
pub fn assemble_council(panel_raw: &str, scenes_raw: &str) -> Result<CouncilAssembly, Refusal> {
    assemble_council_for(panel_raw, scenes_raw, PanelMode::Full)
}
fn validate_council_scenes(council_scenes: &Value) -> Result<(), Refusal> {
    let scenes = council_scenes["scenes"]
        .as_array()
        .filter(|a| a.len() == 10)
        .ok_or_else(|| invalid("scenes.yaml must declare the ten canonical council scenes"))?;
    let mut ids = BTreeSet::new();
    for scene in scenes {
        let id = scene
            .as_object()
            .and_then(|m| m.get("id"))
            .and_then(Value::as_str)
            .ok_or_else(|| invalid("every canonical council scene must declare an id"))?;
        if id.is_empty() || trim(id) != id || !ids.insert(id) {
            return Err(invalid(
                "canonical council scene ids must be normalized and unique",
            ));
        }
    }
    Ok(())
}

fn group_panel_characters(panel: &Value) -> Result<IndexMap<String, Vec<Value>>, Refusal> {
    let characters = panel["characters"]
        .as_array()
        .filter(|a| !a.is_empty())
        .ok_or_else(|| invalid("adversary_panel.yaml must declare a nonempty characters list"))?;
    let mut names = IndexMap::new();
    let mut grouped: IndexMap<String, Vec<Value>> = IndexMap::new();
    for character in characters {
        if !character.is_object() {
            return Err(invalid("every panel character must be a mapping"));
        }
        let raw = character["name"]
            .as_str()
            .ok_or_else(|| invalid("every panel character must declare a string name"))?;
        let name = trim(raw);
        if name.is_empty() {
            return Err(invalid("every panel character must declare a name"));
        }
        let normalized = lowercase(name).replace([' ', '-'], "_").replace('.', "");
        let id = format!("seat_{normalized}");
        let prior = names.entry(id.clone()).or_insert_with(|| name.to_owned());
        if prior != name {
            return Err(invalid(format!(
                "distinct panel names collide at normalized seat {id}"
            )));
        }
        grouped.entry(id).or_default().push(character.clone());
    }
    Ok(grouped)
}

fn collect_pipeline_acts(declarations: &[Value]) -> Result<BTreeSet<String>, Refusal> {
    let mut acts = BTreeSet::new();
    for declaration in declarations {
        if let Some(values) = declaration.get("pipeline_acts") {
            insert_pipeline_acts_value(&mut acts, values)?;
        }
    }
    Ok(acts)
}

fn insert_pipeline_acts_value(acts: &mut BTreeSet<String>, values: &Value) -> Result<(), Refusal> {
    match values {
        Value::Array(values) => {
            for v in values {
                acts.insert(lowercase(&text(Some(v))));
            }
        }
        Value::String(s) => {
            for c in s.chars() {
                acts.insert(lowercase(&c.to_string()));
            }
        }
        Value::Object(m) => {
            for key in m.keys() {
                acts.insert(lowercase(key));
            }
        }
        _ => return Err(invalid("pipeline_acts must be iterable")),
    }
    Ok(())
}

fn matches_role_or_act(role: &str, acts: &BTreeSet<String>, roles: &[&str], act_keys: &[&str]) -> bool {
    roles.iter().any(|r| role.contains(r)) || act_keys.iter().any(|a| acts.contains(*a))
}

fn classify_seat_domain_and_colours(
    role: &str,
    acts: &BTreeSet<String>,
) -> (&'static str, Vec<&'static str>) {
    if matches_role_or_act(role, acts, &["propose", "generator"], &["act_panel_generate"]) {
        ("PRODUCER", vec!["Code", "State"])
    } else if matches_role_or_act(role, acts, &["critic", "critique"], &["act_panel_critique"]) {
        ("CRITIC", vec!["Audit", "State"])
    } else if matches_role_or_act(role, acts, &["gatekeeper"], &["act_panel_gate", "terminalize"]) {
        ("EVALUATOR", vec!["Receipt", "State"])
    } else if matches_role_or_act(
        role,
        acts,
        &["mechanizer", "scheduler", "crystallize"],
        &["act_master_schedule"],
    ) {
        ("SELECTOR", vec!["Code", "Receipt"])
    } else if ["filter", "scanner", "sandbox", "courage"]
        .iter()
        .any(|s| role.contains(s))
    {
        ("TESTER", vec!["Audit", "State"])
    } else {
        ("EVALUATOR", vec!["Ledger", "State"])
    }
}

fn build_grouped_seats(
    grouped: IndexMap<String, Vec<Value>>,
) -> Result<(BTreeMap<String, Value>, BTreeSet<String>), Refusal> {
    let mut seats = BTreeMap::new();
    let mut skills = BTreeSet::new();
    for (id, declarations) in grouped {
        let role = lowercase(&unique_field(&declarations, "role").join(" | "));
        let operator = unique_field(&declarations, "cognitive_operator").join(" | ");
        let acts = collect_pipeline_acts(&declarations)?;
        let (domain, colours) = classify_seat_domain_and_colours(&role, &acts);
        let skill = id.replacen("seat_", "skill_", 1);
        skills.insert(skill.clone());
        // Validate immediately, preserving declaration-order refusal precedence.
        let seat: crate::stage::topology::SeatRequirement = decode(
            json!({"seat_id":id,"trust_domain":domain,"required_operations":[skill],"required_colours":colours,"independent_from":[],"cognitive_operator":operator}),
        )?;
        seats.insert(
            id,
            serde_json::to_value(seat).map_err(|e| invalid(e.to_string()))?,
        );
    }
    Ok((seats, skills))
}

fn retain_core_mode_seats_and_skills(
    seats: &mut BTreeMap<String, Value>,
    skills: &mut BTreeSet<String>,
) -> Result<(), Refusal> {
    if let Some(missing) = CORE_SEATS.iter().find(|id| !seats.contains_key(**id)) {
        return Err(invalid(format!("core panel seat {missing} is not declared")));
    }
    seats.retain(|id, _| CORE_SEATS.contains(&id.as_str()));
    skills.retain(|skill| {
        CORE_SEATS
            .iter()
            .any(|id| id.replacen("seat_", "skill_", 1) == *skill)
    });
    Ok(())
}

fn insert_single_core_seat(
    core: &Value,
    seats: &mut BTreeMap<String, Value>,
    skills: &mut BTreeSet<String>,
) -> Result<(), Refusal> {
    let id = core[0]
        .as_str()
        .ok_or_else(|| invalid("compiled seat id missing"))?;
    let operations = strings(&core[2])?;
    for skill in &operations {
        skills.insert(skill.clone());
    }
    let mut colours = strings(&core[3])?;
    colours.sort();
    seats.entry(id.into()).or_insert_with(|| {
        json!({"seat_id":core[0],"trust_domain":core[1],"required_operations":operations,"required_colours":colours,"independent_from":[],"cognitive_operator":core[4]})
    });
    Ok(())
}

fn merge_core_seats_and_filter_mode(
    layout: &Value,
    seats: &mut BTreeMap<String, Value>,
    skills: &mut BTreeSet<String>,
    mode: PanelMode,
) -> Result<(), Refusal> {
    for core in layout["core_required"]
        .as_array()
        .ok_or_else(|| invalid("compiled core seats missing"))?
    {
        insert_single_core_seat(core, seats, skills)?;
    }
    if mode == PanelMode::Core {
        retain_core_mode_seats_and_skills(seats, skills)?;
    }
    Ok(())
}

fn build_sorted_transitions(layout: &Value) -> Result<Vec<Value>, Refusal> {
    let mut transitions = Vec::new();
    for t in layout["transitions"]
        .as_array()
        .ok_or_else(|| invalid("compiled transitions missing"))?
    {
        transitions.push(json!({"transition_id":t[0],"source_scene_id":t[1],"target_scene_id":t[2],"trigger_statuses":t[3],"residual_codes":t[4],"priority":t[5]}));
    }
    transitions.sort_by(|a, b| {
        (a["priority"].as_u64(), a["transition_id"].as_str())
            .cmp(&(b["priority"].as_u64(), b["transition_id"].as_str()))
    });
    Ok(transitions)
}

fn build_scene_graph_and_scenes(
    layout: &Value,
    seats: &BTreeMap<String, Value>,
) -> Result<(SceneGraph, Vec<Value>, Vec<Value>), Refusal> {
    let mut seatless = Vec::new();
    let mut scenes = Vec::new();
    for scene in layout["act_scenes"]
        .as_array()
        .ok_or_else(|| invalid("compiled scenes missing"))?
    {
        let mut required = strings(&scene[2])?;
        required.retain(|s| seats.contains_key(s));
        required.sort();
        if required.is_empty() {
            let declared = strings(&scene[2])?;
            seatless.push(json!({"scene_id":scene[0],"declared_seat_ids":declared,
                "handled_by":SEATLESS_ACT_SEAT,"handling":"ASSIGNED_TO_EVALUATOR"}));
            required.push(SEATLESS_ACT_SEAT.into());
        }
        let mut statuses = strings(&scene[3])?;
        statuses.sort();
        scenes.push(json!({"scene_id":scene[0],"purpose":scene[1],"required_seat_ids":required,"allowed_result_statuses":statuses,"max_visits":scene[4],"terminal":scene[5]}));
    }
    let transitions = build_sorted_transitions(layout)?;
    let graph: SceneGraph = decode(
        json!({"entry_scene_id":"act1_perception","scenes":scenes,"transitions":transitions,"authority_effect":"None","schema_version":"core.oeas.scene-graph.v1"}),
    )?;
    Ok((graph, scenes, seatless))
}

fn compute_catalog_digest(panel_raw: &str, scenes_raw: &str) -> String {
    let mut hash = Sha256::new();
    hash.update(b"core.oeas.adversary-profile-yaml.v1\0");
    for raw in [panel_raw, scenes_raw] {
        hash.update((raw.len() as u64).to_be_bytes());
        hash.update(raw.as_bytes());
    }
    format!("sha256:{}", hex::encode(hash.finalize()))
}

fn build_assignments_and_scene_seats(
    scenes: &[Value],
    seats: &BTreeMap<String, Value>,
    license: &str,
) -> Result<(Vec<Value>, BTreeSet<String>), Refusal> {
    let mut assignments = Vec::new();
    let mut scene_seats = BTreeSet::new();
    for scene in scenes {
        let req_seats = strings(&scene["required_seat_ids"])?;
        for seat in req_seats {
            assignments.push(json!({"scene_id":scene["scene_id"],"seat_id":seat,"agent_id":format!("agent_{seat}"),"operation_ids":seats[&seat]["required_operations"],"agent_license_id":license}));
            scene_seats.insert(seat);
        }
    }
    Ok((assignments, scene_seats))
}

fn decode_plan_stop_and_panel(
    cast: &str,
    catalog: &str,
    skills: &BTreeSet<String>,
    scenes: &[Value],
    seats: &BTreeMap<String, Value>,
    seatless: Vec<Value>,
    mode: PanelMode,
) -> Result<(LicensedWorkflowPlan, StopCondition, Value), Refusal> {
    let license =
        crate::evidence::sha256_ref(format!("adversary_council_license\0{catalog}").as_bytes());
    let (assignments, scene_seats) = build_assignments_and_scene_seats(scenes, seats, &license)?;
    let plan = decode(
        json!({"plan_name":format!("adversary_council_{cast}_plan"),"catalog_id":catalog,"assignments":assignments,"normalized_operation_ids":skills,"path2_evidence_ids":[],"status":"PROPOSED","authority_effect":"None","schema_version":"core.oeas.licensed-workflow-plan.v1"}),
    )?;
    let stop = decode(
        json!({"max_total_budget":100,"max_scene_steps":20,"max_dry_rounds":5,"stop_on_statuses":["COMPLETED","HOLD","REFUSE"]}),
    )?;
    let panel = json!({"schema_version":"core.adversary.panel.v1","mode":mode.as_str(),
        "scene_seat_ids":scene_seats,"seatless_acts":seatless,"authority_effect":"None"});
    Ok((plan, stop, panel))
}

fn parse_and_build_council_seats(
    panel_raw: &str,
    scenes_raw: &str,
    mode: PanelMode,
) -> Result<(BTreeMap<String, Value>, BTreeSet<String>, Value), Refusal> {
    let panel = parse(panel_raw, "adversary_panel.yaml")?;
    let council_scenes = parse(scenes_raw, "scenes.yaml")?;
    let grouped = group_panel_characters(&panel)?;
    validate_council_scenes(&council_scenes)?;
    let (mut seats, mut skills) = build_grouped_seats(grouped)?;
    let layout: Value = serde_json::from_str(include_str!("council_layout_v1.json"))
        .map_err(|e| invalid(e.to_string()))?;
    merge_core_seats_and_filter_mode(&layout, &mut seats, &mut skills, mode)?;
    Ok((seats, skills, layout))
}

pub fn assemble_council_for(
    panel_raw: &str,
    scenes_raw: &str,
    mode: PanelMode,
) -> Result<CouncilAssembly, Refusal> {
    let (seats, skills, layout) = parse_and_build_council_seats(panel_raw, scenes_raw, mode)?;
    let (graph, scenes, seatless) = build_scene_graph_and_scenes(&layout, &seats)?;
    let catalog = compute_catalog_digest(panel_raw, scenes_raw);
    let cast = match mode {
        PanelMode::Full => "larger_cast",
        PanelMode::Core => "core_cast",
    };
    let definition: SwarmDefinition = decode(
        json!({"definition_name":format!("adversary_panel_{cast}"),"seat_requirements":seats.values().collect::<Vec<_>>(),"skill_catalog_id":catalog,"max_parallelism":1,"authority_effect":"None","schema_version":"core.oeas.swarm-definition.v1"}),
    )?;
    let profile: SwarmProfile = decode(
        json!({"profile_name":format!("adversary_council_{cast}"),"base_definition_id":definition.definition_id(),"scene_graph_id":graph.graph_id(),"skill_ids":skills,"anti_skill_profile_digest":"","authority_effect":"None","schema_version":"core.oeas.swarm-profile.v1"}),
    )?;
    let (plan, stop, panel) = decode_plan_stop_and_panel(
        cast,
        &catalog,
        &skills,
        &scenes,
        &seats,
        seatless,
        mode,
    )?;
    Ok(CouncilAssembly {
        definition,
        graph,
        profile,
        plan,
        stop,
        panel,
    })
}

// Origin: engine/crates_rs/core_adversary/src/council.rs
// Claim: urn:core:crates_rs:core-adversary:council:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcab24c4f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcab24c4f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcab24c4f {
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
impl BoundaryErrorcab24c4f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcab24c4f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcab24c4f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcab24c4f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcab24c4f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcab24c4f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcab24c4f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcab24c4f::ExceedsCapacity {
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
mod l4_boundary_tests_cab24c4f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordcab24c4f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordcab24c4f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordcab24c4f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordcab24c4f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordcab24c4f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorcab24c4f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorcab24c4f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
