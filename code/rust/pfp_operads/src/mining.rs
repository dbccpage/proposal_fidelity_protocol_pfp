//! The mining screen of the pre-mining workflows, and signature reuse between two candidate lists.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:mining:v1
//!
//! A mining reply proposes operad candidates and guidance before any solver runs. The screen
//! refuses a reply that carries a digit outside a source quote (it may be leaking an answer), a
//! candidate that is malformed or ungrounded, or guidance that does not cover the task's grounded
//! slots. The rules, their codes and their order are those the workflows applied before.
//!
//! A screened candidate is still unverified: the screen reads its form, not its meaning.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::sync::LazyLock;

use regex::Regex;
use serde::de::{MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::value::RawValue;
use serde_json::Value as Json;

use crate::envelope::{typings, Candidate, Quote, TASK_RESULT};
use crate::grounding::grounded_slots;
use crate::Refusal;

/// A decimal digit in any script, as the earlier host's `\d` read it.
static DIGIT: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\d").expect("a fixed pattern"));

/// How serde_json hands over a number when another crate in the build turns on arbitrary
/// precision. The mining reply schema is closed, so no reply key can have this name.
const NUMBER_TOKEN: &str = "$serde_json::private::Number";

/// A reply value in document order. Only text is read; numbers, booleans and null are `Other`.
enum Node {
    Text(String),
    List(Vec<Node>),
    Map(Vec<(String, Node)>),
    Other,
}

struct NodeVisitor;

impl<'de> Visitor<'de> for NodeVisitor {
    type Value = Node;

    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        formatter.write_str("a JSON value")
    }

    fn visit_str<E>(self, text: &str) -> Result<Node, E> {
        Ok(Node::Text(text.to_owned()))
    }

    fn visit_bool<E>(self, _: bool) -> Result<Node, E> {
        Ok(Node::Other)
    }

    fn visit_i64<E>(self, _: i64) -> Result<Node, E> {
        Ok(Node::Other)
    }

    fn visit_u64<E>(self, _: u64) -> Result<Node, E> {
        Ok(Node::Other)
    }

    fn visit_f64<E>(self, _: f64) -> Result<Node, E> {
        Ok(Node::Other)
    }

    fn visit_unit<E>(self) -> Result<Node, E> {
        Ok(Node::Other)
    }

    fn visit_seq<A: SeqAccess<'de>>(self, mut items: A) -> Result<Node, A::Error> {
        let mut list = Vec::new();
        while let Some(item) = items.next_element()? {
            list.push(item);
        }
        Ok(Node::List(list))
    }

    fn visit_map<A: MapAccess<'de>>(self, mut entries: A) -> Result<Node, A::Error> {
        let mut map = Vec::new();
        while let Some(entry) = entries.next_entry::<String, Node>()? {
            map.push(entry);
        }
        match map.as_slice() {
            [(key, _)] if key == NUMBER_TOKEN => Ok(Node::Other),
            _ => Ok(Node::Map(map)),
        }
    }
}

impl<'de> Deserialize<'de> for Node {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        deserializer.deserialize_any(NodeVisitor)
    }
}

/// Every text with a digit, in document order, except the quote of a source.
fn digit_errors(node: &Node, path: &mut Vec<String>, errors: &mut Vec<String>) {
    match node {
        Node::Text(text) => {
            let quoted = matches!(path.as_slice(), [.., a, b] if a == "source" && b == "quote");
            if !quoted && DIGIT.is_match(text) {
                errors.push(format!("NUMERICAL_GUIDANCE_FORBIDDEN:{}", path.join("/")));
            }
        }
        Node::List(items) => {
            for (index, item) in items.iter().enumerate() {
                path.push(index.to_string());
                digit_errors(item, path, errors);
                path.pop();
            }
        }
        Node::Map(entries) => {
            for (key, value) in entries {
                path.push(key.clone());
                digit_errors(value, path, errors);
                path.pop();
            }
        }
        Node::Other => {}
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Guidance {
    slot: String,
    source: Quote,
    #[serde(rename = "guidance")]
    _guidance: String,
}

/// The two record lists the screen types. The digit screen reads the whole answer.
#[derive(Deserialize)]
struct Answer {
    operad_candidates: Vec<Candidate>,
    l2_guidance: Vec<Guidance>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request<'a> {
    /// Every slot id of the pinned catalogue.
    catalogue: Vec<String>,
    /// The texts a candidate or a guidance row may quote, by kind.
    sources: BTreeMap<String, String>,
    /// The task's checker; it decides the grounded slots and the licensed operations.
    checker: String,
    #[serde(borrow)]
    answer: &'a RawValue,
}

/// One mined candidate, in reply order.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MinedCandidate {
    pub id: String,
    /// Where the candidate sits in the reply.
    pub pointer: String,
    /// The pointer of the first candidate equal to this one in every field, if there is one.
    pub duplicate_of: Option<String>,
    pub typed: bool,
    pub licensed_as: Option<&'static str>,
}

/// The host's reading of one mining reply.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct MiningReport {
    pub accepted: bool,
    pub errors: Vec<String>,
    pub candidates: Vec<MinedCandidate>,
}

