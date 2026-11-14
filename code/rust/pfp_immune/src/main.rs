//! Host Immune CLI Binary (`pfp_immune`).
//!
//! Provides typed command execution for Epistemic Immune System (EIS)
//! and Prompt Civilization (PCIV) subcommands:
//! - `screen`: Thymus negative selection over self panel
//! - `decide`: Two-signal disposition check using exact rational comparisons
//! - `taint`: Lineage graph forward taint propagation with cycle refusal
//! - `select`: 60/30/10 ecological reserve partition via largest-remainder allocation
//! - `exclusion`: Multi-family consensus agreement and falsifier ordering
//!
//! AuthorityEffect: None.

use core_epistemic_immune_system::anti_skill::{AntiSkillSpecV2, FailureClass};
use core_epistemic_immune_system::thymus::{ThymusGate, ThymusVerdict};
use core_prompt_civilization::forge::PopulationPolicyV1;
use num_bigint::BigInt;
use num_rational::BigRational;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet, VecDeque};
use std::io::Read;
use std::process::ExitCode;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Outcome {
    Pass { json: String },
    Fail { json: String },
}

impl Outcome {
    pub fn json(&self) -> &str {
        match self {
            Outcome::Pass { json } => json,
            Outcome::Fail { json } => json,
        }
    }
}

// ---------------------------------------------------------------------------
// Wire Schemas
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WireRational {
    pub num: i64,
    pub den: i64,
}

