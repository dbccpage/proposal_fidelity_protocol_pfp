//! The compiled skill catalogue: which skills have an executor, which role may
//! use which skill, and the bound skills as MCP tool definitions.
//!
//! AuthorityEffect: None. Reads a catalogue the operad compiler wrote
//! (`operads/skill_operad/json/capability_catalog.v1.json`). A licence answer
//! says the catalogue lists the skill for the role; it grants nothing.

use serde::Deserialize;
use serde_json::{json, Map, Value};

pub const CATALOG_SCHEMA: &str = "core.oewas.capability_catalog.v1";

#[derive(Debug, Deserialize)]
pub struct Executor {
    pub state: String,
    pub host_executor_id: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct Skill {
    pub skill_id: String,
    pub description: String,
    pub source_colours: Vec<String>,
    pub target_colour: String,
    pub residual_effect: String,
    pub executor: Executor,
}

#[derive(Debug, Deserialize)]
pub struct Agent {
    pub agent_id: String,
    pub licensed_skill_ids: Vec<String>,
    pub licensed_colour_ids: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct Catalog {
    pub schema_version: String,
    pub skills: Vec<Skill>,
    pub agents: Vec<Agent>,
}

impl Skill {
    pub fn is_bound(&self) -> bool {
        self.executor.state == "BOUND"
    }
}

impl Catalog {
    pub fn skill(&self, id: &str) -> Option<&Skill> {
        self.skills.iter().find(|s| s.skill_id == id)
    }

    pub fn agent(&self, id: &str) -> Option<&Agent> {
        self.agents.iter().find(|a| a.agent_id == id)
    }
}

/// Parse a catalogue; anything but the v1 schema is refused.
pub fn parse_catalog(bytes: &[u8]) -> Result<Catalog, String> {
    let catalog: Catalog =
        serde_json::from_slice(bytes).map_err(|e| format!("not a skill catalogue: {e}"))?;
    if catalog.schema_version != CATALOG_SCHEMA {
        return Err(format!(
            "catalogue schema is {:?}, expected {CATALOG_SCHEMA:?}",
            catalog.schema_version
        ));
    }
    Ok(catalog)
}

fn tally<'a>(values: impl Iterator<Item = &'a str>) -> String {
    let mut counts: Vec<(&str, usize)> = Vec::new();
    for value in values {
        match counts.iter_mut().find(|(v, _)| *v == value) {
            Some((_, n)) => *n += 1,
            None => counts.push((value, 1)),
        }
    }
    counts.sort();
    let parts: Vec<String> = counts.iter().map(|(v, n)| format!("{n} {v}")).collect();
    parts.join(", ")
}

/// A terminal summary: counts, then each bound skill and its executor.
pub fn render_summary(catalog: &Catalog) -> String {
    let bound: Vec<&Skill> = catalog.skills.iter().filter(|s| s.is_bound()).collect();
    let mut out = format!(
        "{} skills: {} bound to an executor, {} unbound.\n",
        catalog.skills.len(),
        bound.len(),
        catalog.skills.len() - bound.len()
    );
    out.push_str(&format!(
        "Residual effect: {}.\n",
        tally(catalog.skills.iter().map(|s| s.residual_effect.as_str()))
    ));
    out.push_str(&format!("{} agents.\n", catalog.agents.len()));
    if !bound.is_empty() {
        out.push_str("Bound skills:\n");
    }
    for skill in bound {
        out.push_str(&format!(
            "  {:<40} ({}) -> {}  {}  {}\n",
            skill.skill_id,
            skill.source_colours.join(", "),
            skill.target_colour,
            skill.residual_effect,
            skill.executor.host_executor_id.as_deref().unwrap_or("")
        ));
    }
    out
}

/// Whether the catalogue licenses `agent` to use `skill`.
#[derive(Debug, PartialEq, Eq)]
pub enum Licence {
    Licensed,
    /// The skill exists but is not in the agent's licence; these colours of
    /// the skill are outside the agent's colours.
    NotLicensed {
        outside: Vec<String>,
    },
    UnknownAgent,
    UnknownSkill,
}

pub fn licence(catalog: &Catalog, agent_id: &str, skill_id: &str) -> Licence {
    let Some(agent) = catalog.agent(agent_id) else {
        return Licence::UnknownAgent;
    };
    let Some(skill) = catalog.skill(skill_id) else {
        return Licence::UnknownSkill;
    };
    if agent.licensed_skill_ids.iter().any(|s| s == skill_id) {
        return Licence::Licensed;
    }
    let mut outside: Vec<String> = skill
        .source_colours
        .iter()
        .chain(std::iter::once(&skill.target_colour))
        .filter(|c| !agent.licensed_colour_ids.contains(c))
        .cloned()
        .collect();
    outside.sort();
    outside.dedup();
    Licence::NotLicensed { outside }
}

/// The bound skills as MCP tool definitions. Each input port is a property named
/// after its colour and position; the operad signature rides in `_meta`.
pub fn mcp_tools(catalog: &Catalog) -> Value {
    let tools: Vec<Value> = catalog
        .skills
        .iter()
        .filter(|s| s.is_bound())
        .map(|skill| {
            let mut properties = Map::new();
            let mut required = Vec::new();
            for (i, colour) in skill.source_colours.iter().enumerate() {
                let name = format!("{}_{}", colour.to_ascii_lowercase(), i + 1);
                properties.insert(
                    name.clone(),
                    json!({ "description": format!("Input {} (colour {colour})", i + 1) }),
                );
                required.push(Value::String(name));
            }
            json!({
                "name": skill.skill_id,
                "description": skill.description,
                "inputSchema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": false,
                },
                "annotations": {
                    "readOnlyHint": skill.residual_effect == "neutral",
                },
                "_meta": {
                    "operad": {
                        "source_colours": skill.source_colours,
                        "target_colour": skill.target_colour,
                        "residual_effect": skill.residual_effect,
                        "executor": skill.executor.host_executor_id,
                    },
                    "authority_effect": "None",
                },
            })
        })
        .collect();
    json!({ "tools": tools })
}