fn candidate_errors(request: &Request, candidates: &[Candidate], errors: &mut Vec<String>) {
    let ids: BTreeSet<&str> = candidates.iter().map(|op| op.id.as_str()).collect();
    if ids.len() != candidates.len() {
        errors.push("DUPLICATE_MINED_OPERAD_ID".to_owned());
    }
    for op in candidates {
        if !op.arity_agrees() {
            errors.push(format!("MINED_ARITY_MISMATCH:{}", op.id));
        }
        if !op.source.found_in(&request.sources) {
            errors.push(format!("MINED_SOURCE_QUOTE_MISSING:{}", op.id));
        }
        let known = |name: &String| name == TASK_RESULT || request.catalogue.contains(name);
        if !op.witness_refs.iter().all(known) {
            errors.push(format!("MINED_WITNESS_REF_UNKNOWN:{}", op.id));
        }
    }
}

fn guidance_errors(request: &Request, guidance: &[Guidance], errors: &mut Vec<String>) {
    let slots: BTreeSet<&str> = guidance.iter().map(|row| row.slot.as_str()).collect();
    if slots.len() != guidance.len() {
        errors.push("DUPLICATE_L2_GUIDANCE_SLOT".to_owned());
    }
    let grounded = grounded_slots(&request.checker);
    if !grounded.is_empty() && !slots.iter().eq(grounded.iter()) {
        errors.push("MISSING_TASK_L2_GUIDANCE".to_owned());
    }
    for row in guidance {
        if !row.source.found_in(&request.sources) {
            errors.push(format!("L2_SOURCE_QUOTE_MISSING:{}", row.slot));
        }
    }
}

fn pointer(index: usize) -> String {
    format!("/answer/operad_candidates/{index}")
}

/// Screen one mining reply: the digit screen, then candidates, then guidance.
pub fn mining(text: &str) -> Result<MiningReport, Refusal> {
    let bad = |error: serde_json::Error| Refusal::new("BAD_REQUEST", error.to_string());
    let request: Request = serde_json::from_str(text).map_err(bad)?;
    let tree: Node = serde_json::from_str(request.answer.get()).map_err(bad)?;
    let answer: Answer = serde_json::from_str(request.answer.get()).map_err(bad)?;
    let mut errors = Vec::new();
    digit_errors(&tree, &mut Vec::new(), &mut errors);
    candidate_errors(&request, &answer.operad_candidates, &mut errors);
    guidance_errors(&request, &answer.l2_guidance, &mut errors);
    let ops = &answer.operad_candidates;
    let candidates = ops
        .iter()
        .zip(typings(ops, &request.checker)?)
        .enumerate()
        .map(|(index, (op, typing))| MinedCandidate {
            id: typing.id,
            pointer: pointer(index),
            duplicate_of: ops
                .iter()
                .take(index)
                .position(|earlier| earlier == op)
                .map(pointer),
            typed: typing.typed,
            licensed_as: typing.licensed_as,
        })
        .collect();
    Ok(MiningReport {
        accepted: errors.is_empty(),
        errors,
        candidates,
    })
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ReuseRequest {
    mined: Vec<Json>,
    emitted: Vec<Json>,
}

/// The emitted candidates whose signature one of the mined candidates also has.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ReuseReport {
    pub reused: Vec<String>,
}

/// Source colours, target colour and arity, if the record states all three in their types.
fn signature(op: &Json) -> Option<(Vec<&str>, &str, i128)> {
    let sources: Option<Vec<&str>> = op
        .get("source_colours")?
        .as_array()?
        .iter()
        .map(Json::as_str)
        .collect();
    let arity = op.get("arity")?;
    let arity = arity
        .as_i64()
        .map(i128::from)
        .or_else(|| arity.as_u64().map(i128::from))?;
    Some((sources?, op.get("target_colour")?.as_str()?, arity))
}

/// List the emitted candidates that reuse a mined signature, in the order emitted.
pub fn reuse(text: &str) -> Result<ReuseReport, Refusal> {
    let request: ReuseRequest = serde_json::from_str(text)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    let mined: BTreeSet<_> = request.mined.iter().filter_map(signature).collect();
    let reused = request
        .emitted
        .iter()
        .filter(|op| signature(op).is_some_and(|found| mined.contains(&found)))
        .filter_map(|op| op.get("id")?.as_str())
        .map(str::to_owned)
        .collect();
    Ok(ReuseReport { reused })
}