// Subcommand: screen
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScreenCandidateWire {
    pub rule_id: String,
    pub pattern: String,
    pub capability_kind: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScreenInput {
    pub self_panel: Vec<String>,
    pub candidates: Vec<ScreenCandidateWire>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PurgedCandidateWire {
    pub rule_id: String,
    pub reason: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScreenOutput {
    pub status: String,
    pub admitted: Vec<String>,
    pub purged: Vec<PurgedCandidateWire>,
}

// Subcommand: decide
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DecideInput {
    pub signal1_matches: Vec<String>,
    pub danger_score: WireRational,
    pub threshold: WireRational,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DecideOutput {
    pub status: String,
    pub disposition: String,
}

// Subcommand: taint
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LineageEdgeWire {
    pub parent: String,
    pub child: String,
    pub witness: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TaintInput {
    pub edges: Vec<LineageEdgeWire>,
    pub revoked_parents: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TaintOutput {
    pub tainted_nodes: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TaintRefusalOutput {
    pub status: String,
    pub reason: String,
}

// Subcommand: select
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PopulationMemberWire {
    pub id: String,
    pub fitness: WireRational,
    pub lineage_depth: u32,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SelectInput {
    pub population: Vec<PopulationMemberWire>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SelectOutput {
    pub core_60: Vec<String>,
    pub exploratory_30: Vec<String>,
    pub novel_10: Vec<String>,
}

// Subcommand: exclusion
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExclusionInput {
    pub family_votes: BTreeMap<String, String>,
    pub hypotheses: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FalsifierWire {
    pub id: String,
    pub cost: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExclusionOutput {
    pub consensus: String,
    pub falsifiers: Vec<FalsifierWire>,
}

// ---------------------------------------------------------------------------
// Subcommand Handlers
// ---------------------------------------------------------------------------

pub fn handle_screen(payload: &str) -> Result<Outcome, String> {
    let input: ScreenInput =
        serde_json::from_str(payload).map_err(|e| format!("invalid screen input: {e}"))?;

    let gate = ThymusGate::new(input.self_panel);
    let mut admitted = Vec::new();
    let mut purged = Vec::new();

    for candidate in &input.candidates {
        let mut spec = AntiSkillSpecV2::propose(
            candidate.pattern.clone(),
            FailureClass::SemanticHallucination,
            candidate.capability_kind.clone(),
            candidate.rule_id.clone(),
            0,
        );

        match gate.screen(&mut spec) {
            ThymusVerdict::Survived { .. } => {
                admitted.push(candidate.rule_id.clone());
            }
            ThymusVerdict::SelfReactive { matched_sample, .. } => {
                purged.push(PurgedCandidateWire {
                    rule_id: candidate.rule_id.clone(),
                    reason: format!("SELF_REACTIVE: matched self sample '{matched_sample}'"),
                });
            }
            ThymusVerdict::InvalidPattern { .. } => {
                purged.push(PurgedCandidateWire {
                    rule_id: candidate.rule_id.clone(),
                    reason: "INVALID_PATTERN: regex compilation error".to_string(),
                });
            }
        }
    }

    let is_pass = purged.is_empty();
    let status = if is_pass { "PASS" } else { "FAIL" }.to_string();
    let out = ScreenOutput {
        status,
        admitted,
        purged,
    };
    let json = serde_json::to_string(&out).map_err(|e| e.to_string())?;
    if is_pass {
        Ok(Outcome::Pass { json })
    } else {
        Ok(Outcome::Fail { json })
    }
}

pub fn handle_decide(payload: &str) -> Result<Outcome, String> {
    let input: DecideInput =
        serde_json::from_str(payload).map_err(|e| format!("invalid decide input: {e}"))?;

    if input.danger_score.den == 0 || input.threshold.den == 0 {
        return Err("division by zero in rational denominator".to_string());
    }

    let danger_score = BigRational::new(
        BigInt::from(input.danger_score.num),
        BigInt::from(input.danger_score.den),
    );
    let threshold = BigRational::new(
        BigInt::from(input.threshold.num),
        BigInt::from(input.threshold.den),
    );

    let danger_present = danger_score > threshold;
    let match_present = !input.signal1_matches.is_empty();

    let (status, disposition) = match (match_present, danger_present) {
        (false, false) => (
            "PASS".to_string(),
            "no rule match and no host danger".to_string(),
        ),
        (true, false) => (
            "DIAGNOSTIC_OR_NORMALIZE".to_string(),
            "rule match without host danger: diagnostic only".to_string(),
        ),
        (false, true) => (
            "HOLD_OR_REPAIR".to_string(),
            format!(
                "host danger score {}/{} exceeds threshold {}/{}",
                input.danger_score.num,
                input.danger_score.den,
                input.threshold.num,
                input.threshold.den
            ),
        ),
        (true, true) => (
            "HOLD_OR_REPAIR".to_string(),
            format!(
                "two-signal activation: rule match and host danger score {}/{} exceeds threshold {}/{}",
                input.danger_score.num,
                input.danger_score.den,
                input.threshold.num,
                input.threshold.den
            ),
        ),
    };

    let is_pass = status == "PASS";
    let out = DecideOutput {
        status,
        disposition,
    };
    let json = serde_json::to_string(&out).map_err(|e| e.to_string())?;
    if is_pass {
        Ok(Outcome::Pass { json })
    } else {
        Ok(Outcome::Fail { json })
    }
}

fn has_directed_path(adj: &HashMap<String, Vec<String>>, from: &str, to: &str) -> bool {
    if from == to {
        return true;
    }
    let mut visited: HashSet<String> = HashSet::new();
    let mut queue: VecDeque<String> = VecDeque::new();
    queue.push_back(from.to_string());
    visited.insert(from.to_string());

    while let Some(curr) = queue.pop_front() {
        if curr == to {
            return true;
        }
        if let Some(neighbors) = adj.get(&curr) {
            for next in neighbors {
                if visited.insert(next.clone()) {
                    queue.push_back(next.clone());
                }
            }
        }
    }
    false
}

pub fn handle_taint(payload: &str) -> Result<Outcome, String> {
    let input: TaintInput =
        serde_json::from_str(payload).map_err(|e| format!("invalid taint input: {e}"))?;

    let mut adj: HashMap<String, Vec<String>> = HashMap::new();
    for edge in &input.edges {
        if edge.parent == edge.child || has_directed_path(&adj, &edge.child, &edge.parent) {
            let out = TaintRefusalOutput {
                status: "REFUSED".to_string(),
                reason: "LINEAGE_CYCLE_REFUSED: Cycle detected in inheritance DAG".to_string(),
            };
            let json = serde_json::to_string(&out).map_err(|e| e.to_string())?;
            return Ok(Outcome::Fail { json });
        }
        adj.entry(edge.parent.clone())
            .or_default()
            .push(edge.child.clone());
    }

    let mut parent_map: HashMap<String, Vec<String>> = HashMap::new();
    for edge in &input.edges {
        parent_map
            .entry(edge.child.clone())
            .or_default()
            .push(edge.parent.clone());
    }

    let mut tainted: BTreeSet<String> = input.revoked_parents.into_iter().collect();
    loop {
        let mut grown = tainted.clone();
        for (child, parents) in &parent_map {
            let tainted_parent_count = parents.iter().filter(|p| tainted.contains(*p)).count();
            if tainted_parent_count >= 1 {
                grown.insert(child.clone());
            }
        }
        if grown == tainted {
            break;
        }
        tainted = grown;
    }

    let tainted_nodes: Vec<String> = tainted.into_iter().collect();
    let out = TaintOutput { tainted_nodes };
    let json = serde_json::to_string(&out).map_err(|e| e.to_string())?;
    Ok(Outcome::Pass { json })
}

pub fn handle_select(payload: &str) -> Result<Outcome, String> {
    let input: SelectInput =
        serde_json::from_str(payload).map_err(|e| format!("invalid select input: {e}"))?;

    let population = &input.population;
    let (core_count, exploratory_count, novel_count) =
        PopulationPolicyV1::allocate_reserves(population.len());

    let mut sorted_population = population.clone();
    for member in &sorted_population {
        if member.fitness.den == 0 {
            return Err("division by zero in fitness denominator".to_string());
        }
    }
    sorted_population.sort_by(|a, b| {
        let fit_a = BigRational::new(BigInt::from(a.fitness.num), BigInt::from(a.fitness.den));
        let fit_b = BigRational::new(BigInt::from(b.fitness.num), BigInt::from(b.fitness.den));
        fit_b
            .cmp(&fit_a)
            .then_with(|| a.lineage_depth.cmp(&b.lineage_depth))
            .then_with(|| a.id.cmp(&b.id))
    });

    let ids: Vec<String> = sorted_population.into_iter().map(|m| m.id).collect();
    let core_60 = ids.iter().take(core_count).cloned().collect();
    let exploratory_30 = ids
        .iter()
        .skip(core_count)
        .take(exploratory_count)
        .cloned()
        .collect();
    let novel_10 = ids
        .iter()
        .skip(core_count + exploratory_count)
        .take(novel_count)
        .cloned()
        .collect();

    let out = SelectOutput {
        core_60,
        exploratory_30,
        novel_10,
    };
    let json = serde_json::to_string(&out).map_err(|e| e.to_string())?;
    Ok(Outcome::Pass { json })
}

pub fn handle_exclusion(payload: &str) -> Result<Outcome, String> {
    let input: ExclusionInput =
        serde_json::from_str(payload).map_err(|e| format!("invalid exclusion input: {e}"))?;

    let any_include = input.family_votes.values().any(|v| v == "INCLUDE");
    let agreeing_families: Vec<&String> = input
        .family_votes
        .iter()
        .filter(|(_, v)| v.as_str() == "EXCLUDE")
        .map(|(k, _)| k)
        .collect();

    let consensus = if any_include {
        "FRONTIER".to_string()
    } else if agreeing_families.len() >= 2 {
        "PROBABLY_DEAD".to_string()
    } else {
        "UNCORROBORATED".to_string()
    };

    let mut falsifiers: Vec<FalsifierWire> = input
        .hypotheses
        .iter()
        .map(|h| FalsifierWire {
            id: h.clone(),
            cost: 1,
        })
        .collect();
    falsifiers.sort_by(|a, b| a.cost.cmp(&b.cost).then_with(|| a.id.cmp(&b.id)));

    let out = ExclusionOutput {
        consensus,
        falsifiers,
    };
    let json = serde_json::to_string(&out).map_err(|e| e.to_string())?;
    Ok(Outcome::Pass { json })
}

// ---------------------------------------------------------------------------
// CLI Entry Point
// ---------------------------------------------------------------------------

pub const USAGE: &str = "usage: pfp_immune <screen|decide|taint|select|exclusion> [--input <file>]";

fn read_payload(source: Option<&str>) -> Result<String, String> {
    match source {
        None | Some("-") => {
            let mut buf = String::new();
            std::io::stdin()
                .read_to_string(&mut buf)
                .map_err(|e| format!("cannot read stdin: {e}"))?;
            Ok(buf)
        }
        Some(path) => {
            std::fs::read_to_string(path).map_err(|e| format!("cannot read file '{path}': {e}"))
        }
    }
}

pub fn run(args: &[&str]) -> Result<Outcome, String> {
    if args.is_empty()
        || args.contains(&"-h")
        || args.contains(&"--help")
        || args.first() == Some(&"help")
    {
        return Err(USAGE.to_string());
    }

    let subcommand = args[0];
    match subcommand {
        "screen" | "decide" | "taint" | "select" | "exclusion" => {}
        other => return Err(format!("unknown subcommand: '{other}'. {USAGE}")),
    }

    let input_source = match &args[1..] {
        [] => None,
        ["--input", file] => Some(*file),
        [file] if !file.starts_with("--") => Some(*file),
        _ => return Err(format!("invalid arguments: {:?}. {USAGE}", &args[1..])),
    };
    let payload = read_payload(input_source)?;

    match subcommand {
        "screen" => handle_screen(&payload),
        "decide" => handle_decide(&payload),
        "taint" => handle_taint(&payload),
        "select" => handle_select(&payload),
        "exclusion" => handle_exclusion(&payload),
        _ => unreachable!(),
    }
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let args_ref: Vec<&str> = args.iter().map(String::as_str).collect();
    match run(&args_ref) {
        Ok(outcome) => {
            let json = outcome.json();
            println!("{json}");
            ExitCode::from(u8::from(!matches!(outcome, Outcome::Pass { .. })))
        }
        Err(err) => {
            eprintln!("pfp_immune: {err}");
            ExitCode::from(2)
        }
    }
}
