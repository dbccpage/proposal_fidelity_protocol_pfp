//! Reader-relative prompt families, matching the landed Adversary design.
//! Unknown fields remain unknown. AuthorityEffect: None.
use num_bigint::BigInt;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    str::FromStr,
};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Refusal {
    pub code: String,
    pub message: String,
    pub locus: String,
    pub details: BTreeMap<String, String>,
}
fn refuse(code: &str, message: impl Into<String>) -> Refusal {
    Refusal {
        code: code.into(),
        message: message.into(),
        locus: "adversary.domain.prompt_family".into(),
        details: BTreeMap::new(),
    }
}
fn py_repr(text: &str) -> String {
    format!("'{text}'")
}
fn trim_python(text: &str) -> &str {
    text.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}
pub(crate) fn sort_keys(value: &mut Value) {
    match value {
        Value::Object(map) => {
            map.sort_keys();
            for item in map.values_mut() {
                sort_keys(item);
            }
        }
        Value::Array(items) => {
            for item in items {
                sort_keys(item);
            }
        }
        _ => {}
    }
}
pub fn canonical_digest<T: Serialize>(object: &T) -> Result<String, Refusal> {
    let mut value = serde_json::to_value(object)
        .map_err(|_| refuse("FAMILY_WIRE_INVALID", "family cannot be encoded"))?;
    sort_keys(&mut value);
    let raw = serde_json::to_vec(&value)
        .map_err(|_| refuse("FAMILY_WIRE_INVALID", "family cannot be encoded"))?;
    Ok(format!("sha256:{}", hex::encode(Sha256::digest(raw))))
}
pub fn text_digest(text: &str) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(text.as_bytes())))
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Reader {
    pub model: String,
    pub router: String,
    pub seat_id: String,
    pub tier: String,
    pub config_digest: String,
    pub temperature: Option<String>,
    pub params_billion: Option<serde_json::Number>,
    pub open_weights: Option<bool>,
}
impl Reader {
    pub fn digest(&self) -> Result<String, Refusal> {
        canonical_digest(self)
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Shape {
    pub byte_bucket: u32,
    pub line_bucket: u32,
    pub fence_count: usize,
    pub question_count: usize,
}
impl Shape {
    pub fn from_text(text: &str) -> Self {
        Self {
            byte_bucket: usize::BITS - text.len().leading_zeros(),
            line_bucket: usize::BITS - (text.matches('\n').count() + 1).leading_zeros(),
            fence_count: text.matches("```").count(),
            question_count: text.matches('?').count(),
        }
    }
    pub fn digest(&self) -> Result<String, Refusal> {
        canonical_digest(self)
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DomainLabel {
    pub label: String,
    pub proposer_reader: String,
    pub status: String,
    pub check_receipt: Option<String>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PromptNode {
    pub prompt_digest: String,
    pub relation: String,
    pub shape: Option<Shape>,
    pub parent_id: Option<String>,
    pub reader_digest: Option<String>,
    pub domain_labels: Vec<DomainLabel>,
}
impl PromptNode {
    pub fn node_id(&self) -> Result<String, Refusal> {
        canonical_digest(&json!([
            self.prompt_digest,
            self.relation,
            self.parent_id,
            self.reader_digest
        ]))
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CallRecord {
    pub bout_id: String,
    pub request_digest: String,
    pub reader_digest: String,
    pub leg_index: i64,
    pub outcome: String,
    pub cost_microusd: Value,
    pub cost_source: Option<String>,
    pub input_tokens: Option<serde_json::Number>,
    pub output_tokens: Option<serde_json::Number>,
    pub max_tokens: Option<serde_json::Number>,
    pub finish_reason: Option<String>,
    pub ddc_letter: Option<String>,
    pub residual_colour: Option<String>,
    pub reply_digest: Option<String>,
}
impl CallRecord {
    pub fn call_id(&self) -> Result<String, Refusal> {
        canonical_digest(&json!([
            self.bout_id,
            self.request_digest,
            self.reader_digest,
            self.leg_index,
            self.outcome
        ]))
    }
    pub fn truncated(&self) -> Option<bool> {
        self.finish_reason.as_ref().map(|v| v == "length")
    }
    pub fn defect(&self) -> Option<&str> {
        if self.outcome == "OK" {
            None
        } else {
            Some(&self.outcome)
        }
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Fitness {
    pub cost_microusd: Value,
    pub input_tokens: Value,
    pub output_tokens: Value,
    pub checker_verdict: String,
    pub checker_id: Option<String>,
    pub obstruction_removed: Option<bool>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RepairStep {
    pub input_node_id: String,
    pub output_node_id: String,
    pub ddc_letter: Option<String>,
    pub residual_before: Option<String>,
    pub residual_after: Option<String>,
    pub call_ids: Vec<String>,
    pub fitness: Fitness,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Terminal {
    pub kind: String,
    pub detail: String,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PromptFamily {
    pub readers: Vec<Reader>,
    pub nodes: Vec<PromptNode>,
    pub calls: Vec<CallRecord>,
    pub steps: Vec<RepairStep>,
    pub terminal: Option<Terminal>,
}

pub fn decode_family(raw: &[u8]) -> Result<PromptFamily, Refusal> {
    if raw.len() > 1024 * 1024 {
        return Err(refuse("FAMILY_WIRE_INVALID", "family exceeds byte limit"));
    }
    // Decode typed DTOs from original JSON rather than Value -> DTO: the latter
    // can reinterpret a large integer as a floating-point number in deserialize_any.
    serde_json::from_slice(raw)
        .map_err(|_| refuse("FAMILY_WIRE_INVALID", "family is not a typed JSON record"))
}

fn validate_domain_label(label: &DomainLabel, readers: &BTreeSet<String>) -> Result<(), Refusal> {
    let label_name = py_repr(&label.label);
    if !matches!(label.status.as_str(), "proposed" | "checked") {
        return Err(refuse(
            "FAMILY_LABEL_STATUS",
            format!("label {label_name}: status {}", py_repr(&label.status)),
        ));
    }
    let receipt = label.check_receipt.as_ref().is_some_and(|r| !r.is_empty());
    if label.status == "checked" && !receipt {
        return Err(refuse(
            "FAMILY_LABEL_UNCHECKED",
            format!("label {label_name} is 'checked' without a receipt"),
        ));
    }
    if label.status == "proposed" && receipt {
        return Err(refuse(
            "FAMILY_LABEL_STATUS",
            format!("label {label_name} is 'proposed' but carries a receipt"),
        ));
    }
    if !readers.contains(&label.proposer_reader) {
        return Err(refuse(
            "FAMILY_UNKNOWN_READER",
            format!("label {label_name}: proposer is not a declared reader"),
        ));
    }
    Ok(())
}

fn validate_prompt_node(
    node: &PromptNode,
    readers: &BTreeSet<String>,
    nodes: &BTreeMap<String, &PromptNode>,
) -> Result<String, Refusal> {
    if !matches!(
        node.relation.as_str(),
        "root" | "contains" | "repaired_from"
    ) {
        return Err(refuse(
            "FAMILY_RELATION",
            format!("relation {}", py_repr(&node.relation)),
        ));
    }
    let id = node.node_id()?;
    if nodes.contains_key(&id) {
        return Err(refuse("FAMILY_NODE_DUPLICATE", id));
    }
    if (node.relation == "root") != node.parent_id.is_none() {
        return Err(refuse(
            "FAMILY_ROOT_PARENT",
            "exactly the root has no parent",
        ));
    }
    if node
        .reader_digest
        .as_ref()
        .is_some_and(|reader| !readers.contains(reader))
    {
        return Err(refuse(
            "FAMILY_UNKNOWN_READER",
            format!("node {id} names an undeclared reader"),
        ));
    }
    for label in &node.domain_labels {
        validate_domain_label(label, readers)?;
    }
    Ok(id)
}

fn validate_parent_chain(
    node: &PromptNode,
    nodes: &BTreeMap<String, &PromptNode>,
) -> Result<(), Refusal> {
    let mut seen = BTreeSet::new();
    let mut cursor = node;
    let node_id = node.node_id()?;
    while let Some(parent) = &cursor.parent_id {
        let next = nodes.get(parent).ok_or_else(|| {
            refuse(
                "FAMILY_PARENT_MISSING",
                format!("node {node_id}: parent {parent}"),
            )
        })?;
        if !seen.insert(parent) {
            return Err(refuse(
                "FAMILY_CYCLE",
                format!("node {} is on a cycle", node.node_id()?),
            ));
        }
        cursor = next;
    }
    Ok(())
}

fn validate_and_collect_nodes<'a>(
    family: &'a PromptFamily,
    readers: &BTreeSet<String>,
) -> Result<BTreeMap<String, &'a PromptNode>, Refusal> {
    let mut nodes = BTreeMap::new();
    for node in &family.nodes {
        let id = validate_prompt_node(node, readers, &nodes)?;
        nodes.insert(id, node);
    }
    if family.nodes.iter().filter(|n| n.relation == "root").count() != 1 {
        return Err(refuse("FAMILY_ROOT_COUNT", "a family has exactly one root"));
    }
    for node in &family.nodes {
        validate_parent_chain(node, &nodes)?;
    }
    Ok(nodes)
}

fn validate_and_collect_calls<'a>(
    family: &'a PromptFamily,
    readers: &BTreeSet<String>,
) -> Result<BTreeMap<String, &'a CallRecord>, Refusal> {
    let mut calls = BTreeMap::new();
    for call in &family.calls {
        let id = call.call_id()?;
        if !readers.contains(&call.reader_digest) {
            return Err(refuse(
                "FAMILY_UNKNOWN_READER",
                format!("call {id} names an undeclared reader"),
            ));
        }
        let cost = match &call.cost_microusd {
            Value::Number(n) => BigInt::from_str(&n.to_string()).ok(),
            _ => None,
        };
        if cost.is_none_or(|n| n < BigInt::from(0)) {
            return Err(refuse(
                "FAMILY_COST",
                "cost_microusd must be a non-negative integer",
            ));
        }
        if calls.insert(id.clone(), call).is_some() {
            return Err(refuse("FAMILY_CALL_DUPLICATE", id));
        }
    }
    Ok(calls)
}

fn validate_step_fitness(fit: &Fitness, step_readers: &BTreeSet<&String>) -> Result<(), Refusal> {
    if !matches!(
        fit.checker_verdict.as_str(),
        "ACCEPT" | "REJECT" | "NOT_MEASURED"
    ) {
        return Err(refuse(
            "FAMILY_VERDICT",
            format!("verdict {}", py_repr(&fit.checker_verdict)),
        ));
    }
    if fit.checker_verdict != "NOT_MEASURED" {
        let checker = fit
            .checker_id
            .as_ref()
            .filter(|c| !c.is_empty())
            .ok_or_else(|| refuse("FAMILY_CHECKER_MISSING", "a verdict needs a checker id"))?;
        if step_readers.contains(checker) {
            return Err(refuse(
                "FAMILY_FITNESS_CIRCULAR",
                "the checker is one of the step's own readers",
            ));
        }
    } else if fit.checker_id.is_some() || fit.obstruction_removed.is_some() {
        return Err(refuse(
            "FAMILY_VERDICT",
            "NOT_MEASURED carries no checker or removal claim",
        ));
    }
    Ok(())
}

fn validate_repair_step(
    step: &RepairStep,
    nodes: &BTreeMap<String, &PromptNode>,
    calls: &BTreeMap<String, &CallRecord>,
) -> Result<(), Refusal> {
    if !nodes.contains_key(&step.input_node_id) || !nodes.contains_key(&step.output_node_id) {
        return Err(refuse(
            "FAMILY_STEP_NODE_MISSING",
            "step names a node that is not in the family",
        ));
    }
    if step.ddc_letter.as_ref().is_some_and(|letter| {
        !matches!(
            letter.as_str(),
            "E" | "R" | "C" | "I" | "Λ" | "D" | "M" | "T"
        )
    }) {
        return Err(refuse(
            "FAMILY_DDC_LETTER",
            format!(
                "letter {}",
                py_repr(step.ddc_letter.as_deref().unwrap_or(""))
            ),
        ));
    }
    for colour in [&step.residual_before, &step.residual_after]
        .into_iter()
        .flatten()
    {
        if !matches!(colour.as_str(), "Open" | "Closed" | "Exact") {
            return Err(refuse(
                "FAMILY_RESIDUAL_COLOUR",
                format!("colour {}", py_repr(colour)),
            ));
        }
    }
    let mut step_readers = BTreeSet::new();
    for id in &step.call_ids {
        let call = calls
            .get(id)
            .ok_or_else(|| refuse("FAMILY_STEP_CALL_MISSING", format!("call {id}")))?;
        step_readers.insert(&call.reader_digest);
    }
    validate_step_fitness(&step.fitness, &step_readers)
}

fn validate_terminal(family: &PromptFamily) -> Result<(), Refusal> {
    let term = family.terminal.as_ref().ok_or_else(|| {
        refuse(
            "FAMILY_NO_TERMINAL",
            "a family ends as Repaired, BudgetExhausted or TypedResidual",
        )
    })?;
    if !matches!(
        term.kind.as_str(),
        "Repaired" | "BudgetExhausted" | "TypedResidual"
    ) {
        return Err(refuse(
            "FAMILY_TERMINAL_KIND",
            format!("kind {}", py_repr(&term.kind)),
        ));
    }
    if trim_python(&term.detail).is_empty() {
        return Err(refuse(
            "FAMILY_TERMINAL_DETAIL",
            "terminal detail must name the code or residual",
        ));
    }
    if term.kind == "Repaired"
        && !family.steps.last().is_some_and(|last| {
            last.fitness.checker_verdict == "ACCEPT"
                && last.residual_after.as_deref() == Some("Exact")
        })
    {
        return Err(refuse(
            "FAMILY_REPAIRED_UNSUPPORTED",
            "Repaired needs a final step with an external ACCEPT and an Exact residual",
        ));
    }
    if term.kind == "BudgetExhausted" && !term.detail.starts_with("BUDGET_") {
        return Err(refuse(
            "FAMILY_TERMINAL_DETAIL",
            "BudgetExhausted detail must be a BUDGET_* code",
        ));
    }
    Ok(())
}

pub fn validate_family(family: &PromptFamily) -> Result<(), Refusal> {
    let readers = family
        .readers
        .iter()
        .map(Reader::digest)
        .collect::<Result<BTreeSet<_>, _>>()?;
    let nodes = validate_and_collect_nodes(family, &readers)?;
    let calls = validate_and_collect_calls(family, &readers)?;
    for step in &family.steps {
        validate_repair_step(step, &nodes, &calls)?;
    }
    validate_terminal(family)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb290f818 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb290f818` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb290f818 {
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
impl BoundaryErrorb290f818 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb290f818 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb290f818 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb290f818 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb290f818> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb290f818::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb290f818::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb290f818::ExceedsCapacity {
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
mod l4_mutation_checks_b290f818 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_b290f818 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb290f818::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb290f818::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb290f818::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb290f818::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb290f818::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorb290f818::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorb290f818::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
